<!-- Write this before you leave. It is your condition for letting the lead merge and deploy: a complete list of changes. -->
# Revert

Say "revert <unit>" and the lead rolls it back. Never force-push the main branch.

## Safe rollback

- Git SHA before the run: <sha>
- Deployment before the run: <deployment id or "none">

## What landed

| Unit | Branch / PR | Commit | What | Touches runtime? |
| --- | --- | --- | --- | --- |
| <unit> | <branch or PR link> | <sha> | <one line> | <yes/no> |

## What this does not undo

<anything published outside git, e.g. content in a hosted service>
