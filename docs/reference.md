# cursor-longrun reference

Details behind the [README](../README.md).

## Files

After `longrun init`, your repo has:

| Path | What | Written by |
| --- | --- | --- |
| `.cursor/rules/longrun-models.mdc` | role to model map (always applied) | you |
| `.cursor/skills/longrun-{lead,writer,checker,live-check}/SKILL.md` | one job description per role | you; the lead adds Known failures |
| `.cursor/skills/longrun-<preset>/SKILL.md` | preset rules | you; the lead |
| `.cursor/commands/longrun-start.md`, `longrun-status.md` | `/longrun-start` and `/longrun-status` | you |
| `longrun/config.env` | preset, tick, stale minutes, test/build commands, lead chat id | you |
| `longrun/queue.md` | goal, done-when, the order of work, questions for you | you, lead |
| `longrun/preferences.md` | your numbered standing rules | you, lead on your word |
| `longrun/status.md` | one-screen status, rewritten every turn | lead |
| `longrun/roster.tsv` | who is doing what (`id seat skill model state now next`) | lead, `longrun unit` |
| `longrun/decisions.tsv` | every pass and reject with its SHA | checkers |
| `longrun/lessons.tsv` | one row per merge or reject; `twice=yes` means patch a skill | lead |
| `longrun/revert.md` | pre-run SHA, what landed, how to undo it | you, lead |
| `longrun/handoff.md` | what a restarted lead needs | lead |
| `longrun/prompts/` | start, restart, writer, checker and fix briefs | you; lead fills them |
| `longrun/loop.sh` | the timer | you |
| `longrun/checks/` | check scripts (contract below) | you, checkers |

This repo: `bin/longrun` (the CLI), `install.sh`, `kit/` (base files), `presets/` (layered on top), `tools/trace_report.py` (measurement), `tests/smoke.sh`, `examples/hello-queue/` (state files mid-run), `examples/watch/` (launchd job).

### Check script contract

Every script in `longrun/checks/` prints evidence lines (what it measured, with the number), ends with `PASS <name>` or `FAIL <name>: <reason>`, and exits 0 on pass, 1 on fail, 2 on a setup error. Checkers treat a green script as the floor, not the pass: they quote measured numbers and look for what the script cannot see. The checker skill also shows how to turn taste into numbers ("feels wobbly" became "at most 2 yaw-rate sign changes per 10 s" plus frame sequences every 0.25 s).

## Measure your run

Find your lead chat, then report on it:

```bash
longrun report --list-chats            # recent top-level chats: created, workers, id, title
longrun report --chat <composerId> --since 2026-09-21T06:45:00+05:30 --until 2026-09-23T00:31:00+05:30
```

Set `LONGRUN_LEAD_CHAT` in `longrun/config.env` to drop `--chat`. Real output for the content run from the article (state folder name redacted):

```
lead chat   16cf6fa9-9dbb-4463-8611-b562fd41f154
window      2026-09-21 06:45 to 2026-09-23 00:31  (41.8 h)

H  unattended horizon   16.0 h  (2026-09-22 08:19 to 2026-09-23 00:21), ended by a human message

autonomy, five ways
  A_tool     99.9%   tool calls / (tool calls + human messages)   [44957 calls, 45 human]
  A_wake     92.9%   lead wakes not caused by a human            [633 wakes]
  A_call30   68.5%   tool calls >30 min after the last human message
  A_busy     80.1%   busy minutes >30 min after the last human message
  A_active   66.3%   busy minutes / wall-clock minutes            [1661 of 2506]

wake sources  subagent_done 393, timer_tick 178, human 45, other_notification 17

lead mix (6922 calls, state dir '<state-dir>')
  coordination      4307   62.2%
  implementation     899   13.0%
  spawn              443    6.4%
  other             1273   18.4%
  rho = coordination / (coordination + implementation) = 0.83

workers     321 found, 313 active in the window, 38035 tool calls
worker life median 5.4 min, p90 25.4, max 583.8
```

H and the five autonomy measures match the article. rho here comes from a simpler path-based classifier than the article's: it gives 0.83 for this run and 0.14 for the game run (article: 0.77 and 0.13). Use it to watch the trend within a run, not as an exact number.

