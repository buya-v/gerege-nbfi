#!/bin/bash
# T296 — the Go tests for the ledger conformance package, plus a RED DRIVE of the
# new admissibility rule (the rule is deleted in a scratch copy and the test must
# go red; a rule nobody has seen refuse is a rule nobody has tested, P-22).
set -uo pipefail
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac0c499f54ea397f9
. "$W/.softhouse/bin/go-env.sh"
cd "$W/nexus" || exit 1

echo "=== GREEN ARM: go test ./internal/apps/ledger/... ==="
go test ./internal/apps/ledger/... 2>&1 | tail -20
echo
echo "=== RED DRIVE: T296's rule deleted, the test must FAIL ==="
cp internal/apps/ledger/conformance/admit.go /tmp/t296-admit-green.go
python3 - <<'PY'
import re
p = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac0c499f54ea397f9/nexus/internal/apps/ledger/conformance/admit.go"
s = open(p).read()
start = s.index('	for _, name := range v.CapabilitiesRequired {\n		if name != "ledger.opening.balance.and.closure" {')
end = s.index('	// G-09 / G-10 over the chart rows the vector supplies.', start)
open(p, "w").write(s[:start] + s[end:])
print("rule deleted from the working copy")
PY
go test ./internal/apps/ledger/conformance/ -run TestOpeningBalanceCapabilityIsScopedToTheObservedShape 2>&1 | tail -12
cp /tmp/t296-admit-green.go internal/apps/ledger/conformance/admit.go
echo
echo "=== rule restored; re-running the same test ==="
go test ./internal/apps/ledger/conformance/ -run TestOpeningBalanceCapabilityIsScopedToTheObservedShape 2>&1 | tail -5
