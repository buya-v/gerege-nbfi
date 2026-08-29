#!/bin/bash
# T448 -- IS BOUNDARY (iv-a) REALLY "NOT CLOSABLE BY INTERNAL CONSISTENCY"?
#
# T433 discloses (iv-a) as an OPEN FAIL-OPEN and declares it unclosable: a FABRICATED
# post-fork observation added AT THE TIP with a matching MANIFEST.sha256 row is reached by no
# arm, and section 10 exits 0. T433's reason: "a fabricated observation is a claim about the
# oracle, and only the oracle can refute it."
#
# THE DISTINCTION T433's SENTENCE DOES NOT MAKE.  DETECTING a fabrication and REFUSING TO PASS
# ON IT are different problems. The first really does need the oracle. The second is internal,
# and verify-capture-integrity.py ALREADY STATES THE RULE FOR IT, at the site immediately above
# the born-at-tip branch, for the sibling case of a path with no recorded ADD commit:
#
#     "An arm that could not measure part of its own population has not passed on it."
#     "REFUSED, never a pass."
#
# A born-at-tip observation is the SAME category -- ARM F could not measure it -- and gets the
# OPPOSITE treatment: it is printed and the file exits 0. This script tests whether applying
# the file's own rule to its own boundary closes the fail-open, and what that costs.
#
# THE PATCH UNDER TEST is one `check(...)` call: assert `f_at_tip` is empty. On any tree where
# the captures were committed before HEAD this is free -- T448 measured 632 graded and 0 born
# at the tip on the tip of main -- so it fires ONLY in the commit that actually adds a capture,
# which is the moment a human is present to adjudicate it.
#
# ENGINE (P-33/P-53): `grep -c -F` (fixed strings) for every assertion; the patch is applied by
# python3 doing literal string surgery, so no regex dialect is load-bearing.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298):
#   T448_SRC=<repo>  T448_SCRATCH=<dir OUTSIDE the repo>  T448_OUT=<dir> \
#   T448_REF=<commit-ish carrying ARM F>  bash 40-t448-iva-closable.sh
#
# CALIBRATION BEFORE ANY NEGATIVE (P-72; C4): case 1 reproduces T433's own (iv-a) result on the
# UNPATCHED grader. If the fabrication does not come back exit 0 there, the construction is not
# the one T433 disclosed and nothing below is about T433's finding -- so the script REFUSES.
#
# EXIT 0  every case behaved as recorded.  EXIT 1  a case did not.  EXIT 3  REFUSED.
set -u

SRC="${T448_SRC:?T448_SRC must name the source repository}"
SCRATCH="${T448_SCRATCH:?T448_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T448_OUT:?T448_OUT must name the directory to write transcripts into}"
REF="${T448_REF:?T448_REF must name the commit-ish carrying ARM F}"

CAP=".softhouse/capture/tierA-a2"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
MAN="$CAP/MANIFEST.sha256"
FAB="T448-FABRICATED-OBSERVATION.http"

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t448-iva"
FAILURES=0

prepare() {
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
    git -C "$D" config user.email "t448@softhouse.local" || return 1
    git -C "$D" config user.name "T448" || return 1
  fi
  git -C "$D" checkout --quiet --detach "$REF" || return 1
  git -C "$D" reset --quiet --hard "$REF" || return 1
  git -C "$D" clean -qfdx || return 1
  return 0
}

fabricate() {   # a fabricated observation, added AT THE TIP, with a MATCHING manifest row
  printf 'T448 fabricated observation. Nothing in this repository observed it.\n' \
    > "$D/$CAP/out/$FAB" || return 1
  local d
  d="$(shasum -a 256 "$D/$CAP/out/$FAB" | awk '{print $1}')" || return 1
  [ -n "$d" ] || return 1
  printf '%s  out/%s\n' "$d" "$FAB" >> "$D/$MAN" || return 1
  git -C "$D" add -- "$CAP/out/$FAB" "$MAN" || return 1
  git -C "$D" commit -q -m "T448 (iv-a): fabricated observation added AT THE TIP with a matching manifest row" || return 1
  return 0
}

