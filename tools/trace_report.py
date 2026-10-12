#!/usr/bin/env python3
"""Report how a long Cursor run actually went, from Cursor's local store.

Read-only: opens the SQLite file with mode=ro and only reads cursorDiskKV keys
composerData:<id> and bubbleId:<id>:<bubble>. It never touches ItemTable or auth keys.

  python3 tools/trace_report.py --chat <lead composerId> --state-dir <dir you keep state in>

If Cursor holds a lock, copy first:  sqlite3 -readonly <db> ".backup /tmp/copy.vscdb"  and pass --db.
"""
from __future__ import annotations
import argparse, json, os, re, sqlite3, statistics, sys
from datetime import datetime, timezone

DEFAULT_DB = "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
RED = re.compile(r"[A-Za-z0-9_\-\.]{32,}")
NOTIF = re.compile(r"^(kind|status|task_id|title):\s*(.*)$", re.M)
BUILD = re.compile(r"\b(npm|pnpm|yarn|make|cargo|gradle|xcodebuild|dotnet|tsc|vite|next|pytest|go)\s+(run\s+)?(build|test|compile|check)?|\bmake\b|\bcargo build\b", re.I)
EDIT_TOOLS = {"edit_file", "edit_file_v2", "write", "search_replace", "delete_file", "apply_patch"}
READ_TOOLS = {"read_file", "read_file_v2", "grep", "ripgrep", "ripgrep_raw_search", "glob_file_search", "list_dir", "list_dir_v2"}
SPAWN_TOOLS = {"task", "task_v2", "subagent", "spawn_agent"}
GAP_MIN = 30


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


def classify_user(text):
    """human | subagent_done | timer_tick | other_notification | goal_nudge | system | empty"""
    if "AGENT_LOOP_TICK" in text and "<system_notification" in text:
        return "timer_tick"
    if "<system_notification" in text:
        f = dict(NOTIF.findall(text))
        kind = f.get("kind", "")
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


def jload(v):
    try:
        return json.loads(v)
    except Exception:
        return None


def args_of(tf):
    a = tf.get("rawArgs") or tf.get("params") or ""
    if isinstance(a, str):
        a = jload(a) or {"_raw": a}
    return a if isinstance(a, dict) else {}


WINDOW = [0, 10**15]


def load_chat(con, cid):
    """Return (composer dict, list of (t_ms, bubble dict)) for one chat."""
    row = con.execute("select value from cursorDiskKV where key=?", (f"composerData:{cid}",)).fetchone()
    comp = jload(row[0]) if row and row[0] else {}
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
    return comp, bubs


def agent_ids_from_results(bubs):
    """Spawn calls carry the new chat id in their result (agentId); this is more complete than composerData."""
    ids = []
    for _, b in bubs:
        tf = b.get("toolFormerData") or {}
        r = tf.get("result")
        if isinstance(r, str) and "agentId" in r:
            r = jload(r)
        if isinstance(r, dict) and isinstance(r.get("agentId"), str) and r["agentId"]:
            ids.append(r["agentId"])
    return ids


def find_workers(con, lead, lead_bubs):
    """Workers = ids listed on the composer + ids returned by spawn calls. Depth one is the design,
    but sub-subagents listed on a worker are followed too."""
    def listed(cid):
        row = con.execute("select value from cursorDiskKV where key=?", (f"composerData:{cid}",)).fetchone()
        comp = jload(row[0]) if row and row[0] else {}
        return list(comp.get("subagentComposerIds", []) or []) + list(comp.get("subComposerIds", []) or [])
    seen, order = {lead}, []
    stack = listed(lead) + agent_ids_from_results(lead_bubs)
    while stack:
        cid = stack.pop()
        if cid in seen:
            continue
        seen.add(cid); order.append(cid)
        stack += listed(cid)
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


