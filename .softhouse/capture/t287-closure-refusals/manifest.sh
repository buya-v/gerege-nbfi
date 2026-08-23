#!/bin/sh
# manifest.sh -- regenerate MANIFEST.sha256 over every committed artefact in this rig.
#
# Covers out/, req/ and sql/ so that a later edit to a request body or a query is
# DETECTABLE rather than silent. Run from anywhere; paths in the manifest are relative to
# this directory so the digest is stable across worktrees.
#
# Deliberately NOT wired into any harness: this rig is a raw-capture directory and nothing
# in conformance.sh reads it. Saying so out loud because an artefact wired to nothing
# enforces nothing, and a manifest nobody verifies is decoration. To verify by hand:
#     cd <this dir> && shasum -a 256 -c MANIFEST.sha256
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
cd "$DIR"

if command -v shasum >/dev/null 2>&1; then
  HASH="shasum -a 256"
else
  HASH="sha256sum"
fi

# -print0/-0 so a filename with a space or newline cannot split a manifest line.
find out req sql -type f ! -name '.*' -print0 2>/dev/null \
  | LC_ALL=C sort -z \
  | xargs -0 $HASH \
  > MANIFEST.sha256

printf 'MANIFEST.sha256: %s files\n' "$(wc -l < MANIFEST.sha256 | tr -d ' ')"
