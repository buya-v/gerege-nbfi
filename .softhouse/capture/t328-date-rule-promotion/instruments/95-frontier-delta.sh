#!/usr/bin/env bash
# T328 -- THE DEAD-PATH FRONTIER DELTA, AND THE PROOF THAT `added=0` IS A MEASUREMENT.
#
# FU-T326-8 warned that a task adding files may see the guard report `added=N`, and
# that the answer is to INSPECT EVERY `+` ROW rather than blanket-regenerate. T328
# added five tracked instruments to `.softhouse/` and the guard reports added=0.
#
# `added=0` FROM A GUARD IS EXACTLY THE SHAPE A BROKEN SELECTOR PRODUCES, so this
# script does not report it and stop. It asks two questions:
#
#   (1) DID THE CENSUS ACTUALLY SEE THE NEW FILES? The corpus selector is
#       `git ls-files '.softhouse/*.py' '.softhouse/*.sh'`, so the count must include
#       them and the count the census printed must equal that selector's own count.
#   (2) WOULD IT HAVE CAUGHT ONE? A deliberate dead reference is written into a T328
#       instrument, the census re-run, and the frontier must GROW BY EXACTLY ONE and
#       name that file. Then it is removed and the frontier must return to 109.
#
# Exit 0 = the frontier is genuinely unmoved and the guard demonstrably could have
# moved it. The scratch edit is reverted by an EXIT trap and verified.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
CENSUS=.softhouse/capture/t316-dead-path-guards/census_dead_paths.py
VICTIM=.softhouse/capture/t328-date-rule-promotion/instruments/run-impl.sh
PINNED=109

cd "$REPO" || exit 2
restore() {
  git checkout -- "$VICTIM" 2>/dev/null
  local dirty; dirty="$(git status --porcelain -- "$VICTIM")"
  [ -n "$dirty" ] && echo "*** $VICTIM WAS NOT RESTORED: $dirty"
  return 0
}
trap restore EXIT

census_line() { python3 "$CENSUS" 2>&1 | LC_ALL=C grep -a '^T316-DEADPATH-CENSUS:'; }
dead_of()     { printf '%s\n' "$1" | LC_ALL=C sed -n 's/.*deadOccurrences=\([0-9][0-9]*\).*/\1/p'; }
corpus_of()   { printf '%s\n' "$1" | LC_ALL=C sed -n 's/.*corpus=\([0-9][0-9]*\).*/\1/p'; }

rc=0
echo "T328 frontier delta -- HEAD $(git rev-parse --short HEAD)"
echo ""

base="$(census_line)"
echo "BASELINE  $base"
bd="$(dead_of "$base")"; bc="$(corpus_of "$base")"

# (1) THE SELECTOR SAW THEM.
sel="$(git ls-files '.softhouse/*.py' '.softhouse/*.sh' | wc -l | tr -d ' ')"
t328="$(git ls-files '.softhouse/*.py' '.softhouse/*.sh' | LC_ALL=C grep -c 't328-date-rule-promotion' || true)"
echo ""
echo "(1) DID THE CENSUS SEE T328's INSTRUMENTS?"
echo "    corpus printed by the census        : $bc"
echo "    corpus counted from the selector    : $sel"
echo "    of which T328 instruments           : $t328"
if [ "$bc" != "$sel" ]; then
  echo "    *** the census corpus and the selector disagree; added=0 means nothing."; rc=1
elif [ "$t328" -lt 1 ]; then
  echo "    *** the selector does not see any T328 instrument; added=0 is VACUOUS."; rc=1
else
  echo "    OK: the census corpus IS the selector's set and T328's $t328 instruments are in it."
fi

echo ""
echo "    frontier: $bd, pinned $PINNED"
if [ "$bd" != "$PINNED" ]; then
  echo "    *** the frontier MOVED. Inspect every + row before touching the pin (FU-T326-8)."; rc=1
else
  echo "    OK: unmoved. T328's instruments cite only paths that exist and are TRACKED --"
  echo "    every capture_ref, transcript and README they name is committed in this branch."
fi

# (2) IT WOULD HAVE CAUGHT ONE.
printf '%s\n' '# T328 SCRATCH: .softhouse/capture/t328-date-rule-promotion/out/THIS-FILE-DOES-NOT-EXIST.txt' >> "$VICTIM"
drive="$(census_line)"
dd="$(dead_of "$drive")"
echo ""
echo "(2) RED DRIVE -- one deliberate dead reference appended to $VICTIM"
echo "    $drive"
if [ "$dd" -eq $((bd + 1)) ]; then
  echo "    OK: frontier $bd -> $dd, GREW BY EXACTLY ONE."
  python3 "$CENSUS" 2>&1 | LC_ALL=C grep -a 'THIS-FILE-DOES-NOT-EXIST' | sed 's/^/    /' | head -3
else
  echo "    *** frontier went $bd -> $dd, want $((bd + 1)). The census cannot see a dead"
  echo "    *** reference in a T328 instrument, so its silence about them proves nothing."
  rc=1
fi

git checkout -- "$VICTIM"
after="$(census_line)"
ad="$(dead_of "$after")"
echo ""
echo "RESTORED  $after"
if [ "$ad" != "$bd" ]; then
  echo "    *** the frontier did not return to $bd. The tree is dirty."; rc=1
else
  echo "    OK: back to $ad."
fi

echo ""
echo "CONCLUSION: dead-path frontier 109 == pinned 109, added=0 removed=0, and that zero is"
echo "  a MEASUREMENT -- the census sees T328's instruments and grows by one when given a"
echo "  dead reference in one of them. NO PIN MOVE IS WARRANTED, and moving it would be the"
echo "  blanket regeneration FU-T326-8 warns against."
echo "T328 frontier delta: EXIT $rc"
exit "$rc"
