#!/usr/bin/env bash
# T261 BAR -- run the golden-vector conformance harness myself, on the tree that
# would exist if T250 merged (my worktree HEAD + T250's 130 additive files).
#
# P-83: the ORACLE PROBE LINE'S PRESENCE is tested FIRST, and only then its value.
# A run whose probe line is absent has not told you the oracle was reached, and
# reading a value out of an absent line is how a fail-open gets certified.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/../../../.." && pwd)
OUT="$ROOT/.softhouse/reviews/t261-tenant-attestation/evidence"
LOG="$OUT/90-bar.txt"

# shellcheck disable=SC1091
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
echo "go: $(go version 2>&1)"

bash "$ROOT/.softhouse/conformance.sh" > "$LOG" 2>&1
RC=$?
echo "conformance.sh EXIT = $RC   (3 would mean wrong interpreter; not seen if not 3)"
echo ""

echo "=== STEP 1 (P-83): probe line PRESENCE, before any value is read ==="
PRESENT=$(python3 - "$LOG" <<'PY'
import sys
n = 0
for line in open(sys.argv[1], "rb"):
    if b"probe = " in line:
        n += 1
print(n)
PY
)
echo "  lines containing 'probe = ' : $PRESENT"
if [ "$PRESENT" -lt 1 ]; then
  echo "  ABSENT -- the harness did not report contacting the reference oracle."
  echo "  REFUSING to read a value out of a line that is not there. (P-83)"
  exit 5
fi
echo "  PRESENT."
echo ""
echo "=== STEP 2: the probe VALUE ==="
python3 - "$LOG" <<'PY'
import sys
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    if "probe = " in line:
        print("  " + line.strip())
PY
echo ""
echo "=== STEP 3: verdict, counts, pins ==="
python3 - "$LOG" "$RC" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8", errors="replace").read()
rc = sys.argv[2]
want = [
    ("VERDICT",                r"(?m)^.*VERDICT.*$"),
    ("parity/cells",           r"(?m)^.*(parity vectors|cells compared|cells).*$"),
    ("census pins",            r"(?m)^.*census pin.*$"),
    ("fail-open frontier",     r"(?m)^.*frontier.*$"),
    ("refused",                r"(?m)^.*\brefused\b.*$"),
    ("inadmissible",           r"(?m)^.*inadmissible.*$"),
    ("harness errors",         r"(?m)^.*harness error.*$"),
    ("invariant",              r"(?m)^.*invariant violation.*$|(?m)^.*NOT RUN.*$"),
]
for label, pat in want:
    hits = re.findall(pat, t)
    print("--- %s (%d line(s))" % (label, len(hits)))
    for h in hits[:14]:
        print("      " + h.strip()[:200])
print("")
print("exit code: %s" % rc)
PY
exit "$RC"
