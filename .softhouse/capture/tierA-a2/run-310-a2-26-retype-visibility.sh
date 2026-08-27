#!/bin/sh
# A2-26 / group B -- IS THE G-10 RETYPE VISIBLE IN THE JOURNAL-ENTRY READ-BACK?
#
# The driver's re-derivation behind G-10 says `acc_gl_journal_entry` carries no
# classification column, so retyping a GL account "retroactively re-renders every entry
# ever posted to it", and that is the stated reason trap (3) requires the Go port to
# carry classification ON THE ENTRY. That sentence was re-derived from source. It was
# never OBSERVED.
#
# It is observable, cheaply, and only from this fire: out/A2-088-journalentries-loan2.json
# was captured on 2026-08-21 and renders gl 2 as ASSET; gl 2 is INCOME in the database
# today (A2-150-db-final-state.txt, and re-confirmed live). Re-issuing the SAME request
# line and diffing the glAccountType block against the earlier capture answers it
# directly. Whatever comes back is the observation -- if the type is unchanged the
# re-derivation is wrong, and that is the more valuable outcome.
#
# Nothing here writes. Four GETs.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"

# Same request line as A2-088, re-issued today.
sh "$C" A2-320-je-loan2-retype-visibility GET "/journalentries?loanId=2&limit=50" || exit 1
# Same request line as A2-091c, re-issued today.
sh "$C" A2-321-je-loan4-retype-visibility GET "/journalentries?loanId=4&limit=50" || exit 1
# Same request line as A2-235, re-issued today: a control on accounts that were NOT retyped.
sh "$C" A2-322-je-loan5-control GET "/journalentries?loanId=5&limit=80" || exit 1
# The single journal entry row for je#4, whose account is the retyped one.
sh "$C" A2-323-je-entry4-single GET "/journalentries/4" || exit 1
