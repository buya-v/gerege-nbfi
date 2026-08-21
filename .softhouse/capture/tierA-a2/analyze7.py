#!/usr/bin/env python3
"""Derive the A2-7 runtime-vs-creation account table from the committed captures.

NO FLOATING POINT ANYWHERE (P-25: the no-float rule binds analysis scripts too — a float
here is a money defect one remove, and this script's output is read as evidence about
money). Every amount is parsed with `parse_float=decimal.Decimal`, so the JSON literal
`1200000.0` becomes Decimal('1200000.0') and never a binary double; totals are summed as
Decimal and compared exactly. `decimal` is used rather than int-minor-units because these
bytes are the ORACLE's own wire representation and re-scaling them here would be a
transformation this script has no mandate to make — the point is to report what came
back, exactly.

  python3 analyze7.py
"""
import decimal
import json
import os

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, "out")

# CashAccountsForLoan, fineract@426a23544
# fineract-core/src/main/java/org/apache/fineract/accounting/common/AccountingConstants.java:37-62
SLOT_BY_GL_ID = {
    16: "FUND_SOURCE(1)",
    4: "LOAN_PORTFOLIO(2)",
    8: "INTEREST_ON_LOANS(3)",
    9: "INCOME_FROM_FEES(4)",
    10: "INCOME_FROM_PENALTIES(5)",
    13: "LOSSES_WRITTEN_OFF(6)",
    17: "TRANSFERS_SUSPENSE(10)",
    6: "OVERPAYMENT(11)",
    11: "INCOME_FROM_RECOVERY(12)",
}


def load(name):
    with open(os.path.join(OUT, name)) as f:
        return json.load(f, parse_float=decimal.Decimal)


def main():
    d = load("A2-235-je-after-recovery.json")
    rows = d["pageItems"]
    print(f"journal entries on loan 5 (product 46, nine mandatory slots only): "
          f"{d['totalFilteredRecords']} rows\n")

    by_txn = {}
    for r in rows:
        by_txn.setdefault(r["transactionId"], []).append(r)

    debits = decimal.Decimal(0)
    credits = decimal.Decimal(0)
    touched = {}
    for txn in sorted(by_txn, key=lambda t: (len(t), t)):
        print(f"  transactionId {txn}")
        for r in sorted(by_txn[txn], key=lambda x: x["id"]):
            side = r["entryType"]["value"]
            amt = r["amount"]
            gl = r["glAccountId"]
            slot = SLOT_BY_GL_ID.get(gl, "NOT-A-MANDATORY-SLOT")
            touched.setdefault(slot, set()).add(txn)
            print(f"    je#{r['id']:<3} {side:<6} {amt!s:>12}  "
                  f"gl {gl} {r['glAccountCode']} {r['glAccountName']:<24} "
                  f"[{r['glAccountType']['value']}] -> {slot}")
            if side == "DEBIT":
                debits += amt
            else:
                credits += amt
        print()

    print(f"  total DEBIT  = {debits}")
    print(f"  total CREDIT = {credits}")
    print(f"  double-entry balances exactly (Decimal, no float): {debits == credits}\n")

    print("  which of the NINE creation-mandatory slots were actually posted to:")
    for slot in sorted(set(SLOT_BY_GL_ID.values())):
        t = touched.get(slot)
        print(f"    {slot:<26} {'POSTED in ' + ','.join(sorted(t)) if t else 'NEVER POSTED'}")

    unmapped = [s for s in touched if s == "NOT-A-MANDATORY-SLOT"]
    if unmapped:
        print("\n  NOTE: at least one posting hit a GL account outside the nine "
              "mandatory slots.")


if __name__ == "__main__":
    main()
