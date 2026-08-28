#!/usr/bin/env bash
# T340 / P-22 — "construct an input the guard should refuse and does not."
#
# T258's cardinal-restatement census pins by (RULE, FILE): see
# .softhouse/capture/t255-frontier-rot/instruments/20-cardinal-restatement-census.py:379
#     got = sorted({"%s %s" % (tag, rel) for tag, rel, _n, _t in hits})
# The line number is discarded by the set. T258's own red drive
# (50-census-red-drive.sh:39-42, PLANT="$R/$PDIR/planted-restatement.sh") plants only into a
# file that is NOT on the pin, so the (rule, file) collision case was never driven.
#
# THIS PROBE plants a brand-new typed frontier cardinal INTO A FILE ALREADY ON THE PIN, under a
# rule already pinned for that file. If the census is a frontier, it must refuse. Measured below.
#
# Runs against a scratch worktree given as $1; mutates and restores it.
set -u
W="${1:?scratch worktree}"
C=".softhouse/capture/t255-frontier-rot/instruments/20-cardinal-restatement-census.py"
V=".softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh"
cd "$W" || exit 2
echo "T340 CENSUS DUPLICATE PROBE in $W at $(git rev-parse HEAD)"
restore() { git checkout -- "$V" 2>/dev/null; }
trap restore EXIT

echo
echo "== BASELINE — census on the unmutated tree =="
python3 "$C" > /tmp/t340-p30-base.txt 2>&1
echo "  exit=$?  (want 0)"
LC_ALL=C /usr/bin/grep -a 'PIN MATCHED\|PIN COMPARISON' /tmp/t340-p30-base.txt | LC_ALL=C /usr/bin/sed 's/^/    | /'

echo
echo "== PERTURB — append a NEW typed cardinal to $V, which is ALREADY on the pin under R2 =="
printf 'value "frontier count DUPLICATE PLANTED BY T340" "frontier 11, pinned at 11."\n' >> "$V"
echo "  perturbation landed (want 1): $(LC_ALL=C /usr/bin/grep -c 'DUPLICATE PLANTED BY T340' "$V")"

echo
echo "== MEASURE — does the census refuse? =="
python3 "$C" > /tmp/t340-p30-dup.txt 2>&1
rc=$?
echo "  exit=$rc   <-- 0 means IT DID NOT REFUSE"
echo "  the planted line IS reported (hits): $(LC_ALL=C /usr/bin/grep -ac 'DUPLICATE PLANTED BY T340' /tmp/t340-p30-dup.txt)"
LC_ALL=C /usr/bin/sed -n '/PIN COMPARISON/,$p' /tmp/t340-p30-dup.txt | LC_ALL=C /usr/bin/sed 's/^/    | /'
echo
if [ "$rc" -eq 0 ]; then
  echo "  *** F-T340-2 CONFIRMED: a NEW typed frontier cardinal in an ALREADY-PINNED file leaves"
  echo "  *** the pin MATCHED and the census exit 0. FU-6's proposed wiring gates on \`rc -ne 0\`,"
  echo "  *** so wiring it as written would install a guard blind to this shape."
else
  echo "  the census refused (exit $rc) — F-T340-2 would not reproduce."
fi
restore
echo
echo "  restored; planted lines remaining (want 0): $(LC_ALL=C /usr/bin/grep -c 'DUPLICATE PLANTED BY T340' "$V")"
echo "T340 CENSUS DUPLICATE PROBE DONE"
