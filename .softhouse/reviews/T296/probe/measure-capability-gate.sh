#!/bin/bash
# T296 review probe — TWO ARMS over the same probe vector.
#
#   ARM A  the MERGED registry (T294: ledger.opening.balance.and.closure
#          in_graded_domain = true)
#   ARM B  the same tree with ONLY that one boolean reverted to false
#
# Everything else is byte-identical: same binary, same probe vector, same store
# copy. The difference between the two arms is the whole measurement.
#
# The store is COPIED to a scratch directory. Nothing under .softhouse/vectors is
# touched, and no request is sent to the reference oracle.
set -uo pipefail
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac0c499f54ea397f9
. "$W/.softhouse/bin/go-env.sh"

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t296-capgate.XXXXXXXX") || exit 1
cp -R "$W/.softhouse/vectors" "$SCRATCH/vectors" || exit 1
cp "$W/.softhouse/reviews/T296/probe/LDG-REFUSE-04-PROBE-future-dated-entry.json" \
   "$SCRATCH/vectors/ledger/" || exit 1

cd "$W/nexus" || exit 1
go build -o "$SCRATCH/conf" ./internal/apps/loanschedule/conformance/cmd/conformance || exit 1

run_arm() {
  "$SCRATCH/conf" -oracle-probe=up -context=ledger -repo-root="$W" \
    -store="$SCRATCH/vectors" 2>&1
}

echo "=============================================================="
echo "ARM A — the MERGED registry (in_graded_domain: true)"
echo "=============================================================="
run_arm > "$SCRATCH/armA.txt" 2>&1
grep -E "PROBE|REFUSED|inadmissible|refused|ledger (parity|oracle-refusal)" "$SCRATCH/armA.txt" \
  | grep -viE "^ *(a refusal|the run)" | head -20

echo
echo "=============================================================="
echo "ARM B — the SAME probe vector, flip reverted to false"
echo "=============================================================="
python3 - "$SCRATCH/vectors/capabilities-ledger.json" <<'PY'
import json, sys
p = sys.argv[1]
with open(p) as fh:
    r = json.load(fh)
for c in r["capabilities"]:
    if c["name"] == "ledger.opening.balance.and.closure":
        c["in_graded_domain"] = False
with open(p, "w") as fh:
    fh.write(json.dumps(r, indent=2) + "\n")
print("reverted in_graded_domain -> false in the SCRATCH copy only")
PY
run_arm > "$SCRATCH/armB.txt" 2>&1
grep -E "PROBE|REFUSED|inadmissible|refused|ledger (parity|oracle-refusal)" "$SCRATCH/armB.txt" \
  | grep -viE "^ *(a refusal|the run)" | head -20

echo
echo "scratch: $SCRATCH"
cp "$SCRATCH/armA.txt" "$W/.softhouse/reviews/T296/out/capgate-armA-merged.txt"
cp "$SCRATCH/armB.txt" "$W/.softhouse/reviews/T296/out/capgate-armB-flip-reverted.txt"
