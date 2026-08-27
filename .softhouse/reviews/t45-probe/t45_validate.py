"""
T41 (A) -- can DEC-1 REVISION 8, transcribed from its TEXT ALONE, reproduce
every committed observation and capture?

Five checks.  THE COMPARISON SHAPE IS STATED FOR EACH ONE, because a check's
shape is part of its strength (P2-T34-1: the old "13 of 13" compared three
scalars and could not see the defect that was there).

  A1  the thirteen committed observation TRIPLES (level, final, total interest).
      WEAK -- run only so revision 8's result is comparable with revisions 4-7.
      Cells per shape: 3.
  A2  FULL-ROW against the eleven (19, HALF_UP) Path-A pass-3 captures.
      Cells per repayment row: fromDate, dueDate, principal, interest, balance,
      total -- whichever of them the harness publishes -- plus loanTermInDays
      and totalInterest per capture.
  A3  FULL-ROW against the ten (19, HALF_UP) T37 binding captures.  Same cells.
  A4  NEW IN T41.  FULL-CELL against the fifteen parity-setting T39 captures.
      Cells per repayment row: fromDate, dueDate, principal, interest, fee,
      penalty, balance, total, totalOutstandingBalance -- plus loanTermInDays,
      totalDisbursedAmount, totalInterestAmount, totalRepaymentAmount and the
      disbursement row's published columns.
  A5  NEW IN T41.  The SCHEDULE CORE of the twenty-one T40 charge captures.
      Cells per repayment row: fromDate, dueDate, principalDue,
      principalOriginalDue, interestDue, principalLoanBalanceOutstanding,
      totalInstallmentAmountForPeriod -- plus loanTermInDays,
      totalPrincipalExpected and totalInterestCharged.  This is the check that
      makes 4.5.1's premise executable: the contract carries no charge, so if a
      charge moved any cell the contract DOES carry, revision 8 would fail here.

NOTHING HERE IS A NEW OBSERVATION.  Every expectation is transcribed from a
capture file already committed on main; NO ORACLE WAS CONTACTED BY THIS TASK.
Captures whose THREADED MathContext is not (19, HALF_UP) are SKIPPED and named
(4.1.2).  All money is parsed with parse_float=Decimal -- no binary float is
constructed anywhere.
"""
import json
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t45_model_inherited import (Request, generate, totals, m2s, MINOR,
                       assert_threaded_context)

PATHA = ".softhouse/capture/out/capture-prod-raw.json"
BINDING = ".softhouse/capture/dec1-binding/out/t37-binding.json"
PERIODRATIO = ".softhouse/capture/periodratio/out/t39-periodratio.json"
CHARGES_DIR = ".softhouse/capture/charges/out/fc"

# --- A1: the thirteen committed observation triples, transcribed with their
#     provenance.  Schedule start 2024-01-01 throughout.
CASES = [
    (100,      6,  "7.0",  None, ("17.01", "17.00", "2.05"), "capture-prod-raw.json P-00"),
    (1014632,  6,  "7.0",  None, ("172574.64", "172574.62", "20815.82"), "t23-probe2 P=1014632"),
    (127704,  36, "16.8",  None, ("4540.30", "4540.06", "35746.56"), "t23-probe2 P=127704"),
    (135623,   6,  "7.0",  None, ("23067.56", "23067.59", "2782.39"), "t23-probe2 P=135623"),
    (2345024,  6,  "7.0",  None, ("398855.60", "398855.63", "48109.63"), "t23-probe2 P=2345024"),
    (167299,   6, "21.6",  None, ("29665.91", "29665.94", "10696.49"), "t23-probe2 P=167299"),
    (64352,   12, "21.6",  None, ("6010.61", "6010.55", "7775.26"), "t23-probe2 P=64352"),
    (1000,    18, "18.5",  None, ("64.04", "64.14", "152.82"), "t23-probe2 P=1000"),
    (246489,  18, "18.5",  None, ("15786.24", "15786.14", "37663.22"), "t23-probe2 P=246489"),
    (16838,   36, "16.8",  None, ("598.65", "598.46", "4713.21"), "t23-probe2 P=16838"),
    (40595,   36, "16.8",  None, ("1443.28", "1443.47", "11363.27"), "t23-probe2 P=40595"),
    (1200000,  6, "21.6",  None, ("212787.28", "212787.30", "76723.70"), "t23-probe Q0a"),
    (1200000,  6, "21.6", date(2024, 2, 1), ("253114.12", "253114.10", "65570.58"),
     "t23-probe Q0b -- disbursement ON repayment 1's due date"),
]


