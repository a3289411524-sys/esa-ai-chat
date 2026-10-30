# -*- coding: utf-8 -*-
"""
生成「提示词迭代全过程」专题页 index.html

主题：不是完整聊天流水，而是其中一条主线——
      第一个提示词没有产出想要的结果 → 用户逐轮补约束 → AI 逐轮返工 → 最终可用交付。

数据源：qa.json（问答流水），所有引用都标注轮次，可跳转到 full.html 核对原文。
"""
import json, os, datetime, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mdkit import scrub_text, md_to_html

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
qa = json.load(open(os.path.join(HERE, "qa.json"), encoding="utf-8"))
tools = {r["turn"]: r for r in json.load(open(os.path.join(HERE, "tools_by_turn.json"), encoding="utf-8"))}

BY = {t["turn"]: t for t in qa["turns"]}


def users(turn):
    return [i["t"] for i in BY[turn]["items"] if i["k"] == "user" and i["t"].strip()]


def ais(turn):
    return [i["t"] for i in BY[turn]["items"] if i["k"] == "assistant" and i["t"].strip()]


def when(turn):
    ts = BY[turn]["items"][0]["ts"]
    return datetime.datetime.fromtimestamp(ts / 1000).strftime("%m-%d %H:%M")


def tc(turn):
    return tools.get(turn, {}).get("count", 0)


def take(turn, idx=0, limit=900, tail=False):
    """取该轮第 idx 条用户消息（长文按字数截断）。"""
    us = users(turn)
    if not us:
        return ""
    t = us[idx].strip()
    if len(t) <= limit:
        return t
    if tail:
        return "…（略）…\n" + t[-limit:]
    return t[:limit] + "\n…（略）…"


def take_both(turn, idx=0, head=190, tail=230):
    """长文取首尾两段，中间省略。"""
    us = users(turn)
    if not us:
        return ""
    t = us[idx].strip()
    if len(t) <= head + tail:
        return t
    return t[:head] + "\n\n…（中间 6 道题面略）…\n\n" + t[-tail:]


def esc(s):
    return scrub_text(s)


def link_to(turn, label=None):
    return '<a class="ref" href="full.html#t%d">%s</a>' % (turn, label or ("完整流水第 %d 轮" % turn))


