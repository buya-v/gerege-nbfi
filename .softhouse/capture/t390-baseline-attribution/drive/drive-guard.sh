#!/usr/bin/env bash
# T390 drive-guard.sh -- DRIVE THE PROPOSED GUARD RED, AND KEEP A HEALTHY CONTROL BESIDE EVERY
# RED ARM. A patch that has not been driven red is a proposal, not a request.
#
#   bash .softhouse/capture/t390-baseline-attribution/drive/drive-guard.sh
#
# WHAT IS UNDER TEST. The EXACT text of `guard_oracle_state_attributed` as it would land in
# conformance.sh, sourced from ONE file --
#   .softhouse/capture/t390-baseline-attribution/drive/guard-oracle-state-attributed.sh
# -- which is the same file the patch generator inlines. There is deliberately no second copy
# of the guard text for this drive to fall out of step with (P-80).
#
# WHAT THIS HARNESS SUPPLIES is exactly the contract conformance.sh gives a guard: `say`,
# `warn`, `$REPO_ROOT`, and `set -u -o pipefail`. Nothing else, so an accidental dependence on
# some other conformance.sh global would show up here as an unbound-variable failure rather
# than passing silently.
#
# SIX ARMS. Four are RED (the guard must return non-zero), two are GREEN CONTROLS (it must
# return zero). A guard that refuses everything and a guard that cannot fail are the same
# defect wearing opposite signs, so both polarities are asserted, never just the interesting one.
set -uo pipefail

DRIVE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CAP=$(cd "$DRIVE/.." && pwd)
REPO_ROOT=$(cd "$CAP/../../.." && pwd)
export REPO_ROOT

INSTREL=".softhouse/capture/t363-oracle-baseline/instruments/oracle-state-baseline.sh"
REG="$REPO_ROOT/.softhouse/capture/t363-oracle-baseline/PROBES.tsv"

say()  { printf '%s\n' "$*"; }
warn() { printf '%s\n' "$*" >&2; }

# shellcheck source=/dev/null
. "$DRIVE/guard-oracle-state-attributed.sh"

TMP=$(mktemp -d "${TMPDIR:-/tmp}/t390-drive.XXXXXX") || exit 2
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
arm() { # arm <name> <expected-rc> <actual-rc>
  if [ "$2" = "$3" ]; then
    printf '  ok   %-46s expected rc=%s got rc=%s\n' "$1" "$2" "$3"; pass=$((pass+1))
  else
    printf '  ***  %-46s expected rc=%s got rc=%s  <-- ARM FAILED\n' "$1" "$2" "$3"; fail=$((fail+1))
  fi
}

echo "T390 GUARD DRIVE -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  REPO_ROOT = $REPO_ROOT"
echo "  guard text: drive/guard-oracle-state-attributed.sh"
echo "------------------------------------------------------------------------"

# --- GREEN CONTROL 1: the tree as it stands. The registry explains every row above the floor.
out=$(guard_oracle_state_attributed 2>&1); rc=$?
arm "GREEN control: healthy tree, real registry" 0 "$rc"
printf '%s\n' "$out" | grep -q 'ALL MOVEMENT ATTRIBUTED' \
  || { echo "  ***  GREEN control did not print the attributed line"; fail=$((fail+1)); }

# --- RED 1: AN UNATTRIBUTED ROW EXISTS. Built by DELETING one registered transaction from a
#     COPY of the registry -- never by writing to the oracle. The oracle is shared and
#     append-only; manufacturing a red by probing it would be a permanent casualty for a test.
#     Deleting L32's row makes the LIVE, REAL journal transaction L32 unexplained, which is
#     bit-for-bit the condition the guard exists to catch.
grep -v '^txn	L32	' "$REG" > "$TMP/reg-no-L32.tsv"
before=$(grep -c '^txn	L32	' "$REG")
after=$(grep -c '^txn	L32	' "$TMP/reg-no-L32.tsv")
echo "  (red-1 fixture: L32 rows in registry $before -> $after)"
[ "$before" = "1" ] || { echo "  ***  red-1 fixture is not calibrated: expected exactly 1 L32 row"; fail=$((fail+1)); }
out=$(ORACLE_BASELINE_REGISTRY="$TMP/reg-no-L32.tsv" guard_oracle_state_attributed 2>&1); rc=$?
arm "RED 1: an unattributed transaction exists" 1 "$rc"
printf '%s\n' "$out" | grep -q 'UNATTRIBUTED MOVEMENT IN THE SHARED REFERENCE ORACLE' \
  || { echo "  ***  RED 1 refused without naming the condition"; fail=$((fail+1)); }
