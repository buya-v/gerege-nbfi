#!/bin/bash
# T362 — INDEPENDENT drive of adjudicate-section1.py in BOTH directions, end to end,
# by mutating the REAL obs/ bytes rather than feeding parse_verdict a fabricated string.
# T357's own controls (a) and (b) are pure-function tests on synthetic transcripts; this
# exercises check-shape.py -> adjudicate-section1.py -> run-all.sh for real.
#
# D3 is T362's own probe and is NOT a T357 control: it asks whether the corpus guard in
# adjudicate-section1.py section 4 can pass VACUOUSLY over an empty population.
set -u
# TARGET TREE. This script MUTATES the tree it is given and reverts with `git checkout --`.
# It is passed in rather than hard-coded, and there is NO default, because a mutation
# script with a default target is one typo away from rewriting the live repo:
#     git clone --local --shared <repo> <tmp>
#     git -C <tmp> checkout main
#     git -C <tmp> merge softhouse/T357-a2-11-section1-red
#     git -C <tmp> branch -f softhouse/A2-7-capture-mandatory-accounts \
#           origin/softhouse/A2-7-capture-mandatory-accounts   # section 5 needs this ref
#     bash <this script> <tmp>
C="${1:?usage: $0 <path to a main+T357 checkout to operate on>}"
[ -d "$C/.git" ] || { echo "REFUSE: $C is not a git checkout" >&2; exit 9; }
A2="$C/.softhouse/reviews/A2-11"
ADJ="$A2/adjudicate-section1.py"
W="$(mktemp -d -t t362-drive)"
trap 'rm -rf "$W"' EXIT

banner() { echo; echo "=================================================================="; echo "$1"; echo "=================================================================="; }

banner "PRE: is the target tree clean?"
git -C "$C" status --porcelain -- .softhouse/ ; echo "(empty above == clean)"

# ---------------------------------------------------------------- DIRECTION 1: VANISHED
banner "DIRECTION 1 (THE DANGEROUS ONE) — make an adjudicated failure VANISH."
echo "Injecting the three fields as JSON null into the REAL product-46 observation, i.e."
echo "forging exactly the wire shape A2-7 fabricated. check-shape.py should then PASS the"
echo "three assertions, and the adjudicator MUST go RED for losing them."
python3 - "$A2/obs/a2-11-get-loanproduct-46.json" <<'PY'
import collections, json, sys
p = sys.argv[1]
d = json.loads(open(p, 'rb').read().decode(), object_pairs_hook=collections.OrderedDict)
for k in ("paymentChannelToFundSourceMappings", "feeToIncomeAccountMappings",
          "penaltyToIncomeAccountMappings"):
    assert k not in d, "PRECONDITION FAILED: %s already present" % k
    d[k] = None
open(p, 'w').write(json.dumps(d))
print("  injected 3 null fields into %s" % p)
PY

echo "--- check-shape.py under the mutation ---"
python3 "$A2/check-shape.py" > "$W/d1-check.txt" 2>&1
echo "check-shape.py rc=$?   (0 here means section 1 now looks HEALTHY — the trap)"
grep -n "present and null" "$W/d1-check.txt"
grep -n "^FAILURES:" "$W/d1-check.txt"

echo "--- adjudicate-section1.py under the mutation ---"
python3 "$ADJ" > "$W/d1-adj.txt" 2>&1
D1=$?
echo "adjudicate-section1.py rc=$D1   (MUST be non-zero)"
grep -n "STILL PRESENT\|missing=\|exits 1 (RED)\|^FAILURES:\|^  - " "$W/d1-adj.txt" | head -20

echo "--- run-all.sh under the mutation ---"
bash "$A2/run-all.sh" > "$W/d1-runall.txt" 2>&1
R1=$?
echo "run-all.sh rc=$R1   (MUST be non-zero)"
sed -n '/VERDICT — every section/,$p' "$A2/TRANSCRIPT-A2-11.txt"

git -C "$C" checkout -- .softhouse/reviews/A2-11/
echo "reverted; porcelain:"; git -C "$C" status --porcelain -- .softhouse/reviews/A2-11/

# ------------------------------------------------------------- DIRECTION 2: FOURTH FAIL
banner "DIRECTION 2 — introduce a FOURTH, unadjudicated failure."
echo "Mutating GL account 2's observed name so a DIFFERENT section-1 assertion fails."
python3 - "$A2/obs/a2-11-get-glaccount-2.json" <<'PY'
import collections, json, sys
p = sys.argv[1]
d = json.loads(open(p, 'rb').read().decode(), object_pairs_hook=collections.OrderedDict)
assert d["name"] == "Fund Source", "PRECONDITION FAILED: name is %r" % d["name"]
d["name"] = "Fund Source RENAMED BY T362"
open(p, 'w').write(json.dumps(d))
print("  mutated glaccount-2 name in %s" % p)
PY

python3 "$A2/check-shape.py" > "$W/d2-check.txt" 2>&1
echo "check-shape.py rc=$?"
sed -n '/^FAILURES:/,$p' "$W/d2-check.txt"

python3 "$ADJ" > "$W/d2-adj.txt" 2>&1
D2=$?
echo "adjudicate-section1.py rc=$D2   (MUST be non-zero)"
grep -n "UNADJUDICATED\|unexpected=\|^FAILURES:\|^  - " "$W/d2-adj.txt" | head -20

bash "$A2/run-all.sh" > "$W/d2-runall.txt" 2>&1
R2=$?
echo "run-all.sh rc=$R2   (MUST be non-zero)"
sed -n '/VERDICT — every section/,$p' "$A2/TRANSCRIPT-A2-11.txt"

git -C "$C" checkout -- .softhouse/reviews/A2-11/

# ----------------------------------------------------- DIRECTION 3: VACUITY OF §4 CHECK
banner "DIRECTION 3 (T362's OWN probe) — can the CORPUS guard in section 4 pass VACUOUSLY?"
echo "Temporarily move .softhouse/vectors aside and re-run the adjudicator. If section 4"
echo "still reports 'all zero' and PASSES, the corpus guard has no positive control."
mv "$C/.softhouse/vectors" "$W/vectors-hidden-by-t362"
python3 "$ADJ" > "$W/d3-adj.txt" 2>&1
D3=$?
echo "adjudicate-section1.py with vectors/ HIDDEN rc=$D3"
sed -n '/=== 4\./,/=== 5\./p' "$W/d3-adj.txt"
mv "$W/vectors-hidden-by-t362" "$C/.softhouse/vectors"
git -C "$C" checkout -- .softhouse/
echo "restored; porcelain:"; git -C "$C" status --porcelain | head

banner "SUMMARY"
echo "D1 vanished-failure : adjudicate rc=$D1  run-all rc=$R1   (both MUST be non-zero)"
echo "D2 fourth-failure   : adjudicate rc=$D2  run-all rc=$R2   (both MUST be non-zero)"
echo "D3 vectors hidden   : adjudicate rc=$D3                   (0 == VACUOUS PASS, a gap)"
rc=0
[ "$D1" -ne 0 ] && [ "$R1" -ne 0 ] || { echo "  *** D1 DID NOT TRIP ***"; rc=1; }
[ "$D2" -ne 0 ] && [ "$R2" -ne 0 ] || { echo "  *** D2 DID NOT TRIP ***"; rc=1; }
echo
echo "T362 expects: D1 and D2 non-zero (T357's guard works), D3 zero (T357's guard has a"
echo "vacuity gap — finding F-2). This script exits non-zero if D1 or D2 fails to trip,"
echo "so a broken driver cannot be mistaken for a passing guard."
exit "$rc"
