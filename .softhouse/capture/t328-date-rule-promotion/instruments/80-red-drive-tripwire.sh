#!/usr/bin/env bash
# T328 -- RED-DRIVE THE RE-KEYED TRIPWIRE. P-22: "a control that cannot fail is
# worse than none", and the arm this replaces was measured passing on exactly the
# event it was written to catch [FU-T328-1, out/70-T306-tripwire-DID-NOT-FIRE.txt].
# So the replacement does not get to be trusted on its shape.
#
# The arm reads the COMMITTED store from a path fixed in the test source, so the
# only honest way to drive it is to perturb the committed store and put it back.
# THE RESTORE IS AN EXIT TRAP AND IS VERIFIED: the script re-checks `git status`
# for the two vector files before it exits non-zero on anything.
#
# TWO ARMS, ONE PER DIRECTION, because a rule that fires in one direction only
# would have exactly the defect the arm it replaces had.
#
#   ARM A  an ACCEPTANCE moved into the REFUSING region
#          LDG-07 keeps expect.kind "journal-entry" and its business_date is
#          moved back one day, so transaction_date 2026-08-28 becomes STRICTLY
#          AFTER it. The oracle refuses there; the vector still claims 200.
#   ARM B  a REFUSAL moved into the ACCEPTING region
#          LDG-REFUSE-04 keeps expect.kind "refusal" and its latest_closing_date
#          is moved back one day, so transaction_date 2026-01-31 becomes strictly
#          AFTER it. The oracle accepts there; the vector still claims 403.
#
# Exit 0 = both arms went RED and the store was restored byte-identical.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
LDG=$REPO/.softhouse/vectors/ledger
V7=$LDG/LDG-07-entry-on-the-business-date-accepted.json
R4=$LDG/LDG-REFUSE-04-preclosure-entry-on-closing-date.json
TEST=TestOpeningBalanceCapabilityIsScopedToTheObservedShape
ARM="every committed claimant's EXPECTATION AGREES with its date REGION"

restore() {
  git -C "$REPO" checkout -- "$V7" "$R4" 2>/dev/null
  local dirty
  dirty="$(git -C "$REPO" status --porcelain -- "$V7" "$R4")"
  if [ -n "$dirty" ]; then
    echo "*** THE STORE WAS NOT RESTORED. Fix this by hand before doing anything else:"
    echo "$dirty"
  fi
}
trap restore EXIT

run_arm() { # $1 = label
  local out rc
  # -count=1 IS LOAD-BEARING AND WAS MEASURED, NOT ADDED FROM HABIT. The first
  # run of this script omitted it and reported BOTH ARMS GREEN -- go test replayed
  # a CACHED result, because the perturbation is to a data file outside the module
  # and nothing in the package source changed. A red-drive that measures the test
  # cache instead of the code is exactly the vacuous control it exists to prevent
  # [FU-T328-2]. The same trap applies to any future arm that perturbs the store.
  out="$( cd "$REPO/nexus" && go test -count=1 ./internal/apps/ledger/conformance -run "$TEST" 2>&1 )"
  rc=$?
  echo "--- $1"
  printf '%s\n' "$out" | LC_ALL=C grep -a -E "FAIL|records (an ACCEPTANCE|a REFUSAL)|ONE DIFF, NOT TWO" \
    | sed 's/^/    /' | head -12
  echo "    go test exit: $rc"
  return $rc
}

echo "T328 tripwire red-drive -- HEAD $(git -C "$REPO" rev-parse --short HEAD)"
echo "arm under drive: $TEST/\"$ARM\""
echo ""

rc=0

# GREEN BASELINE. Without it a red below could be a pre-existing failure.
if run_arm "BASELINE  committed store, untouched -- the arm must be GREEN"; then
  echo "    OK: green baseline"
else
  echo "    *** the arm is ALREADY RED on the committed store; nothing below measures anything."
  rc=1
fi
echo ""

# ARM A -- acceptance dragged into the refusing region.
python3 - "$V7" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
assert d["request"]["business_date"] == "2026-08-28", d["request"]["business_date"]
d["request"]["business_date"] = "2026-08-27"      # txn 2026-08-28 is now FUTURE-DATED
json.dump(d, open(p, "w"), indent=1); open(p, "a").write("\n")
PY
if run_arm "ARM A  LDG-07's business_date moved back one day (acceptance -> refusing region)"; then
  echo "    *** THE ARM STAYED GREEN. It cannot see an acceptance promoted into the refusing"
  echo "    *** region, which is one of the two things it exists to see."
  rc=1
else
  echo "    OK: RED, and the message names the vector and the region"
fi
git -C "$REPO" checkout -- "$V7"
echo ""

# ARM B -- refusal dragged into the accepting region.
python3 - "$R4" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
assert d["request"]["latest_closing_date"] == "2026-01-31", d["request"]["latest_closing_date"]
d["request"]["latest_closing_date"] = "2026-01-30"   # txn 2026-01-31 is now POST-closure
json.dump(d, open(p, "w"), indent=1); open(p, "a").write("\n")
PY
if run_arm "ARM B  LDG-REFUSE-04's latest_closing_date moved back one day (refusal -> accepting region)"; then
  echo "    *** THE ARM STAYED GREEN. It cannot see a refusal promoted into the accepting"
  echo "    *** region, which is the direction the arm it replaces could never see at all."
  rc=1
else
  echo "    OK: RED, and the message names the vector and the region"
fi
git -C "$REPO" checkout -- "$R4"
echo ""

echo "restored: $(git -C "$REPO" status --porcelain -- "$V7" "$R4" | wc -l | tr -d ' ') dirty vector file(s) (want 0)"
echo "T328 tripwire red-drive: EXIT $rc"
exit "$rc"
