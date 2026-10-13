<!-- The human's standing rules. Numbered. Briefs cite rule numbers. Add a line each time you repeat an instruction. -->
1. One writer per branch and per folder. One concern per branch, named `feat/<unit>`.
2. Checkers never author the work they check, and run on a different model family from the writer.
3. Stop at merge-ready. The lead merges only SHAs with a pass row in `longrun/decisions.tsv`.
4. Commit each finished unit. Small commits are the trail.
5. After every merge or reject, write one row in `longrun/lessons.tsv`. Same miss twice: patch the owning skill the same day.
6. After anything ships, open the live result like a user would. A 200 and a title tag are not enough.
7. Every worker report carries evidence: SHA, URL or PR number, and the check output.
8. Use only this project's credentials. Never open another project's keys.
