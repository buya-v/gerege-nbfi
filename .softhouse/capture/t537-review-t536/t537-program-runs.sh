#!/bin/sh
# T537 item 6 -- THE PROGRAM MUST STILL RUN.
#   * READY must print THROUGH the refusal
#   * --json must stay valid JSON on stdout
#   * no bypass flag, no env var
#   * time it -- a guard that makes the fire slow gets disabled as surely as one that
#     makes it fail
# Usage: sh t537-program-runs.sh <worktree-at-18c64389> <outdir>
set -u
WT=$1
OUT=$2
RT="$WT/.softhouse/bin/ready-tasks.py"

echo "=============================================================================="
echo "A. plain run over the real record -- timing and the shape of the report"
echo "=============================================================================="
S=$(date +%s.%N)
python3 "$RT" --repo "$WT" > "$OUT/t537-ready-plain.txt" 2>&1
RC=$?
E=$(date +%s.%N)
echo "exit code: $RC"
echo "wall clock: $(echo "$E - $S" | bc) s"
echo "report lines: $(wc -l < "$OUT/t537-ready-plain.txt")"
echo
echo "where the driver's own sections land:"
grep -n "^STEP 0\|^READY (\|^BLOCKED (\|^IN PROGRESS\|check-branch-published:\|>>> THE RECORD BELOW\|^GATES" \
    "$OUT/t537-ready-plain.txt" | head -20

echo
echo "=============================================================================="
echo "B. --json must stay valid JSON on stdout"
echo "=============================================================================="
python3 "$RT" --repo "$WT" --json > "$OUT/t537-ready.json" 2> "$OUT/t537-ready-json-stderr.txt"
echo "exit code: $?"
echo "stdout bytes: $(wc -c < "$OUT/t537-ready.json")   stderr bytes: $(wc -c < "$OUT/t537-ready-json-stderr.txt")"
python3 - "$OUT/t537-ready.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print("stdout parses as JSON: YES")
print("top-level keys:", sorted(d)[:12])
print("branch_published:", d.get("branch_published"))
print("ready count:", len(d.get("ready", [])))
PY

echo
echo "=============================================================================="
echo "C. checker --json in the exit-3 arm: document on stdout, banner on stderr"
echo "=============================================================================="
D="$OUT/../json3"; rm -rf "$D"; mkdir -p "$D/.softhouse/bin"
cp "$WT/.softhouse/bin/check-branch-published.py" "$D/.softhouse/bin/"
git -C "$D" init --quiet -b main
git -C "$D" remote add origin "$D/no-such-origin.git"
printf '{"run_id":"x","tasks":[]}' > "$D/.softhouse/tasks.json"
python3 "$D/.softhouse/bin/check-branch-published.py" --repo "$D" --json \
    > "$D/out.json" 2> "$D/err.txt"
echo "exit: $?"
python3 - "$D/out.json" <<'PY'
import json, sys
print("stdout parses as JSON:", end=" ")
try:
    d = json.load(open(sys.argv[1])); print("YES", d.get("verdict"))
except Exception as e:
    print("NO --", e)
PY
echo "stderr first line: $(head -1 "$D/err.txt")"

echo
echo "=============================================================================="
echo "D. IS THERE A BYPASS? -- flags and env vars in both files"
echo "=============================================================================="
echo "--- argument names the checker accepts:"
grep -oE '"--[a-z-]+"' "$WT/.softhouse/bin/check-branch-published.py" | sort -u | tr '\n' ' '
echo
echo "--- bypass-shaped words anywhere in either file:"
grep -nEi "offline|no-fetch|skip[-_]?(check|gate|guard)|--force|nocheck|bypass|disable|override" \
    "$WT/.softhouse/bin/check-branch-published.py" "$RT" | grep -v "^.*#" | head -20
echo "(lines above are non-comment hits; none = no bypass)"
echo
echo "--- every os.environ / getenv read in either file:"
grep -nE "os\.environ|getenv" "$WT/.softhouse/bin/check-branch-published.py" "$RT" | head -20
