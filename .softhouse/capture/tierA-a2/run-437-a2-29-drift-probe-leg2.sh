#!/bin/sh
# A2-29 / G-12 group C, step C.5 ONLY -- re-run after the oracle REFUSED the first attempt.
#
# WHY THIS IS A SEPARATE FILE. run-430-a2-29-drift-probe.sh had already created two GL
# accounts, posted an entry, retyped an account and run three recomputes when its last
# step was refused HTTP 403 `error.msg.glJournalEntry.invalid.future.date` -- 01 September
# 2026 is in the future for this oracle (today is 2026-08-22). Re-running run-430 whole
# would have hit a duplicate glCode and destroyed the state under measurement. The refusal
# is kept verbatim as out/A2-437-je-after-retype-futuredate.*, which is the observation
# that fixed the date; it is not an error that was swept up.
#
# run-430 now carries the corrected date so a fresh replay from an empty oracle works in
# one pass. THIS file is what THIS fire actually executed for step C.5, and both are
# committed rather than one being rewritten to look like the other.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C9="$DIR/cap9.sh"

python3 "$DIR/mkje-a2-29.py" \
    "$DIR/out/A2-431-gl-drift-liability.json" \
    "$DIR/out/A2-430-gl-drift-asset.json" \
    "01 August 2026" 50000000 \
    "A2-29 drift probe leg 2: posted after glCode 19929 was retyped to INCOME" \
    "$DIR/req/a2-29-je-2-after-retype.json"
sh "$C9" A2-439-je-after-retype POST /journalentries req/a2-29-je-2-after-retype.json a2-29-je-2-0002
sh "$C9" A2-440-recompute-4 POST "/journalentries?command=updateRunningBalance" \
      req/a2-29-update-running-balance-org.json a2-29-rb-org-0005
