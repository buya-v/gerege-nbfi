#!/usr/bin/env python3
"""T159 — integer-minor-unit census + prediction scoring for the T159 capture,
plus BYTE-IDENTITY comparison of every T159 cell against its T117 twin.

MONEY DISCIPLINE (P-25): every monetary quantity is an INTEGER count of minor
units, obtained by splitting the oracle's `BigDecimal.toPlainString()` JSON string
on '.' and padding to the currency's decimal places. Residuals are decided by
INTEGER SUBTRACTION. `json.load` uses parse_float=Decimal so a numeric money
literal, if one ever appeared, could not become a binary double. No float is
constructed anywhere in this file.

The BYTE-IDENTITY leg is the point of the re-ask: a T159 cell and its T117 twin
differ only in the case id, the purpose string and the tenant id, so their
`observed` blocks must be character-identical after canonical serialisation. If
they are not, T117's sweep is not reproducible and nothing in it should be
believed.
"""
import gzip
import json
import sys
from decimal import Decimal
from fractions import Fraction

DP = 2


def minor(s, dp=DP):
    if not isinstance(s, str):
        raise TypeError("money must arrive as a JSON string, got %r" % (s,))
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    whole, _, frac = s.partition(".")
    if len(frac) > dp:
        raise ValueError("more fractional digits than dp: %r" % s)
    frac = frac + "0" * (dp - len(frac))
    v = int(whole or "0") * (10 ** dp) + int(frac or "0")
    return -v if neg else v


def load(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as fh:
        return json.load(fh, parse_float=Decimal)


def census(cap):
    o = cap.get("observed")
    i = cap["inputs"]
    base = {
        "id": cap["id"],
        "n": i["numberOfRepayments"],
        "rate": i["annualNominalInterestRate"],
        "B_minor": minor(i["disbursementAmount"]),
    }
    if o is None:
        base.update({"errored": True, "error": cap.get("error"),
                     "errorStackTop0": (cap.get("errorStackTop") or [None])[0],
                     "family": "ERRORED"})
        return base
    periods = o["periods"]
    disb = [p for p in periods if p["type"] == "DISBURSEMENT"]
    reps = [p for p in periods if p["type"] == "REPAYMENT"]
    disbursed = sum(minor(p["principal"]) for p in disb)
    amortized = sum(minor(p["principal"]) for p in reps)
    residual = disbursed - amortized
    base.update({
        "errored": False,
        "repayment_rows": len(reps),
        "disbursed_minor": disbursed,
        "amortized_minor": amortized,
        "unamortized_residual_minor": residual,
        "totalPrincipalAmount_minor": minor(o["totalPrincipalAmount"]),
        "totalInterestAmount_minor": minor(o["totalInterestAmount"]),
        "final_balance_minor": minor(reps[-1]["balance"]),
        "nonzero_principal_rows": len([p for p in reps if minor(p["principal"]) != 0]),
        "intermediate_total_minor_distinct": sorted({minor(p["total"]) for p in reps[:-1]}),
        "last_row_interest": reps[-1]["interest"],
        "family": ("B" if residual != 0 else "clean"),
    })
    return base


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def main():
    t159p, pred_p = sys.argv[1], sys.argv[2]
    t117_paths = sys.argv[3:]

    doc = load(t159p)
    caps = doc["captures"]
    pred = json.load(open(pred_p), parse_float=Decimal)["cases"]

    twins = {}
    for p in t117_paths:
        for c in load(p)["captures"]:
            i = c["inputs"]
            twins[(i["annualNominalInterestRate"], i["numberOfRepayments"],
                   minor(i["disbursementAmount"]))] = c

    rows, scored, ident = [], [], []
    for c in caps:
        if c["id"].startswith("P-CAL"):
            continue
        r = census(c)
        rows.append(r)

        # --- prediction scoring (P-9 control) ---------------------------------
        p = pred[c["id"]]
        got_famB = (r["family"] == "B")
        scored.append({"id": c["id"], "leg": p["leg"], "n": r["n"], "B_minor": r["B_minor"],
                       "predictedFamilyB": p["predictedFamily"] == "B",
                       "observedFamily": r["family"],
                       "agrees": (r["family"] != "ERRORED") and (got_famB == (p["predictedFamily"] == "B")),
                       "confidence": p["confidence"]})

        # --- byte-identity against the T117 twin ------------------------------
        key = (r["rate"], r["n"], r["B_minor"])
        t = twins.get(key)
        if t is not None and c.get("observed") is not None:
            same = canon(c["observed"]) == canon(t["observed"])
            in_diffs = [k for k in set(list(c["inputs"]) + list(t["inputs"]))
                        if k not in ("tenantId", "tenantRoundingModeValue")
                        and c["inputs"].get(k) != t["inputs"].get(k)]
            ident.append({"t159": c["id"], "t117": t["id"],
                          "observed_byte_identical": same,
                          "input_diffs_excluding_tenant_id": in_diffs,
                          "t159_tenantId": c["inputs"]["tenantId"],
                          "t117_tenantId": t["inputs"]["tenantId"]})

    famB = [r for r in rows if r["family"] == "B"]
    errored = [r for r in rows if r["family"] == "ERRORED"]

    # exact-arithmetic description; Fraction only, never float
    tie = []
    for r in famB:
        Br = Fraction(r["B_minor"]) * Fraction(r["rate"]) / 100 / 12
        tie.append({"id": r["id"], "B_minor": r["B_minor"],
                    "2Br_is_odd_integer": (2 * Br).denominator == 1 and int(2 * Br) % 2 == 1,
                    "floor_Br": Br.numerator // Br.denominator,
                    "intermediate_total_eq_floor_Br":
                        r["intermediate_total_minor_distinct"] == [Br.numerator // Br.denominator]})

    out = {
        "asked": len(pred),
        "probe_cases_in_capture": len(rows),
        "observed": len(rows) - len(errored),
        "errored": len(errored),
        "errored_detail": [{k: r[k] for k in ("id", "n", "B_minor", "error", "errorStackTop0")}
                           for r in errored],
        "family_B_count": len(famB),
        "clean_count": len(rows) - len(famB) - len(errored),
        "max_residual_minor": max([r["unamortized_residual_minor"] for r in rows
                                   if r["family"] != "ERRORED"] or [0]),
        "max_residual_cell": max([r for r in rows if r["family"] != "ERRORED"],
                                 key=lambda r: r["unamortized_residual_minor"])["id"],
        "famB_distinct_principals_minor": sorted({r["B_minor"] for r in famB}),
        "predictions": {
            "agree": sum(1 for s in scored if s["agrees"]),
            "disagree": sum(1 for s in scored if not s["agrees"] and s["observedFamily"] != "ERRORED"),
            "unscorable_errored": sum(1 for s in scored if s["observedFamily"] == "ERRORED"),
            "detail": scored,
        },
        "byte_identity": {
            "compared": len(ident),
            "identical": sum(1 for x in ident if x["observed_byte_identical"]),
            "differing": [x for x in ident if not x["observed_byte_identical"]],
            "detail": ident,
        },
        "tie_description": tie,
        "rows": sorted(rows, key=lambda r: (r["B_minor"], r["n"])),
    }
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
