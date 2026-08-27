#!/usr/bin/env python3
"""A2 product-to-account-mapping request bodies.

GL account ids assumed (created by run-020-accounts.sh on a fresh `gerege`):
   1 Assets                 ASSET   HEADER
   2 Fund Source            ASSET   DETAIL
   3 Current Assets         ASSET   HEADER
   4 Loan Portfolio         ASSET   DETAIL
   5 Liabilities            LIAB    HEADER
   6 Overpayment Liability  LIAB    DETAIL
   7 Income                 INCOME  HEADER
   8 Interest On Loans      INCOME  DETAIL
   9 Income From Fees       INCOME  DETAIL
  10 Income From Penalties  INCOME  DETAIL
  11 Recoveries             INCOME  DETAIL
  12 Expenses               EXPENSE HEADER
  13 Losses Written Off     EXPENSE DETAIL
  14 Goodwill Credit        EXPENSE DETAIL
  15 Equity                 EQUITY  HEADER
  16 Fund Source Alternate  ASSET   DETAIL   <- payment-channel override target
  17 Disabled Asset         ASSET   DETAIL   <- transfers in suspense
  18 No Manual Entries      ASSET   DETAIL

MONEY: `principal` is written as a bare integer. No float literal appears in any
monetary field of any payload below. `interestRatePerPeriod` is a RATE, not money.
"""
import json, os, copy

REQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "req")


def w(name, obj):
    with open(os.path.join(REQ, name + ".json"), "w") as f:
        json.dump(obj, f)
        f.write("\n")
    print("wrote", name)


BASE = {
    "shortName": None,           # filled per product
    "name": None,
    "description": "A2 capture: product-to-account mapping",
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
}

CASH_MAP = {
    "fundSourceAccountId": 2,
    "loanPortfolioAccountId": 4,
    "transfersInSuspenseAccountId": 17,
    "interestOnLoanAccountId": 8,
    "incomeFromFeeAccountId": 9,
    "incomeFromPenaltyAccountId": 10,
    "incomeFromRecoveryAccountId": 11,
    "writeOffAccountId": 13,
    "goodwillCreditAccountId": 14,
    "overpaymentLiabilityAccountId": 6,
}


def prod(short, name, rule, extra=None):
    p = copy.deepcopy(BASE)
    p["shortName"] = short
    p["name"] = name
    p["accountingRule"] = rule
    if extra:
        p.update(extra)
    return p


# --- P1: CASH accounting, full mapping, PLUS a payment-channel override.
# Payment type 1 (Money Transfer) is re-pointed to GL 16 (Fund Source Alternate).
# Every other payment type must fall through to the generic fund source, GL 2.
w("prod-060-cash-with-channel-override", prod(
    "A2C1", "A2 Cash Mapping With Channel Override", 2,
    dict(CASH_MAP, paymentChannelToFundSourceMappings=[
        {"paymentTypeId": 1, "fundSourceAccountId": 16},
    ])))

# --- P2: CASH accounting, generic mapping only, NO channel override.
w("prod-061-cash-no-override", prod(
    "A2C2", "A2 Cash Mapping No Override", 2, dict(CASH_MAP)))

# --- refusal probes on the mapping ---
# a HEADER account used as the loan portfolio (must a mapped account be DETAIL?)
w("prod-062-map-header-account", prod(
    "A2R1", "A2 Map Header Account", 2, dict(CASH_MAP, loanPortfolioAccountId=1)))
# an INCOME account where an ASSET is expected (is the GL TYPE checked?)
w("prod-063-map-wrong-type", prod(
    "A2R2", "A2 Map Wrong Type", 2, dict(CASH_MAP, fundSourceAccountId=8)))
# accounting enabled but not one mapping supplied
w("prod-064-cash-no-mappings", prod("A2R3", "A2 Cash No Mappings", 2))
# a GL account id that does not exist
w("prod-065-map-missing-account", prod(
    "A2R3b", "A2 Map Missing Account", 2, dict(CASH_MAP, fundSourceAccountId=99999)))
# channel override naming a payment type that does not exist
w("prod-066-bad-paymenttype", prod(
    "A2R4", "A2 Bad Payment Type", 2,
    dict(CASH_MAP, paymentChannelToFundSourceMappings=[
        {"paymentTypeId": 9999, "fundSourceAccountId": 16}])))
# TWO channel overrides for the SAME payment type — acc_product_mapping has no
# unique constraint over (product, type, payment_type), so this is a real question:
# does the oracle refuse it, or store two rows and resolve one of them?
w("prod-067-duplicate-channel", prod(
    "A2R5", "A2 Duplicate Channel", 2,
    dict(CASH_MAP, paymentChannelToFundSourceMappings=[
        {"paymentTypeId": 1, "fundSourceAccountId": 16},
        {"paymentTypeId": 1, "fundSourceAccountId": 2}])))
# ACCRUAL_PERIODIC (3) supplied with only the CASH mapping set — the three
# receivable accounts are absent.
w("prod-068-accrual-missing-receivables", prod(
    "A2R6", "A2 Accrual Missing Receivables", 3, dict(CASH_MAP)))
# ACCRUAL_PERIODIC, complete
w("prod-069-accrual-complete", prod(
    "A2A1", "A2 Accrual Complete", 3,
    dict(CASH_MAP, receivableInterestAccountId=18,
         receivableFeeAccountId=22, receivablePenaltyAccountId=16)))

# --- update payloads ---
# re-point the generic fund source 2 -> 16 on P2. Does the oracle UPDATE the
# existing acc_product_mapping row, or append a second one?
w("upd-070-repoint-fundsource", {"fundSourceAccountId": 16, "locale": "en"})
# add a channel override to P2 by update
w("upd-071-add-channel", {"locale": "en", "paymentChannelToFundSourceMappings": [
    {"paymentTypeId": 2, "fundSourceAccountId": 16}]})

if __name__ == "__main__":
    pass
