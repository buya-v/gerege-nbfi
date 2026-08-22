#!/bin/sh
# A2-29 / G-12 group C -- CAN THE STORED RUNNING BALANCE BE MADE TO DISAGREE WITH THE
# DERIVED SUM IN A WAY THE ORACLE'S OWN RECALCULATION DOES NOT HEAL?
#
# Group B (run-420) already showed that a FULL recompute healed every one of the 54 rows,
# so "stale between job runs" is settled and is only half the question. THIS batch attacks
# the other half: is there a state the recompute itself carries forward wrong?
#
# THE HYPOTHESIS, derived from the pinned source and NOT from any expected value:
#   JournalEntryRunningBalanceUpdateServiceImpl.calculateRunningBalance decides the SIGN of
#   each leg from `glAccount.classification_enum` JOINED AT RECOMPUTE TIME
#   [VERIFIED: .../JournalEntryRunningBalanceUpdateServiceImpl.java:225-242, and the joins
#   at :256-257 and :263-264], while updateRunningBalance() only ever recomputes entries
#   whose entry_date >= MIN(entry_date WHERE is_running_balance_calculated=false)
#   [VERIFIED: same file:72-79]. Retyping an account changes the sign rule for entries the
#   job will never revisit, and the seed query at :110-116 then READS those stale stored
#   values back to prime the next run.
#
# So the probe is: post, recompute, RETYPE, recompute, post again, recompute, measure.
# Whether the hypothesis holds is decided by out/A2-43x-db-*.txt, not by this comment.
#
# ISOLATION. Two GL accounts created for this probe alone, glCode 19929 / 19930. Nothing
# already in the corpus is retyped -- gl 2 (the G-10 retype) is not touched, and neither is
# any account any product maps. The probe's own accounts are mapped by no product.
#
# THIS BATCH MUTATES THE ORACLE: 2 new GL accounts, 2 manual journal entries, 1 retype,
# and 3 runs of the running-balance recalculation.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C8="$DIR/cap8.sh"
C9="$DIR/cap9.sh"

# --- C.1 the two isolated accounts -------------------------------------------------
sh "$C8" A2-430-gl-drift-asset     POST /glaccounts req/a2-29-gl-drift-asset.json
sh "$C8" A2-431-gl-drift-liability POST /glaccounts req/a2-29-gl-drift-liability.json

# --- C.2 one entry while the account is an ASSET -----------------------------------
python3 "$DIR/mkje-a2-29.py" \
    "$DIR/out/A2-430-gl-drift-asset.json" \
    "$DIR/out/A2-431-gl-drift-liability.json" \
    "01 July 2026" 100000000 \
    "A2-29 drift probe leg 1: posted while glCode 19929 is an ASSET" \
    "$DIR/req/a2-29-je-1-while-asset.json"
sh "$C9" A2-432-je-while-asset POST /journalentries req/a2-29-je-1-while-asset.json a2-29-je-1-0001

# --- C.3 recompute, then read the boundary -----------------------------------------
sh "$C9" A2-433-recompute-1 POST "/journalentries?command=updateRunningBalance" \
      req/a2-29-update-running-balance-org.json a2-29-rb-org-0002

# --- C.4 RETYPE the account ASSET -> INCOME, then recompute again -------------------
python3 "$DIR/a2-29-retype-path.py" "$DIR/out/A2-430-gl-drift-asset.json" > "$DIR/out/A2-434-retype-path.txt"
RETYPE_PATH=$(cat "$DIR/out/A2-434-retype-path.txt")
sh "$C8" A2-435-retype-asset-to-income PUT "$RETYPE_PATH" req/a2-29-retype-asset-to-income.json
sh "$C9" A2-436-recompute-2 POST "/journalentries?command=updateRunningBalance" \
      req/a2-29-update-running-balance-org.json a2-29-rb-org-0003

# --- C.5 a SECOND entry after the retype, then a third recompute --------------------
# If the seed query primes from the stale stored value, this row is computed FRESH and
# flagged calculated=true while still being wrong. If it does not, this row agrees.
python3 "$DIR/mkje-a2-29.py" \
    "$DIR/out/A2-431-gl-drift-liability.json" \
    "$DIR/out/A2-430-gl-drift-asset.json" \
    "01 August 2026" 50000000 \
    "A2-29 drift probe leg 2: posted after glCode 19929 was retyped to INCOME. Dated 01 August 2026 because the oracle REFUSED 01 September 2026 as a future date -- see out/A2-437-je-after-retype-futuredate.json, HTTP 403 error.msg.glJournalEntry.invalid.future.date, kept as the observation it is" \
    "$DIR/req/a2-29-je-2-after-retype.json"
sh "$C9" A2-437-je-after-retype POST /journalentries req/a2-29-je-2-after-retype.json a2-29-je-2-0001
sh "$C9" A2-438-recompute-3 POST "/journalentries?command=updateRunningBalance" \
      req/a2-29-update-running-balance-org.json a2-29-rb-org-0004
