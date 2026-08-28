#!/usr/bin/env python3
"""
T278 - THIRD-PARTY re-derivation of the G-8 shape law, in integer minor units.

INDEPENDENCE STATEMENT (this is the point of the file):
  This module imports NOTHING from any prior instrument in this program. Not
  T229's  src/site3.py  or  src/validate_corpus.py .  Not T264's scripts.  Not
  the cloud T241's  rederive_total_interest_t241.py .  Not T277's
  shapelaw_census_t277.py , dump_seven_t277.py  or  crosscheck_seven_t277b.py .
  Its only inputs are the committed raw  .json.gz  captures.  It contacts no
  oracle, opens no socket and writes nothing outside stdout.

MONEY DISCIPLINE:
  Integer minor units everywhere, INCLUDING intermediate calculation.  There is
  no float literal, no  float()  or  round()  call, no true-division  /  node and
  no  decimal / fractions / math  import in this file.  That is not a claim: it
  is asserted at AST level by  --selftest  against this file's own source.

  Exact rational arithmetic is carried as (numerator, denominator) integer pairs.
  HALF_UP on a positive rational a/b is  (2a + b) // (2b) , which is  floor(x+1/2) .

DEFINITIONS THIS FILE CHOSE FOR ITSELF (stated so a disagreement can be located):
  minor units    a decimal string is parsed to an integer at the capture's own
                 currencyDecimalPlaces (2 for MNT); a string with more fractional
                 digits than that is a hard error, never a truncation.
  B              the disbursement, in minor units, cross-checked against the
                 DISBURSEMENT period's own principal column.
  n              numberOfRepayments, cross-checked against the REPAYMENT row count.
  E              repayment row 1's  total .  On a stuck cell row 1 repays no
                 principal, so its  total  IS the instalment.
  I1q            B * (rate / 1200), quantized HALF_UP to whole minor units.
                 COMPUTED FROM THE RATE.  It is NOT read from row 1's  interest
                 field, which on a stuck cell is already clipped to E.
  delta          I1q - E.
  stuck cell     repayment row 1 repays exactly 0 principal.
  observed
  principal      the SUM OF THE PRINCIPAL COLUMN over every REPAYMENT row.
                 Never a header.  (The header is separately compared to it.)

USAGE
  --selftest                 hand-checked arithmetic + AST money-discipline audit
  --scope t229corpus | all   run the census over one of two capture scopes
  --seven                    row-level dump of the law-(ii) exception cells
  --i1q-from-row             DELIBERATELY WRONG: take I1q from row 1's interest
                             field, to demonstrate the failure mode independently
"""

import argparse
import ast
import glob
import gzip
import json
import os
import sys

# --------------------------------------------------------------------------
# scopes
# --------------------------------------------------------------------------

# The four raw captures that existed under .softhouse/capture/ when T229 ran.
SCOPE_T229CORPUS = (
    ".softhouse/capture/t117-familyb/out/capture-t117-raw.json.gz",
    ".softhouse/capture/t117-familyb/out/capture-t117p2-raw.json.gz",
    ".softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz",
    ".softhouse/capture/t223-g8-region-predicate/out/capture-t223-raw.json.gz",
)

SCOPE_ALL_GLOBS = (
    ".softhouse/capture/*/out/*raw*.json.gz",
    ".softhouse/reviews/*/out/*raw*.json.gz",
)


def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    while here != "/":
        if os.path.isdir(os.path.join(here, ".softhouse")) and os.path.isdir(
            os.path.join(here, ".git")
        ):
            return here
        here = os.path.dirname(here)
    raise SystemExit("T278: cannot locate repo root")


def scope_files(root, scope):
    if scope == "t229corpus":
        out = [os.path.join(root, p) for p in SCOPE_T229CORPUS]
        for p in out:
            if not os.path.exists(p):
                raise SystemExit("T278: missing scope file " + p)
        return out
    if scope == "all":
        seen = []
        for g in SCOPE_ALL_GLOBS:
            for p in sorted(glob.glob(os.path.join(root, g))):
                if p not in seen:
                    seen.append(p)
        return sorted(seen)
    raise SystemExit("T278: unknown scope " + scope)


# --------------------------------------------------------------------------
# integer money + exact rational helpers.  No float, no decimal, no fractions.
# --------------------------------------------------------------------------