# ============================ 里程碑定义 ============================
# 每条：触发轮 / 缺口 / 用户原话 / AI 当时给的 / 用户如何补 / 结果
M = [
    dict(
        id="m1", turn=1, title="第一版提示词：只给了题面和一句「哪个比较容易」",
        quote=take_both(1, 0, 190, 240),
        qtag="用户 · 第 1 轮（10-14 12:40）",
        ai="给出了一张 7 道题的「容易度排序」表，把题 7 排在第一、题 6 排在后面，并附「10 分钟写完，思路清晰」之类的推荐理由。",
        gap="题目问的是「哪一道比较容易」，但作业真正要的是**把第 6 题做完**。提示词里没有交代：要做哪一道、要交付什么、按什么标准算合格。AI 只能猜，猜的代价是整份作业方向错了。",
        fix="第 2 轮改成「这是我的作业我需要你仔细分析一下，给我它们之间的差异还有你去看看这些题目应该是出自同一本书」——补上了**任务性质（作业）**与**第一项交付（辨析差异 + 溯源）**。",
        effect="AI 开始拆解题目结构并检索教材来源，对话从「选择题」转入「作业协作」。",
    ),
    dict(
        id="m2", turn=2, title="教材身份判错：AI 给出了正确书名之外的答案",
        quote=take(2, 0, 200),
        qtag="用户 · 第 2 轮（10-14 13:09）",
        ai="检索后给出一份像模像样的「教材确认」表：作者 Richard S. Figliola 与 Donald E. Beasley，第 8 版，Wiley 出版，附 ISBN。",
        gap="**结论是错的。** 那本书并不包含这 7 道题。提示词只说了「出自同一本书」，没有给出可核对的判据，AI 只能靠书名联想，一旦联想偏了，整条溯源链都建立在错误事实上——后面每一页引用都会跟着错。",
        fix="第 3 轮用户直接纠正：「experimental stress analysis这本书去看看应该是这本书」。",
        effect="AI 改判为 Dally & Riley《Experimental Stress Analysis》第 4 版，并给出与题目内容逐项吻合的证据。",
    ),
    dict(
        id="m3", turn=4, title="从二手检索升级到一手依据：用户直接递上教材原 PDF",
        quote=take(4, 0, 120),
        qtag="用户 · 第 4 轮（10-14 13:43）",
        ai="此前所有页码、章节号、公式编号都来自搜索引擎摘要，无法逐字核对。收到 PDF 后读目录、读 Ch 11 与 Ch 19 习题，做出「作业题 ↔ 教材原题 ↔ 章节」对照表，并指出题 1-3 的数值被改动过（200 kN·m vs 教材 100 kN·m、60 MN vs 100 MN、±0.002 mm/2 mm vs ±0.004 mm/5 mm）。",
        gap="AI 的产出「像」教材原文，但没有任何一处能证明它就是教材原文。提示词缺**一手依据**这一维度。",
        fix="第 4 轮把 43 MB 的教材 PDF 递进来，等于把「可核对的依据」交到 AI 手上。",
        effect="此后每一个数字都能追到具体页码；第 14 轮再要求「这些内容对应教材 PDF 哪些页」时，AI 直接给出页码对照表。",
    ),
    dict(
        id="m4", turn=5, title="讲解深度不足：从「分类表」到「逐题拆解」",
        quote=take(5, 0, 120),
        qtag="用户 · 第 5 轮（10-14 13:50）",
        ai="第 5 轮之前，AI 对 7 道题只给了主题分类表（两类测量方法 + 难度排序）。",
        gap="用户要的是能用来做作业的理解，不是分类标签。提示词缺**输出深度**这一维度。",
        fix="第 5 轮：「我需要详细讲解一下每一个作业的区别以及他们的主题是什么」。",
        effect="AI 输出 4000+ 字的逐题拆解：主题、核心难点、典型解法、哪些题的思路可以互相借用。",
    ),
    dict(
        id="m5", turn=7, title="交付形态与视觉语言：HTML、配色、语气、还要不要绿色",
        quote=take(7, 0, 200),
        qtag="用户 · 第 7 轮（10-14 14:08）",
        ai="第 6 轮 AI 先出了一份题 7 的 HTML 试水版，结构和内容都对，但视觉是默认样式、篇幅偏冗长。",
        gap="「写出来」不等于「能交上去」。提示词缺**交付形态**与**视觉语言**两个维度。",
        fix="第 6 轮「我需要html文件」定形态；第 7 轮追加「用 frontend-design 这个 skill 重新设计一版，配色参考 Claude 的暖橙色加白色，内容要更加简洁，注重准确和务实的语言风格」；第 8 轮追加「最后的部分不要绿色的元素」；第 9 轮追加「把这个风格记录在全局记忆里面」。",
        effect="形成可复用的风格基线（暖橙白 + 准确务实的措辞 + 不用绿色），第 9 轮把它写进长期记忆，后续版本不再回退。",
    ),
    dict(
        id="m6", turn=11, title="受众错配：讲得太专业，听不懂",
        quote=take(11, 0, 260),
        qtag="用户 · 第 11 轮（10-14 14:38）",
        ai="第 10 轮 AI 给出的是标准工程口吻：结构拆解表、对应教材、关键要求、参数表。",
        gap="内容没错，但用户读不进去。提示词从头到尾没有交代**受众是谁**，AI 默认对方是同行。",
        fix="第 11 轮：「我发现你的讲解还是比较让我难懂，我是一个完全的初学者……所以我需要你用大白话的形式先让我知道我在做什么和为什么做吧，知识穿插在这个里面就好」。",
        effect="AI 改用「贴创可贴的应变片 vs 喷麻子的散斑」这类比喻重讲；此后第 16 轮「算纵横比的两个方法给我用大白话的方式讲一下尤其第二种方法」沿用同一口径。",
    ),
    dict(
        id="m7", turn=12, title="协作模式：不要替我缓存标准答案",
        quote=take(12, 0, 200),
        qtag="用户 · 第 12 轮（10-14 22:09）",
        ai="此前 AI 默认自己在「做作业」，会直接给出成品式答案。",
        gap="提示词缺**协作方式**这一维度：默认模式是「AI 交付答案」，而用户要的是「一起推」。",
        fix="第 12 轮：「我不需要你缓存有关这道题目标准答案的内容，我们来协作一起完成这次的任务，记住了吗，列出我们这次要做的事情」。",
        effect="AI 切换到协作模式并列出 6 件事的计划；此后所有结论都以「推导 + 出处」形式呈现，而非成品答案。",
    ),
    dict(
        id="m8", turn=28, title="资源约束：报价从 ¥24,200 被打回重来",
        quote=take(28, 0, 300),
        qtag="用户 · 第 28 轮（10-16 16:12）",
        ai="第 27 轮按「三万极简风格」出了一份 10 件设备的清单，设备型号是凭经验配的。",
        gap="价格是估的，没查过；清单里还包含用户其实已经有的电脑。提示词缺**资源约束**与**数据来源**两个维度。",
        fix="第 23 轮先定方向「装不下就接受误差大一些，此时考虑经济性」；第 24 轮要预算区间；第 27 轮加「进入下一步之前先列出清单给我看看」；第 28 轮直接给可验收的目标：「重新调研核实现在我们真实要花的钱，给你一小时，自己设置一个 goal，之后我来验收，最终标准就是要列出原先的价格和最后你调查的真实价格」。",
        effect="AI 用一小时的浏览器实测重查，得到 v1 ¥24,200 → v2 ¥6,400-10,700 的对照报告，并指出计算机项按用户自有的联想拯救者 Y7000P 2024 计 0 元。",
    ),
    dict(
        id="m9", turn=43, title="数据真实性：海关、运费与「8 倍价差」的来源",
        quote=take(43, 0, 160),
        qtag="用户 · 第 43 轮（10-16 20:49）",
        ai="v2 报告里海康相机标价 ¥1,900，来源写的是 eBay $260 的跨境价。",
        gap="**这个价不能直接用**：不含关税、不含国际运费。AI 把「标价」当成了「到手价」。",
        fix="第 43 轮「这个海康相机的价格是海外的价格对吗如果是的你加上海关和运费了吗」→ 第 44 轮「先不改你先在去复查一下看看还有没有类似的情况，而且你这个 v1 版本的价格是在哪里看到的价差这么多品质有保障吗」→ 第 45 轮「你还没有回答完整我的问题，这个海康镜头的价格差这么多品质有保障吗」。",
        effect="逐件复查后换成京东自营含税含运价（相机 ¥1,034、镜头 ¥600），并把镜头从 1688 白牌换成海康正品，总价收敛到 ¥3,800。第 45 轮还补上了「8 倍价差来自分销加价、不是质量差」的判断依据。",
    ),
    dict(
        id="m10", turn=57, title="数值与所选设备不自洽：精度结论整段重算",
        quote=take(57, 0, 160),
        qtag="用户 · 第 57 轮（10-16 21:20）",
        ai="此前给的两套精度：A ±0.05%、B ±1.5%，推导用的是「理想参数」。",
        gap="用户挑的设备有具体规格（位移台 ±3 μm、网格板 ±10 μm、镜头畸变 1%），报告里的精度数字却没用它们——**结论与自己的采购清单脱节**。",
        fix="先在第 55 轮追问「你这个设计的过程里面没有参考书本 PDF 里面的标准答案吧，没有联网搜索吧」、第 56 轮追问「问题是设计这个实验你是直接套用的教材的方法吗」，把来源问题先摊开；第 57 轮才点到数值：「这个我问一嘴你这个具体的数值有没有结合我么自己选择的设备精度进行调整呢」。",
        effect="AI 承认「没有，这是设计漏洞」，按 v3 设备真实精度重算，得到 A ±0.19% / B ±0.07%。这一步也让第 59 轮之后的外部评审能逐条对照教材，指出真正的硬伤（方法 A 用的是 §19.5.2 测放大率的方法、误差预算把系统误差按 √n 平均、题号写成 Ex 19.10、网格间距写成 0.1 mm）。",
    ),
    dict(
        id="m11", turn=63, title="质量机制：从「外包评审」改到「自问自答」",
        quote=take(63, 0, 300),
        qtag="用户 · 第 63 轮（10-16 22:31）",
        ai="在 Claude / GPT / Gemini 三份外部评价之后，AI 把 10 个硬错、5 个工程错、1 个概念错列成表，第一轮反思的结论是「我应该查数据表」「我应该自检」。",
        gap="反思停在了**现象层**：知道了错在哪，但没回答「为什么一个写完就标 completed 的流程会连续产出这种错误」。",
        fix="三连击升级：第 63 轮要求「沉淀下我们目前看到的所有问题，问问你自己为什么会犯这么多错」；第 64 轮「你不应该只看到了表面……需要加深下你的思考，多思考，广泛的思考……不能只浮于表面」；第 65 轮「这个我不可能每次都找三个 ai 帮你评价……不要寄希望于别人，你要更加的多思考，主动给你自己找事情和找方法」。",
        effect="根因定位从「我应该自检」升级为「**没设过程质量门**——v1/v2/v3 写完直接标完成，没有评审这一步**」；随后把自检 SOP 从「3 AI 评审 30 分钟找 80% 错」改写成「**写前自己深查、写时自己算、写完自问自答 ≥3 轮**」，并明确不外包外部评审。",
    ),
    dict(
        id="m12", turn=88, title="交付收敛：内容该放哪、该删哪、链接该放哪",
        quote=take(88, 0, 160),
        qtag="用户 · 第 88 轮（10-27 09:03）",
        ai="第二次作业提交件初稿把大段对话原文搬进了 PDF。",
        gap="提示词没交代**成果的载体分工**，导致 PDF 变成聊天记录堆砌，评审重点被淹没。",
        fix="第 75 轮要求把 PDF 拆成「最终实验设计 + 材料清单」与「整合改进过程」两块并附可分享链接；第 78 轮收窄内容范围「需要有关于本次实验设计任务有关的，无关的想整理工作区啥的都去掉只保留这些」；第 88 轮明确分工「既然所有的对话记录已经在链接里面了，pdf 里面就放关键的作业要求的记录，错误内容和提示词优化内容的过程放在 pdf 里面」。",
        effect="形成最终形态：两份 PDF（设计方案本体 0 个链接 / 第二次作业复盘三件套 2 个可点击链接）+ 一个对话记录在线页，三者互不重叠。",
    ),
]

