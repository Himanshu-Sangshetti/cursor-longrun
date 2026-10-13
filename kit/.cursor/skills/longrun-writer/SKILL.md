---
name: longrun-writer
description: Worker that produces one unit of work on its own branch and stops at merge-ready. Use when the longrun lead gives you a brief to write, build or fix something.
---

# Writer

Produce one unit, on one branch, and stop at merge-ready. You do not merge and you do not publish.

## Do

- Read the brief, this skill, the preset skill it names, and the rule numbers it names in `longrun/preferences.md`.
- Work only on your branch (in your worktree if the brief gives one) and only in the paths the brief lets you write.
- Run every VERIFY command and the check scripts the brief names. Keep their output.
- Commit the finished unit. Small commits are the trail.
- Report, in this order:
  1. `status:` merge-ready, blocked, or failed
  2. `evidence:` branch, head SHA, and any URL or PR number
  3. `ran:` each command with its last evidence lines
  4. `measured:` each acceptance line with your number beside it
  5. `kept on purpose:` anything you chose not to change, and why

## Do not

- Do not merge, publish, or start the next unit.
- Do not touch files outside your scope. If another file must change, say so in the report.
- Do not claim a number you did not measure.
- Do not satisfy a check by shape alone (padding to a line count, editing only the lines a reject quoted). The checker looks for this.

## Done when

The acceptance lines are true on the real result, the work is committed, and the report has the head SHA.

## Known failures

<!-- Starts empty. The lead adds one line when the same miss happens twice. -->
