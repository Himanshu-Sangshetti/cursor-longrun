#!/usr/bin/env bash
# Build-slot lock: at most LONGRUN_BUILD_SLOTS builds at once on this machine.
#   usage: longrun/scripts/lock.sh run <command...>
# Waits for a free slot (polls every 3 s). Stale locks from dead processes are removed.
# After LONGRUN_LOCK_TIMEOUT seconds prints LOCK TIMEOUT and exits 75.
# The command sees LONGRUN_SLOT (0-based) in its environment.
set -u
here=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck disable=SC1091
. "$here/config.env"
[ "${1:-}" = run ] && [ $# -ge 2 ] || { echo "usage: $0 run <command...>" >&2; exit 2; }
shift
slots=${LONGRUN_BUILD_SLOTS:-1}
timeout=${LONGRUN_LOCK_TIMEOUT:-1800}
root=$(git -C "$here" rev-parse --show-toplevel 2>/dev/null || echo "$here")
dir=${LONGRUN_LOCK_DIR:-${TMPDIR:-/tmp}/longrun-locks-$(basename "$root")}
mkdir -p "$dir"
waited=0
while :; do
  i=0
  while [ $i -lt "$slots" ]; do
    lock="$dir/slot$i.lock"
    if mkdir "$lock" 2>/dev/null; then
      echo $$ >"$lock/pid"
      trap 'rm -rf "$lock"' EXIT INT TERM
      LONGRUN_SLOT=$i "$@"
      exit $?
    fi
    pid=$(cat "$lock/pid" 2>/dev/null || true)
    if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then rm -rf "$lock"; continue; fi
    i=$((i + 1))
  done
  [ $waited -ge "$timeout" ] && { echo "LOCK TIMEOUT (all $slots build slots busy for ${timeout}s)"; exit 75; }
  sleep 3; waited=$((waited + 3))
done