apply_patch() {   # the one-check patch: apply the file's OWN rule to its OWN boundary
  python3 - "$D/$INT" <<'PYEOF' || return 1
import sys
path = sys.argv[1]
anchor = 'check("EVERY post-fork observation ARM F was handed was readable at its own birth commit",'
src = open(path, encoding="utf-8").read()
if anchor not in src:
    print("REFUSED: the ARM F check block anchor is not in the grader; the patch would be a no-op.")
    sys.exit(1)
patch = (
    'check("NO post-fork observation was born AT THE TIP -- ARM F could not measure those, and "\n'
    '      "this file\'s own rule, stated for the sibling no-ADD-record case above, is that an "\n'
    '      "arm which could not measure part of its own population has NOT passed on it",\n'
    '      not f_at_tip, "born at the tip: %d" % len(f_at_tip))\n'
)
open(path, "w", encoding="utf-8").write(src.replace(anchor, patch + anchor, 1))
PYEOF
  grep -q -F -- "NO post-fork observation was born AT THE TIP" "$D/$INT" || return 1
  return 0
}

grade() {   # grade <case-name> ; echoes the exit code, writes the transcript
  local name="$1"
  ( cd "$D" && python3 "$INT" ) > "$OUT/iva-$name.txt" 2>&1
  echo $?
}

report() {   # report <label> <actual> <expected>
  if [ "$2" = "$3" ]; then
    printf '  %-52s rc=%s  expected %s  as recorded\n' "$1" "$2" "$3"
  else
    printf '  %-52s rc=%s  expected %s  *** UNEXPECTED ***\n' "$1" "$2" "$3"
    FAILURES=$((FAILURES + 1))
  fi
}

echo "############ T448 -- IS (iv-a) CLOSABLE BY INTERNAL CONSISTENCY?"
echo "  ref = $REF"
echo

# --- 1. CALIBRATION: reproduce T433's (iv-a) on the UNPATCHED grader. --------------------
if ! prepare; then echo "REFUSED: could not prepare the clone." >&2; exit 3; fi
if ! fabricate; then echo "REFUSED: could not build the fabrication." >&2; exit 3; fi
RC1="$(grade 1-unpatched-fabrication)"
report "1. UNPATCHED grader, fabrication born at the tip" "$RC1" 0
if [ "$RC1" != "0" ]; then
  echo "REFUSED: P-72 CALIBRATION FAILED. T433's (iv-a) construction did not reproduce as an" >&2
  echo "REFUSED: exit 0 here, so nothing below would be about T433's disclosed fail-open." >&2
  exit 3
fi
TIPLINES="$(grep -c -F -- "UNGRADED-BORN-AT-TIP out/$FAB" "$OUT/iva-1-unpatched-fabrication.txt")"
echo "     ARM F PRINTS it as ungraded x$TIPLINES, and the file still exits 0 -- the fail-open."
echo

# --- 2. THE PATCH, on the SAME fabricated tree. -------------------------------------------
if ! apply_patch; then echo "REFUSED: could not apply the one-check patch." >&2; exit 3; fi
RC2="$(grade 2-patched-fabrication)"
report "2. PATCHED grader, same fabrication" "$RC2" 1
CAUGHT="$(grep -c -F -- "FAIL  NO post-fork observation was born AT THE TIP" "$OUT/iva-2-patched-fabrication.txt")"
echo "     the named assertion that fails: x$CAUGHT"
if [ "$CAUGHT" != "1" ]; then FAILURES=$((FAILURES + 1)); fi
echo

