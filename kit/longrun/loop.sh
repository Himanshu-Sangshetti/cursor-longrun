#!/usr/bin/env bash
# Timer for the lead chat. Prints one AGENT_LOOP_TICK_<name> line every N seconds.
#   usage: bash longrun/loop.sh [interval_seconds] [name]   (defaults from longrun/config.env)
#
# Start it from the lead chat as a background shell with notify_on_output and the
# pattern ^AGENT_LOOP_TICK_<name>. Cursor turns each matching line into a new turn.
#
# `sleep` does not advance while the machine sleeps, so the ticks stop with it.
# On macOS this runs under caffeinate. Elsewhere, disable sleep yourself.
set -u
here=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
[ -f "$here/config.env" ] && . "$here/config.env"
INTERVAL="${1:-${LONGRUN_TICK_SEC:-600}}"
NAME="${2:-${LONGRUN_NAME:-run}}"
PROMPT='Tick. Re-read longrun/queue.md and longrun/roster.tsv. Check in-flight workers by files on disk, commits and live results, not by their reports. Replace stuck workers. Keep at least one worker in flight unless the queue is empty. Rewrite longrun/status.md.'

if [ "${LONGRUN_CAFFEINATED:-}" != 1 ] && command -v caffeinate >/dev/null 2>&1; then
  # -d display, -i idle, -m disk, -s system (on AC power)
  LONGRUN_CAFFEINATED=1 exec caffeinate -dims bash "$0" "$INTERVAL" "$NAME"
fi
command -v caffeinate >/dev/null 2>&1 || echo "longrun: caffeinate not found; make sure this machine does not sleep." >&2

n=0
while true; do
  sleep "$INTERVAL"
  n=$((n + 1))
  printf 'AGENT_LOOP_TICK_%s {"n":%d,"prompt":"%s"}\n' "$NAME" "$n" "$PROMPT"
done
