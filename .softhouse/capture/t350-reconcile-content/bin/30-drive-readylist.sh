#!/usr/bin/env bash
# T350 -- the OTHER direction, and it is NOT reachable through branch_wip().
#
# T421 was carried `needs_review` and T428 `needs_retry` while 33 and 35 tracked
# files respectively sat on main. `branch_wip()` is called ONLY for tasks whose
# status is `in_progress` -- in reconcile()'s loop and in main()'s IN PROGRESS
# section. A `needs_retry` task is printed in the READY list as
#
#     T428     opus   review  INDEPENDENT review of T421 ...
#
# with no evidence line of any kind, and the driver dispatches from that list.
# So for these two the reconciler did not answer wrongly -- IT WAS NEVER ASKED.
# "A branch that is gone is not evidence of no work" has to be enforced where the
# dispatch decision is actually made.
#
# This drive builds a tasks.json carrying the two records EXACTLY as fire
# 20260829-080002 iter5 found them, and runs the resolver's normal (non-reconcile)
# path against a fixture main that is today's tip -- where both tasks' deliverables
# demonstrably ARE tracked.
set -u
MOD="${1:?usage: 30-drive-readylist.sh <path-to-ready-tasks.py> <label>}"
LABEL="${2:?}"
FIX=/tmp/t350-fixture
SRC="$(cd "$(dirname "$0")/../../../.." && pwd)"

git -C "$FIX" checkout --quiet --detach 2>/dev/null
HEAD_SHA=$(git -C "$FIX" rev-parse HEAD)
git -C "$FIX" branch -f main "$HEAD_SHA" >/dev/null
git -C "$FIX" update-ref -d refs/heads/softhouse/T421-t406-conditions 2>/dev/null
git -C "$FIX" update-ref -d refs/heads/softhouse/T428-review-t421 2>/dev/null

mkdir -p "$FIX/.softhouse/runs"
cat > "$FIX/.softhouse/tasks.json" <<'JSON'
{
  "tasks": [
    {
      "id": "T421",
      "status": "needs_review",
      "branch": "softhouse/T421-t406-conditions",
      "model": "opus",
      "target": "review",
      "title": "T406's six conditions on T391",
      "dependencies": []
    },
    {
      "id": "T428",
      "status": "needs_retry",
      "branch": "softhouse/T428-review-t421",
      "model": "opus",
      "target": "review",
      "title": "INDEPENDENT review of T421",
      "note": "worker killed mid-flight ... a killed worker is dead, not paused",
      "dependencies": []
    },
    {
      "id": "T351",
      "status": "needs_retry",
      "branch": "softhouse/T351-old-name",
      "model": "opus",
      "target": "code",
      "title": "CONTROL -- work lives on a live ref, NOT on main",
      "dependencies": []
    },
    {
      "id": "T339x",
      "status": "needs_retry",
      "branch": "softhouse/T339x-never-existed",
      "model": "opus",
      "target": "code",
      "title": "CONTROL -- genuinely unstarted, must stay silently READY",
      "dependencies": []
    }
  ]
}
JSON
cp "$SRC/.softhouse/program.json" "$FIX/.softhouse/program.json" 2>/dev/null
cp "$SRC/.softhouse/bin/branch_sweep.py" "$(dirname "$MOD")/branch_sweep.py" 2>/dev/null

echo "=============================================================================="
echo "T350 READY-LIST DRIVE -- $LABEL"
echo "module under test: $MOD"
echo "module sha256:     $(shasum -a 256 "$MOD" | cut -d' ' -f1)"
echo "fixture main:      $HEAD_SHA"
echo "  T421 needs_review, branch softhouse/T421-t406-conditions -- DELETED in fixture"
echo "  T428 needs_retry,  branch softhouse/T428-review-t421     -- DELETED in fixture"
echo "  T351 needs_retry,  branch softhouse/T351-old-name        -- never existed;"
echo "       softhouse/T351-progress-accounting is live and carries t351 content"
echo "  T339x needs_retry, branch softhouse/T339x-never-existed  -- truly nothing"
echo "tracked on fixture main:"
echo -n "  paths naming t421: "; git -C "$FIX" ls-tree -r --name-only main | grep -ci 't421'
echo -n "  paths naming t428: "; git -C "$FIX" ls-tree -r --name-only main | grep -ci 't428'
echo -n "  paths naming t351: "; git -C "$FIX" ls-tree -r --name-only main | grep -ci 't351'
echo -n "  paths naming t339x: "; git -C "$FIX" ls-tree -r --name-only main | grep -ci 't339x'
echo "=============================================================================="
python3 "$MOD" --repo "$FIX"
echo "=============================================================================="
echo "resolver exit: $?"
