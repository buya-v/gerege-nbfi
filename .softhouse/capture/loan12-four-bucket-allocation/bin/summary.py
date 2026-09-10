#!/usr/bin/env python3
"""Summarise a loan detail read-back: the four-term summary and the newest
repayment transaction's four portions."""
import json
import sys

d = json.load(open(sys.argv[1]))
s = d.get('summary', {})
keys = ['principalOutstanding', 'interestOutstanding', 'feeChargesOutstanding',
        'penaltyChargesOutstanding', 'totalOutstanding']
print('summary: ' + '  '.join(f'{k}={s[k]}' for k in keys if k in s))
for t in d.get('transactions', []):
    if t.get('type', {}).get('code') == 'loanTransactionType.repayment' or t.get('type', {}).get('value') == 'Repayment':
        print(f"repayment txn {t['id']} date={t.get('date')} amount={t.get('amount')}")
        for k in ['principalPortion', 'interestPortion', 'feeChargesPortion', 'penaltyChargesPortion']:
            print(f"  {k}={t.get(k)}")
