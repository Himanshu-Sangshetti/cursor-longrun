---
name: live-check
description: Opens the live result the way a user would and reports what is really there. Use after anything is published, deployed or shipped.
---

# Live check

## Purpose

A 200 and a title tag are not proof. Open the real result and look at it.

## Do

- Open the live URL or running app in a real browser, as a user would, and use it: click through the main path.
- Browser automation tool: installed at `<path>` (placeholder: set this to where your browser tool lives, e.g. a Playwright or browser-MCP install).
- Take screenshots and read them. A screenshot you did not look at is not evidence.
- Check the specific things the brief names: text, layout, links, console errors.
- Append one row to `state/decisions.tsv` with the URL, what you saw and pass or reject.

## Do not

- Do not pass from status codes, build logs or the writer's report.
- Do not fix what you find. Reject with findings.
- Do not skip mobile width if users will be on mobile.

## Done when

You opened the live result, read your screenshots, and wrote a decision row that says what you saw.

## Known failures

<!-- Starts empty. It grows from state/lessons.tsv: when the same miss happens twice, add one line here (what went wrong, a named example, why the check that passed did not catch it). -->


