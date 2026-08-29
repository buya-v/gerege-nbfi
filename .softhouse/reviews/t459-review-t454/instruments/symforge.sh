#!/bin/bash
# T459 arm SYMFORGE -- the EIGHTH route candidate.
#
# guard_harness_text_is_committed's discriminator is: "the disk bytes at tracked P hash to the
# committed blob of a tracked Q != P".  The comment above it argues that is INHERENT to the
# route -- "the winner of a checkout collision is always some index entry's blob".
#
# It is not.  Make the colliding entry a 120000 SYMLINK whose target is a tracked forged
# harness.  `git hash-object` on a symlink hashes the TARGET PATH STRING; bash executing it
# follows the link and runs the forged text.  The hash of a short relative path is no tracked
# blob, so owner is unfound and the path lands in the guard's EDITED branch: printed, accepted.
# THE GUARD IS NOT TOUCHED.  Nothing is deleted from it.  The forgery survives a fresh clone.
set -u
. "$( cd "$( dirname "$0" )" && pwd )/drive.sh"
BASE="${1:-02fb1af4}"
A="SYMFORGE"
arm "$A" "$BASE"
D="$( stage "$A" "$BASE" )" || exit 3
S="$D/src"
PAYREL="conformance-payload"".sh"          # relative to .softhouse/, so the link is short
PAY="$SH/$PAYREL"

plant_unreg "$S"
forge "$S" "$D/forged.txt" ROW
cp "$D/forged.txt" "$S/$PAY"
chmod +x "$S/$PAY"
( cd "$S" && git add -- "$PAY" ) >/dev/null 2>&1

# the colliding entry is a SYMLINK, not a blob of the harness
LNK="$( cd "$S" && printf '%s' "$PAYREL" | git hash-object -w --stdin )" || exit 3
( cd "$S" && git update-index --add --cacheinfo "120000,$LNK,$CONFLONG" ) || exit 3
echo "    colliding entry is 120000, target-string blob $LNK"

( cd "$S" && git commit -q -m "T459 SYMFORGE fixture" ) >/dev/null 2>&1 || exit 3
rm -rf "$D/graded"
git clone -q --no-hardlinks "$S" "$D/graded" >/dev/null 2>&1 || exit 3
G="$D/graded"
echo "    committed HEAD:harness   = $( cd "$G" && git rev-parse "HEAD:$CONF" )"
echo "    what the path IS on disk : $( ls -l "$G/$CONF" | sed 's/.* \([^ ]*\) ->/-> /;s/^.*conformance/conformance/' )"
echo "    is it a symlink?         : $( [ -L "$G/$CONF" ] && echo YES || echo no )"
echo "    git hash-object -- path  = $( cd "$G" && git hash-object -- "$CONF" )"
echo "    absolving row reachable through the link: $( LC_ALL=C grep -c 'zz-t459-unreg.sh|CALLER' "$G/$CONF" )"
echo "    git status --porcelain:"; ( cd "$G" && git status --porcelain ) | sed 's/^/      /'
runbar "$G" "$D/bar.log"
LC_ALL=C grep -m2 'HARNESS-TEXT' "$D/bar.log" | sed 's/^/    /'
LC_ALL=C grep -m1 'this harness .*committed .* on disk' "$D/bar.log" | sed 's/^/    /'
