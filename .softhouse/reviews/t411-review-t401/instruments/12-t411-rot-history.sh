#!/usr/bin/env bash
# T411: was T385's prose EVER right? Walk the five figures across T385's own
# commits and forward to main. Distinguishes "the numbers rotted after T385
# wrote them" (T401's thesis) from "the numbers were wrong when written".
set -uo pipefail
GREP=/usr/bin/grep
printf '%-10s  %-46s %5s %5s %5s %5s %6s\n' 'COMMIT' 'SUBJECT' '.zsh' 'c+r' '.sh' '.py' 'corpus'
for c in "$@"; do
  T="$(git ls-tree -r --name-only "$c" 2>/dev/null)" || { echo "$c: unreachable"; continue; }
  n() { printf '%s\n' "$T" | $GREP -cE "$1"; }
  printf '%-10s  %-46s %5s %5s %5s %5s %6s\n' \
    "$(git rev-parse --short "$c")" \
    "$(git log -1 --format=%s "$c" | cut -c1-46)" \
    "$(n '\.zsh$')" \
    "$(n '^\.softhouse/(capture|reviews)/.*\.zsh$')" \
    "$(n '\.sh$')" \
    "$(n '\.py$')" \
    "$(n '(\.sh|\.py)$')"
done
echo
echo "T385 PROSE CLAIMED:                                              110    98   626   722   1348"
