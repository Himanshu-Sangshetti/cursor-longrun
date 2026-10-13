#!/usr/bin/env bash
# Check: the shared project builds. Runs LONGRUN_BUILD_CMD under a build-slot lock.
#   usage: longrun/checks/build.sh
# Prints error lines, then BUILD OK or BUILD FAILED, then PASS/FAIL.
# Exit 0 pass, 1 build failed, 2 setup error or lock timeout.
set -u
here=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck disable=SC1091
. "$here/config.env"
[ -n "${LONGRUN_BUILD_CMD:-}" ] || { echo "FAIL build: LONGRUN_BUILD_CMD is empty in longrun/config.env"; exit 2; }
log=$(mktemp "${TMPDIR:-/tmp}/longrun-build.XXXXXX")
"$here/scripts/lock.sh" run bash -c "$LONGRUN_BUILD_CMD" >"$log" 2>&1
code=$?
if [ $code -eq 75 ]; then cat "$log"; echo "FAIL build: lock timeout"; exit 2; fi
grep -iE '(^|[^a-z])(error|fatal)([^a-z]|$)' "$log" | sort -u | head -n 15
echo "log: $log"
if [ $code -eq 0 ]; then echo "BUILD OK"; echo "PASS build"; exit 0; fi
echo "BUILD FAILED (exit $code)"
echo "FAIL build: if the errors are in files you do not own, wait 60 s and retry (max 3)."
exit 1
