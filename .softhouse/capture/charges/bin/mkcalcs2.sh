#!/bin/sh
# T40 pass 2 — boundary and separated-path calc requests.  Same text-substitution method
# as mkcalcs.sh: the only change from the committed B-01 request is the `charges` array.
#
# What each one is FOR (the discrimination target is stated in the handoff):
#  FC-16  fee due 01 Feb 2026 = period 1 dueDate = period 2 fromDate — upper boundary
#  FC-17  fee due 01 Mar 2027 = two months AFTER the final due date — off the end
#  FC-18  fee due 15 Dec 2025 = BEFORE the disbursement date — off the front
#  FC-19  PERCENT_OF_INTEREST specified-due-date fee, due inside period 6
#  FC-20  PERCENT_OF_INTEREST specified-due-date fee, due ON the disbursement date
#  FC-21  PERCENT_OF_AMOUNT_AND_INTEREST specified-due-date fee, due inside period 6
#  FC-22  PENALTY per instalment + PENALTY specified-due-date on the SAME period boundary
set -eu
W="${T40_WORKTREE:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
CH=$W/.softhouse/capture/charges
BASE=$W/.softhouse/capture/pathb/req/calc-B-01-baseline.json
R=$CH/req

mk() {
  _id=$1; _body=$2
  awk -v body="$_body" '
    $0 == " \"locale\": \"en\"," { print " \"charges\": [" body " ],"; print; next }
    { print }
  ' "$BASE" > "$R/calc-$_id.json"
  grep -q '"charges"' "$R/calc-$_id.json" || { echo "ANCHOR NOT FOUND for $_id" >&2; exit 1; }
  echo "  calc-$_id.json"
}

mk FC-16-fee-on-p1-duedate        '\n  { "chargeId": 7, "amount": 9000, "dueDate": "01 February 2026" }'
mk FC-17-fee-after-final-duedate  '\n  { "chargeId": 7, "amount": 9000, "dueDate": "01 March 2027" }'
mk FC-18-fee-before-disbursement  '\n  { "chargeId": 7, "amount": 9000, "dueDate": "15 December 2025" }'
mk FC-19-pctinterest-sdd-inside-p6 '\n  { "chargeId": 11, "amount": 3.75, "dueDate": "15 June 2026" }'
mk FC-20-pctinterest-sdd-on-disb  '\n  { "chargeId": 11, "amount": 3.75, "dueDate": "01 January 2026" }'
mk FC-21-pctamtint-sdd-inside-p6  '\n  { "chargeId": 12, "amount": 1.2345, "dueDate": "15 June 2026" }'
mk FC-22-penalty-instalment-plus-sdd-on-p3-duedate '\n  { "chargeId": 8, "amount": 1200 },\n  { "chargeId": 6, "amount": 7500, "dueDate": "01 April 2026" }'
