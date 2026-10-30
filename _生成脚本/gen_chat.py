# -*- coding: utf-8 -*-
"""
生成「AI 交互作业-2」完整对话记录页面（脱敏版）
- 数据源: qa.json (SQLite 导出) + tools_by_turn.json (snapshots 工具调用统计)
- 脱敏: 所有 URL 去链接化；高风险域名(盗版教材站/代做平台/搜索结果页)中性化
- 零外链: 不引用任何外部 CSS/JS/字体文件
"""
import json, re, html, os, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)          # 网页部署目录（_在线对话记录页/）
BASE = HERE                            # qa.json / tools_by_turn.json 所在目录
OUT_DIR = SITE
os.makedirs(OUT_DIR, exist_ok=True)

qa = json.load(open(os.path.join(BASE, "qa.json"), encoding="utf-8"))
tools = {r["turn"]: r for r in json.load(open(os.path.join(BASE, "tools_by_turn.json"), encoding="utf-8"))}

# ---------------- 脱敏与渲染（共用模块） ----------------
from mdkit import scrub_text, md_to_html

# ---------------- 阶段划分 ----------------
STAGES = [
    (1, 13, "阶段一 · 题目辨析与选题锁定", "10-14 12:40 – 10-14 22:55",
     "确认 7 道题出自同一本教材《Experimental Stress Analysis》，逐一比较差异后锁定第 6 题（相机纵横比标定），并确立协作规则：不由 AI 缓存标准答案，改为共同推导。"),
    (14, 22, "阶段二 · 教材溯源与方法讲解", "10-16 14:28 – 10-16 15:54",
     "定位教材原文页码，节选并做中英双语版，把两种纵横比标定方法（遮光靶板步进法 / 网格比值法）用大白话讲透，并澄清物空间分辨率的含义。"),
    (23, 27, "阶段三 · 经济性与预算决策", "10-16 15:56 – 10-16 16:05",
     "在视野装不下的现实约束下放弃远心镜头，转向经济性导向：先定预算区间，再决定“够用就好”的选型原则。"),
    (28, 45, "阶段四 · 设备选型与真实价格调研", "10-16 16:12 – 10-16 20:51",
     "接手已有调研文件，逐件核实电商实价（浏览器登录后抓取），发现并纠正海外报价未含关税运费的问题，比对多个候选方案并锁定方案 D。"),
    (46, 52, "阶段五 · 方案定型与设计稿产出", "10-16 20:56 – 10-16 21:12",
     "固化全局下载与安装规则、确定采购原则（质量底线 + 无明显提升选便宜）、确认作业交付口径为纯文字实验设计而非仿真，随后要求出 HTML 初稿。"),
    (53, 59, "阶段六 · 设计稿自检与教材回查", "10-16 21:15 – 10-16 21:41",
     "产出 HTML → PDF 设计稿，回查教材 §19.5.1 原文与图 19.11 / 19.12，核对每条数据的出处。"),
    (60, 67, "阶段七 · 交叉评审与错误根源反思", "10-16 21:48 – 10-16 22:47",
     "引入 Claude 与 Gemini 的评审意见做交叉校验，识别出精度结论、系统误差处理、题号与网格线距等 6 处硬错误，并把问题从“改答案”上升到“为什么会反复犯错”的方法论层面。"),
    (68, 90, "阶段八 · 交付物整合与链接分发", "10-17 09:58 – 10-27 09:54",
     "整理工作区、合并 v5 设计稿、拆分“设计方案”与“复盘”两个板块、收敛聊天记录内容范围只保留与任务相关部分，并把分享链接嵌入 PDF。"),
    (91, 92, "阶段九 · 排版升级与链接修复", "10-29 20:24 – 10-29 21:24",
     "要求改用 LaTeX 输出 PDF、弃用暖橙改靛蓝配色、图表以矢量方式插入；随后发现分享链接再次失效，转入本轮修复。"),
]

# ---------------- 装配 ----------------
turns = qa["turns"]
by_turn = {t["turn"]: t for t in turns}


def short_q(t, n=54):
    u = next((i for i in t["items"] if i["k"] == "user"), None)
    if not u:
        return "（本轮无文字提问）"
    q = re.sub(r"\s+", " ", u["t"]).strip()
    return q[:n] + ("…" if len(q) > n else "")


def build_body():
    parts = []
    for lo, hi, title, when, desc in STAGES:
        parts.append('<section class="stage">')
        parts.append('<header class="stage-head"><h2>%s</h2><div class="stage-when">%s</div></header>' % (title, when))
        parts.append('<p class="stage-desc">%s</p>' % desc)
        parts.append('<div class="stage-body">')
        for idx in range(lo, hi + 1):
            t = by_turn.get(idx)
            if not t:
                continue
            parts.append(render_turn(idx, t))
        parts.append("</div></section>")
    return "\n".join(parts)


