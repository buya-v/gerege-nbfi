#!/bin/bash
# OH-TBCAP-Y step 4 -- execute job 30 and poll run history until the new run ends.
set -u
DIR=$(cd "$(dirname "$0")/.." && pwd)
source "$DIR/bin/rest.sh"

OUT="$DIR/step04-job30"
mkdir -p "$OUT"

rest_get "$OUT/runhistory-before.json" "/jobs/30/runhistory"

# trigger a manual run
rest_post_nobody "$OUT/execute-response.txt" "/jobs/30?command=executeJob"
echo "executeJob HTTP $(cat "$OUT/execute-response.txt.status")"
cat "$OUT/execute-response.txt"; echo

# poll until a run whose version is greater than the max seen before appears
before_max=$(python3 -c "import json;d=json.load(open('$OUT/runhistory-before.json'));print(max([p['version'] for p in d['pageItems']] or [0]))")
echo "max version before = $before_max"

for i in $(seq 1 30); do
  rest_get "$OUT/runhistory-poll-$i.json" "/jobs/30/runhistory"
  done_ver=$(python3 - "$OUT/runhistory-poll-$i.json" "$before_max" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); b=int(sys.argv[2])
new=[p for p in d['pageItems'] if p['version']>b]
if new and all(p.get('jobRunEndTime') for p in new):
    print(max(p['version'] for p in new))
PY
)
  if [ -n "$done_ver" ]; then
    echo "new run completed at poll $i (version $done_ver)"
    cp "$OUT/runhistory-poll-$i.json" "$OUT/runhistory-after.json"
    break
  fi
  sleep 2
done

if [ ! -f "$OUT/runhistory-after.json" ]; then
  echo "NO NEW COMPLETED RUN within poll window"
  cp "$OUT/runhistory-poll-$i.json" "$OUT/runhistory-after.json"
fi

echo "--- runhistory after ---"
python3 -m json.tool "$OUT/runhistory-after.json"
