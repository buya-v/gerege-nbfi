#!/usr/bin/env bash
# T290 -- BREAK T271's RED/GREEN BATTERY LEG `G1` ON PURPOSE, and show the red.
#
# T271 claims: `leg G1 fails if `disagreements` drops below 4`, and rests the whole "the bar went
# green by acknowledgement, not by lowering" argument on it. A claim about a guard is worth what
# its red drive is worth, so this drops the count and re-runs the battery.
#
# HOW THE COUNT IS DROPPED: the four `false` `P2_*` booleans in the committed
# `classify-t219.json` are flipped to `true` -- i.e. the exact retro-edit T114/T176 forbid, done
# here as a MEASUREMENT and undone before this script exits.
#
# IT RESTORES THE COMMITTED EVIDENCE on every exit path including a failure, and verifies the
# restore by sha256. If the restore does not verify, this script exits 2 and says so.
#
# EXIT 0 the battery went RED as T271 claims; 1 it did not (T271's claim would then be wrong);
# 2 the restore failed or an input is missing. Never conflated (P-80).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
EV="$ROOT/.softhouse/capture/t219-g8-residual/out/classify-t219.json"
BATTERY="$ROOT/.softhouse/capture/t271-b1-t219/red/drive-red-t271.py"

for need in "$EV" "$BATTERY"; do
  [ -f "$need" ] || { echo "ERROR: missing input: $need" >&2; exit 2; }
done

BAK="$(mktemp)"
cp "$EV" "$BAK"
BEFORE="$(shasum -a 256 "$EV" | cut -d' ' -f1)"
restore() { cp "$BAK" "$EV"; }
trap 'restore; rm -f "$BAK"' EXIT

echo "T290 -- breaking T271 battery leg G1 on purpose"
echo "================================================================================"
echo "  evidence            : ${EV#"$ROOT"/}"
echo "  sha256 as committed : $BEFORE"
echo ""

python3 - "$EV" <<'PY'
import json
import sys
p = sys.argv[1]
d = json.load(open(p))
n = 0
for row in d["cells"]:
    for k in list(row):
        if k.startswith("P2_") and row[k] is False:
            row[k] = True
            n += 1
json.dump(d, open(p, "w"), indent=1)
open(p, "a").write("\n")
print("  RETRO-EDITED: %d false P2_* booleans flipped to true. The disagreement count must now" % n)
print("  fall from 4 to 0, and G1 must FAIL if T271's claim about it is true.")
PY
echo ""

RC=0
python3 "$BATTERY" || RC=$?
echo "  battery exit: $RC"
echo ""

restore
AFTER="$(shasum -a 256 "$EV" | cut -d' ' -f1)"
echo "  sha256 after restore: $AFTER"
if [ "$AFTER" != "$BEFORE" ]; then
  echo "  !! RESTORE FAILED. The committed evidence is NOT back. This is an ERROR."
  exit 2
fi
echo "  committed evidence restored and VERIFIED."
echo ""

if [ "$RC" -ne 0 ]; then
  echo "  CONCLUSION: G1 DOES fail when the count drops. T271's claim survives this attack, and"
  echo "  \"the bar went green by acknowledgement, not by lowering\" is TRUE OF T271's BATTERY."
  echo "  IT IS NOT TRUE OF THE GUARD T271 SPECIFIES FOR T269, which pins only unacknowledged=0"
  echo "  and passes this same retro-edited tree. See red/drive-red-t290.py leg R2."
  echo "T290-BREAK-G1: DEMONSTRATED batteryWentRed=1 restored=1"
  exit 0
fi
echo "  CONCLUSION: the battery stayed GREEN with the count at zero. T271's claim about G1 is"
echo "  FALSE and must not be quoted."
echo "T290-BREAK-G1: REFUTED batteryWentRed=0 restored=1"
exit 1
