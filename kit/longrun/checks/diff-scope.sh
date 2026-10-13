#!/usr/bin/env bash
# Check: a branch only touched the paths its brief allowed.
#   usage: longrun/checks/diff-scope.sh <base> <head> <allowed-glob>...
#   e.g.   longrun/checks/diff-scope.sh main feat/intro 'docs/*' 'longrun/*'
# Contract: evidence lines, then PASS/FAIL; exit 0 pass, 1 fail, 2 usage error.
set -u
[ $# -ge 3 ] || { echo "usage: $0 <base> <head> <allowed-glob>..." >&2; exit 2; }
base=$1 head=$2; shift 2
files=$(git diff --name-only "$base...$head") || { echo "FAIL diff-scope: cannot diff $base...$head"; exit 2; }
total=0 bad=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  total=$((total + 1)); ok=0
  for g in "$@"; do
    # shellcheck disable=SC2254
    case "$f" in $g) ok=1; break ;; esac
  done
  [ $ok = 1 ] || { bad=$((bad + 1)); echo "out of scope: $f"; }
done <<< "$files"
echo "files changed: $total"
echo "out of scope: $bad"
if [ "$bad" -eq 0 ]; then echo "PASS diff-scope"; exit 0; fi
echo "FAIL diff-scope: $bad of $total files outside: $*"; exit 1