# ============================ 六项约束 ============================
SIX = [
    ("受众是谁", "完全未提", "AI 默认对方是同行，讲解用工程术语，用户读不进去", "第 11 轮", "「我是一个完全的初学者……用大白话的形式」"),
    ("要什么形态的交付物", "完全未提", "先给 Markdown 表格，后给 HTML，后给 PDF，三次返工", "第 6 / 7 / 53 轮", "「我需要html文件」「先做成一个html文件让我看看，合格了就做出pdf文件」"),
    ("用什么工具", "完全未提", "搜索结果页被拒后改用浏览器桥、eBay、1688，工具链反复切换", "第 2 / 26 / 31 轮", "「你可以使用opencli」「我已经打开了chrome浏览器你试下连接下opencli」"),
    ("事实依据从哪来", "完全未提", "教材身份判错、页码靠搜索摘要、报价未含税运", "第 3 / 4 / 43 轮", "「experimental stress analysis这本书」「看下把这是书本原pdf」「你加上海关和运费了吗」"),
    ("输出什么风格", "完全未提", "默认模板风格、篇幅冗长、含绿色元素", "第 7 / 8 / 9 轮", "「配色参考Claude的暖橙色加白色……注重准确和务实」「最后的部分不要绿色的元素」"),
    ("怎么保证质量", "完全未提", "写完直接标完成，连续产出 6 处硬错、5 处工程错", "第 55 / 57 / 63 / 65 轮", "「这个具体的数值有没有结合我么自己选择的设备精度进行调整呢」「不要寄希望于别人」"),
]