printf '%s\n' "$out" | grep -q 'L32' \
  || { echo "  ***  RED 1 did not print the offending transaction id"; fail=$((fail+1)); }
# THE REFUSAL ITSELF, IN THE TRANSCRIPT. A drive that only asserts a return code asks the
# reader to trust that the words were right too. These are the lines a tripped worker sees.
echo "  --- RED 1, what the bar would print (elided to the load-bearing lines) ---"
printf '%s\n' "$out" | LC_ALL=C grep -aE 'UNATTRIBUTED|L32|widening the floor|PROBES.tsv' \
  | sed 's/^/  | /'
echo "  --- end RED 1 ---"

# --- GREEN CONTROL 2: the SAME copied-registry mechanism, with nothing removed. This is the
#     control that separates "the guard detects a missing row" from "the guard refuses any
#     registry it did not find at the default path".
cp "$REG" "$TMP/reg-intact.tsv"
out=$(ORACLE_BASELINE_REGISTRY="$TMP/reg-intact.tsv" guard_oracle_state_attributed 2>&1); rc=$?
arm "GREEN control: same mechanism, intact copy" 0 "$rc"

# --- RED 2: THE ORACLE'S DATABASE IS UNREACHABLE. Must SKIP (rc 0) and SAY SO. This is the
#     carve-out, and it is the one place this guard is deliberately permissive, so it is
#     asserted on BOTH the code and the words: rc 0, and the machine-greppable SKIPPED line.
out=$(ORACLE_BASELINE_DB_CONTAINER="t390-no-such-container-$$" guard_oracle_state_attributed 2>&1); rc=$?
arm "CARVE-OUT: db unreachable SKIPS rather than fails" 0 "$rc"
printf '%s\n' "$out" | grep -q 'ORACLE_STATE_BASELINE = SKIPPED' \
  || { echo "  ***  the skip is SILENT -- that is the fail-open this guard promised not to be"; fail=$((fail+1)); }
printf '%s\n' "$out" | grep -q 'NOT a pass for attribution' \
  || { echo "  ***  the skip did not say it is not a pass"; fail=$((fail+1)); }
echo "  --- CARVE-OUT, what the bar would print ---"
printf '%s\n' "$out" | sed 's/^/  | /'
echo "  --- end CARVE-OUT ---"

# --- RED 3: THE INSTRUMENT IS MISSING. "Did not run" must not read as "clean".
mkdir -p "$TMP/empty-root"
out=$(REPO_ROOT="$TMP/empty-root" guard_oracle_state_attributed 2>&1); rc=$?
arm "RED 3: instrument missing is a REFUSAL" 1 "$rc"
printf '%s\n' "$out" | grep -q 'THE INSTRUMENT IS MISSING' \
  || { echo "  ***  RED 3 refused without naming the cause"; fail=$((fail+1)); }

# --- RED 4: THE INSTRUMENT RETURNS AN UNDECLARED CODE. Fail closed on the unknown. Built by
#     standing up a fake tree whose instrument exits 7.
mkdir -p "$TMP/odd-root/$(dirname "$INSTREL")"
printf '#!/usr/bin/env bash\necho "something the reader has never seen"\nexit 7\n' > "$TMP/odd-root/$INSTREL"
out=$(REPO_ROOT="$TMP/odd-root" guard_oracle_state_attributed 2>&1); rc=$?
arm "RED 4: undeclared exit code is a REFUSAL" 1 "$rc"
printf '%s\n' "$out" | grep -q 'exited 7' \
  || { echo "  ***  RED 4 refused without printing the code it got"; fail=$((fail+1)); }

echo "------------------------------------------------------------------------"
echo "ARMS: $pass ok, $fail failed"
if [ "$fail" -ne 0 ]; then
  echo "DRIVE VERDICT: THE PROPOSED GUARD DOES NOT BEHAVE AS DOCUMENTED (exit 1)."
  exit 1
fi
echo "DRIVE VERDICT: driven RED on four conditions and GREEN on two controls (exit 0)."
exit 0