def busy_minutes(times, after_ms):
    """Minutes with any activity (1-minute buckets), and how many were after `after_ms`."""
    buckets = {t // 60000 for t in times if t}
    return len(buckets), sum(1 for m in buckets if m * 60000 > after_ms)


def longest_stretch(times, human_times):
    """Longest run with no human message and no idle gap over GAP_MIN."""
    ts = sorted(set(t for t in times if t))
    hs = sorted(human_times)
    best = (0, None, None, 0)
    start = prev = None
    n = 0
    def close():
        nonlocal best
        if start is not None and prev is not None and prev - start > best[0]:
            best = (prev - start, start, prev, n)
    import bisect
    for t in ts:
        new = start is None
        if not new:
            i = bisect.bisect_right(hs, prev)
            human_between = i < len(hs) and hs[i] <= t
            if t - prev > GAP_MIN * 60000 or human_between:
                close(); new = True
        if new:
            start, n = t, 0
        prev = t
        n += 1
    close()
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chat", required=True, help="composerId of the lead chat")
    ap.add_argument("--db", default=DEFAULT_DB, help="path to state.vscdb")
    ap.add_argument("--since", help="ISO time with offset, e.g. 2026-09-21T06:45:00+05:30 (ignore earlier bubbles)")
    ap.add_argument("--until", help="ISO time with offset (ignore later bubbles, e.g. follow-ups after the run)")
    ap.add_argument("--state-dir", default="state", help="folder name or path fragment of your state files")
    a = ap.parse_args()
    db = os.path.expanduser(a.db)
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    if a.since:
        WINDOW[0] = int(datetime.fromisoformat(a.since).timestamp() * 1000)
    if a.until:
        WINDOW[1] = int(datetime.fromisoformat(a.until).timestamp() * 1000)

    lead_comp, lead_bubs = load_chat(con, a.chat)
    if not lead_bubs:
        sys.exit("no bubbles found for that chat id")
    workers = find_workers(con, a.chat, lead_bubs)
    lead_calls = calls_of(lead_bubs, a.chat)
    worker_calls, life = [], []
    all_times = [t for t, _ in lead_bubs]
    for w in workers:
        _, wb = load_chat(con, w)
        worker_calls += calls_of(wb, w)
        ts = [t for t, _ in wb if t]
        all_times += ts
        if ts:
            life.append((max(ts) - min(ts)) / 60000)

    # user-role bubbles in the lead: who woke it
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
            human_text.append((t, red(re.sub(r"\s+", " ", b.get("text") or ""))[:140]))

    print(f"lead chat      {a.chat}")
    print(f"window         {fmt(min(all_times))} to {fmt(max(all_times))}  ({(max(all_times)-min(all_times))/3600000:.1f} h)")
    print(f"workers        {len(workers)} found, {len(life)} with activity")
    if life:
        print(f"worker life    median {statistics.median(life):.1f} min, p90 {sorted(life)[int(.9*(len(life)-1))]:.1f}, max {max(life):.1f}")

    print(f"\nhuman messages {len(human_times)}")
    for t, s in human_text[:60]:
        print(f"  {fmt(t)}  {s}")
    if len(human_text) > 60:
        print(f"  ... {len(human_text)-60} more")

    n_l, n_w = len(lead_calls), len(worker_calls)
    print(f"\ntool calls (deduped by toolCallId): {n_l+n_w}  lead {n_l}  workers {n_w}")

    total_wake = sum(wake.values())
    order = ["human", "subagent_done", "timer_tick", "other_notification", "goal_nudge"]
    print(f"\nlead wakes     {total_wake}: " + ", ".join(f"{k} {wake.get(k,0)}" for k in order if wake.get(k, 0)))
    if total_wake:
        print(f"  share not woken by a human: {100*(total_wake-wake.get('human',0))/total_wake:.1f}%")

    all_call_times = [c["t"] for c in lead_calls + worker_calls]
    hs = sorted(human_times)
    import bisect
    def since_human(t):
        i = bisect.bisect_right(hs, t)
        return (t - hs[i-1]) / 60000 if i else None
    unatt = sum(1 for t in all_call_times if (since_human(t) or 0) > GAP_MIN)
    print("\nautonomy")
    if human_times:
        print(f"  tool calls per human message: {(n_l+n_w)/len(human_times):.0f}")
    print(f"  tool calls run >{GAP_MIN} min after the latest human message: {100*unatt/max(1,len(all_call_times)):.1f}%")
    print(f"  tool-call share by agents other than the lead: {100*n_w/max(1,n_l+n_w):.1f}%")
    bm_all = {t // 60000 for t in all_times if t}
    bm_un = {m for m in bm_all if (since_human(m * 60000) or 0) > GAP_MIN}
    print(f"  busy minutes: {len(bm_all)} total, {len(bm_un)} ({100*len(bm_un)/max(1,len(bm_all)):.1f}%) more than {GAP_MIN} min after a human message")
    span, s, e, n = longest_stretch(all_times, human_times)
    if s:
        print(f"  longest unattended busy stretch: {span/3600000:.1f} h ({fmt(s)} to {fmt(e)}), {n} bubbles")

    sd = a.state_dir.strip("/")
    mix = dict(coordination=0, implementation=0, spawn=0, other=0)
    for c in lead_calls:
        n_ = c["name"]; p = c["path"] + " " + c["cmd"]
        if n_ in SPAWN_TOOLS or n_.startswith("task"):
            mix["spawn"] += 1
        elif (n_ in EDIT_TOOLS or n_ in READ_TOOLS or n_.startswith("run_terminal")) and (sd in p or "/skills/" in p or "SKILL.md" in p):
            mix["coordination"] += 1
        elif n_ in EDIT_TOOLS or (n_.startswith("run_terminal") and BUILD.search(c["cmd"])):
            mix["implementation"] += 1
        else:
            mix["other"] += 1
    print(f"\nlead tool-call mix ({n_l} calls; state dir '{sd}')")
    for k, v in mix.items():
        print(f"  {k:15s} {v:6d}  {100*v/max(1,n_l):5.1f}%")
    names = {}
    for c in lead_calls:
        names[c["name"]] = names.get(c["name"], 0) + 1
    print("  top tools: " + ", ".join(f"{k} {v}" for k, v in sorted(names.items(), key=lambda x: -x[1])[:8]))


if __name__ == "__main__":
    main()
