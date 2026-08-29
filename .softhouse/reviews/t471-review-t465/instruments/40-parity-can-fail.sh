#!/usr/bin/env bash
# T471 -- CAN T465'S PARITY INSTRUMENT GO RED?  A GREEN THAT COULD NOT HAVE GONE RED PROVES
# NOTHING, and this program has recorded that repeatedly. T465 reports
# `baseLiterals=43 headLiterals=0 mismatches=0` and reports that the instrument caught a real
# defect of its own mid-repair (a prose reword inside a `new='''...'''` PATCH PAYLOAD). The
# defect itself was never committed, so it cannot be re-derived. What CAN be driven is whether
# the instrument would catch that defect class, and whether its calibration arm fires.
#
# FOUR ARMS, all against a THROWAWAY COPY of T465's tip that lives OUTSIDE the graded repo:
#   BASELINE   as shipped                                  -> expect exit 0, mismatches=0
#   K-PAYLOAD  reword ONE word inside a patch payload      -> expect exit 1, a MISMATCH
#   K-VALUE    widen an assembled pathspec by one char     -> expect exit 1, a MISMATCH
#   K-CALIB    run it with base == head (nothing to remove)-> expect exit 92, NO probe line
#
# NO REAL REPO PATH IS SPELT HERE (P-103): assembled from $S.
# EXIT 0 all arms behaved; 1 an arm misbehaved; 2 a dependency did not resolve.

set -u
S=".softhouse"
INSTR_REL="$S/capture/t465-lock-frontier/instruments/20-assembly-parity.py"
PATCH_REL="$S/reviews/t202-probe/patch.py"
ANCHOR_REL="$S/reviews/t172-probe/check-lock-exclusion-anchor.sh"
PROBE="T465-ASSEMBLY-PARITY:"

SRC="${1:-}"; BASE="${2:-}"; OUTDIR="${3:-}"
[ -n "$SRC" ] && [ -n "$BASE" ] && [ -n "$OUTDIR" ] || { echo "usage: $0 <tip-tree> <base-rev> <outdir>" >&2; exit 2; }
case "$SRC" in /Users/buv/gerege-nbfi*) echo "ERROR: the tree under test must be OUTSIDE the graded repo." >&2; exit 2;; esac
[ -f "$SRC/$INSTR_REL" ] || { echo "ERROR: no parity instrument at $SRC/$INSTR_REL -- REFUSING" >&2; exit 2; }
[ -d "$OUTDIR" ] || { echo "ERROR: no outdir" >&2; exit 2; }

bad=0
run () {   # $1 label, $2 expected exit, $3 expect-probe(yes/no), rest: extra argv
  local label exp expprobe f rc n
  label="$1"; exp="$2"; expprobe="$3"; shift 3
  f="$OUTDIR/parity-$label.txt"
  ( cd "$SRC" && python3 "$INSTR_REL" "$@" ) >"$f" 2>&1
  rc=$?
  n=$(grep -ac "$PROBE" "$f")
  printf 'ARM=%-11s exit=%-3s probe-lines=%s  (expected exit=%s probe=%s)\n' "$label" "$rc" "$n" "$exp" "$expprobe"
  [ "$n" -gt 0 ] && grep -a "$PROBE" "$f" | sed 's/^/    /'
  grep -a '^  !! ' "$f" | sed -n '1,4p' | sed 's/^/    /'
  if [ "$rc" != "$exp" ]; then echo "    ** MISBEHAVED: exit $rc, expected $exp"; bad=1; fi
  case "$expprobe" in
    yes) [ "$n" -ge 1 ] || { echo "    ** MISBEHAVED: no probe line"; bad=1; } ;;
    no)  [ "$n" -eq 0 ] || { echo "    ** MISBEHAVED: printed a probe line on a refusal"; bad=1; } ;;
  esac
}

cp "$SRC/$PATCH_REL"  "$OUTDIR/.patch.orig"
cp "$SRC/$ANCHOR_REL" "$OUTDIR/.anchor.orig"
# The pristine copies are RESTORED and then DELETED: a stray `.orig` beside the evidence is a
# second copy of a graded file with no owner, and T299's defect class is exactly run residue
# left inside a tracked directory.
restore () {
  cp "$OUTDIR/.patch.orig" "$SRC/$PATCH_REL"
  cp "$OUTDIR/.anchor.orig" "$SRC/$ANCHOR_REL"
  rm -f "$OUTDIR/.patch.orig" "$OUTDIR/.anchor.orig"
}
trap restore EXIT INT TERM

echo "=== BASELINE, as shipped"
run BASELINE 0 yes "$BASE"

echo "=== K-PAYLOAD: one word reworded INSIDE a patch payload (T465's own specimen class)"
python3 - "$SRC/$PATCH_REL" <<'PY'
import sys
p=sys.argv[1]; t=open(p).read()
needle="which is the one thing @LOCK@ exists to prevent"
assert t.count(needle)==1, "anchor not unique -- refusing to plant"
open(p,"w").write(t.replace(needle,"which is the sole thing @LOCK@ exists to prevent"))
PY
run K-PAYLOAD 1 yes "$BASE"
cp "$OUTDIR/.patch.orig" "$SRC/$PATCH_REL"

echo "=== K-VALUE: widen an assembled pathspec by one character at its DECLARATION"
python3 - "$SRC/$ANCHOR_REL" <<'PY'
import re,sys
p=sys.argv[1]; t=open(p).read()
m=[l for l in t.split("\n") if l.startswith("EXPECT_PATHSPEC=")]
assert len(m)==1, "expected exactly one declaration, found %d" % len(m)
open(p,"w").write(t.replace(m[0], m[0].rstrip()+'"*"'))
PY
run K-VALUE 1 yes "$BASE"
cp "$OUTDIR/.anchor.orig" "$SRC/$ANCHOR_REL"

echo "=== K-CALIB: base == head, so there is nothing to have removed"
run K-CALIB 92 no HEAD

echo "T471-PARITY-CANFAIL: arms=4 misbehaved=$bad"
[ "$bad" -eq 0 ] || exit 1
