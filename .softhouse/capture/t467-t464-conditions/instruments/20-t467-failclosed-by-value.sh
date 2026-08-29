#!/bin/bash
# T467 / F-T464-2 -- A FAIL-CLOSED BRANCH THAT ONLY A CRASH COULD REACH, MADE REACHABLE BY A
# VALUE. And the proof that the checks it used to take down now run.
#
# WHAT T455 SHIPPED. Section 4 of adjudicate-section1.py classifies each occurrence of seven
# tokens in the vector store: KEY and identifier-shaped VALUE are MATERIAL, a sentence is
# PROSE, and a file that will not parse as JSON keeps the raw substring search where every hit
# is MATERIAL -- "unparseable fails CLOSED, never skipped". The unparseable branch returned
#     [("UNPARSEABLE", text.count(tok))]
# an INT in the slot the other two branches fill with a JSON path, and the caller PRINTS
# where[:70]. So on any tree carrying a non-JSON file with one of those tokens the arm died
# with TypeError: 'int' object is not subscriptable.
#
# THE CONSEQUENCE IS NOT ONE MISSING CHECK. The traceback lands in the middle of section 4,
# BEFORE the named assertion the whole section exists to make, and everything after it --
# section 5's negative controls (a)-(k) included, and (k) is the control FOR THIS BRANCH --
# never executes. No FAILURES: tally is printed at all. The cardinals are re-derived here.
#
# THE REPAIR. The branch returns a STRING location, so the fail-closed direction is reached by
# a VALUE: the arm FAILS on its named assertion, prints FAILURES: 1, and every control still
# runs. Control (k) passed on every crashing run because it only ever inspected the
# classifier's RETURN VALUE; the new control (l) drives the CONSUMER (census + render_rows),
# which is where the defect was.
#
# THE MUTATION IS A NON-JSON FILE IN THE VECTOR STORE CONTAINING A TOKEN -- exactly the shape
# T464 named. It is written into a CLONE, never into the repository under test.
#
# NO HOST PATH AND NO REPO-PATH LITERAL IS WRITTEN IN THIS FILE (T256/T298 and the dead-path
# frontier): paths are assembled from S. Every location is a required parameter; a value that
# does not resolve is exit 3.
#
#   T467_SRC=<repo>  T467_SCRATCH=<dir OUTSIDE the repo>  T467_OUT=<transcript dir> \
#   T467_BEFORE=<commit-ish with the int-returning branch> \
#   T467_AFTER=<commit-ish with the string-returning branch> \
#   bash 20-t467-failclosed-by-value.sh
#
# EXIT 0  every case produced the recorded outcome.  EXIT 1  a case did not.  EXIT 3 REFUSED.
set -u

SRC="${T467_SRC:?T467_SRC must name the source repository}"
SCRATCH="${T467_SCRATCH:?T467_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T467_OUT:?T467_OUT must name the directory to write transcripts into}"
BEFORE="${T467_BEFORE:?T467_BEFORE must name a commit-ish WITHOUT the value-reachable branch}"
AFTER="${T467_AFTER:?T467_AFTER must name a commit-ish WITH it}"

S=".softhouse"
A2="$S/reviews/A2-11"
ADJ="$A2/adjudicate-section1.py"
VEC="$S/vectors"
# The probe file name is assembled too, and it is deliberately NOT .json so that the
# unparseable branch is the one under test.
PROBE_NAME="T467-NON-JSON-PROBE.md"
TOKEN="paymentChannelToFundSourceMappings"

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t467-failclosed"
FAILURES=0

verdict() {
  if [ "$2" = "$3" ]; then echo "  OK   $1 = $2 (expected $3)"
  else echo "  BAD  $1 = $2, EXPECTED $3"; FAILURES=$((FAILURES + 1)); fi
}

prepare() {   # prepare <ref>
  local ref="$1"
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
  fi
  git -C "$D" checkout --quiet --force --detach "$ref" || return 1
  git -C "$D" reset --quiet --hard "$ref" || return 1
  git -C "$D" clean -qfdx || return 1
  [ -f "$D/$ADJ" ] || { echo "REFUSED: $ADJ absent at $ref" >&2; return 1; }
  [ -d "$D/$VEC" ] || { echo "REFUSED: the vector store is absent at $ref" >&2; return 1; }
  git -C "$D" config user.email t467@softhouse.invalid || return 1
  git -C "$D" config user.name "T467 drive" || return 1
  return 0
}