def d(s):
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def jload(path):
    """parse_float=Decimal -- the non-negotiable. No binary float is built."""
    with open(path) as f:
        return json.load(f, parse_float=Decimal)


def a1():
    print("=" * 78)
    print("A1  the thirteen committed observation TRIPLES.")
    print("    CELLS COMPARED: level installment, final installment, total")
    print("    interest -- 3 per shape, 39 in all.  This is the WEAK standard.")
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
            print(f"{'':>44}expected {expect[0]:>13} {expect[1]:>14} {expect[2]:>14}"
                  f"   [{prov}]")
    print(f"\nA1: reproduced {len(CASES) - bad} of {len(CASES)}; 39 cells compared\n")
    return bad


# ---------------------------------------------------------------------------
# A2/A3/A4 -- captures in the {captures:[{id, inputs, observed}]} shape
# ---------------------------------------------------------------------------

REP_KEYS_FULL = ["fromDate", "dueDate", "principal", "interest", "fee",
                 "penalty", "balance", "total", "totalOutstandingBalance"]


def model_cells(rows, req, keys):
    out = {}
    for i, r in enumerate(rows, start=1):
        v = {
            "fromDate": str(r.frm),
            "dueDate": str(r.due),
            "principal": m2s(r.principal_minor),
            "interest": m2s(r.interest_minor),
            "fee": "0.00",          # 4.5: the contract carries no fee; the
            "penalty": "0.00",      # graded domain has none, so both are zero
            "balance": m2s(r.outstanding_minor),
            "total": m2s(r.principal_minor + r.interest_minor),
        }
        # totalOutstandingBalance is a DERIVED aggregate the contract does not
        # carry (4.5): the sum of every later row's total, plus this row's.
        for k in keys:
            if k in v:
                out[f"R{i}.{k}"] = v[k]
    if "totalOutstandingBalance" in keys:
        # 4.5: a derived aggregate the contract deliberately does NOT carry --
        # the sum of every row AFTER this one ("what is still owed once this
        # installment is paid").  Reproducing it from the rows alone is a direct
        # test of 4.5's derivability argument on a column no earlier probe of
        # this document ever compared.
        n = len(rows)
        for i in range(1, n + 1):
            tail = sum(rows[j].principal_minor + rows[j].interest_minor
                       for j in range(i, n))
            out[f"R{i}.totalOutstandingBalance"] = m2s(tail)
    return out


def capture_cells(cap, keys):
    out = {}
    k = 0
    for p in cap["observed"]["periods"]:
        if p.get("type") != "REPAYMENT":
            continue
        k += 1
        for key in keys:
            if key not in p or p[key] is None:
                continue
            if key in ("fromDate", "dueDate"):
                out[f"R{k}.{key}"] = p[key]
            else:
                out[f"R{k}.{key}"] = f"{Decimal(str(p[key])):.2f}"
    return out


