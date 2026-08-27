#!/bin/sh
# Regenerate MANIFEST.sha256 over every artefact in this rig, so drift in any recorded
# observation is detectable by `shasum -a 256 -c MANIFEST.sha256`. ADAPTED from
# ../t294-openingbalance-refusal/manifest.sh; the one difference is that this rig has no
# req/ directory to walk, because IT FIRES NOTHING.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
cd "$DIR"
find sql out -type f ! -name .DS_Store 2>/dev/null | LC_ALL=C sort > /tmp/.t305files.$$
: > MANIFEST.sha256
while IFS= read -r f; do
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$f" >> MANIFEST.sha256
  else sha256sum "$f" >> MANIFEST.sha256; fi
done < /tmp/.t305files.$$
rm -f /tmp/.t305files.$$
printf 'MANIFEST.sha256: %s entries\n' "$(grep -c '' MANIFEST.sha256)"
