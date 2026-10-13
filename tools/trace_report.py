#!/usr/bin/env python3
"""Measure a long Cursor run from Cursor's local store (state.vscdb).

Read-only: opens the SQLite file with mode=ro and only reads cursorDiskKV keys
composerData:<id> and bubbleId:<id>:<bubble>. It never reads ItemTable or auth keys.

  python3 tools/trace_report.py --list-chats
  python3 tools/trace_report.py --chat <lead composerId> --state-dir longrun

Prints the unattended horizon H, five autonomy measures, what woke the lead,
the lead's coordination share (rho) and worker count and life.
If Cursor holds a lock, copy first:  sqlite3 -readonly <db> ".backup /tmp/copy.vscdb"  and pass --db.
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import platform
import re
import sqlite3
import statistics
import sys
from datetime import datetime, timezone

GAP_MIN = 30
RED = re.compile(r"[A-Za-z0-9_\-\.]{32,}")
NOTIF = re.compile(r"^(kind|status|task_id|title):\s*(.*)$", re.M)
BUILD = re.compile(r"\b(npm|pnpm|yarn|bun|make|cargo|gradle|xcodebuild|dotnet|tsc|vite|next|pytest|go|npx|node|tsx|vercel|deploy|publish)\b", re.I)
EDIT_TOOLS = {"edit_file", "edit_file_v2", "write", "search_replace", "delete_file", "apply_patch"}
READ_TOOLS = {"read_file", "read_file_v2", "grep", "ripgrep", "ripgrep_raw_search", "glob_file_search", "list_dir", "list_dir_v2"}
SPAWN_TOOLS = {"task", "task_v2", "subagent", "spawn_agent"}
COORD_MARKERS = ("/skills/", "SKILL.md", "/.cursor/", "agent-transcripts", "/subagents/")
WINDOW = [0, 10**15]


def default_db():
    home = os.path.expanduser("~")
    if platform.system() == "Darwin":
        return os.path.join(home, "Library/Application Support/Cursor/User/globalStorage/state.vscdb")
    if os.name == "nt":
        return os.path.join(os.environ.get("APPDATA", home), "Cursor/User/globalStorage/state.vscdb")
    return os.path.join(home, ".config/Cursor/User/globalStorage/state.vscdb")


def red(s):
    return RED.sub("[REDACTED]", s or "")


def ms(v):
    if isinstance(v, (int, float)) and v > 0:
        return int(v)
    if isinstance(v, str) and v:
        try:
            return int(datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp() * 1000)
        except ValueError:
            return None
    return None


def fmt(t):
    return datetime.fromtimestamp(t / 1000, timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


def jload(v):
    try:
        return json.loads(v)
    except Exception:
        return None


def classify_user(text):
    """human | subagent_done | timer_tick | other_notification | goal_nudge | system | empty"""
    if "AGENT_LOOP_TICK" in text and "<system_notification" in text:
        return "timer_tick"
    if "<system_notification" in text:
        kind = dict(NOTIF.findall(text)).get("kind", "")
        if kind == "subagent":
            return "subagent_done"
        if kind == "shell" and "has notified" in text[:600]:
            return "timer_tick"
        return "other_notification"
    if 'source="goal"' in text:
        return "goal_nudge"
    if "Briefly inform the user about the task result" in text:
        return "subagent_done"
    body = re.sub(r"<timestamp>.*?</timestamp>", "", text, flags=re.S).strip()
    if not body:
        return "empty"
    if body.startswith("<") and "<user_query>" not in body:
        return "system"
    return "human"


def args_of(tf):
    a = tf.get("rawArgs") or tf.get("params") or ""
    if isinstance(a, str):
        a = jload(a) or {"_raw": a}
    return a if isinstance(a, dict) else {}


def composer(con, cid):
    row = con.execute("select value from cursorDiskKV where key=?", (f"composerData:{cid}",)).fetchone()
    return (jload(row[0]) if row and row[0] else None) or {}


def children(comp):
    return list(comp.get("subagentComposerIds") or []) + list(comp.get("subComposerIds") or [])


def load_chat(con, cid):
    """Bubbles of one chat inside WINDOW, as a sorted list of (t_ms, bubble)."""
    bubs = []
    for _, v in con.execute("select key,value from cursorDiskKV where key>=? and key<?",
                            (f"bubbleId:{cid}:", f"bubbleId:{cid};")):
        b = jload(v) if v else None
        if not b:
            continue
        t = ms(b.get("createdAt")) or ms(b.get("startedAtMs")) or 0
        if WINDOW[0] <= t <= WINDOW[1]:
            bubs.append((t, b))
    bubs.sort(key=lambda x: x[0])
    return bubs


def spawned_ids(bubs):
    """Spawn results carry the new chat id (agentId); more complete than composerData."""
    ids = []
    for _, b in bubs:
        r = (b.get("toolFormerData") or {}).get("result")
        if isinstance(r, str) and "agentId" in r:
            r = jload(r)
        if isinstance(r, dict) and isinstance(r.get("agentId"), str) and r["agentId"]:
            ids.append(r["agentId"])
    return ids


def find_workers(con, lead, lead_bubs):
    seen, order = {lead}, []
    stack = children(composer(con, lead)) + spawned_ids(lead_bubs)
    while stack:
        cid = stack.pop()
        if cid in seen:
            continue
        seen.add(cid)
        order.append(cid)
        stack += children(composer(con, cid))
    return order


def calls_of(bubs, cid):
    """Tool calls deduped by toolCallId (the store keeps one bubble per streaming state)."""
    out = {}
    for t, b in bubs:
        tf = b.get("toolFormerData") or {}
        if not tf:
            continue
        key = tf.get("toolCallId") or f"{cid}:{t}:{tf.get('name')}"
        a = args_of(tf)
        path = str(a.get("path") or a.get("relativeWorkspacePath") or a.get("target_file") or "")
        cmd = str(a.get("command") or "")
        prev = out.get(key)
        row = dict(t=prev["t"] if prev and prev["t"] else t, name=tf.get("name") or "", path=path, cmd=cmd)
        if prev:
            row["path"], row["cmd"] = row["path"] or prev["path"], row["cmd"] or prev["cmd"]
        out[key] = row
    return list(out.values())


def longest_stretch(times, human_times):
    """H: longest run with no human message and no activity gap over GAP_MIN. Returns (ms, start, end, why_it_ended)."""
    ts, hs = sorted(set(t for t in times if t)), sorted(human_times)
    best = (0, None, None, "")
    start = prev = None
    for t in ts:
        if start is not None:
            i = bisect.bisect_right(hs, prev)
            human = i < len(hs) and hs[i] <= t
            if human or t - prev > GAP_MIN * 60000:
                if prev - start > best[0]:
                    best = (prev - start, start, prev, "a human message" if human else f"an idle gap over {GAP_MIN} min")
                start = None
        if start is None:
            start = t
        prev = t
    if start is not None and prev - start > best[0]:
        best = (prev - start, start, prev, "the end of the window (still running)")
    return best


def lead_mix(calls, state_dir):
    mix = dict(coordination=0, implementation=0, spawn=0, other=0)
    for c in calls:
        n, target = c["name"], c["path"] + " " + c["cmd"]
        is_shell = n.startswith("run_terminal")
        coord = state_dir in target or any(m in target for m in COORD_MARKERS)
        if n in SPAWN_TOOLS or n.startswith("task"):
            mix["spawn"] += 1
        elif (n in EDIT_TOOLS or n in READ_TOOLS or is_shell) and coord:
            mix["coordination"] += 1
        elif n in EDIT_TOOLS or (n in READ_TOOLS and c["path"]) or (is_shell and BUILD.search(c["cmd"])):
            mix["implementation"] += 1
        else:
            mix["other"] += 1
    return mix


def list_chats(con, limit):
    rows, kids = [], set()
    for _, v in con.execute("select key,value from cursorDiskKV where key>='composerData:' and key<'composerData;'"):
        d = jload(v) if v else None
        if not d or not d.get("composerId"):
            continue
        kids.update(children(d))
        rows.append(d)
    rows = [d for d in rows if d["composerId"] not in kids]
    rows.sort(key=lambda d: ms(d.get("createdAt")) or 0, reverse=True)
    print(f"{'created':16s}  {'workers':>7s}  {'composerId':36s}  title")
    for d in rows[:limit]:
        t = ms(d.get("createdAt"))
        title = re.sub(r"\s+", " ", d.get("name") or "(untitled)")[:60]
        print(f"{fmt(t) if t else '?':16s}  {len(children(d)):7d}  {d['composerId']:36s}  {red(title)}")


def pct(x):
    return f"{100 * x:5.1f}%"


def report(con, a):
    if a.since:
        WINDOW[0] = int(datetime.fromisoformat(a.since).timestamp() * 1000)
    if a.until:
        WINDOW[1] = int(datetime.fromisoformat(a.until).timestamp() * 1000)
    lead_bubs = load_chat(con, a.chat)
    if not lead_bubs:
        sys.exit("no messages found for that chat id in that window (try --list-chats)")
    workers = find_workers(con, a.chat, lead_bubs)
    lead_calls = calls_of(lead_bubs, a.chat)
    worker_calls, life, all_times = [], [], [t for t, _ in lead_bubs if t]
    for w in workers:
        wb = load_chat(con, w)
        worker_calls += calls_of(wb, w)
        ts = [t for t, _ in wb if t]
        all_times += ts
        if ts:
            life.append((max(ts) - min(ts)) / 60000)

    wake, human_times, human_text = {}, [], []
    for t, b in lead_bubs:
        if b.get("type") != 1:
            continue
        k = classify_user(b.get("text") or "")
        if k in ("empty", "system"):
            continue
        wake[k] = wake.get(k, 0) + 1
        if k == "human":
            human_times.append(t)
            human_text.append((t, red(re.sub(r"\s+", " ", b.get("text") or ""))[:120]))

    hs = sorted(human_times)

    def since_human(t):
        i = bisect.bisect_right(hs, t)
        return (t - hs[i - 1]) / 60000 if i else float("inf")

    T, M = len(lead_calls) + len(worker_calls), len(human_times)
    W = sum(wake.values())
    t0 = WINDOW[0] if a.since else min(all_times)
    t1 = WINDOW[1] if a.until else max(all_times)
    D = max(1, (t1 - t0) / 60000)
    busy = {t // 60000 for t in all_times}
    busy30 = {m for m in busy if since_human(m * 60000) > GAP_MIN}
    call_times = [c["t"] for c in lead_calls + worker_calls if c["t"]]
    call30 = sum(1 for t in call_times if since_human(t) > GAP_MIN)
    span, s, e, why = longest_stretch(all_times, human_times)
    mix = lead_mix(lead_calls, a.state_dir.strip("/"))
    rho = mix["coordination"] / max(1, mix["coordination"] + mix["implementation"])

    print(f"lead chat   {a.chat}")
    print(f"window      {fmt(t0)} to {fmt(t1)}  ({D / 60:.1f} h)")
    print()
    if s:
        print(f"H  unattended horizon   {span / 3600000:.1f} h  ({fmt(s)} to {fmt(e)}), ended by {why}")
    print()
    print("autonomy, five ways")
    print(f"  A_tool    {pct(T / max(1, T + M))}   tool calls / (tool calls + human messages)   [{T} calls, {M} human]")
    print(f"  A_wake    {pct(1 - wake.get('human', 0) / max(1, W))}   lead wakes not caused by a human            [{W} wakes]")
    print(f"  A_call30  {pct(call30 / max(1, len(call_times)))}   tool calls >{GAP_MIN} min after the last human message")
    print(f"  A_busy    {pct(len(busy30) / max(1, len(busy)))}   busy minutes >{GAP_MIN} min after the last human message")
    print(f"  A_active  {pct(len(busy) / D)}   busy minutes / wall-clock minutes            [{len(busy)} of {D:.0f}]")
    print()
    order = ["subagent_done", "timer_tick", "human", "other_notification", "goal_nudge"]
    print("wake sources  " + ", ".join(f"{k} {wake[k]}" for k in order if wake.get(k)))
    print()
    print(f"lead mix ({len(lead_calls)} calls, state dir '{a.state_dir}')")
    for k, v in mix.items():
        print(f"  {k:15s} {v:6d}  {pct(v / max(1, len(lead_calls)))}")
    print(f"  rho = coordination / (coordination + implementation) = {rho:.2f}")
    print()
    print(f"workers     {len(workers)} found, {len(life)} active in the window, {len(worker_calls)} tool calls")
    if life:
        p90 = sorted(life)[int(0.9 * (len(life) - 1))]
        print(f"worker life median {statistics.median(life):.1f} min, p90 {p90:.1f}, max {max(life):.1f}")
    if a.show_human:
        print(f"\nhuman messages ({M}, long tokens redacted)")
        for t, txt in human_text:
            print(f"  {fmt(t)}  {txt}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chat", help="composerId of the lead chat")
    ap.add_argument("--db", default=default_db(), help="path to state.vscdb")
    ap.add_argument("--since", help="ISO time with offset, e.g. 2026-09-21T06:45:00+05:30")
    ap.add_argument("--until", help="ISO time with offset (ignore later messages)")
    ap.add_argument("--state-dir", default="longrun", help="path fragment of your state folder (for rho)")
    ap.add_argument("--list-chats", action="store_true", help="list recent top-level chats and exit")
    ap.add_argument("--limit", type=int, default=15, help="rows for --list-chats")
    ap.add_argument("--show-human", action="store_true", help="also print human messages (redacted)")
    a = ap.parse_args()
    db = os.path.expanduser(a.db)
    if not os.path.exists(db):
        sys.exit(f"no Cursor database at {db} (pass --db)")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    if a.list_chats:
        list_chats(con, a.limit)
    elif a.chat:
        report(con, a)
    else:
        ap.error("pass --chat <composerId> or --list-chats")


if __name__ == "__main__":
    main()
