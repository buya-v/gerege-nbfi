#!/usr/bin/env python3
"""
T241 — independent re-derivation of the two counterexamples that falsify T229's committed
`site3.py` TOTAL-INTEREST claim, plus a whole-corpus re-test of the corrected law.

WHY THIS FILE EXISTS AND WHAT IT IS NOT
---------------------------------------
It is NOT a fix to `site3.py`. `site3.py` records what T229 actually ran and is left byte-identical
(T114's standing ruling / T176's prohibition: committed evidence gets a labelled correction or a
successor, never a silent edit that makes it agree with a later document). This is the successor,
and `../../t229-g8-site3/CORRECTION-T241.md` is the label.

It does NOT import `site3.py` or `emi_mechanism_t223.py`. The instalment `E`, the quantized first
interest `I₁q`, `δ`, the three rescue guards and the outcome are RE-DERIVED HERE from the mechanism
citations in T229's docstring, so that agreement between this file and `site3.py` is a reproduction
and not a tautology. T219's reported figures are NOT read by this file at any point — T219 warns
that transcription is how the G-8 record acquires its defects, so nothing here is transcribed.

NO FLOATING POINT ANYWHERE (P-25). Every value on a decision path is `int` minor units,
`fractions.Fraction`, or `decimal.Decimal` under an explicit Context. There is no `float()` call and
no float literal in this file.

ORACLE. "The oracle" here is the Fineract reference implementation at pinned commit
426a23544e8426a38ae43ae404670a0a7e85b9eb. Oracle Database is a prohibited product in this program
and appears nowhere in this work. NO ORACLE WAS CONTACTED BY THIS FILE: every observation is read
out of the committed `.gz` raw captures (G-8 STANDING RULE 5 — the `.gz`, never the plain-JSON
extracts), which is the only source of observation this run had. The reference oracle was
UNREACHABLE on the host this ran on.

WHAT IT CHECKS
--------------
1. The two counterexamples, cell by cell:
     derived  E, I₁q, δ = I₁q − E, a = HALF_UP(B/n), guards 1-3, outcome, TOTAL PRINCIPAL
     observed totalInterestAmount / totalPrincipalAmount / totalRepaymentAmount, AND the same three
              re-summed from the individual schedule rows, all in integer minor units.
2. Every cell T229 and T219 asked, against the same two forms.
3. The whole 296-cell stuck-cell corpus census T229 itself committed
   (`../../t229-g8-site3/out/validate-corpus.json`), re-bucketed by FACT A and by δ.

Run:  python3 rederive_t241.py            # writes ../out/rederivation-t241.json, prints a summary
"""

import datetime
import gzip
import json
import os
import sys
from decimal import Context, Decimal, ROUND_DOWN, ROUND_HALF_UP
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.abspath(os.path.join(HERE, "..", ".."))

# The production MathContext. MoneyHelper.PRECISION = 19 is a compile-time constant; the tenant
# rounding mode is HALF_UP (RoundingMode ordinal 4). [CLAUDE.md, ratified tenant parameters]
MC = Context(prec=19, rounding=ROUND_HALF_UP)
# Wide enough that the operations Fineract performs WITHOUT a MathContext — the two-argument
# BigDecimal.add, setScale(19), and Money's setScale(decimalPlaces) — are exact here too.
WIDE = Context(prec=2000, rounding=ROUND_HALF_UP)
SCALE_19 = Decimal(1).scaleb(-19)


