#!/bin/bash
# T467 / F-T464-1 -- ABUSE (B) IS A CLASS, NOT A SPELLING. Driven RED and GREEN.
#
# T455 closed abuse (B) for the `echo` spelling. Its `emitted_payload` recognised exactly two
# shapes: a line whose first token is echo, and a line whose first token is print(. T464
# measured three other spellings straight through. This file re-derives all three at first
# hand rather than inheriting them:
#
#     printf FMT "<claim>"           # <tag>
#     >&2 echo "<claim>"             # <tag>
#     sys.stdout.write("<claim>")    # <tag>
#
# THE REACH IS NOT HYPOTHETICAL. printf is already used 12 times in 10-drive-conditions.sh and
# 5 times in run-all.sh -- two of the four files section 10 guards. Those cardinals are
# RE-COUNTED HERE, on the tree under test, and printed; they are not quoted from the review.
#
# THE REPAIR IS NOT THREE MORE NAMES. An emitter list is a list the next author extends
# without reading. The AFTER predicate asks what a line CARRIES to a reader -- every non-inert
# python string constant, every shell quoted segment outside a comment -- and names no emitter
# at all. So this file also drives a spelling NOBODY IN THIS REPOSITORY HAS USED (os.write to
# fd 1, through a variable) to test the CLASS claim rather than four instances of it.
#
# AND THE LOAD-BEARING HALF IS THE GREEN, NOT THE RED (P-72). A predicate that reddens honest
# trees is a freeze. Cases A/A2 and G are the calibration and the clean-tree control, at both
# refs and through the whole runner.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298), and no repo-relative path is spelled as a
# literal either: they are ASSEMBLED from S. Every location is a required parameter and a
# value that does not resolve is exit 3 -- never a skipped case, never a pass.
#
#   T467_SRC=<repo to clone>  T467_SCRATCH=<dir OUTSIDE the repo>  T467_OUT=<transcript dir> \
#   T467_BEFORE=<commit-ish with T455's echo-only matcher> \
#   T467_AFTER=<commit-ish with the payload predicate> \
#   bash 10-t467-printed-class.sh
#
# ENGINE (P-33/P-53): every assertion is an exit code or a grep -c -F fixed-string count.
#
# EXIT 0  every case produced the recorded outcome.
# EXIT 1  a case did not -- the finding is printed by name.
# EXIT 3  REFUSED: the harness could not measure. NEVER read as a pass.
set -u

SRC="${T467_SRC:?T467_SRC must name the source repository}"
SCRATCH="${T467_SCRATCH:?T467_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T467_OUT:?T467_OUT must name the directory to write transcripts into}"
BEFORE="${T467_BEFORE:?T467_BEFORE must name a commit-ish WITHOUT the payload predicate}"
AFTER="${T467_AFTER:?T467_AFTER must name a commit-ish WITH the payload predicate}"

# ASSEMBLED, NEVER SPELLED (guard_dead_path_frontier; six workers were refused last fire for
# writing a real repo path as a literal in an instrument).
S=".softhouse"
A2="$S/reviews/A2-11"
INT="$A2/verify-capture-integrity.py"
ADJ="$A2/adjudicate-section1.py"
RUNALL="$A2/run-all.sh"
TRANSCRIPT="$A2/TRANSCRIPT-A2-11.txt"
DRIVECOND="$S/capture/t393-t382-conditions/instruments/10-drive-conditions.sh"
TAG="QUOTED-FALSE-CLAIM"
# THE SENTENCE UNDER TEST IS ASSEMBLED, NOT TYPED. A literal here would be an UNTAGGED
# assertion of the false claim in a tracked executable -- the very thing being driven against.
SENTENCE="$(printf 'There is no committed baseline older than %s for those 632.' HEAD)"
ANCHOR='  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t467-printed"
FAILURES=0

verdict() {   # verdict <label> <got> <want>
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
  [ -f "$D/$INT" ]    || { echo "REFUSED: $INT absent at $ref" >&2; return 1; }
  [ -f "$D/$RUNALL" ] || { echo "REFUSED: $RUNALL absent at $ref" >&2; return 1; }
  [ -f "$D/$DRIVECOND" ] || { echo "REFUSED: $DRIVECOND absent at $ref" >&2; return 1; }
  return 0
}

