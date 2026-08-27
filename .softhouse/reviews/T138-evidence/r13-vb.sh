#!/bin/sh
# T138 — V-B: is verdict.sh's resistance to a DEAD ORACLE really an accident of
# which rows happen to be CLEAN?  Measure it, then measure the counterfactual.
set -u
W=${1:?workdir}
POSTV=$W/post/.softhouse/capture/t91/verdict.sh
D=/tmp/T138-vb; rm -rf "$D"; mkdir -p "$D/dead"

# A dead-oracle transcript: the rig runs, every oracle-dependent check FAILs, the
# certification sentence is never printed, exit 1.  Same shape for all 13.
for n in A2a-mutated-canary-gerege A2b-mutated-canary-default \
         A2c-crafted-canary-and-expectation-gerege A3a-swapped-canary-gerege \
         A3b-missing-canary A3c-no-canary A4a-expect-override-default \
         A4b-expect-override-gerege A4c-decoy-variable A5-helpful-correct-override \
         A6-canary-is-a-directory A7-symlinked-canary A8-foreign-cwd; do
  {
    echo "=== $n"
    echo "recipe under test: .softhouse/capture/charges/bin/preconditions.sh"
    echo "interpreter:       sh    cwd: /repo"
    echo
    echo "== T36 Path B preconditions, tenant 'gerege' =="
    echo "  FAIL  actuator/health unreachable — the oracle never answered"
    echo "  FAIL  rounding-mode canary returned no HTTP status — the mode in force was never established"
    echo
    echo "PRECONDITIONS BREACHED: 2. DO NOT CAPTURE."
    echo
    echo "EXIT=1"
  } > "$D/dead/$n.txt"
done

echo "=================================================================="
echo "A. the SHIPPED expectation table, over 13 dead-oracle transcripts"
echo "=================================================================="
sh "$POSTV" "$D/dead"; echo "EXIT=$?"
echo

echo "=================================================================="
echo "B. the counterfactual: retype ONE CLEAN row (A7) to BREACH"
echo "=================================================================="
cp "$POSTV" "$D/verdict-A7-breach.sh"
LC_ALL=C sed -i.bak 's|^A7-symlinked-canary.txt|BREACH|A7-symlinked-canary.txt|BREACH|' "$D/verdict-A7-breach.sh" 2>/dev/null
LC_ALL=C sed -i.bak2 's|^A7-symlinked-canary.txt\|CLEAN\|PINNED|A7-symlinked-canary.txt\|BREACH\|PINNED|' "$D/verdict-A7-breach.sh"
rm -f "$D"/verdict-A7-breach.sh.bak*
LC_ALL=C grep -n '^A7-' "$D/verdict-A7-breach.sh" | sed 's/^/   /'
sh "$D/verdict-A7-breach.sh" "$D/dead" | tail -6; sh "$D/verdict-A7-breach.sh" "$D/dead" >/dev/null 2>&1; echo "EXIT=$?"
echo

echo "=================================================================="
echo "C. the counterfactual that matters: ALL THREE CLEAN rows -> BREACH"
echo "=================================================================="
cp "$POSTV" "$D/verdict-all-breach.sh"
for r in A4c-decoy-variable A7-symlinked-canary A8-foreign-cwd; do
  LC_ALL=C sed -i.bak "s|^$r.txt|CLEAN|$r.txt|BREACH|" "$D/verdict-all-breach.sh" 2>/dev/null
  LC_ALL=C sed -i.bak2 "s|^$r.txt\\|CLEAN\\||$r.txt\\|BREACH\\||" "$D/verdict-all-breach.sh"
done
rm -f "$D"/verdict-all-breach.sh.bak*
LC_ALL=C grep -nE '^A4c-|^A7-|^A8-' "$D/verdict-all-breach.sh" | sed 's/^/   /'
sh "$D/verdict-all-breach.sh" "$D/dead"; echo "EXIT=$?"
echo
echo "   <- a CLEAN SWEEP reported over an oracle that never answered."
echo

echo "=================================================================="
echo "D. does anything ELSE in the rig notice a dead oracle?"
echo "=================================================================="
echo "-- does any row REQUIRE the certification sentence to be PRESENT?"
LC_ALL=C grep -n 'NEVER\|PINNED\|REQUIRED' "$POSTV" | LC_ALL=C grep -v '^ *#' | sed 's/^/   /'
echo
echo "   NEVER  = the sentence must not appear."
echo "   PINNED = it MAY appear, but only with a passing pin."
echo "   There is no value meaning 'it MUST appear', so no row asserts the"
echo "   oracle answered.  The only thing standing between a dead oracle and a"
echo "   clean sweep is that three rows expect exit 0."
