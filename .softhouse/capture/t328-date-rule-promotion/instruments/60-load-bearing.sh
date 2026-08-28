#!/usr/bin/env bash
# T328 -- IS EACH VECTOR LOAD-BEARING ON ITS OWN?
#
# "The mutant died once both vectors landed" is a weaker claim than it looks: it
# is satisfied by ONE vector doing all the work and the other riding along. This
# instrument withdraws ONE vector at a time from a SCRATCH COPY of the store and
# re-grades the mutant against it. If the mutant survives the withdrawal, the
# withdrawn vector was carrying that kill alone.
#
# THE STORE IS NEVER MUTATED. Everything happens in a temp copy and -store points
# at it; the committed corpus is read-only here.
#
# Exit 0 = both vectors are individually load-bearing (each withdrawal revives the
# mutant on the other guard). Exit 1 = one of them is decorative and the census
# would be claiming a kill nothing needs.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
IMPL=ledger-wrong-date-rules-always-refusing
V6=LDG-06-postclosure-entry-accepted-one-day-after-closing-date
V7=LDG-07-entry-on-the-business-date-accepted

TMP="$(mktemp -d "${TMPDIR:-/tmp}/t328-loadbearing.XXXXXX")" || exit 2
trap 'rm -rf "$TMP"' EXIT

grade() { # $1 = store root, prints the two ledger tallies
  ( cd "$REPO/nexus" && go run ./internal/apps/loanschedule/conformance/cmd/conformance \
      -store "$1" -ledger-impl "$IMPL" -oracle-probe up 2>&1 )
}

report() { # $1 = label, $2 = transcript
  local p f
  p="$(printf '%s\n' "$2" | LC_ALL=C sed -n 's/^ *ledger parity  *PASS \([0-9]*\)  *FAIL \([0-9]*\).*$/\1 \2/p')"
  f="$(printf '%s\n' "$2" | LC_ALL=C grep -aE '^ +LDG-0[67].*(PASS|FAIL|INADMISSIBLE)' | sed 's/^ *//')"
  echo "=== $1"
  echo "    ledger parity PASS/FAIL: $p"
  printf '    %s\n' "$f"
}

echo "T328 load-bearing probe -- HEAD $(git -C "$REPO" rev-parse --short HEAD), impl $IMPL"
echo "Each arm withdraws ONE vector from a SCRATCH COPY. The committed store is never touched."
echo ""

rc=0

# ARM 0 -- BOTH PRESENT. The control: the mutant must be DEAD.
cp -R "$REPO/.softhouse/vectors" "$TMP/both"
t0="$(grade "$TMP/both")"
report "ARM 0  both vectors present (the control)" "$t0"
printf '%s\n' "$t0" | LC_ALL=C grep -aq '^ *ledger parity  *PASS 5  *FAIL 2' || {
  echo "    *** ARM 0 did not report PASS 5 FAIL 2: the mutant is not dead with both vectors."; rc=1; }
echo ""

# ARM 1 -- LDG-07 WITHDRAWN. Only the closure kill remains.
cp -R "$REPO/.softhouse/vectors" "$TMP/no07"
rm -f "$TMP/no07/ledger/$V7.json"
t1="$(grade "$TMP/no07")"
report "ARM 1  LDG-07 WITHDRAWN -- does LDG-06 still kill it?" "$t1"
printf '%s\n' "$t1" | LC_ALL=C grep -aq '^ *ledger parity  *PASS 5  *FAIL 1' || {
  echo "    *** LDG-06 alone does NOT kill the mutant: LDG-07 was carrying that kill."; rc=1; }
echo ""

# ARM 2 -- LDG-06 WITHDRAWN. Only the future-date kill remains.
cp -R "$REPO/.softhouse/vectors" "$TMP/no06"
rm -f "$TMP/no06/ledger/$V6.json"
t2="$(grade "$TMP/no06")"
report "ARM 2  LDG-06 WITHDRAWN -- does LDG-07 still kill it?" "$t2"
printf '%s\n' "$t2" | LC_ALL=C grep -aq '^ *ledger parity  *PASS 5  *FAIL 1' || {
  echo "    *** LDG-07 alone does NOT kill the mutant: LDG-06 was carrying that kill."; rc=1; }
echo ""

# ARM 3 -- BOTH WITHDRAWN. The hole, reproduced on a scratch store: the mutant lives.
cp -R "$REPO/.softhouse/vectors" "$TMP/neither"
rm -f "$TMP/neither/ledger/$V6.json" "$TMP/neither/ledger/$V7.json"
t3="$(grade "$TMP/neither")"
report "ARM 3  BOTH WITHDRAWN -- the store as it stood before T328" "$t3"
printf '%s\n' "$t3" | LC_ALL=C grep -aq '^ *ledger parity  *PASS 5  *FAIL 0' || {
  echo "    *** the mutant did NOT survive with both vectors withdrawn; the survival transcript"
  echo "    *** 10-mutant-SURVIVES-before.txt and this arm disagree, which needs explaining."; rc=1; }
echo ""

echo "CONCLUSION"
echo "  ARM 3 reproduces the hole; ARM 1 and ARM 2 each show ONE surviving guard, so"
echo "  NEITHER VECTOR IS DECORATIVE: each kills a guard the other cannot see."
echo "T328 load-bearing probe: EXIT $rc"
exit "$rc"
