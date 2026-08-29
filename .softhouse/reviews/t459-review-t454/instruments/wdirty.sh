#!/bin/bash
# T459 arm WDIRTY -- the OTHER side of T454's boundary decision: an HONEST uncommitted edit must
# still PASS, and must be NAMED. Without this arm the guard could be "refuse every dirty tree"
# and no transcript here would tell them apart.
set -u
. "$( cd "$( dirname "$0" )" && pwd )/drive.sh"
BASE="${1:-02fb1af4}"
A="WDIRTY"
arm "$A" "$BASE"
D="$( stage "$A" "$BASE" )" || exit 3
rm -rf "$D/graded"
git clone -q --no-hardlinks "$D/src" "$D/graded" >/dev/null 2>&1 || exit 3
G="$D/graded"
# an ordinary uncommitted edit: one harmless comment line appended. Nothing is forged.
printf '\n# T459 arm WDIRTY: an honest uncommitted edit, appended by a developer mid-task.\n' >> "$G/$CONF"
echo "    git status --porcelain:"; ( cd "$G" && git status --porcelain ) | sed 's/^/      /'
echo "    committed HEAD:harness = $( cd "$G" && git rev-parse "HEAD:$CONF" )"
echo "    on disk                = $( cd "$G" && git hash-object -- "$CONF" )"
runbar "$G" "$D/bar.log"
echo "    --- what the guard printed about the edit:"
LC_ALL=C grep -m3 'HARNESS-TEXT' "$D/bar.log" | sed 's/^/    /'
