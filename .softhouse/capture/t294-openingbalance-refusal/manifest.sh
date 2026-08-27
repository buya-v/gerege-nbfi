#!/bin/sh
# manifest.sh -- regenerate MANIFEST.sha256 over every committed artefact in this rig.
#
# COPIED for T294 from .softhouse/capture/t287-closure-refusals/manifest.sh; only this header
# differs. Covers out/, req/ and sql/ so that a later edit to a request body or a query is
# DETECTABLE rather than silent. Run from anywhere; paths in the manifest are relative to
# this directory so the digest is stable across worktrees.
#
# WHAT IS AND IS NOT WIRED, said plainly (P-89 -- "prose does not fire on the next fire", and
# seven artefacts in this program have already shipped wired to nothing):
#
#   WIRED. Two of this rig's artefacts ARE read by something that runs. LDG-REFUSE-03 cites
#   out/OB-01-openingbalance-after-posted-entries.json and .req in provenance, and
#   .softhouse/conformance.sh's ledger half re-reads both on every run: it resolves each
#   path, recomputes its sha256 against the digest in the vector, and refuses the vector if
#   either has changed [admit.go, citationReasons]. So a silent edit to those two files goes
#   RED at the bar, not merely at this manifest.
#
#   NOT WIRED. Everything else here -- the M-0* measurement captures, the sql/, this manifest
#   and guard-precondition.sh -- is read by nothing that runs. guard-precondition.sh fires
#   only when a human or a capture task invokes it. That is the honest state and it is
#   recorded rather than implied. To verify this manifest by hand:
#       cd <this dir> && shasum -a 256 -c MANIFEST.sha256
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
