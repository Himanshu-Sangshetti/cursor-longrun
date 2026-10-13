---
name: longrun-code
description: Preset rules for a longrun over independent code units, one branch and worktree each. Use with the longrun lead, writer and checker skills when LONGRUN_PRESET=code.
---

# Preset: code

Units are independent changes (features, fixes, migrations, docs) that each land as one branch.

## Lead

- Before briefing a unit, run `longrun unit new <unit>`. It creates `feat/<unit>` and a worktree; put the worktree path in the brief.
- Spawn writers in parallel only for units that touch different folders. Two units on one file go in sequence.
- After a pass, merge the SHA into the base branch, record it in `longrun/revert.md`, then run `longrun unit done <unit>`.

## Writer

- Work only inside your worktree. Run `longrun/checks/tests.sh <worktree>` before you report, and paste its evidence lines.
- Add or update tests for what you changed. Do not delete or skip a failing test to get green; report it instead.

## Checker

- In the writer's worktree at the reported SHA, run `longrun/checks/tests.sh <worktree>` and `longrun/checks/diff-scope.sh <base> <sha> <allowed globs>`.
- Green is the floor. Then read the diff: does it do what the GOAL says, for the cases the tests do not cover? Look for tests that were weakened, skipped or deleted.
