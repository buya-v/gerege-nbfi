#!/bin/zsh
# T309 — DRIVE THE SECOND DEFECT: a LIVE driver clearing ANOTHER fire's corpses.
#
# THE DEFECT. `ready-tasks.py`'s caller_is_lock_holder() refused any process whose
# ancestry contained `claude`, reasoning that "a driver or worker must not reconcile its
# own siblings". Sound for LIVE siblings, WRONG for corpses — and the guard had no notion
# of fire identity, so it could not tell the 20260823-140001 driver clearing
# 20260823-080004's dead dispatches from a live driver demoting its own running workers.
# The 140001 driver therefore open-coded the demotion by hand, which is exactly the
# hand-repair the tool exists to replace.
#
# THIS SCRIPT MUST BE RUN FROM INSIDE A `claude` SESSION. That is not a limitation, it is
# the whole subject: the mode is DERIVED from /bin/ps ancestry and cannot be asserted, so
# the only way to exercise `in_session` is to actually be in one. It checks its own
# ancestry first and REFUSES to report anything if it is not.
#
# The LOCK it writes names $$ — this script's own pid, which is by construction an
# ancestor of the python it then invokes. That satisfies the ancestry leg honestly rather
# than by weakening it.
set -uo pipefail
HERE="${0:A:h}"
SRC="${SRC:-$(cd "$HERE/../../.." && pwd)}"
WORK="${TMPDIR:-/tmp}/t309-insession.$$"
mkdir -p "$WORK" || exit 1
trap 'rm -rf "$WORK"' EXIT
PASS=0; FAIL=0

# --------------------------------------------------------- am I actually in-session? ---
ANC=$(/bin/ps -Ao pid=,ppid=,command=)
me=$$; chain=""
for i in {1..64}; do
  line=$(print -r -- "$ANC" | /usr/bin/awk -v p="$me" '$1==p {print; exit}')
  [[ -z "$line" ]] && break
  pp=$(print -r -- "$line" | /usr/bin/awk '{print $2}')
  cmd=$(print -r -- "$ANC" | /usr/bin/awk -v p="$pp" '$1==p {$1="";$2="";print; exit}')
  [[ -z "$cmd" || "$pp" == 0 || "$pp" == 1 ]] && break
  chain="$chain\n    $pp $(print -r -- "$cmd" | cut -c1-70)"
  me=$pp
done
print -r -- "ancestry of this script (pid $$):"
print -r -- "$chain"
if ! print -r -- "$chain" | grep -q "claude"; then
  print -r -- "REFUSING TO REPORT: no \`claude\` in this script's ancestry, so it cannot"
  print -r -- "exercise \`in_session\` mode at all. Run it from inside a claude session."
  exit 2
fi
print -r -- "-> a \`claude\` IS in the chain: \`in_session\` mode is genuinely under test."
print -r -- ""

LOCK_FIRE="20260823-140001"
DEAD_FIRE="20260823-080004"

build() {                       # build <rev>
  local rev=$1
  rm -rf "$WORK/repo"
  mkdir -p "$WORK/repo/.softhouse/bin"
  git init -q "$WORK/repo"
  git -C "$WORK/repo" checkout -q -b main 2>/dev/null
  git -C "$WORK/repo" config user.email t309@example.invalid
  git -C "$WORK/repo" config user.name T309
  git -C "$SRC" show "$rev:.softhouse/bin/ready-tasks.py" > "$WORK/repo/.softhouse/bin/ready-tasks.py" || exit 1
  /usr/bin/python3 - "$WORK/repo" "$LOCK_FIRE" "$DEAD_FIRE" <<'PY'
import json, sys
repo, lock_fire, dead_fire = sys.argv[1], sys.argv[2], sys.argv[3]
t = lambda i, f, **kw: dict({"id": i, "title": i, "status": "in_progress",
                             "branch": "softhouse/%s-b" % i, "dependencies": []},
                            **({"fire": f} if f is not None else {}), **kw)
tasks = [
    t("T801", dead_fire),      # a corpse from a DEAD fire        -> DEMOTE
    t("T802", lock_fire),      # a LIVE sibling of the lock holder -> WITHHOLD
    t("T803", None),           # no `fire` key at all              -> WITHHOLD
    t("T804", None),
    t("T805", ""),             # empty string                      -> WITHHOLD
    t("T806", dead_fire),      # a second corpse                   -> DEMOTE
]
tasks[3]["fire"] = None        # explicit JSON null                -> WITHHOLD
json.dump({"tasks": tasks}, open(repo + "/.softhouse/tasks.json", "w"),
          indent=2, ensure_ascii=False)
PY
  git -C "$WORK/repo" add -A >/dev/null 2>&1
  git -C "$WORK/repo" commit -q -m base
}

