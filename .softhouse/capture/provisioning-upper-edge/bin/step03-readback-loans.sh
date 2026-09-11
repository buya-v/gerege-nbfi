#!/usr/bin/env bash
# STEP 3 (OH-PROVEDGE-BA): read each target loan back from the oracle and record
# the oracle's OWN overdue age (delinquent.pastDueDays / delinquentDays) and the
# oldest not-completed instalment due date. This is the observation, not our
# arithmetic: if the oracle counts differently, its count wins and OWNER.md
# records the divergence.
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
OUT_DIR=".softhouse/capture/provisioning-upper-edge/out"
BD_ISO='2026-09-03'

mkdir -p "$OUT_DIR"

# loan id / external id, resolved from the step-1 state file
MAP=".softhouse/capture/provisioning-upper-edge/out/edge-loans-idmap.txt"
get() { curl -sk -u mifos:password -H "$TEN" "$BASE$1"; }

while IFS='|' read -r ext cext cid lid; do
  [ -z "${lid:-}" ] && continue
  get "/loans/$lid?associations=all" > "$OUT_DIR/loan-$ext-detail-raw.json"
  echo "captured loan-$ext-detail-raw.json (id=$lid)"
done < "$MAP"

python3 - "$OUT_DIR" "$BD_ISO" <<'PY'
import json, os, sys, datetime
out, bd = sys.argv[1], datetime.date.fromisoformat(sys.argv[2])
print("business date =", bd)
for ext in ('EDGE-L29', 'EDGE-L59', 'EDGE-L89'):
    d = json.load(open(os.path.join(out, 'loan-%s-detail-raw.json' % ext)))
    dl = d['delinquent']
    # period 0 is the disbursement placeholder (period=None, amount 0); the first
    # real instalment is the smallest `period` that is not `complete`.
    unpaid = [i for i in d['repaymentSchedule']['periods']
              if i.get('period') and not i.get('complete') and i.get('dueDate')]
    unpaid.sort(key=lambda i: tuple(i['dueDate']))
    first = unpaid[0]
    due = datetime.date(*first['dueDate'])
    oracle_due = datetime.date(*dl['pastDueDate'])
    print("%s id=%s: first-instalment due=%s | oracle pastDueDate=%s pastDueDays=%s delinquentDays=%s "
          "| arithmetic=%d | outstanding=%s status=%s" % (
        ext, d['id'], due, oracle_due, dl['pastDueDays'], dl['delinquentDays'],
        (bd - oracle_due).days, d['summary']['totalOutstanding'], d['status']['value']))
PY

echo "readback done"
