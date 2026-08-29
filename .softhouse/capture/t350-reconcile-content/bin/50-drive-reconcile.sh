#!/usr/bin/env bash
# T350 -- END TO END through `reconcile()`, not just through `branch_wip()`.
#
# `branch_wip` returning `name-only-refs` is only half a fix; the half that matters is
# what reconcile() WRITES. Before T330 that loop wrote `needs_retry` for every task it
# was handed and never compared the kind -- T319's caveat and T312's /CASE-VARIANT flag
# both fired correctly and changed nothing. So this drive runs the real entry point and
# reads the real tasks.json afterwards.
#
# AUTHORITY: `wrapper` mode is reached the only way a caller inside a `claude` can reach
# it honestly -- no `.softhouse/LOCK` on the fixture plus the long flag that names the
# out-of-band liveness probe. Nothing here is forced past a guard.
#
# Two runs, because the verdict depends on WHERE MAIN IS:
#   RUN 1  main = ac72956b (fire 20260828-140005's lock-take commit)
#          T339  in_progress, branch absent, rescue ref live  -> must DEMOTE
#          T351  in_progress, branch absent, content ref live -> must REFUSE
#   RUN 2  main = 280817a1f (the iter4 wave-2 dispatch commit)
#          T431  in_progress, branch AT that commit           -> must DEMOTE
set -u
MOD="${1:?usage: 50-drive-reconcile.sh <path-to-ready-tasks.py> <label>}"
LABEL="${2:?}"
FIX=/tmp/t350-fixture

run_case () {
  local mainsha="$1" json="$2" title="$3"
  git -C "$FIX" checkout --quiet --detach "$mainsha"
  git -C "$FIX" branch -f main "$mainsha" >/dev/null
  git -C "$FIX" update-ref refs/heads/softhouse/rescued-t339-base-20260828-080001 \
      7e8825b9f345d7f14399bc5fdb57c082b759ddcb
  git -C "$FIX" update-ref -d refs/heads/softhouse/T339-review-t270 2>/dev/null
  git -C "$FIX" update-ref -d refs/heads/softhouse/T351-old-name 2>/dev/null
  git -C "$FIX" update-ref refs/heads/softhouse/T431-t407-conditions \
      280817a1ffed480321ebf6318d5a363457f7ba72
  rm -f "$FIX/.softhouse/LOCK"
  printf '%s' "$json" > "$FIX/.softhouse/tasks.json"
  echo
  echo "=============================================================================="
  echo "$title   (fixture main $mainsha)"
  echo "=============================================================================="
  python3 "$MOD" --reconcile --fire T350-DRIVE --repo "$FIX" \
          --no-live-session-established-out-of-band
  echo "reconcile exit: $?"
  echo "--- tasks.json AFTER, statuses only ---"
  python3 - "$FIX" <<'PY'
import json, sys
d = json.load(open(sys.argv[1] + "/.softhouse/tasks.json"))
for t in d["tasks"]:
    print("  %-8s -> %-12s note[:150]: %s"
          % (t["id"], t.get("status"), (t.get("note") or "")[:150]))
PY
}

echo "=============================================================================="
echo "T350 RECONCILE DRIVE -- $LABEL"
echo "module under test: $MOD"
echo "module sha256:     $(shasum -a 256 "$MOD" | cut -d' ' -f1)"
echo "=============================================================================="

run_case ac72956b9a7503356eaca8ffb88fb5c5a911870e \
'{"tasks":[
 {"id":"T339","status":"in_progress","branch":"softhouse/T339-review-t270","model":"opus","target":"review","title":"INDEPENDENT review of T270","dependencies":[]},
 {"id":"T351","status":"in_progress","branch":"softhouse/T351-old-name","model":"opus","target":"code","title":"CONTROL -- live ref carries real t351 content","dependencies":[]}
]}' \
"RUN 1 -- T339 (name-only rescue ref) MUST DEMOTE; T351 (content ref) MUST REFUSE"

run_case 280817a1ffed480321ebf6318d5a363457f7ba72 \
'{"tasks":[
 {"id":"T431","status":"in_progress","branch":"softhouse/T431-t407-conditions","model":"opus","target":"code","title":"C-T407-1 (MAJOR)","dependencies":[]}
]}' \
"RUN 2 -- T431 branch AT the dispatch commit MUST DEMOTE (was: merged/REFUSE)"
