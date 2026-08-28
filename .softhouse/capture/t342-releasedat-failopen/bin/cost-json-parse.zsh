#!/bin/zsh
# T342 — COST THE ALTERNATIVE, in seconds, rather than guessing at it.
#
# The narrow fix is free. Replacing the string surgery with a real JSON parse costs one
# `/usr/bin/python3` fork per field read. This measures that fork against the number of
# reads a fire actually performs, so "it is negligible" is a number and not an opinion.
#
# A fire start reads the LOCK's signals ONCE (fire-program.sh:556-559): released_at,
# started_at, host, pid = 4 field reads. `--lock-signals` is the same 4. Nothing in the
# fire's multi-hour body re-reads them.
set -uo pipefail
F=$(mktemp /tmp/t342-cost.XXXXXX)
printf '{"holder":"local-launchd","host":"h","pid":1,"fire":"20260828-080001","started_at":"2026-08-28T00:00:00Z","heartbeat":"2026-08-28T00:00:00Z","log":"/tmp/l","oracle":"up","postgres":"up"}' > "$F"

print -r -- "python3: $(/usr/bin/python3 -V 2>&1)"
print -r -- ""
print -r -- "--- 4 forks == ONE fire start's worth of LOCK field reads"
time ( repeat 4 /usr/bin/python3 -c 'import json,sys;json.load(open(sys.argv[1]))' "$F" )
print -r -- ""
print -r -- "--- 40 forks == ten fire starts, to get past timer granularity"
time ( repeat 40 /usr/bin/python3 -c 'import json,sys;json.load(open(sys.argv[1]))' "$F" )
print -r -- ""
print -r -- "--- for scale: the SHIPPED wrapper already forks /usr/bin/python3 unconditionally"
print -r -- "    fire-program.sh:488  branch_sweep.py install-hook"
print -r -- "    fire-program.sh:489  branch_sweep.py sweep"
print -r -- "    fire-program.sh:1661 ready-tasks.py (every reconcile)"
print -r -- "    so this adds no new dependency class, only forks."
rm -f "$F"
