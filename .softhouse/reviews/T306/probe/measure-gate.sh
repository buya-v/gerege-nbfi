#!/bin/bash
# T306 — THE THREE-PREDICATE MATRIX.
#
# The same nine probe vectors, plus the four COMMITTED vectors that claim the
# row, graded against THREE versions of the capability gate:
#
#   D  the DRIVER's merged predicate      (command || code || code)
#   N  T306's FIRST-PASS narrowing        (kind=="refusal" && (command || dates))
#   A  the ADJUDICATED predicate          (command || (kind=="refusal" && dates))
#
# ARM N is the one T320 blocked: it makes LDG-05 INADMISSIBLE and brings the
# mutant `ledger-wrong-openingbalance-always-refusing` (T296 arm A) back to
# life. This script is the measurement of that claim, not a restatement of it.
#
# The store is COPIED to scratch and admit.go is patched IN PLACE and RESTORED
# from git, with the restore VERIFIED by re-reading the file's hash rather than
# by printing a literal. Nothing under .softhouse/vectors is touched and no
# request reaches the reference oracle.
set -uo pipefail
W="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
. "$W/.softhouse/bin/go-env.sh"

ADMIT="$W/nexus/internal/apps/ledger/conformance/admit.go"
BEFORE=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t306-matrix.XXXXXXXX") || exit 1
cp -R "$W/.softhouse/vectors" "$SCRATCH/vectors" || exit 1
python3 "$W/.softhouse/reviews/T306/probe/build-probes.py" "$SCRATCH/vectors" || exit 1
echo

restore() {
  git -C "$W" checkout -- "$ADMIT"
  local now
  now=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
  echo "T306-RESTORE: before=${BEFORE:0:12} after=${now:0:12} restored=$([ "$BEFORE" = "$now" ] && echo 1 || echo 0)"
}
trap restore EXIT

run_arm() {
  local label="$1"
  cd "$W/nexus" || exit 1
  if ! go build -o "$SCRATCH/conf-$label" ./internal/apps/loanschedule/conformance/cmd/conformance 2>"$SCRATCH/build-$label.err"; then
    echo "ARM $label DID NOT COMPILE:"; cat "$SCRATCH/build-$label.err"; return 1
  fi
  "$SCRATCH/conf-$label" -oracle-probe=up -context=ledger -repo-root="$W" \
    -store="$SCRATCH/vectors" > "$SCRATCH/run-$label.txt" 2>&1
  echo "  binary exit=$?"
  echo
  echo "  --- verdict per vector ---"
  grep -E "^ +(ZZZ-T306|LDG-)" "$SCRATCH/run-$label.txt" | sed 's/^/  /'
  echo
  echo "  --- census ---"
  grep -E "^ +ledger (parity|oracle-refusal|inadmissible|cells compared)" "$SCRATCH/run-$label.txt" | sed 's/^/  /'
  echo
  echo "  --- WHICH RULE refused WHICH vector (the attribution, not the verdict) ---"
  python3 "$W/.softhouse/reviews/T306/probe/extract-reasons.py" \
      "$SCRATCH/run-$label.txt" "$label" | sed 's/^/  /'
  echo
}

echo "=============================================================="
echo "ARM A — THE ADJUDICATED PREDICATE (this branch, as committed)"
echo "=============================================================="
run_arm A

echo "=============================================================="
echo "ARM D — THE DRIVER'S MERGED PREDICATE, put back"
echo "=============================================================="
python3 - "$ADMIT" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = """		observedShape := openingBalanceCommand ||
			(v.Expect.Kind == "refusal" && (preClosureInputs || futureDatedInputs))"""
new = """		_, _ = preClosureInputs, futureDatedInputs
		observedShape := openingBalanceCommand ||
			v.Expect.Refusal.Code == codeAccountingClosed ||
			v.Expect.Refusal.Code == codeFutureDate"""
assert s.count(old) == 1, "the adjudicated predicate is not where this probe expects it"
open(p, "w").write(s.replace(old, new))
print("  patched admit.go -> the DRIVER's predicate")
PY
run_arm D
git -C "$W" checkout -- "$ADMIT"

echo "=============================================================="
echo "ARM N — T306's FIRST-PASS NARROWING (kind==refusal on ALL arms)"
echo "         This is the arm T320 blocked. Watch LDG-05."
echo "=============================================================="
python3 - "$ADMIT" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = """		observedShape := openingBalanceCommand ||
			(v.Expect.Kind == "refusal" && (preClosureInputs || futureDatedInputs))"""
new = """		observedShape := v.Expect.Kind == "refusal" &&
			(openingBalanceCommand || preClosureInputs || futureDatedInputs)"""
assert s.count(old) == 1, "the adjudicated predicate is not where this probe expects it"
open(p, "w").write(s.replace(old, new))
print("  patched admit.go -> T306's FIRST-PASS narrowing")
PY
run_arm N

echo "scratch: $SCRATCH"