def parse_decimal_to_scaled(text, places):
    """'0.28', 2 -> 28.   '600.0', 4 -> 6000000.   Exact; never truncates."""
    if not isinstance(text, str):
        raise ValueError("money/rate must arrive as a string, got " + repr(text))
    s = text.strip()
    neg = False
    if s.startswith("-"):
        neg = True
        s = s[1:]
    elif s.startswith("+"):
        s = s[1:]
    if "." in s:
        whole, frac = s.split(".", 1)
    else:
        whole, frac = s, ""
    if whole == "":
        whole = "0"
    if not whole.isdigit() or (frac != "" and not frac.isdigit()):
        raise ValueError("not a plain decimal: " + repr(text))
    if len(frac) > places:
        # only allowed if the excess digits are all zero
        if frac[places:].strip("0") != "":
            raise ValueError(
                "value %r has more significant fractional digits than %d"
                % (text, places)
            )
        frac = frac[:places]
    frac = frac + "0" * (places - len(frac))
    val = int(whole) * (10 ** places) + (int(frac) if frac else 0)
    return -val if neg else val


def minor(text):
    """MNT minor units: 2 decimal places, exact."""
    return parse_decimal_to_scaled(text, 2)


def igcd(a, b):
    a = a if a >= 0 else -a
    b = b if b >= 0 else -b
    while b:
        a, b = b, a % b
    return a