def render_turn(idx, t):
    ts = t["items"][0]["ts"]
    when = datetime.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")
    tk = tools.get(idx, {})
    tc = tk.get("count", 0)
    tnames = tk.get("tools", {})
    if tc:
        brief = "、".join("%s×%d" % (k, v) for k, v in sorted(tnames.items(), key=lambda x: -x[1]))
        badge = '<span class="badge">本轮调用工具 %d 次 · %s</span>' % (tc, html.escape(brief))
    else:
        badge = '<span class="badge quiet">本轮无工具调用</span>'

    user_chunks, ai_chunks = [], []
    for it in t["items"]:
        raw = it["t"]
        if not raw or not raw.strip():
            continue
        body = md_to_html(scrub_text(raw))
        (user_chunks if it["k"] == "user" else ai_chunks).append(body)

    chunks = []
    if user_chunks:
        segs = "".join('<div class="seg">%s</div>' % c for c in user_chunks)
        chunks.append('<div class="msg user"><div class="who">提问</div><div class="body">%s</div></div>' % segs)
    if ai_chunks:
        segs = "".join('<div class="seg">%s</div>' % c for c in ai_chunks)
        chunks.append('<div class="msg ai"><div class="who">回应</div><div class="body">%s</div></div>' % segs)
    if not chunks:
        chunks.append('<div class="msg ai"><div class="who">回应</div><div class="body empty">'
                      '（本轮无文字回应，仅有工具调用）</div></div>')

    return ('<article class="turn" id="t%d">'
            '<div class="turn-head"><span class="no">第 %d 轮</span><span class="time">%s</span>%s</div>'
            '%s</article>') % (idx, idx, when, badge, "\n".join(chunks))


def build_toc():
    rows = []
    for lo, hi, title, when, desc in STAGES:
        rows.append('<div class="toc-stage"><span class="toc-title">%s</span><span class="toc-when">%s</span></div>' % (title, when))
        for idx in range(lo, hi + 1):
            if idx not in by_turn:
                continue
            rows.append('<a class="toc-row" href="#t%d"><span class="toc-no">%d</span><span class="toc-q">%s</span></a>'
                        % (idx, idx, html.escape(short_q(by_turn[idx], 62))))
    return "\n".join(rows)


n_turns = len(turns)
n_user = sum(1 for t in turns for i in t["items"] if i["k"] == "user")
n_ai = sum(1 for t in turns for i in t["items"] if i["k"] == "assistant" and i["t"].strip())
n_tools = sum(v.get("count", 0) for v in tools.values())
n_days = len({datetime.datetime.fromtimestamp(t["items"][0]["ts"] / 1000).date() for t in turns})
span_days = (turns[-1]["items"][0]["ts"] - turns[0]["items"][0]["ts"]) / 86400000.0

