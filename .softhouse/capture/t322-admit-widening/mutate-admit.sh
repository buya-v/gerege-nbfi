#!/usr/bin/env bash
# T322 -- THE RED DRIVE FOR admit.go's OPENING-BALANCE LEG RULES.
#
# WHAT THIS IS FOR. T305 added two admissibility rules to `admit.go` (the
# 2*len(legs) LENGTH rule and the MULTISET amount pairing) and drove the PORT
# red, not the RULES. T320-3/T320-3b then found a hole and two defects in them,
# and T306 fixed all three -- in code, asserted by nothing. A rule with no red
# arm is a rule nobody has seen fail.
#
# So every arm this program now owns over those rules is driven here, by MUTATING
# THE RULE AND DEMANDING THE ARM GO RED. An arm that stays green under its own
# mutant is not evidence; it is decoration.
#
# WHAT IT NEVER DOES: it does not contact the reference oracle, it does not read
# or write any Fineract instance, and it does not touch a vector. It edits ONE
# file in place, runs `go test`, and restores that file byte for byte -- the
# restore is CHECKED against a sha256 taken before the first mutation and a
# mismatch is a hard exit, because a harness that can leave a money gate mutated
# is worse than no harness.
#
# USAGE:  bash .softhouse/capture/t322-admit-widening/mutate-admit.sh
#         (bash, never sh/zsh/dash -- this file uses arrays and `local`.)
#
# EXIT: 0 every mutant DIED (its arm went red) and the file was restored.
#       1 a mutant SURVIVED, or an arm was red before any mutation.
#       2 a dependency is missing, a mutation did not apply, or the RESTORE
#         FAILED. Fail-closed: "if I cannot reach what I grade, I have not
#         graded it."

set -u

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 2

TARGET="nexus/internal/apps/ledger/conformance/admit.go"
PKG="./internal/apps/ledger/conformance/"
OUT="$REPO_ROOT/.softhouse/capture/t322-admit-widening/out"
mkdir -p "$OUT" || exit 2

[ -f "$TARGET" ] || { echo "T322-MUTATE: MISSING $TARGET"; exit 2; }
[ -f "$REPO_ROOT/.softhouse/bin/go-env.sh" ] || { echo "T322-MUTATE: MISSING .softhouse/bin/go-env.sh"; exit 2; }

# shellcheck source=/dev/null
. "$REPO_ROOT/.softhouse/bin/go-env.sh" >/dev/null 2>&1
command -v go >/dev/null 2>&1 || { echo "T322-MUTATE: no go toolchain"; exit 2; }

sha() { shasum -a 256 "$1" | awk '{print $1}'; }

BEFORE="$(sha "$TARGET")"
BACKUP="$(mktemp)"
cp "$TARGET" "$BACKUP" || exit 2

restore() {
  cp "$BACKUP" "$TARGET"
  local after
  after="$(sha "$TARGET")"
  if [ "$after" != "$BEFORE" ]; then
    echo "T322-MUTATE: RESTORE FAILED before=$BEFORE after=$after -- $TARGET IS MUTATED ON DISK"
    exit 2
  fi
}
trap 'restore' EXIT

# run_arms <label> <-run regex> <outfile>  -> prints PASS/FAIL, returns go's code
run_arms() {
  local label="$1" re="$2" file="$3"
  ( cd "$REPO_ROOT/nexus" && go test "$PKG" -run "$re" -count=1 ) >"$file" 2>&1
  local rc=$?
  echo "  [$label] go test rc=$rc  -> ${file#"$REPO_ROOT"/}"
  return $rc
}

# The arms, by the rule each one guards.
ARMS_HOLE='TestOpeningBalanceRefusalStillCrossChecksLegAmounts'
ARMS_ACCEPT='TestAcceptedOpeningBalanceIsNotPairedPOSITIONALLY'
ARMS_PAIRING='TestOpeningBalanceLegPairingIsRedDrivable'
ALL_ARMS="$ARMS_HOLE|$ARMS_ACCEPT|$ARMS_PAIRING"

fails=0

echo "=========================================================================="
echo "T322 RED DRIVE -- admit.go opening-balance leg rules"
echo "target : $TARGET"
echo "sha256 : $BEFORE  (before any mutation)"
echo "=========================================================================="
echo
echo "GREEN BASELINE -- every arm must PASS on the UNMUTATED file, or every RED"
echo "below could be red for a reason that has nothing to do with its mutant."
if ! run_arms "GREEN" "$ALL_ARMS" "$OUT/00-green-baseline.txt"; then
  echo "T322-MUTATE: THE ARMS ARE RED BEFORE ANY MUTATION. Nothing below means anything."
  sed -n '1,60p' "$OUT/00-green-baseline.txt"
  exit 1
fi
echo

