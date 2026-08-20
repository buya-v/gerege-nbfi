#!/usr/bin/env python3
"""T64 — check the oracle's pass-3g capture against the prediction registered BEFORE it ran.

    python3 .softhouse/capture/t64-zeroprincipal/check-prediction.py

Reads `predicted-schedules.json` (committed one commit BEFORE the capture, together with
PREDICTION.md) and `.softhouse/capture/out/capture-prod3g-raw.json`, and compares EVERY cell of
EVERY row: kind, installment number, from date, due date, principal, interest, outstanding balance.

It reports mismatches; it does NOT reconcile them. A refuted prediction is a finding.

"The oracle" is the Fineract reference implementation. Oracle Database is a prohibited product in
this program and appears nowhere in this stack.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRED = os.path.join(HERE, "predicted-schedules.json")
CAP = os.path.join(HERE, "..", "out", "capture-prod3g-raw.json")


def minor(text, digits=2):
    """Exact textual major -> minor scaling. No float anywhere."""
    t = text.strip()
    neg = t.startswith("-")
    if neg:
        t = t[1:]
    ip, _, fp = t.partition(".")
    ip = ip or "0"
    if len(fp) > digits:
        if fp[digits:].strip("0"):
            raise SystemExit("significant digit beyond the currency scale: %r" % text)
        fp = fp[:digits]
    fp = fp + "0" * (digits - len(fp))
    v = int((ip + fp) or "0")
    return -v if neg else v


def main():
    pred = json.load(open(PRED))
    caps = {c["id"]: c for c in json.load(open(CAP))["captures"]}

    total, bad = 0, []
    for cid in sorted(pred):
        if cid not in caps:
            bad.append("%s: ABSENT from the capture" % cid)
            continue
        cap = caps[cid]
        if cap.get("observed") is None:
            bad.append("%s: observed is null (error: %s)" % (cid, cap.get("error")))
            continue
        prows = pred[cid]["rows"]
        orows = cap["observed"]["periods"]
        if len(prows) != len(orows):
            bad.append("%s: predicted %d rows, oracle returned %d"
                       % (cid, len(prows), len(orows)))
            continue
        for i, (p, o) in enumerate(zip(prows, orows)):
            def cmp(name, predicted, observed):
                nonlocal total
                total += 1
                if predicted != observed:
                    bad.append("%s row %d %s: predicted %r, oracle %r"
                               % (cid, i, name, predicted, observed))

            cmp("kind", p["kind"], o["type"])
            if o["type"] == "REPAYMENT":
                cmp("installment_number", p["no"], o["periodNumber"])
            cmp("from_date", p["from"], o["periodFromDate"])
            cmp("due_date", p["due"], o["dueDate"])
            cmp("principal_minor", p["principal_minor"], minor(o["principal"]))
            if o["type"] == "REPAYMENT":
                cmp("interest_minor", p["interest_minor"], minor(o["interest"]))
            cmp("outstanding_principal_minor", p["outstanding_minor"], minor(o["balance"]))

    print("compared %d predicted cells across %d shapes" % (total, len(pred)))
    if bad:
        print("\nPREDICTION REFUTED — %d mismatches. This is a FINDING, not a failure to fix:" % len(bad))
        for b in bad[:200]:
            print("  " + b)
        sys.exit(1)
    print("PREDICTION CONFIRMED — zero mismatches.")


if __name__ == "__main__":
    main()
