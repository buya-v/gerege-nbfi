#!/usr/bin/env python3
"""T362 — structural (not token) re-derivation of leg 1/2 of T357's corpus-isolation proof.

A token sweep can only see the tokens you thought of. This walks every vector's JSON
tree, SKIPS the free-prose fields, and reports every remaining scalar that mentions
anything from the loan-product-read subject matter. If the three section-1 failures
touched a graded vector, the touch would have to appear in a NON-PROSE field.
"""
import glob
import json
import os
import pathlib
import sys
from decimal import Decimal

# Root derived from __file__, never hard-coded: this file sits four levels below
# the checkout root, under .softhouse/reviews/t362-review-t357/rig.
W = str(pathlib.Path(__file__).resolve().parents[4])
VEC = os.path.join(W, ".softhouse", "vectors")

PROSE = {"_note", "note", "evidence", "citation", "title", "why", "rationale",
         "reason", "comment", "description", "caveat", "readme", "_readme"}

TOKENS = ("loanproduct", "loanProduct", "loanproducts", "loanProducts",
          "accountingMappings", "accountingRule",
          "FundSourceMappings", "feeToIncome", "penaltyToIncome",
          "product_id", "productId", "m_product_loan",
          "chargeOffExpenseAccount", "loanPortfolioAccount", "goodwillCreditAccount",
          "fundSourceAccount", "incomeFromFeeAccount", "incomeFromPenaltyAccount",
          "tierA-a2", "a2-11", "A2-11", "check-shape", "A2-211")

hits = []
prose_hits = 0
files = sorted(glob.glob(os.path.join(VEC, "**", "*.json"), recursive=True))


def walk(o, path, f, in_prose):
    global prose_hits
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, path + "." + k, f, in_prose or (k in PROSE))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, "%s[%d]" % (path, i), f, in_prose)
    else:
        s = str(o)
        for t in TOKENS:
            if t in s:
                if in_prose:
                    prose_hits += 1
                else:
                    hits.append((os.path.relpath(f, W), path, t, s[:200]))
                break


for f in files:
    with open(f, "rb") as fh:
        walk(json.loads(fh.read().decode("utf-8"), parse_float=Decimal), "", f, False)

print("vectors scanned: %d json files" % len(files))
print("tokens in the subject-matter list: %d" % len(TOKENS))
print("hits inside FREE-PROSE fields (%s): %d  -- these grade nothing"
      % ("/".join(sorted(PROSE)), prose_hits))
print("hits OUTSIDE prose fields: %d" % len(hits))
for f, p, t, s in hits:
    print("  %s\n    path=%s\n    token=%s\n    value=%s" % (f, p, t, s))

# Positive control: the walker must be able to see a non-prose hit at all.
ctl = []


def walk_ctl(o, path, f):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in PROSE:
                continue
            walk_ctl(v, path + "." + k, f)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk_ctl(v, "%s[%d]" % (path, i), f)
    else:
        if "loanschedule" in str(o):
            ctl.append((os.path.relpath(f, W), path))


for f in files:
    with open(f, "rb") as fh:
        walk_ctl(json.loads(fh.read().decode("utf-8"), parse_float=Decimal), "", f)
print()
print("POSITIVE CONTROL — non-prose scalars containing 'loanschedule': %d "
      "(if this were 0 the walker would be blind)" % len(ctl))
for f, p in ctl[:5]:
    print("  %s  path=%s" % (f, p))
sys.exit(1 if hits else 0)
