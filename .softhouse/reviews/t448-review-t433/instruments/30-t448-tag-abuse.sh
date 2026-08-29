#!/bin/bash
# T448 -- CAN THE `[QUOTED-FALSE-CLAIM]` TAG BE ABUSED TO SMUGGLE THE FALSE CLAIM BACK?
#
# T433's correction technique: the false sentence is kept VERBATIM at each corrected site and
# tagged `[QUOTED-FALSE-CLAIM]`, and `30-t433-armf-wiring-guard.sh` asserts BOTH halves --
#   NEGATIVE  no UNTAGGED line asserts the impossibility, and
#   POSITIVE  the tagged quote is still present (at least 3 tagged lines per file).
# T433 drove the guard red four ways. This file asks the opposite question: is the TAG ITSELF
# a way past the guard? The guard's predicate is, verbatim:
#
#     got="$(grep -Ei "$IMPOSS" "$f" | grep -vc "QUOTED-FALSE-CLAIM")"
#     q="$(grep -c "QUOTED-FALSE-CLAIM" "$f")"   ...   [ "$q" -ge 3 ]
#
# Both halves are LINE-LEVEL and TOKEN-LEVEL. Neither asserts that the tag and the quoted text
# are on the same line FOR THE SAME REASON, and neither reads what the file PRINTS. Two
# constructions follow from reading that predicate, and both are DRIVEN here rather than argued.
#
# ENGINE (P-33/P-53): `grep -c -F` (fixed strings) for every assertion this file makes; the
# edits are made by python3 doing literal string surgery, so no regex dialect is load-bearing.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298):
#   T448_SRC=<repo>  T448_SCRATCH=<dir OUTSIDE the repo>  T448_OUT=<dir> \
#   T448_REF=<commit-ish carrying T433's correction>  bash 30-t448-tag-abuse.sh
#
# CALIBRATION BEFORE ANY NEGATIVE (P-72; C4): case A runs the guard on an UNMUTATED clone and
# it must exit 0. A guard that is already red would make every "defeated" verdict below free.
#
# EXIT 0  every case behaved as recorded. EXIT 1 a case did not. EXIT 3 REFUSED, never a pass.
set -u

SRC="${T448_SRC:?T448_SRC must name the source repository}"
SCRATCH="${T448_SCRATCH:?T448_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T448_OUT:?T448_OUT must name the directory to write transcripts into}"
REF="${T448_REF:?T448_REF must name the commit-ish carrying the T433 correction}"

GUARD=".softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh"
RUNALL=".softhouse/reviews/A2-11/run-all.sh"
FALSE_SENTENCE="There is no committed baseline older than HEAD for those 632."

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t448-tag"
FAILURES=0

prepare() {
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
  fi
  git -C "$D" checkout --quiet --detach "$REF" || return 1
  git -C "$D" reset --quiet --hard "$REF" || return 1
  git -C "$D" clean -qfdx || return 1
  [ -f "$D/$GUARD" ] || return 1
  [ -f "$D/$RUNALL" ] || return 1
  return 0
}

run_guard() {   # run_guard <case-name> ; echoes the exit code
  local name="$1"
  T433_ROOT="$D" bash "$D/$GUARD" > "$OUT/tagabuse-$name.txt" 2>&1
  echo $?
}

echo "############ T448 -- ABUSING THE [QUOTED-FALSE-CLAIM] TAG"
echo "  ref = $REF"
echo

# ---------------------------------------------------------------------------------------
# CASE A -- CALIBRATION. The guard must be GREEN on the unmutated tree.
# ---------------------------------------------------------------------------------------
if ! prepare; then
  echo "REFUSED: could not prepare a clone of $SRC at $REF carrying both $GUARD and $RUNALL." >&2
  exit 3
fi
RC_A="$(run_guard A-control)"
echo "  A control (unmutated)                                 guard exit = $RC_A"
if [ "$RC_A" != "0" ]; then
  echo "REFUSED: P-72 CALIBRATION FAILED -- the wiring guard is already RED on the unmutated" >&2
  echo "REFUSED: tree, so 'the guard did not notice' below would be free. No verdict." >&2
  exit 3
fi
echo "  P-72 calibration OK: the wiring guard is GREEN before anything is smuggled."
echo

# ---------------------------------------------------------------------------------------
# CASE B -- SMUGGLE THE CLAIM BACK AS A LIVE, PRINTED ASSERTION.
# The tag goes in a TRAILING SHELL COMMENT. The guard reads the SOURCE line, sees the token,
# and excludes the line. The READER sees stdout, where the comment does not appear -- so the
# sentence is printed with no tag at all.
# ---------------------------------------------------------------------------------------
if ! prepare; then
  echo "REFUSED: could not prepare the clone for case B." >&2
  exit 3
fi
python3 - "$D/$RUNALL" "$FALSE_SENTENCE" <<'PYEOF' || exit 3
import sys
path, sentence = sys.argv[1], sys.argv[2]
anchor = '  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
src = open(path, encoding="utf-8").read()
if anchor not in src:
    print("REFUSED: the section-10 anchor line is not in run-all.sh; the edit would be a no-op.")
    sys.exit(3)