# mutate <id> <name> <from> <to> <arm-regex> <expect-substring>
mutate() {
  local id="$1" name="$2" from="$3" to="$4" re="$5" want="$6"
  local file="$OUT/$id.txt"
  echo "--------------------------------------------------------------------------"
  echo "MUTANT $id -- $name"
  echo "  FROM: $from"
  echo "  TO  : $to"

  python3 - "$TARGET" "$from" "$to" <<'PY'
import sys
p, frm, to = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p, encoding='utf-8').read()
n = s.count(frm)
if n != 1:
    print("MUTATION DID NOT APPLY: %d occurrences" % n)
    sys.exit(2)
open(p, 'w', encoding='utf-8').write(s.replace(frm, to))
PY
  if [ $? -ne 0 ]; then
    echo "  MUTATION FAILED TO APPLY -- the rule has moved and this drive no longer describes it."
    restore
    exit 2
  fi

  if run_arms "$id" "$re" "$file"; then
    echo "  *** MUTANT $id SURVIVED. The arm did not fire. ***"
    fails=$((fails + 1))
  else
    if grep -q -- "$want" "$file"; then
      echo "  MUTANT $id DIED, and for its OWN reason (matched: $want)"
    else
      echo "  *** MUTANT $id died for the WRONG REASON -- expected text absent: $want ***"
      sed -n '1,40p' "$file"
      fails=$((fails + 1))
    fi
  fi
  cp "$BACKUP" "$TARGET"
  echo
}

# ---------------------------------------------------------------------------
# ITEM 1 -- THE UNDECLARED WIDENING (T320-3), closed by T306's obAcceptingLegs.
# ---------------------------------------------------------------------------
# W1 restores T305's condition EXACTLY as it stood: positional pairing skipped
# for defineOpeningBalance REGARDLESS of expect.kind, while the multiset pairing
# that replaces it is still gated on kind != "refusal". That is the hole.
mutate W1 "the WIDENING itself -- positional gate keyed on the COMMAND alone (T305's shape)" \
  'if !obAcceptingLegs &&
			i < len(v.Request.Legs)' \
  'if v.Request.Command != "defineOpeningBalance" &&
			i < len(v.Request.Legs)' \
  "$ARMS_HOLE" \
  "gate and the multiset gate have stopped being complements"

# W2 is the OTHER direction: someone "simplifies" the exemption away and applies
# the positional rule to the accepting shape too. That withdraws LDG-05.
mutate W2 "the OVER-correction -- positional pairing applied to the ACCEPTING shape too" \
  'if !obAcceptingLegs &&
			i < len(v.Request.Legs)' \
  'if true &&
			i < len(v.Request.Legs)' \
  "$ARMS_ACCEPT" \
  "INADMISSIBLE"

# ---------------------------------------------------------------------------
# ITEM 2 -- T305's TWO RULES, neither of which shipped with a red arm.
# ---------------------------------------------------------------------------
mutate L "THE LENGTH RULE relaxed from 2*len(legs) to len(legs)" \
  'want = 2 * len(v.Request.Legs)' \
  'want = len(v.Request.Legs)' \
  "$ARMS_PAIRING" \
  "was ADMITTED on defineOpeningBalance, or"

mutate M "THE MULTISET RULE's surplus report switched off" \
  'if left > 0 {' \
  'if left > 0 && false {' \
  "$ARMS_PAIRING" \
  "ADMITTED by the multiset rule"

# ---------------------------------------------------------------------------
# ITEM 4 -- THE NEGATIVE COUNT. T305 reported every non-zero residue through the
# SURPLUS sentence, so a shortfall printed "-1 time(s) MORE than ... allows".
# ---------------------------------------------------------------------------
mutate S "THE NEGATIVE COUNT reintroduced -- shortfalls reported through the SURPLUS sentence" \
  'if left > 0 {' \
  'if left != 0 {' \
  "$ARMS_PAIRING" \
  "which is not a positive"

# ---------------------------------------------------------------------------
# ITEM 3 -- MAP-ITERATION NON-DETERMINISM. Go randomises map iteration order per
# range statement, so with two surplus amounts the REASON ORDER varied run to
# run. The arm evaluates the same vector 65 times.
# ---------------------------------------------------------------------------
mutate D "THE NON-DETERMINISM reintroduced -- the surplus report left unsorted" \
  '		sort.Strings(surplus)' \
  '		_ = sort.Strings // MUTANT D: the sort removed' \
  "$ARMS_PAIRING" \
  "is NOT order-stable"

echo "=========================================================================="
restore
trap - EXIT
echo "RESTORED: before=$BEFORE after=$(sha "$TARGET") restored=1"
if [ "$fails" -ne 0 ]; then
  echo "T322 RED DRIVE: $fails MUTANT(S) SURVIVED OR DIED FOR THE WRONG REASON -- EXIT 1"
  exit 1
fi
echo "T322 RED DRIVE: ALL 6 MUTANTS DIED, each matched by its own arm's own sentence -- EXIT 0"
exit 0
