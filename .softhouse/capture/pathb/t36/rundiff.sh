#!/bin/sh
# T36 — run the number-by-number diff for all four Path B sets.
set -u
D=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$D/.." && pwd)
R=$D/out/recapture-gerege
rc=0
python3 "$D/t36_diff.py" "$W/out/B-01-baseline-raw.json"            "$R/B-01-baseline-raw.json"            "B-01 baseline"            || rc=1
python3 "$D/t36_diff.py" "$W/out/B-02-multiplesof100-raw.json"      "$R/B-02-multiplesof100-raw.json"      "B-02 multiplesOf 100"     || rc=1
python3 "$D/t36_diff.py" "$W/out/B-03-diycs-fullleapyear-raw.json"  "$R/B-03-diycs-fullleapyear-raw.json"  "B-03 FULL_LEAP_YEAR"      || rc=1
python3 "$D/t36_diff.py" "$W/out/B-04-diycs-feb29only-raw.json"     "$R/B-04-diycs-feb29only-raw.json"     "B-04 FEB_29_PERIOD_ONLY"  || rc=1
echo "========================================================================================"
echo "OVERALL: $([ $rc -eq 0 ] && echo 'NO NUMBER MOVED' || echo 'AT LEAST ONE NUMBER MOVED')"
exit $rc