smuggled = '  echo "%s"  # QUOTED-FALSE-CLAIM\n' % sentence
open(path, "w", encoding="utf-8").write(src.replace(anchor, smuggled + anchor, 1))
PYEOF
SRC_HITS="$(grep -c -F -- "$FALSE_SENTENCE" "$D/$RUNALL")"
echo "  B smuggle-as-live-echo: the sentence now appears x$SRC_HITS in run-all.sh's source"
RC_B="$(run_guard B-smuggle-live-echo)"
echo "  B smuggle-as-live-echo (tag in a trailing comment)    guard exit = $RC_B"
if [ "$RC_B" = "0" ]; then
  echo "       DEFEATED: the guard PASSES a file that re-asserts the false claim as a live echo."
else
  echo "       HELD: the guard caught it."
  FAILURES=$((FAILURES + 1))
fi
# And prove it actually PRINTS untagged, rather than merely sitting in the source.
( cd "$D" && bash "$RUNALL" ) > "$OUT/tagabuse-B-runall.txt" 2>&1
PRINTED_TAGGED="$(grep -c -F -- "QUOTED-FALSE-CLAIM]  commit. $FALSE_SENTENCE" "$D/.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt")"
PRINTED_ALL="$(grep -c -F -- "$FALSE_SENTENCE" "$D/.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt")"
PRINTED_UNTAGGED="$(grep -F -- "$FALSE_SENTENCE" "$D/.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt" | grep -c -v -F "QUOTED-FALSE-CLAIM")"
echo "       run-all.sh's OWN transcript now carries the sentence x$PRINTED_ALL, of which"
echo "       x$PRINTED_UNTAGGED carry NO tag at all (tagged quotation lines: x$PRINTED_TAGGED)."
if [ "$PRINTED_UNTAGGED" -lt 1 ]; then
  echo "       (the smuggled echo did not reach the transcript -- case B is inconclusive)"
  FAILURES=$((FAILURES + 1))
fi
echo

# ---------------------------------------------------------------------------------------
# CASE C -- DELETE THE QUOTED TEXT, KEEP THE TAG. The positive half counts TAGGED LINES; it
# never asserts that a tagged line contains the quoted sentence. Three bare tags satisfy it.
# ---------------------------------------------------------------------------------------
if ! prepare; then
  echo "REFUSED: could not prepare the clone for case C." >&2
  exit 3
fi
python3 - "$D/$RUNALL" <<'PYEOF' || exit 3
import sys
path = sys.argv[1]
lines = open(path, encoding="utf-8").read().split("\n")
kept, dropped = [], 0
for ln in lines:
    if "QUOTED-FALSE-CLAIM" in ln:
        dropped += 1
        continue
    kept.append(ln)
if dropped < 3:
    print("REFUSED: expected at least 3 tagged quotation lines to remove, found %d." % dropped)
    sys.exit(3)
anchor = '  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
if anchor not in kept:
    print("REFUSED: the section-10 anchor line vanished; the edit is not the one intended.")
    sys.exit(3)
i = kept.index(anchor)
bare = ['  # QUOTED-FALSE-CLAIM (tidied: the quotation was removed, the tag was not)'] * 3
open(path, "w", encoding="utf-8").write("\n".join(kept[:i] + bare + kept[i:]))
PYEOF
QUOTED_LEFT="$(grep -c -F -- "$FALSE_SENTENCE" "$D/$RUNALL")"
TAGS_LEFT="$(grep -c -F -- "QUOTED-FALSE-CLAIM" "$D/$RUNALL")"
echo "  C quote deleted, tag kept: the sentence appears x$QUOTED_LEFT, the tag x$TAGS_LEFT"
RC_C="$(run_guard C-quote-gone-tag-kept)"
echo "  C quote-deleted-tag-kept                              guard exit = $RC_C"
if [ "$RC_C" = "0" ]; then
  echo "       DEFEATED: the guard PASSES a file from which the verbatim quotation is GONE,"
  echo "       which is exactly the 'bare negation removed' outcome its third red drive exists"
  echo "       to prevent -- that drive deleted the tag WITH the text, so it never separated"
  echo "       the tag from the text."
else
  echo "       HELD: the guard caught it."
  FAILURES=$((FAILURES + 1))
fi

echo
echo "############ SUMMARY"
echo "  A control                     guard exit $RC_A"
echo "  B claim re-asserted, tag in a trailing comment   guard exit $RC_B"
echo "  C quotation deleted, three bare tags kept        guard exit $RC_C"
echo
if [ "$FAILURES" -ne 0 ]; then
  echo "T448 TAG-ABUSE VERDICT: at least one construction did NOT behave as this file recorded."
  echo "Read the cases above; $FAILURES case(s) differ."
  exit 1
fi
echo "T448 TAG-ABUSE VERDICT: BOTH CONSTRUCTIONS PASS THE GUARD. The guard grades the TAG,"
echo "not the tag's BINDING to the quoted text, and it never reads what the file PRINTS."
exit 0
