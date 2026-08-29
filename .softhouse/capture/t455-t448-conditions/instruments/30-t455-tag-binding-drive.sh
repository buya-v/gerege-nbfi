#!/bin/bash
# T455 / C-T448-2 — THE TAG'S BINDING TO THE TEXT, DRIVEN. And a correction to the repair.
#
# T433's correction technique keeps every false sentence VERBATIM and tags it
# [QUOTED-FALSE-CLAIM]. Its guard asserted the TAG in two token-level, line-level halves:
#     got="$(grep -Ei "$IMPOSS" "$f" | grep -vc "QUOTED-FALSE-CLAIM")"   # negative
#     q="$(grep -c "QUOTED-FALSE-CLAIM" "$f")" ; [ "$q" -ge 3 ]          # positive
# T448 defeated both at guard exit 0:
#   (B) re-assert the claim as a LIVE `echo` with the tag in a TRAILING COMMENT — the source
#       carries the tag, the TRANSCRIPT prints the sentence untagged;
#   (C) DELETE the quotation and keep three bare tags — a tag COUNT, with nothing under it.
#
# T455 RE-DERIVED THE REPAIR RATHER THAN PASTING IT, AND THE RE-DERIVATION FOUND SOMETHING.
# T448's supplied one-predicate repair is
#     both="$(grep -Ei "$IMPOSS" "$f" | grep -c "QUOTED-FALSE-CLAIM")"
#     all="$(grep -Eic "$IMPOSS" "$f")" ;  [ "$both" -ge 1 ] && [ "$both" = "$all" ]
# and the review states that case B fails it with `all` = 2, `both` = 1. IT DOES NOT. The
# smuggled line carries the tag in its trailing comment, so it is counted by BOTH greps:
# all = both = 2, and the predicate PASSES. That is measured below, at case B, as its own
# assertion — not argued. Case B is closed only by a SECOND predicate that reads what a line
# PRINTS rather than what its source contains, which is why the shipped repair has two.
#
# WHERE THE REPAIR LANDED: INSIDE the shipped grader, as section 10 of
# `.softhouse/reviews/A2-11/verify-capture-integrity.py`, which run-all.sh adjudicates at
# exit 0 as its section 10. P-45 — a guard beside the thing it guards enforces nothing. The
# capture-directory guard this file also exercises is T433's, and it is exercised to
# REPRODUCE ITS DEFEAT at first hand, not to rely on it.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298). The old guard's location is a REQUIRED
# parameter for the reason T448 recorded: a repo-relative literal for a file that is absent
# from some ref is a dead path, and it moves guard_dead_path_frontier. A value that does not
# resolve inside the checked-out tree is exit 3 here, never a skipped case and never a pass.
#
#   T455_SRC=<repo>  T455_SCRATCH=<dir OUTSIDE the repo>  T455_OUT=<dir> \
#   T455_REF=<commit-ish carrying T455's section 10> \
#   T455_OLD_GUARD=<repo-relative path of T433's ARM-F wiring guard in THAT tree> \
#   bash 30-t455-tag-binding-drive.sh
#
# ENGINE (P-33/P-53): `grep -c -F` fixed strings for every count this file asserts; the edits
# are python3 literal string surgery, so no regex dialect is load-bearing. The one place a
# regex IS used is the re-implementation of T448's predicate, deliberately, because that is
# the artefact under test and it must be run in its own spelling.
#
# EXIT 0 every case behaved as recorded.  EXIT 1 a case did not.  EXIT 3 REFUSED.
set -u

SRC="${T455_SRC:?T455_SRC must name the source repository}"
SCRATCH="${T455_SCRATCH:?T455_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T455_OUT:?T455_OUT must name the directory to write transcripts into}"
REF="${T455_REF:?T455_REF must name the commit-ish carrying T455's section 10}"
OLD_GUARD="${T455_OLD_GUARD:?T455_OLD_GUARD must give the repo-relative path of T433's ARM-F wiring guard}"

INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
RUNALL=".softhouse/reviews/A2-11/run-all.sh"
TAG="QUOTED-FALSE-CLAIM"
SENTENCE="There is no committed baseline older than HEAD for those 632."

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t455-tag"
FAILURES=0

verdict() {   # verdict <label> <got> <want>
  if [ "$2" = "$3" ]; then echo "  OK   $1 = $2 (expected $3)"
  else echo "  BAD  $1 = $2, EXPECTED $3"; FAILURES=$((FAILURES + 1)); fi
}

