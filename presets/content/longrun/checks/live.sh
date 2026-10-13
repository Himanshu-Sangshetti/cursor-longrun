#!/usr/bin/env bash
# Check: a live page loads for a signed-out user and shows the expected text.
#   usage: longrun/checks/live.sh <url> [expected text]...
# Uses Playwright from LONGRUN_PLAYWRIGHT in longrun/config.env. Screenshots go to
# ${TMPDIR:-/tmp}/longrun-live/. Read them: a screenshot you did not open is not evidence.
# Contract: evidence lines, then PASS/FAIL; exit 0 pass, 1 fail, 2 setup error.
set -u
here=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck disable=SC1091
. "$here/config.env"
[ $# -ge 1 ] || { echo "usage: $0 <url> [expected text]..." >&2; exit 2; }
pw=${LONGRUN_PLAYWRIGHT:-}
if [ -z "$pw" ] || [ ! -d "$pw/playwright" ]; then
  echo "FAIL live: LONGRUN_PLAYWRIGHT ('$pw') has no playwright package. Fix config.env once; do not search for it."
  exit 2
fi
NODE_PATH="$pw" node "$here/checks/live_check.mjs" "$@"
