#!/usr/bin/env python3
"""A FOURTH minor-unit converter over the two new vectors: Fraction arithmetic, the technique
.softhouse/handoff/T8-transcription-audit.py uses. Run after T57-transcription-audit.py (which
uses integer string splicing) and the promotion script (which uses a textual split-and-pad).
Three techniques agreeing on every money cell is the transcription audit's real content."""
import json
import os
import sys
from fractions import Fraction

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
V = os.path.join(ROOT, ".softhouse", "vectors", "loanschedule")
C = json.load(open(os.path.join(ROOT, ".softhouse", "capture", "out", "capture-prod3c-raw.json")),
              parse_float=str, parse_int=str)
cases = {c["id"]: c for c in C["captures"]}

n = bad = 0
for f in ("P-EMI-6-1M014632-emi-smoothing-loop.json", "P-EMI-36-127704-emi-smoothing-loop.json"):
    v = json.load(open(os.path.join(V, f)))
    obs = cases[v["provenance"]["capture_case_id"]]["observed"]
    for row, p in zip(v["expect"]["periods"], obs["periods"]):
        for vk, ck in (("principal_minor", "principal"),
                       ("interest_minor", "interest"),
                       ("outstanding_principal_minor", "balance"),
                       ("observed_total_due_minor", "total")):
            if ck not in p:
                continue
            fr = Fraction(p[ck]) * 100
            assert fr.denominator == 1, (f, ck, p[ck])
            n += 1
            if str(fr.numerator) != str(row[vk]):
                bad += 1
                print("MISMATCH %s %s vector=%r fraction=%r" % (f, vk, row[vk], fr.numerator))
    fr = Fraction(obs["totalInterestAmount"]) * 100
    n += 1
    if str(fr.numerator) != v["expect"]["observed_total_interest_minor"]:
        bad += 1
        print("MISMATCH %s observed_total_interest_minor" % f)
    fr = Fraction(cases[v["provenance"]["capture_case_id"]]["inputs"]["disbursementAmount"]) * 100
    n += 1
    if str(fr.numerator) != v["request"]["disbursements"][0]["amount_minor"]:
        bad += 1
        print("MISMATCH %s request.disbursements[0].amount_minor" % f)

print("Fraction cross-check: %d money cells, %d mismatches" % (n, bad))
sys.exit(1 if bad else 0)
