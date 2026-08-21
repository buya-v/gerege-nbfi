#!/bin/bash
# T177 — sha256 manifest over every committed artefact of this rig, so a later edit to the raw
# evidence is visible in the diff. Sorted, relative paths, excludes the manifest itself.
set -uo pipefail
RIG="$1"
cd "$RIG" || exit 1
find . -type f ! -name MANIFEST.sha256 -print0 \
  | sort -z \
  | xargs -0 shasum -a 256 > MANIFEST.sha256
wc -l < MANIFEST.sha256
