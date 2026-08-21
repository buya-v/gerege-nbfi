#!/usr/bin/env python3
"""T170 — re-derivation of every figure T170 carries into gates.md, BY EXTRACTION
from the committed RAW .gz captures (never from any worker's analysis layer, never
from a plain .json extract — G-8 STANDING RULE 5, P-32).

NO FLOATING POINT ANYWHERE (P-25). Money is parsed by splitting the oracle's
BigDecimal.toPlainString() on '.' and padding to dp; every residual is an integer
subtraction in minor units.

Inputs (all committed):
  .softhouse/capture/t117-familyb/out/capture-t117-raw.json.gz
  .softhouse/capture/t117-familyb/out/capture-t117p2-raw.json.gz
  .softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz
  .softhouse/capture/t83-nonamortizing/out/capture-t83-raw.json      (plain; T83 has no .gz)
  .softhouse/reviews/T84-evidence/out/capture-t84-raw.json.gz
  .softhouse/reviews/T84-evidence/out/capture-t84b-raw.json.gz
  .softhouse/capture/t100-g8-rescope/out/capture-t100-raw.json       (plain; T100 has no .gz)

Output: out/extract-t170.json  (+ a human transcript on stdout)
"""
import gzip, json, hashlib, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

SOURCES = [
    ("t117",   ".softhouse/capture/t117-familyb/out/capture-t117-raw.json.gz"),
    ("t117p2", ".softhouse/capture/t117-familyb/out/capture-t117p2-raw.json.gz"),
    ("t159",   ".softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz"),
    ("t83",    ".softhouse/capture/t83-nonamortizing/out/capture-t83-raw.json"),
    ("t84",    ".softhouse/reviews/T84-evidence/out/capture-t84-raw.json.gz"),
    ("t84b",   ".softhouse/reviews/T84-evidence/out/capture-t84b-raw.json.gz"),
    ("t100",   ".softhouse/capture/t100-g8-rescope/out/capture-t100-raw.json"),
]


def minor(s, dp):
    """'15010.01', dp=2 -> 1501001 (int). Refuses anything that is not a plain decimal."""
    if s is None:
        return None
    s = str(s).strip()
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    if "." in s:
        whole, frac = s.split(".", 1)
    else:
        whole, frac = s, ""
    if not whole.isdigit() or (frac and not frac.isdigit()):
        raise ValueError("not a plain decimal: %r" % s)
    if len(frac) > dp:
        raise ValueError("more fraction digits than dp: %r dp=%d" % (s, dp))
    frac = frac.ljust(dp, "0")
    v = int(whole + frac) if dp else int(whole)
    return -v if neg else v


