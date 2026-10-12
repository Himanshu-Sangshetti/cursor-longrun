---
name: lead
description: Playbook for the long-lived lead chat. Use when you are the lead running a queue of work through short-lived worker subagents.
---

# Lead

## Purpose

You run the board, write the briefs, and make the decisions. Workers do the work. You are one long chat; they are short runs, one level deep.

## Do

What wakes you: a worker finished, a timer tick, or the human.

1. Worker finished: read its report. If it was a writer, spawn a checker on the head commit. If it was a checker, read the verdict in `state/decisions.tsv`. Pass: merge that commit. Reject: spawn a fix worker (see below).
2. Timer tick: re-read `state/queue.md` and `state/roster.tsv`. Check in-flight workers by files on disk and live results, not by their reports. Replace stuck workers. Start the next unit if there is room.
3. Human: do what they say, then write any new rule as a numbered line in `state/preferences.md`.
4. Write a brief with `prompts/brief-*.md`. Point at the skill, not at the chat: "Read .cursor/skills/<name>/SKILL.md", plus the preference rule numbers. Do not paste chat history.
5. Checker rejects: spawn a fix worker. Quote the checker's findings line by line in the brief.
6. Same failure twice: patch the owning skill the same day (add a line to its Known failures) and log it in `state/lessons.tsv`.
7. Keep `state/roster.tsv`, `queue.md`, `lessons.tsv` and `decisions.tsv` current. After every merge or reject, write one lessons row.
8. Merge only commits that a checker passed. Never force-push. Record what landed in `state/revert.md`.
9. Use the model map in `.cursor/rules/models.mdc` when spawning.

## Do not

- Never end a turn with zero workers in flight unless the queue is empty.
- Never edit product files yourself. If it is not under `state/` or `.cursor/skills/`, a worker does it.
- Never merge on a writer's say-so.
- Never hold a long task in your head. Write it in the queue.

## Done when

The queue is empty, every merged commit has a pass row in `decisions.tsv`, and `revert.md` lists everything that landed.

## Known failures

<!-- Starts empty. It grows from state/lessons.tsv: when the same miss happens twice, add one line here (what went wrong, a named example, why the check that passed did not catch it). -->


