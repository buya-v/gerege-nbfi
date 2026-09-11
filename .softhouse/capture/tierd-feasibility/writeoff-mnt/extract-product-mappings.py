#!/usr/bin/env python3
"""Extract the accepted createLoanProduct request body for each named product from a Tier D Feign log.

createJournalEntriesForChargeback [AccrualBasedAccountingProcessorForLoan.java:1215] resolves its
accounts through the product's accounting mappings (FUND_SOURCE — or a payment-channel mapping when
the transaction's paymentTypeId has one — OVERPAYMENT, LOAN_PORTFOLIO).  Account ids differ between
replays (each throwaway seeds its own GL), so the mapping is read from THIS replay's log.  Driver,
2026-09-11: for LP1 here, fundSource 4 / loanPortfolio 10 / overpayment 18, and the only channel
mapping is paymentTypeId 1 -> 17; the chargebacks use paymentTypeId 2, so the default fund source
(4) applies — and the observed legs carry exactly glAccountId 4, 10, 18.
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
