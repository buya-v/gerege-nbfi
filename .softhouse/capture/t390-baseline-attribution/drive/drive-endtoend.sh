#!/usr/bin/env bash
# T390 drive-endtoend.sh -- DRIVE THE WIRING AT THE WHOLE-HARNESS LEVEL, not just at the
# function. P-56: a guard is tested where it RUNS, not only where it is defined. The unit drive
# (drive-guard.sh) proves the function's behaviour; this proves that `run_guards` actually
# reaches it and that its verdict reaches the harness's exit code.
#
#   bash .softhouse/capture/t390-baseline-attribution/drive/drive-endtoend.sh
#
# HOW, GIVEN T390 MAY NOT EDIT `.softhouse/conformance.sh`. conformance.sh computes
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" ; REPO_ROOT="$SCRIPT_DIR/.."
# [conformance.sh:398-399], so a copy whose parent directory MIRRORS the real repository root
# grades the real tree. This builds exactly that: a scratch root whose every entry is a SYMLINK
# back into this worktree, except `.softhouse/conformance.sh`, which is the PATCHED copy.
# `CONFORMANCE_REPO_ROOT` is left unset, so guard_graded_root_is_this_tree returns 0 at its
# first line and nothing here is smuggled past that check [conformance.sh:1346-1349].
#
# This is the same shape `t260-dec2-rev8/instruments/50-collision-and-red-drive.sh` uses to
# drive conformance.sh from /tmp, and it is cited in this file's own no-host-state lint corpus.
#
# TWO ARMS, and both matter:
#   GREEN CONTROL -- patched harness, REAL registry. Must exit 0. Without this arm a red proves
#                    only that the harness can be broken, not that the guard discriminates.
#   RED           -- patched harness, registry with L32's attribution row REMOVED. Must exit 2
#                    (EXIT_UNUSABLE) and print the refusal, with NO oracle probe line, because
#                    run_guards is upstream of the probe (P-84).
set -uo pipefail

DRIVE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CAP=$(cd "$DRIVE/.." && pwd)
ROOT=$(cd "$CAP/../../.." && pwd)
PATCHED="$CAP/out/conformance-PATCHED.sh"
REG="$ROOT/.softhouse/capture/t363-oracle-baseline/PROBES.tsv"
OUT="$CAP/out"

[ -f "$PATCHED" ] || { echo "REFUSING: no patched harness. Run make-patch.sh first." >&2; exit 2; }

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t390-e2e.XXXXXX") || exit 2
SR="$SCRATCH/root"
mkdir -p "$SR/.softhouse" || exit 2
trap 'rm -rf "$SCRATCH"' EXIT

