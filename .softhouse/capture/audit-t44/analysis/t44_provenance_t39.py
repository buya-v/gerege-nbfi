#!/usr/bin/env python3
"""
T44 audit - provenance spot-check: every number T39's handoff publishes in its
observed table and its two worked examples must appear in the OBSERVED payload.
Transcribed here from .softhouse/handoff/T39-periodratio-observation.md (the claim),
checked against .softhouse/capture/periodratio/out/t39-periodratio.json (the observation).
Exact Decimal / exact string comparison. NO FLOAT.
"""
import json, sys
from decimal import Decimal

PAY = sys.argv[1]
doc = json.load(open(PAY), parse_float=Decimal)
cap = {c['id']: c for c in doc['captures']}

# --- handoff section 1, "The observed table": (id, observed total interest) -------------
TOTALS = [
    ("T39-CTL-Q0a", "76723.70"), ("T39-CTL-1", "20815.82"), ("T39-CTL-2", "76723.70"),
    ("T39-P0-A", "76984.00"), ("T39-P0-B", "76772.34"), ("T39-P0-C", "470451.99"),
    ("T39-P0-D", "18659151.45"), ("T39-P0-E", "76809.48"), ("T39-P0-F", "6.41"),
    ("T39-P0-G", "124359.75"), ("T39-P0-H", "149987.71"), ("T39-ME-A", "194510.78"),
    ("T39-ME-B", "76723.70"), ("T39-ME-C", "76723.70"), ("T39-ME-D", "76723.70"),
    ("T39-CAL", "2.05"),
]

# --- handoff section 2, worked example T39-P0-A: the full 6x9 observed table ------------
P0A = [
    (1, "2024-01-28", "2024-02-29", "192580.67", "20250.00", "0.00", "0.00", "1007419.33", "212830.67", "1064153.33"),
    (2, "2024-02-29", "2024-03-31", "193527.22", "19303.45", "0.00", "0.00", "813892.11", "212830.67", "851322.66"),
    (3, "2024-03-31", "2024-04-30", "198180.61", "14650.06", "0.00", "0.00", "615711.50", "212830.67", "638491.99"),
    (4, "2024-04-30", "2024-05-31", "201390.35", "11440.32", "0.00", "0.00", "414321.15", "212830.67", "425661.32"),
    (5, "2024-05-31", "2024-06-30", "205372.89", "7457.78", "0.00", "0.00", "208948.26", "212830.67", "212830.65"),
    (6, "2024-06-30", "2024-07-31", "208948.26", "3882.39", "0.00", "0.00", "0.00", "212830.65", "0.00"),
]
# --- handoff section 2, worked example T39-ME-B ----------------------------------------
MEB = [
    (1, "2024-01-31", "2024-02-29", "191187.28", "21600.00", "1008812.72", "212787.28"),
    (2, "2024-02-29", "2024-03-31", "194628.65", "18158.63", "814184.07", "212787.28"),
    (3, "2024-03-31", "2024-04-30", "198131.97", "14655.31", "616052.10", "212787.28"),
    (4, "2024-04-30", "2024-05-31", "201698.34", "11088.94", "414353.76", "212787.28"),
    (5, "2024-05-31", "2024-06-30", "205328.91", "7458.37", "209024.85", "212787.28"),
    (6, "2024-06-30", "2024-07-31", "209024.85", "3762.45", "0.00", "212787.30"),
]

bad = ok = 0


def chk(label, claimed, observed):
    global bad, ok
    if str(claimed) == str(observed):
        ok += 1
    else:
        bad += 1
        print(f"  MISMATCH {label}: handoff says {claimed!r}, payload has {observed!r}")


print("T44 provenance spot-check of the T39 handoff against the observed payload")
print()
for cid, tot in TOTALS:
    chk(f"{cid}.totalInterestAmount", tot, cap[cid]['observed']['totalInterestAmount'])

reps = [p for p in cap['T39-P0-A']['observed']['periods'] if p['type'] == 'REPAYMENT']
for row in P0A:
    k, f, d, pr, i, fee, pen, bal, tot, tob = row
    p = reps[k - 1]
    for name, claimed, key in (("fromDate", f, 'fromDate'), ("dueDate", d, 'dueDate'),
                               ("principal", pr, 'principal'), ("interest", i, 'interest'),
                               ("fee", fee, 'fee'), ("penalty", pen, 'penalty'),
                               ("balance", bal, 'balance'), ("total", tot, 'total'),
                               ("totalOutstandingBalance", tob, 'totalOutstandingBalance')):
        chk(f"T39-P0-A p{k}.{name}", claimed, p[key])

reps = [p for p in cap['T39-ME-B']['observed']['periods'] if p['type'] == 'REPAYMENT']
for row in MEB:
    k, f, d, pr, i, bal, tot = row
    p = reps[k - 1]
    for name, claimed, key in (("fromDate", f, 'fromDate'), ("dueDate", d, 'dueDate'),
                               ("principal", pr, 'principal'), ("interest", i, 'interest'),
                               ("balance", bal, 'balance'), ("total", tot, 'total')):
        chk(f"T39-ME-B p{k}.{name}", claimed, p[key])

# handoff N-7: loanTermInDays 185 on T39-P0-A (against 182 on the on-lattice controls)
chk("T39-P0-A.loanTermInDays", 185, cap['T39-P0-A']['observed']['loanTermInDays'])
chk("T39-CTL-Q0a.loanTermInDays", 182, cap['T39-CTL-Q0a']['observed']['loanTermInDays'])
# handoff section 1: total disbursed / total repayment on T39-P0-A
chk("T39-P0-A.totalDisbursedAmount", "1200000.00", cap['T39-P0-A']['observed']['totalDisbursedAmount'])
chk("T39-P0-A.totalRepaymentAmount", "1276984.00", cap['T39-P0-A']['observed']['totalRepaymentAmount'])

print()
print(f"  checked {ok + bad} published values: {ok} traced to the observation, {bad} MISMATCHED")
sys.exit(1 if bad else 0)