def half_up_div(a, b):
    """HALF_UP quantization of the exact rational a/b to an integer.  b > 0."""
    if b <= 0:
        raise ValueError("denominator must be positive")
    if a >= 0:
        return (2 * a + b) // (2 * b)
    # HALF_UP on a negative goes away from zero
    return -((2 * (-a) + b) // (2 * b))


def monthly_rate_fraction(annual_rate_text):
    """
    Exact monthly rate as (num, den) integers.   annual% / 100 / 12  ==  r / 1200.
    '600.0' -> (6000, 12000) -> reduced (1, 2).
    """
    k = 0
    if "." in annual_rate_text:
        k = len(annual_rate_text.split(".", 1)[1])
    num = parse_decimal_to_scaled(annual_rate_text, k)
    den = (10 ** k) * 1200
    g = igcd(num, den)
    if g:
        num, den = num // g, den // g
    return num, den


def terminates_within(den, frac_digits):
    """
    True iff a reduced fraction with denominator  den  has a finite decimal
    expansion using at most  frac_digits  fractional digits, i.e. den = 2^a*5^b
    with max(a, b) <= frac_digits.  The oracle holds the monthly factor at
    setScale(19)/(19, HALF_UP); outside this class we cannot reproduce it exactly
    and the cell is EXCLUDED AND COUNTED rather than silently admitted.
    """
    a = 0
    b = 0
    d = den
    while d % 2 == 0:
        d = d // 2
        a += 1
    while d % 5 == 0:
        d = d // 5
        b += 1
    if d != 1:
        return False
    return a <= frac_digits and b <= frac_digits


# --------------------------------------------------------------------------
# capture reading + admission
# --------------------------------------------------------------------------

REQUIRED_UNIFORM = {
    "repaymentFrequency": 1,
    "repaymentFrequencyType": "MONTHS",
    "daysInMonth": "DAYS_30",
    "daysInYear": "DAYS_360",
    "daysInYearCustomStrategy": None,
    "downPaymentEnabled": False,
    "currencyInMultiplesOf": None,
    "installmentAmountInMultiplesOf": None,
    "fixedLength": None,
    "interestRecognitionOnDisbursementDate": False,
    "interestMethod": "DECLINING_BALANCE",
    "allowFullTermForTranche": False,
    "currencyDecimalPlaces": 2,
    "currencyCode": "MNT",
    "mathContextPrecision": 19,
    "mathContextRoundingModeOrdinal": 4,
}


class Reject(Exception):
    pass


def load_cell(cap, source, i1q_from_row):
    """Return a dict of integer facts, or raise Reject(reason)."""
    inp = cap["inputs"]
    obs = cap.get("observed")
    cid = cap.get("id")
    if obs is None:
        raise Reject("no observed block (refusal/error capture)")
    for k, v in REQUIRED_UNIFORM.items():
        if k not in inp:
            raise Reject("missing input key " + k)
        if inp[k] != v:
            raise Reject("non-uniform input %s=%r" % (k, inp[k]))

    num, den = monthly_rate_fraction(inp["annualNominalInterestRate"])
    if not terminates_within(den, 19):
        raise Reject(
            "monthly rate factor %s/%s does not terminate within 19 fractional "
            "digits; the oracle's setScale(19) value is not reproducible here"
            % (num, den)
        )

    n = inp["numberOfRepayments"]
    if not isinstance(n, int) or n < 1:
        raise Reject("bad numberOfRepayments")

    B = minor(inp["disbursementAmount"])
    if B <= 0:
        raise Reject("non-positive disbursement")

    periods = obs["periods"]
    disb = [p for p in periods if p.get("type") == "DISBURSEMENT"]
    rows = [p for p in periods if p.get("type") == "REPAYMENT"]
    if len(disb) != 1:
        raise Reject("expected exactly one DISBURSEMENT period")
    if minor(disb[0]["principal"]) != B:
        raise Reject("disbursement row principal != input disbursementAmount")
    if len(rows) != n:
        raise Reject("REPAYMENT row count %d != n %d" % (len(rows), n))

    prin = [minor(r["principal"]) for r in rows]
    inte = [minor(r["interest"]) for r in rows]
    tot = [minor(r["total"]) for r in rows]
    fee = [minor(r["feeAmount"]) for r in rows]
    pen = [minor(r["penaltyAmount"]) for r in rows]
    if any(f != 0 for f in fee) or any(p != 0 for p in pen):
        raise Reject("fees or penalties present")
    for j in range(n):
        if prin[j] + inte[j] != tot[j]:
            raise Reject("row %d: principal+interest != total" % (j + 1))

    stuck = prin[0] == 0
    E = tot[0]
    if i1q_from_row:
        I1q = inte[0]          # THE TRAP - see --i1q-from-row
    else:
        I1q = half_up_div(B * num, den)
    delta = I1q - E

    return {
        "id": cid,
        "source": os.path.basename(source),
        "n": n,
        "B": B,
        "E": E,
        "I1q": I1q,
        "delta": delta,
        "stuck": stuck,
        "principal_rows": prin,
        "principal_sum": sum(prin),
        "interest_sum": sum(inte),
        "total_sum": sum(tot),
        "I_last": inte[n - 1],
        "last_total": tot[n - 1],
        "hdr_principal": minor(obs["totalPrincipalAmount"]),
        "hdr_interest": minor(obs["totalInterestAmount"]),
        "hdr_repayment": minor(obs["totalRepaymentAmount"]),
        "rate": inp["annualNominalInterestRate"],
    }


# --------------------------------------------------------------------------
# the laws, restated here in integer form from the gates.md block
# --------------------------------------------------------------------------


def law_i_fact_a(c):
    """(i)  last row EMI = E + B."""
    return c["last_total"] == c["E"] + c["B"]


def law_ii_predicted(c):
    """(ii) TOTAL PRINCIPAL = max(0, B_minor - n*delta)."""
    v = c["B"] - c["n"] * c["delta"]
    return v if v > 0 else 0


def law_ii_holds(c):
    return c["principal_sum"] == law_ii_predicted(c)


def full_family_b(c):
    """FULL family B  <=>  delta >= 1  and  B_minor <= n*delta."""
    return c["delta"] >= 1 and c["B"] <= c["n"] * c["delta"]


def partial_family_b(c):
    """PARTIAL family B <=> delta >= 1 and n*delta < B_minor < (delta + 1/2)*n."""
    return (
        c["delta"] >= 1
        and c["n"] * c["delta"] < c["B"]
        and 2 * c["B"] < (2 * c["delta"] + 1) * c["n"]
    )


def last_row_law(c):
    """descriptive: TOTAL PRINCIPAL = max(0, E + B_minor - I_last)."""
    v = c["E"] + c["B"] - c["I_last"]
    return c["principal_sum"] == (v if v > 0 else 0)


def principal_confined_to_last_row(c):
    return all(p == 0 for p in c["principal_rows"][:-1])


# --------------------------------------------------------------------------
# census
# --------------------------------------------------------------------------


def census(root, scope, i1q_from_row=False):
    files = scope_files(root, scope)
    read = 0
    admitted = []
    rejected = []
    for path in files:
        blob = json.loads(gzip.open(path, "rt").read())
        if blob.get("moneyHelperPrecision") != 19:
            raise SystemExit("T278: capture not at precision 19: " + path)
        for cap in blob["captures"]:
            read += 1
            try:
                admitted.append(load_cell(cap, path, i1q_from_row))
            except Reject as e:
                rejected.append((cap.get("id"), str(e)))
    if len(admitted) + len(rejected) != read:
        raise SystemExit("T278: completeness refusal - cells do not account")

    stuck = [c for c in admitted if c["stuck"]]
    fact_a = [c for c in stuck if law_i_fact_a(c)]
    not_fact_a = [c for c in stuck if not law_i_fact_a(c)]
    d0 = [c for c in stuck if c["delta"] == 0]
    d1 = [c for c in stuck if c["delta"] == 1]
    dother = [c for c in stuck if c["delta"] not in (0, 1)]
    fullb = [c for c in stuck if full_family_b(c)]
    partb = [c for c in stuck if partial_family_b(c)]
    exceptions = [c for c in stuck if not law_ii_holds(c)]

    hist = {}
    for c in stuck:
        hist[c["delta"]] = hist.get(c["delta"], 0) + 1

    rep = {
        "scope": scope,
        "files": [os.path.relpath(p, root) for p in files],
        "capturesRead": read,
        "admitted": len(admitted),
        "rejected": len(rejected),
        "rejectReasons": sorted(set(r for _, r in rejected)),
        "rejectedIds": sorted(str(i) for i, _ in rejected),
        "stuckCells": len(stuck),
        "deltaHistogram": {str(k): v for k, v in sorted(hist.items())},
        "deltaOtherThan0or1": [c["id"] for c in dother],
        "factA_holds": len(fact_a),
        "factA_fails": len(not_fact_a),
        "lawII_holds_allStuck": len(stuck) - len(exceptions),
        "lawII_fails_allStuck": len(exceptions),
        "lawII_holds_onFactA": sum(1 for c in fact_a if law_ii_holds(c)),
        "lawII_fails_onFactA": sum(1 for c in fact_a if not law_ii_holds(c)),
        "lawII_holds_on_delta0": sum(1 for c in d0 if law_ii_holds(c)),
        "delta0_count": len(d0),
        "delta1_count": len(d1),
        "fullFamilyB_count": len(fullb),
        "lawII_holds_on_fullFamilyB": sum(1 for c in fullb if law_ii_holds(c)),
        "partialFamilyB_count": len(partb),
        "lawII_holds_on_partialFamilyB": sum(1 for c in partb if law_ii_holds(c)),
        "exceptionIds": [c["id"] for c in exceptions],
        "exceptionAmounts": [c["principal_sum"] for c in exceptions],
        # disjointness, measured not assumed
        "exceptions_intersect_delta0": len(
            [c for c in exceptions if c["delta"] == 0]
        ),
        "exceptions_intersect_factA_failures": len(
            [c for c in exceptions if not law_i_fact_a(c)]
        ),
        "exceptions_all_satisfy_fullFamilyB": all(full_family_b(c) for c in exceptions),
        "factA_failures_that_are_delta0": sum(1 for c in not_fact_a if c["delta"] == 0),
        "delta0_cells_that_hold_factA": sum(1 for c in d0 if law_i_fact_a(c)),
        # header vs row sum - so nothing above rests on a header
        "headerPrincipalMismatches": sum(
            1 for c in stuck if c["hdr_principal"] != c["principal_sum"]
        ),
        "headerInterestMismatches": sum(
            1 for c in stuck if c["hdr_interest"] != c["interest_sum"]
        ),
        "headerRepaymentMismatches": sum(
            1 for c in stuck if c["hdr_repayment"] != c["total_sum"]
        ),
        # the descriptive last-row form
        "lastRowLaw_holds_onFactA": sum(1 for c in fact_a if last_row_law(c)),
        "lastRowLaw_holds_onNotFactA": sum(
            1 for c in not_fact_a if last_row_law(c)
        ),
        "principalConfinedToLastRow_onFactA": sum(
            1 for c in fact_a if principal_confined_to_last_row(c)
        ),
        "principalConfinedToLastRow_onNotFactA": sum(
            1 for c in not_fact_a if principal_confined_to_last_row(c)
        ),
        # the total-repayment discriminator  TOTAL REPAYMENT = n*E + B
        "totalRepaymentLaw_onFactA": sum(
            1 for c in fact_a if c["total_sum"] == c["n"] * c["E"] + c["B"]
        ),
        "totalRepaymentLaw_onNotFactA": sum(
            1 for c in not_fact_a if c["total_sum"] == c["n"] * c["E"] + c["B"]
        ),
        # the FALSE interest form  (n*E + B)  vs the corrected one  (n*E + B - principal)
        "interestEqualsNEplusB_allStuck": sum(
            1 for c in stuck if c["interest_sum"] == c["n"] * c["E"] + c["B"]
        ),
        "interestEqualsNEplusB_fails_allStuck": sum(
            1 for c in stuck if c["interest_sum"] != c["n"] * c["E"] + c["B"]
        ),
        "interestEqualsNEplusB_on_delta0": sum(
            1 for c in d0 if c["interest_sum"] == c["n"] * c["E"] + c["B"]
        ),
        "correctedInterestForm_onFactA": sum(
            1
            for c in fact_a
            if c["interest_sum"] == c["n"] * c["E"] + c["B"] - c["principal_sum"]
        ),
        "correctedInterestForm_onNotFactA": sum(
            1
            for c in not_fact_a
            if c["interest_sum"] == c["n"] * c["E"] + c["B"] - c["principal_sum"]
        ),
        # non-stuck (amortizing) admitted cells - stated so the scope is legible
        "admittedNotStuck": len(admitted) - len(stuck),
    }
    return rep, stuck, exceptions


# --------------------------------------------------------------------------
# self-test: hand-checked arithmetic, then an AST audit of THIS file
# --------------------------------------------------------------------------

FORBIDDEN_CALL_NAMES = ("float", "round")
FORBIDDEN_IMPORTS = ("decimal", "fractions", "math", "numpy")


def ast_money_audit(path):
    src = open(path, "r").read()
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        # a float LITERAL anywhere in the source.  Identified by the runtime type
        # NAME of the constant rather than by referencing the builtin, so that the
        # detector does not itself contain the identifier it forbids.
        if isinstance(node, ast.Constant):
            if type(node.value).__name__ == "float":
                hits.append("float literal at line %d" % node.lineno)
            if type(node.value).__name__ == "complex":
                hits.append("complex literal at line %d" % node.lineno)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            hits.append("true-division node at line %d" % node.lineno)
        if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Div):
            hits.append("true-division augassign at line %d" % node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALL_NAMES:
                hits.append(
                    "call to %s() at line %d" % (node.func.id, node.lineno)
                )
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            else:
                names = [(node.module or "").split(".")[0]]
            for nm in names:
                if nm in FORBIDDEN_IMPORTS:
                    hits.append("import %s at line %d" % (nm, node.lineno))
                if "t277" in nm or "site3" in nm or "t241" in nm or "t264" in nm:
                    hits.append(
                        "INDEPENDENCE VIOLATION: import %s at line %d"
                        % (nm, node.lineno)
                    )
    return hits


def selftest():
    ok = True

    def check(label, got, want):
        nonlocal ok
        good = got == want
        if not good:
            ok = False
        print("  %-58s got=%-14r want=%-14r %s" % (label, got, want, "OK" if good else "FAIL"))

    print("T278 SELFTEST - hand-checked integer arithmetic")
    check("minor('0.28')", minor("0.28"), 28)
    check("minor('9.99')", minor("9.99"), 999)
    check("minor('1498.00')", minor("1498.00"), 149800)
    check("minor('0')", minor("0"), 0)
    check("minor('-0.05')", minor("-0.05"), -5)

    # HALF_UP is not HALF_EVEN.  1/2->1, 3/2->2, 5/2->3, 7/2->4.
    check("half_up 1/2", half_up_div(1, 2), 1)
    check("half_up 3/2", half_up_div(3, 2), 2)
    check("half_up 5/2 (HALF_EVEN would say 2)", half_up_div(5, 2), 3)
    check("half_up 7/2", half_up_div(7, 2), 4)
    check("half_up 4/2", half_up_div(4, 2), 2)
    check("half_up 1/3", half_up_div(1, 3), 0)
    check("half_up 2/3", half_up_div(2, 3), 1)

    # the four rate fractions the corpus actually uses at 600/300/36, plus 7.0
    check("rate 600.0 -> monthly", monthly_rate_fraction("600.0"), (1, 2))
    check("rate 300.0 -> monthly", monthly_rate_fraction("300.0"), (1, 4))
    check("rate 36.0  -> monthly", monthly_rate_fraction("36.0"), (3, 100))
    check("rate 21.6  -> monthly", monthly_rate_fraction("21.6"), (9, 500))
    check("rate 7.0   -> monthly", monthly_rate_fraction("7.0"), (7, 1200))
    check("600.0 terminates<=19", terminates_within(2, 19), True)
    check("36.0 terminates<=19", terminates_within(100, 19), True)
    check("7.0 does NOT terminate<=19", terminates_within(1200, 19), False)

    # THE SHARPEST CELL, worked by hand:
    #   B = 999 minor, rate 600.0%/yr -> monthly 1/2, I1 = 999/2 = 499.5,
    #   HALF_UP -> I1q = 500.  E = 499 (row 1 total).  delta = 1.
    #   B <= n*delta  <=>  999 <= 2000  -> FULL family B antecedent HOLDS,
    #   so law (ii) predicts max(0, 999 - 2000*1) = 0.
    n, d = monthly_rate_fraction("600.0")
    check("I1q for B=999 at 600.0%", half_up_div(999 * n, d), 500)
    fake = {"B": 999, "n": 2000, "delta": 1, "principal_sum": 166}
    check("law (ii) predicts 0 on B=999/n=2000", law_ii_predicted(fake), 0)
    check("full_family_b holds on B=999/n=2000", full_family_b(fake), True)
    check("law (ii) FAILS there", law_ii_holds(fake), False)
    # and the descriptive last-row form on that same cell: 499 + 999 - 1332 = 166
    fake2 = dict(fake)
    fake2.update({"E": 499, "I_last": 1332})
    check("last-row form 499+999-1332", last_row_law(fake2), True)
    # B=11, n=108: I1 = 11/2 = 5.5 -> HALF_UP 6, E=5, delta=1, predict 0
    check("I1q for B=11 at 600.0%", half_up_div(11 * n, d), 6)

    print("T278 SELFTEST - AST money-discipline + independence audit of this file")
    hits = ast_money_audit(os.path.abspath(__file__))
    for h in hits:
        print("  VIOLATION:", h)
    check("AST violations in t278_rederive.py", len(hits), 0)

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# --------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scope", choices=("t229corpus", "all"), default=None)
    ap.add_argument("--seven", action="store_true")
    ap.add_argument("--i1q-from-row", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    root = repo_root()
    os.chdir(root)
    scope = a.scope or "t229corpus"
    rep, stuck, exceptions = census(root, scope, a.i1q_from_row)

    if a.seven:
        print("T278 EXCEPTION-CELL DUMP - scope=%s  i1q_from_row=%s"
              % (scope, a.i1q_from_row))
        print("principal is the SUM OF THE PRINCIPAL COLUMN, never a header")
        print("")
        for c in sorted(exceptions, key=lambda x: (x["source"], x["n"])):
            print(
                "%-26s src=%-28s n=%-5d B=%-5d E=%-5d I1q=%-5d delta=%-2d "
                "FULLfamB=%-5s predicts=%-4d OBSERVED=%-5d  hdr=%-5d "
                "I_last=%-6d lastTotal=%-6d E+B=%-6d"
                % (
                    c["id"], c["source"], c["n"], c["B"], c["E"], c["I1q"],
                    c["delta"], str(full_family_b(c)), law_ii_predicted(c),
                    c["principal_sum"], c["hdr_principal"], c["I_last"],
                    c["last_total"], c["E"] + c["B"],
                )
            )
            print(
                "%-26s   principal rows non-zero at: %s"
                % ("", [(i + 1, p) for i, p in enumerate(c["principal_rows"]) if p])
            )
        print("")
        print("exception count: %d   amounts: %s"
              % (len(exceptions), rep["exceptionAmounts"]))
        return 0

    if a.json:
        print(json.dumps(rep, indent=2, sort_keys=True))
        return 0

    print("T278 CENSUS - scope=%s   i1q_from_row=%s" % (scope, a.i1q_from_row))
    for k in sorted(rep):
        print("  %-42s %s" % (k, rep[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
