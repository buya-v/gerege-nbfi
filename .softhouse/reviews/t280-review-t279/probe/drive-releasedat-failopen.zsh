#!/bin/zsh
# T280 F-A — END TO END: a LIVE holder's lock is declared FREE because `"released_at": null`
# is the LAST key in the JSON object.
#
# `lock_released_at()` extracts the value with  ${${body#*\"released_at\":}%%,*}  — up to the
# first COMMA. When `released_at` is the last key there is no trailing comma, so the match
# runs to the end of the object and the value carries the closing brace. The cleanup strips
# space/tab/CR/LF/quote but NOT `}`, so the value is the 5-character string `null}`, which
# is non-empty, so arm 1 fires: FREE-released.
#
# This is the P-85 shape: a held, live lock read as free.
set -uo pipefail
W="$1"
T=$(mktemp -d /tmp/t280-relnull.XXXXXX)
export GIT_CONFIG_NOSYSTEM=1 HOME="$T/home"; mkdir -p "$HOME"
printf '[user]\n\tname = T280\n\temail = t280@local\n[init]\n\tdefaultBranch = main\n' > "$HOME/.gitconfig"
git init -q --bare "$T/origin.git"
git init -q "$T/repo"; cd "$T/repo"
mkdir -p .softhouse; echo x > .softhouse/x
git add -A >/dev/null; git commit -qm seed
git remote add origin "$T/origin.git"; git push -q origin main

HOSTS=$(hostname -s)
sleep 900 & LIVEPID=$!            # a REAL, RUNNING process that we own
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

emit() {   # $1 = lock body
  print -r -- "$1" > "$T/repo/.softhouse/LOCK"
  GEREGE_NBFI_REPO="$T/repo" zsh "$W" --lock-signals 2>&1 | grep -v '^repo=' | sed 's/^/    /'
}

print -r -- "holder pid $LIVEPID  running: $(kill -0 $LIVEPID 2>/dev/null && print YES || print no)  uid: $(id -u)"
print -r -- ""
print -r -- "--- 1. HELD, live holder, released_at ABSENT (what the wrapper itself writes)"
emit '{
  "holder": "local-launchd",
  "host": "'"$HOSTS"'",
  "pid": '"$LIVEPID"',
  "started_at": "'"$NOW"'"
}'
print -r -- ""
print -r -- "--- 2. HELD, live holder, released_at null but NOT the last key"
emit '{
  "holder": "local-launchd",
  "host": "'"$HOSTS"'",
  "pid": '"$LIVEPID"',
  "released_at": null,
  "started_at": "'"$NOW"'"
}'
print -r -- ""
print -r -- "--- 3. HELD, live holder, released_at null AS THE LAST KEY   <-- THE DEFECT"
emit '{
  "holder": "local-launchd",
  "host": "'"$HOSTS"'",
  "pid": '"$LIVEPID"',
  "started_at": "'"$NOW"'",
  "released_at": null
}'
print -r -- ""
print -r -- "--- 4. same, written by python json.dumps(indent=2) with released_at added last"
python3 -c "
import json,sys
d={'holder':'local-launchd','host':'$HOSTS','pid':$LIVEPID,'started_at':'$NOW'}
d['released_at']=None
open('$T/repo/.softhouse/LOCK','w').write(json.dumps(d,indent=2))
"
GEREGE_NBFI_REPO="$T/repo" zsh "$W" --lock-signals 2>&1 | grep -v '^repo=' | sed 's/^/    /'
print -r -- "    (body: $(tr -d '\n' < "$T/repo/.softhouse/LOCK"))"
print -r -- ""
print -r -- "--- 5. compact json.dumps (no indent), released_at last"
python3 -c "
import json
d={'holder':'local-launchd','host':'$HOSTS','pid':$LIVEPID,'started_at':'$NOW','released_at':None}
open('$T/repo/.softhouse/LOCK','w').write(json.dumps(d))
"
GEREGE_NBFI_REPO="$T/repo" zsh "$W" --lock-signals 2>&1 | grep -v '^repo=' | sed 's/^/    /'
print -r -- "    (body: $(cat "$T/repo/.softhouse/LOCK"))"
print -r -- ""
print -r -- "--- 6. ARM 3 CEILING end to end: lock 105 h old, tip 2.99 h old, holder ALIVE"
STARTED_105=$(date -u -v-105H +%Y-%m-%dT%H:%M:%SZ)
print -r -- '{
  "host": "'"$HOSTS"'",
  "pid": '"$LIVEPID"',
  "started_at": "'"$STARTED_105"'"
}' > "$T/repo/.softhouse/LOCK"
TIP=$(date -u -v-179M +"%Y-%m-%dT%H:%M:%S+0000")
git add -f .softhouse/LOCK >/dev/null
GIT_AUTHOR_DATE="$TIP" GIT_COMMITTER_DATE="$TIP" git commit -qm "third party publishes" >/dev/null
git push -q origin main
GEREGE_NBFI_REPO="$T/repo" zsh "$W" --lock-signals 2>&1 | grep -v '^repo=' | sed 's/^/    /'
print -r -- ""
print -r -- "--- 7. ARM 5 takes the lock from a DEMONSTRABLY LIVE holder on THIS host"
STARTED_8=$(date -u -v-8H +%Y-%m-%dT%H:%M:%SZ)
print -r -- '{
  "host": "'"$HOSTS"'",
  "pid": '"$LIVEPID"',
  "started_at": "'"$STARTED_8"'"
}' > "$T/repo/.softhouse/LOCK"
TIP12=$(date -u -v-12H +"%Y-%m-%dT%H:%M:%S+0000")
git add -f .softhouse/LOCK >/dev/null
GIT_AUTHOR_DATE="$TIP12" GIT_COMMITTER_DATE="$TIP12" git commit -qm "nothing published for 12h" >/dev/null
git push -q origin main
GEREGE_NBFI_REPO="$T/repo" zsh "$W" --lock-signals 2>&1 | grep -v '^repo=' | sed 's/^/    /'
print -r -- "    holder pid $LIVEPID still running: $(kill -0 $LIVEPID 2>/dev/null && print YES || print no)"
kill $LIVEPID 2>/dev/null
print -r -- ""
print -r -- "scratch: $T"
