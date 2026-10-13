You are the {project} writer, fixing a rejected unit. Do not merge. Do not publish.

Read in full:
- .cursor/skills/longrun-writer/SKILL.md (including Known failures)
- .cursor/skills/longrun-{preset}/SKILL.md
- longrun/preferences.md rules {n, n, n}

UNIT: {unit}   BRANCH: feat/{unit}   REJECTED SHA: {sha}   WORKTREE: {path}

THE CHECKER REJECTED IT. Findings, quoted line by line:
> 1. {finding with the checker's number}
> 2. {finding with the checker's number}

GOAL: make every finding false on the real result. Fix the cause, not only the quoted lines. Look for the same miss everywhere in your scope.

SCOPE: same as the original brief: {paths}.

VERIFY: {exact commands}, then re-measure each finding.

REPORT: status; evidence (branch, new head SHA); per finding: old number, new number, what you changed.
