#!/bin/sh
# T151 — drive V-B: verdict.sh's resistance to a DEAD ORACLE was an accident of the data, and this
# is the nine-line assertion that turns it into a decision.  T115 found the hazard and declined to
# fix it ("changing the expectation table is a substantive act"); T138 ruled report-not-fix the
# WRONG call and supplied a fix that CHANGES NO ROW.  This driver is that fix's evidence.
#
# It also CORRECTS T115's own statement of the hazard, which overstated it 3x.  T115 wrote that
# retyping ANY ONE of A4c/A7/A8 from CLEAN to BREACH creates a scorer that reports a clean sweep
# over an oracle that never answered.  Leg 3 below measures that it does not: retyping one still
# exits 1 with two REGRESSION rows.  It takes ALL THREE.
#
# THREE LEGS, plus the correction:
#   L1  NO-OP     — every committed transcript directory scores identically under the shipped and
#                   the patched scorer.  20 directory-instances: the 12 scoreable directories on
#                   the POST tree, plus the 8 that existed at T91's tip.  (`happy/` is not a
#                   verdict.sh input and is excluded, as it always has been.)
#   L2  RED       — 13 dead-oracle transcripts: shipped exit 1 (accidental), patched exit 3.
#   L3  CORRECTION— dead oracle + ONE row retyped (A7), shipped scorer: exit 1, two REGRESSION rows.
#   L4  RED       — dead oracle + ALL THREE retyped: shipped exit 0 and `ALL 13 …`; patched exit 3.
#
# PRE  = a LITERAL IMMUTABLE SHA (P-24: never a ref computed from `main`).
# POST = HEAD — the tree under test, not a baseline.
#
# THE ORACLE IS NEVER CONTACTED.  Every transcript here is synthetic or already committed; nothing
# below runs the rig, and nothing restarts, rebuilds, re-seeds or writes to Fineract.
#
# Usage:  sh t151-drive-vb.sh
# Exit:   0 = every leg behaved as specified; 1 = a leg did not; 2 = the harness could not set up.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
PRE_SHA=8c05f9a7190ee1e0f8be09b92bdccc02d62ea103   # main at the T151 fork point — LITERAL, IMMUTABLE
T91_SHA=ccf3c14171dea52bd044d81d5ca67aba8054b74c   # T91's tip — LITERAL, IMMUTABLE (8 out/ dirs)
POST_SHA=$(cd "$ROOT" && git rev-parse HEAD)
S=/tmp/t151-vb.$$
trap 'rm -rf "$S"' EXIT
mkdir -p "$S"
BAD=0
SENT='PASS  effective rounding mode canary'

note() { printf '  %-58s %s\n' "$1" "$2"; }
check() {  # check <label> <observed> <wanted>
  if [ "$2" = "$3" ]; then printf '  %-58s %s (want %s)   OK\n' "$1" "$2" "$3"
  else printf '  %-58s %s (want %s)   *** NOT AS SPECIFIED ***\n' "$1" "$2" "$3"; BAD=$((BAD+1)); fi
}

echo "PRE  = $PRE_SHA  (literal immutable sha — the shipped scorer)"
echo "POST = $POST_SHA  (HEAD — the tree under test)"
echo "T91  = $T91_SHA  (literal immutable sha — for the 8 older transcript dirs)"
echo

PREV=$S/verdict-PRE.sh
POSTV=$S/verdict-POST.sh
(cd "$ROOT" && git show "$PRE_SHA:.softhouse/capture/t91/verdict.sh")  > "$PREV"  || { echo "ABORT: no PRE verdict.sh" >&2; exit 2; }
(cd "$ROOT" && git show "$POST_SHA:.softhouse/capture/t91/verdict.sh") > "$POSTV" || { echo "ABORT: no POST verdict.sh" >&2; exit 2; }

# The PRE scorer must NOT already carry the assertion, or L2/L4 prove nothing.
if LC_ALL=C /usr/bin/grep -aqF 'never reached a live oracle' "$PREV"; then
  echo "ABORT: the PRE scorer already carries the V-B assertion — move PRE_SHA back." >&2; exit 2; fi
LC_ALL=C /usr/bin/grep -aqF 'never reached a live oracle' "$POSTV" || {
  echo "ABORT: the POST scorer does NOT carry the V-B assertion — there is nothing to prove." >&2; exit 2; }
echo "asserted: PRE lacks the V-B assertion, POST carries it."
echo

# ---------------------------------------------------------------- the dead-oracle transcript set
# The rig ran, every oracle-dependent check FAILed, the certification sentence was never printed,
# exit 1.  Same shape for all thirteen — this is what an outage looks like on disk.
mkdir -p "$S/dead"
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
  } > "$S/dead/$n.txt"
done
if LC_ALL=C /usr/bin/grep -alF "$SENT" "$S/dead"/A*.txt >/dev/null 2>&1; then
  echo "ABORT: the synthetic dead-oracle set contains the certification sentence — it is not a" >&2
  echo "       dead-oracle set at all and neither RED leg would mean anything." >&2; exit 2; fi
echo "asserted: not one of the 13 dead-oracle transcripts carries the certification sentence."
echo

