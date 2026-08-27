#!/usr/bin/env python3
"""T277 -- INDEPENDENT re-derivation of the G-8 unrescued-cell shape law and the
T241 corpus re-bucketing, from the committed RAW `.json.gz` schedule captures.

WHY THIS FILE EXISTS
--------------------
`.softhouse/gates.md` (the block around the `### THE LAW` heading of
`## G-8 -- TWO phenomena at the rounding floor`) states the shape of an UNRESCUED
cell as TWO laws:

    (i)  last row EMI    = E + B
    (ii) TOTAL PRINCIPAL = max(0, B_minor - n*delta)

The cloud's T241 (branch `refs/remotes/origin/softhouse/T241-g8-evidence-hygiene`,
df0aed2c) narrowed the ANTECEDENT of that block from "unrescued" to "unrescued
cell on which FACT A holds", measured (i) on that new domain, and asserted (ii)
was sound. T264 (`refs/heads/softhouse/t264-review-cloud-t241`, 406cfb06)
REJECTED that branch and reported that (ii) fails on SEVEN cells of that domain.

This instrument re-derives all of it WITHOUT IMPORTING ANY PRIOR INSTRUMENT:
not T229's `site3.py` / `validate_corpus.py` / `emi_mechanism_t223.py`,
not the cloud's `rederive_total_interest_t241.py`, not T264's scripts.
It reads only the committed `.json.gz` raw captures (STANDING RULE 5).

ARITHMETIC DISCIPLINE (project non-negotiable)
----------------------------------------------
INTEGER MINOR UNITS ONLY. There is no `float`, no `float()`, no `Decimal`,
no `Fraction`, and no true-division (`/`) operator anywhere in this file.
Money strings are parsed to integer minor units by STRING manipulation.
Rates are carried as an exact integer numerator/denominator pair.
Quantization is HALF_UP implemented on integers.

The self-test at the bottom (`--selftest`) proves the parser and the HALF_UP
quantizer on hand-checked cases before any census is reported.

USAGE
-----
    python3 shapelaw_census_t277.py --selftest
    python3 shapelaw_census_t277.py <repo-root>            # full census -> stdout JSON
    python3 shapelaw_census_t277.py <repo-root> --report    # human-readable summary
"""

import glob
import gzip
import json
import os
import sys

MINOR_DIGITS = 2   # MNT: ISO 4217 numeric 496, minor unit 2


# --------------------------------------------------------------------------
# integer money parsing -- no float, no Decimal
# --------------------------------------------------------------------------
def to_minor(s):
    """'1250.07' -> 125007 ; '0.28' -> 28 ; '-1.5' -> -150 ; 3 -> 300.

    Pure string/integer. Raises if the value carries more fractional digits
    than the currency's minor unit (which would mean a silent truncation).
    """
    if s is None:
        raise ValueError("to_minor(None)")
    if isinstance(s, int):
        return s * (10 ** MINOR_DIGITS)
    text = str(s).strip()
    if text == "":
        raise ValueError("to_minor('')")
    neg = False
    if text[0] in "+-":
        neg = text[0] == "-"
        text = text[1:]
    if "." in text:
        whole, frac = text.split(".", 1)
    else:
        whole, frac = text, ""
    if whole == "":
        whole = "0"
    if not whole.isdigit() or (frac != "" and not frac.isdigit()):
        raise ValueError("not a plain decimal: %r" % (s,))
    if len(frac) > MINOR_DIGITS:
        # allow only trailing zeros beyond the minor unit
        if frac[MINOR_DIGITS:].strip("0") != "":
            raise ValueError("more precision than minor unit: %r" % (s,))
        frac = frac[:MINOR_DIGITS]
    frac = (frac + "0" * MINOR_DIGITS)[:MINOR_DIGITS]
    value = int(whole) * (10 ** MINOR_DIGITS) + int(frac)
    return -value if neg else value


def decimal_to_ratio(s):
    """'600.0' -> (6000, 10).  Exact integer numerator/denominator. No float."""
    text = str(s).strip()
    neg = False
    if text[0] in "+-":
        neg = text[0] == "-"
        text = text[1:]
    if "." in text:
        whole, frac = text.split(".", 1)
    else:
        whole, frac = text, ""
    if whole == "":
        whole = "0"
    if not whole.isdigit() or (frac != "" and not frac.isdigit()):
        raise ValueError("not a plain decimal: %r" % (s,))
    num = int(whole + frac) if frac else int(whole)
    den = 10 ** len(frac)
    return (-num if neg else num), den


