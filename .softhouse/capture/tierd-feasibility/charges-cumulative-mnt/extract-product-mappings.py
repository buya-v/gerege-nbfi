#!/usr/bin/env python3
"""Extract the accepted createLoanProduct request body for each named product from a Tier D Feign log.

createJournalEntriesForChargeAdjustment / ...ForLoanChargeAdjustment /
...ForChargeOffLoanChargeAdjustment [AccrualBasedAccountingProcessorForLoan.java:997-1214] book the
charge-adjustment legs against accounts resolved through the product's accounting mappings
(INCOME_FROM_FEES, INCOME_FROM_PENALTIES, RECEIVABLE_FEES, RECEIVABLE_PENALTIES, FUND_SOURCE,
LOAN_PORTFOLIO, ...).  Account ids differ between replays (each throwaway seeds its own GL), so the
mapping is read from THIS replay's log -- the accepted createLoanProduct bodies.  The loan
read-backs name the product; this script writes the matching create request so the GL account ids
captured by the sweep can be named.

Usage: extract-product-mappings.py <feign log> <product name> [...]
"""
import hashlib, json, os, sys
log, names = sys.argv[1], sys.argv[2:]
out = "product-mappings"; os.makedirs(out, exist_ok=True)
got = {}
for n, ln in enumerate(open(log, errors="replace"), 1):
    if "LoanProductsApi#createLoanProduct" in ln and "{" in ln:
        body = ln[ln.index("{"):].strip()
        try: name = json.loads(body).get("name")
        except ValueError: continue
        if name in names and name not in got: got[name] = (n, body)
man = []
for name in names:
    if name not in got: sys.exit(f"extract-product-mappings: {name} not found in {log}")
    n, body = got[name]
    f = f"{out}/create-request-{name}.json"
    open(f, "w").write(body + "\n")
    man.append({"file": f, "log_line": n, "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest()})
json.dump(man, open(f"{out}/manifest.json", "w"), indent=1)
for m in man: print(m["sha256"], m["file"], "log line", m["log_line"])