writelock() {                   # writelock <fire-or-empty>
  local f=$1
  if [[ -n "$f" ]]; then
    print -r -- "{\"holder\":\"local-launchd\",\"host\":\"$(hostname -s)\",\"pid\":$$,\"fire\":\"$f\"}" > "$WORK/repo/.softhouse/LOCK"
  else
    print -r -- "{\"holder\":\"local-launchd\",\"host\":\"$(hostname -s)\",\"pid\":$$}" > "$WORK/repo/.softhouse/LOCK"
  fi
}

status_of() { /usr/bin/python3 -c "
import json,sys
d=json.load(open('$WORK/repo/.softhouse/tasks.json'))
print(' '.join('%s=%s' % (t['id'], t['status']) for t in d['tasks']))
"; }

check() {                       # check <label> <expected-rc> <expected-statuses>
  local label=$1 wrc=$2 wst=$3
  local out rc st
  out=$(/usr/bin/python3 "$WORK/repo/.softhouse/bin/ready-tasks.py" --reconcile \
          --fire "$LOCK_FIRE" --repo "$WORK/repo" 2>&1)
  rc=$?
  st=$(status_of)
  print -r -- "--- $label"
  print -r -- "$out" | /usr/bin/sed 's/^/      /'
  print -r -- "    rc=$rc  (wanted $wrc)"
  print -r -- "    statuses: $st"
  print -r -- "    wanted  : $wst"
  if [[ "$rc" == "$wrc" && "$st" == "$wst" ]]; then
    print -r -- "    >>> PASS"; (( PASS++ ))
  else
    print -r -- "    >>> FAIL"; (( FAIL++ ))
  fi
  print -r -- ""
}

ALL_IP="T801=in_progress T802=in_progress T803=in_progress T804=in_progress T805=in_progress T806=in_progress"

print -r -- "=============================================================================="
print -r -- "SCENARIO 1 — PRE-FIX bytes (main). A live driver cannot clear a dead fire's"
print -r -- "             dispatches at all: the tool refuses on ancestry alone."
print -r -- "=============================================================================="
build main
writelock "$LOCK_FIRE"
check "pre-fix, lock carries a fire id" 4 "$ALL_IP"

print -r -- "=============================================================================="
print -r -- "SCENARIO 2 — POST-FIX bytes (HEAD). The SAME call must now demote the two"
print -r -- "             corpses of fire $DEAD_FIRE and WITHHOLD everything else."
print -r -- "=============================================================================="
build HEAD
writelock "$LOCK_FIRE"
check "in_session, mixed ownership" 0 \
  "T801=needs_retry T802=in_progress T803=in_progress T804=in_progress T805=in_progress T806=needs_retry"

print -r -- "=============================================================================="
print -r -- "SCENARIO 3 — POST-FIX bytes, but every in_progress task belongs to the LIVE"
print -r -- "             fire. Nothing may be touched. This is the case whose failure"
print -r -- "             DESTROYS WORK, so it is graded on the file, not on the rc alone."
print -r -- "=============================================================================="
build HEAD
/usr/bin/python3 -c "
import json
p='$WORK/repo/.softhouse/tasks.json'
d=json.load(open(p))
for t in d['tasks']: t['fire']='$LOCK_FIRE'
json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)
"
writelock "$LOCK_FIRE"
check "in_session, every task is a LIVE sibling" 4 "$ALL_IP"

print -r -- "=============================================================================="
print -r -- "SCENARIO 4 — POST-FIX bytes, LOCK carries NO fire id. 'Is this mine?' cannot"
print -r -- "             be decided, so nothing may be touched (fail-closed)."
print -r -- "=============================================================================="
build HEAD
writelock ""
check "in_session, lock has no fire id" 4 "$ALL_IP"

print -r -- "=============================================================================="
print -r -- "SCENARIO 5 — POST-FIX bytes, NO LOCK ON DISK. No live fire exists to protect,"
print -r -- "             so this is wrapper authority and every dispatch is a corpse."
print -r -- "=============================================================================="
build HEAD
rm -f "$WORK/repo/.softhouse/LOCK"
check "no lock at all" 0 \
  "T801=needs_retry T802=needs_retry T803=needs_retry T804=needs_retry T805=needs_retry T806=needs_retry"

print -r -- "=============================================================================="
print -r -- "IN-SESSION MATRIX: $PASS passed, $FAIL failed"
(( FAIL == 0 )) || exit 1
print -r -- "DONE"
