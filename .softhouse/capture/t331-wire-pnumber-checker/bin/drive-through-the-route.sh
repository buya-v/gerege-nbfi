#!/usr/bin/env bash
# T331 -- DRIVE THE WIRED GUARD RED AND GREEN **THROUGH conformance.sh ITSELF**.
#
# THIS IS THE ONE THING T282 EXPLICITLY COULD NOT VERIFY AND SAID SO: that the guard fails
# through the route that runs it, not merely when invoked by hand. T282 drove its extracted
# function directly (wiring/10-GREEN, wiring/20-RED) and wrote: "What is still UNPROVEN, and
# must be proven by whoever applies it: that it fails THROUGH THE ROUTE THAT RUNS IT."
#
# THE FIXTURE IS REAL BYTES, NOT AN INVENTION. The planted line is copied verbatim from
# .softhouse/capture/t255-dec2-rev8/instruments/20-verify-anchors.py:36 -- row 2 of the T282
# errata table, a recorded TRUE drift that cites `P-79` while stating the rule patterns.md
# defines under P-80 ("a corrected cardinal rots in every place it was restated"). Measured
# there at grams=4 score=12 cited_score=0, i.e. comfortably over the fatal floor.
#
# THE PLANT GOES IN conformance.sh, WHICH IS DELIBERATE AND IS THE SAFE CHOICE.
#   * it is DIRECTIVE_EXACT, so it is in the only fail-closed zone -- planting anywhere else
#     would drive the report tier, not the fatal tier, and prove nothing about HARD;
#   * T331 is its SOLE WRITER this fire, whereas .softhouse/RESUME.md (T282's suggested
#     fixture site, also DIRECTIVE_EXACT) is written by the orchestrator while workers are
#     live -- P-31, never snapshot a file the orchestrator is actively editing. Planting and
#     reverting there could clobber a concurrent driver write;
#   * and it is the honest drive: the guard fails on the very file it was wired into.
#
# The revert is verified BYTE-IDENTICAL TO THE INDEX with `git diff --quiet`, not by eye.
set -u

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd -P)"
CONF="$ROOT/.softhouse/conformance.sh"
OUT="$ROOT/.softhouse/capture/t331-wire-pnumber-checker/out"
ANCHOR='guard_pnumber_citations() {'
# Verbatim bytes from 20-verify-anchors.py:36. Kept on one line so the extractor sees the
# whole gloss; the correcting id is NOT written adjacent, because T282 measured that an
# adjacent correct id makes the text SELF-CORRECTING and the finding is then suppressed by
# design -- a fixture that self-corrects would drive nothing.
PLANT='# number instead of restating the number (P-79: never fix a rotted number; make the second site READ the first).'

mkdir -p "$OUT"

step() { printf '\n########## %s\n' "$*"; }

step "PRE-FLIGHT: the tree must be clean at the index before planting"
if ! git -C "$ROOT" diff --quiet -- "$CONF"; then
  echo "REFUSED: $CONF already differs from the index. A revert could not then be proven"
  echo "REFUSED: byte-identical, and 'reverted' would be an assertion instead of a measurement."
  exit 3
fi
echo "OK: conformance.sh matches the index."

step "PLANT: insert one verbatim drifted line inside guard_pnumber_citations"
/usr/bin/python3 - "$CONF" "$ANCHOR" "$PLANT" <<'PY'
import sys
p, anchor, plant = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(p, encoding="utf-8").read().splitlines(keepends=True)
hits = [i for i, l in enumerate(lines) if l.rstrip("\n") == anchor]
assert len(hits) == 1, "anchor matched %d times" % len(hits)
lines.insert(hits[0], plant + "\n")
open(p, "w", encoding="utf-8").write("".join(lines))
print("planted at line %d" % (hits[0] + 1))
PY
git -C "$ROOT" diff --stat -- "$CONF"

step "RED: bash .softhouse/conformance.sh  (NEVER sh/zsh/dash)"
( cd "$ROOT" && bash .softhouse/conformance.sh ) >"$OUT/70-RED-through-conformance.txt" 2>&1
RED_RC=$?
echo "EXIT=$RED_RC" >>"$OUT/70-RED-through-conformance.txt"
echo "exit=$RED_RC"
echo "--- probe line count (P-84: read the PRESENCE before the value) ---"
grep -ac 'reference oracle (.*) probe = ' "$OUT/70-RED-through-conformance.txt"
echo "--- the guard's own words ---"
grep -a 'PNUMBER-CITATIONS: FATAL\|A CITED P-NUMBER CARRIES' "$OUT/70-RED-through-conformance.txt"
echo "--- FOR THIS REASON AND NO OTHER: every other guard's refusal line ---"
grep -aE 'REFUSED|FAILED|EXIT 2|a HARD guard failed' "$OUT/70-RED-through-conformance.txt" \
  | grep -av 'PNUMBER' | sort -u

step "REVERT: restore conformance.sh and PROVE it byte-identical to the index"
git -C "$ROOT" checkout -- "$CONF"
if git -C "$ROOT" diff --quiet -- "$CONF"; then
  echo "OK: byte-identical to the index (git diff --quiet)."
else
  echo "FAILED: conformance.sh still differs after revert."
  exit 1
fi

step "GREEN: bash .softhouse/conformance.sh on the reverted tree"
( cd "$ROOT" && bash .softhouse/conformance.sh ) >"$OUT/71-GREEN-through-conformance.txt" 2>&1
GREEN_RC=$?
echo "EXIT=$GREEN_RC" >>"$OUT/71-GREEN-through-conformance.txt"
echo "exit=$GREEN_RC"
grep -a 'probe = \|VERDICT: \|P-number citations: VERDICT PASS' "$OUT/71-GREEN-through-conformance.txt"

step "VERDICT"
rc=0
[ "$RED_RC" = 2 ]   || { echo "FAIL: RED wanted exit 2, got $RED_RC"; rc=1; }
[ "$GREEN_RC" = 0 ] || { echo "FAIL: GREEN wanted exit 0, got $GREEN_RC"; rc=1; }
grep -aq 'PNUMBER-CITATIONS: FATAL' "$OUT/70-RED-through-conformance.txt" \
  || { echo "FAIL: RED printed no PNUMBER-CITATIONS FATAL line"; rc=1; }
[ "$(grep -ac 'reference oracle (.*) probe = ' "$OUT/70-RED-through-conformance.txt")" = 0 ] \
  || { echo "FAIL: RED printed a probe line; a run_guards refusal must precede probe_oracle"; rc=1; }
grep -aq 'P-number citations: VERDICT PASS' "$OUT/71-GREEN-through-conformance.txt" \
  || { echo "FAIL: GREEN did not print the guard's PASS line"; rc=1; }
[ $rc = 0 ] && echo "T331-DRIVE: PASS -- the guard fails THROUGH conformance.sh and recovers." \
            || echo "T331-DRIVE: FAIL"
exit $rc
