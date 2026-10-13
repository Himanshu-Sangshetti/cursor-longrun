---
name: longrun-live-check
description: Opens the live result the way a user would and reports what is really there. Use after anything is published, deployed or shipped in a longrun.
---

# Live check

A 200 status and a title tag are not proof. Open the real result and look at it.

## Do

- Open the live URL or running app as a signed-out user would, and use the main path: click, scroll, submit.
- Use the browser tool set in `longrun/config.env` (`LONGRUN_PLAYWRIGHT`). **Do not search the machine for it.** If it is empty or wrong, stop and report that, so the lead fixes it once.
- Take screenshots and read them. A screenshot you did not look at is not evidence.
- Check what the brief names: text, layout, links, console errors, mobile width (390 px) when users are on mobile.
- Append one row to `longrun/decisions.tsv` with the URL, what you saw, and pass or reject.

## Do not

- Do not pass from status codes, build logs or the writer's report.
- Do not fix what you find. Reject with findings.

## Done when

You opened the live result, read your screenshots, and wrote a decision row saying what you saw, with the URL.

## Known failures

<!-- Starts empty. The lead adds one line when the same miss happens twice. -->