plant() {     # plant the tracked non-JSON vector file carrying a token
  printf '# a note that mentions %s in prose, in a file no JSON parser will accept\n' \
    "$TOKEN" > "$D/$VEC/$PROBE_NAME" || return 1
  git -C "$D" add -- "$VEC/$PROBE_NAME" || return 1
  git -C "$D" commit -q -m "T467 drive: a TRACKED non-JSON vector file carrying a token" || return 1
  return 0
}

run_adj() {   # run_adj <case> ; echoes the exit code
  ( cd "$D" && python3 "$ADJ" ) > "$OUT/failclosed-$1.txt" 2>&1
  echo $?
}

checks_run()  { grep -c '  PASS  \|  FAIL  ' "$OUT/failclosed-$1.txt"; }
tally_lines() { grep -c '^FAILURES:' "$OUT/failclosed-$1.txt"; }
traceback()   { grep -c '^Traceback (most recent call last):' "$OUT/failclosed-$1.txt"; }
named_fail()  { grep -c -F -- 'FAIL  NO vector in the store USES any of these tokens' "$OUT/failclosed-$1.txt"; }
# The controls, counted by their own labels rather than by position.
controls_run() {
  local n=0 c
  for c in '(a) a FOURTH failure' '(b) an adjudicated failure' '(c) a section 1 that went GREEN' \
           '(d) a transcript with NO' '(e) the offline prover TRIPS' \
           '(f) the offline prover TRIPS on the subprocess' '(g) the offline prover does NOT trip' \
           '(h) a token used as an object KEY' '(i) a token inside an IDENTIFIER-SHAPED value' \
           '(j) a token inside a PROSE sentence' '(k) a file that does NOT parse as JSON'; do
    if grep -q -F -- "$c" "$OUT/failclosed-$1.txt"; then n=$((n + 1)); fi
  done
  echo "$n"
}

echo "############ T467 / F-T464-2 -- FAIL-CLOSED BY A VALUE, NOT BY A TRACEBACK"
echo "  BEFORE = $BEFORE   (the branch returns an int)"
echo "  AFTER  = $AFTER   (the branch returns a location string)"
echo

# =========================================================================================
# CALIBRATION -- both refs are GREEN on the unmutated tree, and both run all their checks.
# Without this every number below could be bought by a grader that is simply broken.
# =========================================================================================
prepare "$BEFORE" || { echo "REFUSED: could not prepare $BEFORE" >&2; exit 3; }
RC_CAL_B="$(run_adj cal-BEFORE)"
CHK_CAL_B="$(checks_run cal-BEFORE)"
CTL_CAL_B="$(controls_run cal-BEFORE)"
prepare "$AFTER" || { echo "REFUSED: could not prepare $AFTER" >&2; exit 3; }
RC_CAL_A="$(run_adj cal-AFTER)"
CHK_CAL_A="$(checks_run cal-AFTER)"
CTL_CAL_A="$(controls_run cal-AFTER)"
echo "  CALIBRATION, unmutated tree:"
echo "    BEFORE exit=$RC_CAL_B checks=$CHK_CAL_B controls(a)-(k)=$CTL_CAL_B"
echo "    AFTER  exit=$RC_CAL_A checks=$CHK_CAL_A controls(a)-(k)=$CTL_CAL_A"
verdict "CAL BEFORE is green on a clean tree" "$RC_CAL_B" 0
verdict "CAL AFTER  is green on a clean tree" "$RC_CAL_A" 0
verdict "CAL BEFORE runs all 25 of its checks" "$CHK_CAL_B" 25
verdict "CAL AFTER  runs all 29 of its checks (25 + l, l1, l2, m)" "$CHK_CAL_A" 29
verdict "CAL BEFORE runs all 11 controls (a)-(k)" "$CTL_CAL_B" 11
verdict "CAL AFTER  runs all 11 controls (a)-(k) too" "$CTL_CAL_A" 11
echo

