#!/bin/sh
# T46 -- capture the A-3 / A-5 shapes from the live reference oracle (Fineract), tenant `gerege`.
# RAW OBSERVED FORM ONLY.  Nothing here is a parity vector; nothing is contract-shaped.
#
# ADDITIVE ONLY.  This script creates NO charge definition, modifies none, deletes none.
# T40's ids 1-12 are used exactly as they stand.  Nothing is restarted or re-tenanted; the
# only endpoint touched is the pure calculation endpoint, which persists nothing (`m_loan` 0).
#
# The T40 preconditions gate runs first and aborts the capture if any of its 15 assertions
# breaches -- including T36's BEHAVIOURAL half-cent canary, which is what makes the run
# evidence about the arithmetic and not merely about a configuration row.
set -eu
. "$(dirname "$0")/lib.sh"

O=${1:-$CH/out/t46}
mkdir -p "$O"

sh "$CH/bin/run-preconditions.sh" "$O/preconditions.txt" > /dev/null || {
  echo "ABORT: preconditions breached -- nothing captured." >&2; exit 1; }
echo "preconditions: ALL PASS"
echo

for f in "$CH"/req/calc-T46-CH-*.json; do
  n=$(basename "$f" .json); n=${n#calc-}
  post "$f" "$O/$n-raw.json" || exit 1
done

echo
shasum -a 256 "$O"/T46-CH-*-raw.json
