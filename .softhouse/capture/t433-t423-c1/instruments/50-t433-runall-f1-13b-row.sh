#!/bin/bash
# T433 / C-T423-1 — the DIRECT evidence for the ONE row T433 changed in a tracked executable.
#
# T433 moved `f1-13b` in
# `.softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh` from an expected
# `0 0` (undetected at both refs, on a FALSE stated reason) to `0 1` (CAUGHT at AFTER). A
# changed expectation that was never driven is exactly the defect this program punishes, so it
# is driven here — through the WHOLE `run-all.sh`, not section 10 alone, because `0 1` in that
# matrix is a claim about run-all.sh's exit code and its aggregate VERDICT block.
#
# WHY TWO CASES AND NOT THIRTEEN. T433 re-ran the full 13-case matrix and killed it: 26 whole
# `run-all.sh` runs under contention with the ARM F drive was hours of wall clock. ARM F only
# changes section 10's ARM set, so the only rows whose colour it can move are:
#   * f1-13b  -- the laundered post-fork residual, which ARM F is built to catch;
#   * control -- which must still be 0, because an arm that reddens a clean tree is worse
#                than no arm (P-22's converse, and the reason a control is run at all).
# The other eleven rows are unchanged by construction and each is argued in T433's handoff:
#   f1-13 (mutate, unlaundered)   ARM B/C already exit 1; ARM F agrees; still 1
#   f1-14 (delete)                ARM C path-set; the path leaves ARM F's population; still 1
#   f1-15 (add fabricated)        ARM C path-set; ARM F prints it born-at-tip; still 1
#   f1-16 (untracked fabricated)  ARM D; not in any git tree; still 1
#   f1-09 (symlink)               ARM D lstat; still 1
#   f3, f3b (non-observation)     ARM E; outside ARM F's population; still 1
#   f4a  (fork observation)       ARM A; outside ARM F's population; still 1 at BOTH refs
#   f4b  (fork constant moved)    REFUSED at section 2 before ARM F is reached; still 2
# THIS IS AN ARGUMENT, NOT A MEASUREMENT, and it is labelled as one. The full matrix re-run is
# filed as T433's follow-up F-5.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298).
#   T433_SRC=<repo> T433_CLONE=<scratch OUTSIDE the repo> T433_OUT=<dir> \
#   T433_BEFORE=<sha> T433_AFTER=<sha> bash 50-t433-runall-f1-13b-row.sh
#
# EXIT 0 both rows produced the expected run-all.sh exit code at both refs, for the stated
#        reason. EXIT 1 one did not. EXIT 3 the harness could not run.
set -u
SRC="${T433_SRC:?}"; SCROOT="${T433_CLONE:?}"; OUT="${T433_OUT:?}"
BEFORE="${T433_BEFORE:?}"; AFTER="${T433_AFTER:?}"

CAP=".softhouse/capture/tierA-a2"
RUNALL=".softhouse/reviews/A2-11/run-all.sh"
MAN="$CAP/MANIFEST.sha256"
PICK=".softhouse/capture/t393-t382-conditions/instruments/11-pick-targets.py"
LAUNDER=".softhouse/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py"

mkdir -p "$OUT" "$SCROOT" || exit 3
if ! TARGETS="$(python3 "$SRC/$PICK")"; then echo "REFUSED: no targets" >&2; exit 3; fi
POSTFORK="$(printf '%s\n' "$TARGETS" | awk -F'\t' '$1=="POSTFORK"{print $2}')"
[ -n "$POSTFORK" ] || { echo "REFUSED: POSTFORK empty" >&2; exit 3; }

echo "T433 — the f1-13b ROW, through the WHOLE run-all.sh"
echo "  BEFORE = $BEFORE   (section 10 WITHOUT ARM F)"
echo "  AFTER  = $AFTER   (section 10 WITH ARM F)"
echo "  laundered target = $POSTFORK  (MEASURED by 11-pick-targets.py, never typed)"
echo

D="$SCROOT/f113b"
FAILURES=0

