#!/bin/sh
# T36 — the same ten property invariants on the EMI re-adjust-loop probe captures.
# A capture that pins new behaviour must still satisfy the money invariants; if the loop
# broke one of them, that would be the finding, not a footnote.
set -u
D=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$D/.." && pwd)
O=$D/out/emiloop
set --
for p in 1200000 1200001 1200004 1200027 1200033 1200039 1200045 1200054 1200189; do
  set -- "$@" "$O/emiloop-$p-raw.json::EMI-loop probe principal $p MNT (gerege, 19/HALF_UP)"
done
python3 "$W/t22-audit/t22_invariants.py" "$@"
