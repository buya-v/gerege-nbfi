#!/bin/bash
# T306 — P-22 red-drive. A control that cannot fail is worse than none.
#
# Restores the DRIVER'S merged predicate into admit.go, runs T306's new test
# arms against it, then RESTORES admit.go from the commit and PROVES the restore
# by re-reading the file. If the arms do not go RED under the driver's
# predicate, they are not testing what this review says they test.
#
# admit.go is COMMITTED before this runs, so `git checkout --` restores it
# byte-exactly. The restore is in an EXIT trap and is re-verified afterwards
# rather than claimed (T271/T293's lesson: a probe that PRINTS "restored" from a
# literal has measured nothing).
set -uo pipefail
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-acee94120db93ffce
. "$W/.softhouse/bin/go-env.sh"
A="$W/nexus/internal/apps/ledger/conformance/admit.go"
REL=nexus/internal/apps/ledger/conformance/admit.go
TEST=TestOpeningBalanceCapabilityIsScopedToTheObservedShape

cd "$W" || exit 1
if ! git diff --quiet -- "$REL"; then
  echo "REFUSING: $REL is already dirty; commit it first or the restore is not a restore."
  exit 2
fi
BEFORE=$(shasum -a 256 "$A" | cut -d' ' -f1)
restore() { git -C "$W" checkout -- "$REL"; }
trap restore EXIT

run_arm() {
  cd "$W/nexus" || exit 1
  go test ./internal/apps/ledger/conformance/ -run "$TEST" -v 2>&1 |
    grep -E '^(=== RUN|    --- (PASS|FAIL)|--- (PASS|FAIL)|ok|FAIL|PASS)|was ADMITTED by the capability|bought the capability claim' |
    sed 's/^/  /'
  cd "$W" || exit 1
}

echo "=============================================================="
echo "ARM N — T306's narrowing, as committed"
echo "=============================================================="
run_arm

echo
echo "=============================================================="
echo "ARM D — the DRIVER'S merged predicate put back"
echo "=============================================================="
python3 - "$A" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
narrowed = '''		observedShape := v.Expect.Kind == "refusal" &&
			(v.Request.Command == "defineOpeningBalance" ||
				(v.Request.LatestClosingDate != "" && v.Request.TransactionDate != "" &&
					!isoBefore(v.Request.LatestClosingDate, v.Request.TransactionDate)) ||
				(v.Request.TransactionDate != "" && v.Request.BusinessDate != "" &&
					isoAfter(v.Request.TransactionDate, v.Request.BusinessDate)))
'''
driver = '''		observedShape := v.Request.Command == "defineOpeningBalance" ||
			v.Expect.Refusal.Code == codeAccountingClosed ||
			v.Expect.Refusal.Code == codeFutureDate
'''
if narrowed not in s:
    sys.stderr.write("MUTATION TARGET NOT FOUND — this arm proves nothing.\n")
    sys.exit(2)
open(p, "w").write(s.replace(narrowed, driver))
print("reverted observedShape to the driver's merged predicate")
PY
if [ $? -ne 0 ]; then echo "mutation failed"; exit 2; fi
run_arm

restore
trap - EXIT
AFTER=$(shasum -a 256 "$A" | cut -d' ' -f1)
echo
echo "T306-RESTORE: before=$BEFORE after=$AFTER restored=$([ "$BEFORE" = "$AFTER" ] && echo 1 || echo 0)"
git -C "$W" status --porcelain -- "$REL"
