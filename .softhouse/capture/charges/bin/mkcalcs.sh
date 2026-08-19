#!/bin/sh
# T40 — build the charge-bearing calc requests from the COMMITTED B-01 baseline request.
#
# Method: pure TEXT substitution of one line (` "locale": "en",`) in
# .softhouse/capture/pathb/req/calc-B-01-baseline.json.  Nothing else in the payload is
# touched, so every numeric literal that the zero-charge control just proved reproduces
# byte-for-byte stays byte-identical.  No JSON parse, no re-serialise, no float.
#
# The ONLY difference between each FC-nn request and the control request is the injected
# `charges` array.  That is what makes the comparison a controlled experiment: any cell
# that moves, moved because of the charge.
#
# Charge ids (created by bin/create-charges.sh, m_charge ids 1..10 on tenant `gerege`):
#   1 FLAT / DISBURSEMENT        15000     fee
#   2 FLAT / INSTALMENT_FEE       2500     fee
#   3 PCT_OF_AMOUNT / DISBURSEMENT      1.2345%  fee
#   4 PCT_OF_INTEREST / INSTALMENT_FEE  3.75%    fee
#   5 PCT_OF_AMOUNT_AND_INTEREST / INSTALMENT_FEE 1.2345% fee
#   6 FLAT / SPECIFIED_DUE_DATE   7500     PENALTY
#   7 FLAT / SPECIFIED_DUE_DATE   9000     fee
#   8 FLAT / INSTALMENT_FEE       1200     PENALTY
#   9 PCT_OF_AMOUNT / INSTALMENT_FEE     0.5%     fee
#  10 PCT_OF_AMOUNT / SPECIFIED_DUE_DATE 1.2345%  fee
#
# Baseline period boundaries observed in B-01 (fromDate -> dueDate):
#   p1 2026-01-01 -> 2026-02-01 ... p3 2026-03-01 -> 2026-04-01 ...
#   p6 2026-06-01 -> 2026-07-01 ... p12 2026-12-01 -> 2027-01-01
set -eu
W="${T40_WORKTREE:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
CH=$W/.softhouse/capture/charges
BASE=$W/.softhouse/capture/pathb/req/calc-B-01-baseline.json
R=$CH/req

# mk <id> <charges-array-body-on-one-or-more-lines>
mk() {
  _id=$1; _body=$2
  awk -v body="$_body" '
    $0 == " \"locale\": \"en\"," { print " \"charges\": [" body " ],"; print; next }
    { print }
  ' "$BASE" > "$R/calc-$_id.json"
  # fail loudly if the anchor line was not found
  grep -q '"charges"' "$R/calc-$_id.json" || { echo "ANCHOR NOT FOUND for $_id" >&2; exit 1; }
  # the ONLY added lines must be the charges block; principal/product/dates unchanged
  d=$(diff "$BASE" "$R/calc-$_id.json" | grep -c '^[<>]' || true)
  echo "  calc-$_id.json  (added lines: $d)"
}

# `amount` is MANDATORY on every loan-charge element — the oracle answered HTTP 400
# `validation.msg.loan.charges.amount.cannot.be.blank` when it was omitted [OBSERVED].
# The value repeats the charge definition's own amount exactly, as exact decimal text.
mk FC-01-flat-disbursement            '\n  { "chargeId": 1, "amount": 15000 }'
mk FC-02-flat-instalment              '\n  { "chargeId": 2, "amount": 2500 }'
mk FC-03-pctamount-disbursement       '\n  { "chargeId": 3, "amount": 1.2345 }'
mk FC-04-pctinterest-instalment       '\n  { "chargeId": 4, "amount": 3.75 }'
mk FC-05-pctamountinterest-instalment '\n  { "chargeId": 5, "amount": 1.2345 }'
mk FC-06-penalty-inside-p3            '\n  { "chargeId": 6, "amount": 7500, "dueDate": "15 March 2026" }'
mk FC-07-fee-on-p3-duedate            '\n  { "chargeId": 7, "amount": 9000, "dueDate": "01 April 2026" }'
mk FC-08-penalty-instalment           '\n  { "chargeId": 8, "amount": 1200 }'
mk FC-09-pctamount-instalment         '\n  { "chargeId": 9, "amount": 0.5 }'
mk FC-10-pctamount-inside-p6          '\n  { "chargeId": 10, "amount": 1.2345, "dueDate": "15 June 2026" }'
mk FC-11-fee-on-disbursement-date     '\n  { "chargeId": 7, "amount": 9000, "dueDate": "01 January 2026" }'
mk FC-12-fee-on-final-duedate         '\n  { "chargeId": 7, "amount": 9000, "dueDate": "01 January 2027" }'
mk FC-13-fee-inside-p12               '\n  { "chargeId": 7, "amount": 9000, "dueDate": "31 December 2026" }'
mk FC-14-fee-inside-p1                '\n  { "chargeId": 7, "amount": 9000, "dueDate": "20 January 2026" }'
mk FC-15-combined-fee-and-penalty     '\n  { "chargeId": 1, "amount": 15000 },\n  { "chargeId": 2, "amount": 2500 },\n  { "chargeId": 6, "amount": 7500, "dueDate": "15 March 2026" },\n  { "chargeId": 8, "amount": 1200 }'
