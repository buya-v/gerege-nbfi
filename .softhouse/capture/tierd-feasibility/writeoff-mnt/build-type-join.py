#!/usr/bin/env python3
"""OH-TIERD10-CA: join every `/journalentries` leg to its loan transaction TYPE.

The join is the capture's point: a journal-entry leg carries only
`transactionId` = `L<loanTransactionId>`; the *type* of that loan transaction
(disbursement / accrual / chargeOff / writeOff / ...) lives only in the loan
read-backs under `loans/loan-<id>/*-transactions-*.json`.  This script reads
both and emits, per type, the legs and the loans that produced them.

It also decides whether any `writeOff` transaction on a loan that was already
charged off was observed — i.e. a write-off whose legs *reverse* the charge-off
(a CREDIT to the Credit Loss/Bad Debt account) rather than the ordinary
write-off (a CREDIT to Loans Receivable / Interest-Fee Receivable).  The decision
is made from the join alone, never assumed.

Writes `journalentry-type-join.json` and `journalentry-type-join.md`.
"""
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LOANS = os.path.join(HERE, "loans")
JE = os.path.join(HERE, "journalentries")
SEQ_RE = re.compile(r"-(\d+)\.json$")


def minor(amount):
    """Decimal major units -> integer minor units string (MNT has 2 digits)."""
    return str(int(round(float(amount) * 100)))


def tx_map_for(loan_id):
    """loanTransactionId -> {code, value, date, amount, reversed, ...}.

    Merged over every transaction read-back of the loan; the type of an id must
    be stable across reads (asserted), because later reads may include reverted
    pairs but never a different type for the same id."""
    out = {}
    pat = os.path.join(LOANS, "loan-%d" % loan_id,
                       "loan-%d-detail-associations-transactions-*.json" % loan_id)
    for f in sorted(glob.glob(pat), key=lambda p: int(SEQ_RE.search(p).group(1))):
        body = json.load(open(f))
        for t in body.get("transactions") or []:
            tid = t.get("id")
            typ = t.get("type") or {}
            code = typ.get("code")
            if tid is None:
                continue
            prev = out.get(tid)
            if prev and code and prev["code"] and prev["code"] != code:
                raise SystemExit("type instability loan %d tx %s: %s vs %s"
                                 % (loan_id, tid, prev["code"], code))
            out[tid] = {"code": code, "value": typ.get("value"),
                        "date": t.get("date"), "amount_minor": minor(t.get("amount"))
                        if t.get("amount") is not None else None,
                        "reversed": t.get("reversed"),
                        "manually_reversed": t.get("manuallyReversed")}
    return out


def credit_is_bad_debt(name):
    n = name or ""
    return "Credit Loss" in n or "Bad Debt" in n


