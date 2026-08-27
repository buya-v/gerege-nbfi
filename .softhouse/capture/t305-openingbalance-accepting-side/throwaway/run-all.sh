#!/bin/sh
# T305 -- THE WHOLE THROWAWAY CAPTURE, END TO END, AS ONE REPRODUCIBLE COMMAND.
#
#   bash run-all.sh
#
# WHY THIS EXISTS. The admissibility argument for a capture taken on an instance that no longer
# exists rests on the RECIPE being deterministic and committed. A reviewer who wants to re-derive
# any byte in out/ runs this one script; it rebuilds the instance from the same image the standing
# reference oracle runs, seeds the same tenant parameters, replays the same setup campaign and
# fires the same request bodies. What it CANNOT reproduce is a transaction id (Fineract generates
# one per POST) and a wall-clock timestamp; everything else is byte-stable and the vectors grade
# nothing else.
#
# ORDER, AND EVERY STEP IS FAIL-CLOSED:
#   0  guard-throwaway-isolation.sh  -- refuses unless the rig cannot touch the standing stack,
#                                       and records the standing baseline the later steps re-check
#   1  docker compose up             -- fresh containers, no named volume, port 8444
#   2  wait for the health endpoint
#   3  setup.sh                      -- MNT, four GL accounts, financial activity 300
#   4  capture.sh                    -- THE ACCEPTING CAPTURE (empty ledger)
#   5  capture2.sh                   -- accept-again-with-reversal, plain manual entry, refuse
#   6  down.sh                       -- destroy, and prove the standing oracle did not move
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
CF="$DIR/docker-compose.t305.yml"
OUT="$DIR/out"
say() { printf '\n=== %s\n' "$*"; }

rm -rf "$OUT" "$DIR/req"
mkdir -p "$OUT" /tmp/t305-oracle-logs

say "0 isolation guard (also records out/STANDING-baseline.txt)"
bash "$DIR/guard-throwaway-isolation.sh" > "$OUT/STANDING-baseline.txt" 2>&1 || {
  cat "$OUT/STANDING-baseline.txt"; echo "REFUSED at step 0."; exit 1; }
cat "$OUT/STANDING-baseline.txt"

say "1 docker compose up"
docker compose -p t305-oracle -f "$CF" up -d 2>&1 | sed 's/^/  /'

say "2 waiting for https://localhost:8444/fineract-provider/actuator/health"
i=0
while [ "$i" -lt 60 ]; do
  if curl -sk -m 5 -o /dev/null https://localhost:8444/fineract-provider/actuator/health 2>/dev/null; then break; fi
  i=$((i + 1)); sleep 10
done
curl -sk https://localhost:8444/fineract-provider/actuator/health | tee "$OUT/THROWAWAY-health.txt"; printf '\n'
grep -q '"status":"UP"' "$OUT/THROWAWAY-health.txt" || { echo "throwaway never came up"; exit 1; }

say "3 setup.sh"
bash "$DIR/setup.sh" 2>&1 | tee "$OUT/SETUP.txt"

say "4 capture.sh -- THE ACCEPTING CAPTURE"
bash "$DIR/capture.sh" 2>&1 | tee "$OUT/CAPTURE.txt"

say "5 capture2.sh -- the state-transition sequence"
bash "$DIR/capture2.sh" 2>&1 | tee "$OUT/CAPTURE2.txt"

say "6 down.sh -- destroy and prove the standing oracle did not move"
bash "$DIR/down.sh" 2>&1 | tee "$OUT/TEARDOWN.txt"

say "manifest"
bash "$DIR/manifest.sh"