prepare() {
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
  fi
  git -C "$D" checkout --quiet --detach "$REF" || return 1
  git -C "$D" reset --quiet --hard "$REF" || return 1
  git -C "$D" clean -qfdx || return 1
  [ -f "$D/$INT" ]    || { echo "REFUSED: $INT absent at $REF" >&2; return 1; }
  [ -f "$D/$RUNALL" ] || { echo "REFUSED: $RUNALL absent at $REF" >&2; return 1; }
  [ -f "$D/$OLD_GUARD" ] || {
    echo "REFUSED: T455_OLD_GUARD=$OLD_GUARD does not resolve inside the tree at $REF." >&2
    return 1; }
  return 0
}

grade_new() {   # grade_new <case> ; echoes the SHIPPED grader's exit code
  local n="$1"
  ( cd "$D" && python3 "$INT" ) > "$OUT/tag-$n-new.txt" 2>&1
  echo $?
}

grade_old() {   # grade_old <case> ; echoes T433's capture-directory guard's exit code
  local n="$1"
  T433_ROOT="$D" bash "$D/$OLD_GUARD" > "$OUT/tag-$n-oldguard.txt" 2>&1
  echo $?
}

# T448's SUPPLIED ONE-PREDICATE REPAIR, re-implemented in its own spelling so it can be
# measured rather than believed. Echoes "all both PASS|FAIL".
t448_predicate() {
  local f="$D/$RUNALL"
  local imposs="there is no committed baseline older than HEAD|no baseline older than HEAD anywhere|does not exist and cannot be manufactured here|committed baseline older than HEAD for those 632"
  local all both
  all="$(grep -Eic "$imposs" "$f")"
  both="$(grep -Ei "$imposs" "$f" | grep -c "$TAG")"
  if [ "$both" -ge 1 ] && [ "$both" = "$all" ]; then echo "$all $both PASS"
  else echo "$all $both FAIL"; fi
}

echo "############ T455 — THE [QUOTED-FALSE-CLAIM] TAG, AND ITS BINDING TO THE TEXT"
echo "  ref       = $REF"
echo "  old guard = $OLD_GUARD  (exercised to REPRODUCE its defeat, not relied on)"
echo

# =========================================================================================
# CASE A — CALIBRATION (P-72). Both graders are GREEN on the unmutated tree, and T448's
# predicate passes it too. Without this every "defeated" below would be free.
# =========================================================================================
prepare || { echo "REFUSED: could not prepare a clone of $SRC at $REF" >&2; exit 3; }
RC_A_NEW="$(grade_new A-control)"
RC_A_OLD="$(grade_old A-control)"
P_A="$(t448_predicate)"
echo "  A control (unmutated)   shipped section 10 exit = $RC_A_NEW   T433 guard exit = $RC_A_OLD"
echo "                          T448's one predicate: all=$(echo "$P_A" | awk '{print $1}') both=$(echo "$P_A" | awk '{print $2}') -> $(echo "$P_A" | awk '{print $3}')"
verdict "A the SHIPPED grader is green before anything is smuggled" "$RC_A_NEW" 0
verdict "A T433's guard is green too" "$RC_A_OLD" 0
verdict "A and T448's predicate accepts the honest tree" "$(echo "$P_A" | awk '{print $3}')" PASS
echo

# =========================================================================================
# CASE B — SMUGGLE THE CLAIM BACK AS A LIVE, PRINTED ASSERTION, tag in a trailing comment.
# =========================================================================================
prepare || { echo "REFUSED: could not prepare for case B" >&2; exit 3; }
python3 - "$D/$RUNALL" "$SENTENCE" "$TAG" <<'PYEOF' || exit 3
import sys
path, sentence, tag = sys.argv[1], sys.argv[2], sys.argv[3]
anchor = '  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
src = open(path, encoding="utf-8").read()
if anchor not in src:
    print("REFUSED: the section-10 anchor is not in run-all.sh; the edit would be a no-op.")
    sys.exit(3)
