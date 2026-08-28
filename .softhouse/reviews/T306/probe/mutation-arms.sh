#!/bin/bash
# T306 — RED-DRIVE. P-22: "A guard, a canary, or a control that cannot fail is
# worse than none — because it is believed."
#
# Every arm this task added or kept is run against a MUTANT admit.go written to
# defeat it. An arm that stays GREEN against the code it was written to catch is
# not a control, and T320-3 recorded that T305's two leg rules shipped with no
# arm at all.
#
# admit.go is patched IN PLACE and RESTORED FROM GIT after every mutant, and the
# restore is verified by RE-READING the file's hash rather than by printing a
# literal. If the final line does not read restored=1, the worktree is dirty and
# the run must not be believed.
set -uo pipefail
W="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
. "$W/.softhouse/bin/go-env.sh"
ADMIT="$W/nexus/internal/apps/ledger/conformance/admit.go"
BEFORE=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)

restore() {
  git -C "$W" checkout -- "$ADMIT"
  local now
  now=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
  echo
  echo "T306-RESTORE: before=${BEFORE:0:12} after=${now:0:12} restored=$([ "$BEFORE" = "$now" ] && echo 1 || echo 0)"
}
trap restore EXIT

# mutate <label> <description> <python-heredoc-on-stdin>
mutate() {
  local label="$1" desc="$2"
  echo "=============================================================="
  echo "MUTANT $label — $desc"
  echo "=============================================================="
  git -C "$W" checkout -- "$ADMIT"
  if ! python3 - "$ADMIT"; then
    echo "  MUTATION DID NOT APPLY — the anchor moved. This arm proves nothing."
    return 1
  fi
  cd "$W/nexus" || return 1
  go test ./internal/apps/ledger/conformance/ \
      -run 'TestOpeningBalance(CapabilityIsScopedToTheObservedShape|LegPairingIsRedDrivable|InputsAreDefaultDeny)' \
      2>&1 | grep -E '^(    --- |--- |ok|FAIL|PASS)' | sed 's/^/  /'
  echo
}

mutate D "the DRIVER's predicate: two arms keyed on expect.refusal.code" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
old = """		observedShape := openingBalanceCommand ||
			(v.Expect.Kind == "refusal" && (preClosureInputs || futureDatedInputs))"""
new = """		_, _ = preClosureInputs, futureDatedInputs
		observedShape := openingBalanceCommand ||
			v.Expect.Refusal.Code == codeAccountingClosed ||
			v.Expect.Refusal.Code == codeFutureDate"""
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
print("  applied")
PY

mutate N "T306's FIRST-PASS narrowing: kind==refusal in front of ALL THREE arms" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
old = """		observedShape := openingBalanceCommand ||
			(v.Expect.Kind == "refusal" && (preClosureInputs || futureDatedInputs))"""
new = """		observedShape := v.Expect.Kind == "refusal" &&
			(openingBalanceCommand || preClosureInputs || futureDatedInputs)"""
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
print("  applied")
PY

mutate W "the OVER-WIDENING: drop the refusal precondition from the DATE arms too" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
old = """		observedShape := openingBalanceCommand ||
			(v.Expect.Kind == "refusal" && (preClosureInputs || futureDatedInputs))"""
new = """		observedShape := openingBalanceCommand || preClosureInputs || futureDatedInputs"""
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
print("  applied")
PY

mutate L "the LENGTH rule relaxed: an accepted opening balance stores len(legs), not 2*len(legs)" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
old = """		if obAcceptingLegs {
			want = 2 * len(v.Request.Legs)
		}"""
new = """		if obAcceptingLegs {
			want = len(v.Request.Legs)
		}"""
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
print("  applied")
PY

mutate M "the MULTISET rule switched off entirely" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
old = "	if obAcceptingLegs && len(v.Expect.Legs) > 0 {\n		count := map[string]int{}"
new = "	if false && obAcceptingLegs && len(v.Expect.Legs) > 0 {\n		count := map[string]int{}"
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
print("  applied")
PY

mutate S "the SURPLUS guard reverted to T305's  left != 0  — a shortfall reported as a negative surplus" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
old = "			if left > 0 {\n				surplus = append(surplus, text)"
new = "			if left != 0 {\n				surplus = append(surplus, text)"
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
print("  applied")
PY

mutate O "the SORT removed — T305's map-iteration order restored" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
old = "		sort.Strings(surplus)\n"
assert s.count(old) == 1
s = s.replace(old, "")
# `sort` stays imported elsewhere in the file; if not, keep the build honest.
open(p, "w").write(s)
print("  applied")
PY
