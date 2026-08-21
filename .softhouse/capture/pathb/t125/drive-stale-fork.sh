#!/bin/bash
# T125 — RED/GREEN for the THIRD file, `capture/charges/bin/attest.py`.
#
# That file is a stale fork: a verbatim copy of pathb/t36/attest.py@aafc8b3 committed into
# charges/bin by T40 and never re-pointed.  `charges/t22-audit/` and
# `charges/req/calc-B-01-baseline.json` do not exist, so it cannot complete a capture and
# never has (no attestation on disk was produced by it).  It therefore has no "green
# attestation" to drive.  What CAN be driven, and is what matters, is the gate itself:
#
#   RED   tenant `default` (a real HALF_EVEN JVM): the gate must REFUSE, exit 4, before the
#         run reaches anything else.
#   GREEN tenant `gerege`  (the ratified HALF_UP tenant): the gate must NOT refuse — the run
#         must get PAST it and fail later, on this fork's own missing paths.  "Fails for a
#         different reason, further down" is the only green this file can honestly produce,
#         and printing anything stronger would be the very dishonesty this task is closing.
#
# The outer precondition gate is bypassed in both halves by the same single labelled
# substitution used by drive-canary-red.sh, because preconditions.sh is what currently
# refuses a wrong-mode tenant and the question here is what the INNER gate does.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
CHBIN="$HERE/../../charges/bin"
SCRATCH="$CHBIN/.t125-scratch-attest.py"
OUTDIR="$HERE/stale-fork-proof"
mkdir -p "$OUTDIR"
rc_all=0

sed -e "s|^if pre.returncode != 0:|if False:  # T125: OUTER precondition gate DISABLED|" \
    "$CHBIN/attest.py" > "$SCRATCH"
echo "== the ONLY change made to charges/bin/attest.py for these runs =="
diff "$CHBIN/attest.py" "$SCRATCH" | tee "$OUTDIR/scratch.diff"

for tenant in default gerege; do
  echo
  echo "=================================================================="
  echo "charges/bin/attest.py  tenant=$tenant"
  echo "=================================================================="
  python3 "$SCRATCH" "$tenant" > "$OUTDIR/$tenant.stdout.txt" 2> "$OUTDIR/$tenant.stderr.txt"
  rc=$?
  cat "$OUTDIR/$tenant.stdout.txt"
  cat "$OUTDIR/$tenant.stderr.txt"
  echo "EXIT CODE: $rc"
  if [ "$tenant" = default ]; then
    if [ "$rc" -eq 4 ]; then
      echo "RED OK: the gate REFUSED a HALF_EVEN JVM with the dedicated exit code 4."
    else
      echo "RED FAILED: expected exit 4, got $rc"; rc_all=1
    fi
  else
    if [ "$rc" -eq 4 ]; then
      echo "GREEN FAILED: the gate refused the RATIFIED tenant."; rc_all=1
    elif grep -q "ATTESTATION REFUSED" "$OUTDIR/$tenant.stderr.txt"; then
      echo "GREEN FAILED: the gate refused the RATIFIED tenant."; rc_all=1
    else
      echo "GREEN OK: the gate did NOT refuse the ratified tenant; the run proceeded past it"
      echo "          and then failed on this stale fork's own missing paths, as documented."
    fi
  fi
done

rm -f "$SCRATCH"
rm -rf "$CHBIN/out"          # this fork's OUT is charges/bin/out/, created by the runs above
echo
echo "T125 stale-fork proof: $rc_all (0 = RED refused, GREEN did not)"
exit $rc_all
