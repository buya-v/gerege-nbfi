#!/bin/zsh
# T288 — build a scratch repo that reproduces the 2026-08-22 exit-protocol failure,
# so the REAL fire-program.sh can be driven against it end to end.
#
# The failure being reproduced: a fire ends, its workers are dead, and tasks.json still
# says `in_progress`. Three shapes of dead dispatch are planted, because they must
# produce three DIFFERENT notes:
#   T900  branch exists, worker left UNCOMMITTED work in a live worktree
#         -> the sweep rescues it, and the task note must NAME the rescue branch
#   T901  branch exists with a real commit ahead of main (worker committed, then died)
#         -> note must carry the commit count and head sha, not "nothing was found"
#   T902  "branch": null — the isolation-violation shape ready-tasks.py already flags
#         -> note must say no branch was recorded and nothing could be looked for
#   T903  status `pending` — the CONTROL. Nothing may touch it.
#
# Nothing here touches the real repo. Usage: build-fixture.sh [dir]
set -uo pipefail
BASE="${1:-/tmp/t288-drive}"
rm -rf "$BASE"
mkdir -p "$BASE/logs" "$BASE/fake"

# --- a bare origin, so the wrapper's pulls and pushes are real -------------------
git init -q --bare "$BASE/origin.git"

REPO="$BASE/repo"
mkdir -p "$REPO/.softhouse"
# T304 (FU-T284-3): FAIL CLOSED ON A DEAD `cd`. $BASE comes from $1, so $REPO may not
# exist; there is no `set -e` here, and everything below this line writes with plain `>`
# into `.softhouse/`. DRIVEN, not reasoned: with $1 uncreatable this script re-inited the
# surrounding repo, rewrote `git config user.name/email`, replaced tasks.json, RESUME.md
# and program.json, `git add -A && git commit`ed the replacement ONTO THE CHECKED-OUT
# BRANCH, then `git checkout -b`'d away -- so `git status --porcelain` came back EMPTY and
# the clobber survived only in the ref. Transcript:
# .softhouse/capture/t304-evidence-destruction/evidence/100-dead-cd-red-drive.txt
cd "$REPO" || { echo "build-fixture: cannot cd to $REPO -- refusing rather than writing .softhouse/ in \$PWD" >&2; exit 2; }
git init -q -b main .
git config user.name Fixture
git config user.email fixture@example.invalid

cat > .softhouse/tasks.json <<'JSON'
{
  "run_id": "t288-fixture",
  "status": "active",
  "tasks": [
    {
      "id": "T900",
      "status": "in_progress",
      "executor": "agent",
      "model": "opus",
      "target": "code",
      "title": "worker died with uncommitted work in its worktree",
      "branch": "softhouse/t900-uncommitted",
      "dependencies": []
    },
    {
      "id": "T901",
      "status": "in_progress",
      "executor": "agent",
      "model": "opus",
      "target": "code",
      "title": "worker committed to its branch and then died",
      "branch": "softhouse/t901-committed",
      "dependencies": []
    },
    {
      "id": "T902",
      "status": "in_progress",
      "executor": "agent",
      "model": "sonnet",
      "target": "code",
      "title": "dispatched with no branch recorded at all",
      "branch": null,
      "dependencies": []
    },
    {
      "id": "T903",
      "status": "pending",
      "executor": "agent",
      "model": "opus",
      "target": "code",
      "title": "CONTROL — never dispatched, must be left exactly as it is",
      "branch": "softhouse/t903-untouched",
      "dependencies": []
    }
  ]
}
JSON

cat > .softhouse/RESUME.md <<'MD'
# RESUME — t288 fixture

Pause reason: this manifest is deliberately stale. It was written before the fire ran.

| task | status |
|------|--------|
| T900 | in_progress |
| T901 | in_progress |
| T902 | in_progress |
MD

print -r -- '{"status":"active","contexts":[]}' > .softhouse/program.json
git add -A
git commit -q -m "fixture: repo with three dead dispatches still marked in_progress"
git remote add origin "$BASE/origin.git"
git push -q -u origin main

# T901: a branch with a real commit ahead of main — WIP that landed but was never merged
git checkout -q -b softhouse/t901-committed
print -r -- "partial work from a worker that committed and then died" > wip-t901.txt
git add -A
git commit -q -m "T901 WIP"
git checkout -q main

# T900: a live-looking worktree on the task branch with UNCOMMITTED work in it
git branch -q softhouse/t900-uncommitted main
git worktree add -q "$BASE/agent-fixture900" softhouse/t900-uncommitted
print -r -- "uncommitted deliverable the worker never got to commit" > "$BASE/agent-fixture900/wip-t900.txt"

# a fake `claude` for the wrapper to invoke: emits a plausible stream-json result and
# exits 0 immediately, so the driver is DEAD by the time the exit guard runs — which is
# precisely the state the guard is written for.
cat > "$BASE/fake/claude" <<'SH'
#!/bin/zsh
print -r -- '{"type":"system","subtype":"init","session_id":"fixture"}'
print -r -- '{"type":"assistant","message":{"model":"claude-opus-5","content":[]}}'
print -r -- '{"type":"result","subtype":"success","is_error":false,"num_turns":1,"result":"fixture driver did nothing"}'
exit 0
SH
chmod +x "$BASE/fake/claude"

# a second fake: the 2026-08-22 23:00 fire, which was refused by the five-hour quota 20
# seconds in and never got a turn. The three lines below are the SHAPES taken verbatim
# from that fire's own stream (~/Library/Logs/gerege-nbfi/fire-20260822-230001.jsonl):
# the rejection is nested under .rate_limit_info, and the only assistant event carries
# model "<synthetic>" — the harness speaking, not the model.
cat > "$BASE/fake/claude-quota" <<'SH'
#!/bin/zsh
print -r -- '{"type":"system","subtype":"init","session_id":"fixture-quota"}'
print -r -- '{"type":"rate_limit_event","rate_limit_info":{"status":"rejected","resetsAt":1787414400,"rateLimitType":"five_hour","overageStatus":"rejected"}}'
print -r -- '{"type":"assistant","message":{"model":"<synthetic>","role":"assistant","content":[]}}'
print -r -- '{"type":"result","subtype":"success","is_error":true,"num_turns":1,"result":"You'"'"'ve hit your session limit · resets 12am (Asia/Ulaanbaatar)"}'
exit 1
SH
chmod +x "$BASE/fake/claude-quota"

print -r -- "fixture built at $BASE"
git -C "$REPO" log --oneline -1
git -C "$REPO" worktree list
