#!/bin/sh
# T80 — the single sentence this whole task exists to make honest.
#
# T77's exploit made the rig print
#     PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)
# on the HALF_EVEN `default` tenant, with a request that was not a half-minor-unit tie.  A reader
# believes that sentence; it is the strongest claim the rig makes.  It must therefore appear ONLY
# in a transcript that (a) names tenant 'gerege' and (b) shows the canary DIGEST COMPARISON passing.
#
# This scans every committed T80 transcript and fails if that co-occurrence is ever violated.
set -u
T80=$(cd "$(dirname "$0")" && pwd)
O=$T80/out
S='PASS  effective rounding mode canary'
D='PASS  canary request pinned by DIGEST COMPARISON'
bad=0
for f in "$O"/attack-*.txt "$O"/*/preconditions.txt; do
  [ -f "$f" ] || continue
  if LC_ALL=C grep -qaF "$S" "$f"; then
    if LC_ALL=C grep -qaF "$D" "$f" && LC_ALL=C grep -qa "tenant 'gerege'" "$f" \
       && ! LC_ALL=C grep -qa "tenant 'default'" "$f"; then
      echo "OK        $f — canary PASS is accompanied by a passing digest pin, tenant gerege"
    else
      echo "VIOLATION $f — the canary PASS appears WITHOUT a passing digest pin, or not on gerege"
      bad=$((bad+1))
    fi
  else
    echo "absent    $f"
  fi
done
echo
echo "violations: $bad"
[ "$bad" = "0" ] || exit 1
echo "RESULT: the HALF_UP claim is never made except on tenant gerege with the pinned canary."
exit 0