def row_check(path, label, keys, extra_totals=False):
    print("=" * 78)
    print(f"{label}  FULL-CELL against every committed capture in")
    print(f"    {path}")
    print(f"    CELLS COMPARED per repayment row: {', '.join(keys)}")
    print(f"    plus loanTermInDays and totalInterestAmount"
          + (", totalDisbursedAmount, totalRepaymentAmount" if extra_totals else ""))
    print("=" * 78)
    data = jload(path)
    bad_caps = checked = total_cells = 0
    for cap in data["captures"]:
        i = cap["inputs"]
        skip = assert_threaded_context(i)
        if skip:
            print(f"{cap['id']:<16} SKIPPED ({skip})")
            continue
        if i.get("daysInMonth") != "DAYS_30" or i.get("daysInYear") != "DAYS_360":
            print(f"{cap['id']:<16} SKIPPED (day count outside the graded domain)")
            continue
        req = Request(start=d(i["scheduleGenerationStartDate"]),
                      disb=d(i["disbursementDate"]),
                      principal_minor=int(Decimal(str(i["disbursementAmount"])) * MINOR),
                      n=i["numberOfRepayments"],
                      rate_pct=Decimal(str(i["annualNominalInterestRate"])),
                      every=i.get("repaymentEvery", 1))
        rows = generate(req)
        exp = capture_cells(cap, keys)
        got = model_cells(rows, req, keys)
        diffs = [(k, got.get(k), v) for k, v in exp.items() if got.get(k) != v]
        ncells = len(exp)

        ti = totals(rows)[1]
        exp_ti = int(Decimal(str(cap["observed"]["totalInterestAmount"])) * MINOR)
        ncells += 1
        if ti != exp_ti:
            diffs.append(("totalInterestAmount", m2s(ti), m2s(exp_ti)))
        term = (rows[-1].due - rows[0].frm).days
        ncells += 1
        if term != cap["observed"]["loanTermInDays"]:
            diffs.append(("loanTermInDays", term, cap["observed"]["loanTermInDays"]))
        if extra_totals:
            tp = totals(rows)[0]
            for key, val in (("totalDisbursedAmount", req.principal_minor),
                             ("totalRepaymentAmount", tp + ti)):
                if key in cap["observed"]:
                    ncells += 1
                    e = int(Decimal(str(cap["observed"][key])) * MINOR)
                    if val != e:
                        diffs.append((key, m2s(val), m2s(e)))
            # the disbursement row's published columns
            for p in cap["observed"]["periods"]:
                if p.get("type") == "DISBURSEMENT":
                    for key in ("dueDate", "principal"):
                        if key in p:
                            ncells += 1
                            g = (str(req.disb) if key == "dueDate"
                                 else m2s(req.principal_minor))
                            e = (p[key] if key == "dueDate"
                                 else f"{Decimal(str(p[key])):.2f}")
                            if g != e:
                                diffs.append((f"DISB.{key}", g, e))

        checked += 1
        total_cells += ncells
        if diffs:
            bad_caps += 1
        print(f"{cap['id']:<16} rows={len(rows):<3} cells={ncells:<4} "
              f"{'OK' if not diffs else 'MISMATCH'}")
        for k, g, e in diffs:
            print(f"    {k}: model {g!r}  capture {e!r}")
    print(f"\n{label}: {checked - bad_caps} of {checked} captures reproduce; "
          f"{total_cells} cells compared\n")
    return bad_caps, total_cells


# ---------------------------------------------------------------------------
# A5 -- the schedule core of T40's charge captures
# ---------------------------------------------------------------------------

