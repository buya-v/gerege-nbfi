#!/usr/bin/env python3
"""T277 CROSS-CHECK -- a SECOND, independent re-derivation of the law-(ii)
exception set, written by the RESUMING worker so the seven do not rest on a
single instrument.

WHY A SECOND FILE
-----------------
`shapelaw_census_t277.py` is the primary instrument. It derives `I1q` by
COMPUTING the monthly rate factor from `annualNominalInterestRate` and
quantizing HALF_UP. If that derivation were wrong, every `delta` in the census
would be wrong the same way and the pins would still all agree with each other.

This file breaks that shared dependency. It imports NOTHING from the census and
re-derives the rate factor, the HALF_UP quantizer, the admission rule, the
stuck-cell selector and both law forms from scratch, by a different route:
the annual rate is carried as an exact integer numerator over `10^k * 1200`
(never a per-month percentage), and HALF_UP is implemented as `(2a + b) // 2b`
rather than by scaled comparison. Agreement between the two is then agreement
between two separately written arithmetics on the same committed bytes.

A DEAD END WORTH RECORDING, because the next worker will try it too
-------------------------------------------------------------------
The obvious "fully independent" move -- read `I1q` straight out of the schedule's
repayment row 1 instead of computing it -- IS INVALID, and silently so. On a
STUCK cell row 1 repays no principal, so the oracle emits `interest == total == E`:
the reported interest is ALREADY CLIPPED to the instalment and the deficit is
carried, not shown. Taking `I1q` from that field yields `delta = 0` on all 296
cells by construction, which then "refutes" law (ii) on 183 cells and reports the
exception set as disjointness-broken. Measured, not supposed: that run is in
`evidence/60-crosscheck-DEAD-END-i1q-from-row.txt`. `I1q` IS NOT OBSERVABLE in the
emitted schedule; it must be computed from the rate. Anyone re-deriving delta from
row 1's `interest` field is measuring E twice.

It also cross-checks with the total principal taken from the ROW SUM only, never
from the `totalPrincipalAmount` header, and separately reports whether the header
agreed -- so a header/row divergence could not hide inside either figure.

ARITHMETIC
----------
INTEGER MINOR UNITS ONLY. There is no float, no `float()`, no `round()`, no
`Decimal`, no `Fraction`, and no true-division anywhere in this file -- asserted
at AST level by `--selftest`, not merely claimed. Money strings are parsed to
integer minor units by string manipulation. MNT: ISO 4217 numeric 496, minor
unit 2.

USAGE
-----
    python3 crosscheck_seven_t277b.py --selftest
    python3 crosscheck_seven_t277b.py <repo-root>
    python3 crosscheck_seven_t277b.py <repo-root> --i1q-from-row
        # reproduces the DEAD END above on purpose, so the claim that it is a
        # dead end is a measurement and not an assertion. MUST exit non-zero.
"""

import ast
import glob
import gzip
import json
import os
import sys

MINOR_DIGITS = 2

# The four raw captures that existed under `.softhouse/capture/` when T229 ran.
# This is the `t229corpus` scope -- it is NOT "the corpus", and reproducing 296
# is impossible without pinning it. Stated here independently of the census.
SCOPE_T229_CORPUS = (
    "capture-t117-raw.json.gz",
    "capture-t117p2-raw.json.gz",
    "capture-t159-raw.json.gz",
    "capture-t223-raw.json.gz",
)

# What this file must find, or it exits non-zero. Pinned so it FAILS LOUDLY.
EXPECT_STUCK = 296
EXPECT_FACT_A = 220
EXPECT_NOT_FACT_A = 76
EXPECT_LAW_II_ON_FACT_A = 213
EXPECT_SEVEN = (
    ("T117P2-R600p0-N108-B11", 108, 11, 5, 6, 1, 0, 5),
    ("T117P2-R600p0-N121-B11", 121, 11, 5, 6, 1, 0, 4),
    ("T117P2-R600p0-N150-B11", 150, 11, 5, 6, 1, 0, 2),
    ("T159-R600p0-N108-B11", 108, 11, 5, 6, 1, 0, 5),
    ("T159-R600p0-N121-B11", 121, 11, 5, 6, 1, 0, 4),
    ("T159-R600p0-N150-B11", 150, 11, 5, 6, 1, 0, 2),
    ("T159-R600p0-N2000-B999", 2000, 999, 499, 500, 1, 0, 166),
)