CSS = """
:root{
  --bg:#FAF7F2; --card:#FFFFFF; --card-alt:#F6F1E8;
  --ink:#1F1A17; --ink-2:#5A5652; --ink-3:#8C8780;
  --line:#E5DEC9; --line-soft:#EFEAE0;
  --accent:#D97757; --accent-deep:#B85C3F; --accent-soft:#FBE8DA;
  --user:#2C4A7E; --user-soft:#E8EDF6;
  --code:#F4EFE6;
}
*{box-sizing:border-box;margin:0;padding:0}
html{font-size:16px;scroll-behavior:smooth}
body{font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB","Source Han Sans SC",system-ui,sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.72;-webkit-font-smoothing:antialiased;padding-bottom:70px}
.container{max-width:940px;margin:0 auto;padding:0 24px}
a{color:var(--accent-deep)}
code{font-family:"JetBrains Mono",Consolas,"Courier New",monospace;font-size:.88em;background:var(--code);
  padding:1px 5px;border-radius:3px;color:var(--accent-deep)}
pre{background:var(--code);border-left:3px solid var(--accent);padding:14px 16px;overflow-x:auto;margin:12px 0;
  border-radius:0 4px 4px 0}
pre code{background:none;padding:0;color:var(--ink);font-size:.86em;line-height:1.6}
.header{padding:56px 0 30px;border-bottom:1px solid var(--line)}
.eyebrow{font-size:12px;letter-spacing:1.4px;text-transform:uppercase;color:var(--accent);font-weight:700;margin-bottom:12px}
h1{font-family:"Source Serif 4",Georgia,"Times New Roman","Songti SC",serif;font-size:33px;line-height:1.28;
  font-weight:700;letter-spacing:-.2px}
.sub{margin-top:14px;color:var(--ink-2);font-size:15.5px;max-width:740px}
.sub b{color:var(--ink)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:1px;background:var(--line);
  border:1px solid var(--line);margin:28px 0 0}
.stat{background:var(--card);padding:15px 14px}
.stat .v{font-family:"Source Serif 4",Georgia,serif;font-size:25px;font-weight:700;color:var(--accent-deep);line-height:1.1}
.stat .k{font-size:11.5px;color:var(--ink-3);margin-top:5px;letter-spacing:.4px}
.note{margin:26px 0 0;padding-left:14px;border-left:3px solid var(--accent);color:var(--ink-2);font-size:14px}
.note b{color:var(--ink)}
.toc{margin:34px 0 0;border:1px solid var(--line);background:var(--card)}
.toc-head{padding:13px 18px;border-bottom:1px solid var(--line);font-size:13px;font-weight:700;letter-spacing:.5px;color:var(--ink-2)}
.toc-body{padding:10px 8px 14px;max-height:430px;overflow-y:auto}
.toc-stage{padding:11px 12px 5px;font-size:12.5px;font-weight:700;color:var(--accent-deep);display:flex;
  justify-content:space-between;gap:12px}
.toc-when{font-weight:400;color:var(--ink-3);font-size:11.5px}
.toc-row{display:flex;gap:11px;padding:3px 12px;font-size:13px;color:var(--ink-2);text-decoration:none;
  border-radius:3px;line-height:1.5}
.toc-row:hover{background:var(--card-alt);color:var(--accent-deep)}
.toc-no{color:var(--ink-3);font-family:"JetBrains Mono",Consolas,monospace;font-size:11.5px;min-width:34px;text-align:right;padding-top:2px}
.toc-q{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.stage{margin:52px 0 0}
.stage-head{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;border-bottom:2px solid var(--accent);
  padding-bottom:9px}
.stage-head h2{font-family:"Source Serif 4",Georgia,"Songti SC",serif;font-size:22px;font-weight:700;color:var(--ink)}
.stage-when{font-size:12px;color:var(--ink-3);font-family:"JetBrains Mono",Consolas,monospace}
.stage-desc{margin:12px 0 20px;color:var(--ink-2);font-size:14.5px;max-width:800px}
.turn{background:var(--card);border:1px solid var(--line);margin:0 0 14px;scroll-margin-top:20px}
.turn-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:9px 16px;
  background:var(--card-alt);border-bottom:1px solid var(--line)}
.turn-head .no{font-size:12.5px;font-weight:700;color:var(--accent-deep)}
.turn-head .time{font-size:11.5px;color:var(--ink-3);font-family:"JetBrains Mono",Consolas,monospace}
.badge{font-size:11.5px;color:var(--ink-2);background:var(--card);border:1px solid var(--line);
  padding:2px 9px;border-radius:11px}
.badge.quiet{color:var(--ink-3)}
.msg{padding:15px 18px}
.msg+.msg{border-top:1px dashed var(--line-soft)}
.who{font-size:11.5px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px}
.msg.user{border-left:3px solid var(--user);padding-left:18px}
.msg.user .who{color:var(--user)}
.msg.user .body{background:var(--user-soft);padding:12px 14px;border-radius:0 4px 4px 0}
.msg.ai{border-left:3px solid var(--accent);padding-left:18px}
.msg.ai .who{color:var(--accent-deep)}
.msg.ai .body{padding:2px 0}
.seg+.seg{margin-top:11px;padding-top:11px;border-top:1px dashed var(--line-soft)}
.msg.user .body .seg+.seg{border-top-color:rgba(44,74,126,.22)}
.body.empty{color:var(--ink-3);font-style:normal}
pre.tagline{background:var(--card-alt);border-left:3px solid var(--ink-3);border-radius:0 4px 4px 0;
  color:var(--ink-2);font-size:.82em;line-height:1.5;word-break:break-all}
.body p{margin:.55em 0}
.body ul,.body ol{margin:.5em 0 .6em 1.3em}
.body li{margin:.24em 0}
.body h1,.body h2,.body h3,.body h4{font-family:"Source Serif 4",Georgia,"Songti SC",serif;margin:1em 0 .45em;line-height:1.35}
.body h1{font-size:21px}.body h2{font-size:18px}.body h3{font-size:16px}.body h4{font-size:15px}
.body blockquote{margin:.6em 0;padding-left:13px;border-left:3px solid var(--line);color:var(--ink-2)}
.body hr{border:0;border-top:1px solid var(--line);margin:1.1em 0}
.body table{border-collapse:collapse;width:100%;font-size:13.5px;margin:.6em 0}
.body th,.body td{border:1px solid var(--line);padding:7px 10px;vertical-align:top}
.body th{background:var(--card-alt);font-weight:700}
.tw{overflow-x:auto}
.msg.user .body table{background:var(--card)}
.footer{margin:60px 0 0;padding-top:22px;border-top:1px solid var(--line);color:var(--ink-2);font-size:13.5px}
.footer h3{font-family:"Source Serif 4",Georgia,"Songti SC",serif;font-size:17px;color:var(--ink);margin-bottom:10px}
.footer li{margin:.35em 0;margin-left:1.2em}
@media print{
  body{background:#fff;padding:0}
  .toc,.badge{display:none}
  .turn{break-inside:avoid;border-color:#ccc}
}
"""

