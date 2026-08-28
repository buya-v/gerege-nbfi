#!/bin/zsh
# T325 instrument 50 — DOES THE WIRING FAIL CLOSED?
#
# Instruments 20 and 30 drive the GUARD. This one drives the GLUE: the
# `attest_run` / `attest_exit_protocol` functions that fire-program.sh actually
# calls, extracted from the shipped file by their markers.
#
# WHY IT IS A SEPARATE INSTRUMENT. A guard that is correct and a wiring that
# swallows its verdict are indistinguishable from the guard's own test suite —
# and that combination is this program's most-repeated failure. T190, T202, T302
# and T319 are all one shape: a load-bearing check whose return code was thrown
# away, so the reassuring answer was logged for work nobody had verified. The
# arms below are exactly the paths where that could happen again.
#
# It never runs a fire, never takes the lock, never invokes `claude`, and touches
# only scratch clones under /private/tmp.

set -uo pipefail

HERE=${0:A:h}
REPO_ROOT=${HERE:h:h:h:h}
FIRE="$REPO_ROOT/.softhouse/bin/fire-program.sh"
GUARD="$REPO_ROOT/.softhouse/guards/repo-state-attest.sh"
[[ -r "$FIRE" ]]  || { print -r -- "REFUSED: cannot read $FIRE"; exit 2 }
[[ -r "$GUARD" ]] || { print -r -- "REFUSED: cannot read $GUARD"; exit 2 }

ROOT=$(mktemp -d /private/tmp/t325-glue-XXXXXX) || exit 2
ROOT=$(cd -- "$ROOT" && pwd -P)
case "$ROOT" in ("$REPO_ROOT"*) print -r -- "REFUSED: scratch root inside the repo"; exit 2 ;; esac
print -r -- "scratch: $ROOT"
print -r -- "shipped glue under test: $FIRE"
print -r -- "git: $(git --version)"
print

BLOCK="$ROOT/attest-wiring.zsh"
awk '
  index($0,"T325-ATTEST-WIRING BEGIN") { inb=1; next }
  index($0,"T325-ATTEST-WIRING END")   { inb=0 }
  inb { print }
' "$FIRE" > "$BLOCK"
N=$(grep -c '.' "$BLOCK")
if (( N == 0 )); then
  print -r -- "REFUSED: the T325-ATTEST-WIRING markers extracted ZERO lines. Refusing to test a copy."
  exit 2
fi
print -r -- "extracted $N lines of shipped wiring"
print

LOGFILE="$ROOT/fire.log"
log() { print -r -- "$*" >> "$LOGFILE" }
SCRIPT_DIR="$REPO_ROOT/.softhouse/bin"
LOG_DIR="$ROOT"
ATTEST_DIR="$ROOT"
source "$BLOCK" || { print -r -- "REFUSED: the extracted wiring would not load"; exit 2 }
print -r -- "ATTEST resolves to: $ATTEST"
[[ -r "$ATTEST" ]] || { print -r -- "REFUSED: the wiring's own default path does not resolve to a readable guard"; exit 2 }
print

PASS=0; FAIL=0; FAILED=()

mkrepo() {
  local d="$ROOT/$1"
  git init -q -b main "$d" >/dev/null 2>&1 || return 1
  (
    cd "$d" || exit 1
    git config user.name Buyan; git config user.email buya.vol@gmail.com
    mkdir -p .softhouse
    printf '{"tasks":[]}\n' > .softhouse/tasks.json
    printf 'work\n' > worker-output.txt
    git add -A; git commit -q -m init
  ) || return 1
  print -rn -- "$d"
}

# name, expected rc, expected substring in the log
check() {
  local name="$1" want_rc="$2" want_txt="$3" got_rc="$4"
  local body; body=$(cat "$LOGFILE" 2>/dev/null)
  local ok=1
  (( got_rc == want_rc )) || ok=0
  [[ "$body" == *"$want_txt"* ]] || ok=0
  if (( ok )); then
    print -r -- "ARM $name: PASS  rc=$got_rc (expected $want_rc), log contains ${want_txt:0:60}..."
    PASS=$((PASS+1))
  else
    print -r -- "ARM $name: FAIL  rc=$got_rc (expected $want_rc)"
    print -r -- "      wanted in log: $want_txt"
    print -r -- "$body" | sed 's/^/      /'
    FAIL=$((FAIL+1)); FAILED+=("$name")
  fi
}

print -r -- "=== W1 — the ordinary case: a clean iteration attests PASS ==="
REPO=$(mkrepo w1) || exit 2
: > "$LOGFILE"
ATTEST_BEFORE="$ROOT/w1.before"
attest_run "attest-before" snapshot "$REPO" "$ATTEST_BEFORE" >/dev/null
( cd "$REPO" && printf 'more\n' >> worker-output.txt && git commit -qam "an ordinary commit" ) >/dev/null
attest_exit_protocol >/dev/null; RC=$?
check W1_clean_iteration 0 "exit-protocol attestation PASSED" $RC

print
print -r -- "=== W2 — damage: the wiring must REPORT it, not swallow it ==="
REPO=$(mkrepo w2) || exit 2
: > "$LOGFILE"
ATTEST_BEFORE="$ROOT/w2.before"
attest_run "attest-before" snapshot "$REPO" "$ATTEST_BEFORE" >/dev/null
( cd "$REPO" && git update-index --assume-unchanged worker-output.txt && printf 'DESTROYED\n' > worker-output.txt )
attest_exit_protocol >/dev/null; RC=$?
check W2_damage_is_reported 1 "EXIT-PROTOCOL VIOLATION" $RC

print
print -r -- "=== W3 — NO BASELINE: unattested must not resolve to clean ==="
# The path a fire takes when the pre-driver snapshot failed. The pre-T325 code
# would simply have said nothing here, which reads as "fine".
REPO=$(mkrepo w3) || exit 2
: > "$LOGFILE"
ATTEST_BEFORE=""
attest_exit_protocol >/dev/null; RC=$?
check W3_no_baseline_is_unattested 2 "UNATTESTED" $RC

print
print -r -- "=== W4 — the guard file is MISSING: fail closed, loudly ==="
REPO=$(mkrepo w4) || exit 2
: > "$LOGFILE"
SAVED_ATTEST="$ATTEST"
ATTEST="$ROOT/no-such-guard.sh"
ATTEST_BEFORE="$ROOT/w4.before"
attest_run "attest-before" snapshot "$REPO" "$ATTEST_BEFORE" >/dev/null; RC=$?
check W4_missing_guard_refuses 2 "NOT READABLE" $RC
ATTEST="$SAVED_ATTEST"

print
print -r -- "=== W5 — the AFTER snapshot cannot be taken: still not clean ==="
REPO=$(mkrepo w5) || exit 2
: > "$LOGFILE"
ATTEST_BEFORE="$ROOT/w5.before"
attest_run "attest-before" snapshot "$REPO" "$ATTEST_BEFORE" >/dev/null
rm -rf "$REPO"          # the repo is gone between the two snapshots
attest_exit_protocol >/dev/null; RC=$?
check W5_after_snapshot_refused 2 "UNATTESTED" $RC

print
print -r -- "================================================================"
print -r -- "TOTAL: PASS=$PASS FAIL=$FAIL"
if (( FAIL != 0 )); then
  print -r -- "FAILED: ${FAILED[*]}"
  print -r -- "scratch kept: $ROOT"
  exit 1
fi
print -r -- "scratch kept: $ROOT"
exit 0
