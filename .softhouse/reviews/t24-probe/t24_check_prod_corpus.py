#!/usr/bin/env python3
"""
T24 — run the WITH-LOOP re-derivation against the eleven-capture (19, HALF_UP) corpus so that
adding the loop to DEC-1's normative text is shown NOT to break any capture the contract is
already frozen against.

Reads .softhouse/capture/out/capture-prod-raw.json read-only (T25 owns that directory this fire).
"""
import datetime
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rd", os.path.join(HERE, "t24_rederive_with_loop.py"))
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)

obs = json.load(open(".softhouse/capture/out/capture-prod-raw.json"))


def d(s):
    y, m, day = s.split("-")
    return datetime.date(int(y), int(m), int(day))


ok_all = True
for c in obs["captures"]:
    i = c["inputs"]
    o = c["observed"]
    if i["repaymentFrequencyType"] != "MONTHS" or i["daysInMonth"] != "DAYS_30" \
            or i["daysInYear"] != "DAYS_360" or i["repaymentFrequency"] != 1 \
            or i["disbursementDate"] != i["scheduleGenerationStartDate"] \
            or int(i["mathContextPrecision"]) != 19:
        print(f"{c['id']:<14} SKIPPED (outside this model's scope: "
              f"freq={i['repaymentFrequencyType']} dim={i['daysInMonth']} "
              f"prec={i['mathContextPrecision']} disb={i['disbursementDate']} "
              f"start={i['scheduleGenerationStartDate']})")
        continue
    res = rd.derive(i["disbursementAmount"], int(i["numberOfRepayments"]),
                    i["annualNominalInterestRate"], d(i["scheduleGenerationStartDate"]),
                    seed=d(i["disbursementDate"]), digits=int(i["currencyDecimalPlaces"]),
                    apply_loop=True)
    rows = [p for p in o["periods"] if p["type"] == "REPAYMENT"]
    ok = str(res["term_days"]) == str(o["loanTermInDays"])
    for mine, theirs in zip(res["rows"], rows):
        if (str(mine["principal"]) != theirs["principal"] or str(mine["interest"]) != theirs["interest"]
                or str(mine["balance"]) != theirs["balance"] or str(mine["due"]) != theirs["dueDate"]
                or str(mine["emi"]) != theirs["total"]):
            ok = False
    if str(res["total_interest"]) != o["totalInterestAmount"]:
        ok = False
    ok_all &= ok
    trace = ",".join(a for a, _, _ in res["loop"])
    print(f"{c['id']:<14} {'MATCH' if ok else '*** MISMATCH ***':<18} EMI={res['emi']} "
          f"residual={res['diff']} loop=[{trace}]")

print()
print("with-loop model reproduces every in-scope (19, HALF_UP) capture to the minor unit"
      if ok_all else "*** the with-loop model breaks a capture ***")
