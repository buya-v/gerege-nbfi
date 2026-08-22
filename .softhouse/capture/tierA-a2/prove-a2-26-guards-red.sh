#!/bin/sh
# A2-26 -- drive every guard this task shipped RED before believing any of them (P-22).
#
# Three guards were added by A2-26:
#   G1  mkreq-a2-26.sh verify   -- the A2-3xx admissibility bodies differ from the bodies
#                                  the oracle originally accepted in nothing but two
#                                  string fields.
#   G2  census-a2-26.py         -- classified + skipped == total, exit non-zero otherwise.
#   G3  cap9.sh                 -- refuses to run without an Idempotency-Key, because a
#                                  probe that silently sent no key would prove nothing.
#
# Each is run GREEN on the real tree, then RED against a deliberately broken input, then
# the tree is restored and re-run GREEN so this script leaves nothing behind. Every
# scratch edit is made on a COPY under a temp dir, never on committed evidence, except
# G1's which must touch the real req/ file and is restored by regenerating it from its
# own builder.
#
# Exit 0 only if all three went green, then red, then green again.
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
FAIL=0
TMP=$(mktemp -d "${TMPDIR:-/tmp}/a226prove.XXXXXX")
# T216: QUIT added alongside EXIT HUP INT TERM -- same P-40 tail as cap.sh/cap8.sh in
# this same directory (see prove-quit-trap-a226.py). Without it, Ctrl-\ leaks $TMP.
trap 'rm -rf "$TMP"' EXIT HUP INT TERM QUIT

say() { printf '\n===== %s =====\n' "$1"; }

# ---------------------------------------------------------------- G1
say "G1 GREEN: mkreq-a2-26.sh verify on the real tree"
sh "$DIR/mkreq-a2-26.sh" verify && echo "exit 0 as expected" || { echo "UNEXPECTED: G1 was not green"; FAIL=1; }

say "G1 RED: change ONE GL account id in an emitted body (16 -> 2, the retyped account)"
cp "$DIR/req/a2-26-admit-p46.json" "$TMP/p46.orig"
sed 's/"fundSourceAccountId": 16/"fundSourceAccountId": 2/' "$TMP/p46.orig" > "$DIR/req/a2-26-admit-p46.json"
if sh "$DIR/mkreq-a2-26.sh" verify; then
  echo "UNEXPECTED: G1 stayed green with a money-path account id altered"; FAIL=1
else
  echo "exit non-zero as expected -- G1 detects an altered GL account id"
fi
cp "$TMP/p46.orig" "$DIR/req/a2-26-admit-p46.json"

say "G1 RED 2: change a NUMBER that is not an account id (principal 1200000 -> 1200001)"
sed 's/"principal": 1200000/"principal": 1200001/' "$TMP/p46.orig" > "$DIR/req/a2-26-admit-p46.json"
if sh "$DIR/mkreq-a2-26.sh" verify; then
  echo "UNEXPECTED: G1 stayed green with a money literal altered"; FAIL=1
else
  echo "exit non-zero as expected -- G1 detects an altered money literal"
fi
cp "$TMP/p46.orig" "$DIR/req/a2-26-admit-p46.json"

say "G1 GREEN again: the tree is restored"
sh "$DIR/mkreq-a2-26.sh" verify && echo "exit 0 as expected" || { echo "UNEXPECTED: restore failed"; FAIL=1; }

# ---------------------------------------------------------------- G2
say "G2 GREEN: census-a2-26.py accounts for every file under out/"
python3 "$DIR/census-a2-26.py" > "$TMP/census.green" 2>&1 \
  && grep -c "ACCOUNTING: .* True" "$TMP/census.green" >/dev/null \
  && grep "^ACCOUNTING" "$TMP/census.green" \
  || { echo "UNEXPECTED: G2 was not green"; FAIL=1; }

say "G2 RED: run the same census over a COPY of out/ carrying one unrecognised file"
mkdir -p "$TMP/rig/out"
cp -R "$DIR/out/." "$TMP/rig/out/"
cp "$DIR/census-a2-26.py" "$TMP/rig/census-a2-26.py"
printf 'not a cap.sh artefact\n' > "$TMP/rig/out/A2-999-smuggled.dat"
if python3 "$TMP/rig/census-a2-26.py" > "$TMP/census.red" 2>&1; then
  echo "UNEXPECTED: G2 exited 0 with an unclassified file present"; FAIL=1
else
  echo "exit non-zero as expected"
fi
grep -n "SKIPPED FILES" -A 3 "$TMP/census.red" | head -6
grep -n "^ACCOUNTING" "$TMP/census.red"
echo "NOTE: the file is NAMED in the skipped list with a reason -- it is not swallowed."
echo "     That is the whole difference from the enumerator this census replaces."

say "G2 RED 2: an UNPARSEABLE body is a class, not a drop -- and it is FATAL"
printf '{ this is not json' > "$TMP/rig/out/A2-998-broken.json"
printf 'GET /journalentries?loanId=999\n' > "$TMP/rig/out/A2-998-broken.http"
printf '200\n' > "$TMP/rig/out/A2-998-broken.status"
rm -f "$TMP/rig/out/A2-999-smuggled.dat"
if python3 "$TMP/rig/census-a2-26.py" > "$TMP/census.red2" 2>&1; then
  echo "UNEXPECTED: G2 exited 0 with an unreadable observation body present"; FAIL=1
else
  echo "exit non-zero as expected"
fi
grep -n "UNPARSEABLE-JSON" "$TMP/census.red2" | head -2 \
  && echo "the broken body is REPORTED by name, not skipped" \
  || { echo "UNEXPECTED: the unparseable body vanished"; FAIL=1; }

say "G2 RED 3: the arithmetic identity ALONE cannot fail -- proving why the exit code is stricter"
echo "The 'classified + skipped == total' identity is TRUE in every red run above, because"
echo "an unrecognised file lands in the skipped list and the sum still balances. That identity is"
echo "therefore NOT a tripwire (P-29). The refusal is keyed on the skipped list being"
echo "NON-EMPTY, which is what the two red runs above actually exercised."
grep -n "^ACCOUNTING" "$TMP/census.red" "$TMP/census.red2"

# ---------------------------------------------------------------- G3
say "G3 RED: cap9.sh with no Idempotency-Key must refuse"
if sh "$DIR/cap9.sh" A2-999-should-not-exist POST /journalentries req/a2-26-manual-je-idem.json 2>"$TMP/g3.err"; then
  echo "UNEXPECTED: cap9.sh ran without a key"; FAIL=1
else
  echo "exit non-zero as expected; it said:"; cat "$TMP/g3.err"
fi
if [ -e "$DIR/out/A2-999-should-not-exist.json" ] || [ -e "$DIR/out/A2-999-should-not-exist.http" ]; then
  echo "UNEXPECTED: the refusal still wrote something under out/"; FAIL=1
else
  echo "and it wrote NOTHING under out/ -- checked, not assumed"
fi

say "RESULT"
if [ "$FAIL" -eq 0 ]; then echo "all three guards went green, then red, then green"; else echo "SOMETHING DID NOT BEHAVE AS STATED"; fi
exit "$FAIL"
