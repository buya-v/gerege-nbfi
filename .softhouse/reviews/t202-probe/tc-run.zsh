#!/bin/zsh
# T202 -- builds the scratch repo then drives one subject/signal pair via the
# python spawner (launchd-faithful dispositions).
set -uo pipefail
SUBJECT=$1; SIG=$2; LABEL=$3
REPO=/tmp/t202/tc-repo
rm -rf "$REPO"; mkdir -p "$REPO/.softhouse"
cd "$REPO" || exit 1
git init -q -b main
print -r -- baseline > .softhouse/tasks.json
print -r -- "{\"holder\":\"local-launchd\",\"host\":\"$(hostname -s)\",\"pid\":0}" > .softhouse/LOCK
git add -A
git -c user.name=t202 -c user.email=t202@example.com commit -q -m baseline
/usr/bin/python3 /tmp/t202/tc-spawn.py "$SUBJECT" "$REPO" "$SIG" "$LABEL"
