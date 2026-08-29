#!/bin/bash
# T459 FINAL BAR -- run from scratch OUTSIDE the repository, on my own committed tree.
set -u
R="$1"
CWD=/tmp/t459/finalbar
rm -rf "$CWD"; mkdir -p "$CWD"
SH=".soft""house"; CONF="$SH/conformance"".sh"
echo "=== git status --porcelain BEFORE ==="
( cd "$R" && git status --porcelain )
echo "=== HEAD ==="
( cd "$R" && git log --oneline -1 )
LOG=<evidence>/90-FINAL-BAR.log
rc=0
( cd "$CWD" && bash "$R/$CONF" ) > "$LOG" 2>&1 || rc=$?
if [ ! -s "$LOG" ]; then echo "INSTRUMENT FAILURE: empty bar log"; exit 3; fi
echo "=== git status --porcelain AFTER ==="
( cd "$R" && git status --porcelain )
echo
echo "EXIT = $rc"
echo -n "grep -c 'probe = ' = "; LC_ALL=C grep -c 'probe = ' "$LOG"
LC_ALL=C grep 'probe = ' "$LOG"
LC_ALL=C grep -m1 '^VERDICT' "$LOG"
echo "--- pinned figures ---"
LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population' "$LOG"
LC_ALL=C grep -m2 'deadOccurrences\|T316-DEADPATH' "$LOG"
LC_ALL=C grep -m3 'frontier' "$LOG" | head -3
LC_ALL=C grep -m1 'GUARD-COST CENSUS' "$LOG"
LC_ALL=C grep -m1 'guard-cost: PASS' "$LOG"
LC_ALL=C grep -m1 'registration decisive lines' "$LOG"
LC_ALL=C grep -m1 'HARNESS-TEXT CENSUS' -A3 "$LOG"
LC_ALL=C grep -m1 'host-state\|census == pinned' "$LOG"
LC_ALL=C grep -m1 'wrong ledger implementation\|DIED through this harness' "$LOG"
