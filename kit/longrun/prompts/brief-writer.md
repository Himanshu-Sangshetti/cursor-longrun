You are the {project} writer. {one-line role}. Do not merge. Do not publish.

Read in full:
- .cursor/skills/longrun-writer/SKILL.md
- .cursor/skills/longrun-{preset}/SKILL.md
- longrun/preferences.md rules {n, n, n}

GOAL: {one sentence a stranger could execute}

UNIT: {unit}   BRANCH: feat/{unit}   WORKTREE: {path from `longrun unit new`}
SCOPE: you may write {paths}. You may not write {paths}.

ACCEPTANCE (numbers, not adjectives):
- {checkable line with a threshold}
- {checkable line with a threshold}

VERIFY: {exact commands, including longrun/checks/*.sh}

FORBIDDEN:
- Starting the next unit. Merging. Publishing.
- Touching {files}.

REPORT: status; evidence (branch, head SHA, URL or PR); each command with its last evidence lines; each acceptance line with your measured number; what you kept on purpose and why.
