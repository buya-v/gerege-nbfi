#!/bin/bash
# T306, CHARTER QUESTION 3 — is the capability gate still LOAD-BEARING after the
# driver's merge, T305's edit and this task's re-keying?
#
# T296 proved it was by flipping ONE boolean and measuring the difference:
#
#     in_graded_domain FALSE  ->  INADMISSIBLE, the registry gate refuses
#     in_graded_domain TRUE   ->  ADMITTED AND GRADED, no complaint
#
# This re-runs that arm over the FOUR committed vectors that now claim the row --
# LDG-REFUSE-03, LDG-05, LDG-REFUSE-04, LDG-REFUSE-05 -- rather than over T296's
# scratch probe. If the two arms read the same, the gate is inert and every
# review that preceded it was silently undone.
#
# The store is COPIED to scratch. Nothing under .softhouse/vectors is touched and
# no request reaches the reference oracle.
set -uo pipefail
W="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
. "$W/.softhouse/bin/go-env.sh"

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t306-flip.XXXXXXXX") || exit 1
cp -R "$W/.softhouse/vectors" "$SCRATCH/vectors" || exit 1

cd "$W/nexus" || exit 1
go build -o "$SCRATCH/conf" ./internal/apps/loanschedule/conformance/cmd/conformance || exit 1

run_arm() {
  "$SCRATCH/conf" -oracle-probe=up -context=ledger -repo-root="$W" \
    -store="$SCRATCH/vectors" > "$SCRATCH/$1.txt" 2>&1
  echo "  binary exit=$?"
  grep -E "^ +LDG-(05|REFUSE-0[345])" "$SCRATCH/$1.txt" | sed 's/^/  /'
  grep -E "^ +ledger (parity|oracle-refusal|inadmissible|cells compared)" "$SCRATCH/$1.txt" | sed 's/^/  /'
}

echo "=============================================================="
echo "ARM A — the registry AS COMMITTED (in_graded_domain: true)"
echo "=============================================================="
run_arm armA

echo
echo "=============================================================="
echo "ARM B — the SAME tree, in_graded_domain reverted to FALSE"
echo "=============================================================="
python3 - "$SCRATCH/vectors/capabilities-ledger.json" <<'PY'
import json, sys
p = sys.argv[1]
with open(p) as fh:
    r = json.load(fh)
n = 0
for c in r["capabilities"]:
    if c["name"] == "ledger.opening.balance.and.closure":
        c["in_graded_domain"] = False
        n += 1
assert n == 1, "expected exactly one row named ledger.opening.balance.and.closure, found %d" % n
with open(p, "w") as fh:
    fh.write(json.dumps(r, indent=2) + "\n")
print("  reverted in_graded_domain -> false in the SCRATCH copy only")
PY
run_arm armB

echo
echo "scratch: $SCRATCH"
cp "$SCRATCH/armA.txt" "$W/.softhouse/reviews/T306/out/40-flip-armA-graded-true.txt"
cp "$SCRATCH/armB.txt" "$W/.softhouse/reviews/T306/out/41-flip-armB-graded-false.txt"
