"""
T34 (A2): the same from-text model checked ROW BY ROW against every committed
Path-A capture at the production MathContext (19, HALF_UP), read directly out of
.softhouse/capture/out/capture-prod-raw.json.

This is a stronger check than the thirteen aggregate triples: it compares the
due dates, the per-period principal / interest split and the outstanding balance
of every row, which is where the month-end date rule and the zero-clamped
roll-forward actually show up.

NOTHING HERE IS A NEW OBSERVATION.  The expectations are transcribed from a
committed capture file; no oracle was contacted by this task.
"""
import json
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t34_model import Request, generate, m2s, MINOR

RAW = ".softhouse/capture/out/capture-prod-raw.json"


def d(s):
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def main():
    data = json.load(open(RAW))
    print(f"moneyHelperPrecision recorded in the capture file: "
          f"{data.get('moneyHelperPrecision')}")
    print()
    bad_caps = 0
    for cap in data["captures"]:
        i = cap["inputs"]
        if i["mathContextPrecision"] != 19:
            print(f"{cap['id']:<14} SKIPPED (precision {i['mathContextPrecision']}, "
                  f"not a parity setting)")
            continue
        if i["daysInMonth"] != "DAYS_30" or i["daysInYear"] != "DAYS_360":
            print(f"{cap['id']:<14} SKIPPED (day count outside the graded domain)")
            continue
        req = Request(start=d(i["scheduleGenerationStartDate"]),
                      disb=d(i["disbursementDate"]),
                      principal_minor=int(Decimal(i["disbursementAmount"]) * MINOR),
                      n=i["numberOfRepayments"],
                      rate_pct=Decimal(i["annualNominalInterestRate"]),
                      every=i["repaymentFrequency"])
        rows = generate(req)
        obs = [p for p in cap["observed"]["periods"] if p["type"] == "REPAYMENT"]
        bad = []
        for k, (o, r) in enumerate(zip(obs, rows), start=1):
            got = (str(r.due), m2s(r.principal_minor), m2s(r.interest_minor),
                   m2s(r.outstanding_minor))
            exp = (o["dueDate"], f'{Decimal(o["principal"]):.2f}',
                   f'{Decimal(o["interest"]):.2f}', f'{Decimal(o["balance"]):.2f}')
            if got != exp:
                bad.append((k, got, exp))
        ti = sum(r.interest_minor for r in rows)
        exp_ti = int(Decimal(cap["observed"]["totalInterestAmount"]) * MINOR)
        term_ok = (rows[-1].due - rows[0].frm).days == cap["observed"]["loanTermInDays"]
        status = "OK" if (not bad and ti == exp_ti and term_ok) else "MISMATCH"
        if status != "OK":
            bad_caps += 1
        print(f"{cap['id']:<14} rows={len(obs):<3} totInt {m2s(ti)} "
              f"(capture {m2s(exp_ti)})  term_ok={term_ok}  {status}")
        for k, got, exp in bad:
            print(f"    period {k}: got {got}")
            print(f"              exp {exp}")
    print()
    print(f"captures with a mismatch: {bad_caps}")
    return bad_caps


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
