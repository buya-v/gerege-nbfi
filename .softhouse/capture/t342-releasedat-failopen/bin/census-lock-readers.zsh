#!/bin/zsh
# T342 — CENSUS OF EVERY LOCK-FIELD READER IN fire-program.sh THAT DOES JSON BY STRING SURGERY.
#
# T280's F-A named one reader. The task asks whether it is the only one with that shape.
# There are THREE functions and FOUR fields:
#
#   lock_pid_state()    "host"        ${${body#*\"host\": \"}%%\"*}      cut at first QUOTE
#   lock_pid_state()    "pid"         ${${body#*\"pid\": }%%,*}          cut at first COMMA
#   lock_released_at()  "released_at" ${${body#*\"released_at\":}%%,*}   cut at first COMMA
#   lock_started_age()  "started_at"  ${${body#*\"started_at\": \"}%%\"*} cut at first QUOTE
#
# Each is driven through the SHIPPED FILE (`--lock-signals`), not a copy, against the four
# adversarial shapes the task names: KEY LAST, VALUE CONTAINS A COMMA, KEY TWICE, and NOT
# VALID JSON AT ALL. Plus one the shipped writer makes plausible: COMPACT separators.
#
# What matters in the output is the VERDICT column, and specifically whether an adversarial
# body moves a lock held by a LIVE process owned by this very user off HELD.
#
# Usage: zsh census-lock-readers.zsh <path-to-fire-program.sh>
set -uo pipefail
W="${1:?usage: census-lock-readers.zsh <fire-program.sh>}"
W="${W:A}"
T=$(mktemp -d /tmp/t342-census.XXXXXX)
export GIT_CONFIG_NOSYSTEM=1 HOME="$T/home"; mkdir -p "$HOME"
printf '[user]\n\tname = T342\n\temail = t342@local\n[init]\n\tdefaultBranch = main\n' > "$HOME/.gitconfig"
git init -q --bare "$T/origin.git"
git init -q "$T/repo"; cd "$T/repo"
mkdir -p .softhouse; echo x > .softhouse/x
git add -A >/dev/null; git commit -qm seed
git remote add origin "$T/origin.git"; git push -q origin main

H=$(hostname -s)
sleep 900 & LIVE=$!                      # a REAL running process owned by this uid
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)       # young lock: no ceiling, no staleness

print -r -- "wrapper under test : $W"
print -r -- "live holder pid    : $LIVE (running: $(kill -0 $LIVE 2>/dev/null && print YES || print no)), uid $(id -u), host $H"
print -r -- "every body below names THAT pid on THIS host with a started_at of NOW."
print -r -- "THE ONLY CORRECT VERDICT FOR EVERY ROW IS A *HELD* ONE. Anything else is a fail-open."
print -r -- ""

case_() {  # $1 = label, $2 = body
  local label="$1" body="$2" line
  print -r -- "$body" > "$T/repo/.softhouse/LOCK"
  line=$(GEREGE_NBFI_REPO="$T/repo" zsh "$W" --lock-signals 2>&1 | grep -E '^(lock_present|verdict)=')
  local sig="${${(f)line}[1]}" ver="${${(f)line}[2]}"
  print -r -- "  ---- $label"
  print -r -- "       $sig"
  print -r -- "       $ver"
  case "$ver" in
    verdict=HELD*) print -r -- "       => held. safe." ;;
    *)             print -r -- "       => *** FAIL-OPEN: a lock held by live pid $LIVE was not held ***" ;;
  esac
  print -r -- ""
}

print -r -- "=============================================================="
print -r -- "GROUP 1 — released_at (lock_released_at, cut at first COMMA)"
print -r -- "=============================================================="

case_ "1a BASELINE: no released_at key at all (what the shipped writer emits)" \
'{
  "holder": "local-launchd",
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "started_at": "'"$NOW"'"
}'

case_ "1b KEY LAST: \"released_at\": null is the final key" \
'{
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "started_at": "'"$NOW"'",
  "released_at": null
}'

