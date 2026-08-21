#!/bin/sh
# financialactivityaccount battery. Mixed valid/invalid; refusals are observations.
DIR=$(cd "$(dirname "$0")" && pwd)
for n in fin-100-liability-transfer fin-101-asset-transfer fin-102-duplicate-activity \
         fin-103-wrong-account-type fin-104-unknown-activity fin-105-missing-account \
         fin-106-header-account; do
  sh "$DIR/cap.sh" "A2-${n}" POST /financialactivityaccounts "req/$n.json"
done
