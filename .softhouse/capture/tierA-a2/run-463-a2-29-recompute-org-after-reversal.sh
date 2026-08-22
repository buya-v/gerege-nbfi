#!/bin/sh
# A2-29 / G-12 group E, step E.3 -- the ORGANISATION-scoped recalculation, run AFTER
# out/A2-462-db-after-office-scope.txt has recorded what the office-scoped one left behind.
# Separate file because running it inside run-460 would have destroyed the state run-460
# exists to measure.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
sh "$DIR/cap9.sh" A2-463-recompute-org-after-reversal POST \
      "/journalentries?command=updateRunningBalance" \
      req/a2-29-update-running-balance-org.json a2-29-rb-org-0006
