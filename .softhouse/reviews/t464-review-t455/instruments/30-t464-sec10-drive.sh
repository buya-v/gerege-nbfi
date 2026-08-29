#!/bin/bash
# T464 — end-to-end drive of the SHIPPED section 10 (T455 / C-T448-2) at the AFTER ref, with
# my own mutations, plus the P-45 wiring question. Not T455's instrument.
set -u
S='.softhouse'
GRADER="$S/reviews/A2-11/verify-capture-integrity.py"
RUNALL="$S/reviews/A2-11/run-all.sh"
SRC="${T464_SRC:?}"; SCRATCH="${T464_SCRATCH:?}"; REF="${T464_AFTER:?}"
D="$SCRATCH/sec10"; FAIL=0

prepare() {
  if [ ! -d "$D/.git" ]; then rm -rf "$D"; git clone --quiet --shared "$SRC" "$D" || return 3; fi
  git -C "$D" checkout --quiet --force --detach "$REF" || return 3
  git -C "$D" reset --quiet --hard "$REF" || return 3
  git -C "$D" clean -qfdx || return 3
  [ -f "$D/$GRADER" ] || return 3
}
grade() { ( cd "$D" && python3 "$GRADER" ) > "$SCRATCH/s10-$1.txt" 2>&1; echo $?; }
expect() { if [ "$2" = "$3" ]; then echo "  OK   $1: grader exit $2"; else echo "  BAD  $1: grader exit $2 want $3"; FAIL=$((FAIL+1)); fi; }

# the sentence is ASSEMBLED, never a literal in this file (it would be an untagged assertion)
W1="There is no committed baseline older than"; W2="HEAD for those 632."
SENT="$W1 $W2"
TAGW="QUOTED-FALSE-CLAIM"

echo "############ T464 — SHIPPED SECTION 10, DRIVEN"
prepare || exit 3
RC="$(grade A-control)"; expect "A control, unmutated AFTER tree" "$RC" 0
grep -n 'PREDICATE 1\|PREDICATE 2\|SELF-DRIVE\|VACUITY' "$SCRATCH/s10-A-control.txt" | grep -c 'PASS' | sed 's/^/       section-10 PASS lines: /'

prepare || exit 3
python3 - "$D/$RUNALL" "$SENT" "$TAGW" <<'PYEOF' || exit 3
import sys
p, sent, tag = sys.argv[1], sys.argv[2], sys.argv[3]
anchor = '  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
s = open(p, encoding="utf-8").read()
assert anchor in s
open(p, "w", encoding="utf-8").write(s.replace(anchor, '  echo "%s"  # %s\n' % (sent, tag) + anchor, 1))
PYEOF
RC="$(grade B-echo-tag-in-comment)"; expect "B  echo, tag in trailing comment" "$RC" 1
grep 'FAIL  PREDICATE' "$SCRATCH/s10-B-echo-tag-in-comment.txt" | cut -c1-95 | sed 's/^/       /'

prepare || exit 3
python3 - "$D/$RUNALL" <<'PYEOF' || exit 3
import sys
p = sys.argv[1]
tag = "QUOTED-" + "FALSE-CLAIM"
anchor = '  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
lines = open(p, encoding="utf-8").read().split("\n")
kept = [l for l in lines if tag not in l]
assert len(lines) - len(kept) >= 3, "expected >=3 tagged lines"
i = kept.index(anchor)
open(p, "w", encoding="utf-8").write("\n".join(kept[:i] + ["  # %s (tidied)" % tag] * 3 + kept[i:]))
PYEOF
RC="$(grade C-quote-deleted)"; expect "C  quotation deleted, 3 bare tags" "$RC" 1
grep 'FAIL  PREDICATE' "$SCRATCH/s10-C-quote-deleted.txt" | cut -c1-95 | sed 's/^/       /'

# ---- MY OWN CASE: the same abuse as B, but through printf (an emitter already used 12x in
# 10-drive-conditions.sh and 5x in run-all.sh). Does PREDICATE 2 see it?
prepare || exit 3
python3 - "$D/$RUNALL" "$SENT" "$TAGW" <<'PYEOF' || exit 3
import sys
p, sent, tag = sys.argv[1], sys.argv[2], sys.argv[3]
anchor = '  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
s = open(p, encoding="utf-8").read()
assert anchor in s
smug = "  printf '%%s\\n' \"" + sent + '"  # ' + tag + "\n"
open(p, "w", encoding="utf-8").write(s.replace(anchor, smug + anchor, 1))
PYEOF
RC="$(grade Bprime-printf)"; echo "  ??   B' printf, tag in trailing comment: grader exit $RC  (0 = EVADES)"
( cd "$D" && bash "$RUNALL" ) > "$SCRATCH/s10-Bprime-runall.txt" 2>&1
PRINTED_UNTAGGED="$(grep -F -- "$SENT" "$D/$S/reviews/A2-11/TRANSCRIPT-A2-11.txt" | grep -c -v -F "$TAGW")"
echo "       the regenerated transcript carries the sentence UNTAGGED x$PRINTED_UNTAGGED"

echo
echo "--- P-45: WHAT INVOKES THE GRADER? (assembled path, printed) ---"
git -C "$D" grep -n -- "verify-capture-integrity.py" -- "*.sh" | grep -v "/out/" | grep -E "python3 |INT=" | sed 's/^/    /'
echo
[ "$FAIL" -ne 0 ] && { echo "T464 SECTION-10 DRIVE: $FAIL case(s) off."; exit 1; }
echo "T464 SECTION-10 DRIVE: A/B/C as T455 recorded. EXIT 0"
