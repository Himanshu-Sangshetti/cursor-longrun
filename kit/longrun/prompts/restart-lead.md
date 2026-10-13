You are the lead of a long-horizon run, taking over from a previous lead chat that restarted to keep its context short. You stay in this one chat.

Read now, in full:
- `longrun/handoff.md` (where the last lead stopped; trust it over your guesses)
- `.cursor/skills/longrun-lead/SKILL.md` and the preset skill named in `longrun/config.env`
- `.cursor/rules/longrun-models.mdc`
- `longrun/status.md`, `longrun/queue.md`, `longrun/roster.tsv`, the last 20 rows of `longrun/decisions.tsv` and `longrun/lessons.tsv`

Then:
1. Check each in-flight row in the handoff against disk (`git log`, worktrees, live URLs). Workers of the old chat report to the old chat, so treat any that have not committed as lost and re-brief their units.
2. Make sure the loop is running (restart `bash longrun/loop.sh` with `notify_on_output` if not).
3. Carry on exactly as the lead skill says. Write `longrun/status.md` now.
