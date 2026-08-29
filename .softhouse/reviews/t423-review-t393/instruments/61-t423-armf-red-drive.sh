#!/bin/bash
# T423 — the RED half of the ARM F condition (P-22: a proposal whose failing case was never
# run is a hope, which is T393's own phrasing and the standard it is being held to).
#
# Builds a repository carrying T393's DISCLOSED RESIDUAL — a post-fork observation mutated
# with its MANIFEST.sha256 row rewritten in the SAME commit — and grades it two ways:
#
#   section 10 (verify-capture-integrity.py)      EXPECTED exit 0, VERDICT: PASS   (the gap)
#   60-t423-birth-arm-reaches-residual.py         EXPECTED exit 1, the file NAMED  (the close)
#
# If section 10 goes red here, T393's residual is not real and this whole condition is wrong.
# If ARM F goes green here, the proposed arm does not reach the residual and the condition is
# also wrong. Both directions are therefore load-bearing and both are recorded.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298).
#   T423_SRC=<repo>  T423_CLONE=<scratch OUTSIDE the repo>  T423_OUT=<dir>  T423_AFTER=<sha>
# EXIT 0 both graders behaved as expected. EXIT 1 one did not. EXIT 3 the harness could not run.
set -u
SRC="${T423_SRC:?}"; SCROOT="${T423_CLONE:?}"; OUT="${T423_OUT:?}"; AFTER="${T423_AFTER:?}"
CAP=".softhouse/capture/tierA-a2"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
MAN="$CAP/MANIFEST.sha256"
FORK="12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
ARMF="$(cd "$(dirname "$0")" && pwd)/60-t423-birth-arm-reaches-residual.py"
[ -f "$ARMF" ] || { echo "REFUSED: ARM F instrument not found beside this script" >&2; exit 3; }
mkdir -p "$OUT" "$SCROOT" || exit 3

POSTFORK="$(comm -13 \
  <(git -C "$SRC" ls-tree -r --name-only "$FORK" -- "$CAP/out" "$CAP/req" | sed "s|^$CAP/||" | LC_ALL=C sort) \
  <(git -C "$SRC" ls-tree -r --name-only HEAD    -- "$CAP/out" "$CAP/req" | sed "s|^$CAP/||" | LC_ALL=C sort) \
  | head -1)"
[ -n "$POSTFORK" ] || { echo "REFUSED: empty post-fork set" >&2; exit 3; }
echo "T423 ARM-F red drive; residual target = $POSTFORK"

D="$SCROOT/armf"
rm -rf "$D" || exit 3
git clone --quiet --shared "$SRC" "$D" || exit 3
git -C "$D" config user.email t423@softhouse.local
git -C "$D" config user.name T423
git -C "$D" checkout --quiet --detach "$AFTER" || exit 3
git -C "$D" reset --quiet --hard "$AFTER" || exit 3

printf '\nT423-RESIDUAL-MARKER\n' >> "$D/$CAP/$POSTFORK" || exit 3
NEW="$(shasum -a 256 "$D/$CAP/$POSTFORK" | awk '{print $1}')" || exit 3
perl -pi -e "s|^[0-9a-f]{64}(\s+\*?\Q$POSTFORK\E)\$|$NEW\$1|" "$D/$MAN" || exit 3
grep -q -E "^$NEW" "$D/$MAN" || { echo "REFUSED: manifest row not laundered" >&2; exit 3; }
git -C "$D" add -- "$CAP/$POSTFORK" "$MAN" || exit 3
git -C "$D" commit -q -m "T423: the disclosed residual -- post-fork observation mutated, manifest row rewritten in the same commit" || exit 3
echo "  laundered commit $(git -C "$D" rev-parse --short HEAD); working tree clean: [$(git -C "$D" status --porcelain | wc -l | tr -d ' ') path(s) dirty]"

( cd "$D" && python3 "$INT" ) > "$OUT/T423-armf-section10-on-laundered.txt" 2>&1
RC10=$?
( T423_TARGET="$D" python3 "$ARMF" ) > "$OUT/T423-armf-armF-on-laundered.txt" 2>&1
RCF=$?

V10="$(sed -n 's/^VERDICT: \([A-Z]*\).*/\1/p' "$OUT/T423-armf-section10-on-laundered.txt" | tail -1)"
VF="$(sed -n 's/^VERDICT: \([A-Z]*\).*/\1/p' "$OUT/T423-armf-armF-on-laundered.txt" | tail -1)"
NAMED="$(grep -c "LAUNDERED-OR-MUTATED $POSTFORK" "$OUT/T423-armf-armF-on-laundered.txt")"

echo
echo "  section 10 on the laundered repo : exit $RC10  VERDICT $V10   (expected 0 / PASS)"
echo "  ARM F      on the laundered repo : exit $RCF   VERDICT $VF    (expected 1 / FAIL)"
echo "  ARM F named the laundered file   : $NAMED                    (expected 1)"

FAIL=0
[ "$RC10" = "0" ] && [ "$V10" = "PASS" ] || { echo "  *** section 10 did not behave as T393 disclosed"; FAIL=1; }
[ "$RCF" = "1" ] && [ "$VF" = "FAIL" ] && [ "$NAMED" = "1" ] || { echo "  *** ARM F did not reach the residual"; FAIL=1; }
[ "$FAIL" = "0" ] && { echo "T423 ARM-F DRIVE VERDICT: PASS — the residual is real AND closable."; exit 0; }
echo "T423 ARM-F DRIVE VERDICT: FAIL"; exit 1
