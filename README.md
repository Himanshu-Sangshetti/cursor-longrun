# cursor-longrun

Run one task in Cursor for many hours without you.

This is the setup from my article **[Cursor for Autonomous Long Horizon Tasks](https://x.com/himanshutwtxs/status/2110027536088596486)**, packaged so you can drop it into your own repo. It produced two runs: a content factory that ran 42 hours (16 of them straight with no human input, 308 subagents, ~1.8k commits) and a game build of about 170 hours.

It is not a harness. Cursor's agent is the harness. This repo is what goes on top of it: the roles, the shared state files, the rules, the checks, and a small CLI (`longrun`) that sets them up, tells you when the run is ready to leave alone, and measures it afterwards.

## The setup in one picture

- **Lead:** one Cursor chat that plans, writes briefs, starts workers and merges. It never edits product files.
- **Workers:** short-lived subagents, one job each, on a fast model.
- **Checkers:** separate workers on a different model family whose only job is pass or reject, with numbers.
- **State files:** small plain files in `longrun/` (queue, roster, status, decisions, lessons, revert) that every agent reads and writes.
- **Skills:** one per role. When the same failure happens twice, the lead adds a line to the skill.
- **Loop:** a 10-minute timer under `caffeinate`, so the lead keeps waking up while you're away.

## Quick start

Inside your project's git repo:

```bash
curl -fsSL https://raw.githubusercontent.com/Himanshu-Sangshetti/cursor-longrun/main/install.sh | bash -s -- --preset code --goal "Every public function has a tested example"
```

1. **Fill the blanks.** `grep -rn '<<FILL' longrun .cursor` lists them: the order of work in `longrun/queue.md`, your rollback notes in `longrun/revert.md`, model names in `.cursor/rules/longrun-models.mdc`, and your test command in `longrun/config.env`.
2. **Run `longrun doctor`** until it says `ready`. Every failure prints its fix.
3. **Start the lead.** Open a new Agent chat in Cursor and type `/longrun-start` (or paste `longrun/prompts/start-lead.md`). Grant the permissions it asks for, then leave. Check in with `longrun status`.

## Pick a preset

Whether a run can go long without you depends on two questions: can the work be split into independent units, and can something other than you check each one?

| Preset | Use it when | Each unit is checked by |
| --- | --- | --- |
| `code` | units are independent changes your tests can judge | your test and lint commands, on its own branch |
| `content` | units are pages, docs or lessons that get published | numeric content checks, then a live check of the published page |
| `shared` | everything is one codebase that must keep building (a game, an app) | a build check under a build-slot lock, with file ownership per workstream |

Prefer `code` or `content` if you can shape the work that way. With a branch per unit, the content run had 2 merge conflicts across 308 workers. On one shared tree, the game run's first eight parallel workers hit 15 failed compiles.

## What the runs taught (and where the kit applies it)

| Lesson | Evidence from the runs | In the kit |
| --- | --- | --- |
| Write the order of work into a file before you leave | 29 of 79 interruptions in the game run were agents asking what to do next | `queue.md`; `doctor` fails on an empty queue |
| Make every unit checkable by something other than you | script-checkable work was accepted 23 of 24 times, look-and-feel work 4 of 12 | checker skill, `longrun/checks/` |
| Keep the lead out of the product | the lead that only coordinated ran 16 h alone; the one that wrote code needed a human every 41 min | lead rule; `longrun report` prints the split |
| Keep the lead's chat short | the game lead re-read 130.5M tokens, more than all its workers combined | `handoff.md` and a restart prompt |
| Keep the machine awake | the content run lost over 9 hours to a sleeping laptop | `loop.sh` under `caffeinate`; `longrun watch` |

The article has the full analysis, the math and the caveats. These are two runs, not a controlled experiment.

## Measure your run

```bash
longrun report --list-chats              # find your lead chat
longrun report --chat <id>               # unattended hours, five autonomy measures, wake sources, worker stats
```

It reads Cursor's local database read-only and never touches settings or auth keys.

## More

- [`docs/reference.md`](docs/reference.md): every file the kit installs, the check-script contract, watching a run from outside, what is Cursor-specific vs portable, what we couldn't verify, FAQ.
- [`examples/hello-queue/`](examples/hello-queue/): what the state files look like mid-run.
- Works on macOS and Linux (CI runs both). Windows via WSL, untested.

MIT licensed.