# ============================ 三次返工级事件 ============================
REWORK = [
    dict(
        n="返工 01", when="10-14 13:09 → 13:22",
        title="教材身份判错",
        before="第 2 轮结论：教材为 Figliola & Beasley《Theory and Design for Mechanical Measurements》第 8 版（Wiley，ISBN 9781394361137），并附完整「教材确认」表。",
        after="第 3 轮纠正后：教材为 Dally & Riley《Experimental Stress Analysis》第 4 版（College House Enterprises，ISBN 0-9762413-0-7）。第 4 轮拿到原 PDF 后完成逐章比对。",
        lesson="检索到的「像答案的答案」必须能被一手材料证伪。提示词里没有判据，AI 就没有自查的落点。",
    ),
    dict(
        n="返工 02", when="10-16 16:12 → 10-16 21:12",
        title="采购价与方案重做",
        before="v1 清单：10 件设备，凭经验配价，总价 ¥24,200；含 200 mm 工业 C 接口镜头（国内不流通）、电脑 ¥5,000。",
        after="v2 实测：¥6,400-10,700；v3 锁定方案 D：海康 MVL 50 mm 镜头、电脑按用户自有 Y7000P 2024 计 0 元；总价 ¥3,800。",
        lesson="「有没有查过」和「查到的价能不能直接用」是两件事——跨境价不含关税运费，1688 批发价未含税未含运。",
    ),
    dict(
        n="返工 03", when="10-16 21:20 → 10-17 12:50",
        title="精度结论整段重算",
        before="理想参数推导：A ±0.05%、B ±1.5%，并把 B 定性为「快速够用」。",
        after="按 v3 设备真实精度重算：A ±0.19% / B ±0.07%（结论反转）；再经外部评审与自检，最终 A 单步 ±2.83%、A 首尾 5.00 mm 总长法 ±0.31%、B ±0.08%，并改为「B 为主、A 交叉验证」。",
        lesson="结论与交付清单里的设备规格脱节，等于结论没有落地依据。提示词要显式要求「数值须与已选设备对应」。",
    ),
]

# ============================ 质量机制三阶段 ============================
QM = [
    ("第一阶段 · 列出错", "第 63 轮",
     "AI 承认「没做交叉评审我自己没发现这些错」，把 10 个硬错、5 个工程错、1 个概念错逐条列表，每条附「谁指出的 / 教材原文 / 我错在哪 / 如何修正」。",
     "解决了「错在哪」，但结论停在「我应该查数据表」「我应该自检」——仍然只解释了个体失误，没解释流程为什么允许连续出错。"),
    ("第二阶段 · 追问根因", "第 64 轮",
     "用户要求「不能只浮于表面」。AI 改用「说话前三思 + 目标驱动」反问自己，把根因定位为「**没设过程质量门——把『动手』和『完成』混淆了**」，并指出 v3 当时属于「虚假完成」。",
     "第一次把问题从「答案层面」升级到「流程层面」，但改进动作仍指向「写完找 3 个 AI 评审」。"),
    ("第三阶段 · 收回责任", "第 65-66 轮",
     "用户直接否定外包：「这个我不可能每次都找三个 ai 帮你评价……不要寄希望于别人，你要更加的多思考，主动给你自己找事情和找方法」。AI 随即把自检 SOP 从「3 AI 评审 30 分钟找 80% 错」改写为「**写前自己深查、写时自己算、写完自问自答 ≥3 轮**」，并把「token 用在思考上」写入长期记忆。",
     "质量门从「外部资源」变成「流程内建」。此后 v4 → v6 全部由自问自答推进，未再依赖外部评审。"),
]