def load(path):
    full = os.path.join(ROOT, path)
    raw = open(full, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    if path.endswith(".gz"):
        doc = json.loads(gzip.decompress(raw))
    else:
        doc = json.loads(raw)
    canon = hashlib.sha256(
        json.dumps(doc["captures"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return doc, sha, canon


def analyse(case, dp_default=2):
    """Return a dict of integer-minor-unit facts, or an error record."""
    cid = case.get("id")
    inp = case.get("inputs") or {}
    obs = case.get("observed")
    dp = inp.get("currencyDecimalPlaces", dp_default)
    rec = {
        "id": cid,
        "rate": inp.get("annualNominalInterestRate"),
        "n": inp.get("numberOfRepayments"),
        "dp": dp,
        "disbursed_minor": minor(inp.get("disbursementAmount"), dp)
        if inp.get("disbursementAmount") is not None else None,
    }
    if obs is None:
        rec["outcome"] = "ERRORED"
        for k in ("error", "errorClass", "errorMessage", "errorStackTop",
                  "errorStackDepthTotal", "outcome"):
            if k in case and k != "outcome":
                rec[k] = case[k]
        rec["raw_keys"] = sorted(case.keys())
        return rec
    periods = obs.get("periods") or []
    rep = [p for p in periods if p.get("type") == "REPAYMENT"]
    amortized = sum(minor(p.get("principal"), dp) for p in rep)
    balances = sorted({p.get("balance") for p in rep if p.get("balance") is not None})
    nz = [p.get("periodNumber") for p in rep if minor(p.get("principal"), dp) != 0]
    rec.update({
        "outcome": "OBSERVED",
        "repayment_rows": len(rep),
        "amortized_minor": amortized,
        "residual_minor": (rec["disbursed_minor"] - amortized)
        if rec["disbursed_minor"] is not None else None,
        "totalPrincipalAmount": obs.get("totalPrincipalAmount"),
        "totalInterestAmount": obs.get("totalInterestAmount"),
        "totalInterestAmount_minor": minor(obs.get("totalInterestAmount"), dp)
        if obs.get("totalInterestAmount") is not None else None,
        "totalOutstandingAmount": obs.get("totalOutstandingAmount"),
        "distinct_repayment_balances": balances,
        "nonzero_principal_rows": nz,
        "final_balance_minor": minor(rep[-1].get("balance"), dp) if rep else None,
        "final_interest": rep[-1].get("interest") if rep else None,
        "first_dueDate": rep[0].get("dueDate") if rep else None,
        "last_dueDate": rep[-1].get("dueDate") if rep else None,
        "zero_principal_rows": sum(1 for p in rep if minor(p.get("principal"), dp) == 0),
    })
    # family classification, exactly the committed discriminator: does the REPAYMENT
    # principal column sum to the disbursed amount?
    if rec["disbursed_minor"] is None:
        rec["family"] = "?"
    elif amortized == rec["disbursed_minor"]:
        rec["family"] = "A_or_clean"
        rec["fails"] = rec["final_balance_minor"] != 0
    else:
        rec["family"] = "B"
        rec["fails"] = True
        rec["partial"] = amortized != 0
    return rec


def main():
    out = {"sources": {}, "cells": {}, "summary": {}}
    allrecs = {}
    for tag, path in SOURCES:
        doc, sha, canon = load(path)
        caps = doc["captures"]
        recs = [analyse(c) for c in caps]
        allrecs[tag] = recs
        out["sources"][tag] = {
            "path": path,
            "file_sha256": sha,
            "canonical_over_captures_sha256": canon,
            "canonicalisation_recipe":
                "json.dumps(doc['captures'], sort_keys=True, separators=(',',':')), UTF-8",
            "cases": len(caps),
            "errored": sum(1 for r in recs if r["outcome"] == "ERRORED"),
            "observed": sum(1 for r in recs if r["outcome"] == "OBSERVED"),
        }

    def rec(tag, cid):
        for r in allrecs[tag]:
            if r["id"] == cid:
                return r
        raise KeyError("%s not in %s" % (cid, tag))

    # ---- the cells T170 quotes into gates.md ----
    named = [
        ("t159",   "T159-R600p0-N3000-B1001"),   # the headline, MNT 10.01 at n=3000
        ("t159",   "T159-R600p0-N2000-B999"),    # the fourth PARTIAL cell
        ("t159",   "T159-R600p0-N3000-B10001"),  # the DISPUTED cell (T177) — not the headline
        ("t159",   "T159-R600p0-N2000-B10001"),  # T159's detonation #1
        ("t159",   "T159-R600p0-N3000-B100001"), # T159's detonation #2
        ("t117p2", "T117P2-R600p0-N1000-B501"),  # T117's headline, MNT 5.01 at n=1000
        ("t117p2", "T117P2-R600p0-N108-B11"),
        ("t117p2", "T117P2-R600p0-N121-B11"),
        ("t117p2", "T117P2-R600p0-N150-B11"),
    ]
    for tag, cid in named:
        out["cells"]["%s/%s" % (tag, cid)] = rec(tag, cid)

    # ---- corpus-level counts, per source and unioned ----
    def famB(tag):
        return [r for r in allrecs[tag] if r.get("family") == "B"]

    newB = {}
    for tag in ("t117", "t117p2", "t159"):
        b = famB(tag)
        newB[tag] = {
            "family_b_cells": len(b),
            "partial_cells": sorted(r["id"] for r in b if r.get("partial")),
            "distinct_principals_minor": sorted({r["disbursed_minor"] for r in b}),
            "distinct_n": sorted({r["n"] for r in b}),
            "max_residual_minor": max((r["residual_minor"] for r in b), default=None),
            "max_n": max((r["n"] for r in b), default=None),
        }
    out["summary"]["new_captures_family_b"] = newB

    union_new = famB("t117") + famB("t117p2") + famB("t159")
    out["summary"]["union_t117_t159"] = {
        "family_b_cells": len(union_new),
        "distinct_principals_minor": sorted({r["disbursed_minor"] for r in union_new}),
        "all_principals_odd": all(r["disbursed_minor"] % 2 == 1 for r in union_new),
        "max_residual_minor": max(r["residual_minor"] for r in union_new),
        "max_residual_cell": max(union_new, key=lambda r: r["residual_minor"])["id"],
        "max_n": max(r["n"] for r in union_new),
        "min_n": min(r["n"] for r in union_new),
        "partial_cells": sorted(r["id"] for r in union_new if r.get("partial")),
        "rates": sorted({r["rate"] for r in union_new}),
    }

    old_union = famB("t83") + famB("t84") + famB("t84b") + famB("t100")
    out["summary"]["record_four_captures_family_b"] = {
        "family_b_cells": len(old_union),
        "distinct_principals_minor": sorted({r["disbursed_minor"] for r in old_union}),
        "distinct_n": sorted({r["n"] for r in old_union}),
        "rates": sorted({r["rate"] for r in old_union}),
    }
    out["summary"]["grand_union_family_b_cells"] = len(old_union) + len(union_new)

    # errored cells, everywhere
    err = []
    for tag in allrecs:
        for r in allrecs[tag]:
            if r["outcome"] == "ERRORED":
                err.append({"source": tag, **r})
    out["summary"]["errored_cells"] = err

    # P-40: count what was skipped
    skipped = []
    for tag in allrecs:
        for r in allrecs[tag]:
            if r["outcome"] == "OBSERVED" and r.get("family") == "?":
                skipped.append({"source": tag, "id": r["id"],
                                "why": "no disbursementAmount in inputs"})
    out["summary"]["skipped_unclassifiable"] = skipped
    out["summary"]["total_cases_read"] = sum(v["cases"] for v in out["sources"].values())

    dest = os.path.join(ROOT, ".softhouse/capture/t170-g8-rebuild/out/extract-t170.json")
    with open(dest, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    json.dump(out["summary"], sys.stdout, indent=1, sort_keys=True)
    print()
    for k, v in out["cells"].items():
        print("----", k)
        print(json.dumps(v, sort_keys=True, indent=1))


if __name__ == "__main__":
    main()
