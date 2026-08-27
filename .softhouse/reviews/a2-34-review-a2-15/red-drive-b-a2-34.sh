#!/bin/bash
# A2-34 RED DRIVES, PART B.
# PART A established that `conformance.sh` REFUSES --ledger-impl / -ledger-impl
# ("conformance: unknown option"). The wrong-implementation kills are therefore
# reachable only by driving the Go binary directly, exactly as A2-15's handoff
# §10 disclosed for its own CASE 8. This part does that, and re-checks RD-8's
# exemption refusal against the LEDGER SECTION rather than against a stock line.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac008956278f2d6ea
cd "$R"
export GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go
export GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath
export GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache
export GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache
export PATH="$GOROOT/bin:$PATH"
V=.softhouse/vectors/ledger
LOG=/tmp/a234-red
mkdir -p "$LOG"

echo "=== 0. conformance.sh REFUSES the flag — quoted, not described"
bash .softhouse/conformance.sh --ledger-impl ledger-wrong-truncating 2>&1 | head -2
bash .softhouse/conformance.sh -ledger-impl ledger-wrong-truncating 2>&1 | head -2
echo

echo "=== 1. build the conformance binary"
cd nexus
go build -o /tmp/a234-conf ./internal/apps/loanschedule/conformance/cmd/conformance || exit 1
cd "$R"
echo "  built /tmp/a234-conf"
echo

echo "=== 2. the registered ledger implementations (-list style)"
/tmp/a234-conf -h 2>&1 | LC_ALL=C /usr/bin/grep -aF 'ledger' | head -20
echo
/tmp/a234-conf -list 2>&1 | LC_ALL=C /usr/bin/grep -aF 'ledger-impl' | head -20
echo

echo "=== 3. EVERY registered wrong ledger implementation, driven"
for impl in ledger-wrong-truncating ledger-wrong-header-refusing ledger-wrong-manual-permission-ignored ledger-wrong-netting-totals ledger-wrong-code-ignored ledger-wrong-split-drift; do
  /tmp/a234-conf -vectors .softhouse/vectors -ledger-impl "$impl" > "$LOG/impl-$impl.txt" 2>&1
  ex=$?
  echo "--- $impl  exit=$ex"
  LC_ALL=C /usr/bin/grep -aF "ledger parity" "$LOG/impl-$impl.txt" | head -2
  LC_ALL=C /usr/bin/grep -aF "ledger oracle-refusal" "$LOG/impl-$impl.txt" | head -1
  LC_ALL=C /usr/bin/grep -aE "MONEY want|INVARIANT double_entry_balances +VIOLATED|INVARIANT splits_sum_to_whole +VIOLATED|LDG-04 .*FAIL|FAIL " "$LOG/impl-$impl.txt" | head -6
  echo
done

echo "=== 4. the CORRECT implementation on the same route (anti-no-op)"
/tmp/a234-conf -vectors .softhouse/vectors > "$LOG/impl-correct.txt" 2>&1
echo "  exit=$?"
LC_ALL=C /usr/bin/grep -aF "ledger parity" "$LOG/impl-correct.txt" | head -2
echo

echo "=== 5. RD-8 RE-CHECK — a planted invariant_exemptions on a LEDGER vector:"
echo "        what does the LEDGER SECTION say, not the stock 'ADMITS NONE' line?"
F=$V/LDG-02-repayment-split-4leg-minor-units.json
python3 - "$F" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p))
d["invariant_exemptions"] = [{"invariant": "splits_sum_to_whole", "reason": "A2-34 RD-8b planted"}]
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
PY
LC_ALL=C /usr/bin/grep -c -aF 'A2-34 RD-8b planted' "$F"
bash .softhouse/conformance.sh > "$LOG/rd8b.txt" 2>&1; echo "  exit=$?"
LC_ALL=C /usr/bin/grep -n -aE "LDG-02.*(INADMISSIBLE|FAIL|PASS)|ledger inadmissible|ADMITS NONE|declares 1" "$LOG/rd8b.txt" | head -10
git checkout -- .softhouse/vectors/ledger
echo

echo "=== 6. RD-9 RE-CHECK — does the pinned population gate notice the ledger"
echo "        SECTION VANISHING ENTIRELY (all six deleted)?"
mkdir -p /tmp/a234-ledgerbak
cp $V/*.json /tmp/a234-ledgerbak/
rm -f $V/*.json
bash .softhouse/conformance.sh > "$LOG/rd10.txt" 2>&1; echo "  exit=$?"
LC_ALL=C /usr/bin/grep -n -aiE "LEDGER parity vectors|LEDGER money cells|NO LEDGER VECTOR|VERDICT" "$LOG/rd10.txt" | head -10
cp /tmp/a234-ledgerbak/*.json $V/
git status --porcelain .softhouse/vectors/ | head
echo
echo "=== 7. final control"
bash .softhouse/conformance.sh > "$LOG/controlB.txt" 2>&1; echo "  exit=$?"
LC_ALL=C /usr/bin/grep -aF "VERDICT: PASS" "$LOG/controlB.txt"
LC_ALL=C /usr/bin/grep -aF "ledger parity           PASS 4    FAIL 0" "$LOG/controlB.txt"
git status --porcelain .softhouse/vectors/ nexus/ | head
