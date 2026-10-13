#!/usr/bin/env bash
# Check: every "## " section of every Markdown file has at least MIN words of substance
# (code blocks and blank lines excluded). Turns "too thin" into a number.
#   usage: longrun/checks/doc-words.sh <file-or-dir> [min=40]
# Contract: evidence lines, then PASS/FAIL; exit 0 pass, 1 fail, 2 usage error.
set -u
[ $# -ge 1 ] || { echo "usage: $0 <file-or-dir> [min]" >&2; exit 2; }
min=${2:-40} thin=0 total=0
files=$(find "$1" -name '*.md' -type f | sort)
[ -n "$files" ] || { echo "FAIL doc-words: no .md files under $1"; exit 2; }
for f in $files; do
  out=$(awk -v min="$min" -v f="$f" '
    /^```/ { code = !code; next }
    /^## / { if (h != "") print f ": " h ": " w " words" (w < min ? " THIN" : ""); h = substr($0, 4); w = 0; next }
    !code && h != "" { w += NF }
    END { if (h != "") print f ": " h ": " w " words" (w < min ? " THIN" : "") }' "$f")
  [ -n "$out" ] && echo "$out"
  total=$((total + $(printf '%s\n' "$out" | grep -c ': ')))
  thin=$((thin + $(printf '%s\n' "$out" | grep -c ' THIN$')))
done
echo "sections: $total, under $min words: $thin"
if [ "$thin" -eq 0 ]; then echo "PASS doc-words"; exit 0; fi
echo "FAIL doc-words: $thin of $total sections under $min words"; exit 1