prepare() {
  local ref="$1"
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
    git -C "$D" config user.email t433@softhouse.local || return 1
    git -C "$D" config user.name T433 || return 1
  fi
  git -C "$D" reset --quiet --hard || return 1
  git -C "$D" clean -qfdx || return 1
  git -C "$D" checkout --quiet --detach "$ref" || return 1
  git -C "$D" reset --quiet --hard "$ref" || return 1
}

mut_none() { return 0; }
mut_laundered() {
  printf '\nT433-F1-13B-MARKER\n' >> "$D/$CAP/$POSTFORK" || return 1
  python3 "$SRC/$LAUNDER" "$D" "$POSTFORK" >/dev/null || return 1
  git -C "$D" add -- "$CAP/$POSTFORK" "$MAN" || return 1
  git -C "$D" commit -q -m "T433 f1-13b: post-fork observation mutated, manifest row rewritten in the SAME commit" || return 1
}

# WHAT THE `0 0` / `0 1` COLUMN IN 10-drive-conditions.sh ACTUALLY IS. It is the SECTION 10
# exit code as printed in run-all.sh's own VERDICT table — read by T393 with
# `awk '/^  10 /{print $3}'` — and NOT run-all.sh's process exit code. This drive uses T393's
# spelling exactly, because a re-drive that scores a different column is not a re-drive.
# (The first version of this script scored the process rc and every row came back UNEXPECTED;
#  the cause is recorded below under PRE-EXISTING, and it is not ARM F.)
sec10_of() { awk '/^  10 /{print $3}' "$1" | tail -1; }
sec_of()   { awk -v s="$2" '$1==s && NF>=4 {print $3}' "$1" | tail -1; }
verdict_of() { sed -n 's/.*RUN-ALL VERDICT: \([A-Z]*\).*/\1/p' "$1" | tail -1; }
moved10_of() { awk '/^  10 /{print ($4=="***")?"MOVED":"as-adjudicated"}' "$1" | tail -1; }

run_row() {  # run_row <name> <mutfn> <expect_before> <expect_after>
  local name="$1" fn="$2" eb="$3" ea="$4" ref want tag rc t
  for tag in BEFORE AFTER; do
    if [ "$tag" = BEFORE ]; then ref="$BEFORE"; want="$eb"; else ref="$AFTER"; want="$ea"; fi
    prepare "$ref" || { echo "  HARNESS FAILURE preparing $ref"; exit 3; }
    "$fn" || { echo "  HARNESS FAILURE mutating for $name/$tag — a case that did not mutate"; \
               echo "  would report the colour of a CLEAN tree, which is a null control."; exit 3; }
    t="$OUT/runall-$name-$tag.txt"
    ( cd "$D" && bash "$RUNALL" ) > "$t" 2>&1
    rc=$?
    local s10 s9 v armf mv res
    s10="$(sec10_of "$t")"; s9="$(sec_of "$t" 9)"; v="$(verdict_of "$t")"
    mv="$(moved10_of "$t")"
    armf="$(grep -c 'LAUNDERED-OR-MUTATED' "$t")"
    # ABSENCE IS NOT ZERO: a missing section-10 row means the section never recorded a
    # verdict, which run-all.sh itself refuses to read as a pass. Neither will this.
    if [ -z "$s10" ]; then s10="ABSENT"; fi
    res="as expected"
    [ "$s10" = "$want" ] || { res="*** UNEXPECTED ***"; FAILURES=$((FAILURES + 1)); }
    printf '  %-10s %-6s sec10=%-6s sec10row=%-14s armf-named=%s  sec9=%-4s runall-rc=%s verdict=%-5s expected sec10=%s  %s\n' \
      "$name" "$tag" "$s10" "$mv" "$armf" "${s9:-?}" "$rc" "${v:-none}" "$want" "$res"
  done
}

# name      mutation        BEFORE AFTER   (the SECTION 10 column, T393's spelling)
run_row control   mut_none        0 0
run_row f1-13b    mut_laundered   0 1

