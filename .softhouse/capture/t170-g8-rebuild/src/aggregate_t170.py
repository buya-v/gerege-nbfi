#!/usr/bin/env python3
"""T170 — aggregate shape facts over the family-B cells, in integer minor units only.

Reads the same RAW .gz captures as extract_t170.py and answers exactly the questions
T170 needs in order to rewrite a discriminator row without over-claiming:

  * how many family-B cells are FULL (amortized == 0) and how many are PARTIAL
  * distinct SHAPES (rate, n, principal) as opposed to distinct measurements
  * whether residual == the final row's balance on every cell
  * the cardinality of the balance column on full vs partial cells
  * the final row's interest, full vs partial
  * totalOutstandingAmount on every family-B cell

Output: out/aggregate-t170.json
"""
import gzip, json, os, sys, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_t170 import SOURCES, minor, analyse, load  # noqa: E402


def main():
    recs = {}
    for tag, path in SOURCES:
        doc, _, _ = load(path)
        recs[tag] = [(analyse(c), c) for c in doc["captures"]]

    def famB(tags):
        out = []
        for t in tags:
            for r, c in recs[t]:
                if r.get("family") == "B":
                    out.append((t, r, c))
        return out

    new = famB(["t117", "t117p2", "t159"])
    old = famB(["t83", "t84", "t84b", "t100"])
    allB = new + old

    def shape(r):
        return (r["rate"], r["n"], r["disbursed_minor"])

    res = {
        "new_cells": len(new),
        "old_cells": len(old),
        "all_cells": len(allB),
        "new_full": sum(1 for _, r, _ in new if r["amortized_minor"] == 0),
        "new_partial": sum(1 for _, r, _ in new if r["amortized_minor"] != 0),
        "old_full": sum(1 for _, r, _ in old if r["amortized_minor"] == 0),
        "old_partial": sum(1 for _, r, _ in old if r["amortized_minor"] != 0),
        "distinct_shapes_new": len({shape(r) for _, r, _ in new}),
        "distinct_shapes_all": len({shape(r) for _, r, _ in allB}),
        "partial_shapes": sorted({shape(r) for _, r, _ in allB if r["amortized_minor"] != 0}),
        "partial_measurements": sorted(r["id"] for _, r, _ in allB if r["amortized_minor"] != 0),
        "residual_equals_final_balance_all": all(
            r["residual_minor"] == r["final_balance_minor"] for _, r, _ in allB),
        "residual_ne_final_balance": [r["id"] for _, r, _ in allB
                                      if r["residual_minor"] != r["final_balance_minor"]],
        "totalOutstandingAmount_values": sorted({str(r["totalOutstandingAmount"]) for _, r, _ in allB}),
        "totalPrincipalAmount_values_full": sorted(
            {str(r["totalPrincipalAmount"]) for _, r, _ in allB if r["amortized_minor"] == 0}),
        "totalPrincipalAmount_values_partial": sorted(
            {str(r["totalPrincipalAmount"]) for _, r, _ in allB if r["amortized_minor"] != 0}),
        "balance_column_cardinality_full": sorted(
            {len(r["distinct_repayment_balances"]) for _, r, _ in allB if r["amortized_minor"] == 0}),
        "balance_column_cardinality_partial": sorted(
            {len(r["distinct_repayment_balances"]) for _, r, _ in allB if r["amortized_minor"] != 0}),
        "nonzero_principal_row_count_full": sorted(
            {len(r["nonzero_principal_rows"]) for _, r, _ in allB if r["amortized_minor"] == 0}),
        "nonzero_principal_row_count_partial": sorted(
            {len(r["nonzero_principal_rows"]) for _, r, _ in allB if r["amortized_minor"] != 0}),
        "nonzero_principal_row_is_last_partial": all(
            r["nonzero_principal_rows"] == [r["repayment_rows"]]
            for _, r, _ in allB if r["amortized_minor"] != 0),
        "rates": sorted({r["rate"] for _, r, _ in allB}),
        "n_min": min(r["n"] for _, r, _ in allB),
        "n_max": max(r["n"] for _, r, _ in allB),
        "principal_min_minor": min(r["disbursed_minor"] for _, r, _ in allB),
        "principal_max_minor": max(r["disbursed_minor"] for _, r, _ in allB),
        "principals_all_odd": all(r["disbursed_minor"] % 2 == 1 for _, r, _ in allB),
    }

    # last row's interest, by group
    li_full = collections.Counter(str(r["final_interest"]) for _, r, _ in allB
                                  if r["amortized_minor"] == 0)
    li_part = {r["id"]: str(r["final_interest"]) for _, r, _ in allB if r["amortized_minor"] != 0}
    res["final_interest_full_distinct_count"] = len(li_full)
    res["final_interest_full_top"] = li_full.most_common(8)
    res["final_interest_partial"] = li_part
    # on B = 1 minor cells only (the shape the record's sentence was written over)
    b1 = [r for _, r, _ in allB if r["disbursed_minor"] == 1]
    res["b1_cells"] = len(b1)
    res["b1_final_interest_values"] = sorted({str(r["final_interest"]) for r in b1})
    res["b1_totalPrincipalAmount_values"] = sorted({str(r["totalPrincipalAmount"]) for r in b1})

    # the family-A side of the discriminator, over the four record captures, so the
    # rebuilt table's family-A column stays checked too
    famA = []
    for t in ("t83", "t84", "t84b", "t100"):
        for r, c in recs[t]:
            if r.get("family") == "A_or_clean" and r.get("fails"):
                famA.append(r)
    res["family_a_failing_cells_record"] = len(famA)
    res["family_a_nonzero_principal_row_counts"] = sorted({len(r["nonzero_principal_rows"]) for r in famA})
    res["family_a_nonzero_row_is_last"] = all(
        r["nonzero_principal_rows"] == [r["repayment_rows"]] for r in famA)
    res["family_a_balance_cardinality"] = sorted({len(r["distinct_repayment_balances"]) for r in famA})
    res["family_a_final_interest_values"] = sorted({str(r["final_interest"]) for r in famA})[:6]
    res["family_a_max_residual_minor"] = max(r["residual_minor"] for r in famA)
    res["family_a_max_residual_cell"] = max(famA, key=lambda r: r["residual_minor"])["id"]
    res["family_a_max_final_balance_minor"] = max(r["final_balance_minor"] for r in famA)
    res["family_a_max_final_balance_cell"] = max(famA, key=lambda r: r["final_balance_minor"])["id"]
    res["family_a_rates"] = sorted({r["rate"] for r in famA})
    res["family_a_n_max"] = max(r["n"] for r in famA)

    dest = os.path.join(ROOT, ".softhouse/capture/t170-g8-rebuild/out/aggregate-t170.json")
    with open(dest, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print(json.dumps(res, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
