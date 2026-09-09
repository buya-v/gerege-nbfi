#!/bin/bash
# kills.sh <context> <impl> [worktree]  -> kill count for one wrong implementation.
# Worktree defaults to the repo this script lives in, so cwd no longer decides the
# answer -- it used to, and from the wrong cwd every control reported 0. See _measure.sh.
. "$(dirname "$0")/_measure.sh"
[ $# -ge 2 ] || m_die "usage: kills.sh <context> <impl> [worktree]"
m_setup "${3:-$(cd "$(dirname "$0")/../../.." && pwd)}" "$1"
m_require_registered "$2" "$(m_list)"
m_extract "$(m_run "$2")"
