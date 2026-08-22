#!/bin/sh
# A2-29 / G-12 group F -- THE REPORT SURFACE.
#
# `GeneralLedgerReport Table` (stretchy_report id 194, use_report = true on THIS oracle)
# is the one installed report whose SQL touches office_running_balance. It touches it
# TWICE, and the two touches are not the same kind of read:
#
#   * `j1.office_running_balance as aftertxn` -- projected in the `details` subquery and
#     then NOT selected by the outer query, so it reaches no cell of the result;
#   * `je.office_running_balance is not null` -- a PREDICATE in the openingbalance
#     subquery, which is a read that can change the result set.
#
# [VERIFIED: fineract-provider/src/main/resources/db/changelog/tenant/parts/
#  0018_pentaho_reports_to_table.xml:153 (the PostgreSQL variant), and re-read from the
#  live oracle's own stretchy_report row -- see out/A2-470-db-report-194-sql.txt]
#
# On the ADOPTED schema the column is `DECIMAL(19,6) NOT NULL DEFAULT 0.000000`
# [VERIFIED: .../db/changelog/tenant/parts/0001_initial_schema.xml:166-171], so
# `is not null` is satisfied by every row and the predicate is a no-op HERE. It stops
# being a no-op the moment a port leaves the column NULL. That is the whole reason this
# batch exists: the question is not "does the report print the number" but "does the
# report's ROW SET depend on the column".
#
# Read-only: every request is a GET.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"

sh "$C" A2-471-report-generalledger GET "/runreports/GeneralLedgerReport%20Table?R_officeId=1&R_GLAccountNO=4&R_startDate=2026-01-01&R_endDate=2026-08-22&genericResultSet=true"

# The same report with a LATER start date, so the openingbalance subquery -- the one
# carrying the `office_running_balance is not null` predicate -- has rows to work on.
# A2-471's openingbalance is 0 in every row only because nothing predates its start date;
# that is not evidence about the predicate, so it gets a second run rather than a
# conclusion.
sh "$C" A2-472-report-generalledger-later-start GET "/runreports/GeneralLedgerReport%20Table?R_officeId=1&R_GLAccountNO=4&R_startDate=2026-05-01&R_endDate=2026-08-22&genericResultSet=true"
