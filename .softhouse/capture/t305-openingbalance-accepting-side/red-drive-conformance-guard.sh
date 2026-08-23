#!/bin/sh
# T305 -- RED-DRIVE OF conformance.sh's guard_accepting_side_gap_declared.
#
# P-22: "a control that cannot fail is worse than none". The guard prints OPEN AND DECLARED
# on the green bar; that proves it RUNS, not that it REFUSES. All four of its cells are
# driven here, plus the attestation refusal, plus its fail-closed branch.
#
# HOW THE FUNCTION IS OBTAINED, and why not by copying it: the body is EXTRACTED FROM THE
# LIVE conformance.sh AT RUN TIME by name, the same technique conformance.sh itself uses to
# read the cannotCatch const out of ledgerguard/main.go rather than restating its size
# (P-80: "A CORRECTED CARDINAL ROTS IN EVERY PLACE IT WAS RESTATED"). A copied body would
# be a second source of truth that goes stale the first time somebody edits the guard, and
# this rig would then certify a function that is no longer in the harness. If the extraction
# fails, THIS SCRIPT EXITS NON-ZERO rather than falling back to anything.
#
# THE TREES ARE SCRATCH. Nothing under $REPO_ROOT is modified: each arm builds a throwaway
# directory holding only the two paths the guard reads, plus a git repo where needed for the
# `git ls-files` arm. THE REAL VECTOR STORE IS NEVER EDITED, not even transiently, because a
# crash mid-arm would leave the corpus mutated.
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$DIR/../../.." && pwd)
SRC="$ROOT/.softhouse/conformance.sh"
FAILED=0

[ -f "$SRC" ] || { echo "REFUSING: $SRC not found."; exit 2; }

TMPD=$(mktemp -d "${TMPDIR:-/tmp}/t305cg.XXXXXX")
trap 'rm -rf "$TMPD"' EXIT HUP INT TERM QUIT

# ---- extract the function by name, from the live harness --------------------------------
FN="$TMPD/fn.sh"
sed -n '/^guard_accepting_side_gap_declared() {$/,/^}$/p' "$SRC" > "$FN"
LINES=$(grep -c '' "$FN")
if [ "$LINES" -lt 20 ]; then
  echo "REFUSING: could not extract guard_accepting_side_gap_declared from conformance.sh"
  echo "  (extracted $LINES line(s)). The guard may have been renamed or reshaped; this rig"
  echo "  will not certify a function it could not read."
  exit 2
fi
echo "extracted guard_accepting_side_gap_declared: $LINES lines, from the LIVE conformance.sh"
echo ""

# ---- a harness that supplies only what the function uses --------------------------------
cat > "$TMPD/harness.sh" <<'H'
say()  { printf '%s\n' "$*"; }
warn() { printf '%s\n' "$*" >&2; }
. "$FNFILE"
guard_accepting_side_gap_declared
H

mktree() { # mktree DIR  -- a scratch REPO_ROOT with an empty ledger corpus + capabilities file
  mkdir -p "$1/.softhouse/vectors/ledger"
  printf '{"capabilities":[{"name":"x","evidence":"nothing here"}]}\n' > "$1/.softhouse/vectors/capabilities-ledger.json"
  ( cd "$1" && git init -q . && git config user.email t@t && git config user.name t ) >/dev/null 2>&1
}
addmarker() { printf '{"capabilities":[{"name":"x","evidence":"T305-ACCEPTING-SIDE-GAP open"}]}\n' > "$1/.softhouse/vectors/capabilities-ledger.json"; }
addaccept() { printf '{"request":{"command":"defineOpeningBalance"},"expect":{"kind":"entry"}}\n' > "$1/.softhouse/vectors/ledger/ACCEPT.json"; }
addrefusal(){ printf '{"request":{"command":"defineOpeningBalance"},"expect":{"kind":"refusal"}}\n' > "$1/.softhouse/vectors/ledger/REFUSE.json"; }

run() { # run TREE -> prints combined output, returns the guard's rc
  REPO_ROOT="$1" FNFILE="$FN" sh "$TMPD/harness.sh" 2>&1
}

