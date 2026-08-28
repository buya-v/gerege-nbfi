#!/bin/sh
# Regenerate MANIFEST.sha256 over every artefact this throwaway rig produced, so drift in any
# recorded observation is detectable by `shasum -a 256 -c MANIFEST.sha256`. ADAPTED from
# ../manifest.sh; this rig DOES have a req/ directory, because unlike the read-only rig one
# directory up it FIRES -- at a disposable instance, never at the standing reference oracle.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
cd "$DIR"
find req out -type f ! -name .DS_Store 2>/dev/null | LC_ALL=C sort > /tmp/.t327tfiles.$$
: > MANIFEST.sha256
while IFS= read -r f; do
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$f" >> MANIFEST.sha256
  else sha256sum "$f" >> MANIFEST.sha256; fi
done < /tmp/.t327tfiles.$$
rm -f /tmp/.t327tfiles.$$
printf 'MANIFEST.sha256: %s entries\n' "$(grep -c '' MANIFEST.sha256)"
