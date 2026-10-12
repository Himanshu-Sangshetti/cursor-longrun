# long-horizon-harness

A small Cursor template for running one long task for many hours: one lead chat, short worker subagents, state in plain files, separate checkers.

For people who want to hand an agent a big queue of work, go to bed, and wake up to merged, checked results. It comes from a real 41.8 hour run. See the article: <link to article>.

## Quick start

1. Copy `.cursor/`, `state/`, `prompts/`, `scripts/` and `tools/` into your project.
2. Fill in `state/queue.md` (the order of work) and `state/preferences.md` (your rules). Set the model names in `.cursor/rules/models.mdc`.
3. Open a Cursor agent chat. Paste `prompts/start-lead.md`. That chat is the lead.
4. Approve the permissions the lead asks for, and write `state/revert.md` (what the lead may merge, and how to undo it).
5. Start `scripts/loop.sh 600 <name>` as a background shell with `notify_on_output` and the pattern `^AGENT_LOOP_TICK_<name>`. Then leave.

## How it fits together

```
                human (rarely)
                     |
                     v
   timer tick --> [ LEAD chat ] <-- worker finished
 (scripts/loop.sh)   |   ^
                     |   | reports
        briefs       v   |
          +--> writer --+        writers: fast model, one branch each
          +--> checker --+       checkers: other model family, measure
          +--> live-check +      opens the real result like a user
                     |
                     v
   state/  preferences  queue  roster  lessons  decisions  revert
   (small plain files; the lead and checkers write, everyone reads)
   .cursor/skills/  <-- the lead patches a skill when a failure repeats
```

## File map

| File | Purpose | Written by | Read by |
| --- | --- | --- | --- |
| `README.md` | this page | you | you |
| `.cursor/rules/models.mdc` | role to model map | you | lead |
| `.cursor/skills/lead/SKILL.md` | lead playbook | you, lead (patches) | lead |
| `.cursor/skills/writer/SKILL.md` | writer job | you, lead (patches) | writers |
| `.cursor/skills/checker/SKILL.md` | checker job | you, lead (patches) | checkers |
| `.cursor/skills/live-check/SKILL.md` | open the live result | you, lead (patches) | live-checkers |
| `state/preferences.md` | your numbered rules | you, lead (on your word) | everyone |
| `state/queue.md` | ordered work | you, lead | lead |
| `state/roster.tsv` | who is doing what | lead | lead, you |
| `state/lessons.tsv` | one row per merge or reject | lead | lead |
| `state/decisions.tsv` | pass and reject verdicts with SHAs | checkers | lead, you |
| `state/revert.md` | what landed, how to undo | you, lead | you |
| `prompts/start-lead.md` | opening message for the lead | you | lead |
| `prompts/brief-*.md` | writer, checker and fix briefs | lead (fills in) | workers |
| `scripts/loop.sh` | timer tick, keeps the Mac awake | you | Cursor |
| `tools/trace_report.py` | measure a finished run | you | you |

## The rules that matter

- The lead never edits product files. Workers do.
- Never end a turn with zero workers in flight unless the queue is empty.
- Workers are short and one level deep. They do not spawn workers.
- Write the order of work in `queue.md` before you leave.
- Every unit is checked by a different role, on a different model family.
- A green script is the floor, not the pass. The checker measures for itself.
- One branch per unit, one writer per branch.
- Briefs point at skills, not at chat history.
- Same failure twice: patch the owning skill the same day.
- Commit state files. Write `revert.md` and grant permissions before you sleep.

## What the numbers looked like in the real run

- 16 hours busy without a human message.
- 308 workers, median life 5.4 minutes.
- Checkers were 33.5% of worker calls but 13% of context.
- 2 merge conflicts in 308 workers, with one branch per unit.
- 21 of the 25 rules came from the human, not the agents.

Details and caveats: <link to article>.

## Measure your own run

```
python3 tools/trace_report.py --chat <lead composerId> --state-dir state
```

It opens Cursor's local store (`state.vscdb`) read-only and prints human messages, tool calls (lead vs workers), what woke the lead, how much ran unattended, the longest unattended stretch, the lead's tool-call mix, and worker count and median life. Use `--db` for another path, `--since` and `--until` to cut a window. It only reads chat keys, never settings or auth keys, and redacts long tokens. If Cursor has the file locked, copy it first: `sqlite3 -readonly <db> ".backup /tmp/copy.vscdb"`.

## License

MIT. See `LICENSE`.