echo
echo "############ REASONS, not just colours"
R=0
chk() { local got; got="$(grep -c -- "$3" "$OUT/$2")"
        if [ "$got" = "$4" ]; then echo "  OK   $1 (x$got)"; else echo "  BAD  $1 expected x$4 got x$got"; R=$((R+1)); fi; }
chkv() { local got; got="$(verdict_of "$OUT/$2")"
         if [ "$got" = "$3" ]; then echo "  OK   $1 (verdict $got)"; else echo "  BAD  $1 expected $3 got ${got:-none}"; R=$((R+1)); fi; }
chks() { local got; got="$(sec_of "$OUT/$2" "$3")"
         if [ "$got" = "$4" ]; then echo "  OK   $1 (section $3 = $got)"; else echo "  BAD  $1 expected section $3 = $4, got ${got:-ABSENT}"; R=$((R+1)); fi; }

# `RUN-ALL VERDICT: PASS` occurs in section 10's own BANNER PROSE, which quotes T382's finding
# verbatim — a naive `grep -c` returns 3 on a clean tree. This is the same false positive T393
# recorded one column over. So the verdict is read the way run-all.sh PRINTS it, last one wins.
chks "BEFORE: section 10 PASSED the laundered tree — T393's residual is REAL" \
     "runall-f1-13b-BEFORE.txt" 10 0
chk  "BEFORE: nothing named the laundered file (there was no ARM F)" \
     "runall-f1-13b-BEFORE.txt" "LAUNDERED-OR-MUTATED" 0
chks "AFTER: section 10 is 1 — ARM F reddened it" \
     "runall-f1-13b-AFTER.txt" 10 1
chk  "AFTER: ARM F NAMES the laundered file" \
     "runall-f1-13b-AFTER.txt" "LAUNDERED-OR-MUTATED $POSTFORK" 1
chk  "AFTER: section 10's row in the VERDICT table is marked MOVED" \
     "runall-f1-13b-AFTER.txt" "^  10 .*\*\*\* MOVED \*\*\*" 1
chkv "AFTER: the aggregate verdict is FAIL" "runall-f1-13b-AFTER.txt" FAIL
chks "control BEFORE: section 10 passes a clean tree" "runall-control-BEFORE.txt" 10 0
chks "control AFTER: section 10 STILL passes a clean tree — ARM F does not redden the control" \
     "runall-control-AFTER.txt" 10 0

echo
echo "############ PRE-EXISTING, MEASURED HERE, AND NOT CAUSED BY ARM F"
echo "  run-all.sh's PROCESS exit code is 1 on an UNMUTATED tree at BOTH refs, because"
echo "  SECTION 9 (adjudicate-section1.py) is adjudicated 0 and exits 1. That is true at"
echo "  $BEFORE — unmodified main, with no ARM F in the tree at all — so it"
echo "  is a condition T433 MEASURED, not one T433 introduced. It is asserted here in both"
echo "  directions so the claim is falsifiable rather than an excuse:"
chks "section 9 already moves on the CONTROL at BEFORE (no ARM F anywhere)" \
     "runall-control-BEFORE.txt" 9 1
chks "section 9 moves identically on the CONTROL at AFTER" \
     "runall-control-AFTER.txt" 9 1
chks "section 10 is UNAFFECTED by it on the control at AFTER" \
     "runall-control-AFTER.txt" 10 0

echo
if [ "$FAILURES" -ne 0 ] || [ "$R" -ne 0 ]; then
  echo "T433 f1-13b ROW DRIVE: FAIL — $FAILURES wrong section-10 code(s), $R wrong reason(s)."
  exit 1
fi
echo "T433 f1-13b ROW DRIVE: PASS. The row's new expectation 0 -> 1 in 10-drive-conditions.sh"
echo "is a MEASUREMENT taken in T393's own column: through the WHOLE run-all.sh, section 10"
echo "exits 0 at $BEFORE on the laundered tree and 1 at $AFTER, its"
echo "VERDICT-table row marked *** MOVED ***, with ARM F naming the file — while the control's"
echo "section 10 stays 0 at both refs. Section 9's pre-existing move is measured, disclosed,"
echo "and shown to be present at the ref that has no ARM F."
exit 0
