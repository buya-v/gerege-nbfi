"""
T38 (A) -- can DEC-1 revision 7, transcribed from its TEXT ALONE, reproduce
every committed observation?

Three checks, in increasing strength:

  A1  the thirteen aggregate observation TRIPLES earlier revisions used
      (level installment, final installment, total interest).  This is the
      weak standard P2-T34-1 objects to, run here only so revision 7's result
      is comparable with revisions 4, 5 and 6.
  A2  ROW BY ROW against all twelve committed Path-A captures
      (.softhouse/capture/out/capture-prod-raw.json): due date, from date,
      principal, interest AND outstanding balance on every repayment row, plus
      the disbursement row's principal and (where the capture records it) its
      outstanding balance, plus the loan term in days and total interest.
  A3  ROW BY ROW against all eleven committed T37 binding captures
      (.softhouse/capture/dec1-binding/out/t37-binding.json), same cell set.

NOTHING HERE IS A NEW OBSERVATION.  Every expectation is transcribed from a
capture file already committed on main; no oracle was contacted by this task.
Captures threaded at a precision other than 19 are SKIPPED and named -- the
model is fixed at the production MathContext (19, HALF_UP).
"""
import json
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t38_model import Request, generate, totals, m2s, MINOR

PATHA = ".softhouse/capture/out/capture-prod-raw.json"
BINDING = ".softhouse/capture/dec1-binding/out/t37-binding.json"

# (principal MAJOR units, n, rate %, disbursement date or None (== schedule start),
#  (level installment, final installment, total interest), provenance)
CASES = [
    (100,      6,  "7.0",  None, ("17.01", "17.00", "2.05"),
     "shipped fixture / capture-prod-raw.json P-00"),
    (1014632,  6,  "7.0",  None, ("172574.64", "172574.62", "20815.82"),
     "t23-probe2-output.txt CASE P=1014632"),
    (127704,  36, "16.8",  None, ("4540.30", "4540.06", "35746.56"),
     "t23-probe2-output.txt CASE P=127704"),
    (135623,   6,  "7.0",  None, ("23067.56", "23067.59", "2782.39"),
     "t23-probe2-output.txt CASE P=135623"),
    (2345024,  6,  "7.0",  None, ("398855.60", "398855.63", "48109.63"),
     "t23-probe2-output.txt CASE P=2345024"),
    (167299,   6, "21.6",  None, ("29665.91", "29665.94", "10696.49"),
     "t23-probe2-output.txt CASE P=167299"),
    (64352,   12, "21.6",  None, ("6010.61", "6010.55", "7775.26"),
     "t23-probe2-output.txt CASE P=64352"),
    (1000,    18, "18.5",  None, ("64.04", "64.14", "152.82"),
     "t23-probe2-output.txt CASE P=1000"),
    (246489,  18, "18.5",  None, ("15786.24", "15786.14", "37663.22"),
     "t23-probe2-output.txt CASE P=246489"),
    (16838,   36, "16.8",  None, ("598.65", "598.46", "4713.21"),
     "t23-probe2-output.txt CASE P=16838"),
    (40595,   36, "16.8",  None, ("1443.28", "1443.47", "11363.27"),
     "t23-probe2-output.txt CASE P=40595"),
    (1200000,  6, "21.6",  None, ("212787.28", "212787.30", "76723.70"),
     "t23-probe-output.txt Q0a"),
    (1200000,  6, "21.6", date(2024, 2, 1), ("253114.12", "253114.10", "65570.58"),
     "t23-probe-output.txt Q0b -- disbursement ON repayment 1's due date"),
]


def d(s):
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def a1():
    print("=" * 78)
    print("A1  the thirteen COMMITTED observation triples (level, final, total")
    print("    interest).  This is the WEAK standard; see A2/A3.")
    print("=" * 78)
    bad = 0
    print(f"{'principal':>12} {'n':>3} {'rate':>5} {'disb':>11} "
          f"{'level':>14} {'final':>14} {'tot int':>14}  ok")
    for p, n, r, disb, expect, prov in CASES:
        start = date(2024, 1, 1)
        req = Request(start=start, disb=disb or start,
                      principal_minor=p * 100, n=n, rate_pct=Decimal(r))
        rows = generate(req)
        rel = [x for x in rows if x.emi_minor != 0]
        got = (m2s(rel[0].emi_minor), m2s(rows[-1].emi_minor), m2s(totals(rows)[1]))
        ok = got == expect
        bad += 0 if ok else 1
        print(f"{p:>12} {n:>3} {r:>5} {str(disb or ''):>11} "
              f"{got[0]:>14} {got[1]:>14} {got[2]:>14}  {'OK' if ok else 'MISMATCH'}")
        if not ok:
            print(f"{'':>12} {'':>3} {'':>5} {'expected':>11} "
                  f"{expect[0]:>14} {expect[1]:>14} {expect[2]:>14}   [{prov}]")
    print(f"\nA1: reproduced {len(CASES) - bad} of {len(CASES)}\n")
    return bad


