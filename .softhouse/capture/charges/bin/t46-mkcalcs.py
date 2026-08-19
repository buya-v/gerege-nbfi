#!/usr/bin/env python3
"""T46 -- author the new charge requests that close T44 findings A-3 and A-5.

NEW IDS, NEW PASS.  `patterns.md`: new cases belong in a new pass with new ids, never mixed
into a re-emission.  Nothing under `req/calc-FC-*.json` or `req/charge-*.json` is touched, and
NO charge definition is created, modified or deleted -- T40's ids 1-12 are used exactly as
they stand.

Every request body is emitted as TEXT.  No Python float is constructed anywhere in this file:
the amounts below are string literals and are written into the JSON verbatim, so
`0.021875` reaches the wire as the six characters after the point, not as a binary double.

WHAT EACH SHAPE DISCRIMINATES
-----------------------------
A-3 -- "the charge corpus cannot see which input supplies the money".  T40 always set the
       request `amount` EQUAL to the definition's `m_charge.amount`, so no capture could tell
       "the definition governs" from "the request governs".  T46-CH-01..05 make them DISAGREE,
       on five different charge_calculation_enum values, and the observed fee says which wins.
       The two possible outcomes are written into each file's `_t46_note` so the discrimination
       is legible before the run, not chosen after it.

A-5 -- "§11's arithmetic proof that no half-cent tie exists at that base is false".  Period 1's
       interest is 21,600.00 [T40 handoff §5, capture FC-04 / control B-01].  A percent-of-
       interest charge at rate p yields 21600 * p/100 = 216p.  T40 argued 216p can never end in
       ...5 at the third decimal.  It can: p = 0.021875 gives exactly 4.725 and p = 0.009375
       gives exactly 2.025 -- both exact terminating decimals, both exact half-cent ties.
       HALF_UP -> 4.73 / 2.03.  HALF_EVEN -> 4.72 / 2.02.  These are the rounding-mode canary
       INSIDE the charge arithmetic that T40 declared impossible.
"""
import pathlib

REQ = pathlib.Path(__file__).resolve().parent.parent / "req"

TEMPLATE = """{{
 "clientId": 1,
 "productId": 1,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "charges": [
  {{ "chargeId": {charge_id}, "amount": {amount} }} ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}}
"""

# id, charge_id, request amount (EXACT TEXT), what the definition says, what each reading predicts
CASES = [
    ("T46-CH-01-defvsreq-pctinterest", 4, "1.25",
     "m_charge id 4 = 3.750000 % of interest, INSTALMENT_FEE (charge_time_enum 8, "
     "charge_calculation_enum 4)",
     "DEFINITION governs -> period-1 fee 810.00 (3.75 % of 21,600.00); "
     "REQUEST governs -> period-1 fee 270.00 (1.25 % of 21,600.00)"),
    ("T46-CH-02-defvsreq-flat-disb", 1, "7777.77",
     "m_charge id 1 = 15000.000000 flat, DISBURSEMENT_FEE (time 1, calc 1)",
     "DEFINITION governs -> disbursement fee 15000.00; "
     "REQUEST governs -> disbursement fee 7777.77"),
    ("T46-CH-03-tie-pctinterest-4725", 4, "0.021875",
     "m_charge id 4 = 3.750000 % of interest, INSTALMENT_FEE",
     "REQUEST governs and 21,600.00 x 0.021875 % = 4.725 EXACTLY -- a half-cent tie. "
     "HALF_UP -> 4.73; HALF_EVEN -> 4.72"),
    ("T46-CH-04-tie-pctinterest-2025", 4, "0.009375",
     "m_charge id 4 = 3.750000 % of interest, INSTALMENT_FEE",
     "REQUEST governs and 21,600.00 x 0.009375 % = 2.025 EXACTLY -- a half-cent tie. "
     "HALF_UP -> 2.03; HALF_EVEN -> 2.02"),
    ("T46-CH-05-defvsreq-pctamtint", 5, "2.5",
     "m_charge id 5 = 1.234500 % of amount PLUS interest, INSTALMENT_FEE (time 8, calc 3)",
     "DEFINITION governs -> the FC-05 fee column; REQUEST governs -> roughly 2x it "
     "(2.5 / 1.2345). The observed ratio decides."),
    ("T46-CH-06-defvsreq-pctamount-disb", 3, "0.5",
     "m_charge id 3 = 1.234500 % of amount, DISBURSEMENT_FEE (time 1, calc 2)",
     "DEFINITION governs -> disbursement fee 14814.00 (1.2345 % of 1,200,000); "
     "REQUEST governs -> 6000.00 (0.5 % of 1,200,000)"),
    ("T46-CH-07-defvsreq-penalty-instalment", 8, "333.33",
     "m_charge id 8 = 1200.000000 flat PENALTY per instalment (time 8, calc 1, is_penalty true)",
     "DEFINITION governs -> penalty 1200.00 per period; "
     "REQUEST governs -> penalty 333.33 per period"),
]


def main():
    written = []
    for cid, charge_id, amount, definition, discriminates in CASES:
        body = TEMPLATE.format(charge_id=charge_id, amount=amount)
        assert amount in body, "amount text was mangled"
        path = REQ / f"calc-{cid}.json"
        path.write_text(body)
        written.append((path.name, charge_id, amount, definition, discriminates))

    print("T46 charge requests authored (new ids, new pass; no charge definition created "
          "or modified):")
    for name, charge_id, amount, definition, disc in written:
        print(f"\n  {name}")
        print(f"    request charges[0] : {{\"chargeId\": {charge_id}, \"amount\": {amount}}}")
        print(f"    definition         : {definition}")
        print(f"    discriminates      : {disc}")


if __name__ == "__main__":
    main()
