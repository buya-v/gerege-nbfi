#!/usr/bin/env python3
"""Transcribe the two schedules T21's auditor OBSERVED from the reference oracle
(Fineract) and printed in `.softhouse/reviews/t21v2/t21v2-probe-oracle-out.txt`
section B, so that pass 3i's PREDICTION can name every cell of them before pass 3i
runs.

This script OBSERVES NOTHING. It is a transcriber: its whole input is a committed
transcript on `main`, and its output is the prediction that pass 3i is then graded
against. Whether the transcript is right is exactly what pass 3i tests.

Section B of that transcript is:
    MNT 5,000,000 / 18 x 18.5%, currencyDecimalPlaces = 0,
    CurrencyData.inMultiplesOf  null (arm A)  vs  100 (arm B),
    (19, HALF_UP), start = disbursement = 2024-01-01, MONTHS/1,
    DAYS_30 / DAYS_360, DECLINING_BALANCE, no down payment.

Usage:  python3 extract-t21v2-AB.py <transcript> <out.json>
"""
import json
import re
import sys

MARKER = ('### MNT 5,000,000 / 18 x 18.5%   '
          'currency inMultiplesOf null vs 100 at decimalPlaces 0')

def main(transcript, outpath):
    src = open(transcript, encoding='utf-8').read()
    start = src.index(MARKER)
    end = src.index('======== C.', start)
    block = src[start:end]

    arms = {}
    cur = None
    for line in block.splitlines():
        s = line.strip()
        m = re.match(r'^([AB]): term=(\d+) disb=(\S+) int=(\S+) rep=(\S+)$', s)
        if m:
            cur = m.group(1)
            arms[cur] = {
                "loanTermInDays": int(m.group(2)),
                "totalDisbursedAmount": m.group(3),
                "totalInterestAmount": m.group(4),
                "totalRepaymentAmount": m.group(5),
                "periods": [],
            }
            continue
        m = re.match(r'^DISB (\S+) (\S+)$', s)
        if m and cur:
            arms[cur]["periods"].append(
                {"type": "DISBURSEMENT", "dueDate": m.group(1), "principal": m.group(2)})
            continue
        m = re.match(r'^REP  #(\d+) from=(\S+) due=(\S+) prin=(\S+) int=(\S+) '
                     r'fee=(\S+) pen=(\S+) tot=(\S+) bal=(\S+) totOut=(\S+)$', s)
        if m and cur:
            arms[cur]["periods"].append({
                "type": "REPAYMENT",
                "periodNumber": int(m.group(1)),
                "periodFromDate": m.group(2),
                "dueDate": m.group(3),
                "principal": m.group(4),
                "interest": m.group(5),
                "feeAmount": m.group(6),
                "penaltyAmount": m.group(7),
                "total": m.group(8),
                "balance": m.group(9),
                "totalOutstandingBalance": m.group(10),
            })
    if sorted(arms) != ['A', 'B']:
        sys.exit("expected arms A and B, got %r" % sorted(arms))
    for k in ('A', 'B'):
        if len(arms[k]["periods"]) != 19:
            sys.exit("arm %s has %d rows, expected 19" % (k, len(arms[k]["periods"])))
    json.dump(arms, open(outpath, 'w', encoding='utf-8'), indent=1)
    for k in ('A', 'B'):
        print("arm %s: term=%s interest=%s rows=%d"
              % (k, arms[k]["loanTermInDays"], arms[k]["totalInterestAmount"],
                 len(arms[k]["periods"])))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
