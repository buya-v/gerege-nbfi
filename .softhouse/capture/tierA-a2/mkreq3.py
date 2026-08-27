#!/usr/bin/env python3
"""A2 RESOLUTION probe payloads.

The point of these: product 22 carries BOTH
  - a generic FUND_SOURCE mapping (financial_account_type=1, payment_type NULL) -> GL 2
  - a payment-channel override           (financial_account_type=1, payment_type=1)    -> GL 16
Disbursing with paymentTypeId 1 vs paymentTypeId 2 makes the oracle CHOOSE, and the
journal entry it writes names the account that actually resolved. Nothing else in
this slice answers that question.

MONEY: every amount below is a bare integer. `principal` 1200000 MNT. No float
literal appears anywhere in this file.
"""
import json, os, copy

REQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "req")


def w(name, obj):
    with open(os.path.join(REQ, name + ".json"), "w") as f:
        json.dump(obj, f)
        f.write("\n")
    print("wrote", name)


def loan(product_id, client_id=1):
    return {
        "clientId": client_id,
        "productId": product_id,
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


w("loan-080-on-product22-a", loan(22))
w("loan-081-on-product22-b", loan(22))
w("loan-082-on-product27-dup", loan(27))

w("approve-083", {"approvedOnDate": "01 February 2026",
                  "approvedLoanAmount": 1200000,
                  "locale": "en", "dateFormat": "dd MMMM yyyy"})

# DISBURSE with payment type 1 — the OVERRIDDEN channel. Expected to resolve GL 16
# if the payment-type-specific row wins; GL 2 if the generic row wins.
w("disburse-084-paymenttype1", {"actualDisbursementDate": "01 February 2026",
                                "transactionAmount": 1200000,
                                "paymentTypeId": 1,
                                "locale": "en", "dateFormat": "dd MMMM yyyy"})
# DISBURSE with payment type 2 — NO override row exists for it. This is the
# RESOLUTION MISS on the payment-type dimension: the fallback path.
w("disburse-085-paymenttype2", {"actualDisbursementDate": "01 February 2026",
                                "transactionAmount": 1200000,
                                "paymentTypeId": 2,
                                "locale": "en", "dateFormat": "dd MMMM yyyy"})
# DISBURSE with NO paymentTypeId at all — the second miss shape.
w("disburse-086-nopaymenttype", {"actualDisbursementDate": "01 February 2026",
                                 "transactionAmount": 1200000,
                                 "locale": "en", "dateFormat": "dd MMMM yyyy"})

if __name__ == "__main__":
    pass
