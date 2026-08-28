#!/bin/zsh
# T349 -- put the scratch repo back into the RED state (dispatch record committed, unpushed)
# and run the unit drives against it.
set -u
ROOT=${T349_ROOT:-/tmp/t349-scratch}
CAP=${T349_CAP:?capture dir}
cd "$ROOT/repo"
git checkout -q main
print -r -- '{"tasks":[{"id":"T900","status":"pending","branch":null},{"id":"T349","status":"pending","branch":null}]}' > .softhouse/tasks.json
git add -A >/dev/null 2>&1; git commit -q -m "unit-drive: origin state = T900/T349 pending"
git push -q origin main
print -r -- '{"tasks":[{"id":"T900","status":"in_progress","branch":"softhouse/T900-probe"},{"id":"T349","status":"in_progress","branch":"softhouse/T349-x"}]}' > .softhouse/tasks.json
git add -A >/dev/null 2>&1; git commit -q -m "unit-drive: local dispatch record, NOT pushed"
print -r -- "origin: $(git show origin/main:.softhouse/tasks.json)"
print -r -- ""
/usr/bin/python3 "$CAP/probe/unit-drive-candidate.py" "$CAP/probe/spawn-gate-candidate.py" "$ROOT/repo"
