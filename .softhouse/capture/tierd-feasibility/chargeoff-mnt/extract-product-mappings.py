#!/usr/bin/env python3
"""Extract the loan-product GL account mappings the charge-off posting reads.

createJournalEntriesForChargeOff [AccrualBasedAccountingProcessorForLoan.java:890] resolves
each leg's account through the product's accountingMappings.  Those are observed twice in
the raw Feign log (driver, 2026-09-11):
  * the oracle's own echo: LoanProductsApi#retrieveOneLoanProduct for product 20 (the only
    retrieveOne in the replay) carries `accountingMappings`;
  * the createLoanProduct request bodies the oracle ACCEPTED for LP1 (product 2) and
    LP1_INTEREST_FLAT (product 3), the products of the loans the charge-off vectors cite.
Every *AccountId in the two requests equals the id in the echo, so the mapping is observed,
not synthesised.  Bodies are written verbatim (one JSON document each) with their sha256.
Usage: extract-product-mappings.py <feign-chargeoff-mnt.log>
"""
import hashlib, json, os, sys
log = sys.argv[1]
out = "product-mappings"; os.makedirs(out, exist_ok=True)
want = {"retrieveOneLoanProduct": None, "LP1": None, "LP1_INTEREST_FLAT": None}
for n, ln in enumerate(open(log, errors="replace"), 1):
    if "LoanProductsApi#retrieveOneLoanProduct] {" in ln and want["retrieveOneLoanProduct"] is None:
        want["retrieveOneLoanProduct"] = (n, ln[ln.index("] {") + 2:].strip())
    elif "LoanProductsApi#createLoanProduct" in ln and "{" in ln:
        body = ln[ln.index("{"):].strip()
        try: name = json.loads(body).get("name")
        except ValueError: continue
        if name in want and want[name] is None: want[name] = (n, body)
man = []
for key, got in want.items():
    if got is None: sys.exit(f"extract-product-mappings: {key} not found in {log}")
    n, body = got
    json.loads(body)  # must parse
    f = f"{out}/{'product-20-retrieve-one-response' if key == 'retrieveOneLoanProduct' else 'create-request-' + key}.json"
    open(f, "w").write(body + "\n")
    man.append({"file": f, "log_line": n, "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest()})
json.dump(man, open(f"{out}/manifest.json", "w"), indent=1)
for m in man: print(m["sha256"], m["file"], "log line", m["log_line"])