def half_up_ratio(num, den):
    """HALF_UP quantization of the exact rational num/den to a whole integer.

    HALF_UP rounds away from zero at the .5 boundary (java.math.RoundingMode.HALF_UP),
    which is the tenant setting ratified for MNT (CLAUDE.md: HALF_UP, ordinal 4).
    Implemented on integers only -- floor-division, never `/`.
    """
    if den < 0:
        num, den = -num, -den
    if num >= 0:
        return (2 * num + den) // (2 * den)
    return -((2 * (-num) + den) // (2 * den))


# --------------------------------------------------------------------------
# the rate factor
# --------------------------------------------------------------------------
def monthly_rate_factor(annual_pct_str):
    """Fineract `rateFactorByRepaymentEveryMonth`, DAYS_30 / DAYS_360,
    repaymentEvery = 1, actual == calculated:

        r = (annualNominalInterestRate / 100) * (30 / 360)

    Returned as an EXACT integer pair (num, den). No division performed.
    """
    a_num, a_den = decimal_to_ratio(annual_pct_str)
    # (a_num/a_den) / 100 * 30/360  ==  a_num * 30 / (a_den * 100 * 360)
    return a_num * 30, a_den * 100 * 360


def terminates_within_scale(num, den, scale):
    """True iff the exact rational num/den has a FINITE decimal expansion that
    fits in `scale` fractional digits -- i.e. num*10**scale is divisible by den
    after reducing. If False, the oracle's setScale(19) truncated/rounded the
    rate factor and this cell's I1q is not exactly derivable here.
    """
    return (num * (10 ** scale)) % den == 0


# --------------------------------------------------------------------------
# census
# --------------------------------------------------------------------------
def gz_paths(root):
    pat = os.path.join(root, ".softhouse", "**", "*.json.gz")
    return sorted(glob.glob(pat, recursive=True))


def admit(inputs):
    """The population this law is stated about. Returns (ok, reason)."""
    if inputs.get("repaymentFrequencyType") != "MONTHS":
        return False, "not-monthly"
    if inputs.get("repaymentFrequency") != 1:
        return False, "repaymentEvery!=1"
    if str(inputs.get("mathContextPrecision")) != "19":
        return False, "precision!=19"
    # NOTE: the real input keys are `daysInMonth` / `daysInYear`.
    # T229's validate_corpus.py filtered on `daysInMonthType` / `daysInYearType`,
    # which DO NOT EXIST in the raw captures, so its day-count filter was inert.
    # This instrument filters on the keys that are actually present, and the
    # census below reports whether that changes the admitted population.
    if inputs.get("daysInMonth") not in (None, "DAYS_30"):
        return False, "daysInMonth"
    if inputs.get("daysInYear") not in (None, "DAYS_360"):
        return False, "daysInYear"
    if inputs.get("downPaymentEnabled"):
        return False, "downPayment"
    if inputs.get("currencyInMultiplesOf"):
        return False, "multiplesOf"
    return True, None


def census(root):
    rows = []
    skipped = {}
    files = gz_paths(root)
    for path in files:
        with gzip.open(path) as fh:
            raw = json.load(fh)
        for cap in raw.get("captures", []):
            inputs = cap.get("inputs") or {}
            observed = cap.get("observed")
            if cap.get("threw") or not observed:
                skipped["threw-or-empty"] = skipped.get("threw-or-empty", 0) + 1
                continue
            ok, why = admit(inputs)
            if not ok:
                skipped[why] = skipped.get(why, 0) + 1
                continue

            reps = [p for p in observed["periods"] if p["type"] == "REPAYMENT"]
            if len(reps) < 2:
                skipped["<2-repayment-rows"] = skipped.get("<2-repayment-rows", 0) + 1
                continue

            # ---- STUCK-CELL SELECTOR: row 1 repays no principal ----
            if to_minor(reps[0]["principal"]) != 0:
                skipped["not-stuck"] = skipped.get("not-stuck", 0) + 1
                continue

            b_minor = to_minor(observed["totalDisbursedAmount"])
            n = int(inputs["numberOfRepayments"])
            e_minor = to_minor(reps[0]["total"])
            last_total = to_minor(reps[-1]["total"])

            # ---- ROW SUMS: derived from the schedule, never from the header ----
            row_principal = sum(to_minor(p["principal"]) for p in reps)
            row_interest = sum(to_minor(p["interest"]) for p in reps)
            row_total = sum(to_minor(p["total"]) for p in reps)

            hdr_principal = to_minor(observed["totalPrincipalAmount"])
            hdr_interest = to_minor(observed["totalInterestAmount"])
            hdr_repayment = to_minor(observed["totalRepaymentAmount"])

            r_num, r_den = monthly_rate_factor(str(inputs["annualNominalInterestRate"]))
            rate_exact = terminates_within_scale(r_num, r_den, 19)
            i1q = half_up_ratio(b_minor * r_num, r_den)
            delta = i1q - e_minor

            rows.append({
                "file": os.path.basename(path),
                "id": cap["id"],
                "ratePct": str(inputs["annualNominalInterestRate"]),
                "rateFactorExactAt19": rate_exact,
                "n": n,
                "nRepaymentRows": len(reps),
                "bMinor": b_minor,
                "eMinor": e_minor,
                "i1qMinor": i1q,
                "delta": delta,

                # header vs rows -- if these disagree the header is not trusted
                "headerEqualsRows_principal": hdr_principal == row_principal,
                "headerEqualsRows_interest": hdr_interest == row_interest,
                "headerEqualsRows_repayment": hdr_repayment == row_total,

                "rowPrincipalMinor": row_principal,
                "rowInterestMinor": row_interest,
                "rowRepaymentMinor": row_total,

                # ---- FACT A / law (i): last row EMI == E + B ----
                "lastRowTotalMinor": last_total,
                "lawI_lastRowEmiEqualsEplusB": last_total == e_minor + b_minor,

                # ---- law (ii): TOTAL PRINCIPAL == max(0, B - n*delta) ----
                "lawII_predictedPrincipalMinor": max(0, b_minor - n * delta),
                "lawII_holds": row_principal == max(0, b_minor - n * delta),

                # ---- the interest law the re-bucketing is about ----
                "interestLaw_predictedMinor": n * e_minor + b_minor,
                "interestLaw_holds": row_interest == n * e_minor + b_minor,

                # ---- T241's sharper diagnosis: n*E+B is the REPAYMENT ----
                "repaymentLaw_holds": row_total == n * e_minor + b_minor,
            })
    return files, rows, skipped


def summarize(rows):
    fact_a = [r for r in rows if r["lawI_lastRowEmiEqualsEplusB"]]
    not_fact_a = [r for r in rows if not r["lawI_lastRowEmiEqualsEplusB"]]
    d0 = [r for r in rows if r["delta"] == 0]
    hist = {}
    for r in rows:
        k = str(r["delta"])
        hist[k] = hist.get(k, 0) + 1
    return {
        "stuckCellsExamined": len(rows),
        "deltaHistogram": hist,
        "lawI_factA_holds": len(fact_a),
        "lawII_holds_all": sum(1 for r in rows if r["lawII_holds"]),
        "lawII_holds_on_factA": sum(1 for r in fact_a if r["lawII_holds"]),
        "lawII_factA_domain": len(fact_a),
        "interestLaw_holds_all": sum(1 for r in rows if r["interestLaw_holds"]),
        "interestLaw_fails_all": sum(1 for r in rows if not r["interestLaw_holds"]),
        "interestLaw_holds_on_delta0": sum(1 for r in d0 if r["interestLaw_holds"]),
        "delta0_count": len(d0),
        "repaymentLaw_holds_on_factA": sum(1 for r in fact_a if r["repaymentLaw_holds"]),
        "repaymentLaw_holds_on_notFactA": sum(1 for r in not_fact_a if r["repaymentLaw_holds"]),
        "notFactA_count": len(not_fact_a),
        "headerRowMismatches": sum(
            1 for r in rows
            if not (r["headerEqualsRows_principal"]
                    and r["headerEqualsRows_interest"]
                    and r["headerEqualsRows_repayment"])),
        "rateFactorInexactAt19": sum(1 for r in rows if not r["rateFactorExactAt19"]),
    }


# --------------------------------------------------------------------------
# EXPECTATIONS -- what this instrument asserts about main, so it RE-RUNS as a guard
# --------------------------------------------------------------------------
EXPECTED = {
    "stuckCellsExamined": 296,
    "deltaHistogram": {"0": 113, "1": 183},
    "lawI_factA_holds": 220,
    "lawII_holds_all": 289,
    "lawII_holds_on_factA": 213,
    "lawII_factA_domain": 220,
    "interestLaw_holds_all": 176,
    "interestLaw_fails_all": 120,
    "interestLaw_holds_on_delta0": 0,
    "delta0_count": 113,
    "repaymentLaw_holds_on_factA": 220,
    "repaymentLaw_holds_on_notFactA": 0,
    "notFactA_count": 76,
    "headerRowMismatches": 0,
    "rateFactorInexactAt19": 0,
}

# The EXCEPTION SET of law (ii): the cells on the FACT-A domain where
# TOTAL PRINCIPAL != max(0, B - n*delta). Keyed by (id, file) because the same
# cell id is captured more than once. Value is the OBSERVED principal in minor
# units, against a law-predicted 0.
EXPECTED_LAW_II_EXCEPTIONS = {
    ("T117P2-R600p0-N108-B11", "capture-t117p2-raw.json.gz"): 5,
    ("T117P2-R600p0-N121-B11", "capture-t117p2-raw.json.gz"): 4,
    ("T117P2-R600p0-N150-B11", "capture-t117p2-raw.json.gz"): 2,
    ("T159-R600p0-N108-B11", "capture-t159-raw.json.gz"): 5,
    ("T159-R600p0-N121-B11", "capture-t159-raw.json.gz"): 4,
    ("T159-R600p0-N150-B11", "capture-t159-raw.json.gz"): 2,
    ("T159-R600p0-N2000-B999", "capture-t159-raw.json.gz"): 166,
}


def exceptions(rows):
    out = {}
    for r in rows:
        if not r["lawII_holds"]:
            out[(r["id"], r["file"])] = r["rowPrincipalMinor"]
    return out


def check(rows):
    """Returns (ok, failures[]). This is what makes the file a GUARD and not a table."""
    got = summarize(rows)
    fails = []
    for k, want in EXPECTED.items():
        if got.get(k) != want:
            fails.append("summary[%s]: expected %r, measured %r" % (k, want, got.get(k)))

    exc = exceptions(rows)
    if exc != EXPECTED_LAW_II_EXCEPTIONS:
        for k in sorted(set(exc) | set(EXPECTED_LAW_II_EXCEPTIONS)):
            if exc.get(k) != EXPECTED_LAW_II_EXCEPTIONS.get(k):
                fails.append("lawII exception %s: expected %r, measured %r"
                             % (k, EXPECTED_LAW_II_EXCEPTIONS.get(k), exc.get(k)))

    # Structural claims the gates.md wording depends on:
    #  (a) every law-(ii) exception is on the FACT-A domain
    #  (b) every law-(ii) exception has delta >= 1 and satisfies the FULL family B
    #      antecedent  (delta >= 1 AND B_minor <= n*delta), so the law predicts 0
    #  (c) the exception set is DISJOINT from the delta == 0 cells
    for r in rows:
        if r["lawII_holds"]:
            continue
        if not r["lawI_lastRowEmiEqualsEplusB"]:
            fails.append("exception %s is NOT FACT-A-true" % r["id"])
        if r["delta"] < 1:
            fails.append("exception %s has delta=%d, not >=1" % (r["id"], r["delta"]))
        if not r["bMinor"] <= r["n"] * r["delta"]:
            fails.append("exception %s does not satisfy FULL family B antecedent" % r["id"])
        if r["lawII_predictedPrincipalMinor"] != 0:
            fails.append("exception %s: law predicts %d, not 0"
                         % (r["id"], r["lawII_predictedPrincipalMinor"]))
        if r["rowPrincipalMinor"] <= 0:
            fails.append("exception %s repays %d, not a positive amount"
                         % (r["id"], r["rowPrincipalMinor"]))
    return (len(fails) == 0), fails, got, exc


# --------------------------------------------------------------------------
# self-test of the arithmetic primitives -- run BEFORE any census is believed
# --------------------------------------------------------------------------
def selftest():
    bad = []

    def eq(label, got, want):
        if got != want:
            bad.append("%s: got %r want %r" % (label, got, want))

    eq("to_minor('0.28')", to_minor("0.28"), 28)
    eq("to_minor('1250.07')", to_minor("1250.07"), 125007)
    eq("to_minor('0.00')", to_minor("0.00"), 0)
    eq("to_minor('30.00')", to_minor("30.00"), 3000)
    eq("to_minor('-1.5')", to_minor("-1.5"), -150)
    eq("to_minor('11')", to_minor("11"), 1100)
    eq("to_minor('9.990')", to_minor("9.990"), 999)

    eq("ratio('600.0')", decimal_to_ratio("600.0"), (6000, 10))
    eq("ratio('36.0')", decimal_to_ratio("36.0"), (360, 10))
    eq("ratio('21.6')", decimal_to_ratio("21.6"), (216, 10))

    # 600.0 % p.a. -> monthly factor 1/2 exactly
    n_, d_ = monthly_rate_factor("600.0")
    eq("rateFactor(600.0) == 1/2", (n_ * 2 == d_), True)
    # 36.0 % p.a. -> monthly factor 3/100 exactly
    n_, d_ = monthly_rate_factor("36.0")
    eq("rateFactor(36.0) == 3/100", (n_ * 100 == d_ * 3), True)

    # HALF_UP: exact halves round AWAY FROM ZERO
    eq("half_up 1/2", half_up_ratio(1, 2), 1)
    eq("half_up 3/2", half_up_ratio(3, 2), 2)
    eq("half_up 5/2", half_up_ratio(5, 2), 3)     # HALF_UP, not HALF_EVEN (=2)
    eq("half_up -1/2", half_up_ratio(-1, 2), -1)
    eq("half_up 1/3", half_up_ratio(1, 3), 0)
    eq("half_up 2/3", half_up_ratio(2, 3), 1)
    eq("half_up 3001/2", half_up_ratio(3001, 2), 1501)   # T241's B3001 I1q
    eq("half_up 4499/2", half_up_ratio(4499, 2), 2250)   # T241's B4499 I1q
    eq("half_up 11/2", half_up_ratio(11, 2), 6)
    eq("half_up 999/2", half_up_ratio(999, 2), 500)

    eq("terminates 1/2 @19", terminates_within_scale(1, 2, 19), True)
    eq("terminates 1/3 @19", terminates_within_scale(1, 3, 19), False)

    # no-float attestation on this very file
    src = open(__file__).read()
    for token in ("float(", "Decimal", "Fraction", "import decimal", "import fractions"):
        if token in src.replace("no `Decimal`", "").replace("no `Fraction`", ""):
            pass  # docstring mentions are stripped below by the AST check
    return bad


def ast_no_float(path):
    """AST-level proof: no float literal, no float() call, no true-division node."""
    import ast
    tree = ast.parse(open(path).read())
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            findings.append("float literal at line %d" % node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("float", "round"):
            findings.append("%s() call at line %d" % (node.func.id, node.lineno))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            findings.append("true-division at line %d" % node.lineno)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) else [])
            for nm in names:
                if nm and nm.split(".")[0] in ("decimal", "fractions", "numpy", "math"):
                    findings.append("banned import %s at line %d" % (nm, node.lineno))
    return findings


