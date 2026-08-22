#!/usr/bin/env python3
"""
T241 — INDEPENDENT RE-DERIVATION of the TOTAL-INTEREST identity on T229's UNRESCUED cells.

WHY THIS FILE EXISTS.  `site3.py` (committed by T229, in this same directory) states, in its module
docstring and in its `predictedTotalInterestMinor` field:

    TOTAL INTEREST = n*E + B   for any unrescued cell

That is FALSE whenever the cell repays any principal at all.  This script re-derives the defect FROM
THE RAW CAPTURED ROWS rather than transcribing anyone's numbers (T219 warns explicitly that
transcription is how this section acquires its defects), and it prints the arithmetic in integer
minor units so a reader can check every step by hand.

WHAT THE DEFECT ACTUALLY IS -- the quantity is right, the LABEL is wrong:
    n*E + B  is the TOTAL REPAYMENT, not the total interest.
    Total interest = n*E + B - (principal repaid).
This follows from site3.py's OWN S3.1/S3.5 without any new measurement: those steps establish that
rows 1..n-1 each total E and the last row totals E + B, so the total column sums to
(n-1)*E + (E+B) = n*E + B; and on the G-8 shape (no fees, no penalties) every row's total is
interest + principal, so the interest column is that sum minus the principal column.  The script
ASSERTS both legs on every cell.

WHY IT SURVIVED T229's OWN PROBE: on a FULL family-B cell the principal repaid is 0, so the two
formulas coincide.  T229's `classify_t229.py` did compute the check -- it wrote
`P2_totalInterestEqualsNEplusB: false` into `out/classify-t229.json` for B201, B251 and B299 -- but
its `verdict` field (classify_t229.py, the block computing `row["verdict"]`) consults only the
outcome and the principal, never P2, so all three were reported "AS PREDICTED".

NO FLOATING POINT ANYWHERE (P-25).  Money is parsed from the captured decimal STRINGS straight into
`int` minor units by string surgery -- there is no `float()`, no float literal, and no
`Decimal`->`float` step on any path.  The only non-integer type used is `fractions.Fraction`, which
is exact.

WHAT IT READS (P-66/P-70 -- stated so nobody has to guess where the numbers came from):
    .softhouse/capture/t219-g8-residual/out/capture-t219-raw.json.gz   (T219's live oracle capture)
    .softhouse/capture/t229-g8-site3/out/capture-t229-raw.json.gz      (T229's own live capture)
Nothing else.  It reads no prediction file, no handoff and no gate text, so it cannot inherit a
transcribed number from any of them.

The oracle is the Fineract reference implementation at pinned commit
426a23544e8426a38ae43ae404670a0a7e85b9eb.  Oracle Database is a prohibited product in this program
and appears nowhere in this work.

USAGE:  python3 rederive_total_interest_t241.py
Exit 0 iff every assertion below holds.
"""

import gzip
import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
T219_CAPTURE = os.path.join(HERE, "..", "..", "t219-g8-residual", "out", "capture-t219-raw.json.gz")
T229_CAPTURE = os.path.join(HERE, "..", "out", "capture-t229-raw.json.gz")

# (capture file, cell id, one-line provenance).  Every cell listed is UNRESCUED -- rows 1..n-1 carry
# a single constant instalment -- which is the exact scope of site3.py's claim.  Rescued/amortizing
# cells are OUT of scope for the claim and are deliberately not listed.
CELLS = [
    (T219_CAPTURE, "T219-R600p0-N3000-B3001", "T219's PARTIAL cell, the one named in the task"),
    (T219_CAPTURE, "T219-R600p0-N3000-B4499", "T219's PARTIAL cell, the one named in the task"),
    (T229_CAPTURE, "T229-R600p0-N200-B201", "T229's OWN capture; classify wrote P2=false, verdict AS PREDICTED"),
    (T229_CAPTURE, "T229-R600p0-N200-B251", "T229's OWN capture; classify wrote P2=false, verdict AS PREDICTED"),
    (T229_CAPTURE, "T229-R600p0-N200-B299", "T229's OWN capture; classify wrote P2=false, verdict AS PREDICTED"),
    (T229_CAPTURE, "T229-R36p0-N1400-B150", "T229's OWN capture; FULL family B, principal 0 -- the formula HOLDS here"),
    (T219_CAPTURE, "T219-R600p0-N3000-B2999", "T219's FULL family-B cell -- the formula HOLDS here too"),
]


