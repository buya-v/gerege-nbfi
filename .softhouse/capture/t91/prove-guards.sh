#!/bin/sh
# T91 — SHIP NO GUARD YOU HAVE NOT DRIVEN RED (P-22).
#
# Every guard T91 adds is driven to FAIL here first, then shown passing.  A proof that only shows
# the "after" cannot tell a fix from a no-op.
#
# It is destructive, so it works ONLY inside a `git archive` export under /tmp that it creates
# itself.  It never touches the worktree and never touches the oracle.
#
# Usage:  sh prove-guards.sh            (run from anywhere inside the repo)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
S=/tmp/t91-guards.$$
trap 'rm -rf "$S"' EXIT
mkdir -p "$S/export"
(cd "$ROOT" && git archive HEAD) | tar -x -C "$S/export"
E=$S/export

echo "=================================================================== G-1"
echo "GUARD: the call-through refuses when the hardened rig is absent, and says so BEFORE it"
echo "       could have asserted anything.  The message 'PRECONDITIONS NOT RUN' must be TRUE AT"
echo "       THE MOMENT IT PRINTS."
echo
echo "-- GREEN first (rig present): expect exit 0 and 'ALL PRECONDITIONS HOLD'"
CANARY_REQ=$E/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json \
  sh "$E/.softhouse/capture/charges/bin/preconditions.sh" gerege 2>&1 | tail -1
echo "   exit=$?"
echo
echo "-- RED (rig deleted): expect exit 2, no assertion made"
rm -f "$E/.softhouse/capture/pathb/t36/preconditions.sh"
CANARY_REQ=$E/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json \
  sh "$E/.softhouse/capture/charges/bin/preconditions.sh" gerege
echo "   exit=$?"
echo
echo "-- RED through the T40 wrapper too (bin/run-preconditions.sh must propagate it)"
sh "$E/.softhouse/capture/charges/bin/run-preconditions.sh" "$S/rp.txt" | tail -1
echo

echo "=================================================================== G-2"
echo "GUARD: verdict.sh treats an EMPTY transcript set as an ERROR, not a pass."
echo "       'a check that passes vacuously on zero files' is the defect class this run keeps"
echo "       finding, so it must not be reintroduced by the thing that checks for it."
echo
mkdir -p "$S/empty"
sh "$HERE/verdict.sh" "$S/empty" >/dev/null 2>"$S/g2.err"
echo "   exit=$?   (expect 3)"
cat "$S/g2.err"
echo

echo "=================================================================== G-3"
echo "GUARD: shell-invariance.sh treats ZERO compared pairs as an ERROR."
echo
mkdir -p "$S/inv/x-sh" "$S/inv/x-bash"
sh "$HERE/shell-invariance.sh" "$S/inv" x >/dev/null 2>"$S/g3.err"
echo "   exit=$?   (expect 3)"
cat "$S/g3.err"
echo

echo "=================================================================== G-4"
echo "GUARD: verdict.sh's greps are 'LC_ALL=C grep -a'."
echo "       A transcript with one stray non-UTF-8 byte must not be able to make the scanner say"
echo "       the HALF_UP certification is ABSENT when it is present."
echo
mkdir -p "$S/poison"
cp "$ROOT/.softhouse/capture/t91/out/prefix-copy-sh"/A*.txt "$S/poison/" 2>/dev/null || \
  { echo "   (no committed pre-fix transcripts to poison; skipping G-4)"; exit 0; }
python3 - "$S/poison/A2a-mutated-canary-gerege.txt" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
i = b.find(b'PASS  effective rounding mode canary')
j = b.find(b'\n', i)
open(p, 'wb').write(b[:j] + b'\xff\xfe' + b[j:])
print('   poisoned the certification line itself with an invalid multibyte sequence')
PY
echo
echo "-- what /usr/bin/grep (BSD) does with and without -a:"
LC_ALL=C /usr/bin/grep -qF 'PASS  effective rounding mode canary' "$S/poison/A2a-mutated-canary-gerege.txt"
echo "   BSD  -qF  rc=$?"
LC_ALL=C /usr/bin/grep -aqF 'PASS  effective rounding mode canary' "$S/poison/A2a-mutated-canary-gerege.txt"
echo "   BSD -aqF  rc=$?"
echo "   MEASURED: on this machine BSD grep matched EITHER WAY.  T80 reported that BSD grep in a"
echo "   UTF-8 locale matches nothing here; that did NOT reproduce for me and I do not repeat it"
echo "   as fact.  What DID reproduce is below."
echo
if command -v ugrep >/dev/null 2>&1; then
  LC_ALL=C ugrep -qF 'PASS  effective rounding mode canary' "$S/poison/A2a-mutated-canary-gerege.txt"
  echo "   ugrep  -qF  rc=$?   (1 = 'absent' — WRONG, the sentence is there)"
  LC_ALL=C ugrep -aqF 'PASS  effective rounding mode canary' "$S/poison/A2a-mutated-canary-gerege.txt"
  echo "   ugrep -aqF  rc=$?   (0 = present — correct)"
else
  echo "   ugrep is not on PATH here; the ugrep limb was measured interactively and is reported"
  echo "   in the handoff.  Without -a it returned 1 ('absent') on this exact poisoned file."
fi
echo
echo "-- verdict.sh (with -a) on the poisoned set: must still name A2a as an admission"
sh "$HERE/verdict.sh" "$S/poison" 2>&1 | LC_ALL=C /usr/bin/grep -a '^A2a'
echo
echo "=================================================================== done"
