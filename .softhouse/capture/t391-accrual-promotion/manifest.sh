#!/bin/sh
# T391 -- digest every file in this rig, so a later edit to a script that
# produced committed evidence is DETECTABLE rather than invisible.
#
# Same purpose as T388's manifest.sh and the same scope rule: THE WHOLE RIG, not
# only its outputs. A capture script is part of the evidence, because a recipe
# nobody can re-derive is not a recipe (D-1, and T114's rule against editing a
# script that has produced committed observations).
#
# `shasum -a 256 -c MANIFEST.sha256` from this directory verifies it.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
cd "$DIR"
find . -type f ! -name 'MANIFEST.sha256' | LC_ALL=C sort | tr '\n' '\0' |
  xargs -0 shasum -a 256 > MANIFEST.sha256
echo "MANIFEST.sha256: $(wc -l < MANIFEST.sha256 | tr -d ' ') files"