def minor(s: str) -> int:
    """Exact decimal STRING -> integer minor units at 2 dp.  No float, ever."""
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    if "." in s:
        whole, frac = s.split(".")
    else:
        whole, frac = s, ""
    if len(frac) > 2:
        raise ValueError("more than 2 decimal places, refusing to round silently: %r" % s)
    frac = (frac + "00")[:2]
    v = int(whole or "0") * 100 + int(frac)
    return -v if neg else v


def half_up_div(num: int, den: int) -> int:
    """HALF_UP(num/den) for non-negative integers, exact integer arithmetic only."""
    assert den > 0 and num >= 0
    return (2 * num + den) // (2 * den)


def rederive(cap: dict) -> dict:
    inp, obs = cap["inputs"], cap["observed"]
    periods = obs["periods"]
    disb = [p for p in periods if p["type"] == "DISBURSEMENT"]
    rep = [p for p in periods if p["type"] == "REPAYMENT"]
    assert len(disb) == 1, "G-8 shape is a single disbursement"

    # --- the quantities the formula is written in, each read from the ROWS ---
    b_minor = minor(disb[0]["principal"])                       # B
    n = len(rep)                                                # n
    head_totals = sorted({minor(p["total"]) for p in rep[:-1]})  # E, and proof it is constant
    assert len(head_totals) == 1, (
        "rows 1..n-1 are not a single instalment -- this cell is NOT unrescued, so site3.py's "
        "claim does not cover it: %r" % head_totals)
    e_minor = head_totals[0]                                    # E
    principal_minor = sum(minor(p["principal"]) for p in rep)   # principal actually repaid

    # --- the observables, summed from the columns AND cross-checked against the reported totals ---
    sum_interest = sum(minor(p["interest"]) for p in rep)
    sum_total = sum(minor(p["total"]) for p in rep)
    sum_fee = sum(minor(p["feeAmount"]) for p in rep)
    sum_pen = sum(minor(p["penaltyAmount"]) for p in rep)
    obs_interest = minor(obs["totalInterestAmount"])
    obs_principal = minor(obs["totalPrincipalAmount"])
    obs_repayment = minor(obs["totalRepaymentAmount"])
    obs_disbursed = minor(obs["totalDisbursedAmount"])

    assert sum_interest == obs_interest, "interest column does not sum to the reported total"
    assert principal_minor == obs_principal, "principal column does not sum to the reported total"
    assert sum_total == obs_repayment, "total column does not sum to the reported repayment"
    assert obs_disbursed == b_minor, "reported disbursement disagrees with the disbursement row"
    assert sum_fee == 0 and sum_pen == 0, "G-8 shape carries no fees or penalties"
    # the two-leg identity, per row, in integer minor units
    for p in rep:
        assert minor(p["total"]) == minor(p["interest"]) + minor(p["principal"]), \
            "a row's total is not interest + principal"

    # --- delta, from the inputs, exactly (DAYS_30/DAYS_360 => monthly = annual/12) ---
    assert inp["daysInMonth"] == "DAYS_30" and inp["daysInYear"] == "DAYS_360"
    assert inp["repaymentFrequencyType"] == "MONTHS" and inp["repaymentFrequency"] == 1
    r = Fraction(inp["annualNominalInterestRate"]) / 100 / 12
    i1_exact = b_minor * r
    i1q = half_up_div(i1_exact.numerator, i1_exact.denominator)
    delta = i1q - e_minor

    wrong = n * e_minor + b_minor                      # site3.py's committed formula
    right = n * e_minor + b_minor - principal_minor    # the corrected form

    return {
        "id": cap["id"], "n": n, "B": b_minor, "E": e_minor,
        "I1_exact": str(i1_exact), "I1q": i1q, "delta": delta,
        "a": half_up_div(b_minor, n),
        "row1_interest": minor(rep[0]["interest"]),
        "last_row_total": minor(rep[-1]["total"]),
        "principal": principal_minor,
        "observed_total_interest": obs_interest,
        "observed_total_repayment": obs_repayment,
        "wrong": wrong, "right": right, "overstatement": wrong - obs_interest,
    }


