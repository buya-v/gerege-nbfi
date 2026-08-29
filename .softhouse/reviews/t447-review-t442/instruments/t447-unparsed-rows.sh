#!/usr/bin/env bash
# =============================================================================================
# T447 -- READ T442's 23 UNPARSED ROWS.
#
# T442's census reports `unparsed=23`: 23 search lines that `shlex.split` could not tokenise, so
# no pattern operand could be extracted and the row was filed under RUNTIME. The handoff names
# them but does not say what is IN them. AN UNPARSED ROW IS NOT A SAFE ROW -- the whole point of
# extracting the pattern operand is to ask whether it self-matches, and for these 23 that
# question was never asked.
#
# This prints each of the 23 lines, and for each one runs the ONE question T442's census would
# have run had it tokenised: is there any quoted literal on that line, >= 3 chars, which
# `git grep -l -F` finds IN THE SEARCHING FILE ITSELF? A hit does not prove a defect -- direction
# is still prose -- but it is the row that has to be read, and the reader now sees which.
#
# Usage: t447-unparsed-rows.sh <T442-CLASS-SWEEP.txt>
# Exit 0 = printed. Exit 2 = could not measure.
# =============================================================================================
set -uo pipefail
T=${1:-}
[ -r "${T:-/nonexistent}" ] || { echo "REFUSED: usage: $0 <T442-CLASS-SWEEP.txt>" >&2; exit 2; }
REPO=$(git rev-parse --show-toplevel) || exit 2

DECLARED=$(sed -n 's/.*of which UNPARSED by shlex.*: \([0-9]*\)$/\1/p' "$T" | head -1)
[ -n "$DECLARED" ] || { echo "REFUSED: could not read the declared unparsed count" >&2; exit 2; }

ROWS=$(sed -n '/of which UNPARSED by shlex/,/^$/p' "$T" | sed -n 's/^    \(\.softhouse\/.*\)$/\1/p')
N=$(printf '%s\n' "$ROWS" | grep -c '.')
if [ "$N" -ne "$DECLARED" ]; then
  echo "REFUSED: parsed $N rows, transcript declares $DECLARED" >&2; exit 2
fi

echo "=============================================================================================="
echo "T447 -- T442's UNPARSED ROWS, READ"
echo "=============================================================================================="
echo "repo    : $REPO"
echo "commit  : $(git rev-parse HEAD)"
echo "declared unparsed rows : $DECLARED   parsed here : $N   MATCH"
echo

SELFHIT=0
printf '%s\n' "$ROWS" | while IFS= read -r row; do
  [ -n "$row" ] || continue
  f=${row%:*}; ln=${row##*:}
  echo "----------------------------------------------------------------------------------------------"
  echo "$row"
  sed -n "${ln}p" "$REPO/$f" | sed 's/^/    /'
  # every single-quoted literal of >=3 chars on that line, with no $ in it
  sed -n "${ln}p" "$REPO/$f" \
    | tr "'" '\n' | awk 'NR%2==0' \
    | while IFS= read -r lit; do
        case "$lit" in ''|*'$'*|*'`'*) continue ;; esac
        [ "${#lit}" -ge 3 ] || continue
        hits=$(git -C "$REPO" grep -l -F -e "$lit" -- .softhouse 2>/dev/null | grep -c '.')
        self=$(git -C "$REPO" grep -l -F -e "$lit" -- "$f" 2>/dev/null | grep -c '.')
        if [ "$self" -gt 0 ]; then
          printf '    literal %-46s hits=%-4s SELF-MATCHES\n' "'$lit'" "$hits"
        else
          printf '    literal %-46s hits=%-4s (not in this file)\n' "'$lit'" "$hits"
        fi
      done
done
echo "----------------------------------------------------------------------------------------------"
echo "T447-UNPARSED-RESULT: rows=$N"
exit 0