def main():
    loan_ids = sorted(int(d.split("-")[1]) for d in os.listdir(LOANS)
                      if d.startswith("loan-"))
    maps = {lid: tx_map_for(lid) for lid in loan_ids}

    leg_records = []
    unmatched = []
    for lid in loan_ids:
        for f in sorted(glob.glob(os.path.join(JE, "loan-%d" % lid, "*.json"))):
            body = json.load(open(f))
            for it in body.get("pageItems") or []:
                label = it.get("transactionId")
                n = int(label[1:]) if isinstance(label, str) and label.startswith("L") else None
                tx = maps[lid].get(n)
                if tx is None:
                    unmatched.append({"loan": lid, "file": os.path.relpath(f, HERE),
                                      "transaction_id": label})
                leg_records.append({
                    "loan": lid,
                    "journalentries_file": os.path.relpath(f, HERE),
                    "transaction_id": label,
                    "transaction_id_num": n,
                    "type_code": tx["code"] if tx else None,
                    "type_value": tx["value"] if tx else None,
                    "transaction_date": tx["date"] if tx else None,
                    "entry_type": (it.get("entryType") or {}).get("value"),
                    "gl_account_code": it.get("glAccountCode"),
                    "gl_account_name": it.get("glAccountName"),
                    "amount_minor": minor(it.get("amount")),
                    "reversed": it.get("reversed"),
                })

    # type -> legs -> loans
    types = {}
    for r in leg_records:
        key = r["type_code"] or "(unmapped)"
        t = types.setdefault(key, {"type_code": r["type_code"],
                                   "type_value": r["type_value"],
                                   "loans": [], "transactions": [], "legs": []})
        if r["loan"] not in t["loans"]:
            t["loans"].append(r["loan"])
        if r["transaction_id"] not in t["transactions"]:
            t["transactions"].append(r["transaction_id"])
        t["legs"].append(r)
    for t in types.values():
        t["loans"].sort()
        t["transactions"].sort(key=lambda s: int(s[1:]) if s and s[1:].isdigit() else 0)
        t["legs"].sort(key=lambda r: (r["loan"], r["transaction_id_num"] or 0))

    # All write-off transactions that have journal-entry legs, and the ones that
    # reverse a charge-off.
    wo_grouped = {}
    for r in leg_records:
        if r["type_code"] and r["type_code"].endswith("writeOff"):
            wo_grouped.setdefault((r["loan"], r["transaction_id"]), []).append(r)
    writeoffs = []
    chargedoff_writeoffs = []
    for (lid, label), legs in sorted(wo_grouped.items(), key=lambda kv: (kv[0][0], int(kv[0][1][1:]))):
        credits = [l for l in legs if l["entry_type"] == "CREDIT"]
        charged_off = any(credit_is_bad_debt(l["gl_account_name"]) for l in credits)
        rec = {"loan": lid, "transaction_id": label,
               "transaction_id_num": int(label[1:]),
               "date": legs[0]["transaction_date"],
               "amount_minor": maps[lid][int(label[1:])]["amount_minor"],
               "charged_off_loan": charged_off,
               "legs": legs}
        writeoffs.append(rec)
        if charged_off:
            chargedoff_writeoffs.append(rec)

    obj = {
        "currency": "MNT",
        "tenant": "tierd",
        "loan_ids": loan_ids,
        "legs": len(leg_records),
        "unmatched_legs": unmatched,
        "types": types,
        "writeoff_transactions": writeoffs,
        "writeoff_on_charged_off_loan": chargedoff_writeoffs,
    }
    with open(os.path.join(HERE, "journalentry-type-join.json"), "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write("\n")
    write_md(obj)
    print("joined %d legs across %d types; %d unmatched; writeOff txs %d; "
          "writeOff on charged-off loan %d (loans %s)"
          % (len(leg_records), len(types), len(unmatched), len(writeoffs),
             len(chargedoff_writeoffs),
             [r["loan"] for r in chargedoff_writeoffs]))
    for u in unmatched:
        print("  UNMATCHED", u)


def write_md(obj):
    out = []
    w = out.append
    w("# Journal-entry leg -> loan transaction TYPE join")
    w("")
    w("Every `/journalentries` leg carries only `transactionId` = `L<loanTransactionId>`; the")
    w("transaction **type** comes only from the loan read-backs")
    w("(`loans/loan-<id>/loan-<id>-detail-associations-transactions-*.json`,")
    w("`transactions[].id -> transactions[].type.code`).  Amounts are integer minor units (MNT).")
    w("")
    w("Legs joined: %d; unmatched: %d." % (obj["legs"], len(obj["unmatched_legs"])))
    w("")
    for key in sorted(obj["types"], key=lambda k: (k == "(unmapped)", k)):
        t = obj["types"][key]
        w("## `%s`%s" % (t["type_code"], "" if not t["type_value"] else " — %s" % t["type_value"]))
        w("")
        w("loans: %s; transactions: %s; legs: %d"
          % (", ".join(str(x) for x in t["loans"]),
             ", ".join(t["transactions"]), len(t["legs"])))
        w("")
        w("| loan | tx | entry | account code | account name | amount (minor) | reversed |")
        w("| --- | --- | --- | --- | --- | --- | --- |")
        for r in t["legs"]:
            w("| %d | %s | %s | %s | %s | %s | %s |" % (
                r["loan"], r["transaction_id"], r["entry_type"], r["gl_account_code"],
                r["gl_account_name"], r["amount_minor"], r["reversed"]))
        w("")
    w("## `writeOff` transactions with journal-entry legs")
    w("")
    w("| loan | tx | date | amount (minor) | reverses a charge-off |")
    w("| --- | --- | --- | --- | --- |")
    for r in obj["writeoff_transactions"]:
        w("| %d | %s | %s | %s | %s |" % (r["loan"], r["transaction_id"],
          "%s-%s-%s" % tuple(r["date"]) if r["date"] else "",
          r["amount_minor"], "yes" if r["charged_off_loan"] else "no"))
    w("")
    w("## `writeOff` on a charged-off loan (the `:1616` branch)")
    w("")
    if not obj["writeoff_on_charged_off_loan"]:
        w("None observed: no `writeOff` transaction's legs credit a Credit Loss/Bad Debt")
        w("account, so no write-off reversed a charge-off in this replay.")
    else:
        w("Observed for %d loans; each lists the loan, the `writeOff` transaction id and the "
          "legs that reverse the earlier charge-off (CREDIT to Credit Loss/Bad Debt, DEBIT to "
          "Written off)." % len(obj["writeoff_on_charged_off_loan"]))
        w("")
        for r in obj["writeoff_on_charged_off_loan"]:
            w("### loan %d — `writeOff` transaction `%s` — %s — %s minor"
              % (r["loan"], r["transaction_id"],
                 "%s-%s-%s" % tuple(r["date"]) if r["date"] else "", r["amount_minor"]))
            w("")
            w("| entry | account code | account name | amount (minor) |")
            w("| --- | --- | --- | --- |")
            for l in r["legs"]:
                w("| %s | %s | %s | %s |" % (l["entry_type"], l["gl_account_code"],
                                            l["gl_account_name"], l["amount_minor"]))
            w("")
    with open(os.path.join(HERE, "journalentry-type-join.md"), "w") as fh:
        fh.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
