#!/bin/zsh
# T211 -- build the scratch repo the subject runs against.  NEVER the live repo:
# a fire is running from /Users/buv/gerege-nbfi and holds the real LOCK.
set -uo pipefail
REPO="${T211_REPO:-/tmp/t211-scratch/repo}"
rm -rf "$REPO"
mkdir -p "$REPO/.softhouse"
cd "$REPO" || exit 1
git init -q -b main
print -r -- baseline > .softhouse/tasks.json
cat > .softhouse/LOCK <<EOF
{
  "holder": "local-launchd",
  "host": "$(hostname -s)",
  "pid": 0,
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
git add -A
git -c user.name=t211 -c user.email=t211@example.com commit -q -m baseline
print -r -- "scratch repo ready at $REPO (LOCK present, no remote 'origin' -- push failures are expected and are the real code path)"
