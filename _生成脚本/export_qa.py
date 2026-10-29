# -*- coding: utf-8 -*-
"""
步骤 1：把本 session 的问答流水从本地消息库导出为 qa.json

数据源：C:\\Users\\32894\\.minimax\\v2\\sqlite\\runtime-state.sqlite
表：local_runtime_message_rows
说明：只导出「用户提问」与「AI 文字回应」两类消息；工具调用与思考过程不落在这里，
      工具调用由 extract_toolcalls.py 单独统计（只保留次数与工具名，不保留原始输出）。
"""
import sqlite3, json, os, collections
from config import RECORD_CUTOFF_TS

HERE = os.path.dirname(os.path.abspath(__file__))
DB = r"C:\Users\32894\.minimax\v2\sqlite\runtime-state.sqlite"
SESSION_ID = "mvs_355e8edaa251415a9663e09563d3e3e6"
OUT = os.path.join(HERE, "qa.json")

con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
cur = con.cursor()
rows = cur.execute(
    "SELECT role, turn_id, created_at_ms, data_json FROM local_runtime_message_rows "
    "WHERE session_id=? ORDER BY created_at_ms", (SESSION_ID,)).fetchall()

turns = collections.OrderedDict()
n_user = n_ai = 0
for role, turn_id, ts, dj in rows:
    if ts > RECORD_CUTOFF_TS:
        continue
    d = json.loads(dj)
    mt, mc = d.get("msg_type"), d.get("msg_content")
    if not isinstance(mc, str):
        continue
    if role == "user" and mt == 1:
        kind = "user"; n_user += 1
    elif role == "assistant" and mt in (1, 2):
        kind = "assistant"; n_ai += 1
    else:
        continue
    key = turn_id or ("t%d" % ts)
    turns.setdefault(key, {"turn": len(turns) + 1, "items": []})
    turns[key]["items"].append({"k": kind, "ts": ts, "t": mc})
    turns[key]["ts"] = ts

out = {"session": SESSION_ID, "n_turns": len(turns), "n_user": n_user,
       "n_assistant": n_ai, "turns": list(turns.values())}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

total = sum(len(i["t"]) for t in out["turns"] for i in t["items"])
print("turns: %d | user: %d | assistant: %d | chars: %d -> %s"
      % (len(turns), n_user, n_ai, total, OUT))
con.close()