smuggled = '  echo "%s"  # %s\n' % (sentence, tag)
open(path, "w", encoding="utf-8").write(src.replace(anchor, smuggled + anchor, 1))
print("smuggled the sentence back as a LIVE echo with the tag in a trailing comment")
PYEOF
SRC_HITS="$(grep -c -F -- "$SENTENCE" "$D/$RUNALL")"
RC_B_NEW="$(grade_new B-smuggle-live-echo)"
RC_B_OLD="$(grade_old B-smuggle-live-echo)"
P_B="$(t448_predicate)"
B_P2="$(grep -c -F -- 'FAIL  PREDICATE 2, PRINTED' "$OUT/tag-B-smuggle-live-echo-new.txt")"
B_P1="$(grep -c -F -- 'FAIL  PREDICATE 1, BINDING' "$OUT/tag-B-smuggle-live-echo-new.txt")"
echo "  B live echo, tag in a trailing comment  (sentence now x$SRC_HITS in run-all.sh's source)"
echo "                          shipped section 10 exit = $RC_B_NEW   T433 guard exit = $RC_B_OLD"
echo "                          T448's one predicate: all=$(echo "$P_B" | awk '{print $1}') both=$(echo "$P_B" | awk '{print $2}') -> $(echo "$P_B" | awk '{print $3}')"
verdict "B the SHIPPED grader REFUSES it" "$RC_B_NEW" 1
verdict "B on PREDICATE 2 (what the line PRINTS), x1" "$B_P2" 1
verdict "B and NOT on PREDICATE 1 — the source line does carry the tag" "$B_P1" 0
verdict "B T433's guard is DEFEATED by it, reproducing T448's finding at first hand" "$RC_B_OLD" 0
verdict "B AND SO IS T448's OWN ONE-PREDICATE REPAIR — the review says it fails here; measured, it PASSES" \
        "$(echo "$P_B" | awk '{print $3}')" PASS
# The harm is what a READER sees, so prove it reaches the transcript rather than sitting in
# the source. run-all.sh is not executed here (that is 10-t455-runall-and-footer.sh's job);
# what is asserted is that the emitted payload carries no tag, which is predicate 2's claim.
UNTAGGED_PAYLOAD="$(grep -F -- "$SENTENCE" "$D/$RUNALL" | grep -c -v -F "$TAG\"")"
echo "                          source lines carrying the sentence outside a tagged payload: $UNTAGGED_PAYLOAD"
echo

# =========================================================================================
# CASE C — DELETE THE QUOTATION, KEEP THE TAG. Three bare tags satisfy a tag COUNT.
# =========================================================================================
prepare || { echo "REFUSED: could not prepare for case C" >&2; exit 3; }
python3 - "$D/$RUNALL" "$TAG" <<'PYEOF' || exit 3
import sys
path, tag = sys.argv[1], sys.argv[2]
lines = open(path, encoding="utf-8").read().split("\n")
kept, dropped = [], 0
for ln in lines:
    if tag in ln:
        dropped += 1
        continue
    kept.append(ln)
if dropped < 3:
    print("REFUSED: expected at least 3 tagged lines to remove, found %d." % dropped)
    sys.exit(3)
anchor = '  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
if anchor not in kept:
    print("REFUSED: the section-10 anchor vanished; the edit is not the one intended.")
    sys.exit(3)
i = kept.index(anchor)
bare = ['  # %s (tidied: the quotation was removed, the tag was not)' % tag] * 3
open(path, "w", encoding="utf-8").write("\n".join(kept[:i] + bare + kept[i:]))
print("deleted %d tagged quotation lines and inserted 3 bare tags" % dropped)
PYEOF
QUOTED_LEFT="$(grep -c -F -- "$SENTENCE" "$D/$RUNALL")"
TAGS_LEFT="$(grep -c -F -- "$TAG" "$D/$RUNALL")"
RC_C_NEW="$(grade_new C-quote-gone-tag-kept)"
RC_C_OLD="$(grade_old C-quote-gone-tag-kept)"
P_C="$(t448_predicate)"
C_P1="$(grep -c -F -- 'FAIL  PREDICATE 1, BINDING' "$OUT/tag-C-quote-gone-tag-kept-new.txt")"
echo "  C quotation deleted, tag kept  (sentence x$QUOTED_LEFT, tag x$TAGS_LEFT)"
echo "                          shipped section 10 exit = $RC_C_NEW   T433 guard exit = $RC_C_OLD"
echo "                          T448's one predicate: all=$(echo "$P_C" | awk '{print $1}') both=$(echo "$P_C" | awk '{print $2}') -> $(echo "$P_C" | awk '{print $3}')"
verdict "C the SHIPPED grader REFUSES it" "$RC_C_NEW" 1
verdict "C on PREDICATE 1 (de-wrapped tagged block holds no quotation), x1" "$C_P1" 1
verdict "C T433's guard is DEFEATED by it, reproducing T448's finding at first hand" "$RC_C_OLD" 0
verdict "C T448's one predicate DOES close this half" "$(echo "$P_C" | awk '{print $3}')" FAIL
echo

