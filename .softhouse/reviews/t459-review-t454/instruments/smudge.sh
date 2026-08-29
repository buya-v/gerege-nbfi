#!/bin/bash
# T459 arm SMUDGE -- T454 named a `.gitattributes` `filter=` as an OPEN, UNDRIVEN route and
# predicted it lands in the guard's EDITED branch (printed and accepted).  This drives it, and
# in the STRONGER construction the handoff did not consider: the attribute goes in
# `.git/info/attributes`, which is NOT committed, and the filter has a CLEAN half that inverts
# the SMUDGE half, so `git status`, `git diff-index` AND `git hash-object` are all clean.
set -u
. "$( cd "$( dirname "$0" )" && pwd )/drive.sh"
BASE="${1:-02fb1af4}"
A="SMUDGE"
arm "$A" "$BASE"
D="$( stage "$A" "$BASE" )" || exit 3
plant_unreg "$D/src"
( cd "$D/src" && git commit -q -m "T459 SMUDGE fixture: an unregistered checker" ) >/dev/null 2>&1 || exit 3
rm -rf "$D/graded"
git clone -q --no-hardlinks "$D/src" "$D/graded" >/dev/null 2>&1 || exit 3
G="$D/graded"

ROW3="zz-t459-unreg.sh|CALLER|$WIT|zz-t459-unreg.sh"
# the smudge half INJECTS the absolving row on checkout; the clean half REMOVES it again
cat > "$D/smudge.sh" <<SM
#!/bin/bash
LC_ALL=C awk -v row='$ROW3' '/ledgerguard"\$/ { sub(/ledgerguard"\$/, "ledgerguard\n" row "\"") } { print }'
SM
cat > "$D/clean.sh" <<CL
#!/bin/bash
LC_ALL=C awk -v row='$ROW3' 'BEGIN{p=row "\""} \$0 == p { next } /^drive-red-ledger-invariants\.sh\|SUBJECT\|.*ledgerguard\$/ { print \$0 "\""; next } { print }'
CL
chmod +x "$D/smudge.sh" "$D/clean.sh"

# THE ATTRIBUTE IS NOT COMMITTED. .git/info/attributes is per-clone, invisible in every diff.
printf 'conformance%s filter=t459\n' ".sh" > "$G/.git/info/attributes"
( cd "$G" && git config filter.t459.smudge "$D/smudge.sh" && git config filter.t459.clean "$D/clean.sh" )

rm -f "$G/$CONF"
( cd "$G" && git checkout -- "$CONF" ) || exit 3

echo "    committed HEAD:harness       = $( cd "$G" && git rev-parse "HEAD:$CONF" )"
echo "    on disk, RAW (--no-filters)  = $( git hash-object --no-filters -- "$G/$CONF" )"
echo "    on disk, as git sees it      = $( cd "$G" && git hash-object -- "$CONF" )"
echo "    absolving row present on disk: $( LC_ALL=C grep -c 'zz-t459-unreg.sh|CALLER' "$G/$CONF" )"
echo "    git status --porcelain:"; ( cd "$G" && git status --porcelain ) | sed 's/^/      /'
echo "    git diff-index --name-only HEAD:"; ( cd "$G" && git diff-index --name-only HEAD -- ) | sed 's/^/      /'
echo "    committed footprint of the attack (git show HEAD --stat, filtered):"
( cd "$G" && git show --stat --oneline HEAD ) | sed 's/^/      /'
runbar "$G" "$D/bar.log"
LC_ALL=C grep -m1 'this harness .*committed .* on disk' "$D/bar.log" | sed 's/^/    /'
LC_ALL=C grep -m1 'HARNESS-TEXT CENSUS' -A2 "$D/bar.log" | sed 's/^/    /'