doc = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>实验力学第 6 题 · AI 完整交互记录</title>
<style>%(css)s</style>
</head>
<body>
<div class="container">

<header class="header">
  <div class="eyebrow">AI 交互作业 · 第二次作业 · 支撑材料</div>
  <h1>实验力学第 6 题（相机纵横比标定）<br>与 AI 的完整交互记录</h1>
  <p class="sub">本页面是提交件《第 6 组 + 金行云（第二次作业）》的支撑材料，完整保留本次任务中<b>用户提问</b>与 <b>AI 回应</b>的全部文字往来，并标注每一轮 AI 实际调用工具的次数与工具名，用于说明 AI 参与设计的深度与过程的可追溯性。<b>页面不展示工具的原始输出</b>，以控制篇幅并避免无关信息干扰评审。</p>

  <div class="stats">
    <div class="stat"><div class="v">%(n_turns)d</div><div class="k">交互轮次</div></div>
    <div class="stat"><div class="v">%(n_user)d</div><div class="k">用户提问</div></div>
    <div class="stat"><div class="v">%(n_ai)d</div><div class="k">AI 文字回应</div></div>
    <div class="stat"><div class="v">%(n_tools)d</div><div class="k">工具调用次数</div></div>
    <div class="stat"><div class="v">%(n_days)d</div><div class="k">活跃天数</div></div>
  </div>

  <p class="note"><b>关于脱敏：</b>对话中出现的第三方网址已统一去除链接化处理；少数指向盗版教材站、作业代做平台与搜索引擎结果页的站点名做了中性化替换，替换位置以方括号标注。除此之外，全部提问与回应的文字内容均未改动、未删减、未重写。</p>
</header>

<nav class="toc">
  <div class="toc-head">对话目录（共 %(n_turns)d 轮，可点击跳转）</div>
  <div class="toc-body">
%(toc)s
  </div>
</nav>

%(body)s

<footer class="footer">
  <h3>记录说明</h3>
  <ul>
    <li>记录区间：2026-10-14 至 2026-10-29，时间跨度 %(span_days).1f 天，其中 %(n_days)d 天有实际交互，覆盖作业的全部推进阶段。</li>
    <li>统计口径：轮次按一次“用户提问 → AI 回应”的完整交互计；AI 回应可能分多次输出，均按原顺序保留；工具调用次数为该轮内 AI 实际发起的工具调用总数。</li>
    <li>工具调用明细：原始工具输出（含网页正文、文件内容等）不在本页展示，仅保留工具名称与调用次数，以免冗长内容掩盖对话本身。</li>
    <li>内容一致性：保留全部问答原文，未做摘要、改写或节选；仅对第三方网址做去链接与中性化处理。</li>
    <li>配套提交件：《第 6 组 + 金行云（设计方案）.pdf》为实验设计方案本体，《第 6 组 + 金行云（第二次作业）.pdf》为提示词优化过程、错误复盘过程与关键记录。</li>
  </ul>
</footer>

</div>
</body>
</html>
""" % {
    "css": CSS,
    "n_turns": n_turns,
    "n_user": n_user,
    "n_ai": n_ai,
    "n_tools": n_tools,
    "n_days": n_days,
    "span_days": span_days,
    "toc": build_toc(),
    "body": build_body(),
}

p = os.path.join(OUT_DIR, "full.html")
with open(p, "w", encoding="utf-8") as f:
    f.write(doc)

print("written:", p)
print("bytes:", os.path.getsize(p))
# 残留自检
bad = [w for w in ["pdfcoffee", "chegg", "Chegg", "bing.com", "google.com", "duckduckgo", "archive.org"] if w in doc]
print("risky residue:", bad if bad else "NONE")
print("http refs left:", doc.count("http://"), doc.count("https://"))
print("href= refs:", doc.count("href="))
