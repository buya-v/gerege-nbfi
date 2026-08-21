#!/usr/bin/env python3
"""A2 MISS-probe and financial-activity-account payloads.

MONEY: all amounts are bare integers.
"""
import json, os

REQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "req")


def w(n, o):
    with open(os.path.join(REQ, n + ".json"), "w") as f:
        json.dump(o, f)
        f.write("\n")
    print("wrote", n)


# Loan on product 24, whose LOAN_PORTFOLIO is mapped to a HEADER account (GL 1).
# The create was accepted; the question is whether a POSTING to a HEADER account
# is accepted too, or refused at journal-entry time.
w("loan-090-on-product24-header", {
    "clientId": 1, "productId": 24, "principal": 1200000,
    "loanTermFrequency": 6, "loanTermFrequencyType": 2, "numberOfRepayments": 6,
    "repaymentEvery": 1, "repaymentFrequencyType": 2, "interestRatePerPeriod": 0,
    "interestType": 0, "amortizationType": 1, "interestCalculationPeriodType": 1,
    "transactionProcessingStrategyCode": "mifos-standard-strategy",
    "expectedDisbursementDate": "01 February 2026",
    "submittedOnDate": "01 February 2026", "loanType": "individual",
    "locale": "en", "dateFormat": "dd MMMM yyyy"})

# Charge off loan 1. Product 22 carries NO CHARGE_OFF_EXPENSE mapping
# (CashAccountsForLoan.CHARGE_OFF_EXPENSE = 16 is absent from acc_product_mapping
# for product 22) — this is the genuine RESOLUTION MISS: the key is not there at all.
w("chargeoff-092", {"transactionDate": "01 March 2026",
                    "locale": "en", "dateFormat": "dd MMMM yyyy"})

# ---- financialactivityaccount ----
# valid: LIABILITY_TRANSFER(200) -> a LIABILITY account (GL 6)
w("fin-100-liability-transfer", {"financialActivityId": 200, "glAccountId": 6})
# valid: ASSET_TRANSFER(100) -> an ASSET account (GL 2)
w("fin-101-asset-transfer", {"financialActivityId": 100, "glAccountId": 2})
# refusal: duplicate activity — financial_activity_type is UNIQUE in the DDL
w("fin-102-duplicate-activity", {"financialActivityId": 200, "glAccountId": 21})
# refusal: ASSET_TRANSFER(100) pointed at a LIABILITY account — the
# FinancialActivity->GLAccountType pairing lives only in the Java enum, not the schema
w("fin-103-wrong-account-type", {"financialActivityId": 100, "glAccountId": 6})
# refusal: an activity value that is not one of {100,101,102,103,200,201,300}
w("fin-104-unknown-activity", {"financialActivityId": 232, "glAccountId": 2})
# refusal: GL account that does not exist
w("fin-105-missing-account", {"financialActivityId": 300, "glAccountId": 99999})
# HEADER account as a financial activity target — is usage checked here?
w("fin-106-header-account", {"financialActivityId": 300, "glAccountId": 15})
# update an existing mapping to a different GL account (observe the `changes` map)
w("fin-107-update", {"financialActivityId": 200, "glAccountId": 21})

# ---- glaccount update probes ----
# flip a HEADER that HAS children to DETAIL (GL 1 has children 2, 3, 21)
w("upd-110-header-to-detail", {"usage": 1})
# flip the TYPE of an account that is already mapped to a product (GL 2 -> INCOME)
w("upd-111-retype-mapped-account", {"type": 4})
# disable an account that is mapped and has journal entries (GL 2)
w("upd-112-disable-mapped", {"disabled": True})
# forbid manual entries on GL 2
w("upd-113-nomanual", {"manualEntriesAllowed": False})

if __name__ == "__main__":
    pass