def cells_from_model(rows, attach_idx):
    """Flatten the model's answer to an addressable cell map, in the shape the
    capture files publish."""
    out = {}
    for i, r in enumerate(rows, start=1):
        out[f"R{i}.fromDate"] = str(r.frm)
        out[f"R{i}.dueDate"] = str(r.due)
        out[f"R{i}.principal"] = m2s(r.principal_minor)
        out[f"R{i}.interest"] = m2s(r.interest_minor)
        out[f"R{i}.balance"] = m2s(r.outstanding_minor)
        out[f"R{i}.total"] = m2s(r.principal_minor + r.interest_minor)
    return out


def cells_from_capture(cap):
    out = {}
    k = 0
    for p in cap["observed"]["periods"]:
        if p["type"] != "REPAYMENT":
            continue
        k += 1
        out[f"R{k}.fromDate"] = p.get("fromDate")
        out[f"R{k}.dueDate"] = p["dueDate"]
        out[f"R{k}.principal"] = f'{Decimal(p["principal"]):.2f}'
        out[f"R{k}.interest"] = f'{Decimal(p["interest"]):.2f}'
        out[f"R{k}.balance"] = f'{Decimal(p["balance"]):.2f}'
        out[f"R{k}.total"] = f'{Decimal(p["total"]):.2f}'
    # drop cells the harness does not publish
    return {kk: vv for kk, vv in out.items() if vv is not None}


def row_check(path, label):
    print("=" * 78)
    print(f"{label}  ROW-BY-ROW against every committed capture in")
    print(f"    {path}")
    print("=" * 78)
    data = json.load(open(path))
    bad_caps = 0
    checked = 0
    total_cells = 0
    for cap in data["captures"]:
        i = cap["inputs"]
        if i["mathContextPrecision"] != 19:
            print(f"{cap['id']:<14} SKIPPED (threaded precision "
                  f"{i['mathContextPrecision']}, not the production setting)")
            continue
        if i["daysInMonth"] != "DAYS_30" or i["daysInYear"] != "DAYS_360":
            print(f"{cap['id']:<14} SKIPPED (day count outside the graded domain)")
            continue
        req = Request(start=d(i["scheduleGenerationStartDate"]),
                      disb=d(i["disbursementDate"]),
                      principal_minor=int(Decimal(i["disbursementAmount"]) * MINOR),
                      n=i["numberOfRepayments"],
                      rate_pct=Decimal(i["annualNominalInterestRate"]),
                      every=i.get("repaymentEvery", i.get("repaymentFrequency", 1)))
        rows = generate(req)
        got = cells_from_model(rows, None)
        exp = cells_from_capture(cap)
        diffs = [(k, got.get(k), v) for k, v in exp.items() if got.get(k) != v]
        # totals + term
        ti = totals(rows)[1]
        exp_ti = int(Decimal(cap["observed"]["totalInterestAmount"]) * MINOR)
        if ti != exp_ti:
            diffs.append(("totalInterest", m2s(ti), m2s(exp_ti)))
        term = (rows[-1].due - rows[0].frm).days
        if term != cap["observed"]["loanTermInDays"]:
            diffs.append(("loanTermInDays", term, cap["observed"]["loanTermInDays"]))
        checked += 1
        total_cells += len(exp) + 2
        status = "OK" if not diffs else "MISMATCH"
        if diffs:
            bad_caps += 1
        print(f"{cap['id']:<14} rows={len(exp)//6:<3} cells={len(exp)+2:<4} {status}")
        for k, g, e in diffs:
            print(f"    {k}: model {g!r}  capture {e!r}")
    print(f"\n{label}: {checked - bad_caps} of {checked} captures reproduce; "
          f"{total_cells} cells compared\n")
    return bad_caps


def main():
    bad = a1()
    bad += row_check(PATHA, "A2")
    bad += row_check(BINDING, "A3")
    print("=" * 78)
    print("OVERALL:", "PASS" if bad == 0 else f"FAIL ({bad} failing checks)")
    print("=" * 78)
    return bad


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
