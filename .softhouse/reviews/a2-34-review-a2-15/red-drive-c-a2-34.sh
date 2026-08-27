#!/bin/bash
# A2-34 RED DRIVES, PART C — the six registered WRONG ledger implementations,
# driven with the binary's real flags (-store / -oracle-probe / -ledger-impl).
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac008956278f2d6ea
cd "$R"
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export PATH="$GOROOT/bin:$PATH"
LOG=/tmp/a234-red; mkdir -p "$LOG"

echo "=== registered implementations"
/tmp/a234-conf -list-implementations 2>&1 | LC_ALL=C /usr/bin/grep -aF 'ledger'
echo

echo "=== CONTROL: the CORRECT ledger implementation on this route (anti-no-op)"
/tmp/a234-conf -store "$R/.softhouse/vectors" -oracle-probe up > "$LOG/c-correct.txt" 2>&1
echo "  exit=$?"
LC_ALL=C /usr/bin/grep -aE "^    ledger (parity|oracle-refusal|invariants)" "$LOG/c-correct.txt"
echo

for impl in ledger-wrong-truncating ledger-wrong-header-refusing ledger-wrong-manual-permission-ignored ledger-wrong-netting-totals ledger-wrong-code-ignored ledger-wrong-split-drift; do
  /tmp/a234-conf -store "$R/.softhouse/vectors" -oracle-probe up -ledger-impl "$impl" > "$LOG/c-$impl.txt" 2>&1
  ex=$?
  echo "--- $impl   exit=$ex"
  LC_ALL=C /usr/bin/grep -aE "^    ledger (parity|oracle-refusal)" "$LOG/c-$impl.txt"
  echo "    kills / invariant lines:"
  LC_ALL=C /usr/bin/grep -aE "MONEY want|VIOLATED|want \"|LDG-0[0-9].*(FAIL|PASS)" "$LOG/c-$impl.txt" | head -8
  echo
done
