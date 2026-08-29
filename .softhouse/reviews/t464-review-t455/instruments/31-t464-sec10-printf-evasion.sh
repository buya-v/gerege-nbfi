#!/bin/bash
# T464 — B' : the abuse-B shape through `printf`, an emitter already used 12x in
# 10-drive-conditions.sh and 5x in run-all.sh. Does section 10 see it, and does the sentence
# actually reach the transcript untagged?
set -u
S='.softhouse'
GRADER="$S/reviews/A2-11/verify-capture-integrity.py"
RUNALL="$S/reviews/A2-11/run-all.sh"
TRANS="$S/reviews/A2-11/TRANSCRIPT-A2-11.txt"
SRC="${T464_SRC:?}"; SCRATCH="${T464_SCRATCH:?}"; REF="${T464_AFTER:?}"
D="$SCRATCH/pf"
W1="There is no committed baseline older than"; W2="HEAD for those 632."
SENT="$W1 $W2"; TAGW="QUOTED-FALSE-CLAIM"

rm -rf "$D"; git clone --quiet --shared "$SRC" "$D" || exit 3
git -C "$D" checkout --quiet --force --detach "$REF" || exit 3
git -C "$D" clean -qfdx || exit 3

python3 - "$D/$RUNALL" "$SENT" "$TAGW" <<'PYEOF' || exit 3
import sys
p, sent, tag = sys.argv[1], sys.argv[2], sys.argv[3]
anchor = '  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
s = open(p, encoding="utf-8").read()
assert anchor in s
smug = '  printf "' + sent + '\\n"  # ' + tag + "\n"
open(p, "w", encoding="utf-8").write(s.replace(anchor, smug + anchor, 1))
PYEOF

echo "smuggled line, as written into run-all.sh:"
grep -n -F -- "$SENT" "$D/$RUNALL" | sed 's/^/    /'
echo
( cd "$D" && python3 "$GRADER" ) > "$SCRATCH/pf-grader.txt" 2>&1
echo "  section-10 grader exit = $?   (0 means the smuggle EVADES both predicates)"
grep -c 'FAIL  ' "$SCRATCH/pf-grader.txt" | sed 's/^/  FAIL lines in the grader: /'
( cd "$D" && bash "$RUNALL" ) > "$SCRATCH/pf-runall.txt" 2>&1
echo "  run-all.sh exit = $?"
ALL="$(grep -c -F -- "$SENT" "$D/$TRANS")"
UNT="$(grep -F -- "$SENT" "$D/$TRANS" | grep -c -v -F "$TAGW")"
echo "  the REGENERATED transcript carries the sentence x$ALL, of which x$UNT carry NO tag."
grep -F -- "$SENT" "$D/$TRANS" | grep -v -F "$TAGW" | sed 's/^/      UNTAGGED IN TRANSCRIPT: /'