# ---------------------------------------------------------------------------------------------
# integer / exact helpers
# ---------------------------------------------------------------------------------------------
def half_up_div(num: int, den: int) -> int:
    """HALF_UP(num/den) for den > 0, integer arithmetic only."""
    assert den > 0
    if num < 0:
        return -((2 * (-num) + den) // (2 * den))
    return (2 * num + den) // (2 * den)


def quantize_fraction(x: Fraction) -> int:
    """HALF_UP quantization of an exact minor-unit quantity to a whole minor unit."""
    return half_up_div(x.numerator, x.denominator)


def minor(s) -> int:
    """A money string in MAJOR units -> integer MINOR units, exactly. Refuses anything that is not
    a whole number of minor units, so a silent truncation cannot happen here."""
    d = Decimal(str(s)).scaleb(2)
    assert d == d.to_integral_value(), "not a whole minor unit: %r" % (s,)
    return int(d.to_integral_value(rounding=ROUND_DOWN))


# ---------------------------------------------------------------------------------------------
# the mechanism, re-derived (sources are T229's, bound by matched text at 426a23544…;
# NOT re-opened by T241 — [UNVERIFIED by T241, inherited from T229])
# ---------------------------------------------------------------------------------------------
def month_day_counts(start: datetime.date, n: int):
    """Actual calendar days in each of n monthly periods, anchored on the start day."""
    out, y, m, prev = [], start.year, start.month, start
    for _ in range(n):
        m += 1
        if m == 13:
            m, y = 1, y + 1
        cur = datetime.date(y, m, start.day)
        out.append((cur - prev).days)
        prev = cur
    return out


def rate_factor(annual_pct: Decimal, actual_days: int, calc_days: int) -> Decimal:
    """ProgressiveEMICalculator.rateFactorByRepaymentPeriod for DAYS_30 / DAYS_360 /
    repaymentEvery 1. setScale(mc.getPrecision(), …) consumes 19 as DECIMAL PLACES."""
    ir = MC.divide(annual_pct, Decimal(100))
    frac = MC.divide(MC.multiply(Decimal(30), Decimal(1)), Decimal(360))
    v = MC.multiply(ir, frac)
    v = MC.multiply(v, Decimal(actual_days))
    v = MC.divide(v, Decimal(calc_days))
    return WIDE.quantize(v, SCALE_19)


def derive(annual_str: str, n: int, b_minor: int, dp: int = 2,
           start=datetime.date(2024, 1, 1)) -> dict:
    annual = Decimal(annual_str)
    disbursed = WIDE.quantize(Decimal(b_minor).scaleb(-dp), Decimal(1).scaleb(-dp))
    rfs = [rate_factor(annual, d, d) for d in month_day_counts(start, n)]
    rfp1 = [WIDE.add(Decimal(1), rf) for rf in rfs]          # two-arg add, no MathContext: exact

    acc = Decimal(1)
    for v in rfp1:                                            # rateFactorN
        acc = MC.multiply(acc, v)
    fn = Decimal(1)
    for v in rfp1[1:]:                                        # fnResult
        fn = MC.add(Decimal(1), MC.multiply(fn, v))

    emi_raw = MC.divide(MC.multiply(acc, disbursed), fn)
    emi_q = WIDE.quantize(emi_raw, Decimal(1).scaleb(-dp))    # Money(..) setScale(dp, HALF_UP)
    e = int(emi_q.scaleb(dp).to_integral_value(rounding=ROUND_DOWN))

    i1_exact = Fraction(b_minor) * Fraction(rfs[0])           # exact, in minor units
    i1q = quantize_fraction(i1_exact)
    delta = i1q - e
    a = half_up_div(b_minor, n)

    guard1 = (n >= 2) and (b_minor != 0) and (b_minor > n // 2)   # shouldBeAdjusted
    guard2 = a != 0                                              # non-zero adjustment
    guard3 = (delta >= 0) and (a > delta)                        # hasLessEmiDifference
    rescue = bool(guard1 and guard2 and guard3)

    if delta < 0:
        outcome, principal = "AMORTIZES_NORMALLY", b_minor
    elif rescue:
        outcome, principal = "RESCUED_BY_SITE3", None
    elif delta == 0:
        outcome, principal = "LAST_ROW_CARRIES_ALL_PRINCIPAL", b_minor
    else:
        principal = max(0, b_minor - n * delta)
        outcome = "FAMILY_B_FULL" if principal == 0 else "FAMILY_B_PARTIAL"

    return {
        "n": n, "bMinor": b_minor, "rate": annual_str,
        "emiRawStr": str(emi_raw), "eMinor": e,
        "i1ExactMinorStr": str(i1_exact), "i1QuantizedMinor": i1q,
        "deltaMinor": delta, "aMinor": a,
        "guard1": guard1, "guard2": guard2, "guard3": guard3, "rescues": rescue,
        "outcome": outcome, "totalPrincipalMinor": principal,
        # the two competing forms
        "site3py_totalInterestMinor": None if principal is None else n * e + b_minor,
        "corrected_totalInterestMinor": None if principal is None else n * e + b_minor - principal,
    }


# ---------------------------------------------------------------------------------------------
# observation, out of the committed .gz captures only (STANDING RULE 5)
# ---------------------------------------------------------------------------------------------
CAPTURES = [
    "t229-g8-site3/out/capture-t229-raw.json.gz",
    "t219-g8-residual/out/capture-t219-raw.json.gz",
    "t219-g8-residual/out/capture-t219-run3-raw.json.gz",
]


def load_observations() -> dict:
    obs = {}
    for rel in CAPTURES:
        raw = json.load(gzip.open(os.path.join(CAP, rel)))
        for c in raw.get("captures", []):
            c["_file"] = rel
            obs[c["id"]] = c
    return obs


def observe(cap: dict) -> dict:
    o = cap.get("observed")
    if not o:
        return {"present": False, "file": cap["_file"]}
    rows = [p for p in o["periods"] if p.get("type") == "REPAYMENT"]
    return {
        "present": True, "file": cap["_file"], "repaymentRows": len(rows),
        "totalInterestMinor": minor(o["totalInterestAmount"]),
        "totalPrincipalMinor": minor(o["totalPrincipalAmount"]),
        "totalRepaymentMinor": minor(o["totalRepaymentAmount"]),
        "totalDisbursedMinor": minor(o["totalDisbursedAmount"]),
        # re-summed from the rows, so the totals are checked against their own detail
        "rowSumInterestMinor": sum(minor(r["interest"]) for r in rows),
        "rowSumPrincipalMinor": sum(minor(r["principal"]) for r in rows),
        "rowSumTotalMinor": sum(minor(r["total"]) for r in rows),
        "row1TotalMinor": minor(rows[0]["total"]) if rows else None,
        "lastRowTotalMinor": minor(rows[-1]["total"]) if rows else None,
    }


# ---------------------------------------------------------------------------------------------
def main():
    obs = load_observations()

    # --- 1. the two counterexamples ----------------------------------------------------------
    counterexamples = []
    for cid, rate, n, b in [("T219-R600p0-N3000-B3001", "600.0", 3000, 3001),
                            ("T219-R600p0-N3000-B4499", "600.0", 3000, 4499)]:
        d = derive(rate, n, b)
        o = observe(obs[cid])
        d.update({
            "id": cid, "observed": o,
            "site3py_form_agrees": d["site3py_totalInterestMinor"] == o["totalInterestMinor"],
            "corrected_form_agrees": d["corrected_totalInterestMinor"] == o["totalInterestMinor"],
            "site3py_form_equals_observed_TOTAL_REPAYMENT":
                d["site3py_totalInterestMinor"] == o["totalRepaymentMinor"],
            "totals_match_row_sums": (o["rowSumInterestMinor"] == o["totalInterestMinor"]
                                      and o["rowSumPrincipalMinor"] == o["totalPrincipalMinor"]),
            "derivedPrincipal_matches_observed":
                d["totalPrincipalMinor"] == o["totalPrincipalMinor"],
        })
        counterexamples.append(d)

    # --- 2. every cell T229 and T219 asked ---------------------------------------------------
    census = []
    for rel in ["t229-g8-site3/src/cells-t229.json", "t219-g8-residual/src/cells-t219.json"]:
        for c in json.load(open(os.path.join(CAP, rel))):
            d = derive(c["rate"], c["n"], c["bMinor"])
            cap = obs.get(c["id"]) or obs.get(c["id"] + "-RUN3")
            o = observe(cap) if cap else {"present": False, "file": None}
            row = {"id": c["id"], "cellsFile": rel, "outcome": d["outcome"],
                   "eMinor": d["eMinor"], "deltaMinor": d["deltaMinor"],
                   "site3py": d["site3py_totalInterestMinor"],
                   "corrected": d["corrected_totalInterestMinor"], "observed": o}
            if o["present"] and d["site3py_totalInterestMinor"] is not None:
                row["site3py_agrees"] = d["site3py_totalInterestMinor"] == o["totalInterestMinor"]
                row["corrected_agrees"] = d["corrected_totalInterestMinor"] == o["totalInterestMinor"]
            census.append(row)

    # --- 3. the whole committed stuck-cell corpus --------------------------------------------
    vc = json.load(open(os.path.join(CAP, "t229-g8-site3/out/validate-corpus.json")))
    rows = vc["rows"]

    def bucket(sel, label):
        rs = [r for r in rows if sel(r)]
        return {
            "bucket": label, "cells": len(rs),
            "factA_holds": sum(1 for r in rs if r["factA_emiDiffEqualsB"]),
            "site3py_interest_law_holds":
                sum(1 for r in rs if r["interestObserved"] == r["n"] * r["eMinor"] + r["bMinor"]),
            "corrected_interest_law_holds":
                sum(1 for r in rs if r["interestObserved"]
                    == r["n"] * r["eMinor"] + r["bMinor"] - r["principalObserved"]),
            "totalRepayment_equals_nE_plus_B":
                sum(1 for r in rs if r["interestObserved"] + r["principalObserved"]
                    == r["n"] * r["eMinor"] + r["bMinor"]),
            "observedPrincipal_is_zero": sum(1 for r in rs if r["principalObserved"] == 0),
        }

    corpus = {
        "source": "t229-g8-site3/out/validate-corpus.json (T229's own committed corpus census)",
        "buckets": [
            bucket(lambda r: True, "ALL stuck cells"),
            bucket(lambda r: r["delta"] >= 1, "delta >= 1"),
            bucket(lambda r: r["delta"] == 0, "delta == 0"),
            bucket(lambda r: r["factA_emiDiffEqualsB"], "FACT A holds"),
            bucket(lambda r: not r["factA_emiDiffEqualsB"], "FACT A fails"),
        ],
    }

    payload = {
        "task": "T241",
        "oracleContacted": False,
        "observationSource": "committed .gz raw captures only (G-8 STANDING RULE 5)",
        "mathContext": "precision 19, HALF_UP (the ratified production setting)",
        "counterexamples": counterexamples,
        "cellCensus": census,
        "corpusCensus": corpus,
    }
    outdir = os.path.join(HERE, "..", "out")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "rederivation-t241.json"), "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)

    for d in counterexamples:
        o = d["observed"]
        print("%s  n=%d B=%d  E=%d I1q=%d delta=%d a=%d  %s  principal=%s"
              % (d["id"], d["n"], d["bMinor"], d["eMinor"], d["i1QuantizedMinor"],
                 d["deltaMinor"], d["aMinor"], d["outcome"], d["totalPrincipalMinor"]))
        print("    site3.py  n*E+B     = %d   agrees with observed interest? %s"
              % (d["site3py_totalInterestMinor"], d["site3py_form_agrees"]))
        print("    corrected n*E+B-P   = %d   agrees with observed interest? %s"
              % (d["corrected_totalInterestMinor"], d["corrected_form_agrees"]))
        print("    observed interest %d · principal %d · repayment %d (row sums %d / %d / %d)"
              % (o["totalInterestMinor"], o["totalPrincipalMinor"], o["totalRepaymentMinor"],
                 o["rowSumInterestMinor"], o["rowSumPrincipalMinor"], o["rowSumTotalMinor"]))
        print("    n*E+B IS the observed TOTAL REPAYMENT: %s"
              % d["site3py_form_equals_observed_TOTAL_REPAYMENT"])
    print()
    for b in corpus["buckets"]:
        print("%-18s cells %4d · FACT A %4d · n*E+B %4d · n*E+B-P %4d · repay==n*E+B %4d · P==0 %4d"
              % (b["bucket"], b["cells"], b["factA_holds"], b["site3py_interest_law_holds"],
                 b["corrected_interest_law_holds"], b["totalRepayment_equals_nE_plus_B"],
                 b["observedPrincipal_is_zero"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
