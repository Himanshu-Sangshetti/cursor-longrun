<!-- Who may edit what. Every brief repeats the worker's row as "YOU OWN:" and "Do NOT edit:". -->
# Owners

| Workstream | Owns (file globs) | Notes |
| --- | --- | --- |
| <<FILL: workstream>> | <<FILL: e.g. src/ui/**, not src/ui/theme.ts>> | |
| lead | `longrun/**`, `.cursor/skills/**` | never product files |

## Collision rule

1. Edit ONLY the files your workstream owns. If another file must change, write the request in your report.
2. **Never fix someone else's compile error.** Wait 60 s and run `longrun/checks/build.sh` again. After 3 failed retries, stop and report the error with the file and its owner.
3. Two workstreams that need the same file go in sequence, not in parallel. The lead decides the order in `longrun/queue.md`.
4. Use another workstream's code only through its public API, via a thin adapter in your own file.
