#!/usr/bin/env bash
# T446 — the SIXTH ROUTE drive.
#
# T445 keeps exactly one working-tree read of a graded path: it reads
# .softhouse/conformance.sh from THIS HOST, and argues the case attack on that read
# "provably cannot win" because the index entry that sorts LAST wins a collision and an
# all-lowercase path therefore cannot be beaten by a case variant.
#
# The mechanism is right and the corollary is false. Case is not the only fold this
# filesystem applies. U+017F LATIN SMALL LETTER LONG S folds onto ASCII 's' on APFS, and
# its UTF-8 bytes (c5 bf) sort AFTER ascii 's' (73) -- so it sorts LAST and it WINS.
#
# Usage: bash drive-longs.sh <work-root> <source-repo> <ref> <arm>
#   arm CONTROL : plant an UNREGISTERED checker only        -> the harness must refuse
#   arm LONGS   : the same tree, plus a forged harness at
#                 .softhouse/conformance.<U+017F>h that DECLARES that checker
# In both arms `git show HEAD:.softhouse/conformance.sh` is byte-identical to the honest
# harness; only what the checkout MATERIALISES differs.
set -u
WORK="${1:?}"; SRC="${2:?}"; REF="${3:?}"; ARM="${4:?}"
G=".softhouse/guards"
CONFREL=".softhouse/conformance.sh"
MEMBER="zz-t446-unreg.sh"
WIT="zz-t446-witness.txt"
LONGS_LEAF="$(printf 'conformance.\xc5\xbfh')"

rm -rf "$WORK/$ARM"; mkdir -p "$WORK/$ARM"
S="$WORK/$ARM/seed"; C="$WORK/$ARM/graded"; CWD="$WORK/$ARM/cwd"; mkdir -p "$CWD"

git clone -q "$SRC" "$S" || exit 1
( cd "$S" && git checkout -q "$REF" ) || exit 1

# an UNREGISTERED checker: no REACHED-BY row, not invoked by the harness, not in the table
{ printf '#!/usr/bin/env bash\n'; printf '# a checker with no registration of any kind\n'; printf 'exit 0\n'; } > "$S/$G/$MEMBER"
chmod +x "$S/$G/$MEMBER"
{ printf 'a witness planted by the T446 sixth-route drive.\n'
  printf 'it runs %s on every fire.\n' "$MEMBER"; printf 'end.\n'; } > "$S/$G/$WIT"
( cd "$S" && git add -A ) || exit 1

if [ "$ARM" = "LONGS" ]; then
  # the forgery: the SAME harness with ONE extra DECLARATION TABLE row.
  FORGED="$WORK/$ARM/forged"
  awk -v row="$MEMBER|CALLER|$G/$WIT|$MEMBER" '
    { print }
    /^  DECLARED="repo-state-attest\.sh\|CALLER\|/ { print row }
  ' "$S/$CONFREL" > "$FORGED"
  if [ "$(wc -l < "$FORGED")" -le "$(wc -l < "$S/$CONFREL")" ]; then
    echo "FORGERY DID NOT APPLY — anchor not found"; exit 1
  fi
  BLOB="$( cd "$S" && git hash-object -w "$FORGED" )" || exit 1
  ( cd "$S" && git update-index --add --cacheinfo "100755,$BLOB,.softhouse/$LONGS_LEAF" ) || exit 1
fi

( cd "$S" && git -c user.email=t446@local -c user.name=t446 commit -q -m "T446 sixth-route fixture" ) || exit 1

git clone -q "$S" "$C" 2>"$WORK/$ARM/clonewarn" || exit 1

echo "=============================== arm $ARM ==============================="
echo "index entries under .softhouse matching conformance:"
( cd "$C" && git ls-files -s -- '.softhouse/*' | LC_ALL=C grep -i 'conformance' | sed 's/^/    /' )
echo "COMMITTED blob of $CONFREL (what a reviewer reads):"
echo "    $( cd "$C" && git rev-parse "HEAD:$CONFREL" )"
echo "MATERIALISED file at $CONFREL (what bash executes):"
echo "    $( cd "$C" && git hash-object "$CONFREL" )"
echo "    identical to the committed blob? $( cd "$C" && [ "$(git rev-parse "HEAD:$CONFREL")" = "$(git hash-object "$CONFREL")" ] && echo YES || echo '*** NO ***' )"
echo "clone warnings:"; sed 's/^/    /' "$WORK/$ARM/clonewarn"
echo "git status --porcelain of the graded clone:"
( cd "$C" && git status --porcelain | sed 's/^/    /' )
echo "ls of the materialised .softhouse entries that fold onto conformance.sh:"
( cd "$C/.softhouse" && ls -b | LC_ALL=C grep -i conformance | sed 's/^/    /' )

RC=0
( cd "$CWD" && bash "$C/$CONFREL" ) > "$WORK/$ARM/bar.log" 2>&1 || RC=$?
N="$(LC_ALL=C grep -c 'probe = ' "$WORK/$ARM/bar.log" || true)"
echo "EXIT = $RC"
echo "probe line count (read BEFORE its value) = $N"
if [ "$N" -ge 1 ]; then echo "probe value = $(LC_ALL=C grep -m1 'probe = ' "$WORK/$ARM/bar.log" | sed 's/.*probe = //')"
else echo "probe value = ABSENT"; fi
LC_ALL=C grep -m1 '^VERDICT' "$WORK/$ARM/bar.log" || echo "VERDICT = (none)"
LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population=' "$WORK/$ARM/bar.log" || echo "(no census line)"
echo "--- registration sentences ---"
LC_ALL=C grep -n 'guards_dir_registration\|guards-dir registration\|INVOKED BY NOTHING\|DECLARED against' "$WORK/$ARM/bar.log" | head -20
