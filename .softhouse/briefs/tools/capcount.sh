#!/bin/bash
# capcount.sh <worktree> <context> <impl> -> kill count against an arbitrary worktree.
. "$(dirname "$0")/_measure.sh"
[ $# -ge 3 ] || m_die "usage: capcount.sh <worktree> <context> <impl>"
m_setup "$1" "$2"
m_require_registered "$3" "$(m_list)"
m_extract "$(m_run "$3")"