How it reads the data: it opens `state.vscdb` read-only (macOS `~/Library/Application Support/Cursor/User/globalStorage/`, Linux `~/.config/Cursor/User/globalStorage/`, Windows `%APPDATA%\Cursor\User\globalStorage\`), reads only `composerData:*` and `bubbleId:*` keys, and never reads settings or auth keys. Human messages are not printed unless you pass `--show-human`, and long tokens are redacted. If Cursor has the file locked, copy it first: `sqlite3 -readonly <db> ".backup /tmp/copy.vscdb"` and pass `--db /tmp/copy.vscdb`. Cursor stores no billed token counts, so the tool reports no cost.

## Watch from outside the chat

`longrun watch` exits 1 and posts a notification when no state file has changed for `--stale-min` minutes (default `LONGRUN_STALE_MIN`, 30). Since the lead rewrites `status.md` every turn, a stale file means the lead stopped. Run it on a schedule:

```bash
# cron: every 10 minutes
*/10 * * * * /ABSOLUTE/PATH/TO/longrun -C /ABSOLUTE/PATH/TO/your-repo watch --stale-min 30 >> /tmp/longrun-watch.log 2>&1
```

On macOS use the launchd job in [`examples/watch/dev.longrun.watch.plist`](examples/watch/dev.longrun.watch.plist). A watcher on the same Mac catches a stuck lead or a dead loop, but it sleeps with the Mac, so it only tells you about a sleep after the Mac wakes. To catch that while it happens, run `longrun -C <repo> watch` from another machine over ssh.

## Cursor-specific vs portable

Not really. In Cursor, the harness (the agent loop, tools, context handling, subagents, the Task tool) is Cursor's agent. This repo is an orchestration kit on top of it: the roles, the files they share, the rules, the checks, and a CLI that sets them up and measures the result.

What is Cursor-specific:

- `.cursor/rules/*.mdc` (always-applied model map), `.cursor/skills/*/SKILL.md`, `.cursor/commands/*.md`.
- Spawning workers with the Task tool and a per-worker `model`.
- The timer: a background shell watched with `notify_on_output`, from Cursor's built-in loop skill (`/loop`). This is how the runs worked; it is not a documented public API, so it may change.
- `tools/trace_report.py`, which reads Cursor's local database layout.

What is portable: everything under `longrun/` (state files, briefs, checks, loop), the skills' text, and `longrun init/doctor/status/unit/watch`. To port to another agent CLI that has subagents: put the skills where that tool loads instructions (for example an `AGENTS.md` or its skills folder), replace "Task tool with model" in the lead skill with that tool's subagent call, and wake the lead with that tool's scheduler or a cron job that sends the tick prompt. `longrun report` will not work there; the measures (H and the five A's) are defined in the article so you can compute them from that tool's logs.

## What we could not verify

- **Slash commands.** Cursor's current docs describe skills and say `/migrate-to-skills` converts "slash commands" into skills with `disable-model-invocation: true`. They do not document `.cursor/commands/*.md` itself. The kit ships `/longrun-start` and `/longrun-status` there because Cursor has read commands from that folder, but we have not confirmed it in the current version. If they do not appear in your `/` menu, run `/migrate-to-skills` or paste `longrun/prompts/start-lead.md`.
- **Cache lifetime.** The article found a 1-hour prompt cache about 13x cheaper per wake than a 5-minute one. As far as we know Cursor does not let you choose; the lead skill says to prefer it where possible.
- **Nesting.** Cursor 2.5+ lets a subagent start one more level of subagents. The kit keeps workers at depth one on purpose; nothing enforces it except the skills.
- **Linux and Windows.** The smoke test passes locally on macOS; CI runs it on macOS and Ubuntu. Windows is untested (use WSL).

## FAQ

**Can I use it in an existing repo with its own `.cursor/` folder?** Yes. Kit files are prefixed `longrun-`; `init` refuses to overwrite anything unless you pass `--force`.

**Where do worktrees go?** `../<repo>-<unit>` by default. Change `LONGRUN_WORKTREE_DIR` or pass `--dir`. `longrun unit done` refuses to remove an unmerged branch unless you pass `--force`.

**How many workers at once?** Little's law: average workers alive = start rate x average life. The content run started about 7.4 an hour with a 20-minute mean life, so about 2.5 on average (peak 14). Start with two or three; on the `shared` preset, grow only while builds stay green.

**Do I have to use `caffeinate`?** `loop.sh` uses it on macOS automatically. Without it, the timer stops when the Mac sleeps, and so does the run.

**Why plain files and not a database?** Every agent can read and write them with the tools it already has, you can read them in a diff, and they go into git with the work.

**How do I see the state files mid-run?** `examples/hello-queue/` is a small filled example, three doc units about 50 minutes in.

## Development

```bash
bash tests/smoke.sh                       # init for every preset, doctor, status, unit, watch, checks
python3 -m py_compile tools/trace_report.py
shellcheck bin/longrun install.sh kit/longrun/*.sh kit/longrun/checks/*.sh presets/*/longrun/*/*.sh
```

