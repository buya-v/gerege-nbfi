#!/bin/bash
# T416 — driving the F-T405-4 REQUEST against real transcripts.
#
# `.softhouse/conformance.sh` is held by T404 this wave, so the two proposed
# pins are shipped as a REQUEST rather than an edit. This script drives the
# PATCH'S OWN LOGIC — the two _census_one extraction expressions and the two
# _cmp comparisons — against the transcripts e4drive.sh produced, so the request
# arrives with a red-before/green-after rather than with a proposal.
#
# It also re-extracts the FOUR EXISTING pinned figures from the same
# transcripts, because the claim being made is not "a new pin would fire" but
# "no existing pin fires", and only the second half is a hole.
set -u
ROOT="${1:?repo root}"
OUT="$ROOT/.softhouse/capture/t416-t405-conditions/out"

# The four pins .softhouse/conformance.sh holds today (lines 524, 681-683).
PIN_DECLARED=0
PIN_PARITY=10
PIN_REFUSAL=6
PIN_MONEYCELLS=63
# The two this request adds.
PIN_INADMISSIBLE=0
PIN_DIVERGENCE_PASS=1

x() { LC_ALL=C sed -n "$2" "$1" | head -1; }

report() {
  local label="$1"
  local f="$OUT/e4-$label.log"
  local declared parity refusal money inadm divpass
  declared="$(x "$f" 's/^ *ledger exemptions  *\([0-9][0-9]*\) DECLARED.*$/\1/p')"
  parity="$(x "$f" 's/^ *ledger parity  *PASS \([0-9][0-9]*\)  *FAIL [0-9][0-9]*$/\1/p')"
  refusal="$(x "$f" 's/^ *ledger oracle-refusal  *PASS \([0-9][0-9]*\)  *FAIL [0-9][0-9]*.*$/\1/p')"
  money="$(x "$f" 's/^ *ledger cells compared  *[0-9][0-9]* graded, of which \([0-9][0-9]*\) are MONEY cells.*$/\1/p')"
  # THE TWO NEW EXTRACTIONS, in the same shape as the four above.
  inadm="$(x "$f" 's/^ *ledger inadmissible  *\([0-9][0-9]*\).*$/\1/p')"
  divpass="$(x "$f" 's/^ *divergence vectors  *PASS \([0-9][0-9]*\)  *FAIL [0-9][0-9]*.*$/\1/p')"

  local existing="GREEN" proposed="GREEN"
  [ "$declared" = "$PIN_DECLARED" ] || existing="RED"
  [ "$parity"   = "$PIN_PARITY"   ] || existing="RED"
  [ "$refusal"  = "$PIN_REFUSAL"  ] || existing="RED"
  [ "$money"    = "$PIN_MONEYCELLS" ] || existing="RED"
  [ "$inadm"    = "$PIN_INADMISSIBLE" ] || proposed="RED"
  [ "$divpass"  = "$PIN_DIVERGENCE_PASS" ] || proposed="RED"

  printf '%-24s declared=%-2s parity=%-2s refusal=%-2s money=%-2s | inadm=%-2s divPASS=%-2s || FOUR EXISTING PINS: %-5s  TWO PROPOSED PINS: %s\n' \
    "$label" "$declared" "$parity" "$refusal" "$money" "$inadm" "$divpass" "$existing" "$proposed"
}

echo "A figure that is EMPTY below was not extractable, which is itself a defect (_census_one"
echo "refuses on a missing line). All six must be present on every row."
echo
report baseline
report divergence-inadmissible
report parity-inadmissible
echo
echo "READ: the divergence row is the finding. The four pins the bar holds today are all GREEN"
echo "on a store whose ONLY divergence vector was refused admission — the class T397 routes a new"
echo "refusal into is the one class whose disappearance moves no pinned number. The parity row is"
echo "the control: an inadmissible PARITY vector is already caught, twice over (parity and money)."