# =========================================================================================
# CASE D — THE POSITIVE HALF, DRIVEN. Remove the replacement text and the guard must fail on
# the POSITIVE assertion, not the negative one. A negative-only guard passes on an empty file
# (P-35), which is how a correction becomes a bare negation removed.
# =========================================================================================
prepare || { echo "REFUSED: could not prepare for case D" >&2; exit 3; }
python3 - "$D/$RUNALL" <<'PYEOF' || exit 3
import sys
path = sys.argv[1]
marker = "BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION"
src = open(path, encoding="utf-8").read()
if marker not in src:
    print("REFUSED: the replacement text is already absent; the edit would be a no-op.")
    sys.exit(3)
open(path, "w", encoding="utf-8").write(src.replace(marker, "[REDACTED BY T455 CASE D]"))
print("removed the replacement text from run-all.sh")
PYEOF
RC_D_NEW="$(grade_new D-positive-half)"
D_POS="$(grep -c -F -- 'FAIL  POSITIVE HALF' "$OUT/tag-D-positive-half-new.txt")"
echo "  D replacement text removed              shipped section 10 exit = $RC_D_NEW  positive-half-fail=$D_POS"
verdict "D the SHIPPED grader REFUSES a file that no longer says what the baseline IS" "$RC_D_NEW" 1
verdict "D on the POSITIVE half, x1" "$D_POS" 1
echo

# =========================================================================================
# CASE E — THE FOOTER ASSERTION, DRIVEN (C-T448-6). Delete run-all.sh's regenerated footer
# marker and section 10 must go red. An assertion nobody has seen fail is not an assertion.
# =========================================================================================
prepare || { echo "REFUSED: could not prepare for case E" >&2; exit 3; }
python3 - "$D/$RUNALL" <<'PYEOF' || exit 3
import sys
path = sys.argv[1]
marker = "CORRECTION INDEX, REGENERATED ON EVERY RUN"
src = open(path, encoding="utf-8").read()
if marker not in src:
    print("REFUSED: the footer marker is already absent; the edit would be a no-op.")
    sys.exit(3)
open(path, "w", encoding="utf-8").write(src.replace(marker, "correction notes"))
print("removed the regenerated-footer marker from run-all.sh")
PYEOF
RC_E_NEW="$(grade_new E-footer-removed)"
E_FOOT="$(grep -c -F -- 'FAIL  run-all.sh REGENERATES its correction footer' "$OUT/tag-E-footer-removed-new.txt")"
echo "  E regenerated footer removed            shipped section 10 exit = $RC_E_NEW  footer-fail=$E_FOOT"
verdict "E the SHIPPED grader REFUSES a run-all.sh that stopped emitting its footer" "$RC_E_NEW" 1
verdict "E on the footer assertion, x1" "$E_FOOT" 1
echo

echo "############ SUMMARY — shipped section 10 vs T433's guard vs T448's supplied predicate"
printf '  %-34s %-10s %-10s %s\n' case shipped T433-guard T448-predicate
printf '  %-34s %-10s %-10s %s\n' "A control"                 "$RC_A_NEW" "$RC_A_OLD" "$(echo "$P_A" | awk '{print $3}')"
printf '  %-34s %-10s %-10s %s\n' "B live echo, tag in comment" "$RC_B_NEW" "$RC_B_OLD" "$(echo "$P_B" | awk '{print $3}')"
printf '  %-34s %-10s %-10s %s\n' "C quotation deleted"       "$RC_C_NEW" "$RC_C_OLD" "$(echo "$P_C" | awk '{print $3}')"
printf '  %-34s %-10s %-10s %s\n' "D replacement text removed" "$RC_D_NEW" "-"        "-"
printf '  %-34s %-10s %-10s %s\n' "E footer marker removed"   "$RC_E_NEW" "-"        "-"
echo
if [ "$FAILURES" -ne 0 ]; then
  echo "T455 TAG-BINDING DRIVE: FAIL — $FAILURES case(s) did not behave as recorded."
  exit 1
fi
echo "T455 TAG-BINDING DRIVE: PASS. Both of T448's abuses are RED in the shipped grader, each"
echo "on a DIFFERENT named predicate, while the honest tree stays green; and the review's own"
echo "one-predicate repair is measured to close (C) and NOT (B)."
exit 0