# --- 3. THE COST. The same patch on a CLEAN tree must stay GREEN, or the close is unusable.
if ! prepare; then echo "REFUSED: could not prepare the clean clone." >&2; exit 3; fi
if ! apply_patch; then echo "REFUSED: could not apply the patch to the clean clone." >&2; exit 3; fi
RC3="$(grade 3-patched-clean)"
report "3. PATCHED grader, CLEAN tree (the cost of the close)" "$RC3" 0
GRADED="$(sed -n 's/^      GRADED against a birth blob older than HEAD *: \([0-9]*\)$/\1/p' "$OUT/iva-3-patched-clean.txt")"
ATTIP="$(sed -n 's/^      UNGRADED, born AT THE TIP (boundary iv-a) *: \([0-9]*\)$/\1/p' "$OUT/iva-3-patched-clean.txt")"
echo "     on the clean tree ARM F graded ${GRADED:-?} and found ${ATTIP:-?} born at the tip,"
echo "     so the added check costs NOTHING except in the commit that actually adds a capture."

# --- 4. THE OTHER ROUTE INTO (iv-a): rename + whole rewrite (T433's iv-b2). ----------------
if ! prepare; then echo "REFUSED: could not prepare the clone for the iv-b2 route." >&2; exit 3; fi
TARGET="out/A2-200-glaccounts-live-precheck.http"
if [ ! -f "$D/$CAP/$TARGET" ]; then
  echo "REFUSED: $TARGET is not in the tree; the iv-b2 route cannot be built." >&2
  exit 3
fi
NEW="out/T448-REWRITTEN-observation.http"
git -C "$D" mv "$CAP/$TARGET" "$D/$CAP/$NEW" 2>/dev/null || git -C "$D" mv "$CAP/$TARGET" "$CAP/$NEW" || exit 3
printf 'T448 iv-b2 route: every byte replaced, so git records a genuine ADD at the tip.\n' \
  > "$D/$CAP/$NEW" || exit 3
DIG="$(shasum -a 256 "$D/$CAP/$NEW" | awk '{print $1}')" || exit 3
python3 - "$D/$MAN" "$TARGET" "$NEW" "$DIG" <<'PYEOF' || exit 3
import sys
man, old, new, dig = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
lines = open(man, encoding="utf-8").read().split("\n")
out, hit = [], 0
for ln in lines:
    if ln.endswith(" " + old) or ln.endswith("  " + old):
        out.append("%s  %s" % (dig, new))
        hit += 1
    else:
        out.append(ln)
if hit != 1:
    print("REFUSED: expected exactly one manifest row for %s, found %d." % (old, hit))
    sys.exit(1)
open(man, "w", encoding="utf-8").write("\n".join(out))
PYEOF
git -C "$D" add -A -- "$CAP" || exit 3
git -C "$D" commit -q -m "T448 iv-b2 route: observation renamed and wholly rewritten, manifest relabelled, ONE commit" || exit 3
RC4="$(grade 4-unpatched-ivb2)"
report "4. UNPATCHED grader, iv-b2 route into (iv-a)" "$RC4" 0
if ! apply_patch; then echo "REFUSED: could not apply the patch for the iv-b2 route." >&2; exit 3; fi
RC5="$(grade 5-patched-ivb2)"
report "5. PATCHED grader, iv-b2 route into (iv-a)" "$RC5" 1

echo
echo "############ WHAT THIS MEASURED"
echo "  UNPATCHED: fabrication rc=$RC1, iv-b2 rc=$RC4  -- both exit 0, T433's disclosed fail-open."
echo "  PATCHED  : fabrication rc=$RC2, iv-b2 rc=$RC5  -- both RED, on a NAMED assertion."
echo "  COST     : the patched grader on a CLEAN tree rc=$RC3."
echo
echo "  This does NOT detect a fabrication -- nothing internal can, and T433 is right about"
echo "  that half. It removes the FAIL-OPEN: the grader stops exiting 0 over a population it"
echo "  did not measure, which is the rule the file already applies to its sibling case."
if [ "$FAILURES" -ne 0 ]; then
  echo
  echo "T448 (iv-a) CLOSABILITY: $FAILURES case(s) did not behave as recorded. Read them above."
  exit 1
fi
echo
echo "T448 (iv-a) CLOSABILITY VERDICT: THE FAIL-OPEN IS CLOSABLE INTERNALLY, at zero cost on a"
echo "clean tree, by one check that applies the grader's own stated rule to its own boundary."
exit 0
