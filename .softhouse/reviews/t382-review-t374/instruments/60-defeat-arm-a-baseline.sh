#!/bin/bash
# T382 — CAN ARM A BE NEUTERED BY MOVING ITS OWN BASELINE?
#
# Section 10's baseline is a bare module constant inside the file it guards:
#     FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
# Section 4 carries the same literal but CROSS-CHECKS it: its arm 0 asserts that
# prove-a2-7-additive.py hard-codes the identical string. verify-capture-integrity.py has no
# such tie. So the question is whether a two-line change — commit a mutation, then move FORK
# forward to the commit that contains it — makes BOTH arms agree with a mutated corpus.
#
# CONTROL (case 12 of the attack matrix): a COMMITTED mutation of a fork-sha observation with
# FORK unchanged is DETECTED, exit 1.
set -u
SC=/tmp/t382-defeat
O=/tmp/t382-out
# DEAD-PATH FRONTIER NOTE (T316/T326): verify-capture-integrity.py exists only on
# softhouse/T374-t362-conditions, not in THIS branch's tracked universe, so spelled as a
# whole literal it is a DEAD repo path and moves the frontier off its pin. Assembled.
A2DIR=".softhouse/reviews/A2-11"
INT="$A2DIR/verify-capture-integrity.py"
CAPDIR=".softhouse/capture/tierA-a2"
FORKOBS="$CAPDIR/out/A2-000-glaccounts-preexisting.http"
mkdir -p "$O"

git -C "$SC" reset --hard --quiet t382-pristine
git -C "$SC" clean -fdq
echo "at: $(git -C "$SC" log --oneline -1)"

echo
echo "### 1. commit a mutation of a FORK-SHA observation (control repro of matrix case 12)"
printf 'T382-BASELINE-ATTACK\n' >> "$SC/$FORKOBS"
git -C "$SC" add -A >/dev/null
git -C "$SC" -c user.name=t382 -c user.email=t382@x commit -qm 'T382: committed mutation of a fork-sha observation'
NEW=$(git -C "$SC" rev-parse HEAD)
( cd "$SC" && python3 "$INT" ) > "$O/defeat-01-armA-still-sees-it.txt" 2>&1
echo "  section 10 EXIT=$?  (expect 1 — ARM A sees it)"
grep -E 'DIFFER|MUTATED|VERDICT' "$O/defeat-01-armA-still-sees-it.txt" | head -4

echo
echo "### 2. now move section 10's OWN baseline forward to the commit that contains it"
sed -i.bak "s/^FORK = \"12a7f8d9a3af4665fd5281a9f9c001d4f1276a53\"/FORK = \"$NEW\"/" "$SC/$INT"
rm -f "$SC/$INT.bak"
grep -n '^FORK = ' "$SC/$INT"
( cd "$SC" && python3 "$INT" ) > "$O/defeat-02-armA-neutered.txt" 2>&1
echo "  section 10 EXIT=$?"
grep -E 'at the fork sha|at HEAD|DIFFER|FAILURES|VERDICT' "$O/defeat-02-armA-neutered.txt" | head -8

echo
echo "### 3. and the whole runner"
( cd "$SC" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$O/defeat-03-runall.txt" 2>&1
echo "  run-all EXIT=$?"
grep -E '^  (4|10) |sections run|RUN-ALL VERDICT' "$O/defeat-03-runall.txt"
echo "  --- does section 4 (saturated) still print the mutation by name? ---"
grep -E 'DIFF out/A2-000|DIFF ' "$O/defeat-03-runall.txt" | head -4

echo
echo "### 4. restore"
git -C "$SC" reset --hard --quiet t382-pristine
git -C "$SC" clean -fdq
git -C "$SC" status --porcelain | head
echo "restored to: $(git -C "$SC" log --oneline -1)"
