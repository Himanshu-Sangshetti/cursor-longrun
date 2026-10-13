#!/usr/bin/env bash
# Smoke test for bin/longrun: init (all presets), doctor, status, unit, watch, checks.
#   usage: tests/smoke.sh
# shellcheck disable=SC2001
set -u
HERE=$(cd "$(dirname "$0")/.." && pwd)
LONGRUN="$HERE/bin/longrun"
export LONGRUN_NO_NOTIFY=1 GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.com GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.com
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
PASS=0 FAILS=0

t() { # t <name> <expected exit> <command...>: run, record, keep output in $OUT
  local name=$1 want=$2; shift 2
  OUT=$("$@" 2>&1); local got=$?
  if [ "$got" = "$want" ]; then PASS=$((PASS + 1)); echo "ok   $name"
  else FAILS=$((FAILS + 1)); echo "FAIL $name (exit $got, want $want)"; echo "$OUT" | sed 's/^/     /'; fi
}
has() { # has <name> <text>: last output contains text
  if printf '%s' "$OUT" | grep -qF -- "$2"; then PASS=$((PASS + 1)); echo "ok   $1"
  else FAILS=$((FAILS + 1)); echo "FAIL $1: output lacks '$2'"; echo "$OUT" | sed 's/^/     /'; fi
}
new_repo() {
  rm -rf "${TMP:?}/$1"; mkdir -p "$TMP/$1"; cd "$TMP/$1" || exit 1
  git init -q -b main . 2>/dev/null || { git init -q .; git checkout -q -b main; }
  echo "# toy" >README.md; git add -A; git commit -qm init
}
fill() { # replace every <<FILL ...>> in the given files with a value
  local f; for f in "$@"; do sed 's/<<FILL[^>]*>>/x/g' "$f" >"$f.tmp" && mv "$f.tmp" "$f"; done
}
commit() { git add -A && git commit -qm "$1"; }

echo "== code preset"
new_repo code
t "init refuses outside flags" 1 "$LONGRUN" init --preset nope
t "init code" 0 "$LONGRUN" init --preset code --goal "Ship three docs"
has "init prints next steps" "/longrun-start"
t "goal filled in queue" 0 grep -q "Goal: Ship three docs" longrun/queue.md
t "goal filled in command" 0 grep -q "Goal: Ship three docs" .cursor/commands/longrun-start.md
t "command matches start prompt" 0 cmp -s longrun/prompts/start-lead.md .cursor/commands/longrun-start.md
t "pre-run sha filled" 0 grep -q "Git SHA before the run: $(git rev-parse --short HEAD)" longrun/revert.md
t "preset recorded" 0 grep -q "^LONGRUN_PRESET='code'" longrun/config.env
t "tests.sh installed" 0 test -x longrun/checks/tests.sh
t "watch ok right after init" 0 "$LONGRUN" watch
t "init refuses to overwrite" 1 "$LONGRUN" init --preset code
has "lists conflicts" "longrun/queue.md"
t "doctor fails before filling" 1 "$LONGRUN" doctor
has "doctor: dirty tree" "FAIL  working tree has uncommitted changes"
has "doctor: queue" "FAIL  queue has no units"
has "doctor: revert" "FAIL  revert.md filled"
has "doctor: models" "FAIL  model map filled"
has "doctor: test cmd" "FAIL  LONGRUN_TEST_CMD is empty"
has "doctor gives fix lines" "fix: "
fill longrun/queue.md longrun/revert.md .cursor/rules/longrun-models.mdc
echo "LONGRUN_TEST_CMD='true'" >>longrun/config.env
chmod -x longrun/checks/tests.sh
commit "fill"
t "doctor catches non-executable script" 1 "$LONGRUN" doctor
has "doctor: chmod fix" "chmod +x"
chmod +x longrun/checks/tests.sh; commit "chmod"
t "doctor passes after filling" 0 "$LONGRUN" doctor
has "doctor ready" "doctor: ready"

t "status" 0 "$LONGRUN" status
has "status shows queue" "1. x. state: queued"
has "status shows lead row" "lead"