def to_minor(value):
    """'9.99' -> 999 ; '0.05' -> 5 ; 3 -> 300. Pure string/integer, no float.

    Raises rather than truncating if more fractional digits are present than the
    currency carries -- a silent truncation in a money path is a defect.
    """
    if value is None:
        raise ValueError("to_minor(None)")
    if isinstance(value, int):
        return value * (10 ** MINOR_DIGITS)
    text = str(value).strip()
    if text == "":
        raise ValueError("to_minor('')")
    negative = text.startswith("-")
    if negative or text.startswith("+"):
        text = text[1:]
    if "." in text:
        whole, frac = text.split(".", 1)
    else:
        whole, frac = text, ""
    if not whole:
        whole = "0"
    if not whole.isdigit() or (frac and not frac.isdigit()):
        raise ValueError("to_minor(%r): not a plain decimal" % (value,))
    if len(frac) > MINOR_DIGITS:
        if frac[MINOR_DIGITS:].strip("0") != "":
            raise ValueError("to_minor(%r): more precision than the minor unit" % (value,))
        frac = frac[:MINOR_DIGITS]
    frac = frac + "0" * (MINOR_DIGITS - len(frac))
    minor = int(whole) * (10 ** MINOR_DIGITS) + int(frac or "0")
    if negative:
        minor = -minor
    return minor


def annual_pct_to_monthly_fraction(pct_text):
    """'600.0' -> (6000, 12000) meaning the EXACT monthly factor 6000/12000 = 1/2.

    monthly factor = annual_percent / 100 / 12 = annual_percent / 1200.
    The percentage is carried as an integer numerator over 10^k, so the returned
    pair is exact: no float, no Decimal, nothing rounded here.
    """
    text = str(pct_text).strip()
    negative = text.startswith("-")
    if negative or text.startswith("+"):
        text = text[1:]
    if "." in text:
        whole, frac = text.split(".", 1)
    else:
        whole, frac = text, ""
    if not whole:
        whole = "0"
    if not whole.isdigit() or (frac and not frac.isdigit()):
        raise ValueError("annual rate %r is not a plain decimal" % (pct_text,))
    numerator = int(whole + frac) if frac else int(whole)
    denominator = (10 ** len(frac)) * 1200
    if negative:
        numerator = -numerator
    return numerator, denominator


