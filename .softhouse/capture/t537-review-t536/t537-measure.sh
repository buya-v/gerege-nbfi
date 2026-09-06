#!/bin/sh
# T537 item 2 -- RE-MEASURE THE TWO NUMBERS, apples to apples.
#
# T536 asserts, in `check-branch-published.py` above LANDING_PROMOTIONS:
#   "these four carry 66 of the 73 legitimate merged-and-pruned waivers
#    (`--measure-waivers` reproduces the count)"
#
# Both checkers are pointed at the SAME record -- the tree at 18c64389 -- so the only
# variable is the classifier. `--repo` supplies both the git repo and `tasks.json`;
# the tool itself is located by its own path, so T527's binary reads T536's record.
#
#   $1  path to the T537 review worktree (holds main's / T527's checker)
#   $2  path to the worktree at 18c64389 (holds T536's checker and the record)
set -e
MAIN="$1"
T536="$2"
OUT="$MAIN/.softhouse/capture/t537-review-t536"

echo "=============================================================================="
echo "A. T527's checker (on main) over the record at 18c64389"
echo "=============================================================================="
python3 "$MAIN/.softhouse/bin/check-branch-published.py" --repo "$T536" \
    > "$OUT/t537-measure-t527.txt" 2>&1 || true
grep -E "^(check-branch-published|origin:|backed:|WAIVED \(merged)" "$OUT/t537-measure-t527.txt"

echo
echo "=============================================================================="
echo "B. T536's checker over the same record"
echo "=============================================================================="
python3 "$T536/.softhouse/bin/check-branch-published.py" --repo "$T536" \
    > "$OUT/t537-measure-t536.txt" 2>&1 || true
grep -E "^(check-branch-published|origin:|backed:|WAIVED \(merged|baseline freeze)" \
    "$OUT/t537-measure-t536.txt"

echo
echo "=============================================================================="
echo "C. the two waiver sets, diffed by task+branch"
echo "=============================================================================="
awk '/^WAIVED \(merged/,/^$/' "$OUT/t537-measure-t527.txt" \
  | grep -E '^  [A-Za-z0-9-]+ +softhouse/' | awk '{print $1"\t"$2}' | sort -u \
  > "$OUT/t537-waivers-t527.txt"
awk '/^WAIVED \(merged/,/^$/' "$OUT/t537-measure-t536.txt" \
  | grep -E '^  [A-Za-z0-9-]+ +softhouse/' | awk '{print $1"\t"$2}' | sort -u \
  > "$OUT/t537-waivers-t536.txt"
echo "T527 pruned-proved waivers: $(wc -l < "$OUT/t537-waivers-t527.txt")"
echo "T536 pruned-proved waivers: $(wc -l < "$OUT/t537-waivers-t536.txt")"
echo
echo "LOST by T536's stricter classifier (in T527, not in T536):"
comm -23 "$OUT/t537-waivers-t527.txt" "$OUT/t537-waivers-t536.txt" || true
echo
echo "GAINED by T536 (in T536, not in T527):"
comm -13 "$OUT/t537-waivers-t527.txt" "$OUT/t537-waivers-t536.txt" || true
echo
echo "=============================================================================="
echo "D. findings counts"
echo "=============================================================================="
echo -n "T527 findings: "; grep -c '^  UNBACKED-\|^  LOCAL-ONLY-' "$OUT/t537-measure-t527.txt" || true
echo -n "T536 findings: "; grep -c '^  UNBACKED-\|^  LOCAL-ONLY-' "$OUT/t537-measure-t536.txt" || true
echo
echo "=============================================================================="
echo "E. does the documented flag --measure-waivers exist?"
echo "=============================================================================="
python3 "$T536/.softhouse/bin/check-branch-published.py" --measure-waivers \
    --repo "$T536" 2>&1 | head -3 || true
echo "(exit above)"
echo
echo "=============================================================================="
echo "F. highest task id in the shipped baseline (T536 claims T504)"
echo "=============================================================================="
python3 - "$T536/.softhouse/capture/t527-branch-published/baseline.json" <<'PY'
import json, re, sys
d = json.load(open(sys.argv[1]))
ids = [e["task"] for e in d["waived"]]
def ordi(t):
    m = re.fullmatch(r"[Tt](\d+)[a-z]?", t)
    if m: return (1, int(m.group(1)))
    m = re.fullmatch(r"[Aa]2-(\d+)", t)
    if m: return (0, int(m.group(1)))
    return (2, 0)
print("entries:", len(d["waived"]), " distinct tasks:", len(set(ids)))
print("frozen_above:", d.get("frozen_above"))
print("highest id present:", max(ids, key=ordi))
above = sorted({t for t in ids if ordi(t) > ordi(d.get("frozen_above","T527"))})
print("entries ABOVE the freeze line:", above or "none")
PY
