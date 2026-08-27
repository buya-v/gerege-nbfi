#!/bin/sh
# A2-26 / group E -- DOES THE REFERENCE ORACLE HONOUR `Idempotency-Key` ON A LEDGER POST?
#
# "`Idempotency-Key` is mandatory on every money-movement POST" is a Gerege
# non-negotiable, and the whole A2 corpus contains ZERO observation of what the reference
# oracle does with one: cap.sh and cap8.sh never send the header, and run-220's own
# header says so and carries it as a follow-up. So the port has a mandatory behaviour
# with no oracle evidence behind it in this slice.
#
# The probe is the smallest one that can decide it: POST the SAME manual journal entry
# body TWICE under the SAME key, then count the rows that actually landed in the ledger.
# A ledger POST is the right surface -- a duplicate is directly visible as duplicate
# journal-entry rows, with no loan state to reason through.
#
#   A2-360  first  POST, key K            -> whatever the oracle says
#   A2-361  second POST, SAME key K       -> whatever the oracle says
#   A2-362  third  POST, DIFFERENT key K2 -> the CONTROL. If A2-361 were suppressed for
#                                            any reason other than the key, A2-362 would
#                                            be suppressed too. Without this leg the
#                                            probe cannot tell idempotency from any other
#                                            duplicate-rejection.
#   A2-363  read back every entry on 02 June 2026 and count.
#
# The key is a fixed literal, not generated, so this run is re-derivable: re-running it
# against a fresh oracle sends the identical bytes and identical header. Against THIS
# oracle a re-run is itself a further idempotency observation, which is a feature.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C9="$DIR/cap9.sh"
C8="$DIR/cap8.sh"

K1=a2-26-idem-probe-0000000000000001
K2=a2-26-idem-probe-0000000000000002

sh "$C9" A2-360-manual-je-idem-first  POST /journalentries req/a2-26-manual-je-idem.json "$K1" || exit 1
cat "$DIR/out/A2-360-manual-je-idem-first.json"; echo

sh "$C9" A2-361-manual-je-idem-repeat POST /journalentries req/a2-26-manual-je-idem.json "$K1" || exit 1
cat "$DIR/out/A2-361-manual-je-idem-repeat.json"; echo

sh "$C9" A2-362-manual-je-idem-control POST /journalentries req/a2-26-manual-je-idem.json "$K2" || exit 1
cat "$DIR/out/A2-362-manual-je-idem-control.json"; echo

sh "$C8" A2-363-je-office1-2june GET "/journalentries?officeId=1&fromDate=02%20June%202026&toDate=02%20June%202026&locale=en&dateFormat=dd%20MMMM%20yyyy&limit=100" || exit 1
