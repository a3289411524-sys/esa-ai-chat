# -*- coding: utf-8 -*-
"""
共用模块：脱敏规则 + Markdown -> HTML 渲染。

脱敏规则（两套生成脚本共用，避免规则漂移）：
  1. 全部第三方网址去链接化 —— 裸 URL 变成「〔域名〕」，markdown 链接保留文字并附「〔域名〕」
  2. 指向盗版教材站、作业代做平台、搜索引擎结果页的站点名做中性化替换
其余正文文字一律不动。
"""
import re, html

RISKY = [
    ("www.pdfcoffee.com", "\u3014\u8d44\u6599\u68c0\u7d22\u7ad9\u3015"),
    ("pdfcoffee.com", "\u3014\u8d44\u6599\u68c0\u7d22\u7ad9\u3015"),
    ("pdfcoffee", "\u3014\u8d44\u6599\u68c0\u7d22\u7ad9\u3015"),
    ("www.chegg.com", "\u3014\u7b54\u7591\u5e73\u53f0\u3015"),
    ("chegg.com", "\u3014\u7b54\u7591\u5e73\u53f0\u3015"),
    ("Chegg", "\u3014\u7b54\u7591\u5e73\u53f0\u3015"),
    ("chegg", "\u3014\u7b54\u7591\u5e73\u53f0\u3015"),
    ("web.archive.org", "\u3014\u7f51\u9875\u5b58\u6863\u7ad9\u3015"),
    ("archive.org", "\u3014\u6587\u732e\u5b58\u6863\u7ad9\u3015"),
    ("www.bing.com", "\u3014\u641c\u7d22\u5f15\u64ce\u7ed3\u679c\u9875\u3015"),
    ("cn.bing.com", "\u3014\u641c\u7d22\u5f15\u64ce\u7ed3\u679c\u9875\u3015"),
    ("bing.com", "\u3014\u641c\u7d22\u5f15\u64ce\u7ed3\u679c\u9875\u3015"),
    ("www.google.com", "\u3014\u641c\u7d22\u5f15\u64ce\u7ed3\u679c\u9875\u3015"),
    ("google.com", "\u3014\u641c\u7d22\u5f15\u64ce\u7ed3\u679c\u9875\u3015"),
    ("duckduckgo.com", "\u3014\u641c\u7d22\u5f15\u64ce\u7ed3\u679c\u9875\u3015"),
]
URL_RE = re.compile(r"https?://[^\s\u3000<>\"'`)\]]+", re.I)


def _host(u):
    m = re.match(r"https?://([^/\s?#]+)", u, re.I)
    return m.group(1) if m else u[:40]


def scrub_url(u):
    h = _host(u)
    for bad, rep in RISKY:
        if bad.lower() in h.lower():
            return rep
    return "\u3014" + h + "\u3015"


def scrub_text(s):
    """把裸 URL 换成非链接形式，并中性化高风险域名。"""
    s = URL_RE.sub(lambda m: scrub_url(m.group(0)), s)
    for bad, rep in RISKY:
        if bad in s:
            s = s.replace(bad, rep)
    return s


def inline(s):
    s = html.escape(s, quote=False)
    parts = s.split("`")
    out = []
    for i, seg in enumerate(parts):
        if i % 2 == 1:
            out.append("<code>" + seg + "</code>")
        else:
            out.append(_inline_no_code(seg))
    return "".join(out)


def _inline_no_code(s):
    s = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", s, flags=re.S)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s, flags=re.S)
    s = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"~~(.+?)~~", r"<del>\1</del>", s, flags=re.S)
    s = re.sub(r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)",
               lambda m: m.group(1) + " " + scrub_url(m.group(2)), s)
    return s


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def md_to_html(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(code), quote=False) + "</code></pre>")
            continue
        if not stripped:
            i += 1
            continue
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            out.append("<hr>"); i += 1; continue
        if re.match(r"^<(media|questionnaire-response|user-provided-context)\b", stripped):
            out.append('<pre class="tagline"><code>' + html.escape(stripped, quote=False) + "</code></pre>")
            i += 1; continue

        # 表格
        if "|" in stripped and i + 1 < n and "-" in lines[i + 1] \
                and re.fullmatch(r"\|?[\s:\-|]+\|[\s:\-|]*", lines[i + 1].strip()):
            head = _split_row(stripped)
            aligns = []
            for c in _split_row(lines[i + 1].strip()):
                c = c.strip()
                if c.startswith(":") and c.endswith(":"):
                    aligns.append("center")
                elif c.endswith(":"):
                    aligns.append("right")
                else:
                    aligns.append("left")
            i += 2
            body = []
            while i < n and "|" in lines[i] and lines[i].strip():
                body.append(_split_row(lines[i].strip())); i += 1
            t = ["<div class='tw'><table><thead><tr>"]
            for j, c in enumerate(head):
                a = aligns[j] if j < len(aligns) else "left"
                t.append("<th style='text-align:%s'>%s</th>" % (a, inline(c)))
            t.append("</tr></thead><tbody>")
            for row in body:
                t.append("<tr>")
                for j in range(len(head)):
                    c = row[j] if j < len(row) else ""
                    a = aligns[j] if j < len(aligns) else "left"
                    t.append("<td style='text-align:%s'>%s</td>" % (a, inline(c)))
                t.append("</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t)); continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            lv = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lv, inline(m.group(2)), lv)); i += 1; continue

        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>"); continue

        if re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line):
            items = []
            while i < n:
                mm = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if not mm:
                    if lines[i].strip() == "" and i + 1 < n and re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i + 1]):
                        i += 1; continue
                    break
                items.append((len(mm.group(1)) // 2, mm.group(3))); i += 1
            out.append(_render_list(items)); continue

        buf = [stripped]; i += 1
        while i < n and lines[i].strip() and not re.match(r"^(\s*)([-*+]|\d+[.)])\s+", lines[i]) \
                and not lines[i].strip().startswith("```") and not lines[i].strip().startswith(">") \
                and not re.match(r"^#{1,6}\s+", lines[i].strip()) \
                and not re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        out.append("<p>" + inline("\n".join(buf)).replace("\n", "<br>") + "</p>")
    return "\n".join(out)


def _render_list(items):
    out, stack = [], []
    for indent, text in items:
        while len(stack) > indent:
            out.append("</%s>" % stack.pop())
        while len(stack) < indent:
            out.append("<ul>"); stack.append("ul")
        out.append("<li>" + inline(text) + "</li>")
    while stack:
        out.append("</%s>" % stack.pop())
    return "".join(out)
