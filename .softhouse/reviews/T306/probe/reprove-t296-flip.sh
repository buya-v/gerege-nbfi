#!/bin/bash
# T306 review probe, QUESTION 3 — is the capability gate still LOAD-BEARING
# after the merge?
#
# T296 proved it was by flipping ONE boolean and measuring the difference:
#
#     in_graded_domain FALSE  ->  INADMISSIBLE
#     in_graded_domain TRUE   ->  ADMITTED AND GRADED
#
# This re-runs that arm against the MERGED admit.go, over the THREE committed
# vectors that now claim the row (LDG-REFUSE-03/04/05) rather than over T296's
# scratch probe. If the two arms now read the same, the merge made the gate
# inert and the review that preceded it was silently undone.
#
# The store is COPIED to scratch. Nothing under .softhouse/vectors is touched
# and no request reaches the reference oracle.
set -uo pipefail
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-acee94120db93ffce
. "$W/.softhouse/bin/go-env.sh"

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t306-flip.XXXXXXXX") || exit 1
cp -R "$W/.softhouse/vectors" "$SCRATCH/vectors" || exit 1

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
grep -E "LDG-REFUSE-0[345].*(PASS|FAIL|INADMISSIBLE|REFUSED)" "$SCRATCH/armA.txt"
grep -E "^ *ledger (oracle-refusal|inadmissible)" "$SCRATCH/armA.txt"

echo
echo "=============================================================="
echo "ARM B — the SAME tree, in_graded_domain reverted to false"
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
grep -E "LDG-REFUSE-0[345].*(PASS|FAIL|INADMISSIBLE|REFUSED)" "$SCRATCH/armB.txt"
grep -E "^ *ledger (oracle-refusal|inadmissible)" "$SCRATCH/armB.txt"

echo
echo "scratch: $SCRATCH"
cp "$SCRATCH/armA.txt" "$W/.softhouse/reviews/T306/out/flip-armA-merged.txt"
cp "$SCRATCH/armB.txt" "$W/.softhouse/reviews/T306/out/flip-armB-reverted.txt"
