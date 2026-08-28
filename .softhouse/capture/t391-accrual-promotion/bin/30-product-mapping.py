#!/usr/bin/env python3
"""T391 -- print a loan product's accounting mappings AS THE CONTRACT BOUNDARY
RENDERS THEM.

The vector's `request.product_mappings` is transcribed from THIS, not from SQL.
Both were measured (out/T391-S01-slot-resolution.txt is the SQL side) and they
agree; the REST side is the one the vector cites, because the seam the vector
declares is `ledger_rest_posting` and a vector must be transcribable from the
boundary it names.

parse_float=str / parse_int=str for the usual reason: no number in this program
passes through a float, not even on its way to a terminal.
"""
import json
import sys

path = sys.argv[1]
with open(path, "rb") as fh:
    d = json.load(fh, parse_float=str, parse_int=str)

print("id =", d["id"], "| name =", d["name"])
print("accountingRule =", json.dumps(d.get("accountingRule"), ensure_ascii=False, sort_keys=True))
cur = d.get("currency") or {}
print("currency.code =", cur.get("code"), "| decimalPlaces =", cur.get("decimalPlaces"),
      "| inMultiplesOf =", cur.get("inMultiplesOf"))
am = d.get("accountingMappings") or {}
for k in sorted(am):
    print("  accountingMappings.%s = %s" % (k, json.dumps(am[k], ensure_ascii=False, sort_keys=True)))
for extra in ("paymentChannelToFundSourceMappings", "feeToIncomeAccountMappings",
              "penaltyToIncomeAccountMappings"):
    if d.get(extra):
        print("  %s = %s" % (extra, json.dumps(d[extra], ensure_ascii=False, sort_keys=True)))
    else:
        print("  %s = (absent or empty)" % extra)
