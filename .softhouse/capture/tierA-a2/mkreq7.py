#!/usr/bin/env python3
"""A2-7 request bodies.

Written by task A2-7. ADDITIVE ONLY: every filename below is new (a2-7-*), so this
script cannot overwrite an existing request body. That is the defect D-1 recorded in
FLAGGED-NOT-REPRODUCIBLE.txt — mkreq2.py rewrote the bodies its captures had been taken
against, which stranded 30 real oracle responses with false recipes. The guard here is
mechanical, not a promise: the script REFUSES to write any path that already exists.

Account ids referenced below are NOT guessed. They are read back from the live oracle in
out/A2-200-glaccounts-live-precheck.json (GET /glaccounts, HTTP 200) and each one is
re-read individually in out/A2-201..A2-209. The nine slots are the nine that
LoanProductDataValidator marks notNull() for cash AND accrual accounting
[fineract@426a23544 fineract-provider/src/main/java/org/apache/fineract/portfolio/
loanproduct/serialization/LoanProductDataValidator.java].

  slot (CashAccountsForLoan ordinal)      gl id  gl code  observed type
  FUND_SOURCE (1)                            16  10300    ASSET
  LOAN_PORTFOLIO (2)                          4  10201    ASSET
  INTEREST_ON_LOANS (3)                       8  40100    INCOME
  INCOME_FROM_FEES (4)                        9  40200    INCOME
  INCOME_FROM_PENALTIES (5)                  10  40300    INCOME
  LOSSES_WRITTEN_OFF (6)                     13  50100    EXPENSE
  TRANSFERS_SUSPENSE (10)                    17  10400    ASSET
  OVERPAYMENT (11)                            6  20100    LIABILITY
  INCOME_FROM_RECOVERY (12)                  11  40400    INCOME

Deliberately ABSENT from a2-7-prod-210: goodwillCreditAccountId and
chargeOffExpenseAccountId. Both are ignoreIfNull() at product creation. Leaving them
unmapped is the instrument that measures whether the RUNTIME posting paths require
accounts the CREATION validator does not.
"""
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
REQ = os.path.join(DIR, "req")

NINE_MANDATORY = {
    "fundSourceAccountId": 16,
    "loanPortfolioAccountId": 4,
    "transfersInSuspenseAccountId": 17,
    "interestOnLoanAccountId": 8,
    "incomeFromFeeAccountId": 9,
    "incomeFromPenaltyAccountId": 10,
    "incomeFromRecoveryAccountId": 11,
    "writeOffAccountId": 13,
    "overpaymentLiabilityAccountId": 6,
}

PRODUCT_SHELL = {
    "description": "A2-7 capture: product-to-account mapping",
    "currencyCode": "MNT",
    "digitsAfterDecimal": 2,
    "inMultiplesOf": 0,
    "principal": 1200000,
    "numberOfRepayments": 6,
    "repaymentEvery": 1,
    "repaymentFrequencyType": 2,
    "interestRatePerPeriod": 0,
    "interestRateFrequencyType": 3,
    "amortizationType": 1,
    "interestType": 0,
    "interestCalculationPeriodType": 1,
    "transactionProcessingStrategyCode": "mifos-standard-strategy",
    "daysInYearType": 1,
    "daysInMonthType": 1,
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
    "isInterestRecalculationEnabled": False,
    "accountingRule": 2,
}

FILES = {}

# --- the deliverable: a cash product carrying EXACTLY the nine mandatory slots.
p = dict(PRODUCT_SHELL)
p["shortName"] = "A7M1"
p["name"] = "A2-7 Cash Nine Mandatory Only"
p.update(NINE_MANDATORY)
FILES["a2-7-prod-210-cash-nine-mandatory.json"] = p

# --- counterfactual: the same mapping block that prod-061 sent and the oracle ACCEPTED
# as product 23 (fundSourceAccountId 2), re-sent now that GL account 2 has been retyped
# ASSET -> INCOME by the already-captured A2-111-update-retype-mapped. Whatever the
# oracle answers is the observation; nothing here predicts it.
p = dict(PRODUCT_SHELL)
p["shortName"] = "A7M2"
p["name"] = "A2-7 Cash Fund Source Account 2 After Retype"
p.update(NINE_MANDATORY)
p["fundSourceAccountId"] = 2
FILES["a2-7-prod-214-fundsource-retyped-account.json"] = p