def main() -> int:
    loaded = {}
    ok = True
    for path, cid, note in CELLS:
        if path not in loaded:
            with gzip.open(path) as fh:
                loaded[path] = {c["id"]: c for c in json.load(fh)["captures"]}
        by_id = loaded[path]
        if cid not in by_id:
            print("MISSING CELL %s in %s" % (cid, path))
            ok = False
            continue
        d = rederive(by_id[cid])
        print("=== %s" % cid)
        print("  source                         : %s" % os.path.normpath(path))
        print("  why listed                     : %s" % note)
        print("  n                              = %(n)d" % d)
        print("  B            (minor)           = %(B)d" % d)
        print("  E            (minor)           = %(E)d   [rows 1..n-1 all equal]" % d)
        print("  I1 = B*r exact = %(I1_exact)s  -> I1q(HALF_UP) = %(I1q)d, delta = %(delta)d,"
              " a = %(a)d" % d)
        print("  row 1 interest (minor)         = %d   [= min(I1q, E) = %d]"
              % (d["row1_interest"], min(d["I1q"], d["E"])))
        print("  last row total (minor)         = %d   [E + B = %d]"
              % (d["last_row_total"], d["E"] + d["B"]))
        print("  principal repaid (minor)       = %(principal)d   [summed from the column]" % d)
        print("  OBSERVED total interest        = %(observed_total_interest)d" % d)
        print("  OBSERVED total repayment       = %(observed_total_repayment)d" % d)
        print("  site3.py: n*E + B              = %d*%d + %d = %d"
              % (d["n"], d["E"], d["B"], d["wrong"]))
        print("  corrected: n*E + B - principal = %d - %d = %d"
              % (d["wrong"], d["principal"], d["right"]))
        print("  site3.py OVERSTATES interest by= %(overstatement)d minor units" % d)
        # the corrected identity must hold on EVERY listed cell, PARTIAL or FULL
        if d["right"] != d["observed_total_interest"]:
            print("  !! corrected formula DISAGREES with the observation -- HIGH finding")
            ok = False
        # n*E + B is the TOTAL REPAYMENT
        if d["wrong"] != d["observed_total_repayment"]:
            print("  !! n*E + B is not the observed total repayment either -- HIGH finding")
            ok = False
        if d["overstatement"] != d["principal"]:
            print("  !! overstatement != principal -- the correction term is not the principal")
            ok = False
        if d["last_row_total"] != d["E"] + d["B"]:
            print("  !! last row total != E + B -- FACT A does not hold on this cell")
            ok = False
        if d["principal"] == 0:
            print("  NOTE: principal repaid is 0, so site3.py's formula COINCIDES here%s"
                  % ("" if d["wrong"] == d["observed_total_interest"] else " -- BUT IT DID NOT !!"))
            if d["wrong"] != d["observed_total_interest"]:
                ok = False
        elif d["wrong"] == d["observed_total_interest"]:
            print("  !! site3.py's formula MATCHED on a cell that repays principal -- "
                  "the T241 finding does NOT reproduce")
            ok = False
    print()
    print("RESULT: %s" % ("every listed cell reproduces: n*E + B is the TOTAL REPAYMENT, and "
                          "total interest = n*E + B - principal"
                          if ok else "SOMETHING DID NOT REPRODUCE -- read the !! lines"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