grade() {     # grade <case> ; echoes section 10's exit code
  ( cd "$D" && python3 "$INT" ) > "$OUT/printed-$1.txt" 2>&1
  echo $?
}

p2_fails() { grep -c -F -- 'FAIL  PREDICATE 2, PRINTED' "$OUT/printed-$1.txt"; }
p1_fails() { grep -c -F -- 'FAIL  PREDICATE 1, BINDING' "$OUT/printed-$1.txt"; }

# smuggle <spelling> -- re-assert the sentence as a LIVE emitter with the tag in a trailing
# comment. The edit is python literal-string surgery, so no shell quoting is load-bearing.
smuggle() {
  python3 - "$D" "$INT" "$RUNALL" "$SENTENCE" "$TAG" "$1" "$ANCHOR" <<'PYEOF' || return 1
import os, sys
root, intp, runall, sentence, tag, spelling, anchor = sys.argv[1:8]
if spelling in ("echo", "printf", "stderr-echo"):
    path, target = os.path.join(root, runall), "shell"
else:
    path, target = os.path.join(root, intp), "python"
src = open(path, encoding="utf-8").read()
if target == "shell":
    if anchor not in src:
        print("REFUSED: the section-10 anchor is not in run-all.sh; the edit would be a no-op.")
        sys.exit(3)
    line = {
        "echo":        '  echo "%s"  # %s\n' % (sentence, tag),
        "printf":      "  printf '%%s\\n' \"%s\"  # %s\n" % (sentence, tag),
        "stderr-echo": '  >&2 echo "%s"  # %s\n' % (sentence, tag),
    }[spelling]
    out = src.replace(anchor, line + anchor, 1)
else:
    panchor = "print()\nif refusals:"
    if panchor not in src:
        print("REFUSED: the python anchor is not in the grader; the edit would be a no-op.")
        sys.exit(3)
    line = {
        "sys-stdout-write": 'sys.stdout.write("%s\\n")  # %s\n' % (sentence, tag),
        "os-write":         ('_t467 = "%s"  # %s\n' % (sentence, tag)
                             + 'os.write(1, _t467.encode())\n'),
    }[spelling]
    out = src.replace(panchor, line + panchor, 1)
if out == src:
    print("REFUSED: the smuggle edit changed nothing.")
    sys.exit(3)
open(path, "w", encoding="utf-8").write(out)
print("smuggled the sentence back as a LIVE %s, tag in a trailing comment" % spelling)
PYEOF
  return 0
}

echo "############ T467 / F-T464-1 -- WHAT A LINE PRINTS, NOT WHICH BUILTIN PRINTS IT"
echo "  BEFORE = $BEFORE   (T455's echo/print( matcher)"
echo "  AFTER  = $AFTER   (the payload predicate)"
echo

# =========================================================================================
# 0. THE REACH, RE-COUNTED ON THE TREE UNDER TEST. T464 states 12 and 5; this counts them.
# =========================================================================================
prepare "$AFTER" || { echo "REFUSED: could not prepare $AFTER" >&2; exit 3; }
PF_DRIVE="$(grep -c 'printf' "$D/$DRIVECOND")"
PF_RUNALL="$(grep -c 'printf' "$D/$RUNALL")"
ERR_DRIVE="$(grep -cE '>&2' "$D/$DRIVECOND")"
echo "  RE-DERIVED REACH (this tree, not the review's figures):"
echo "    printf in 10-drive-conditions.sh : $PF_DRIVE"
echo "    printf in run-all.sh             : $PF_RUNALL"
echo "    >&2    in 10-drive-conditions.sh : $ERR_DRIVE"
verdict "0 printf really is already in 10-drive-conditions.sh, 12 times" "$PF_DRIVE" 12
verdict "0 and in run-all.sh, 5 times" "$PF_RUNALL" 5
echo "    (so this is not a spelling someone would have to invent to defeat T455's matcher;"
echo "     it is the spelling the guarded files already reach for.)"
echo