# --- loan on the nine-mandatory product. productId is filled in at run time from the
# observed POST /loanproducts response, never assumed: see run-200-a2-7.sh.
FILES["a2-7-loan-220.json"] = {
    "clientId": 1,
    "productId": "__PRODUCT_ID__",
    "principal": 1200000,
    "loanTermFrequency": 6,
    "loanTermFrequencyType": 2,
    "numberOfRepayments": 6,
    "repaymentEvery": 1,
    "repaymentFrequencyType": 2,
    "interestRatePerPeriod": 0,
    "interestType": 0,
    "amortizationType": 1,
    "interestCalculationPeriodType": 1,
    "transactionProcessingStrategyCode": "mifos-standard-strategy",
    "expectedDisbursementDate": "01 February 2026",
    "submittedOnDate": "01 February 2026",
    "loanType": "individual",
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}

FILES["a2-7-approve-221.json"] = {
    "approvedOnDate": "01 February 2026",
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}

FILES["a2-7-disburse-222.json"] = {
    "actualDisbursementDate": "01 February 2026",
    "transactionAmount": 1200000,
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}

# runtime probes. Each names ONE accounting slot.
FILES["a2-7-chargeoff-224.json"] = {
    "transactionDate": "01 March 2026",
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}
FILES["a2-7-goodwill-225.json"] = {
    "transactionDate": "01 March 2026",
    "transactionAmount": 100000,
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}
FILES["a2-7-repayment-226.json"] = {
    "transactionDate": "01 March 2026",
    "transactionAmount": 200000,
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}
FILES["a2-7-writeoff-228.json"] = {
    "transactionDate": "01 April 2026",
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}
FILES["a2-7-recovery-230.json"] = {
    "transactionDate": "01 May 2026",
    "transactionAmount": 50000,
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}

# --- the UPDATE-path probe. validateForCreate makes nine accounts notNull() and, for
# accrual, three receivables as well. validateForUpdate (LoanProductDataValidator.java:
# 1333) marks EVERY one of those the same ignoreIfNull(), including accountingRule
# itself at :1796. So this body switches a CASH product to ACCRUAL PERIODIC while
# supplying none of the three receivable accounts that creating an accrual product
# requires. Whether the oracle accepts it is the observation.
FILES["a2-7-upd-240-cash-to-accrual.json"] = {
    "accountingRule": 3,
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}

# --- the other half of the same probe: an update that does NOT change the accounting
# rule and supplies NO account parameter at all. Same endpoint, same product, same
# absence of accounts; only the rule change is removed. Varying exactly one thing is
# what makes A2-240's answer attributable.
FILES["a2-7-upd-242-no-rule-change.json"] = {
    "description": "A2-7 update: no accounting rule change, no account parameters",
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
}


def main():
    """Idempotent, and REFUSES to change a byte it did not itself just produce.

    D-1 (FLAGGED-NOT-REPRODUCIBLE.txt) happened because mkreq2.py silently rewrote
    request bodies that captures had already been taken against, so 30 real oracle
    responses now carry recipes that cannot regenerate them. The guard is therefore not
    "these names are new" — that is a promise, and P-22 says a promise is not a guard.
    It is a byte comparison: an existing file whose content already equals what this
    script would write is left ALONE (rerunning is safe and provably a no-op); an
    existing file whose content DIFFERS aborts the whole run with a non-zero exit and
    writes nothing at all.
    """
    os.makedirs(REQ, exist_ok=True)
    rendered = {n: json.dumps(b, indent=2) + "\n" for n, b in FILES.items()}

    conflicts = []
    for n, text in sorted(rendered.items()):
        p = os.path.join(REQ, n)
        if os.path.exists(p) and open(p).read() != text:
            conflicts.append(n)
    if conflicts:
        print("REFUSING, and writing NOTHING: these request bodies exist on disk with "
              "DIFFERENT content. Rewriting a body a capture was taken against is "
              "defect D-1:\n  " + "\n  ".join(conflicts), file=sys.stderr)
        return 1

    for n, text in sorted(rendered.items()):
        p = os.path.join(REQ, n)
        if os.path.exists(p):
            print("unchanged req/" + n)
            continue
        with open(p, "w") as f:
            f.write(text)
        print("wrote     req/" + n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
