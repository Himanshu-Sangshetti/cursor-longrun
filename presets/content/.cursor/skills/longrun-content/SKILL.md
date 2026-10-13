---
name: longrun-content
description: Preset rules for a longrun that writes and publishes content (pages, docs, lessons, question sets). Use with the longrun skills when LONGRUN_PRESET=content.
---

# Preset: content

Each unit is a piece of content that stands alone. Every unit goes writer, then checker, then live-check:

1. **Writer** drafts on `feat/<unit>` in its worktree and stops at merge-ready.
2. **Checker** (different model family) measures the draft at the SHA: substance, not shape. Use numeric gates you can rerun (words of substance per section, duplicates against existing units, banned phrases, images per lesson). Save any gate you write as a script in `longrun/checks/` so the next checker reruns the same measure.
3. **Lead** merges and publishes the passed SHA.
4. **Live-check** opens the published page: `longrun/checks/live.sh <url> "<text that must appear>"`, then reads the screenshots.

## Tools

- Playwright is installed at the path in `LONGRUN_PLAYWRIGHT` (`longrun/config.env`). **Use that path. Do not run `which`, `npm root -g` or `find` to look for it.** In one real run, 42 workers spent 58 shell calls rediscovering it.
- The live site is `LONGRUN_LIVE_URL`.

## Shortcuts checkers must close

Writers learn to satisfy the measure instead of the work. Seen in a real run, each closed by a skill line:

- every file landing on exactly the same line count;
- blank lines padded in to hit a length gate;
- fixing only the lines the last reject quoted;
- reporting a file it never opened as clean.

Measure on the whole unit, with the content's meaning in mind, and compare against an accepted unit.
