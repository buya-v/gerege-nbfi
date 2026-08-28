#!/usr/bin/env bash
# T145 -- drive the ORIGINAL discriminate.py (READ-ONLY, T114) and the SCRATCH COPY,
# and diff both against the committed transcript.
#
# T114 ruling: discriminate.py produced committed evidence
# (.softhouse/capture/actualactual/analysis/DISCRIMINATION-OUTPUT.txt, cited by
# REPRODUCE.md:68). It is therefore NEVER edited in place. It is INVOKED here, which
# is a read; the repair lives only in the scratch copy.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
ANA="$ROOT/.softhouse/capture/actualactual/analysis"
OUT="$ROOT/.softhouse/capture/t145-analysis-float/out"
mkdir -p "$OUT"

echo "ROOT=$ROOT"
echo "REV=$(git -C "$ROOT" rev-parse HEAD)"
echo "python=$(python3 -VV | tr '\n' ' ')"
echo

echo "############ LEG 0 -- the ORIGINAL, re-run from its own directory (a READ) ############"
( cd "$ANA" && python3 discriminate.py ) > "$OUT/orig-rerun.txt" 2>&1
echo "  exit=$?"
if diff -q "$ANA/DISCRIMINATION-OUTPUT.txt" "$OUT/orig-rerun.txt" >/dev/null; then
  echo "  ORIGINAL REPRODUCES ITS COMMITTED TRANSCRIPT BYTE-FOR-BYTE"
else
  echo "  ORIGINAL DIVERGES FROM ITS COMMITTED TRANSCRIPT -- diff below"
  diff "$ANA/DISCRIMINATION-OUTPUT.txt" "$OUT/orig-rerun.txt" | head -60
fi
echo "  original bytes UNCHANGED on disk: $(git -C "$ROOT" diff --stat -- .softhouse/capture/actualactual/analysis/discriminate.py | wc -l | tr -d ' ') modified-file lines (0 == untouched)"
echo

echo "############ LEG 1 -- the SCRATCH COPY (parse_float=Decimal + exact-text predicate) ############"
( cd "$ANA" && python3 "$OUT/../bin/discriminate_v2.py" ) > "$OUT/v2-rerun.txt" 2>&1
echo "  exit=$?"
echo

echo "############ LEG 2 -- WHICH PUBLISHED NUMBERS CHANGE ############"
echo "  diff  committed transcript  vs  SCRATCH COPY output:"
if diff -q "$ANA/DISCRIMINATION-OUTPUT.txt" "$OUT/v2-rerun.txt" >/dev/null; then
  echo "    IDENTICAL -- NO published number changes under the repair."
else
  diff "$ANA/DISCRIMINATION-OUTPUT.txt" "$OUT/v2-rerun.txt" > "$OUT/published-delta.txt"
  echo "    DIFFERS. Full delta in out/published-delta.txt; changed lines:"
  sed 's/^/    /' "$OUT/published-delta.txt"
fi
