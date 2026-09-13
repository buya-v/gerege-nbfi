#!/usr/bin/env python3
"""Extract the `/journalentries` responses from a Tier D MNT Feign log.

Copied unchanged (logic) from OH-TIERD21-DA repayment-p1-mnt/ by the driver,
2026-09-12; the default LOG below names the OH-TIERD22-DB LoanMerchantIssuedRefund log.

`bin/extract.py` is loan-keyed and deliberately skips non-`/loans` routes, so the GL
journal entries for loan transactions are not in `loans/`.
This supplementary extractor captures exactly those bodies, attributed to the
loan in each response (`entityId`; `transactionId` is `L<loanId>`).

It writes one raw JSON body per response plus a manifest.  The manifest carries
money as integer minor units (MNT, 2 ISO 4217 digits); the raw bodies keep the
decimal major units the oracle emitted, unchanged.

Usage:
    python3 extract-journalentries.py [LOG] [OUT_DIR]
"""
import hashlib
import json
import os
import re
import sys

DEFAULT_LOG = (
    "/Users/buv/fineract-tierd/fineract-e2e-tests-runner/"
    "build/capture/feign-merchant-refund-mnt.log"
)
DEFAULT_OUT = os.path.dirname(os.path.abspath(__file__))

PREFIX_RE = re.compile(rb"^\S+ \[([^\]]*)\] (\w+) (\S+) - \[([^\]]+)\] (.*)$")
ARROW_RE = re.compile(rb"^---> ([A-Z]+) (\S+) HTTP/1\.1$")
REQ_END_RE = re.compile(rb"^---> END HTTP \((\d+)-byte body\)$")
RESP_START_RE = re.compile(rb"^<--- HTTP/1\.1 (\d+)")
RESP_END_RE = re.compile(rb"^<--- END HTTP \((\d+)-byte body\)$")

WRITEOFF_TOKENS = ("Credit Loss", "Bad Debt", "Charge Off", "Recoveries", "Written Off")


def enum_value(x):
    return x.get("value") if isinstance(x, dict) else x


def minor_units(amount):
    """Decimal major units -> integer minor units string (MNT has 2 digits)."""
    return str(int(round(float(amount) * 100)))


def main():
    log = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    je_dir = os.path.join(out, "journalentries")

    states = {}
    records = []
    with open(log, "rb") as fh:
        for line_no, raw in enumerate(fh, 1):
            raw = raw.rstrip(b"\n").rstrip(b"\r")
            m = PREFIX_RE.match(raw)
            if not m:
                continue
            thread, content = m.group(1), m.group(5)
            arrow = ARROW_RE.match(content)
            if arrow:
                url = arrow.group(2).decode("utf-8", "replace")
                states[thread] = {
                    "url": url, "method": arrow.group(1).decode(),
                    "status": None, "in_body": False, "parts": [],
                    "want": "/journalentries" in url, "source_line": line_no,
                }
                continue
            cur = states.get(thread)
            if cur is None:
                continue
            sm = RESP_START_RE.match(content)
            if sm:
                cur["status"] = int(sm.group(1))
                cur["in_body"], cur["parts"] = False, []
                continue
            if REQ_END_RE.match(content):
                cur["in_body"], cur["parts"] = False, []
                continue
            if RESP_END_RE.match(content):
                if cur["want"]:
                    cur["body"] = b"\n".join(cur["parts"]).decode("utf-8", "replace")
                    records.append(cur)
                del states[thread]
                continue
            if not cur["in_body"]:
                if content == b"":
                    cur["in_body"], cur["parts"] = True, []
                continue
            if cur["want"]:
                cur["parts"].append(content)

    man = []
    seq = {}
    for rec in records:
        obj = json.loads(rec["body"])
        items = obj.get("pageItems", []) if isinstance(obj, dict) else []
        loan_ids = sorted({it.get("entityId") for it in items if it.get("entityId") is not None})
        loan_id = loan_ids[0] if len(loan_ids) == 1 else None
        currencies = {it.get("currency", {}).get("code") for it in items if it.get("currency")}
        if not items or loan_id is None or currencies != {"MNT"}:
            raise SystemExit(
                "unexpected journalentries body: loan_ids=%r currencies=%r url=%s"
                % (loan_ids, currencies, rec["url"])
            )
        body = rec["body"].encode("utf-8")
        seq[loan_id] = seq.get(loan_id, 0) + 1
        rel = "journalentries/loan-%d/loan-%d-journalentries-%d.json" % (
            loan_id, loan_id, seq[loan_id])
        path = os.path.join(out, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(body)
        legs = []
        for it in items:
            name = it.get("glAccountName")
            legs.append({
                "gl_account_name": name,
                "gl_account_code": it.get("glAccountCode"),
                "entry_type": enum_value(it.get("entryType")),
                "amount_minor": minor_units(it.get("amount")),
            })
        man.append({
            "file": rel,
            "loan_id": loan_id,
            "url": rec["url"],
            "method": rec["method"],
            "http_status": rec["status"],
            "source_line": rec["source_line"],
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "total_filtered_records": obj.get("totalFilteredRecords"),
            "page_items": len(items),
            "currency": "MNT",
            "gl_legs": legs,
            "writeoff_leg": any(t in (leg["gl_account_name"] or "") for leg in legs for t in WRITEOFF_TOKENS),
        })

    man.sort(key=lambda e: (e["loan_id"], e["source_line"]))
    with open(os.path.join(out, "journalentries-manifest.json"), "w") as fh:
        json.dump(man, fh, indent=1)
        fh.write("\n")

    summary = {
        "responses": len(man),
        "loans": len({e["loan_id"] for e in man}),
        "loan_ids": sorted({e["loan_id"] for e in man}),
        "page_items": sum(e["page_items"] for e in man),
        "responses_with_writeoff_leg": sum(1 for e in man if e["writeoff_leg"]),
        "gl_leg_counts": {},
    }
    for e in man:
        for leg in e["gl_legs"]:
            summary["gl_leg_counts"][leg["gl_account_name"]] = (
                summary["gl_leg_counts"].get(leg["gl_account_name"], 0) + 1)
    with open(os.path.join(out, "journalentries-summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")

    print("journalentries responses: %d over %d loans; %d carry a charge-off leg"
          % (summary["responses"], summary["loans"], summary["responses_with_writeoff_leg"]))


if __name__ == "__main__":
    main()
