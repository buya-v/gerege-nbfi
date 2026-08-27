#!/usr/bin/env python3
"""T159 — INDEPENDENT re-derivation of T117's money claims from the RAW captures.

Reads ONLY `out/capture-t117-raw.json.gz` and `out/capture-t117p2-raw.json.gz`
(the bytes the oracle emitted). Does NOT read any of T117's analysis output.

MONEY DISCIPLINE (P-25): every monetary quantity here is an INTEGER number of
minor units, obtained by splitting the oracle's BigDecimal.toPlainString() JSON
string on '.' and padding to `dp`. No float, no Decimal-of-float, anywhere on a
money path. json.load uses parse_float=Decimal purely as a belt-and-braces guard
for any NON-money numeric literal; money is never routed through it.
"""
import gzip
import json
import sys
from decimal import Decimal
from fractions import Fraction

DP = 2  # MNT


def minor(s, dp=DP):
    """'5.01' -> 501 (integer minor units). Rejects anything not a string."""
    if not isinstance(s, str):
        raise TypeError("money must arrive as a JSON string, got %r (%s)" % (s, type(s)))
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    if "." in s:
        whole, frac = s.split(".", 1)
    else:
        whole, frac = s, ""
    if len(frac) > dp:
        raise ValueError("more fractional digits than dp: %r" % s)
    frac = frac + "0" * (dp - len(frac))
    v = int(whole or "0") * (10 ** dp) + int(frac or "0")
    return -v if neg else v


def load(path):
    with gzip.open(path, "rt") as fh:
        return json.load(fh, parse_float=Decimal)


def census(cap):
    """Return an integer-minor-unit census of one capture case."""
    o = cap["observed"]
    periods = o["periods"]
    disb_rows = [p for p in periods if p.get("type") == "DISBURSEMENT"]
    rep_rows = [p for p in periods if p.get("type") == "REPAYMENT"]
    other = [p for p in periods if p.get("type") not in ("DISBURSEMENT", "REPAYMENT")]
    disbursed = sum(minor(p["principal"]) for p in disb_rows)
    amortized = sum(minor(p["principal"]) for p in rep_rows)
    interest = sum(minor(p["interest"]) for p in rep_rows)
    zero_principal_rows = sum(1 for p in rep_rows if p["principal"] == "0.00")
    nonzero_principal_rows = [
        (p["periodNumber"], p["principal"]) for p in rep_rows if minor(p["principal"]) != 0
    ]
    balances = [minor(p["balance"]) for p in rep_rows]
    return {
        "id": cap["id"],
        "n_asked": cap["inputs"]["numberOfRepayments"],
        "rate": cap["inputs"]["annualNominalInterestRate"],
        "input_disbursement_minor": minor(cap["inputs"]["disbursementAmount"]),
        "disbursement_rows": len(disb_rows),
        "repayment_rows": len(rep_rows),
        "other_rows": len(other),
        "disbursed_minor": disbursed,
        "amortized_minor": amortized,
        "unamortized_residual_minor": disbursed - amortized,
        "total_principal_amount_minor": minor(o["totalPrincipalAmount"]),
        "total_interest_amount_minor": minor(o["totalInterestAmount"]),
        "summed_row_interest_minor": interest,
        "final_balance_minor": balances[-1] if balances else None,
        "distinct_balances_minor": sorted(set(balances)),
        "rows_with_principal_exactly_0.00": zero_principal_rows,
        "nonzero_principal_rows": nonzero_principal_rows,
        "first_row_interest": rep_rows[0]["interest"] if rep_rows else None,
        "last_row_interest": rep_rows[-1]["interest"] if rep_rows else None,
        "first_due": rep_rows[0]["dueDate"] if rep_rows else None,
        "last_due": rep_rows[-1]["dueDate"] if rep_rows else None,
        "loanTermInDays": o["loanTermInDays"],
    }


def all_cases(paths):
    out = {}
    for p in paths:
        d = load(p)
        tag = "p2" if "t117p2" in p else "p1"
        for c in d["captures"]:
            key = c["id"] if not c["id"].startswith("P-CAL") else c["id"] + "@" + tag
            if key in out:
                raise SystemExit("DUPLICATE id across captures: %s" % key)
            out[key] = c
    return out


