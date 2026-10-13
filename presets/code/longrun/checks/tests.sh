#!/usr/bin/env bash
# Check: the project's lint and test commands pass in a worktree.
#   usage: longrun/checks/tests.sh [dir]     (dir defaults to the current directory)
# Commands come from LONGRUN_LINT_CMD and LONGRUN_TEST_CMD in longrun/config.env.
# Contract: evidence lines, then PASS/FAIL; exit 0 pass, 1 fail, 2 setup error.
set -u
here=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck disable=SC1091
. "$here/config.env"
dir=${1:-.}
cd "$dir" || { echo "FAIL tests: no such dir $dir"; exit 2; }
[ -n "${LONGRUN_TEST_CMD:-}" ] || { echo "FAIL tests: LONGRUN_TEST_CMD is empty in longrun/config.env"; exit 2; }
echo "dir: $(pwd)"
echo "head: $(git rev-parse --short HEAD 2>/dev/null || echo none)"
fail=0
for kind in lint test; do
  if [ $kind = lint ]; then cmd=${LONGRUN_LINT_CMD:-}; else cmd=$LONGRUN_TEST_CMD; fi
  [ -n "$cmd" ] || { echo "$kind: skipped (no command)"; continue; }
  start=$(date +%s)
  out=$(bash -c "$cmd" 2>&1); code=$?
  echo "$kind: \`$cmd\` exit $code in $(( $(date +%s) - start )) s"
  printf '%s\n' "$out" | tail -n 12 | sed "s/^/  $kind| /"
  [ $code -eq 0 ] || fail=1
done
if [ $fail -eq 0 ]; then echo "PASS tests"; exit 0; fi
echo "FAIL tests: see the exit codes above"; exit 1
