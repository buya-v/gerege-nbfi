#!/usr/bin/env python3
"""
T48 -- author the request payloads for the charge gaps T46 left open.

ADDITIVE, NEW IDS, NEW PASS.  Nothing under charges/req/ that already exists is touched;
every file this writes is named calc-T48-CH-*.json.  No committed observation is mutated.

MONEY NEVER PASSES THROUGH A FLOAT.  Every monetary literal below is authored as an exact
decimal string and written into the JSON with json.dumps' raw-literal escape hatch, so the
bytes on the wire are the characters written here.  Python floats are not used to hold any
amount.

THE FOUR GAPS (from .softhouse/handoff/T46-capture-corrections.md section 8):
  1. whether m_charge.amount governs when the request OMITS `amount` -- T46 established that
     when the request SUPPLIES it the request wins 7 for 7 and m_charge.amount is ignored,
     but every capture in the corpus supplies it, so the omission case is TO_BE_CAPTURED.
  2. chargeCalculationType 5 and 9.
  3. chargeTimeType 2 (SPECIFIED_DUE_DATE) with a DISAGREEING amount.
  4. RepaymentEvery > 3.

N46-1 (the ambient charge rounding mode) is NOT attempted: separating it requires a tenant
write on the SHARED server, which this task is forbidden to make.
"""
import json
import os
import pathlib

D = pathlib.Path(__file__).resolve().parents[1] / "req"

BASE = [
    ("clientId", 1), ("productId", 1), ("loanType", "individual"),
    ("principal", "1200000"), ("loanTermFrequency", 12), ("loanTermFrequencyType", 2),
    ("numberOfRepayments", 12), ("repaymentEvery", 1), ("repaymentFrequencyType", 2),
    ("interestRatePerPeriod", "21.6"), ("interestRateFrequencyType", 3),
    ("amortizationType", 1), ("interestType", 0), ("interestCalculationPeriodType", 1),
    ("transactionProcessingStrategyCode", "advanced-payment-allocation-strategy"),
    ("expectedDisbursementDate", "01 January 2026"), ("submittedOnDate", "01 January 2026"),
]
# keys whose values are exact decimal literals and must be emitted UNQUOTED but VERBATIM
RAW = {"principal", "interestRatePerPeriod", "amount"}


def render(pairs, charges=None):
    out = []
    for k, v in pairs:
        if k in RAW:
            out.append(' "%s": %s' % (k, v))
        elif isinstance(v, str):
            out.append(' "%s": %s' % (k, json.dumps(v)))
        else:
            out.append(' "%s": %s' % (k, json.dumps(v)))
    if charges is not None:
        cs = []
        for c in charges:
            parts = []
            for k, v in c:
                if k in RAW:
                    parts.append('"%s": %s' % (k, v))
                elif isinstance(v, str):
                    parts.append('"%s": %s' % (k, json.dumps(v)))
                else:
                    parts.append('"%s": %s' % (k, json.dumps(v)))
            cs.append("  { " + ", ".join(parts) + " }")
        out.append(' "charges": [\n' + ",\n".join(cs) + " ]")
    out.append(' "locale": "en"')
    out.append(' "dateFormat": "dd MMMM yyyy"')
    return "{\n" + ",\n".join(out) + "\n}\n"


def w(name, charges=None, **over):
    pairs = [(k, over.pop(k, v)) for k, v in BASE]
    assert not over, "unknown override %r" % over
    (D / name).write_text(render(pairs, charges))
    print("wrote", name)


