#!/usr/bin/env python3
"""Cross-check the two pass-3c parity candidates against task T37's INDEPENDENT capture of the
same two shapes (.softhouse/capture/dec1-binding/out/t37-binding.json, cases T37-3-A / T37-3-B,
a different harness through the same Path A seam).

This is a REPRODUCTION check across harnesses, not a calibration: T37's captures were never
promoted and its harness does not emit the pass-3b columns. Any column both harnesses emit must
agree exactly. A disagreement would be a finding to report loudly, never to reconcile."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
A = {c["id"]: c for c in json.load(open(os.path.join(
    ROOT, ".softhouse/capture/out/capture-prod3c-raw.json")))["captures"]}
B = {c["id"]: c for c in json.load(open(os.path.join(
    ROOT, ".softhouse/capture/dec1-binding/out/t37-binding.json")))["captures"]}

PAIRS = [("P-EMI-6-1M014632", "T37-3-A"), ("P-EMI-36-127704", "T37-3-B")]
# column name in pass 3c -> column name in T37's harness
ROWMAP = {"type": "type", "periodNumber": "periodNumber", "periodFromDate": "fromDate",
          "dueDate": "dueDate", "principal": "principal", "interest": "interest",
          "balance": "balance", "total": "total", "feeAmount": "fee", "penaltyAmount": "penalty",
          "totalOutstandingBalance": "totalOutstandingBalance"}
TOTMAP = {"loanTermInDays": "loanTermInDays", "totalDisbursedAmount": "totalDisbursedAmount",
          "totalInterestAmount": "totalInterestAmount", "totalRepaymentAmount": "totalRepaymentAmount"}

n = bad = 0
for mine, theirs in PAIRS:
    oa, ob = A[mine]["observed"], B[theirs]["observed"]
    print("%s vs %s" % (mine, theirs))
    for ka, kb in TOTMAP.items():
        n += 1
        if str(oa[ka]) != str(ob[kb]):
            bad += 1
            print("  MISMATCH total %s: %r vs %r" % (ka, oa[ka], ob[kb]))
    if len(oa["periods"]) != len(ob["periods"]):
        bad += 1
        print("  MISMATCH row count %d vs %d" % (len(oa["periods"]), len(ob["periods"])))
        continue
    for i, (pa, pb) in enumerate(zip(oa["periods"], ob["periods"])):
        for ka, kb in ROWMAP.items():
            if ka not in pa or kb not in pb:
                continue
            n += 1
            if str(pa[ka]) != str(pb[kb]):
                bad += 1
                print("  MISMATCH row %d %s: %r vs %r" % (i, ka, pa[ka], pb[kb]))
    print("  columns both harnesses emit: compared through row %d" % i)

print("T37 cross-check: %d cells compared, %d mismatches" % (n, bad))
sys.exit(1 if bad else 0)
