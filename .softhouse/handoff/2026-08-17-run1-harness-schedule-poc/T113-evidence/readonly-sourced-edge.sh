#!/bin/bash
# T113 / T130 — the one DISCLOSED behaviour change of the F1 fix: the harness
# SOURCED into a shell where `_conformance_psub_line` is already readonly.
#
#   bash .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T113-evidence/readonly-sourced-edge.sh [harness]
#
# Exit 0 = every row behaved as required. Exit 1 = at least one did not, INCLUDING
# the case where the subject is missing.
#
# T130 ARMED THIS SCRIPT. T113 shipped it as seven lines that PRINTED an exit code
# and asserted nothing, so it exited 0 whatever the harness did — the P-22 shape
# ("a guard that cannot fail is worse than none, because it is believed"), raised by
# T121 as F-T121-2. The expectations below are now in code.
#
# WHAT IS BEING ASSERTED, and why each row is here:
#   [1] the subject exists — the F1 assignment is in the harness. Without it this
#       script would be measuring the pre-fix file and calling it the fix.
#   [2] sourced WITHOUT the readonly -> ADMITTED. This is the control. Without it,
#       "sourced -> refused" would be satisfied by a harness that refuses every
#       sourced invocation, which is a different and much worse thing.
#   [3] sourced WITH the readonly -> REFUSED at exit 3, and ZERO verdict tokens.
#       Fail-closed: exit 3 prints no verdict and cannot turn a red run green. The
#       outcome it replaces was an ADMISSION PRODUCED BY FORGERY, which can.
#   [4] the refusal names the probe rather than inventing a cause.
#
# DRIVEN RED (P-22): run it with the PRE-FIX bytes as the harness —
#   git show f2813c8d51199ef676eb2924ca180041d00242db:.softhouse/conformance.sh > /tmp/pre.sh
#   bash …/readonly-sourced-edge.sh /tmp/pre.sh
# Row [1] refuses (no F1 assignment) and row [3] fails with exit 0: pre-fix, the
# readonly shell was ADMITTED, by forgery rather than by evidence.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
HARNESS="${1:-$REPO_ROOT/.softhouse/conformance.sh}"
TOKEN="$(sed -n 's/^CONFORMANCE_PSUB_TOKEN="\(.*\)"$/\1/p' "$HARNESS" 2>/dev/null | head -1)"

pass=0; fail=0
ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; printf '        %s\n' "${2:-}"; }

[ -f "$HARNESS" ] || { printf 'T113 readonly-edge: no harness at %s — refusing to report anything.\n' "$HARNESS" >&2; exit 1; }
[ -n "$TOKEN" ]   || { printf 'T113 readonly-edge: no CONFORMANCE_PSUB_TOKEN in %s — INERT, exit 1.\n' "$HARNESS" >&2; exit 1; }

echo "T113/T130 — the harness sourced into a shell with _conformance_psub_line readonly"
echo "host bash: $(/bin/bash --version | head -1)"
echo "harness  : $HARNESS"
echo "token    : $TOKEN"
echo

# [1] subject present?
if grep -q '^      _conformance_psub_line=$' "$HARNESS"; then
  ok "[1] the F1 assignment is present — this IS the post-fix harness"
else
  bad "[1] the F1 assignment is NOT in $HARNESS" \
      "this script would be describing pre-fix behaviour as though it were the fix. Every row below is about a file that does not contain the change."
fi

# [2] CONTROL: sourced with no readonly must still be admitted.
/bin/bash -c '( . "$1" --help ) >/dev/null 2>&1; exit $?' _ "$HARNESS"
code=$?
if [ "$code" = 0 ]; then
  ok "[2] control: sourced WITHOUT the readonly -> ADMITTED (exit 0)"
else
  bad "[2] control: sourced WITHOUT the readonly" \
      "expected exit 0, got $code — the refusal in [3] would then not be about the readonly at all, and this script would be reporting a blanket refusal as a targeted one"
fi

# [3] the edge itself, plus its verdict-token count.
out="$(/bin/bash -c 'readonly _conformance_psub_line="$2"; ( . "$1" --help ) 2>&1' _ "$HARNESS" "$TOKEN")"
/bin/bash -c 'readonly _conformance_psub_line="$2"; ( . "$1" --help ) >/dev/null 2>&1; exit $?' _ "$HARNESS" "$TOKEN"
code=$?
tokens="$(printf '%s\n' "$out" | grep -cE 'VERDICT|PASS|FAIL')"
if [ "$code" = 3 ]; then
  ok "[3] sourced WITH _conformance_psub_line readonly -> REFUSED (exit 3)"
else
  bad "[3] sourced WITH _conformance_psub_line readonly" \
      "expected exit 3, got $code. Exit 0 here means the pre-fix behaviour: the readonly variable FORGED the token and a psub-dead shell would have been admitted on it."
fi
if [ "$tokens" -eq 0 ]; then
  ok "[3b] that refusal printed ZERO verdict tokens — it cannot turn a red run green"
else
  bad "[3b] verdict tokens on the refusal path" "$tokens found; a refusal must print no verdict at all"
fi

# [4] the diagnosis must name the probe, not invent a cause.
case "$out" in
  *"process-substitution probe did not deliver its token"*)
    ok "[4] the refusal names the probe and reports the observation" ;;
  *)
    bad "[4] refusal text" "did not contain 'process-substitution probe did not deliver its token'. First lines:
$(printf '%s\n' "$out" | head -3)" ;;
esac

echo
printf '%s\n' "$out" | head -3
echo
echo "======================================================================="
printf 'T113/T130 READONLY-SOURCED EDGE: %d passed, %d failed\n' "$pass" "$fail"
echo "======================================================================="
[ "$fail" -eq 0 ]
