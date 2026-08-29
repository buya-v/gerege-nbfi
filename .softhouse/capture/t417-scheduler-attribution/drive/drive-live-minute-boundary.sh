#!/usr/bin/env bash
# drive-live-minute-boundary.sh -- THE LIVE ARM.
#
# Opens a witness, waits across a minute boundary so that a REAL scheduled job runs inside the
# window (job 36 "Send Asynchronous Events", cron `0 0/1 * * * ?`, 1440 runs in the last 24h),
# then closes it. Nothing here writes to the shared reference oracle: any movement observed is
# the oracle's own, which is the whole point.
#
# This arm answers a question that cannot be answered by argument: does a scheduled job running
# inside a capture window actually MOVE the graded surface? The verdict is whichever it is --
# QUIESCENT-WITH-RUNS if the run touched nothing graded, CONTAMINATED if it did.
set -uo pipefail
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
I="$DIR/instruments/oracle-window-witness.sh"
OUT="$DIR/out/DRIVE-LIVE-minute-boundary.txt"
LABEL="LIVE-MINUTE-BOUNDARY"
{
  echo "LIVE ARM -- capture window deliberately spanning a scheduler minute boundary"
  echo "host UTC at open : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  bash "$I" open "$LABEL"; echo "open rc=$?"
  echo "-- waiting 80s, across the next minute boundary --"
} > "$OUT" 2>&1
python3 -c "import time; time.sleep(80)" 2>/dev/null || sleep 80
{
  echo "host UTC at close: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  bash "$I" close "$LABEL"; echo "close rc=$?"
} >> "$OUT" 2>&1
cat "$OUT"
