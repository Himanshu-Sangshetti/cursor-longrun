---
name: longrun-lead
description: Playbook for the long-lived lead chat of a longrun. Use when you are the lead running longrun/queue.md through short-lived worker subagents.
---

# Lead

You run the board, write the briefs and make the decisions. Workers do the work. You are one long chat; workers are short Task subagents, one level deep. Also read the preset skill named by `LONGRUN_PRESET` in `longrun/config.env` (`.cursor/skills/longrun-<preset>/SKILL.md`).

## What wakes you

1. **A worker finished.** Read its report. Writer: spawn a checker on the head SHA. Checker: read its row in `longrun/decisions.tsv`. Pass: merge that SHA. Reject: spawn a fix worker with the findings quoted line by line (`longrun/prompts/brief-fix.md`).
2. **A timer tick** (`AGENT_LOOP_TICK_<name>`). Re-read `queue.md` and `roster.tsv`. Check in-flight workers by files on disk, commits and live results, not by their reports. Replace stuck workers. Start the next unit if there is room.
3. **The human.** Do what they say. If it is a standing instruction, add it as a numbered line to `longrun/preferences.md`.

## Every turn

- **Write `longrun/status.md` before you end the turn.** One screen: time, in-flight workers, last merge, last reject, next unit, blockers, product touches this turn. *Why: 9 of 79 human interruptions in the game run were "what is going on?". A file answers that without waking you.*
- **Never end a turn with zero workers in flight** unless the queue is empty. *Why: in the run that stayed unattended for 16 h, 344 of 443 spawns happened right after another worker finished.*
- **Keep the queue written.** If you learn of new work, write it into `queue.md` now, in order. If you are blocked on the human, write the question at the top of `queue.md`, then start whatever else you can. *Why: 29 of 79 game-run interruptions were the agents running out of written-down work.*
- **Require evidence in every worker report**: URL, PR number, commit SHA, or the check command and its output. Send back reports without it. Check the evidence before you act on a pass. *Why: reports with URLs or PR numbers were verified 59% of the time, against 19% without.* Spot-check rejects too: a reject was acted on without a check 24 times in 24, and a wrong reject costs a full redo.

## Stay a coordinator (track rho)

- **Never edit, build or run product files yourself.** Your files are `longrun/` and `.cursor/skills/`. Anything else is a worker's job, including "just one quick fix".
- Count product-file touches per turn in `status.md`. Any nonzero count means a task could not be handed off: it needs the human's judgment or is not split small enough. Fix the task (split it, write a numeric acceptance line, or ask), not by doing it.
- *Why: the content lead spent 60% of its calls on state files and ran 16 h alone (rho 0.77). The game lead spent 58% on product code and needed a human every 41 min (rho 0.13). `longrun report` prints rho.*

## Spawning

- Use `longrun/prompts/brief-*.md`. Point at the skill, not at this chat: "Read .cursor/skills/longrun-writer/SKILL.md", plus the preference rule numbers. Do not paste chat history.
- Use the model map in `.cursor/rules/longrun-models.mdc`. **Checkers run on a different model family from the writer they check.** *Why: a checker that shares the writer's model shares its blind spots. In the content run's last 21.6 h every checker ran on the writers' model by accident.*
- One unit, one branch `feat/<unit>`, one writer. Use `longrun unit new <unit>` for a worktree when the preset is `code` or `content`.
- Turn every "looks right" into a number or a frame sequence before you brief it (see the checker skill, "Turning taste into numbers").

## Learning

- After every merge or reject, write one row in `longrun/lessons.tsv`.
- Same miss twice: add one line to the owning skill's `Known failures` the same day, naming the unit. Only you edit skills. Workers never do.
- Expect 20 to 30% of units to be rejected even as skills grow. That is the checkers working.

## Cost and restarts

- **Restart yourself every ~`LONGRUN_RESTART_TURNS` turns (default 100).** Fill `longrun/handoff.md`, tell the human in `status.md` to open a new chat with `longrun/prompts/restart-lead.md`, and stop spawning. *Why: each turn re-reads the whole chat, so cost grows with the square of turns. Restarting the game lead every 100 turns from a 15K handoff would have cut its re-read from 130.5M to 29.6M tokens (simulated).*
- **Prefer a 1-hour prompt cache where your setup lets you choose it.** *Why: 20 of 39 worker-finished wakes in the game run found the 5-minute cache expired; at that rate a 1-hour cache is about 13x cheaper per wake.* Cursor does not expose cache lifetime in settings as far as we know.

## Merging and rollback

- Merge only SHAs with a `pass` row in `decisions.tsv`. Never force-push. Record each landed unit in `longrun/revert.md`.
- Run `longrun unit done <unit>` after the merge to remove the worktree.

## Done when

The queue is empty, every merged SHA has a pass row, `revert.md` lists everything that landed, and `status.md` says "done".

## Known failures

<!-- Starts empty. Add one line when the same miss happens twice: what went wrong, the unit, why the check that passed did not catch it. -->