def half_up(numerator, denominator):
    """Round numerator/denominator to the nearest integer, HALF away from zero.

    Integer arithmetic only -- FLOOR division on integers, never true division.
    HALF_UP, not HALF_EVEN: 5/2 -> 3, and 7/2 -> 4.
    """
    if denominator <= 0:
        raise ValueError("half_up: non-positive denominator")
    if numerator >= 0:
        return (2 * numerator + denominator) // (2 * denominator)
    return -((-2 * numerator + denominator) // (2 * denominator))


def terminates_within_19(numerator, denominator):
    """True when numerator/denominator has a finite decimal expansion inside 19
    fractional digits -- i.e. denominator divides numerator * 10^19 exactly.

    The oracle computes the rate factor at (19, HALF_UP) with setScale(19). Where
    the exact rational does not terminate inside 19 digits this instrument cannot
    reproduce the oracle's I1q, so the cell is EXCLUDED AND COUNTED, never
    silently admitted.
    """
    return (numerator * (10 ** 19)) % denominator == 0


def gz_paths(root):
    found = []
    for pattern in ("capture/*/out/*-raw.json.gz", "reviews/*/out/*-raw.json.gz"):
        found.extend(glob.glob(os.path.join(root, ".softhouse", pattern)))
    return sorted(found)


def admitted(inputs):
    """The population the shape law is stated about. Coded from the law's own
    stated antecedent, not copied from any prior instrument."""
    if inputs.get("repaymentFrequencyType") != "MONTHS":
        return False
    if inputs.get("repaymentFrequency") != 1:
        return False
    if str(inputs.get("mathContextPrecision")) != "19":
        return False
    if inputs.get("daysInMonth") not in (None, "DAYS_30"):
        return False
    if inputs.get("daysInYear") not in (None, "DAYS_360"):
        return False
    if inputs.get("downPaymentEnabled"):
        return False
    if inputs.get("currencyInMultiplesOf"):
        return False
    return True


def scan(root, i1q_from_row=False):
    cells = []
    excluded = {}
    for path in gz_paths(root):
        base = os.path.basename(path)
        if base not in SCOPE_T229_CORPUS:
            continue
        with gzip.open(path) as handle:
            raw = json.load(handle)
        for cap in raw.get("captures", []):
            observed = cap.get("observed")
            if cap.get("threw") or not observed:
                continue
            if not admitted(cap.get("inputs") or {}):
                continue
            reps = [p for p in observed["periods"] if p["type"] == "REPAYMENT"]
            if len(reps) < 2:
                continue
            if to_minor(reps[0]["principal"]) != 0:
                continue        # not a STUCK cell: row 1 repays principal

            n = int(cap["inputs"]["numberOfRepayments"])
            b_minor = to_minor(observed["totalDisbursedAmount"])
            e_minor = to_minor(reps[0]["total"])

            # I1q -- the UNCLIPPED quantized first-period interest. It is NOT in
            # the emitted schedule (see the DEAD END note at the top), so it is
            # computed from the exact rate fraction and quantized HALF_UP.
            if i1q_from_row:
                i1q = to_minor(reps[0]["interest"])        # deliberately wrong
            else:
                r_num, r_den = annual_pct_to_monthly_fraction(
                    cap["inputs"]["annualNominalInterestRate"])
                if not terminates_within_19(r_num, r_den):
                    key = "rate-factor-inexact-at-19"
                    excluded[key] = excluded.get(key, 0) + 1
                    continue
                i1q = half_up(b_minor * r_num, r_den)
            delta = i1q - e_minor
            row_principal = sum(to_minor(p["principal"]) for p in reps)
            last_total = to_minor(reps[-1]["total"])
            last_interest = to_minor(reps[-1]["interest"])
            head_principal = to_minor(observed["totalPrincipalAmount"])
            non_zero_principal_rows = [
                idx for idx, p in enumerate(reps) if to_minor(p["principal"]) != 0
            ]

            cells.append({
                "file": base,
                "id": cap["id"],
                "n": n,
                "b": b_minor,
                "e": e_minor,
                "i1q": i1q,
                "delta": delta,
                "observedPrincipal": row_principal,
                "headerPrincipal": head_principal,
                "lastTotal": last_total,
                "lastInterest": last_interest,
                "nRepRows": len(reps),
                "nonZeroPrincipalRows": non_zero_principal_rows,
            })
    return cells, excluded


def law_ii_predicted(cell):
    """TOTAL PRINCIPAL = max(0, B_minor - n*delta) -- integers throughout."""
    predicted = cell["b"] - cell["n"] * cell["delta"]
    if predicted < 0:
        predicted = 0
    return predicted


def fact_a(cell):
    """last row EMI = E + B."""
    return cell["lastTotal"] == cell["e"] + cell["b"]


def full_family_b(cell):
    """delta >= 1 AND B_minor <= n*delta."""
    return cell["delta"] >= 1 and cell["b"] <= cell["n"] * cell["delta"]


def selftest():
    assert to_minor("9.99") == 999
    assert to_minor("0.05") == 5
    assert to_minor("14.98") == 1498
    assert to_minor("13.32") == 1332
    assert to_minor(3) == 300
    assert to_minor("-1.50") == -150
    assert to_minor("0") == 0
    try:
        to_minor("0.001")
        raise AssertionError("to_minor accepted sub-minor precision")
    except ValueError:
        pass
    # HALF_UP, hand-checked -- and it is HALF_UP, NOT HALF_EVEN
    assert half_up(5, 2) == 3, "2.5 must round to 3 under HALF_UP"
    assert half_up(7, 2) == 4
    assert half_up(3, 2) == 2, "1.5 must round to 2 (HALF_EVEN would give 2 too)"
    assert half_up(1, 2) == 1, "0.5 must round to 1 -- HALF_EVEN would give 0"
    assert half_up(4, 2) == 2
    assert half_up(-5, 2) == -3
    assert half_up(0, 7) == 0

    # exact monthly rate fraction, hand-checked
    assert annual_pct_to_monthly_fraction("600.0") == (6000, 12000)   # = 1/2
    assert annual_pct_to_monthly_fraction("300.0") == (3000, 12000)   # = 1/4
    assert annual_pct_to_monthly_fraction("36.0") == (360, 12000)     # = 3/100
    assert annual_pct_to_monthly_fraction("7.0") == (70, 12000)       # = 7/1200
    assert terminates_within_19(6000, 12000)
    assert terminates_within_19(360, 12000)
    assert not terminates_within_19(70, 12000), "7/1200 does not terminate"

    # I1q on the sharpest of the seven, by hand:
    #   B = 999 minor, 600.0 % p.a. -> monthly factor 1/2 -> 499.5 -> HALF_UP 500
    assert half_up(999 * 6000, 12000) == 500
    #   E is 499 in that schedule, so delta = 500 - 499 = 1
    assert 500 - 499 == 1

    # law (ii) on hand-checked integers
    probe = {"b": 999, "n": 2000, "delta": 1}
    assert law_ii_predicted(probe) == 0
    probe2 = {"b": 999, "n": 200, "delta": 1}
    assert law_ii_predicted(probe2) == 799
    # FACT A / antecedent on hand-checked integers
    assert fact_a({"lastTotal": 1498, "e": 499, "b": 999})
    assert not fact_a({"lastTotal": 1497, "e": 499, "b": 999})
    assert full_family_b({"delta": 1, "b": 999, "n": 2000})
    assert not full_family_b({"delta": 0, "b": 999, "n": 2000})

    # AST-level proof of arithmetic discipline: ASSERTED, not claimed.
    with open(os.path.abspath(__file__)) as handle:
        tree = ast.parse(handle.read())
    floats = divs = calls = imports = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            floats = floats + 1
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            divs = divs + 1
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("float", "round"):
            calls = calls + 1
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names]
            if isinstance(node, ast.ImportFrom):
                names.append(node.module or "")
            for name in names:
                head = (name or "").split(".")[0]
                if head in ("decimal", "fractions", "math", "numpy",
                            "shapelaw_census_t277", "dump_seven_t277"):
                    imports = imports + 1
    assert floats == 0, "float literal present"
    assert divs == 0, "true-division present"
    assert calls == 0, "float()/round() call present"
    assert imports == 0, "forbidden or shared import present"
    print("SELFTEST PASS -- integer parser, law forms and antecedents hand-checked; "
          "AST clean: 0 float literals, 0 true-division, 0 float()/round(), "
          "0 decimal/fractions/math imports, 0 imports of the primary instrument.")


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0
    if len(argv) < 2:
        sys.stderr.write("usage: crosscheck_seven_t277b.py <repo-root> | --selftest\n")
        return 2
    root = argv[1]
    dead_end = "--i1q-from-row" in argv
    cells, excluded = scan(root, i1q_from_row=dead_end)
    if dead_end:
        print("*** DELIBERATE DEAD-END MODE: I1q taken from repayment row 1's")
        print("*** `interest` field, which on a STUCK cell is already clipped to E.")
        print("*** This run MUST FAIL. It is the calibration for the claim that")
        print("*** I1q is not observable in the emitted schedule.")
        print()

    fact_a_cells = [c for c in cells if fact_a(c)]
    not_fact_a = [c for c in cells if not fact_a(c)]
    exceptions = [c for c in fact_a_cells if law_ii_predicted(c) != c["observedPrincipal"]]
    law_ii_on_fact_a = len(fact_a_cells) - len(exceptions)
    header_mismatch = [c for c in cells if c["headerPrincipal"] != c["observedPrincipal"]]
    delta0 = [c for c in cells if c["delta"] == 0]
    exceptions_at_delta0 = [c for c in exceptions if c["delta"] == 0]
    exceptions_not_fact_a = [c for c in exceptions if not fact_a(c)]
    # the last-row form, checked independently: principal confined to the last
    # repayment row, and equal to max(0, E + B - I_last)
    confined = 0
    last_row_form = 0
    for c in fact_a_cells:
        rows = c["nonZeroPrincipalRows"]
        if rows == [] or rows == [c["nRepRows"] - 1]:
            confined = confined + 1
        predicted = c["e"] + c["b"] - c["lastInterest"]
        if predicted < 0:
            predicted = 0
        if predicted == c["observedPrincipal"]:
            last_row_form = last_row_form + 1

    print("T277 CROSS-CHECK (second instrument, independently written arithmetic)")
    print("  scope t229corpus files: %s" % ", ".join(SCOPE_T229_CORPUS))
    print("  cells excluded and counted: %s" % (excluded or "{}"))
    print("  stuck cells                       %4d   (expected %d)"
          % (len(cells), EXPECT_STUCK))
    print("  FACT A holds                      %4d   (expected %d)"
          % (len(fact_a_cells), EXPECT_FACT_A))
    print("  FACT A fails                      %4d   (expected %d)"
          % (len(not_fact_a), EXPECT_NOT_FACT_A))
    print("  law (ii) holds on FACT A          %4d   (expected %d)"
          % (law_ii_on_fact_a, EXPECT_LAW_II_ON_FACT_A))
    print("  law (ii) EXCEPTIONS on FACT A     %4d   (expected %d)"
          % (len(exceptions), len(EXPECT_SEVEN)))
    print("  delta == 0 cells                  %4d" % len(delta0))
    print("  exceptions with delta == 0        %4d   (DISJOINTNESS: expected 0)"
          % len(exceptions_at_delta0))
    print("  exceptions that FAIL FACT A       %4d   (DISJOINTNESS: expected 0)"
          % len(exceptions_not_fact_a))
    print("  header != row-sum principal       %4d   (expected 0)" % len(header_mismatch))
    print("  principal confined to LAST row    %4d / %d"
          % (confined, len(fact_a_cells)))
    print("  max(0, E + B - I_last) matches    %4d / %d"
          % (last_row_form, len(fact_a_cells)))
    print()
    print("  THE EXCEPTION SET -- integer minor units, principal from the ROW SUM:")
    observed_tuples = []
    for c in sorted(exceptions, key=lambda x: (x["id"],)):
        predicted = law_ii_predicted(c)
        observed_tuples.append(
            (c["id"], c["n"], c["b"], c["e"], c["i1q"], c["delta"],
             predicted, c["observedPrincipal"]))
        print("    %-24s n=%-5d B=%-5d E=%-5d I1q=%-5d delta=%d  "
              "FULL-family-B=%s  law(ii) predicts %d  OBSERVED %d"
              % (c["id"], c["n"], c["b"], c["e"], c["i1q"], c["delta"],
                 full_family_b(c), predicted, c["observedPrincipal"]))

    failures = []
    if len(cells) != EXPECT_STUCK:
        failures.append("stuck cell count moved")
    if len(fact_a_cells) != EXPECT_FACT_A:
        failures.append("FACT A count moved")
    if len(not_fact_a) != EXPECT_NOT_FACT_A:
        failures.append("FACT A failure count moved")
    if law_ii_on_fact_a != EXPECT_LAW_II_ON_FACT_A:
        failures.append("law (ii) count on FACT A moved")
    if tuple(sorted(observed_tuples)) != tuple(sorted(EXPECT_SEVEN)):
        failures.append("EXCEPTION SET moved")
    if exceptions_at_delta0:
        failures.append("an exception has delta == 0 -- disjointness broken")
    if exceptions_not_fact_a:
        failures.append("an exception fails FACT A -- disjointness broken")
    if header_mismatch:
        failures.append("a header principal disagrees with its row sum")
    if not all(full_family_b(c) for c in exceptions):
        failures.append("an exception does NOT satisfy the FULL family B antecedent")

    print()
    if failures:
        print("RESULT: FAIL -- " + " ; ".join(failures))
        return 1
    print("RESULT: PASS -- the seven REPRODUCE against a second, independent "
          "derivation of I1q; every exception satisfies the block's own FULL "
          "family B antecedent and is predicted 0 principal; the exception set "
          "is disjoint from the delta==0 cells and from the FACT-A failures.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