case_ "1c KEY NOT LAST: identical semantics, comma follows" \
'{
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "released_at": null,
  "started_at": "'"$NOW"'"
}'

case_ "1d KEY TWICE: first null, second a real timestamp (JSON says LAST wins => released)" \
'{
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "released_at": null,
  "released_at": "2026-08-28T09:00:00Z",
  "started_at": "'"$NOW"'"
}'

case_ "1e KEY TWICE: first a timestamp, second null (JSON says LAST wins => NOT released)" \
'{
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "released_at": "2026-08-28T09:00:00Z",
  "released_at": null,
  "started_at": "'"$NOW"'"
}'

case_ "1f NOT JSON AT ALL: the six-character substring in a prose note" \
'this file is not json. someone wrote "released_at": here by hand and stopped.
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "started_at": "'"$NOW"'"'

case_ "1g TRUNCATED WRITE: the writer died mid-object after released_at" \
'{
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "started_at": "'"$NOW"'",
  "released_at": "2026-08'

print -r -- "=============================================================="
print -r -- "GROUP 2 — pid (lock_pid_state, cut at first COMMA)"
print -r -- "=============================================================="

case_ "2a KEY LAST: \"pid\" is the final key, so no comma follows it" \
'{
  "host": "'"$H"'",
  "started_at": "'"$NOW"'",
  "pid": '"$LIVE"'
}'

case_ "2b KEY TWICE: first the live pid, second a pid that is certainly dead" \
'{
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "pid": 999999,
  "started_at": "'"$NOW"'"
}'

case_ "2c KEY TWICE REVERSED: first a dead pid, second the live one (JSON: last wins => alive)" \
'{
  "host": "'"$H"'",
  "pid": 999999,
  "pid": '"$LIVE"',
  "started_at": "'"$NOW"'"
}'

case_ "2d COMPACT SEPARATORS: json.dumps(separators=(\",\",\":\")) — no space after the colon" \
"$(python3 -c "
import json
print(json.dumps({'host':'$H','pid':$LIVE,'started_at':'$NOW'},separators=(',',':')))")"

print -r -- "=============================================================="
print -r -- "GROUP 3 — host (lock_pid_state, cut at first QUOTE)"
print -r -- "=============================================================="

case_ "3a VALUE CONTAINS A COMMA: a hostname with a comma in it" \
'{
  "host": "'"$H"', spare",
  "pid": '"$LIVE"',
  "started_at": "'"$NOW"'"
}'

case_ "3b KEY TWICE: first this host, second another (JSON: last wins => other_host)" \
'{
  "host": "'"$H"'",
  "host": "some-other-machine",
  "pid": '"$LIVE"',
  "started_at": "'"$NOW"'"
}'

print -r -- "=============================================================="
print -r -- "GROUP 4 — started_at (lock_started_age, cut at first QUOTE)"
print -r -- "=============================================================="

case_ "4a KEY LAST: \"started_at\" is the final key" \
'{
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "started_at": "'"$NOW"'"
}'

case_ "4b KEY TWICE: first a 105h-old stamp, second NOW (JSON: last wins => young)" \
'{
  "host": "'"$H"'",
  "pid": '"$LIVE"',
  "started_at": "'"$(date -u -v-105H +%Y-%m-%dT%H:%M:%SZ)"'",
  "started_at": "'"$NOW"'"
}'

case_ "4c NOT JSON AT ALL: garbage that still contains the started_at substring" \
'garbage garbage "started_at": "'"$NOW"'" garbage "host": "'"$H"'" "pid": '"$LIVE"','

case_ "4d COMPACT SEPARATORS: no space after the colon anywhere" \
"$(python3 -c "
import json
print(json.dumps({'host':'$H','pid':$LIVE,'started_at':'$NOW','released_at':None},separators=(',',':')))")"

kill $LIVE 2>/dev/null
print -r -- "scratch: $T"