retype() {  # retype <src verdict.sh> <dst> <row...>
  src=$1; dst=$2; shift 2
  python3 - "$src" "$dst" "$@" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
for r in sys.argv[3:]:
    old = r + '|CLEAN|'
    assert old in s, 'ABORT: row %s is not CLEAN in %s — the retype would be a no-op' % (r, src)
    s = s.replace(old, r + '|BREACH|')
open(dst, 'w').write(s)
PY
  [ $? -eq 0 ] || { echo "ABORT: retype did not apply" >&2; exit 2; }
}

echo "=== L1  NO-OP on every committed transcript directory (shipped exit == patched exit)"
same=0; total=0
score_dirs() {  # score_dirs <label> <sha>
  ck=$S/ck-$1
  rm -rf "$ck"
  git clone --quiet --no-hardlinks --shared "$ROOT" "$ck" || { echo "ABORT: clone failed" >&2; exit 2; }
  (cd "$ck" && git checkout -q -B t151vb "$2") || { echo "ABORT: checkout $2 failed" >&2; exit 2; }
  for d in "$ck"/.softhouse/capture/t91/out/*/; do
    b=$(basename "$d")
    [ "$b" = happy ] && continue
    ls "$d"/A*.txt >/dev/null 2>&1 || continue
    t=$S/tr-$1-$b; rm -rf "$t"; cp -R "$d" "$t"; chmod -R u+w "$t"
    sh "$PREV"  "$t" >/dev/null 2>&1; a=$?
    sh "$POSTV" "$t" >/dev/null 2>&1; c=$?
    total=$((total+1))
    if [ "$a" = "$c" ]; then same=$((same+1)); v=SAME; else v='*** CHANGED ***'; BAD=$((BAD+1)); fi
    n=$(LC_ALL=C /usr/bin/grep -alF "$SENT" "$t"/A*.txt 2>/dev/null | wc -l | tr -d ' ')
    printf '  %-22s shipped=%s patched=%s  %-15s  transcripts carrying the sentence: %s\n' \
           "$1/$b" "$a" "$c" "$v" "$n"
  done
}
score_dirs POST "$POST_SHA"
score_dirs T91  "$T91_SHA"
echo "  ---"
check "L1  directories scoring identically" "$same/$total" "20/20"
echo

echo "=== L2  RED on a dead oracle"
sh "$PREV"  "$S/dead" >/dev/null 2>&1; a=$?
sh "$POSTV" "$S/dead" > "$S/l2.txt" 2>&1; c=$?
check "L2  shipped scorer over 13 dead-oracle transcripts" "$a" 1
check "L2  patched scorer over 13 dead-oracle transcripts" "$c" 3
LC_ALL=C /usr/bin/grep -a 'never reached a live oracle' "$S/l2.txt" | sed 's/^/      /'
echo

echo "=== L3  CORRECTION: retyping ONE row is NOT enough (T115 said it was)"
retype "$PREV" "$S/v-one.sh" A7-symlinked-canary.txt
sh "$S/v-one.sh" "$S/dead" > "$S/l3.txt" 2>&1; a=$?
reg=$(LC_ALL=C /usr/bin/grep -ac 'REGRESSION (breached, expected clean)' "$S/l3.txt" | tr -d ' ')
check "L3  shipped scorer, A7 alone retyped: exit" "$a" 1
check "L3  shipped scorer, A7 alone retyped: REGRESSION rows" "$reg" 4
echo "      (4 = 2 table rows + the 2 matching lines echoed into the failure list)"
LC_ALL=C /usr/bin/grep -a 'REGRESSION' "$S/l3.txt" | sed 's/^/      /'
echo

echo "=== L4  RED on the case that matters: dead oracle AND all three CLEAN rows retyped"
retype "$PREV"  "$S/v-all-PRE.sh"  A4c-decoy-variable.txt A7-symlinked-canary.txt A8-foreign-cwd.txt
retype "$POSTV" "$S/v-all-POST.sh" A4c-decoy-variable.txt A7-symlinked-canary.txt A8-foreign-cwd.txt
sh "$S/v-all-PRE.sh"  "$S/dead" > "$S/l4pre.txt"  2>&1; a=$?
sh "$S/v-all-POST.sh" "$S/dead" > "$S/l4post.txt" 2>&1; c=$?
check "L4  shipped scorer + all three retyped: exit" "$a" 0
if LC_ALL=C /usr/bin/grep -aq 'ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION' "$S/l4pre.txt"; then
  note "L4  shipped scorer printed the clean sweep" "yes — a clean sweep over an oracle that never answered"
else
  note "L4  shipped scorer printed the clean sweep" "*** NOT AS SPECIFIED *** (expected it to)"; BAD=$((BAD+1))
fi
check "L4  patched scorer + all three retyped: exit" "$c" 3
LC_ALL=C /usr/bin/grep -a 'never reached a live oracle' "$S/l4post.txt" | sed 's/^/      /'
echo

if [ "$BAD" -eq 0 ]; then
  echo "done — every leg behaved as specified."
  echo "V-B: no-op on 20 of 20 committed directories, exit 3 on a dead oracle, exit 3 on the"
  echo "retyped case that was exit 0.  T115's 'any one' is corrected to 'all three'."
  exit 0
fi
echo "done — $BAD leg(s) did NOT behave as specified."
exit 1