def a5():
    import os
    print("=" * 78)
    print("A5  the SCHEDULE CORE of the twenty-one T40 charge captures in")
    print(f"    {CHARGES_DIR}")
    print("    CELLS COMPARED per repayment row: fromDate, dueDate,")
    print("    principalOriginalDue, principalDue, interestDue,")
    print("    principalLoanBalanceOutstanding, totalInstallmentAmountForPeriod;")
    print("    plus loanTermInDays, totalPrincipalExpected, totalInterestCharged.")
    print("    Request = the committed B-01 baseline (schedule start = ")
    print("    disbursement 2026-01-01, MNT 1,200,000, 12 x 21.6%), which every")
    print("    FC-nn shares -- only a `charges` array was injected.")
    print("    THE CONTRACT CARRIES NO CHARGE, so the model computes none; if a")
    print("    charge moved a cell the contract DOES carry, revision 8 fails here.")
    print("=" * 78)
    start = disb = date(2026, 1, 1)
    req = Request(start=start, disb=disb, principal_minor=1200000 * MINOR,
                  n=12, rate_pct=Decimal("21.6"))
    rows = generate(req)
    bad_caps = checked = total_cells = 0
    for fn in sorted(os.listdir(CHARGES_DIR)):
        if not fn.endswith("-raw.json"):
            continue
        cap = jload(os.path.join(CHARGES_DIR, fn))
        cid = fn[:-len("-raw.json")]
        diffs = []
        ncells = 0
        k = 0
        for p in cap["periods"]:
            if "period" not in p:
                continue                     # the disbursement pseudo-period
            k += 1
            r = rows[k - 1]
            pairs = [
                ("fromDate", str(r.frm), "%04d-%02d-%02d" % tuple(p["fromDate"])),
                ("dueDate", str(r.due), "%04d-%02d-%02d" % tuple(p["dueDate"])),
                ("principalOriginalDue", m2s(r.principal_minor),
                 f'{Decimal(str(p["principalOriginalDue"])):.2f}'),
                ("principalDue", m2s(r.principal_minor),
                 f'{Decimal(str(p["principalDue"])):.2f}'),
                ("interestDue", m2s(r.interest_minor),
                 f'{Decimal(str(p["interestDue"])):.2f}'),
                ("principalLoanBalanceOutstanding", m2s(r.outstanding_minor),
                 f'{Decimal(str(p["principalLoanBalanceOutstanding"])):.2f}'),
                ("totalInstallmentAmountForPeriod",
                 m2s(r.principal_minor + r.interest_minor),
                 f'{Decimal(str(p["totalInstallmentAmountForPeriod"])):.2f}'),
            ]
            for name, g, e in pairs:
                ncells += 1
                if g != e:
                    diffs.append((f"R{k}.{name}", g, e))
        tp, ti, _ = totals(rows)
        for name, g, e in (
                ("loanTermInDays", (rows[-1].due - rows[0].frm).days,
                 cap["loanTermInDays"]),
                ("totalPrincipalExpected", m2s(tp),
                 f'{Decimal(str(cap["totalPrincipalExpected"])):.2f}'),
                ("totalInterestCharged", m2s(ti),
                 f'{Decimal(str(cap["totalInterestCharged"])):.2f}')):
            ncells += 1
            if str(g) != str(e):
                diffs.append((name, g, e))
        checked += 1
        total_cells += ncells
        if diffs:
            bad_caps += 1
        print(f"{cid:<48} cells={ncells:<4} {'OK' if not diffs else 'MISMATCH'}")
        for k2, g, e in diffs:
            print(f"    {k2}: model {g!r}  capture {e!r}")
    print(f"\nA5: {checked - bad_caps} of {checked} captures reproduce; "
          f"{total_cells} cells compared\n")
    return bad_caps, total_cells


def main():
    bad = a1()
    cells = 39
    for path, label, keys, extra in (
            (PATHA, "A2", ["fromDate", "dueDate", "principal", "interest",
                           "balance", "total"], False),
            (BINDING, "A3", ["fromDate", "dueDate", "principal", "interest",
                             "balance", "total"], False),
            (PERIODRATIO, "A4", REP_KEYS_FULL, True)):
        b, c = row_check(path, label, keys, extra)
        bad += b
        cells += c
    b, c = a5()
    bad += b
    cells += c
    print("=" * 78)
    print(f"OVERALL: {'PASS' if bad == 0 else 'FAIL (%d failing checks)' % bad}"
          f"   -- {cells} cells compared in all")
    print("=" * 78)
    return bad


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
