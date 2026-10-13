# hello-queue

What the state files look like about 50 minutes into a small run. The toy repo is `tinycalc`, a command-line calculator with no docs. The queue has three doc-writing units, preset `code`.

At this moment:

- `readme-quickstart` was written, checked, merged and its worktree removed.
- `contributing` was rejected once (two sections were too thin, measured), and a fix worker is on it.
- `api-reference` is waiting for the main line.

Read the files in this order: `longrun/status.md`, `longrun/queue.md`, `longrun/roster.tsv`, `longrun/decisions.tsv`, `longrun/lessons.tsv`, `longrun/revert.md`. Then `longrun/checks/doc-words.sh`, the check that turned "too thin" into a number.

Try the board yourself:

```
cp -R examples/hello-queue /tmp/hq && cd /tmp/hq && git init -q && git add -A && git commit -qm demo
longrun status
```
