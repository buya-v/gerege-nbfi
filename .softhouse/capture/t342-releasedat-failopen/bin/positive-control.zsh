#!/bin/zsh
# T342 — POSITIVE CONTROL. The census proves the readers no longer say FREE when they
# should say HELD. That is only half the property: a reader that always says HELD would
# pass the census and would DISABLE arms 1 and 2 entirely, turning a fail-open into a
# fail-shut that strands the lock for 24 h. This drives the states where a takeover arm
# MUST fire, and fails if it does not.
set -uo pipefail
W="${1:?usage: positive-control.zsh <fire-program.sh>}"
W="${W:A}"
T=$(mktemp -d /tmp/t342-pos.XXXXXX)
export GIT_CONFIG_NOSYSTEM=1 HOME="$T/home"; mkdir -p "$HOME"
printf '[user]\n\tname = T342\n\temail = t342@local\n[init]\n\tdefaultBranch = main\n' > "$HOME/.gitconfig"
git init -q --bare "$T/origin.git"
git init -q "$T/repo"; cd "$T/repo"
mkdir -p .softhouse; echo x > .softhouse/x
git add -A >/dev/null; git commit -qm seed
git remote add origin "$T/origin.git"; git push -q origin main

H=$(hostname -s)
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# A pid that is certainly NOT running: take a short-lived child and let it exit.
sleep 0 & DEADPID=$!; wait $DEADPID 2>/dev/null
while kill -0 $DEADPID 2>/dev/null; do sleep 0.1; done

typeset -i fails=0
expect() {  # $1 label, $2 expected verdict, $3 body
  local label="$1" want="$2" body="$3" got
  print -r -- "$body" > "$T/repo/.softhouse/LOCK"
  got=$(GEREGE_NBFI_REPO="$T/repo" zsh "$W" --lock-signals 2>&1 | sed -n 's/^verdict=//p')
  if [[ "$got" == "$want" ]]; then
    printf '  OK    %-52s -> %s\n' "$label" "$got"
  else
    (( fails++ ))
    printf '  FAIL  %-52s -> %s  (wanted %s)\n' "$label" "$got" "$want"
  fi
}

print -r -- "wrapper under test: $W"
print -r -- "dead pid used: $DEADPID (running: $(kill -0 $DEADPID 2>/dev/null && print YES || print no))"
print -r -- ""
print -r -- "ARM 1 must still fire on a WELL-FORMED release:"

expect "released_at a real timestamp, key LAST" FREE-released \
'{
  "host": "'"$H"'",
  "pid": 1,
  "started_at": "'"$NOW"'",
  "released_at": "2026-08-28T09:00:00Z"
}'

expect "released_at a real timestamp, key in the MIDDLE" FREE-released \
'{
  "host": "'"$H"'",
  "released_at": "2026-08-28T09:00:00Z",
  "pid": 1,
  "started_at": "'"$NOW"'"
}'

expect "released_at a real timestamp, COMPACT separators" FREE-released \
"$(python3 -c "
import json
print(json.dumps({'host':'$H','pid':1,'started_at':'$NOW','released_at':'2026-08-28T09:00:00Z'},separators=(',',':')))")"

print -r -- ""
print -r -- "ARM 2 must still fire on a DEAD holder on this host:"

expect "dead pid on this host, pid key in the middle" TAKE-dead-pid \
'{
  "host": "'"$H"'",
  "pid": '"$DEADPID"',
  "started_at": "'"$NOW"'"
}'

expect "dead pid on this host, pid key LAST (was pid_state=absent before T342)" TAKE-dead-pid \
'{
  "host": "'"$H"'",
  "started_at": "'"$NOW"'",
  "pid": '"$DEADPID"'
}'

expect "dead pid on this host, COMPACT separators (was absent before T342)" TAKE-dead-pid \
"$(python3 -c "
import json
print(json.dumps({'host':'$H','pid':$DEADPID,'started_at':'$NOW'},separators=(',',':')))")"

print -r -- ""
print -r -- "ARM 0 must still fire when there is no lock at all:"
rm -f "$T/repo/.softhouse/LOCK"
got=$(GEREGE_NBFI_REPO="$T/repo" zsh "$W" --lock-signals 2>&1 | sed -n 's/^verdict=//p')
if [[ "$got" == FREE-no-lock ]]; then printf '  OK    %-52s -> %s\n' "no LOCK file" "$got"
else (( fails++ )); printf '  FAIL  %-52s -> %s  (wanted FREE-no-lock)\n' "no LOCK file" "$got"; fi

print -r -- ""
if (( fails )); then
  print -r -- "RESULT: FAIL — $fails positive control(s) regressed. The fix is fail-SHUT, not fail-closed."
  exit 1
fi
print -r -- "RESULT: PASS — every takeover arm still fires on the input it is written for."
print -r -- "scratch: $T"