# =========================================================================================
# CASE 1 -- BEFORE, a tracked non-JSON vector file carrying a token. THE CRASH.
# =========================================================================================
prepare "$BEFORE" || exit 3
plant || { echo "REFUSED: could not plant the probe at BEFORE" >&2; exit 3; }
RC_1="$(run_adj 1-nonjson-BEFORE)"
CHK_1="$(checks_run 1-nonjson-BEFORE)"
TB_1="$(traceback 1-nonjson-BEFORE)"
TALLY_1="$(tally_lines 1-nonjson-BEFORE)"
NAMED_1="$(named_fail 1-nonjson-BEFORE)"
CTL_1="$(controls_run 1-nonjson-BEFORE)"
SKIPPED_1=$((CHK_CAL_B - CHK_1))
echo "  1  BEFORE, tracked non-JSON vector with a token:"
echo "     exit=$RC_1  traceback=$TB_1  checks executed=$CHK_1 of $CHK_CAL_B  SKIPPED=$SKIPPED_1"
echo "     FAILURES: lines=$TALLY_1  named assertion fired=$NAMED_1  controls (a)-(k) reached=$CTL_1"
verdict "1  it exits non-zero -- but as a CRASH" "$RC_1" 1
verdict "1  a traceback is printed, x1" "$TB_1" 1
verdict "1  10 of the 25 checks execute" "$CHK_1" 10
verdict "1  15 checks are SKIPPED" "$SKIPPED_1" 15
verdict "1  the FAILURES: tally NEVER PRINTS" "$TALLY_1" 0
verdict "1  the NAMED assertion never runs" "$NAMED_1" 0
verdict "1  NONE of the 11 controls (a)-(k) is reached, including (k) -- the control FOR the branch that was supposed to fail closed" "$CTL_1" 0
echo

# =========================================================================================
# CASE 2 -- AFTER, THE SAME TREE. Fail-closed by a value, with the controls still running.
# =========================================================================================
prepare "$AFTER" || exit 3
plant || { echo "REFUSED: could not plant the probe at AFTER" >&2; exit 3; }
RC_2="$(run_adj 2-nonjson-AFTER)"
CHK_2="$(checks_run 2-nonjson-AFTER)"
TB_2="$(traceback 2-nonjson-AFTER)"
TALLY_2="$(tally_lines 2-nonjson-AFTER)"
NAMED_2="$(named_fail 2-nonjson-AFTER)"
CTL_2="$(controls_run 2-nonjson-AFTER)"
UNPARSE_2="$(grep -c -F -- 'UNPARSEABLE' "$OUT/failclosed-2-nonjson-AFTER.txt")"
echo "  2  AFTER, the same tree:"
echo "     exit=$RC_2  traceback=$TB_2  checks executed=$CHK_2 of $CHK_CAL_A"
echo "     FAILURES: lines=$TALLY_2  named assertion fired=$NAMED_2  controls (a)-(k) reached=$CTL_2"
echo "     UNPARSEABLE rows printed=$UNPARSE_2"
verdict "2  it exits 1 by a VALUE" "$RC_2" 1
verdict "2  with NO traceback" "$TB_2" 0
verdict "2  ALL 29 checks execute -- the 15 that were skipped now run" "$CHK_2" 29
verdict "2  the FAILURES: tally PRINTS" "$TALLY_2" 1
verdict "2  the NAMED assertion fires, x1" "$NAMED_2" 1
verdict "2  and all 11 controls (a)-(k) run, including (k)" "$CTL_2" 11
echo

# =========================================================================================
# CASE 3 -- AFTER, CLEAN TREE. The control that stops case 2 from being free (P-72). A branch
# that reddened every tree would produce case 2 and would be a freeze, not a fail-closed rule.
# =========================================================================================
prepare "$AFTER" || exit 3
RC_3="$(run_adj 3-clean-AFTER)"
CHK_3="$(checks_run 3-clean-AFTER)"
MAT_3="$(grep -c 'MATERIAL=0' "$OUT/failclosed-3-clean-AFTER.txt")"
echo "  3  AFTER, CLEAN tree: exit=$RC_3 checks=$CHK_3 tokens reported MATERIAL=0: $MAT_3 of 7"
verdict "3  the honest tree is still GREEN at AFTER" "$RC_3" 0
verdict "3  all 29 checks run" "$CHK_3" 29
verdict "3  and all 7 tokens still measure MATERIAL=0" "$MAT_3" 7
echo

