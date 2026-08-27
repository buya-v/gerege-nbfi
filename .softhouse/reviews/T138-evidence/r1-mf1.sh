#!/bin/sh
# T138 — INDEPENDENT re-derivation of T115's MF-1.  Written from scratch; T115's
# t115-drive-mf1.sh was NOT invoked and its transcripts were NOT read as evidence.
#
# Baselines are literal immutable shas (P-24), never a ref computed from main:
#   PRE  = ccf3c14171dea52bd044d81d5ca67aba8054b74c  (softhouse/T91-preconditions-copy tip)
#   POST = softhouse/T115-t91-microfixes tip, pinned below as a literal sha too.
set -u
PRE_SHA=ccf3c14171dea52bd044d81d5ca67aba8054b74c
POST_SHA=$1                     # literal sha, passed in by the caller
W=${2:?usage: r1-mf1.sh <post-sha> <workdir>}
PREV=$W/pre/.softhouse/capture/t91/verdict.sh
POSTV=$W/post/.softhouse/capture/t91/verdict.sh

echo "PRE  verdict.sh sha256: $(shasum -a 256 "$PREV"  | cut -c1-16)"
echo "POST verdict.sh sha256: $(shasum -a 256 "$POSTV" | cut -c1-16)"
echo "baseline commits: PRE=$PRE_SHA POST=$POST_SHA"
echo

# Refuse to compare the fix to itself.
if grep -q 'no EXIT= line' "$PREV"; then
  echo "ABORT: the PRE tree already contains MF-1 — this would compare the fix to itself." >&2
  exit 2
fi
grep -q 'no EXIT= line' "$POSTV" || { echo "ABORT: POST tree lacks MF-1." >&2; exit 2; }

BREACH='A2a-mutated-canary-gerege A2b-mutated-canary-default
A2c-crafted-canary-and-expectation-gerege A3a-swapped-canary-gerege
A3b-missing-canary A3c-no-canary A4a-expect-override-default
A4b-expect-override-gerege A5-helpful-correct-override A6-canary-is-a-directory'

mk_truncated() {   # $1 = dest dir
  rm -rf "$1"; mkdir -p "$1"
  cp "$W"/pre/.softhouse/capture/t91/out/prefix-livetwin-sh/*.txt "$1"/
  chmod -R u+w "$1"
  for b in $BREACH; do
    echo 'truncated, nothing was ever run' > "$1/$b.txt"
  done
}

echo "=============================================================="
echo "LEG 1 (RED, pre-MF-1): 10 of 13 transcripts are one content-free line"
echo "=============================================================="
mk_truncated "$W/red"
sh "$PREV" "$W/red"; echo "PRE_MF1_EXIT=$?"
echo

echo "=============================================================="
echo "LEG 2 (RED, post-MF-1): the SAME input"
echo "=============================================================="
mk_truncated "$W/red2"
sh "$POSTV" "$W/red2"; echo "POST_MF1_EXIT=$?"
echo "ERROR rows: $(sh "$POSTV" "$W/red2" 2>/dev/null | grep -c 'ERROR (no EXIT= line')"
echo

echo "=============================================================="
echo "LEG 3 (GREEN): the real PRE-fix transcripts, post-MF-1 scorer"
echo "=============================================================="
for d in prefix-livetwin-sh prefix-livetwin-bash prefix-copy-sh prefix-copy-bash; do
  rm -rf "$W/g-$d"; cp -R "$W/pre/.softhouse/capture/t91/out/$d" "$W/g-$d"; chmod -R u+w "$W/g-$d"
  echo "--- $d"
  sh "$POSTV" "$W/g-$d" | tail -12
  sh "$POSTV" "$W/g-$d" >/dev/null 2>&1; echo "EXIT=$?"
  echo "ADMITS count: $(sh "$POSTV" "$W/g-$d" 2>/dev/null | grep -c 'ADMITS')"
done
echo

echo "=============================================================="
echo "LEG 4 (GREEN): the real POST-fix transcripts, post-MF-1 scorer"
echo "=============================================================="
for d in postfix-livetwin-sh postfix-livetwin-bash postfix-copy-sh postfix-copy-bash t115-post-sh t115-post-bash; do
  [ -d "$W/post/.softhouse/capture/t91/out/$d" ] || continue
  rm -rf "$W/gp-$d"; cp -R "$W/post/.softhouse/capture/t91/out/$d" "$W/gp-$d"; chmod -R u+w "$W/gp-$d"
  sh "$POSTV" "$W/gp-$d" >/dev/null 2>&1
  echo "$d EXIT=$?  last: $(sh "$POSTV" "$W/gp-$d" 2>/dev/null | tail -1)"
done
echo

echo "=============================================================="
echo "LEG 5: does the SHAPE test create a FALSE error on any legitimate"
echo "       transcript?  Every committed transcript dir, both scorers."
echo "=============================================================="
for tree in pre post; do
  for d in "$W/$tree"/.softhouse/capture/t91/out/*/; do
    b=$(basename "$d")
    [ "$b" = happy ] && continue
    ls "$d"/A*.txt >/dev/null 2>&1 || continue
    rm -rf "$W/sh-$tree-$b"; cp -R "$d" "$W/sh-$tree-$b"; chmod -R u+w "$W/sh-$tree-$b"
    e=$(sh "$POSTV" "$W/sh-$tree-$b" 2>/dev/null | grep -c 'ERROR (no EXIT= line')
    echo "$tree/$b   false-ERROR rows: $e   (last lines all EXIT=?: $(for f in "$d"/A*.txt; do LC_ALL=C tail -1 "$f"; done | grep -cv '^EXIT=[0-9][0-9]*$'  ) non-conforming)"
  done
done
echo
echo "LEG 5b: the happy/ transcripts too (different shape, not scored by verdict.sh)"
for f in "$W"/post/.softhouse/capture/t91/out/happy/*.txt; do
  printf '%-52s last=%s\n' "$(basename "$f")" "$(LC_ALL=C tail -1 "$f")"
done
echo

echo "=============================================================="
echo "LEG 6: T107b's residual — a transcript whose last line is a BARE NUMERAL"
echo "=============================================================="
rm -rf "$W/bare"; cp -R "$W/pre/.softhouse/capture/t91/out/postfix-livetwin-sh" "$W/bare" 2>/dev/null \
  || cp -R "$W/post/.softhouse/capture/t91/out/postfix-livetwin-sh" "$W/bare"
chmod -R u+w "$W/bare"
# A2a expects BREACH; truncate it to a bare `5` — a non-zero "status" under the value test.
echo '5' > "$W/bare/A2a-mutated-canary-gerege.txt"
echo "--- value test only (T107's specified rule), emulated:"
last=$(LC_ALL=C tail -1 "$W/bare/A2a-mutated-canary-gerege.txt")
st=$(printf '%s\n' "$last" | sed 's/EXIT=//')
case "$st" in ''|*[!0-9]*) echo "   value test: shape=bad" ;; *) echo "   value test: shape=OK, st=$st -> BREACH row scores OK (vacuous pass)" ;; esac
echo "--- shipped rule (shape + value):"
sh "$POSTV" "$W/bare" | grep 'A2a'
sh "$POSTV" "$W/bare" >/dev/null 2>&1; echo "EXIT=$?"
echo
echo "--- and the PRE-fix scorer on the same input:"
rm -rf "$W/bare2"; cp -R "$W/bare" "$W/bare2"
sh "$PREV" "$W/bare2" | grep 'A2a'
sh "$PREV" "$W/bare2" >/dev/null 2>&1; echo "PRE_EXIT=$?"
