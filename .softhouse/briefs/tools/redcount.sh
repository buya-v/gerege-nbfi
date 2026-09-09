#!/bin/bash
# redcount.sh <worktree> <context> -> count of registered <context>-wrong-* drives.
# `grep -c` prints 0 and EXITS 1; that exit must not reach the caller as a failure,
# but an EMPTY listing must -- an unbuildable binary lists nothing, which is not "0 drives".
. "$(dirname "$0")/_measure.sh"
[ $# -ge 2 ] || m_die "usage: redcount.sh <worktree> <context>"
m_setup "$1" "$2"
listing="$(m_list)"
printf '%s\n' "$listing" | grep -q . \
  || m_die "-list-implementations produced NO output for '$2'. An empty listing is a broken binary, not zero drives."
printf '%s' "$(printf '%s\n' "$listing" | grep -c "^$2-wrong-" | tr -dc '0-9')"