arm() { # arm LABEL TREE EXPECTED_RC PATTERN
  local out rc=0
  out=$(REPO_ROOT="$2" FNFILE="$FN" sh "$TMPD/harness.sh" 2>&1) || rc=$?
  if [ "$rc" != "$3" ]; then
    printf 'NOT OK  %-56s rc %s, expected %s\n' "$1" "$rc" "$3"; FAILED=1; return
  fi
  if [ -n "$4" ] && ! printf '%s\n' "$out" | grep -q "$4"; then
    printf 'NOT OK  %-56s rc %s but pattern absent: %s\n' "$1" "$rc" "$4"; FAILED=1; return
  fi
  printf 'ok      %-56s rc %s\n' "$1" "$rc"
}

# ARM 1 -- vectors=0, marker ABSENT  -> FAIL, the hole reopened silently
T1="$TMPD/t1"; mktree "$T1"
arm "ARM 1 gap OPEN, declaration REMOVED -> refuses" "$T1" 1 "NOTHING DECLARES IT"

# ARM 2 -- vectors=0, marker PRESENT -> ok, the state this tree is actually in
T2="$TMPD/t2"; mktree "$T2"; addmarker "$T2"
arm "ARM 2 gap OPEN and DECLARED -> passes" "$T2" 0 "OPEN AND DECLARED"

# ARM 3 -- vectors>0, marker PRESENT -> FAIL, the caveat outlived its defect
T3="$TMPD/t3"; mktree "$T3"; addmarker "$T3"; addaccept "$T3"
arm "ARM 3 gap CLOSED but declaration STALE -> refuses" "$T3" 1 "DECLARATION IS NOW STALE"

# ARM 4 -- vectors>0, marker ABSENT -> ok, closed and cleaned up together
T4="$TMPD/t4"; mktree "$T4"; addaccept "$T4"
arm "ARM 4 gap CLOSED and declaration removed -> passes" "$T4" 0 "CLOSED, and the declaration was removed"

# ARM 5 -- a REFUSAL vector carrying the same command must NOT count as an acceptance.
# This is the arm that matters most: LDG-REFUSE-03 is exactly this shape and lives in the
# real corpus, so a guard that counted it would read the hole as closed on the green bar.
T5="$TMPD/t5"; mktree "$T5"; addmarker "$T5"; addrefusal "$T5"
arm "ARM 5 a REFUSAL vector does not count as an acceptance" "$T5" 0 "accepting vectors 0"

# ARM 6 -- a TRACKED disposability attestation refuses, even with everything else correct.
T6="$TMPD/t6"; mktree "$T6"; addmarker "$T6"
mkdir -p "$T6/.softhouse/capture/t999-rig/attest"
echo "authorised" > "$T6/.softhouse/capture/t999-rig/attest/gerege.disposable"
( cd "$T6" && git add -A && git commit -qm x ) >/dev/null 2>&1
arm "ARM 6 a TRACKED disposability attestation refuses" "$T6" 1 "TRACKED DISPOSABILITY ATTESTATION"

# ARM 7 -- the SAME file UNTRACKED does not refuse. The distinction is the whole point:
# red-drive-gate.sh creates one transiently, and a scratch file is not an authorisation.
T7="$TMPD/t7"; mktree "$T7"; addmarker "$T7"
mkdir -p "$T7/.softhouse/capture/t999-rig/attest"
echo "scratch" > "$T7/.softhouse/capture/t999-rig/attest/gerege.disposable"
arm "ARM 7 an UNTRACKED attestation does NOT refuse" "$T7" 0 "no tracked disposability attestation"

# ARM 8 -- fail-closed: the paths it reads are missing.
T8="$TMPD/t8"; mkdir -p "$T8"
arm "ARM 8 missing corpus fails CLOSED" "$T8" 1 "Fail-closed"

echo ""
if [ "$FAILED" -eq 0 ]; then
  echo "RED-DRIVE PASS: all four cells of the two-way rule were driven, the refusal-vector"
  echo "false-positive was excluded, and tracked/untracked attestations were separated."
  exit 0
fi
echo "RED-DRIVE FAILED: guard_accepting_side_gap_declared does not behave as documented."
exit 1