t "unit new" 0 "$LONGRUN" unit new intro
WT="$TMP/code-intro"
t "worktree exists" 0 test -d "$WT"
t "branch exists" 0 git show-ref --verify --quiet refs/heads/feat/intro
t "roster row added" 0 grep -q "^intro	writer" longrun/roster.tsv
t "unit new twice fails" 1 "$LONGRUN" unit new intro
t "bad unit name" 1 "$LONGRUN" unit new "Bad Name"
(cd "$WT" && echo "intro" >docs.md && git add docs.md && git commit -qm "intro doc")
t "tests.sh passes in worktree" 0 longrun/checks/tests.sh "$WT"
has "tests.sh evidence" "PASS tests"
t "diff-scope passes" 0 longrun/checks/diff-scope.sh main feat/intro 'docs.md'
t "diff-scope fails out of scope" 1 longrun/checks/diff-scope.sh main feat/intro 'src/*'
has "diff-scope evidence" "out of scope: docs.md"
t "unit done refuses unmerged" 1 "$LONGRUN" unit "done" intro
git merge -q --no-edit feat/intro
t "unit done after merge" 0 "$LONGRUN" unit "done" intro
t "worktree removed" 1 test -d "$WT"
t "roster marked done" 0 grep -q "^intro	writer	longrun-writer	-	done" longrun/roster.tsv

echo "== watch"
t "watch fresh" 0 "$LONGRUN" watch --stale-min 30
has "watch ok line" "longrun ok"
for f in longrun/*.md longrun/*.tsv; do touch -t 202001010000 "$f"; done
t "watch stale" 1 "$LONGRUN" watch --stale-min 30
has "watch stale line" "longrun STALE"
t "watch via -C from elsewhere" 1 bash -c "cd / && '$LONGRUN' -C '$TMP/code' watch"
touch longrun/status.md
t "watch fresh again" 0 "$LONGRUN" watch

echo "== content preset"
new_repo content
t "init content" 0 "$LONGRUN" init --preset content --goal "Write guides"
t "live check installed" 0 test -x longrun/checks/live.sh
fill longrun/queue.md longrun/revert.md .cursor/rules/longrun-models.mdc
echo "LONGRUN_PLAYWRIGHT='$TMP/nowhere'" >>longrun/config.env; commit "fill"
t "doctor wants playwright" 1 "$LONGRUN" doctor
has "doctor: playwright" "FAIL  LONGRUN_PLAYWRIGHT"
t "live.sh refuses without playwright" 2 longrun/checks/live.sh https://example.com
has "live.sh says not to search" "do not search"
mkdir -p "$TMP/pw/playwright"
echo "LONGRUN_PLAYWRIGHT='$TMP/pw'" >>longrun/config.env; commit "pw"
t "doctor passes content" 0 "$LONGRUN" doctor

echo "== shared preset"
new_repo shared
t "init shared" 0 "$LONGRUN" init --preset shared
t "owners installed" 0 test -f longrun/owners.md
fill longrun/queue.md longrun/revert.md .cursor/rules/longrun-models.mdc longrun/prompts/start-lead.md
commit "fill"
t "doctor wants build cmd and owners" 1 "$LONGRUN" doctor
has "doctor: build cmd" "FAIL  LONGRUN_BUILD_CMD is empty"
has "doctor: owners" "FAIL  owner table filled"
fill longrun/owners.md
echo "LONGRUN_BUILD_CMD='echo compiling'" >>longrun/config.env; commit "fill2"
t "doctor passes shared" 0 "$LONGRUN" doctor
t "build.sh ok" 0 longrun/checks/build.sh
has "BUILD OK printed" "BUILD OK"
echo "LONGRUN_BUILD_CMD='echo \"error: Foo.cs broke\"; exit 3'" >>longrun/config.env
t "build.sh fails" 1 longrun/checks/build.sh
has "BUILD FAILED printed" "BUILD FAILED (exit 3)"
has "error line shown" "error: Foo.cs broke"
has "collision rule in output" "wait 60 s and retry"
export LONGRUN_LOCK_DIR="$TMP/locks"
mkdir -p "$LONGRUN_LOCK_DIR/slot0.lock"; echo $$ >"$LONGRUN_LOCK_DIR/slot0.lock/pid"
echo "LONGRUN_LOCK_TIMEOUT=3" >>longrun/config.env
t "lock times out when slot busy" 75 longrun/scripts/lock.sh run true
has "LOCK TIMEOUT printed" "LOCK TIMEOUT"
echo 999999 >"$LONGRUN_LOCK_DIR/slot0.lock/pid"
t "stale lock is reclaimed" 0 longrun/scripts/lock.sh run true
unset LONGRUN_LOCK_DIR

echo "== report"
t "report --help" 0 "$LONGRUN" report --help
has "report help lists --list-chats" "--list-chats"
t "report without db fails cleanly" 1 "$LONGRUN" report --chat x --db "$TMP/none.vscdb"

echo
echo "smoke: $PASS passed, $FAILS failed"
[ "$FAILS" -eq 0 ]
