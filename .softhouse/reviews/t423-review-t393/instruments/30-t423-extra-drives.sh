#!/bin/bash
# T423 — two drives T393 did not run, both against the POST-FIX bytes (fc51790d).
#
# DRIVE 1 — the 77. ARM E's population is the 27 non-observation entries in the FORK-SHA
#   manifest. The manifest at HEAD holds 104 such entries. The other 77 are the capture
#   scripts and red/green evidence added SINCE the fork sha -- cap8.sh, cap9.sh, cap10.sh,
#   mkreq7.py, resolve7.py, resolve8.py, every run-*.sh that produced the 632 post-fork
#   observations. ARM C filters to out/ and req/ and never reads their rows; ARM E's
#   population does not contain them; ARMs A, B and D are out/+req/ only; section 4 compares
#   fork-manifest entries and they are not in it. Question: is a COMMITTED, UNLAUNDERED
#   mutation of one of them visible to the aggregate verdict?
#
# DRIVE 2 — ARM B's missing try/except, driven rather than reasoned. T393 recorded that with
#   five arms an uncaught exception in ARM B skips ARMs C, D and E. A `git` that fails on one
#   `show HEAD:<path>` is injected by a PATH shim, which is the honest shape of the real
#   failure (a corrupt object, a gc race, a resource limit) without corrupting a repository.
#
# No host path is written in this file; every location is a required parameter.
#   T423_SRC=<repo>  T423_CLONE=<scratch>  T423_OUT=<dir>  T423_AFTER=<post-fix sha>
set -u
SRC="${T423_SRC:?}"; SCROOT="${T423_CLONE:?}"; OUT="${T423_OUT:?}"; AFTER="${T423_AFTER:?}"
CAP=".softhouse/capture/tierA-a2"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
RUNALL=".softhouse/reviews/A2-11/run-all.sh"
mkdir -p "$OUT" "$SCROOT" || exit 3

D="$SCROOT/extra"
rm -rf "$D" || exit 3
git clone --quiet --shared "$SRC" "$D" || exit 3
git -C "$D" config user.email t423@softhouse.local
git -C "$D" config user.name T423
git -C "$D" checkout --quiet --detach "$AFTER" || exit 3
git -C "$D" reset --quiet --hard "$AFTER" || exit 3

echo "############ DRIVE 1 — a committed mutation of a POST-FORK NON-OBSERVATION entry"
TARGET="cap8.sh"
if ! git -C "$D" ls-files --error-unmatch -- "$CAP/$TARGET" >/dev/null 2>&1; then
  echo "REFUSED: $TARGET is not tracked; the drive would be a no-op." >&2; exit 3
fi
grep -q "^[0-9a-f]\{64\}  $TARGET\$" "$D/$CAP/MANIFEST.sha256" \
  || { echo "REFUSED: $TARGET has no MANIFEST row; pick another target." >&2; exit 3; }
echo "target: $CAP/$TARGET  (tracked, has a MANIFEST row, NOT in ARM E's fork-sha population)"
printf '\n# T423-MUTATION-MARKER\n' >> "$D/$CAP/$TARGET" || exit 3
git -C "$D" add -- "$CAP/$TARGET" || exit 3
git -C "$D" commit -q -m "T423 probe: committed mutation of a POST-FORK capture script" || exit 3
( cd "$D" && bash "$RUNALL" ) > "$OUT/T423-drive1-nonobs-postfork.txt" 2>&1
RC1=$?
S10="$(awk '/^  10 /{print $3}' "$OUT/T423-drive1-nonobs-postfork.txt" | tail -1)"
V1="$(sed -n 's/.*RUN-ALL VERDICT: \([A-Z]*\).*/\1/p' "$OUT/T423-drive1-nonobs-postfork.txt" | tail -1)"
NAMED="$(grep -c -E "^ +DIFF ${TARGET}\$" "$OUT/T423-drive1-nonobs-postfork.txt")"
echo "  section10=$S10   run-all rc=$RC1   verdict=$V1   section4-named-it=$NAMED"
echo "  (section 4 naming it while the aggregate says PASS is T362's F-1 shape: a saturated"
echo "   section is the ONLY thing that saw it.)"
git -C "$D" reset --quiet --hard "$AFTER" || exit 3

echo
echo "############ DRIVE 2 — ARM B raises: how many arms never run, and what does the operator see?"
SHIM="$SCROOT/shim"
rm -rf "$SHIM"; mkdir -p "$SHIM" || exit 3
REALGIT="$(command -v git)" || exit 3
cat > "$SHIM/git" <<SHIMEOF
#!/bin/bash
# Fail exactly one \`git show HEAD:<path>\` -- the shape of a corrupt object or a gc race.
for a in "\$@"; do
  case "\$a" in
    HEAD:*)
      if [ ! -f "$SHIM/.fired" ]; then
        : > "$SHIM/.fired"
        echo "fatal: T423 injected object read failure for \$a" >&2
        exit 128
      fi
      ;;
  esac
done
exec "$REALGIT" "\$@"
SHIMEOF
chmod +x "$SHIM/git"
( cd "$D" && PATH="$SHIM:$PATH" python3 "$INT" ) > "$OUT/T423-drive2-armB-raises.txt" 2>&1
RC2=$?
echo "  verify-capture-integrity.py exit = $RC2"
echo "  Traceback printed        : $(grep -c '^Traceback' "$OUT/T423-drive2-armB-raises.txt")"
echo "  ARM C header reached     : $(grep -c '=== 5. ARM C' "$OUT/T423-drive2-armB-raises.txt")"
echo "  ARM D header reached     : $(grep -c '=== 6. ARM D' "$OUT/T423-drive2-armB-raises.txt")"
echo "  ARM E header reached     : $(grep -c '=== 7. ARM E' "$OUT/T423-drive2-armB-raises.txt")"
echo "  FAILURES: line printed   : $(grep -c '^FAILURES:' "$OUT/T423-drive2-armB-raises.txt")"
echo "  VERDICT: line printed    : $(grep -c '^VERDICT:' "$OUT/T423-drive2-armB-raises.txt")"
echo "  Is exit 1 distinguishable from a genuine mutation? exit 1 is ALSO the mutation code."
exit 0
