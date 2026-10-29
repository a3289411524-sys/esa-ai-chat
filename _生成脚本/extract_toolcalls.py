# -*- coding: utf-8 -*-
"""
步骤 2：统计每一轮 AI 实际发起的工具调用次数与工具名 -> tools_by_turn.json

数据源：本地 session 目录下的 messages.jsonl 与 snapshots/*.jsonl
方法：把每条 toolCall 的时间戳按「轮次时间窗口」归到对应轮次
      （轮次边界取 qa.json 中每轮第一条消息的时间戳）
说明：只统计「调用了什么、调了几次」，不保留工具的原始输出内容。
"""
import json, os, bisect, collections
from config import RECORD_CUTOFF_TS

HERE = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = (r"C:\Users\32894\.minimax\v2\sessions\2026\10\14"
                r"\04-40-47-004-session_bXZzXzM1NWU4ZWRhYTI1MTQxNWE5NjYzZTA5NTYzZDNlM2U2")
QA = os.path.join(HERE, "qa.json")
OUT = os.path.join(HERE, "tools_by_turn.json")

files = []
for dp, dn, fn in os.walk(SESSION_DIR):
    for f in fn:
        if f.endswith(".jsonl"):
            files.append(os.path.join(dp, f))

events = []
for p in files:
    with open(p, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"toolCall"' not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            m = o.get("message", {})
            c = m.get("content")
            if not isinstance(c, list):
                continue
            ts = m.get("timestamp") or o.get("timestamp") or o.get("created_at")
            for x in c:
                if isinstance(x, dict) and x.get("type") == "toolCall":
                    events.append((ts, x.get("name")))
events = sorted(e for e in events if isinstance(e[0], int) and e[0] <= RECORD_CUTOFF_TS)

qa = json.load(open(QA, encoding="utf-8"))
turns = qa["turns"]
bounds = []
for i, t in enumerate(turns):
    s = t["items"][0]["ts"]
    e = turns[i + 1]["items"][0]["ts"] if i + 1 < len(turns) else 10 ** 18
    bounds.append((s, e))
starts = [x[0] for x in events]

res = []
for i, (s, e) in enumerate(bounds):
    names = collections.Counter()
    j = bisect.bisect_left(starts, s)
    while j < len(events) and events[j][0] < e:
        names[events[j][1]] += 1
        j += 1
    res.append({"turn": i + 1, "ts": s, "count": sum(names.values()), "tools": dict(names)})

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False)
print("tool events: %d | turns covered: %d/%d | total calls: %d -> %s"
      % (len(events), sum(1 for r in res if r["count"]), len(turns),
         sum(r["count"] for r in res), OUT))
