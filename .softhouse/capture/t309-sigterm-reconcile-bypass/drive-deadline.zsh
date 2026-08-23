#!/bin/zsh
# T309 — THE INNER BOUND, DRIVEN. `--deadline-secs` must degrade WIP EVIDENCE to
# UNVERIFIED while STILL PERFORMING THE DEMOTION.
#
# The two bounds fail in different directions on purpose and neither direction is
# guessable from the code alone:
#   * OUTER (reconcile_bounded, fire-program.sh) kills the process. Nothing is written.
#     Exercised by drive-sigterm.zsh --wedge.
#   * INNER (--deadline-secs, this file) clamps each subprocess and, when the budget is
#     gone, answers rc=None. branch_wip renders that as UNVERIFIED — but the task is
#     STILL demoted, because a dead dispatch is dead whether or not `git` answered. The
#     status is the repair; the branch sha is colour.
# If the inner bound suppressed the demotion it would be the outer bound with extra
# steps, and the in_progress lie would survive every slow machine.
set -uo pipefail
HERE="${0:A:h}"
SRC="${SRC:-$(cd "$HERE/../../.." && pwd)}"
WORK="${TMPDIR:-/tmp}/t309-deadline.$$"
mkdir -p "$WORK/repo/.softhouse/bin" || exit 1
trap 'rm -rf "$WORK"' EXIT
PASS=0; FAIL=0

git init -q "$WORK/repo"
git -C "$WORK/repo" checkout -q -b main 2>/dev/null
git -C "$WORK/repo" config user.email t309@example.invalid
git -C "$WORK/repo" config user.name T309
git -C "$SRC" show "HEAD:.softhouse/bin/ready-tasks.py" > "$WORK/repo/.softhouse/bin/ready-tasks.py" || exit 1

plant() {
  /usr/bin/python3 - "$WORK/repo" <<'PY'
import json, sys
repo = sys.argv[1]
tasks = [{"id": "T8%02d" % i, "title": "t", "status": "in_progress",
          "branch": "softhouse/T8%02d-b" % i, "fire": "20260823-080004",
          "dependencies": []} for i in range(8)]
json.dump({"tasks": tasks}, open(repo + "/.softhouse/tasks.json", "w"),
          indent=2, ensure_ascii=False)
PY
  rm -f "$WORK/repo/.softhouse/LOCK"     # no lock => wrapper authority
}

run() {                                   # run <deadline-or-empty>
  local d=$1
  local -a a; a=(--reconcile --fire 20260823-140001 --repo "$WORK/repo")
  [[ -n "$d" ]] && a+=(--deadline-secs "$d")
  /usr/bin/python3 "$WORK/repo/.softhouse/bin/ready-tasks.py" "${a[@]}" 2>&1
}

grade() {                                 # grade <label> <want-demoted> <want-unverified>
  local label=$1 wd=$2 wu=$3
  local demoted unverified
  demoted=$(/usr/bin/python3 -c "
import json
d=json.load(open('$WORK/repo/.softhouse/tasks.json'))
print(sum(1 for t in d['tasks'] if t['status']=='needs_retry'))
")
  unverified=$(print -r -- "$OUT" | grep -c "WIP=unverified")
  print -r -- "    demoted=$demoted (want $wd)   WIP=unverified lines=$unverified (want $wu)"
  if [[ "$demoted" == "$wd" && "$unverified" == "$wu" ]]; then
    print -r -- "    >>> PASS"; (( PASS++ ))
  else
    print -r -- "    >>> FAIL"; (( FAIL++ ))
    print -r -- "$OUT" | sed 's/^/      /'
  fi
  print -r -- ""
}

print -r -- "=== A. no deadline — full evidence, all 8 demoted ==="
plant
OUT=$(run "")
print -r -- "$OUT" | grep -E "budget:|WIP=|RESULT:" | sed 's/^/      /'
grade "no deadline" 8 0

print -r -- "=== B. a deadline so small the FIRST git call cannot fit — evidence must go"
print -r -- "       UNVERIFIED and all 8 must STILL be demoted ==="
plant
OUT=$(run 0.001)
print -r -- "$OUT" | grep -E "budget:|WIP=|NOTE:|RESULT:" | sed 's/^/      /'
grade "exhausted deadline" 8 8

print -r -- "=== C. --deadline-secs rejects junk rather than substituting a default ==="
plant
OUT=$(run "banana"); RC=$?
print -r -- "      $OUT"
if [[ "$RC" == 64 ]]; then print -r -- "    >>> PASS (rc=64)"; (( PASS++ )); else print -r -- "    >>> FAIL (rc=$RC, wanted 64)"; (( FAIL++ )); fi
print -r -- ""

print -r -- "DEADLINE MATRIX: $PASS passed, $FAIL failed"
(( FAIL == 0 )) || exit 1
print -r -- "DONE"
