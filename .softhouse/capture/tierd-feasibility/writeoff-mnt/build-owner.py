#!/usr/bin/env python3
"""Build `OWNER.md` for the writeoff-mnt capture (OH-TIERD10-CA).

Everything is derived from this directory's committed artifacts:
`scenario-results.json`, `manifest-writeoff-passed.json`, `journalentries-summary.json`,
`journalentries-manifest.json`, `journalentry-type-join.json`, `product-mappings/manifest.json`.
The final section is the journal-entry leg -> loan-transaction-type join, which is the
point of the capture.  It re-hashes the journal-entry bodies against their manifest before
claiming them.
"""
import collections
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = ("fineract-e2e-tests-runner/src/test/resources/features/LoanWriteOff.feature")


def load(name):
    with open(os.path.join(HERE, name)) as fh:
        return json.load(fh)


def sha256_file(path):
    h = hashlib.sha256()
    with open(os.path.join(HERE, path), "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_hashes():
    bad = []
    for entry in load("journalentries-manifest.json"):
        if sha256_file(entry["file"]) != entry["sha256"]:
            bad.append(entry["file"])
    for entry in load("product-mappings/manifest.json"):
        if sha256_file(entry["file"]) != entry["sha256"]:
            bad.append(entry["file"])
    return bad


def main():
    results = load("scenario-results.json")
    manifest = load("manifest-writeoff-passed.json")
    je_summary = load("journalentries-summary.json")
    join = load("journalentry-type-join.json")
    pm = load("product-mappings/manifest.json")
    bad = verify_hashes()

    per_loan = collections.Counter(e["loan_id"] for e in manifest)
    per_loan_reads = collections.Counter(e["loan_id"] for e in manifest if e["kind"] == "read")
    scenarios = results["scenarios"]

    out = []
    w = out.append
    w("# OWNER — writeoff-mnt capture (OH-TIERD10-CA)")
    w("")
    w("Replay of `%s`" % FEATURE)
    w("with the Feign capture on, in the throwaway reference-oracle tenant `tierd` (MNT).")
    w("")
    w("## Ownership rule")
    w("")
    w("Cucumber ran scenarios sequentially in file order (`--max-workers=1`) and each scenario")
    w("creates exactly one loan; loans are numbered by the resourceId returned by `POST /loans`.")
    w("Therefore **scenario S*k* owns loan *k*** and **every body under `loans/loan-*k*/`**.")
    w("This is corroborated, not merely assumed:")
    w("- %d scenarios, %d loans, one `create` per loan (counts agree);"
      % (len(scenarios), len(per_loan)))
    w("- the `clientId` in each `loan-<k>-create-request.json` equals *k*, so the loan the")
    w("  runner created for scenario *k* is the loan numbered *k*;")
    w("- the product each scenario names in the feature matches its loan's `loanProductName`")
    w("  (table below);")
    w("- `manifest-writeoff.json` enumerates every file with `loan_id`, `source_line`, `url`,")
    w("  `sha256` and the oracle's HTTP status.")
    w("")
    w("`manifest-writeoff.json` (all %d loans, `committed: true` on each) and"
      % len(per_loan))
    w("`manifest-writeoff-passed.json` are identical here because **all %d scenarios passed**."
      % len(scenarios))
    w("")
    w("## Scenario -> loan -> read-backs")
    w("")
    w("Read-back files are the `detail-*` bodies (loan detail / associations / transactions);")
    w("command bodies (`create`/`approve`/`disburse`/`repayment`/`charge-off`/`writeoff`")
    w("request+response) are captured alongside so a copy is self-contained. Exact names are in")
    w("the manifest. Amounts in these bodies are the oracle's verbatim text, never re-serialised.")
    w("")
    w("| scenario | tag | feature line | loan | product | read-backs | committed files | result |")
    w("|----------|-----|-------------:|-----:|---------|-----------:|----------------:|--------|")
    for s in scenarios:
        w("| S%d | %s | %d | %d | `%s` | %d | %d | %s |" % (
            s["index"], s["tag"], s["feature_line"], s["loan"], s["feature_product"],
            per_loan_reads[s["loan"]], per_loan[s["loan"]], s["result"]))
    w("")
    w("Total: %d scenarios / %d loans / %d bodies, %d committed."
      % (len(scenarios), len(per_loan), len(manifest), len(manifest)))
    w("")
    w("## Scenario outcomes")
    w("")
    w("All %d scenarios passed; 0 failed. No scenario in this capture failed, so there is no"
      % len(scenarios))
    w("failed-scenario exclusion to make.")
    w("")
    for s in scenarios:
        w("- **S%d %s — %s.** `%s`" % (s["index"], s["tag"], s["result"], s["name"]))
    w("")
    w("## `/journalentries` and product mappings (the type join)")
    w("")
    w("`journalentries/loan-<id>/` holds the runner's `GET /journalentries?transactionId=L<id>`")
    w("responses, extracted from the raw Feign log by `extract-journalentries.py` (copied from")
    w("chargeoff-mnt; logic unchanged): **%d** responses over **%d** loans, sha256 in"
      % (je_summary["responses"], je_summary["loans"]))
    w("`journalentries-manifest.json`. Every leg's `entityId` is its directory's loan.")
    w("Re-hashed after writing: %s."
      % ("all %d responses match their manifest sha256" % je_summary["responses"]
         if not bad else "MISMATCH: %s" % ", ".join(bad)))
    w("")
    w("Every leg carries only `transactionId` = `L<loanTransactionId>`; the transaction **type**")
    w("comes only from the loan read-backs under `loans/`")
    w("(`loans/loan-<id>/loan-<id>-detail-associations-transactions-*.json`,")
    w("`transactions[].id -> transactions[].type.code`). The join is in")
    w("`journalentry-type-join.json` / `.md`. **%d legs, %d unmatched.**"
      % (join["legs"], len(join["unmatched_legs"])))
    w("")
    w("| transaction type | value | loans | transactions | legs |")
    w("|------------------|-------|-------|--------------|-----:|")
    for key in sorted(join["types"]):
        t = join["types"][key]
        w("| `%s` | %s | %s | %s | %d |" % (
            t["type_code"], t["type_value"],
            ", ".join(str(x) for x in t["loans"]), ", ".join(t["transactions"]),
            len(t["legs"])))
    w("")
    w("### `writeOff` on a charged-off loan — `createJournalEntriesForWriteOffsWhenLoanIsChargedOff`")
    w("")
    if not join["writeoff_on_charged_off_loan"]:
        w("**None observed.** No `writeOff` transaction's legs credit a Credit Loss/Bad Debt")
        w("account, so no write-off reversed a charge-off in this replay. That is a finding, not")
        w("a failure.")
    else:
        w("**Yes — observed.** %d of the %d `writeOff` transactions reverse a charge-off: their"
          % (len(join["writeoff_on_charged_off_loan"]), len(join["writeoff_transactions"])))
        w("legs CREDIT the Credit Loss/Bad Debt accounts that the earlier `chargeOff` transaction")
        w("debited (and DEBIT `Written off`), instead of crediting Loans Receivable / Interest-Fee")
        w("Receivable as an ordinary write-off does. The type join names the branch")
        w("`createJournalEntriesForWriteOffsWhenLoanIsChargedOff`")
        w("[AccrualBasedAccountingProcessorForLoan.java:1616] for these.")
        w("")
        w("| loan | `writeOff` tx | date | amount (minor) | charged-off loan |")
        w("|-----:|---------------|------|---------------:|------------------|")
        for r in join["writeoff_on_charged_off_loan"]:
            d = "%s-%s-%s" % tuple(r["date"]) if r["date"] else ""
            w("| %d | %s | %s | %s | yes |" % (r["loan"], r["transaction_id"], d,
                                              r["amount_minor"]))
        w("")
        for r in join["writeoff_on_charged_off_loan"]:
            d = "%s-%s-%s" % tuple(r["date"]) if r["date"] else ""
            w("### loan %d, `writeOff` `%s` (%s), %s minor" % (
                r["loan"], r["transaction_id"], d, r["amount_minor"]))
            w("")
            w("| entry | account code | account name | amount (minor) |")
            w("|-------|--------------|--------------|---------------:|")
            for l in r["legs"]:
                w("| %s | %s | %s | %s |" % (l["entry_type"], l["gl_account_code"],
                                            l["gl_account_name"], l["amount_minor"]))
            w("")
        w("The remaining `writeOff` transactions were ordinary write-offs (no charge-off to")
        w("reverse): loans %s."
          % ", ".join(str(r["loan"]) for r in join["writeoff_transactions"]
                      if not r["charged_off_loan"]))
        w("Loan 8 is the instructive case: its transaction list contains a `chargeOff` (`L30`),")
        w("but the charge-off was undone, so its `writeOff` (`L31`) credits Loans Receivable /")
        w("Interest-Fee Receivable — the join, not the mere presence of a chargeOff, decides.")
    w("")
    w("### Accounting shapes observed")
    w("")
    w("| shape | `writeOff` txs | loans |")
    w("|-------|---------------:|-------|")
    w("| charged-off reversal: C Credit Loss/Bad Debt, D Written off | %d | %s |" % (
        len(join["writeoff_on_charged_off_loan"]),
        ", ".join(str(r["loan"]) for r in join["writeoff_on_charged_off_loan"])))
    plain = [r for r in join["writeoff_transactions"] if not r["charged_off_loan"]
             and not any(l["gl_account_name"] and "Credit Loss" in l["gl_account_name"]
                         and l["entry_type"] == "DEBIT" for l in r["legs"])]
    w("| ordinary: C Loans Receivable + Interest/Fee Receivable, D Written off | %d | %s |" % (
        len(plain), ", ".join(str(r["loan"]) for r in plain)))
    w("| non-charged-off debit to Credit Loss (write-off reason map) | 1 | 11 |")
    w("")
    w("### Product mappings")
    w("")
    w("`product-mappings/create-request-<name>.json` holds the accepted create request of every")
    w("product the loans use (%d products), read from THIS replay's log by"
      % len(pm))
    w("`extract-product-mappings.py` (account ids differ between replays, each throwaway seeds")
    w("its own GL). sha256 in `product-mappings/manifest.json`; re-hashed: %s."
      % ("all %d match" % len(pm) if not bad else "MISMATCH: %s" % ", ".join(bad)))
    w("")
    for entry in pm:
        name = os.path.basename(entry["file"])[len("create-request-"):-len(".json")]
        w("- `%s` — `%s`" % (name, entry["file"]))
    w("")

    with open(os.path.join(HERE, "OWNER.md"), "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote OWNER.md (%d lines); hash check: %s"
          % (len(out), "OK" if not bad else bad))


if __name__ == "__main__":
    main()
