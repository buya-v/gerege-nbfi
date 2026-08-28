#!/usr/bin/env bash
# T307 instrument 30 -- IS LDG-REFUSE-06 LOAD-BEARING, OR IS IT CORPUS INFLATION?
#
# T295 refused to promote A2-02 because it "would raise the corpus count by one and
# the kill count by zero". That refusal was correct on the shape as it stood. This
# instrument MEASURES whether it is still true now that a fourth cell exists, rather
# than asserting that it is not -- because "we added a cell, therefore the vector
# now earns its place" is exactly the self-certifying claim this store refuses.
#
# THREE ARMS:
#   A  new mutant vs the FULL store              -> must DIE, on LDG-REFUSE-06 only
#   B  new mutant vs the store MINUS LDG-REFUSE-06 -> must SURVIVE   (load-bearing)
#   C  correct port vs the FULL store            -> must PASS        (anti-vacuity)
#
# Arm B is the one that carries the argument. Without it, arm A only shows that the
# mutant dies somewhere.
#
# NO ORACLE CONTACT: `-oracle-probe=skipped`, and the ledger comparator replays
# captured bytes against a port. Nothing is posted anywhere, and nothing is read
# from the reference oracle either.
#
# THE ARMS ARE JUDGED ON THE LEDGER REFUSAL **FAIL COUNT**, NOT ON THE PROCESS
# EXIT, and that distinction is the instrument's own P-84 discipline. With the
# probe declared `skipped` the binary is exit 2 on EVERY arm by construction -- "no
# trustworthy verdict is available" -- so an arm keyed on the exit code would read
# every arm as a death and report LOAD-BEARING no matter what the comparator did.
# The quantity this measurement is about is "how many oracle-refusal vectors did
# this implementation fail", so that is the quantity it reads. Measured, not
# assumed: the first draft of this instrument keyed on the exit code and reported
# arms B and C as failures while their ledger halves were clean.
#
# Run with bash, never sh. EXIT: 0 all three arms as expected; 2 otherwise.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
RIG="$(dirname "$HERE")"
REPO="$(cd "$RIG/../../.." && pwd)"
OUT="$RIG/out"
MUTANT="ledger-wrong-accounting-closed-echoes-transaction-date"
VECTOR="LDG-REFUSE-06-preclosure-entry-before-closing-date-echoes-the-closing-date.json"
PROBE="T307-LOADBEARING:"

mkdir -p "$OUT"
rc=0

drive() { # <store-root> <impl> <outfile>
  ( cd "$REPO/nexus" && go run ./internal/apps/loanschedule/conformance/cmd/conformance \
      -oracle-probe=skipped -store="$1" -ledger-impl="$2" ) >"$3" 2>&1
  echo $?
}

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
cp -R "$REPO/.softhouse/vectors/." "$scratch/"
if [ ! -f "$scratch/ledger/$VECTOR" ]; then
  echo "$PROBE FATAL the scratch copy has no $VECTOR; arm B would measure nothing" >&2
  exit 2
fi
rm -f "$scratch/ledger/$VECTOR"

a_exit="$(drive "$REPO/.softhouse/vectors" "$MUTANT" "$OUT/10-armA-mutant-full-store.txt")"
b_exit="$(drive "$scratch"                 "$MUTANT" "$OUT/20-armB-mutant-without-LDG-REFUSE-06.txt")"
c_exit="$(drive "$REPO/.softhouse/vectors" "ledger-go" "$OUT/30-armC-correct-port-full-store.txt")"

refline() { LC_ALL=C grep -a '^ *ledger oracle-refusal ' "$1" | head -1 | sed 's/^ *//;s/  */ /g;s/ (.*//'; }
# refusalfail prints the FAIL figure, or `?` if the line is absent -- and `?` is
# never treated as a number, so a run that printed no ledger section refuses
# rather than scoring 0 (P-84: read the ABSENCE, not the value).
refusalfail() {
  LC_ALL=C sed -n 's/^ *ledger oracle-refusal  *PASS [0-9][0-9]*  *FAIL \([0-9][0-9]*\).*$/\1/p' "$1" \
    | head -1 | grep -E '^[0-9]+$' || echo '?'
}
cell()    { LC_ALL=C grep -a 'refusal.arg0_value' "$1" | head -1 | sed 's/^ *//'; }
which()   { LC_ALL=C grep -aE '^ *LDG-[A-Z0-9.-]+.*FAIL' "$1" | sed 's/^ *//;s/ .*//'; }

a_fail="$(refusalfail "$OUT/10-armA-mutant-full-store.txt")"
b_fail="$(refusalfail "$OUT/20-armB-mutant-without-LDG-REFUSE-06.txt")"
c_fail="$(refusalfail "$OUT/30-armC-correct-port-full-store.txt")"

echo "$PROBE ARM A  mutant vs FULL store          binexit=$a_exit  $(refline "$OUT/10-armA-mutant-full-store.txt")"
echo "$PROBE   diverged on: $(which "$OUT/10-armA-mutant-full-store.txt" | tr '\n' ' ')"
echo "$PROBE   cell:        $(cell "$OUT/10-armA-mutant-full-store.txt")"
echo "$PROBE ARM B  mutant WITHOUT LDG-REFUSE-06  binexit=$b_exit  $(refline "$OUT/20-armB-mutant-without-LDG-REFUSE-06.txt")"
echo "$PROBE ARM C  correct port vs FULL store    binexit=$c_exit  $(refline "$OUT/30-armC-correct-port-full-store.txt")"
echo "$PROBE   (binexit is 2 on ALL THREE by construction -- the probe is declared skipped. The"
echo "$PROBE    verdict below reads the ledger oracle-refusal FAIL counts: A=$a_fail B=$b_fail C=$c_fail)"

if [ "$a_fail" != "1" ]; then
  echo "$PROBE FAIL arm A: ledger oracle-refusal FAIL is $a_fail, want exactly 1. The mutant must" >&2
  echo "$PROBE      die on LDG-REFUSE-06 and on NOTHING ELSE -- a wider kill would mean it is" >&2
  echo "$PROBE      failing for a defect it does not claim to have" >&2; rc=2
fi
if [ "$b_fail" != "0" ]; then
  echo "$PROBE FAIL arm B: ledger oracle-refusal FAIL is $b_fail, want 0. The mutant died WITHOUT" >&2
  echo "$PROBE      LDG-REFUSE-06, so something else already killed it and the new vector is not" >&2
  echo "$PROBE      load-bearing -- exactly the corpus inflation T295 refused to commit" >&2; rc=2
fi
if [ "$c_fail" != "0" ]; then
  echo "$PROBE FAIL arm C: the CORRECT port fails $c_fail refusal vector(s) on the full store, so" >&2
  echo "$PROBE      arms A and B could both be measuring a harness defect" >&2; rc=2
fi

if [ "$rc" -eq 0 ]; then
  echo "$PROBE VERDICT LOAD-BEARING: the mutant dies with LDG-REFUSE-06 and survives without it,"
  echo "$PROBE   and the correct port passes both. Kill count +1, not +0."
else
  echo "$PROBE VERDICT REFUSED"
fi
exit "$rc"
