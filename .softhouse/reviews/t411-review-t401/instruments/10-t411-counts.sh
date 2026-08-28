#!/usr/bin/env bash
# T411 independent re-measurement of the five T385/T401 figures.
#
# Takes a commit-ish and measures from the TREE AT THAT COMMIT (git ls-tree -r),
# never from the working disk -- so the figure cannot drift with uncommitted work.
#
# Every alternation is -E, and every grep is /usr/bin/grep spelled ABSOLUTELY, so
# no shell function shim can change the answer. See F-T411-1: this repo's harness
# installs a `grep` shell function that resolves to ugrep, and ugrep and BSD grep
# DISAGREE on anchored BRE alternation. An instrument that says `grep` is asking a
# question whose answer depends on how it was launched.
set -uo pipefail
GREP=/usr/bin/grep
REF="${1:?usage: 10-t411-counts.sh <commit-ish>}"
SHA="$(git rev-parse --short "$REF")"

echo "T411 COUNTS @ $SHA  ($(git log -1 --format=%s "$REF" | cut -c1-60))"
echo "instrument: 10-t411-counts.sh"
echo "grep      : $($GREP --version 2>&1 | head -1)"
echo

TREE="$(git ls-tree -r --name-only "$REF")"
n() { printf '%s\n' "$TREE" | $GREP -cE "$1"; }

printf '%-44s %6s\n' 'FIGURE' 'COUNT'
printf '%-44s %6s   selector: %s\n' 'tracked .zsh, whole repo' "$(n '\.zsh$')" "ls-tree -r --name-only | grep -cE '[.]zsh\$'"
printf '%-44s %6s   selector: %s\n' 'tracked .zsh under capture/+reviews/' "$(n '^[.]softhouse/(capture|reviews)/.*[.]zsh$')" "... grep -cE '^[.]softhouse/(capture|reviews)/.*[.]zsh\$'"
printf '%-44s %6s   selector: %s\n' 'tracked .sh, whole repo' "$(n '\.sh$')" "ls-tree -r --name-only | grep -cE '[.]sh\$'"
printf '%-44s %6s   selector: %s\n' 'tracked .py, whole repo' "$(n '\.py$')" "ls-tree -r --name-only | grep -cE '[.]py\$'"
printf '%-44s %6s   selector: %s\n' 'S1 fail-open corpus (.sh + .py)' "$(n '(\.sh|\.py)$')" "ls-tree -r --name-only | grep -cE '([.]sh|[.]py)\$'"
echo
echo "--- cross-checks: independent selectors that MUST agree ---"
printf '  .sh + .py summed separately             : %s\n' "$(( $(n '\.sh$') + $(n '\.py$') ))"
printf '  S1 corpus via python str.endswith       : %s\n' "$(printf '%s\n' "$TREE" | python3 -c 'import sys;print(sum(1 for l in sys.stdin.read().split("\n") if l.endswith((".sh",".py"))))')"
printf '  .zsh via python str.endswith            : %s\n' "$(printf '%s\n' "$TREE" | python3 -c 'import sys;print(sum(1 for l in sys.stdin.read().split("\n") if l.endswith(".zsh")))')"
echo
echo "--- THE DEFECTIVE IDIOM, on this same corpus, for contrast (F-T411-1) ---"
printf '  /usr/bin/grep -c BRE  %s : %s\n' "'[.]sh\$\\|[.]py\$'" "$(printf '%s\n' "$TREE" | $GREP -c '\.sh$\|\.py$'; )"
printf '  ... exit status of that call            : %s  <-- SUCCESS while undercounting\n' "$?"
echo
echo "--- .zsh distribution ---"
printf '%s\n' "$TREE" | $GREP -E '\.zsh$' | sed -E 's#^([.]softhouse/[^/]+)/.*#\1#' | sort | uniq -c | sort -rn
printf '  .zsh NOT under .softhouse/              : %s\n' "$(printf '%s\n' "$TREE" | $GREP -E '\.zsh$' | $GREP -cvE '^\.softhouse/')"
printf '  .zsh under the guards directory         : %s\n' "$(printf '%s\n' "$TREE" | $GREP -cE '^\.softhouse/guards/.*\.zsh$')"
