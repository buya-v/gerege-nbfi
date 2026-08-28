#!/usr/bin/env python3
"""T388 -- emit the thirteen GL-account creation bodies under req/.

WHY A GENERATOR AND NOT THIRTEEN HAND-TYPED FILES. The point of these accounts is
that they are DISJOINT from every GL account any PROMOTED vector reads. Generating
them from one table keeps the slot -> account correspondence in a single place that
a reader can check against the ported AccrualAccountsForLoan enum
(nexus/internal/apps/ledger/slots.go).

NO FLOAT ANYWHERE. This script emits no monetary value at all; a GL account carries
none. There is no numeric money field in scope.
"""
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
REQ = os.path.join(DIR, "req")

# Fineract GLAccountType ordinals [VERIFIED against the live tenant:
# out/T388-B03-before-per-account.txt shows gl_code 10000 Assets classification_enum 1,
# 20000 Liabilities 2, 30000 Equity 3, 40000 Income 4, 50000 Expenses 5].
ASSET, LIABILITY, EQUITY, INCOME, EXPENSE = 1, 2, 3, 4, 5
DETAIL = 1

# (file stem, slot code, AccrualAccountsForLoan name, gl code, account name, type)
ACCOUNTS = [
    ("G01-gl-fund-source",           1, "FUND_SOURCE",           "T388-1000", "T388 Accrual Fund Source",    ASSET),
    ("G02-gl-loan-portfolio",        2, "LOAN_PORTFOLIO",        "T388-1100", "T388 Accrual Loan Portfolio", ASSET),
    ("G03-gl-interest-on-loans",     3, "INTEREST_ON_LOANS",     "T388-4000", "T388 Interest On Loans",      INCOME),
    ("G04-gl-income-from-fees",      4, "INCOME_FROM_FEES",      "T388-4100", "T388 Income From Fees",       INCOME),
    ("G05-gl-income-from-penalties", 5, "INCOME_FROM_PENALTIES", "T388-4200", "T388 Income From Penalties",  INCOME),
    ("G06-gl-losses-written-off",    6, "LOSSES_WRITTEN_OFF",    "T388-5000", "T388 Losses Written Off",     EXPENSE),
    ("G07-gl-interest-receivable",   7, "INTEREST_RECEIVABLE",   "T388-1200", "T388 Interest Receivable",    ASSET),
    ("G08-gl-fees-receivable",       8, "FEES_RECEIVABLE",       "T388-1300", "T388 Fees Receivable",        ASSET),
    ("G09-gl-penalties-receivable",  9, "PENALTIES_RECEIVABLE",  "T388-1400", "T388 Penalties Receivable",   ASSET),
    ("G10-gl-transfers-suspense",   10, "TRANSFERS_SUSPENSE",    "T388-1500", "T388 Transfers Suspense",     ASSET),
    ("G11-gl-overpayment",          11, "OVERPAYMENT",           "T388-2000", "T388 Overpayment Liability",  LIABILITY),
    ("G12-gl-income-from-recovery", 12, "INCOME_FROM_RECOVERY",  "T388-4300", "T388 Income From Recovery",   INCOME),
    ("G13-gl-goodwill-credit",      13, "GOODWILL_CREDIT",       "T388-5100", "T388 Goodwill Credit",        EXPENSE),
]


def main():
    os.makedirs(REQ, exist_ok=True)
    for stem, slot, slotname, code, name, gltype in ACCOUNTS:
        body = {
            "name": name,
            "glCode": code,
            "manualEntriesAllowed": True,
            "type": gltype,
            "usage": DETAIL,
            "description": (
                "T388 accrual capture: AccrualAccountsForLoan slot %d %s. "
                "A NEW account created by T388, so that no GL account any PROMOTED "
                "vector reads is moved by this capture." % (slot, slotname)
            ),
        }
        path = os.path.join(REQ, stem + ".json")
        with open(path, "w") as fh:
            fh.write(json.dumps(body, separators=(",", ":")))
        print("wrote req/%s.json  slot %-2d %s" % (stem, slot, slotname))
    return 0


if __name__ == "__main__":
    sys.exit(main())