def main():
    base = sys.argv[1]
    caps = all_cases([
        base + "/out/capture-t117-raw.json.gz",
        base + "/out/capture-t117p2-raw.json.gz",
    ])
    report = {}

    # --- (b) the headline cell -------------------------------------------
    headline = census(caps["T117P2-R600p0-N1000-B501"])
    report["headline_B501_N1000"] = headline

    # --- (b) the three PARTIAL cells at B = 11 ---------------------------
    report["partial_B11"] = [
        census(caps["T117P2-R600p0-N%d-B11" % n]) for n in (108, 121, 150)
    ]

    # --- whole-corpus residual maximum, re-derived ------------------------
    rows = []
    for cid, c in caps.items():
        if cid.startswith("P-CAL"):
            continue
        cs = census(c)
        rows.append(cs)
    rows.sort(key=lambda r: -r["unamortized_residual_minor"])
    report["case_count_excluding_calibrations"] = len(rows)
    report["max_residual_minor"] = rows[0]["unamortized_residual_minor"]
    report["top10_by_residual"] = [
        {k: r[k] for k in ("id", "disbursed_minor", "amortized_minor",
                           "unamortized_residual_minor", "final_balance_minor")}
        for r in rows[:10]
    ]

    # residual == final balance on every case?
    mismatch = [r["id"] for r in rows
                if r["unamortized_residual_minor"] != r["final_balance_minor"]]
    report["residual_ne_final_balance"] = mismatch

    # --- family-B census, re-derived from raw ----------------------------
    # family B (per gates.md discriminator): the principal column does NOT sum
    # to the disbursement.  family A: it DOES sum, but the balance column is
    # stale.  Here we only need "does not sum".
    famb = [r for r in rows if r["unamortized_residual_minor"] != 0]
    clean = [r for r in rows if r["unamortized_residual_minor"] == 0]
    report["famB_count"] = len(famb)
    report["clean_count"] = len(clean)
    report["famB_distinct_principals_minor"] = sorted(
        {r["input_disbursement_minor"] for r in famb})
    report["famB_partial_cells"] = [
        {k: r[k] for k in ("id", "disbursed_minor", "amortized_minor",
                           "unamortized_residual_minor", "nonzero_principal_rows")}
        for r in famb if r["amortized_minor"] != 0
    ]
    report["famB_sum_to_zero_count"] = sum(1 for r in famb if r["amortized_minor"] == 0)

    # --- odd/even split of family B --------------------------------------
    report["famB_all_odd_principals"] = all(
        r["input_disbursement_minor"] % 2 == 1 for r in famb)
    report["clean_cells_with_odd_principal"] = sum(
        1 for r in clean if r["input_disbursement_minor"] % 2 == 1)

    # --- band structure at B = 1, re-derived -----------------------------
    b1 = sorted([r for r in rows if r["input_disbursement_minor"] == 1],
                key=lambda r: r["n_asked"])
    report["B1_cell_count"] = len(b1)
    report["B1_famB_count"] = sum(1 for r in b1 if r["unamortized_residual_minor"] != 0)
    report["B1_clean_count"] = sum(1 for r in b1 if r["unamortized_residual_minor"] == 0)
    report["B1_clean_terms"] = [r["n_asked"] for r in b1
                                if r["unamortized_residual_minor"] == 0]
    report["B1_famB_terms"] = [r["n_asked"] for r in b1
                               if r["unamortized_residual_minor"] != 0]

    # --- exact-arithmetic tie description (Fraction, never float) --------
    # r = annualRate/100/12 as an exact Fraction; B*r in minor units.
    tie = {"famB_all_half_integer": True,
           "famB_intermediate_total_eq_floor_Br": 0, "famB_checked_for_floor": 0,
           "nonfamB_odd_B": 0, "checked": 0}
    for r in rows:
        rate = Fraction(r["rate"])  # e.g. '600.0'
        mrate = rate / 100 / 12
        Br = Fraction(r["input_disbursement_minor"]) * mrate
        half_int = (2 * Br).denominator == 1 and int(2 * Br) % 2 == 1
        if r["unamortized_residual_minor"] != 0:
            tie["checked"] += 1
            if not half_int:
                tie["famB_all_half_integer"] = False
            # every INTERMEDIATE row's `total` == floor(B*r)?  Fraction floor via
            # integer division on numerator/denominator -- exact, never a float.
            cap = caps[r["id"]]
            inter = [p for p in cap["observed"]["periods"]
                     if p.get("type") == "REPAYMENT"][:-1]
            tot = sorted({minor(p["total"]) for p in inter})
            tie["famB_checked_for_floor"] += 1
            if tot == [Br.numerator // Br.denominator]:
                tie["famB_intermediate_total_eq_floor_Br"] += 1
        else:
            if r["input_disbursement_minor"] % 2 == 1:
                tie["nonfamB_odd_B"] += 1
    report["tie_description"] = tie

    print(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main()
