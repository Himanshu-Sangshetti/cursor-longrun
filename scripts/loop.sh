#!/usr/bin/env bash
# Tick loop for the lead chat.
#   usage: scripts/loop.sh [interval_seconds=600] [name=run]
#
# How the lead wakes: start this script in a Cursor background shell with
# notify_on_output and a regex such as  ^AGENT_LOOP_TICK_<name>
# Cursor turns each matching line into a new turn in the lead chat.
# (Ask the lead: "run scripts/loop.sh 600 <name> as a background shell with
# notify_on_output, pattern ^AGENT_LOOP_TICK_<name>".)
#
# The timer pauses if the machine sleeps. `sleep` does not advance while the host is
# asleep, so ticks stop with it. caffeinate below keeps a Mac awake while this runs.
# On other systems, disable sleep yourself or use a scheduler that survives it.

INTERVAL="${1:-600}"
NAME="${2:-run}"

tick() {
  while true; do
    sleep "$INTERVAL"
    echo "AGENT_LOOP_TICK_${NAME} {\"prompt\":\"Audit. Re-read state/queue.md and state/roster.tsv. Check in-flight workers by files on disk and live results, not by their reports. Replace stuck workers. Keep at least one worker in flight unless the queue is empty. Post a one-screen status.\"}"
  done
}

if command -v caffeinate >/dev/null 2>&1; then
  # -d display, -i idle, -m disk, -s system (on AC power), -u declare user active
  export -f tick 2>/dev/null || true
  export INTERVAL NAME
  exec caffeinate -dimsu bash -c "$(declare -f tick); tick"
else
  echo "caffeinate not found; make sure this machine does not sleep." >&2
  tick
fi