# ============================ 可复用模板 ============================
TPL = [
    ("交代任务性质与交付物", "「这是我的作业……我要的是……」+ 最终交什么文件、给谁看", "第 2 / 75 轮"),
    ("给判据而不是给答案", "「你自己查一遍，先别反驳，先做记录」", "第 59 / 63 轮"),
    ("标受众与表达口径", "「我是一个完全的初学者……用大白话」", "第 11 / 16 轮"),
    ("给一手依据", "「这是书本原 pdf」「对应教材的哪些页」", "第 4 / 14 轮"),
    ("给资源约束与验收标准", "「预算取中间值」「给你一小时……最终标准是要列出原先价格和真实价格」", "第 24 / 28 轮"),
    ("要求先给清单再动手", "「在进入下一步之前先列出这个清单给我看看」", "第 27 轮"),
    ("要求数值与已选条件自洽", "「你的具体数值有没有结合我选的设备精度调整」", "第 57 轮"),
    ("要求内容范围收敛", "「与本次任务有关的留下，无关的删掉」", "第 78 / 88 轮"),
]

# ============================ 渲染 ============================
def render_quote(text, tag, turn):
    return ('<blockquote class="uq"><div class="qt">%s</div><div class="qx">%s</div>'
            '<div class="qf">%s</div></blockquote>') % (
        tag, md_to_html(esc(text)), link_to(turn))


def render_milestone(m):
    return """
<article class="ms" id="%(id)s">
  <div class="ms-head">
    <span class="ms-n">%(title)s</span>
    <span class="ms-w">%(when)s</span>
    <span class="ms-t">第 %(turn)d 轮 · AI 调用工具 %(tc)d 次</span>
  </div>
  <div class="ms-body">
    <div class="ms-block">
      <div class="ms-label">当时的提示词</div>
      %(quote)s
    </div>
    <div class="ms-block">
      <div class="ms-label">AI 给出的</div>
      <div class="ms-txt">%(ai)s</div>
    </div>
    <div class="ms-block gap">
      <div class="ms-label">差距在哪</div>
      <div class="ms-txt">%(gap)s</div>
    </div>
    <div class="ms-block fix">
      <div class="ms-label">补上的约束</div>
      <div class="ms-txt">%(fix)s</div>
    </div>
    <div class="ms-block eff">
      <div class="ms-label">结果</div>
      <div class="ms-txt">%(effect)s</div>
    </div>
  </div>
</article>""" % dict(id=m["id"], title=m["title"], when=when(m["turn"]), turn=m["turn"],
                   tc=tc(m["turn"]), quote=render_quote(m["quote"], m["qtag"], m["turn"]),
                   ai=md_to_html(esc(m["ai"])), gap=md_to_html(esc(m["gap"])),
                   fix=md_to_html(esc(m["fix"])), effect=md_to_html(esc(m["effect"])))


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
.container{max-width:960px;margin:0 auto;padding:0 24px}
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
.sub{margin-top:14px;color:var(--ink-2);font-size:15.5px;max-width:800px}
.sub b{color:var(--ink)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:1px;background:var(--line);
  border:1px solid var(--line);margin:28px 0 0}
.stat{background:var(--card);padding:15px 14px}
.stat .v{font-family:"Source Serif 4",Georgia,serif;font-size:25px;font-weight:700;color:var(--accent-deep);line-height:1.1}
.stat .k{font-size:11.5px;color:var(--ink-3);margin-top:5px;letter-spacing:.4px}
.note{margin:26px 0 0;padding-left:14px;border-left:3px solid var(--accent);color:var(--ink-2);font-size:14px}
.note b{color:var(--ink)}
.jump{margin:30px 0 0;border:1px solid var(--line);background:var(--card)}
.jump-head{padding:13px 18px;border-bottom:1px solid var(--line);font-size:13px;font-weight:700;color:var(--ink-2)}
.jump-body{padding:12px 18px 16px;display:flex;flex-wrap:wrap;gap:8px}
.jump-body a{font-size:13px;text-decoration:none;border:1px solid var(--line);padding:5px 12px;border-radius:14px;
  background:var(--card-alt);color:var(--ink-2)}
