#!/bin/zsh
# T385 independent probe harness. Unsets the live-fire snapshot vars (T383's recorded hazard),
# points the wrapper at a throwaway repo and a /tmp LOG_DIR, and runs --probe only.
# $1 = path to wrapper under test. Remaining args are extra env assignments (VAR=VAL).
_w="$1"; shift
unset FIRE_SNAPSHOT_OF FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT FIRE_NO_SNAPSHOT
export GEREGE_NBFI_REPO=/tmp/t385/subject
export LOG_DIR=/tmp/t385/logs
for kv in "$@"; do export "$kv"; done
/bin/zsh "$_w" --probe 2>&1
print -r -- "rc $?"
