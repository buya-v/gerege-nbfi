#!/bin/bash
# drivecount.sh <worktree> <context> -- simpler form; same contract as redcount.sh.
exec "$(dirname "$0")/redcount.sh" "$@"