.jump-body a:hover{border-color:var(--accent);color:var(--accent-deep)}
section.sec{margin:56px 0 0}
.sec-head{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;border-bottom:2px solid var(--accent);padding-bottom:9px}
.sec-head h2{font-family:"Source Serif 4",Georgia,"Songti SC",serif;font-size:23px;font-weight:700}
.sec-no{font-family:"JetBrains Mono",Consolas,monospace;font-size:12px;color:var(--ink-3)}
.sec-desc{margin:13px 0 22px;color:var(--ink-2);font-size:14.5px;max-width:820px}
p.tx{margin:.7em 0;color:var(--ink-2)}
p.tx b,li b{color:var(--ink)}
.tw{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:.6em 0;background:var(--card)}
th,td{border:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}
th{background:var(--card-alt);font-weight:700;color:var(--ink)}
.ms{background:var(--card);border:1px solid var(--line);margin:0 0 18px}
.ms-head{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:11px 18px;background:var(--card-alt);
  border-bottom:1px solid var(--line)}
.ms-n{font-size:14px;font-weight:700;color:var(--accent-deep)}
.ms-w{font-size:11.5px;color:var(--ink-3);font-family:"JetBrains Mono",Consolas,monospace}
.ms-t{font-size:11.5px;color:var(--ink-3);margin-left:auto}
.ms-body{padding:4px 18px 16px}
.ms-block{margin-top:14px;padding-left:13px;border-left:2px solid var(--line)}
.ms-label{font-size:11.5px;font-weight:700;letter-spacing:1.2px;color:var(--ink-3);margin-bottom:5px}
.ms-txt{color:var(--ink-2);font-size:14.5px}
.ms-txt p,.rw-v p,.qm-v p{margin:.3em 0}
.ms-txt p:first-child,.rw-v p:first-child,.qm-v p:first-child{margin-top:0}
.ms-txt p:last-child,.rw-v p:last-child,.qm-v p:last-child{margin-bottom:0}
.ms-txt strong,.rw-v strong,.qm-v strong{color:var(--ink)}
.ms-block.gap{border-left-color:var(--accent)}
.ms-block.gap .ms-label{color:var(--accent-deep)}
.ms-block.fix{border-left-color:var(--user)}
.ms-block.fix .ms-label{color:var(--user)}
.ms-block.eff{border-left-color:var(--ink-3)}
blockquote.uq{margin:0;padding:12px 16px;background:var(--user-soft);border-left:3px solid var(--user);border-radius:0 4px 4px 0}
.qt{font-size:11.5px;font-weight:700;letter-spacing:1px;color:var(--user);margin-bottom:7px}
.qx{color:var(--ink);font-size:14.5px}
.qx p{margin:.4em 0}
.qf{margin-top:9px;font-size:12px}
.ref{color:var(--user);text-decoration:none;border-bottom:1px dotted var(--user)}
.ref:hover{color:var(--accent-deep);border-bottom-color:var(--accent-deep)}
.rw{background:var(--card);border:1px solid var(--line);margin:0 0 16px;padding:16px 18px}
.rw-h{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px}
.rw-n{font-size:12px;font-weight:700;letter-spacing:1px;color:var(--accent-deep)}
.rw-t{font-size:15.5px;font-weight:700;color:var(--ink)}
.rw-w{font-size:11.5px;color:var(--ink-3);font-family:"JetBrains Mono",Consolas,monospace}
.rw-row{display:grid;grid-template-columns:88px 1fr;gap:12px;padding:9px 0;border-top:1px dashed var(--line-soft)}
.rw-row:first-of-type{border-top:0}
.rw-k{font-size:12px;font-weight:700;color:var(--ink-3)}
.rw-v{color:var(--ink-2);font-size:14px}
.rw-v.lesson{border-left:3px solid var(--accent);padding-left:12px;color:var(--ink)}
.qm{background:var(--card);border:1px solid var(--line);margin:0 0 14px;padding:15px 18px}
.qm-h{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.qm-s{font-size:14.5px;font-weight:700;color:var(--accent-deep)}
.qm-w{font-size:11.5px;color:var(--ink-3);font-family:"JetBrains Mono",Consolas,monospace}
.qm-v{color:var(--ink-2);font-size:14.5px}
.qm-v.lim{margin-top:8px;padding-top:8px;border-top:1px dashed var(--line-soft);color:var(--ink-3);font-size:13.5px}
.tpl{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--card)}
.tpl th{background:var(--card-alt)}
.tpl td:first-child{font-weight:700;color:var(--ink);white-space:nowrap}
.foot{margin:60px 0 0;padding-top:22px;border-top:1px solid var(--line);color:var(--ink-2);font-size:13.5px}
.foot h3{font-family:"Source Serif 4",Georgia,"Songti SC",serif;font-size:17px;color:var(--ink);margin-bottom:10px}
.foot li{margin:.35em 0;margin-left:1.2em}
@media print{body{background:#fff;padding:0}.jump{display:none}.ms,.rw,.qm{break-inside:avoid}}
"""

# 六项约束表
six_rows = []
for i, (dim, has, bad, turns, quote) in enumerate(SIX, 1):
    six_rows.append(
        "<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (i, dim, has, md_to_html(esc(bad)), turns, md_to_html(esc(quote))))

rework_html = "".join(
    """<div class="rw"><div class="rw-h"><span class="rw-n">%(n)s</span><span class="rw-t">%(title)s</span>
<span class="rw-w">%(when)s</span></div>
<div class="rw-row"><div class="rw-k">最初给出</div><div class="rw-v">%(before)s</div></div>
<div class="rw-row"><div class="rw-k">改成</div><div class="rw-v">%(after)s</div></div>
<div class="rw-row"><div class="rw-k">教训</div><div class="rw-v lesson">%(lesson)s</div></div></div>"""
    % dict(n=r["n"], title=r["title"], when=r["when"],
           before=md_to_html(esc(r["before"])), after=md_to_html(esc(r["after"])),
           lesson=md_to_html(esc(r["lesson"])))
    for r in REWORK)

qm_html = "".join(
    """<div class="qm"><div class="qm-h"><span class="qm-s">%(s)s</span><span class="qm-w">%(w)s</span></div>
<div class="qm-v">%(v)s</div><div class="qm-v lim">%(lim)s</div></div>"""
    % dict(s=s, w=w, v=md_to_html(esc(v)), lim=md_to_html(esc(lim))) for s, w, v, lim in QM)

tpl_rows = "".join(
    "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (a, b, c) for a, b, c in TPL)

ms_html = "\n".join(render_milestone(m) for m in M[1:])
ms_rest = len(M) - 1

n_turns = len(qa["turns"])
n_user = qa["n_user"]
n_ai = sum(1 for t in qa["turns"] for i in t["items"] if i["k"] == "assistant" and i["t"].strip())
n_tools = sum(r.get("count", 0) for r in tools.values())
t0 = BY[1]["items"][0]["ts"]
t1 = BY[n_turns]["items"][0]["ts"]
span = (t1 - t0) / 86400000.0

doc = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>提示词迭代全过程 · 实验力学第 6 题</title>
<style>%(css)s</style>
</head>
<body>
<div class="container">

<header class="header">
  <div class="eyebrow">AI 交互作业 · 第二次作业 · 提示词优化过程</div>
  <h1>从一句提问到一份可交付的实验设计<br>——提示词的 %(ms)s 次迭代全过程</h1>
  <p class="sub">本页不是完整聊天流水，而是从 %(n_turns)d 轮交互中抽出的一条主线：<b>第一个提示词没有产出想要的结果</b>——AI 答的是「哪道题比较容易」，而作业要的是「把第 6 题做完」。此后每一轮返工，都对应用户补上一条此前没写进提示词的约束。这里按<b>缺口 → 补约束 → 结果</b>的顺序逐条列出，每条都可回原始轮次核对。</p>

  <div class="stats">
    <div class="stat"><div class="v">%(n_turns)d</div><div class="k">总交互轮次</div></div>
    <div class="stat"><div class="v">%(ms)d</div><div class="k">关键修正节点</div></div>
    <div class="stat"><div class="v">6</div><div class="k">补齐的约束维度</div></div>
    <div class="stat"><div class="v">3</div><div class="k">返工级事件</div></div>
    <div class="stat"><div class="v">%(n_ai)d</div><div class="k">AI 文字回应</div></div>
    <div class="stat"><div class="v">%(n_tools)d</div><div class="k">工具调用次数</div></div>
  </div>

  <p class="note"><b>怎么读这份记录：</b>每个节点都写成「当时的提示词 → AI 给出的 → 差距在哪 → 补上的约束 → 结果」。引用的是<b>原始提示词原文</b>，可点右侧链接跳到完整流水核对。<b>对话中出现的第三方网址已去链接化</b>，个别指向盗版教材站与代做平台的站点名做了中性化替换，问答文字本身未作改动。</p>
</header>

<nav class="jump">
  <div class="jump-head">目录</div>
  <div class="jump-body">
    <a href="#s1">1 · 第一个提示词与它的失败</a>
    <a href="#s2">2 · 六项从未写进提示词的约束</a>
    <a href="#s3">3 · 关键修正链（%(ms)d 个节点）</a>
    <a href="#s4">4 · 三次返工级事件</a>
    <a href="#s5">5 · 质量机制是怎么建立的</a>
    <a href="#s6">6 · 可复用的提示词模板</a>
    <a href="#s7">7 · 完整对话流水</a>
  </div>
</nav>

<section class="sec" id="s1">
  <div class="sec-head"><h2>第一个提示词与它的失败</h2><span class="sec-no">第 1 轮 · 10-14 12:40</span></div>
  <p class="sec-desc">整段协作的第一条消息。用户把 7 道题的题面原样贴进来，末尾给出作业提交要求，然后问了一句「看下这几个内容你觉得哪一个比较容易」。</p>
  %(m1)s
  <p class="tx">这条提示词本身信息密度并不低——题目、提交要求、问题都齐了。问题在于它<b>只定义了要区分的对象，没定义要交付的东西</b>。AI 忠实地回答了字面问题，于是整段协作从第一步就跑偏了。</p>
</section>

<section class="sec" id="s2">
  <div class="sec-head"><h2>六项从未写进提示词的约束</h2><span class="sec-no">由 92 轮反推得出</span></div>
  <p class="sec-desc">把整条迭代链按维度归拢，会发现反复返工的根因其实是同一件事：<b>第一版提示词省略了下面六项</b>。每一项都在后面被单独补上，且补上之后同类问题没有再犯第二遍。</p>
  <div class="tw"><table class="tpl">
    <thead><tr><th>#</th><th>约束维度</th><th>第一版提示词</th><th>缺失导致的后果</th><th>补在哪一轮</th><th>当时的原话</th></tr></thead>
    <tbody>%(six)s</tbody>
  </table></div>
</section>

<section class="sec" id="s3">
  <div class="sec-head"><h2>关键修正链</h2><span class="sec-no">%(ms_rest)d 个节点 · 第 2 轮起按时间顺序</span></div>
  <p class="sec-desc">每一格都是一次可验证的修正：提示词缺了什么 → AI 因此做错了什么 → 用户用哪句话补上 → 结果如何。第一个节点（第一版提示词本身）已在上一节展开。</p>
  %(ms_html)s
</section>

<section class="sec" id="s4">
  <div class="sec-head"><h2>三次返工级事件</h2><span class="sec-no">整段推倒重来</span></div>
  <p class="sec-desc">不是打补丁，是把已经做完的产出推翻重做。这三次最能说明「提示词缺一条约束」的代价。</p>
  %(rework)s
</section>

<section class="sec" id="s5">
  <div class="sec-head"><h2>质量机制是怎么建立的</h2><span class="sec-no">第 63-66 轮</span></div>
  <p class="sec-desc">前面所有约束都是「这一次补上」。第 63-66 轮做的是另一件事：把一次性修补升级成流程约束。这一段是整条迭代链里最有价值的部分。</p>
  %(qm)s
</section>

<section class="sec" id="s6">
  <div class="sec-head"><h2>可复用的提示词模板</h2><span class="sec-no">从 92 轮里提炼</span></div>
  <p class="sec-desc">以下八条不是理论总结，每一条都对应上面某个节点里用户实际说过的原话，可直接套用到下一次任务上。</p>
  <div class="tw"><table class="tpl">
    <thead><tr><th>要补的约束</th><th>可直接照抄的说法</th><th>出处轮次</th></tr></thead>
    <tbody>%(tpl)s</tbody>
  </table></div>
</section>

<section class="sec" id="s7">
  <div class="sec-head"><h2>完整对话流水</h2><span class="sec-no">同站 full.html</span></div>
  <p class="sec-desc">本页是主线摘录。全部 %(n_turns)d 轮问答（%(n_user)d 次提问 / %(n_ai)d 条 AI 文字回应 / %(n_tools)d 次工具调用，时间跨度 %(span).1f 天）另有一份完整记录，按九个阶段分节编排，每轮标注该轮 AI 实际调用的工具次数与工具名。</p>
  <p class="tx"><a class="ref" href="full.html">打开完整对话流水 →</a></p>
</section>

<footer class="foot">
  <h3>记录说明</h3>
  <ul>
    <li>本页呈现的是「提示词迭代」这一条主线，不是全部对话；未入选的轮次多为执行细节、文件搬运或与本作业无关的工作区整理。</li>
    <li>所有引用均为原始提示词原文，节选处已用「（略）」标出；每条可跳转至完整流水核对。</li>
    <li>统计口径：轮次按一次「用户提问 → AI 回应」计；工具调用次数为该轮 AI 实际发起的工具调用总数。</li>
    <li>脱敏：全部第三方网址去链接化；少数指向盗版教材站、作业代做平台与搜索引擎结果页的站点名做中性化替换。除此之外问答文字未改动。</li>
    <li>配套提交件：《第 6 组 + 金行云（设计方案）.pdf》为实验设计方案本体，《第 6 组 + 金行云（第二次作业）.pdf》为提示词优化过程、错误复盘过程与关键记录。</li>
  </ul>
</footer>

</div>
</body>
</html>
""" % dict(css=CSS, ms=len(M), ms_rest=ms_rest, n_turns=n_turns, n_user=n_user, n_ai=n_ai, n_tools=n_tools,
           span=span, m1=render_milestone(M[0]), six="".join(six_rows), ms_html=ms_html,
           rework=rework_html, qm=qm_html, tpl=tpl_rows)

out = os.path.join(SITE, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(doc)
print("written:", out, os.path.getsize(out))
for bad in ["pdfcoffee", "chegg", "Chegg", "bing.com", "google.com", "duckduckgo", "archive.org"]:
    if bad in doc:
        print("!! risky residue:", bad)
print("http refs:", doc.count("http://"), doc.count("https://"))
