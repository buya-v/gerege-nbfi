#!/bin/zsh
# T280 — CONSTRUCT the mtime-vs-push-recency disagreement instead of asserting it.
#
# T279's drive-wrapper-vs-skill.zsh "demonstrates" this case with three hard-coded
# integers (OLD_MTIME_AGE=759 ...). Nothing in it reads a file mtime or a git tip. This
# script builds a REAL repo where the two signals disagree, runs `git pull --ff-only`
# exactly as the wrapper does at STEP 0.2, and reads BOTH signals off the shipped
# `--lock-signals` path.
set -uo pipefail
W="$1"
T=$(mktemp -d /tmp/t280-mtime.XXXXXX)
export GIT_CONFIG_NOSYSTEM=1 HOME="$T/home"; mkdir -p "$HOME"
printf '[user]\n\tname = T280\n\temail = t280@local\n[init]\n\tdefaultBranch = main\n' > "$HOME/.gitconfig"

git init -q --bare "$T/origin.git"
git init -q "$T/holder"; cd "$T/holder"
mkdir -p .softhouse; echo seed > .softhouse/seed
git add -A >/dev/null; git commit -qm seed
git remote add origin "$T/origin.git"; git push -q origin main

HOSTS=$(hostname -s)
# A lock stamped 8 HOURS AGO by a holder that is still alive (a real pid we own).
sleep 900 &
LIVEPID=$!
STARTED=$(date -u -v-8H +%Y-%m-%dT%H:%M:%SZ)
print -r -- '{
  "holder": "local-launchd",
  "host": "'"$HOSTS"'",
  "pid": '"$LIVEPID"',
  "started_at": "'"$STARTED"'"
}' > .softhouse/LOCK
git add -f .softhouse/LOCK >/dev/null
# Backdate the LOCK COMMIT and the tip to 12 h ago -> nothing published for 12 h.
TIPDATE=$(date -u -v-12H +"%Y-%m-%dT%H:%M:%S+0000")
GIT_AUTHOR_DATE="$TIPDATE" GIT_COMMITTER_DATE="$TIPDATE" git commit -qm "softhouse: local fire lock (t280)"
git push -q origin main

# THE FRESH CLONE the scheduled fire actually is. Its checkout writes the LOCK file NOW,
# so its mtime is seconds old while the lock is 8 h old and nothing was published for 12 h.
git clone -q "$T/origin.git" "$T/fire"
cd "$T/fire"
git pull --ff-only -q 2>/dev/null    # STEP 0.2 — the operation T265 says resets the mtime

print -r -- "=== CONSTRUCTED, NOT ASSUMED ==="
MT=$(/usr/bin/stat -f %m "$T/fire/.softhouse/LOCK")
NOW=$(date +%s)
print -r -- "  lock file mtime age     : $(( NOW - MT ))s"
print -r -- "  started_at              : $STARTED"
print -r -- "  started_at age          : $(( NOW - $(TZ=UTC /bin/date -j -f %Y-%m-%dT%H:%M:%SZ "$STARTED" +%s) ))s"
print -r -- "  origin/main tip age     : $(( NOW - $(git log -1 --format=%ct origin/main) ))s"
print -r -- "  holder pid $LIVEPID is  : $(kill -0 $LIVEPID 2>/dev/null && print ALIVE || print gone)"
print -r -- ""
print -r -- "  ratio mtime:started_at  : $(python3 -c "print(round(($NOW-$(TZ=UTC /bin/date -j -f %Y-%m-%dT%H:%M:%SZ "$STARTED" +%s))/max(1,$NOW-$MT),1))")x"
print -r -- ""
print -r -- "=== the SHIPPED reader on this repo ==="
GEREGE_NBFI_REPO="$T/fire" zsh "$W" --lock-signals 2>&1 | sed 's/^/  /'
print -r -- ""
print -r -- "=== does mtime decide anything? flip ONLY the mtime, keep every other signal ==="
touch -t "$(date -v-30M +%Y%m%d%H%M)" "$T/fire/.softhouse/LOCK"
print -r -- "  after touch -30m:"
GEREGE_NBFI_REPO="$T/fire" zsh "$W" --lock-signals 2>&1 | sed 's/^/  /'
touch -t "$(date -v-3d +%Y%m%d%H%M)" "$T/fire/.softhouse/LOCK"
print -r -- "  after touch -3d:"
GEREGE_NBFI_REPO="$T/fire" zsh "$W" --lock-signals 2>&1 | sed 's/^/  /'
print -r -- ""
print -r -- "=== grep: every use of the lock file mtime in the shipped wrapper ==="
grep -n 'stat -f %m' "$W" | sed 's/^/  /'
print -r -- ""
kill $LIVEPID 2>/dev/null
print -r -- "scratch: $T"