# ---- gap 1 + gap 3: definition amount vs request amount --------------------------------
# m_charge rows on `gerege` as left by T40/T46 (read-only SELECT, fineract_gerege):
#   id 1  flat            chargeTimeType 1 (DISBURSEMENT)      amount 15000.000000
#   id 2  flat            chargeTimeType 8 (INSTALMENT_FEE)    amount  2500.000000
#   id 3  PERCENT_OF_AMOUNT  chargeTimeType 1                  amount     1.234500
#   id 7  flat            chargeTimeType 2 (SPECIFIED_DUE_DATE) amount 9000.000000
# Each pair below is IDENTICAL except for the presence of `amount`, so any cell that moves
# between them moved because of that one field.
w("calc-T48-CH-01-defamount-omitted-tt2.json",
  charges=[[("chargeId", 7), ("dueDate", "01 April 2026")]])
w("calc-T48-CH-02-defamount-disagree-tt2.json",
  charges=[[("chargeId", 7), ("amount", "4444"), ("dueDate", "01 April 2026")]])
w("calc-T48-CH-03-defamount-omitted-tt8.json", charges=[[("chargeId", 2)]])
w("calc-T48-CH-04-defamount-disagree-tt8.json", charges=[[("chargeId", 2), ("amount", "3333")]])
w("calc-T48-CH-05-defamount-omitted-tt1.json", charges=[[("chargeId", 1)]])
w("calc-T48-CH-06-defamount-disagree-tt1.json", charges=[[("chargeId", 1), ("amount", "5555")]])
w("calc-T48-CH-07-defamount-omitted-pct.json", charges=[[("chargeId", 3)]])
w("calc-T48-CH-08-defamount-disagree-pct.json", charges=[[("chargeId", 3), ("amount", "2.5")]])
# zero-charge control on the same shape, so "the charge vanished" can be told from
# "the charge landed" by byte-comparison rather than by inspection
w("calc-T48-CH-00-zerocharge-control.json")

# ---- gap 2: chargeCalculationType 5 -----------------------------------------------------
# PERCENT_OF_DISBURSEMENT_AMOUNT(5) [ChargeCalculationType.java:30], the only loan-valid
# calculation type with no capture in the corpus.  Charge ids are filled in by
# t48-capture.sh AFTER it creates the definitions, so this file is a TEMPLATE and carries
# the placeholder 0 until then; the capture script refuses to post a placeholder.
w("calc-T48-CH-10-calc5-disbursement-TEMPLATE.json",
  charges=[[("chargeId", 0), ("amount", "1.2345")]])
w("calc-T48-CH-11-calc5-specifieddue-TEMPLATE.json",
  charges=[[("chargeId", 0), ("amount", "1.2345"), ("dueDate", "01 April 2026")]])
w("calc-T48-CH-12-calc5-instalment-TEMPLATE.json",
  charges=[[("chargeId", 0), ("amount", "1.2345")]])
w("calc-T48-CH-13-calc5-omitted-TEMPLATE.json", charges=[[("chargeId", 0)]])
# the direct comparator: PERCENT_OF_AMOUNT(2) at the same rate at disbursement is charge 3,
# already captured by T40 as FC-03.  Re-issued here at this pass's shape so the two
# calculation types are compared on identical inputs.
w("calc-T48-CH-14-calc2-disbursement-comparator.json",
  charges=[[("chargeId", 3), ("amount", "1.2345")]])

# ---- gap 4: RepaymentEvery > 3 ----------------------------------------------------------
w("calc-T48-CH-20-repayevery4.json", repaymentEvery=4, loanTermFrequency=24, numberOfRepayments=6)
w("calc-T48-CH-21-repayevery6.json", repaymentEvery=6, loanTermFrequency=24, numberOfRepayments=4)
w("calc-T48-CH-22-repayevery12.json", repaymentEvery=12, loanTermFrequency=24, numberOfRepayments=2)
w("calc-T48-CH-23-repayevery4-instalmentfee.json", repaymentEvery=4, loanTermFrequency=24,
  numberOfRepayments=6, charges=[[("chargeId", 2), ("amount", "2500")]])
w("calc-T48-CH-24-repayevery3-comparator.json", repaymentEvery=3, loanTermFrequency=24,
  numberOfRepayments=8)
