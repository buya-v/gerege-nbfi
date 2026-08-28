#!/bin/bash
# T428 -- adjudicate T421's ELEVENTH-BRANCH claim by DELETING the branch, not by
# mangling its message.
#
# T421: `product_mappings[i].gl_account_id <= 0` `continue`s past the off-the-chart
# check, "so without a drive a regression there REPORTS THE WRONG REASON". Delete
# the whole branch and the same fixture should still be REFUSED -- but by the
# OFF-THE-CHART reason. That is the claim, and this is the measurement of it.
set -u
tree="$1"; out="$2"
ADMIT="$tree/nexus/internal/apps/ledger/conformance/admit.go"
BACKUP=$(mktemp)
cp "$ADMIT" "$BACKUP"
BEFORE=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
restore() {
  cp "$BACKUP" "$ADMIT"
  AFTER=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
  [ "$BEFORE" = "$AFTER" ] || { echo "*** RESTORE FAILED" >&2; exit 9; }
  echo "admit.go RESTORED byte-for-byte ($AFTER)" >> "$out"
  rm -f "$BACKUP"
}
trap restore EXIT

{
  echo "T428 ARM-11 BRANCH-DELETION DRIVE -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "admit.go sha256: $BEFORE"
} > "$out"

python3 - "$ADMIT" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()
BRANCH = '''			if m.GLAccountID <= 0 {
				add("request.product_mappings[%d].gl_account_id is %d", i, m.GLAccountID)
				continue
			}
'''
if t.count(BRANCH) != 1:
    raise SystemExit("branch not found exactly once (%d) -- drive would be vacuous" % t.count(BRANCH))
open(p, "w").write(t.replace(BRANCH, ""))
print("ELEVENTH BRANCH DELETED (4 lines).")
PY

go test -C "$tree/nexus" -count=1 -run TestSlotAdmissionInputsAreDefaultDeny -v \
  ./internal/apps/ledger/conformance/ > /tmp/t428-arm11.txt 2>&1
rc=$?
{
  echo "go test exit: $rc"
  LC_ALL=C grep -E '^ *--- (PASS|FAIL): TestSlotAdmission' /tmp/t428-arm11.txt
  echo
  echo "--- what arm 11 saw with the branch GONE ---"
  LC_ALL=C sed -n '/11\._a_mapping_row_with_a_NON-POSITIVE/,/^ *--- /p' /tmp/t428-arm11.txt | head -20
  LC_ALL=C grep -n 'ADMITTED, or refused for a DIFFERENT reason' -A 3 /tmp/t428-arm11.txt | head -20
} >> "$out"
cat "$out"
