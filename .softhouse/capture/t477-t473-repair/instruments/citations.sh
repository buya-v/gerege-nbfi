#!/bin/bash
# =============================================================================================
# T477 -- THE CITATION SWEEP, RE-RUN FOR THIS DIFF.
#
# Every inbound `conformance.sh:NNNN` citation in the tree is A PIN INTO A LINE NUMBER, and this
# task inserts a few hundred lines into that file.  T466 recorded that its FIRST draft moved 213
# citations, two of them load-bearing (`patterns.md` and `fire-program.sh`), and repaired the
# diff rather than the pins.  The same measurement is taken here, for the same reason, and it is
# taken from the merge base rather than from a remembered number.
#
# The sweep itself is T466`s `citation-sweep.py`, unmodified, because T473 reproduced its 1799 /
# 20 to the row from an independently built extractor; what T477 supplies is the two texts and
# the corpus.  usage:  citations.sh [<base-rev>]   (default: merge-base with main)
# =============================================================================================
set -u

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 3
R=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd) || exit 3
SH=".soft""house"
CONF="$SH/conformance"".sh"
SWEEP="$SH/capture/t466-t459-conditions/instruments/citation-sweep"".py"
cd "$R" || { echo "REFUSED: could not enter $R" >&2; exit 3; }
[ -f "$SWEEP" ] || { echo "REFUSED: T466's citation sweep is absent." >&2; exit 3; }

SCR="${T477_WORK:-}"
if [ -z "$SCR" ]; then
  SCR=$(mktemp -d "${TMPDIR:-/tmp}/t477-work.XXXXXXXXXX") || exit 3
fi
BASE="${1:-}"
if [ -z "$BASE" ]; then
  BASE=$(git merge-base main HEAD) || exit 3
fi
echo "base rev  : $BASE"
echo "head rev  : $(git rev-parse HEAD)"
echo "base blob : $(git rev-parse "$BASE:$CONF")"
echo "head blob : $(git rev-parse "HEAD:$CONF")"
git show "$BASE:$CONF" >"$SCR/before.txt" || exit 3
git show "HEAD:$CONF"  >"$SCR/after.txt"  || exit 3
echo "before lines: $(LC_ALL=C grep -c '' "$SCR/before.txt")   after lines: $(LC_ALL=C grep -c '' "$SCR/after.txt")"
echo
git ls-files >"$SCR/tracked.txt"
echo "tracked paths in the corpus: $(LC_ALL=C grep -c '' "$SCR/tracked.txt")"
/usr/bin/python3 "$SWEEP" "$SCR/before.txt" "$SCR/after.txt" "$CONF" <"$SCR/tracked.txt"
rc=$?
echo "sweep exit=$rc"
exit "$rc"
