#!/bin/bash
# T357 — P-22 on T357's OWN deliverable ("a guard you have not seen fail is not a guard",
# and P-80: check your own deliverable against its own rule).
#
# T357 added two things to .softhouse/reviews/A2-11/: an aggregate VERDICT block in
# run-all.sh, and adjudicate-section1.py. Both are guards. Neither is a guard until it has
# been WATCHED failing on a broken input. adjudicate-section1.py carries its own in-process
# negative controls; this script proves the OUTER loop — that a broken input propagates all
# the way through run-all.sh's exit code, which is the number a caller actually reads.
#
# Every mutation is made in the working tree and REVERTED with `git checkout --` before the
# script returns, and the script verifies the revert with `git status --porcelain`. It never
# contacts the oracle.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
A2="$ROOT/.softhouse/reviews/A2-11"
OUT="$HERE/out"
mkdir -p "$OUT"

pass=0; fail=0
note() { echo; echo "=================================================================="; echo "$@"; echo "=================================================================="; }
assert() { # assert LABEL COND_STR ACTUAL EXPECTED
  if [ "$3" = "$4" ]; then echo "  PASS  $1 (got $3)"; pass=$((pass+1));
  else echo "  FAIL  $1 (got $3, expected $4)"; fail=$((fail+1)); fi
}

note "BASELINE — unmutated tree"
bash "$A2/run-all.sh" > /dev/null 2>&1; rc=$?
assert "run-all.sh exits 0 on a clean tree" x "$rc" 0
grep -c '\*\*\* MOVED \*\*\*' "$A2/TRANSCRIPT-A2-11.txt" > /dev/null
mv "$A2/TRANSCRIPT-A2-11.txt" "$OUT/50-TRANSCRIPT-t357-clean.txt"

note "NEGATIVE CONTROL 1 — an obs/ file goes MISSING."
echo "check-shape.py then aborts on a traceback. Note that a traceback also exits 1, which is"
echo "section 1's ADJUDICATED code, so the verdict block ALONE would not catch this. Section 9"
echo "is the layer that does: no 'FAILURES:' line means declared=None, and all three"
echo "adjudicated failures go missing. This control proves the two layers compose."
mv "$A2/obs/a2-11-get-loanproduct-22.json" "$A2/obs/.hidden-by-t357"
bash "$A2/run-all.sh" > /dev/null 2>&1; rc=$?
mv "$A2/obs/.hidden-by-t357" "$A2/obs/a2-11-get-loanproduct-22.json"
cp "$A2/TRANSCRIPT-A2-11.txt" "$OUT/51-NC1-missing-obs-file.txt"
assert "run-all.sh exits NON-ZERO when an obs/ file is missing" x "$([ "$rc" -ne 0 ] && echo nonzero || echo zero)" nonzero
assert "the verdict block names section 9 as MOVED" x \
  "$(awk '/^  9 /{print ($4=="***")?"moved":"notmoved"}' "$OUT/51-NC1-missing-obs-file.txt" | head -1)" moved

note "NEGATIVE CONTROL 2 — an ADJUDICATED failure is made to VANISH."
echo "Inject the exact three lines A2-7 FABRICATED into the product-46 observation. One of the"
echo "three adjudicated failures then flips to PASS. That is the dangerous direction — section 1"
echo "looks HEALTHIER — and it is precisely what re-admitting P-46's error would look like."
python3 - "$A2/obs/a2-11-get-loanproduct-46.json" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1])
d = json.loads(p.read_text())
d["paymentChannelToFundSourceMappings"] = None
p.write_text(json.dumps(d))
print("  injected the fabricated key into a throwaway copy of the observation")
PY
bash "$A2/run-all.sh" > /dev/null 2>&1; rc=$?
cp "$A2/TRANSCRIPT-A2-11.txt" "$OUT/52-NC2-vanished-failure.txt"
git -C "$ROOT" checkout -- .softhouse/reviews/A2-11/obs/a2-11-get-loanproduct-46.json
assert "run-all.sh exits NON-ZERO when an adjudicated failure vanishes" x \
  "$([ "$rc" -ne 0 ] && echo nonzero || echo zero)" nonzero
assert "section 9 reports the vanished failure by name" x \
  "$(grep -c 'missing=\[.*paymentChannelToFundSourceMappings' "$OUT/52-NC2-vanished-failure.txt")" 1

note "RESTORE — the tree must be exactly as it was"
cp "$OUT/50-TRANSCRIPT-t357-clean.txt" "$A2/TRANSCRIPT-A2-11.txt"
dirty="$(git -C "$ROOT" status --porcelain .softhouse/reviews/A2-11/obs/ | wc -l | tr -d ' ')"
assert "obs/ is byte-clean after both mutations" x "$dirty" 0
bash "$A2/run-all.sh" > /dev/null 2>&1; rc=$?
assert "run-all.sh is back to exit 0 after the reverts" x "$rc" 0

echo
echo "controls passed: $pass   controls failed: $fail"
[ "$fail" -eq 0 ]