# =========================================================================================
# A / A2 -- CALIBRATION. Both refs are GREEN on the unmutated tree.
# =========================================================================================
RC_A2="$(grade A2-control-AFTER)"
CHK_A2="$(grep -c '  PASS  \|  FAIL  ' "$OUT/printed-A2-control-AFTER.txt")"
verdict "A2 the AFTER grader is GREEN on the unmutated tree" "$RC_A2" 0
prepare "$BEFORE" || { echo "REFUSED: could not prepare $BEFORE" >&2; exit 3; }
RC_A="$(grade A-control-BEFORE)"
CHK_A="$(grep -c '  PASS  \|  FAIL  ' "$OUT/printed-A-control-BEFORE.txt")"
verdict "A  the BEFORE grader is GREEN on the unmutated tree" "$RC_A" 0
echo "     checks executed by the grader: BEFORE=$CHK_A  AFTER=$CHK_A2"
echo

# =========================================================================================
# THE FIVE SPELLINGS, AT BOTH REFS.
# =========================================================================================
for SPELL in echo printf stderr-echo sys-stdout-write os-write; do
  prepare "$BEFORE" || { echo "REFUSED: could not prepare $BEFORE for $SPELL" >&2; exit 3; }
  smuggle "$SPELL" || { echo "REFUSED: could not smuggle $SPELL at BEFORE" >&2; exit 3; }
  RCB="$(grade "B-$SPELL-BEFORE")"
  prepare "$AFTER" || { echo "REFUSED: could not prepare $AFTER for $SPELL" >&2; exit 3; }
  smuggle "$SPELL" || { echo "REFUSED: could not smuggle $SPELL at AFTER" >&2; exit 3; }
  RCA="$(grade "B-$SPELL-AFTER")"
  P2="$(p2_fails "B-$SPELL-AFTER")"
  P1="$(p1_fails "B-$SPELL-AFTER")"
  echo "  spelling: $SPELL"
  echo "    BEFORE section 10 exit = $RCB     AFTER section 10 exit = $RCA  (P2 fired x$P2, P1 x$P1)"
  case "$SPELL" in
    echo)
      verdict "  $SPELL is already CAUGHT at BEFORE -- T455's close, NOT REGRESSED here" "$RCB" 1 ;;
    *)
      verdict "  $SPELL GETS THROUGH at BEFORE" "$RCB" 0 ;;
  esac
  verdict "  $SPELL is REFUSED at AFTER" "$RCA" 1
  verdict "  $SPELL fires PREDICATE 2 exactly once" "$P2" 1
  verdict "  $SPELL does NOT fire PREDICATE 1 -- the SOURCE line does carry the tag" "$P1" 0
  echo
done

# =========================================================================================
# T -- THE READER'S ARTEFACT. run-all.sh, end to end, and the REGENERATED TRANSCRIPT.
# Section 10's exit code is an intermediate. The harm F-T464-1 names is a transcript that
# carries the false sentence UNTAGGED, so that is measured directly, at both refs.
# =========================================================================================
prepare "$BEFORE" || { echo "REFUSED: could not prepare $BEFORE for the transcript case" >&2; exit 3; }
smuggle printf || exit 3
bash "$D/$RUNALL" > "$OUT/printed-T-runall-BEFORE.txt" 2>&1
RC_T_B=$?
UNTAGGED_B="$(grep -F -- "$SENTENCE" "$D/$TRANSCRIPT" | grep -c -v -F -- "$TAG")"
TAGGEDLN_B="$(grep -F -- "$SENTENCE" "$D/$TRANSCRIPT" | grep -c -F -- "$TAG")"
echo "  T  BEFORE, printf smuggle, WHOLE RUNNER:"
echo "     run-all.sh exit = $RC_T_B"
echo "     regenerated transcript: sentence UNTAGGED x$UNTAGGED_B, tagged x$TAGGEDLN_B"
verdict "T  BEFORE run-all.sh PASSES a tree that prints the false sentence untagged" "$RC_T_B" 0
verdict "T  BEFORE the regenerated transcript carries it UNTAGGED, x1" "$UNTAGGED_B" 1

