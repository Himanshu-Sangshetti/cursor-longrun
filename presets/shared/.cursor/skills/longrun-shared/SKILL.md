---
name: longrun-shared
description: Preset rules for a longrun where every worker edits one shared codebase that must keep building (games, apps without per-unit branches). Use with the longrun skills when LONGRUN_PRESET=shared.
---

# Preset: shared

All workers edit one working tree. Units cannot be isolated on branches, so two rules hold the run together: file ownership (`longrun/owners.md`) and one build gate (`longrun/checks/build.sh`).

## Lead

- Every brief repeats the worker's row from `longrun/owners.md` as `YOU OWN:` and `Do NOT edit:`.
- Start small waves. Ownership keeps workers out of each other's files but not out of each other's way: in one real run, the first wave of eight parallel workers on one project hit 15 failed compiles, almost all inside another worker's half-written file. Start with two or three workers and grow while builds stay green.
- Sequence work on shared files (entry points, game controller, global UI). Never run two workstreams on one file at once.
- Write the order of work in `longrun/queue.md` after every wave. The run without one needed a human every 41 minutes.

## Writer

- Run `longrun/checks/build.sh` before you start and after every meaningful edit. Commit only states that print `BUILD OK`.
- **Collision rule: never fix someone else's compile error.** If the build fails in a file you do not own, wait 60 s and retry. After 3 retries, stop and report the error, the file and its owner from `owners.md`.
- Keep half-written code out of shared paths: build new code in your own files and switch it on last.

## Checker

- `BUILD OK` is the floor. Measure the behaviour the brief names, with numbers and frame sequences where motion or feel is involved (see "Turning taste into numbers" in the checker skill).
- Check that the writer touched only its owned globs: `git diff --name-only <from>..<sha>`.
