#!/bin/zsh
# T280 — drive the SHIPPED wrapper's signal readers over LOCK BODIES the 192-state space
# does not name: unparseable JSON, released_at as the LAST key, pid null/0/absent,
# started_at in the FUTURE, and a repo with no origin/main at all.
set -uo pipefail
W="$1"
T=$(mktemp -d /tmp/t280-lock.XXXXXX)
export GIT_CONFIG_NOSYSTEM=1 HOME="$T/home"; mkdir -p "$HOME"
printf '[user]\n\tname = T280\n\temail = t280@local\n[init]\n\tdefaultBranch = main\n' > "$HOME/.gitconfig"
git init -q --bare "$T/origin.git"
git init -q "$T/repo"; cd "$T/repo"
mkdir -p .softhouse; echo x > .softhouse/x; git add -A >/dev/null; git commit -qm seed
git remote add origin "$T/origin.git"; git push -q origin main

HOSTS=$(hostname -s)
NOWISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OLDISO=$(date -u -v-100H +%Y-%m-%dT%H:%M:%SZ)
FUTISO=$(date -u -v+48H +%Y-%m-%dT%H:%M:%SZ)

probe() {
  local name="$1" body="$2"
  print -r -- "$body" > "$T/repo/.softhouse/LOCK"
  print -r -- "--- $name"
  GEREGE_NBFI_REPO="$T/repo" zsh "$W" --lock-signals 2>&1 | sed 's/^/    /' | grep -v '^    repo='
  print -r -- ""
}

probe "A. baseline: wrapper-shaped live lock (pid 1, other proc, this host)" \
'{
  "holder": "local-launchd",
  "host": "'"$HOSTS"'",
  "pid": 1,
  "started_at": "'"$NOWISO"'"
}'

probe "B. released_at is the LAST key, value null  <-- no trailing comma" \
'{
  "host": "'"$HOSTS"'",
  "pid": 1,
  "started_at": "'"$NOWISO"'",
  "released_at": null
}'

probe "C. released_at NOT last, value null (trailing comma present)" \
'{
  "host": "'"$HOSTS"'",
  "released_at": null,
  "pid": 1,
  "started_at": "'"$NOWISO"'"
}'

probe "D. released_at last key, genuinely RELEASED" \
'{
  "host": "'"$HOSTS"'",
  "pid": 1,
  "started_at": "'"$NOWISO"'",
  "released_at": "2026-08-28T09:00:00Z"
}'

probe "E. lock body is NOT JSON at all" \
'this file got clobbered by a merge conflict
<<<<<<< HEAD
whatever
'

probe "F. pid is null (last key), live holder on this host" \
'{
  "host": "'"$HOSTS"'",
  "started_at": "'"$NOWISO"'",
  "pid": null
}'

probe "G. pid 0 (T265 F-4)" \
'{
  "host": "'"$HOSTS"'",
  "pid": 0,
  "started_at": "'"$NOWISO"'"
}'

probe "H. started_at in the FUTURE (+48h) -- negative age" \
'{
  "host": "'"$HOSTS"'",
  "pid": 1,
  "started_at": "'"$FUTISO"'"
}'

probe "I. started_at 100h old, pid 1 alive, tip fresh -> should be arm 3 CEILING" \
'{
  "host": "'"$HOSTS"'",
  "pid": 1,
  "started_at": "'"$OLDISO"'"
}'

print -r -- "=== direct lock_decide probes (no repo needed) ==="
probe_d() {
  local desc="$1"; shift
  local v
  v=$(zsh "$W" --lock-decide "$@")
  printf '  %-64s -> %s\n' "$desc" "$v"
}
probe_d "negative started_age, fresh tip"                     1 "" -3600 3600 absent
probe_d "fresh started_age, NEGATIVE tip age (clock skew)"    1 "" 3600 -3600 absent
probe_d "started 25h + NEGATIVE tip"                          1 "" 90000 -3600 absent
probe_d "released_at = 4-char string 'null'"                  1 "null" 3600 3600 absent
probe_d "released_at reads as the string 'null}' (case B)"    1 "null}" 3600 3600 alive_here
probe_d "started_age non-numeric junk"                        1 "" "abc" 3600 absent
probe_d "tip_age non-numeric junk"                            1 "" 3600 "abc" absent

print -r -- ""
print -r -- "=== origin/main ABSENT (fresh init, no remote branch) ==="
git init -q "$T/norem"; mkdir -p "$T/norem/.softhouse"
print -r -- '{"host": "'"$HOSTS"'", "pid": 1, "started_at": "'"$NOWISO"'"}' > "$T/norem/.softhouse/LOCK"
GEREGE_NBFI_REPO="$T/norem" zsh "$W" --lock-signals 2>&1 | sed 's/^/    /'
print -r -- ""
print -r -- "scratch: $T"
