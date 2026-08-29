#!/usr/bin/env bash
# T445: materialise a source repository pinned at one commit, for the drive to clone from.
# Every path is an ARGUMENT; no literal shared-temp path is bound to a name here.
#   usage: bash mk-src.sh <dest> <repo> <ref>
set -eu
DEST="${1:?dest}"; REPO="${2:?repo}"; REF="${3:?ref}"
rm -rf "$DEST"
git clone -q "$REPO" "$DEST"
( cd "$DEST" && git checkout -q "$REF" && git log --oneline -1 && git status --porcelain )