# THE SCRATCH ROOT IS A REAL COPY, NOT A SYMLINK FARM, AND THAT WAS MEASURED RATHER THAN
# ANTICIPATED. Two earlier versions of this drive symlinked the tree. Both had a PASSING RED arm
# and a FAILING GREEN CONTROL, for reasons that have nothing to do with this patch: this
# harness's censuses walk the filesystem, and a directory walker does not descend a symlink.
#   attempt 1 (symlink everything): `ledgerguard` -> "REFUSED — INSPECTED ZERO Go files under
#     .../root/nexus"; bar exit 2 while the wired guard's own line read ALL MOVEMENT ATTRIBUTED.
#     [out/E2E-GREEN-selftest-FIRST-ATTEMPT.txt]
#   attempt 2 (materialise nexus + .softhouse/guards): ledgerguard passed, and TWO more surfaced
#     -- "guard_no_float_in_vectors INSPECTED ZERO FILES under .../root/.softhouse/vectors" and
#     "REFUSED — INSPECTED 0 .java FILES across 0 DIRECTORIES under .../root".
#     [out/E2E-GREEN-selftest-SECOND-ATTEMPT.txt]
# Chasing them one at a time is whack-a-mole against a whole class, so the class is removed:
# everything is copied and only `.git` is a symlink. A GREEN CONTROL THAT FAILS FOR AN UNRELATED
# REASON PROVES NOTHING, and quietly deleting the control rather than repairing it would have
# been the worse half of the same choice. ~241M and a few seconds; this is a drive, not the bar.
#
# Note what those two failures also demonstrate, for free: these censuses are fail-CLOSED on an
# empty population. That is the property T374/T382 spent a fire establishing elsewhere, and it
# held here without being asked.
for e in "$ROOT"/* "$ROOT"/.[!.]*; do
  [ -e "$e" ] || continue
  b=$(basename "$e")
  [ "$b" = ".softhouse" ] && continue
  # `.git` is the ONLY symlink. Everything else is materialised.
  if [ "$b" = ".git" ]; then ln -s "$e" "$SR/$b" || exit 2
  else cp -R "$e" "$SR/$b" || exit 2; fi
done
for e in "$ROOT"/.softhouse/* "$ROOT"/.softhouse/.[!.]*; do
  [ -e "$e" ] || continue
  b=$(basename "$e")
  [ "$b" = "conformance.sh" ] && continue
  cp -R "$e" "$SR/.softhouse/$b" || exit 2
done
cp "$PATCHED" "$SR/.softhouse/conformance.sh" || exit 2

echo "T390 END-TO-END DRIVE -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  real root    : $ROOT"
echo "  scratch root : $SR   (all symlinks except .softhouse/conformance.sh)"
echo "  CONFORMANCE_REPO_ROOT is UNSET, deliberately."
echo "------------------------------------------------------------------------"

pass=0; fail=0
note() { printf '  %s\n' "$*"; }

# ---------- GREEN CONTROL -------------------------------------------------------------
echo "GREEN CONTROL: patched harness, REAL registry, --self-test"
go=$(bash "$SR/.softhouse/conformance.sh" --self-test 2>&1); grc=$?
printf '%s\n' "$go" > "$OUT/E2E-GREEN-selftest.txt"
if [ "$grc" -eq 0 ]; then note "ok   exit 0"; pass=$((pass+1)); else note "***  exit $grc, expected 0"; fail=$((fail+1)); fi
if printf '%s\n' "$go" | LC_ALL=C grep -q 'ALL MOVEMENT ATTRIBUTED'; then
  note "ok   the wired guard RAN and passed"; pass=$((pass+1))
else
  note "***  the wired guard did not print its pass line -- run_guards may not reach it"; fail=$((fail+1))
fi
printf '%s\n' "$go" | LC_ALL=C grep -aE 'oracle-state baseline|ALL MOVEMENT ATTRIBUTED' | sed 's/^/  | /'

# ---------- RED -----------------------------------------------------------------------
echo ""
echo "RED: patched harness, registry with L32's attribution row REMOVED, --self-test"
grep -v '^txn	L32	' "$REG" > "$SCRATCH/reg-no-L32.tsv"
b=$(grep -c '^txn	L32	' "$REG"); a=$(grep -c '^txn	L32	' "$SCRATCH/reg-no-L32.tsv")
note "(fixture calibration: L32 rows $b -> $a)"
[ "$b" = "1" ] || { note "***  fixture not calibrated"; fail=$((fail+1)); }

ro=$(ORACLE_BASELINE_REGISTRY="$SCRATCH/reg-no-L32.tsv" bash "$SR/.softhouse/conformance.sh" --self-test 2>&1); rrc=$?
printf '%s\n' "$ro" > "$OUT/E2E-RED-selftest.txt"
if [ "$rrc" -eq 2 ]; then note "ok   exit 2 (EXIT_UNUSABLE)"; pass=$((pass+1)); else note "***  exit $rrc, expected 2"; fail=$((fail+1)); fi
if printf '%s\n' "$ro" | LC_ALL=C grep -q 'UNATTRIBUTED MOVEMENT IN THE SHARED REFERENCE ORACLE'; then
  note "ok   the harness printed the refusal"; pass=$((pass+1))
else
  note "***  the harness exited without naming the condition"; fail=$((fail+1))
fi
# P-84: PRESENCE before value. run_guards is upstream of the probe, so a guard refusal must
# carry NO probe line at all. "EXIT 2 WITH NO PROBE LINE IS THE GUARD WORKING."
pn=$(printf '%s\n' "$ro" | LC_ALL=C grep -c 'probe = ')
if [ "$pn" -eq 0 ]; then
  note "ok   P-84: the refusal carries NO 'probe = ' line (count 0) -- guard, not outage"; pass=$((pass+1))
else
  note "***  P-84: the refusal carried $pn 'probe = ' lines; it would be misread as an outage"; fail=$((fail+1))
fi
printf '%s\n' "$ro" | LC_ALL=C grep -aE 'UNATTRIBUTED|L32 |a HARD guard failed' | sed 's/^/  | /'

echo "------------------------------------------------------------------------"
echo "ARMS: $pass ok, $fail failed"
[ "$fail" -eq 0 ] || { echo "E2E VERDICT: THE WIRING DOES NOT BEHAVE AS CLAIMED (exit 1)."; exit 1; }
echo "E2E VERDICT: wired guard drives the WHOLE HARNESS red, and a healthy control green (exit 0)."