def main(argv):
    if "--selftest" in argv:
        bad = selftest()
        bad += ["AST: " + f for f in ast_no_float(__file__)]
        if bad:
            print("SELFTEST FAIL")
            for b in bad:
                print("  " + b)
            return 1
        print("SELFTEST PASS -- parser, HALF_UP quantizer and rate factor verified; "
              "AST clean: no float literal, no float()/round() call, no true-division, "
              "no decimal/fractions/math import.")
        return 0

    root = argv[1] if len(argv) > 1 else "."
    files, rows, skipped = census(root)
    ok, fails, got, exc = check(rows)

    if "--report" in argv:
        print("T277 shape-law census -- source: %d raw .json.gz captures under %s/.softhouse"
              % (len(files), root))
        for f in files:
            print("    %s" % os.path.relpath(f, root))
        print()
        print("ADMITTED STUCK CELLS: %d   (skipped: %s)" % (len(rows), skipped))
        print()
        for k in sorted(got):
            mark = "  " if got[k] == EXPECTED.get(k) else "!!"
            print("%s %-34s %s   (expected %s)" % (mark, k, got[k], EXPECTED.get(k)))
        print()
        print("LAW (ii) EXCEPTION SET -- observed principal against a law-predicted 0:")
        for (cid, cfile) in sorted(exc):
            r = [x for x in rows if x["id"] == cid and x["file"] == cfile][0]
            print("    %-26s %-28s n=%-5d B=%-5d E=%-5d I1q=%-5d delta=%d "
                  "B<=n*delta=%s  predicted=%d  OBSERVED=%d"
                  % (cid, cfile, r["n"], r["bMinor"], r["eMinor"], r["i1qMinor"],
                     r["delta"], r["bMinor"] <= r["n"] * r["delta"],
                     r["lawII_predictedPrincipalMinor"], r["rowPrincipalMinor"]))
        print()
        if ok:
            print("RESULT: PASS -- every expectation reproduced, exception set exact.")
        else:
            print("RESULT: FAIL")
            for f in fails:
                print("    " + f)
        return 0 if ok else 1

    json.dump({
        "instrument": "T277 shapelaw_census_t277.py",
        "sourceFiles": [os.path.relpath(f, root) for f in files],
        "skipped": skipped,
        "summary": got,
        "expected": EXPECTED,
        "lawII_exceptions": {"%s|%s" % k: v for k, v in sorted(exc.items())},
        "lawII_exceptions_expected": {"%s|%s" % k: v
                                      for k, v in sorted(EXPECTED_LAW_II_EXCEPTIONS.items())},
        "pass": ok,
        "failures": fails,
        "rows": rows,
    }, sys.stdout, indent=1, sort_keys=True)
    print()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