prepare "$AFTER" || { echo "REFUSED: could not prepare $AFTER for the transcript case" >&2; exit 3; }
smuggle printf || exit 3
bash "$D/$RUNALL" > "$OUT/printed-T-runall-AFTER.txt" 2>&1
RC_T_A=$?
SEC10_MOVED="$(grep -cE '^ +10 +0 +1 +\*\*\* MOVED \*\*\*' "$OUT/printed-T-runall-AFTER.txt")"
echo "  T  AFTER, the same smuggle, WHOLE RUNNER:"
echo "     run-all.sh exit = $RC_T_A   section 10 row MOVED x$SEC10_MOVED"
verdict "T  AFTER run-all.sh REFUSES it" "$RC_T_A" 1
verdict "T  AFTER the section 10 row is reported MOVED, x1" "$SEC10_MOVED" 1
echo

# =========================================================================================
# G -- THE CLEAN-TREE CONTROL THROUGH THE WHOLE RUNNER AT AFTER. Without this the reds above
# are free: a predicate that always fires would produce every one of them.
# =========================================================================================
prepare "$AFTER" || { echo "REFUSED: could not prepare $AFTER for the clean control" >&2; exit 3; }
bash "$D/$RUNALL" > "$OUT/printed-G-runall-AFTER-clean.txt" 2>&1
RC_G=$?
DEV_G="$(sed -n 's/^  *sections run: [0-9]*  *deviations: \([0-9]*\).*/\1/p' "$OUT/printed-G-runall-AFTER-clean.txt" | tail -1)"
[ -n "$DEV_G" ] || DEV_G=UNPRINTED
CLEAN_UNTAGGED="$(grep -F -- "$SENTENCE" "$D/$TRANSCRIPT" | grep -c -v -F -- "$TAG")"
echo "  G  AFTER, CLEAN TREE, whole runner: exit = $RC_G  deviations = $DEV_G"
verdict "G  the honest tree still PASSES the whole runner at AFTER" "$RC_G" 0
verdict "G  with zero deviations" "$DEV_G" 0
verdict "G  and its regenerated transcript carries NO untagged statement of the claim" "$CLEAN_UNTAGGED" 0
echo

# =========================================================================================
# COVERAGE (T467 / F-T464-5) -- WHICH BYTES THIS TRANSCRIPT ACTUALLY GRADED.
# T464's LOW finding was that T455's four transcripts recorded intermediate commits and a
# reader could not tell whether they covered the merged bytes without running git log. So the
# blob ids are printed HERE, in the transcript, for the files this drive grades. A reader
# checks coverage with one command per file: git rev-parse <tip>:<path>.
# =========================================================================================
echo "############ COVERAGE -- the graded bytes, named"
prepare "$AFTER" >/dev/null || exit 3
echo "  graded ref (AFTER) resolves to: $(git -C "$D" rev-parse HEAD)"
for f in "$INT" "$ADJ" "$RUNALL" "$DRIVECOND"; do
  printf '  %-62s blob %s\n' "$f" "$(git -C "$D" rev-parse "HEAD:$f")"
  printf '  %-62s last touched at this ref by %s\n' "" "$(git -C "$D" log -1 --format='%h %s' -- "$f")"
done
echo "  If git rev-parse <branch-tip>:<path> prints the same blob for each file above, this"
echo "  transcript grades the merged bytes. Any commit made on the branch after this ref that"
echo "  does not appear as the last-touched commit above left these files untouched."
echo

if [ "$FAILURES" -ne 0 ]; then
  echo "T467 PRINTED-CLASS DRIVE: FAIL -- $FAILURES case(s) did not behave as recorded."
  exit 1
fi
echo "T467 PRINTED-CLASS DRIVE: PASS. Five emitter spellings, one of them never used in this"
echo "repository, all RED at AFTER on PREDICATE 2, and all but echo GREEN at BEFORE; the whole"
echo "runner reproduces the reader-visible harm at BEFORE and refuses it at AFTER; and the"
echo "honest tree still passes end to end, with zero deviations."
exit 0
