#!/bin/sh
# T40 STEP 2 — ZERO-CHARGE CONTROL.
#
# Before adding a single charge, re-emit an ALREADY-COMMITTED Path B capture through
# THIS harness and prove it is byte-for-byte identical.  If the control does not
# reproduce, the harness is the variable and nothing captured after it is trustworthy.
# (patterns.md: "Re-emit a capture input-for-input before you add cases to it.")
#
# The request files are sent BYTE-VERBATIM from .softhouse/capture/pathb/req/ (read-only
# to T40).  Nothing is regenerated, reformatted or re-serialised.
set -eu
. "$(dirname "$0")/lib.sh"

O=$CH/out/control
mkdir -p "$O"

echo "### preconditions"
sh "$CH/bin/run-preconditions.sh" "$O/preconditions.txt" > /dev/null || {
  echo "ABORT: preconditions breached — nothing captured." >&2; exit 1; }
grep -c '^  PASS' "$O/preconditions.txt" | sed 's/^/  preconditions PASS count: /'

echo
echo "### zero-charge control captures (committed requests, byte-verbatim)"
for c in B-01-baseline B-02-multiplesof100 B-03-diycs-fullleapyear B-04-diycs-feb29only; do
  post "$W/.softhouse/capture/pathb/req/calc-$c.json" "$O/$c-raw.json"
done

echo
echo "### digest comparison vs the COMMITTED corpus (.softhouse/capture/pathb/out/)"
rc=0
for c in B-01-baseline B-02-multiplesof100 B-03-diycs-fullleapyear B-04-diycs-feb29only; do
  new=$(sha "$O/$c-raw.json")
  old=$(sha "$W/.softhouse/capture/pathb/out/$c-raw.json")
  if [ "$new" = "$old" ]; then
    echo "  IDENTICAL  $c  $new"
  else
    echo "  MISMATCH   $c  new=$new committed=$old" >&2
    rc=1
  fi
done

if [ "$rc" != "0" ]; then
  echo >&2
  echo "CONTROL FAILED. The harness does not reproduce the committed corpus. STOP: do not" >&2
  echo "capture charges through it, and do not treat anything it produced as an observation." >&2
  exit 1
fi
echo
echo "CONTROL PASSED — harness reproduces all four committed Path B captures byte-for-byte."