# =========================================================================================
# CASE 4 -- F-T464-6, THE DISCRIMINATOR'S EDGE, DRIVEN ON A REAL FILE RATHER THAN IN MEMORY.
# An identifier-shaped VALUE with one TRAILING SPACE was reclassified PROSE, i.e. immaterial:
# an evasion one whitespace character wide. At AFTER the value is stripped before the shape
# test, so it is MATERIAL. Controls (l2) and (m) assert the same thing in memory on every run;
# this drives it through the live corpus walk, which is the code path that grades the store.
# =========================================================================================
plant_trailing_space() {
  python3 - "$D" "$VEC" "$TOKEN" <<'PYEOF' || return 1
import json, os, sys
root, vec, tok = sys.argv[1], sys.argv[2], sys.argv[3]
p = os.path.join(root, vec, "T467-TRAILING-SPACE-PROBE.json")
if os.path.exists(p):
    print("REFUSED: the probe already exists.")
    sys.exit(3)
with open(p, "w", encoding="utf-8") as fh:
    json.dump({"provenance": {"capture_ref": "A2-99-" + tok + " "}}, fh)
print("planted a JSON vector whose capture_ref is identifier-shaped apart from ONE TRAILING SPACE")
PYEOF
  git -C "$D" add -- "$VEC/T467-TRAILING-SPACE-PROBE.json" || return 1
  git -C "$D" commit -q -m "T467 drive: identifier-shaped value with one trailing space" || return 1
  return 0
}
prepare "$BEFORE" || exit 3
plant_trailing_space || { echo "REFUSED: could not plant the trailing-space probe" >&2; exit 3; }
RC_4B="$(run_adj 4-trailingspace-BEFORE)"
NAMED_4B="$(named_fail 4-trailingspace-BEFORE)"
prepare "$AFTER" || exit 3
plant_trailing_space || { echo "REFUSED: could not plant the trailing-space probe" >&2; exit 3; }
RC_4A="$(run_adj 4-trailingspace-AFTER)"
NAMED_4A="$(named_fail 4-trailingspace-AFTER)"
echo "  4  identifier-shaped value with ONE TRAILING SPACE, through the live corpus walk:"
echo "     BEFORE exit=$RC_4B named-assertion=$NAMED_4B     AFTER exit=$RC_4A named-assertion=$NAMED_4A"
verdict "4  BEFORE grades it PROSE and PASSES -- the evasion, reproduced" "$RC_4B" 0
verdict "4  BEFORE the named assertion does not fire" "$NAMED_4B" 0
verdict "4  AFTER grades it MATERIAL and FAILS" "$RC_4A" 1
verdict "4  AFTER on the named assertion, x1" "$NAMED_4A" 1
echo "     (THE RESIDUAL LIMIT IS PUBLISHED, NOT CLOSED: a token inside a genuinely MULTI-WORD"
echo "      value is still graded PROSE. Control (m) asserts that, so it cannot drift silently.)"
echo

# =========================================================================================
# COVERAGE (T467 / F-T464-5) -- the bytes this transcript graded, named in the transcript.
# =========================================================================================
echo "############ COVERAGE -- the graded bytes, named"
prepare "$AFTER" >/dev/null || exit 3
echo "  graded ref (AFTER) resolves to: $(git -C "$D" rev-parse HEAD)"
printf '  %-62s blob %s\n' "$ADJ" "$(git -C "$D" rev-parse "HEAD:$ADJ")"
printf '  %-62s last touched at this ref by %s\n' "" "$(git -C "$D" log -1 --format='%h %s' -- "$ADJ")"
echo "  A reader confirms this transcript covers the merged bytes with one command:"
echo "  git rev-parse <branch-tip>:<that path> must print the same blob."
echo

if [ "$FAILURES" -ne 0 ]; then
  echo "T467 FAIL-CLOSED DRIVE: FAIL -- $FAILURES case(s) did not behave as recorded."
  exit 1
fi
echo "T467 FAIL-CLOSED DRIVE: PASS. The unparseable branch is reached by a VALUE; the 15 checks"
echo "the traceback used to skip -- controls (a)-(k) among them -- all run; the clean tree is"
echo "still green; and the one-space evasion in the MATERIAL/PROSE discriminator is closed."
exit 0
