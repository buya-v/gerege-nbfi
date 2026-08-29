#!/usr/bin/env bash
# =============================================================================================
# T444 — ARM `CASE`: the residual T431 does NOT close, driven through the WHOLE BAR.
#
# T431 records "a case-SENSITIVE filesystem" as an unreached bound. The interesting direction is
# the other one: on a case-INSENSITIVE host, the INDEX can hold two entries differing only in
# case while the FILESYSTEM holds ONE file. Every test in this direction that reads the INDEX
# then grades one entry, and the closing `grep`, which reads the FILESYSTEM, reads the OTHER.
#
#   index:  <d>/W.txt  100644  DECOY blob        <- the path the member DECLARES
#           <d>/w.txt  120000  symlink -> member <- sorts AFTER 'W', so it WINS the checkout
#                                                   collision and is the file `grep` opens
#
# The pin resolves the declared path exactly; the empty-result branch does not fire; THE
# ROUND-TRIP TEST HOLDS EXACTLY (`self_path == self_norm`); the mode test reads 100644 so the
# symlink refusal never fires; the blob test compares the decoy blob, not the member's. The
# `grep` then reads the member's own bytes through the symlink and the member vouches for
# itself — the exact amnesty this direction exists to refuse.
#
# Work root and source repo are ARGUMENTS. The bar is run in a SECOND, FRESH clone so the
# collision is resolved by git's own checkout, not by the order this script created files in.
#
# USAGE: bash drive-case.sh <workroot> <srcrepo> <ref>
# =============================================================================================
set -u
WORK="${1:?usage: drive-case.sh <workroot> <srcrepo> <ref>}"
SRC="${2:?usage: drive-case.sh <workroot> <srcrepo> <ref>}"
REF="${3:?usage: drive-case.sh <workroot> <srcrepo> <ref>}"
[ -e "$WORK" ] && { echo "work root $WORK exists; refusing to reuse" >&2; exit 2; }
mkdir -p "$WORK" || exit 2

GUARDS_REL=".softhouse/guards"
DIR_LEAF="zz-t444k"
MEM_LEAF="zz-t444k-member.sh"
UP_LEAF="W.txt"
LO_LEAF="w.txt"

echo "=== T444 ARM CASE — src=$SRC ref=$REF work=$WORK ==="
echo "git: $(git --version)"
git clone --no-hardlinks -q "$SRC" "$WORK/a" >/dev/null 2>&1 || { echo "clone failed"; exit 2; }
cd "$WORK/a" || exit 2
git checkout -q "$REF" || { echo "checkout failed"; exit 2; }
echo "ref HEAD: $(git log --oneline -1)"
echo "core.ignorecase = $(git config core.ignorecase)"
d="$GUARDS_REL/$DIR_LEAF"
mkdir -p "$d"
{ printf '#!/usr/bin/env bash\n'
  printf '# %s -- PLANTED, UNWIRED checker. NOTHING in the harness runs it.\n' "$MEM_LEAF"
  printf '# GUARDS-DIR-REGISTRATION: REACHED-BY %s/%s\n' "$d" "$UP_LEAF"
  printf 'exit 0\n'; } > "$d/$MEM_LEAF"
ln -s "$MEM_LEAF" "$d/$LO_LEAF"
git add -A >/dev/null 2>&1
D="$(printf 'T444 arm CASE decoy blob. It does NOT name the member.\n' | git hash-object -w --stdin)"
git update-index --add --cacheinfo 100644,"$D","$d/$UP_LEAF" || { echo "update-index failed"; exit 2; }
git -c user.email=t444@x -c user.name=t444 commit -q -m "T444 arm CASE"
echo "=== committed entries for this directory ==="
git ls-tree -r HEAD -- "$d"

echo
echo "=== FRESH CLONE — this is where the bar runs ==="
cd "$WORK" || exit 2
git clone --no-hardlinks -q "$WORK/a" "$WORK/b" 2>&1 | LC_ALL=C sed -n '1,8p'
cd "$WORK/b" || exit 2
git checkout -q "$(cd "$WORK/a" && git rev-parse HEAD)" 2>/dev/null || true
echo "--- filesystem ---"; ls -l "$d"
echo "--- index ---"; git ls-files -s -- "$d"
echo "--- git status --porcelain ---"; git status --porcelain | LC_ALL=C sed -n '1,10p'

echo
echo "=== THE WHOLE BAR ==="
bash .softhouse/conformance.sh > "$WORK/case.out" 2>&1
rc=$?
echo "EXIT=$rc"
echo "-- P-84: PRESENCE of the probe line, read BEFORE its value --"
echo "   grep -c 'probe = ' = $(LC_ALL=C grep -c 'probe = ' "$WORK/case.out")"
echo "-- then its value --"
LC_ALL=C grep 'probe = ' "$WORK/case.out"
echo "-- guards-dir census --"
LC_ALL=C grep 'GUARDS-DIR-REGISTRATION: population' "$WORK/case.out"
echo "-- what the guard printed about this member --"
LC_ALL=C grep -A1 "REACHED-BY .*$DIR_LEAF" "$WORK/case.out"
echo "-- any registration refusal --"
LC_ALL=C grep -E 'THAT WITNESS IS A SYMLINK|MORE THAN ONE TRACKED PATH|DID NOT ROUND-TRIP|matched NO INDEX ENTRY|DOES NOT NAME|IS INVOKED BY NOTHING|RESOLVES TO' "$WORK/case.out" | LC_ALL=C sed -n '1,6p'
echo "-- VERDICT --"
LC_ALL=C grep -E '^VERDICT' "$WORK/case.out"
echo "-- tree clean after the run? --"
git status --porcelain | LC_ALL=C sed -n '1,5p'
echo "=== full transcript: $WORK/case.out ==="
