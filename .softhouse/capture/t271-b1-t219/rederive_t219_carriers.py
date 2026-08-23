#!/usr/bin/env python3
"""T271 / B-1 -- re-derive every P2 carrier in `t219-g8-residual` FROM THE RAW CAPTURE, in integer
minor units, and establish what `T219-R600p0-N103-B1` actually is.

WHY THIS EXISTS
    `.softhouse/capture/t219-g8-residual/out/classify-t219.json` carries FOUR pairs in which a row
    records an affirmative `verdict` over a `P2_*` predicate it recorded as `false`. That is
    T259's shape (P-45 moved one layer out: the guard RAN, wrote its answer down, and the summary
    line above it said the opposite). T259 predicted the same ruling would apply here. It does not
    apply cleanly, and this file measures why.

WHAT IT READS
    THE RAW GZ CAPTURE, not the classifier's own derived fields. Every quantity below is summed
    from `observed.periods[]` and cross-checked against the capture header totals, so a defect in
    `classify_t219.py`'s derivation cannot hide inside a re-derivation that trusts it. The
    committed `classify-t219.json` is then read SECOND, only to assert my numbers reproduce its
    recorded ones.

NO FLOATING POINT, INCLUDING INTERMEDIATES (project non-negotiable; T145).
    * every JSON read uses `parse_float=Decimal`, so no float ever enters the process;
    * `minor()` multiplies a `Decimal` by 100, asserts integrality, and returns `int`;
    * `require_int()` asserts `type(v) is int` on every quantity that reaches the arithmetic;
    * every comparison below is int-vs-int.

THE THREE FORMS OF THE THIRD CONJUNCT, kept apart on purpose
    REGISTERED    interest == n*E + B                        (as recorded in T229's PREDICTION.md)
    CORRECTED     interest == n*E + B - principalRepaid      (T259's ruling, adopted d20836e)
    UNCONDITIONAL interest == totalRepayment - principalRepaid   (totalRepayment MEASURED)
    plus the STRUCTURE test that `totalRepayment == n*E + B` silently presumes:
    every repayment row except the last totals exactly E, and the last totals exactly E + B.

EXIT CODES, never conflated (P-80):
    0  every re-derivation reproduced the committed record and every printed conclusion held
    1  a REAL measured negative: a re-derived figure contradicts the committed record
    2  usage, IO or parse error. NEVER used to report an absence.

PROBE LINE.  The last line is always
    T271-REDERIVE: <STATE> carriers=.. reproduced=.. agreeREG=.. agreeCORR=.. agreeUNCOND=..
                   structureHolds=.. contradictions=..
Test its PRESENCE before its VALUE (P-83).
"""
import gzip
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
T219 = (HERE / ".." / "t219-g8-residual").resolve()
PROBE = "T271-REDERIVE:"


class RuleError(Exception):
    """Anything that is an ERROR (exit 2) rather than a measured negative (exit 1)."""


def load_json(path: Path):
    return json.loads(path.read_text(), parse_float=Decimal)


def load_gz(path: Path):
    with gzip.open(path, "rt") as fh:
        return json.loads(fh.read(), parse_float=Decimal)


def minor(v) -> int:
    """Decimal-only conversion to integer minor units. Refuses anything non-integral."""
    if isinstance(v, float):
        raise RuleError(f"float reached minor(): {v!r} -- parse_float=Decimal was not applied")
    d = Decimal(str(v)) * 100
    if d != d.to_integral_value():
        raise RuleError(f"not an integral number of minor units: {v!r}")
    return int(d)


def require_int(name: str, v) -> int:
    if type(v) is not int:
        raise RuleError(f"{name} is {type(v).__name__}, not int: {v!r}")
    return v


def rederive(cap) -> dict:
    """Sum the schedule from the RAW periods. Nothing here reads classify-t219.json."""
    o = cap["observed"]
    reps = [r for r in o["periods"] if r["type"] == "REPAYMENT"]
    if not reps:
        raise RuleError(f"{cap['id']}: no REPAYMENT rows in the raw capture")
    totals = [minor(r["total"]) for r in reps]
    prins = [minor(r["principal"]) for r in reps]
    ints = [minor(r["interest"]) for r in reps]
    d = {
        "rows": len(reps),
        "sumTotalMinor": sum(totals),
        "sumPrincipalMinor": sum(prins),
        "sumInterestMinor": sum(ints),
        "row1TotalMinor": totals[0],
        "row1InterestMinor": ints[0],
        "lastTotalMinor": totals[-1],
        "hdrPrincipalMinor": minor(o["totalPrincipalAmount"]),
        "hdrInterestMinor": minor(o["totalInterestAmount"]),
        "hdrRepaymentMinor": minor(o["totalRepaymentAmount"]),
        "hdrDisbursedMinor": minor(o["totalDisbursedAmount"]),
        "principalRowCount": sum(1 for p in prins if p != 0),
        "principalRowIndex1Based": next((i for i, p in enumerate(prins, 1) if p != 0), 0),
        "distinctTotalsExLast": sorted(set(totals[:-1])),
    }
    for k, v in d.items():
        if k != "distinctTotalsExLast":
            require_int(k, v)
    d["emiDifferenceMinor"] = d["lastTotalMinor"] - d["row1TotalMinor"]
    return d


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        print(f"ERROR: takes no arguments; got {argv!r}", file=sys.stderr)
        return 2

    raw_path = T219 / "out" / "capture-t219-raw.json.gz"
    pred_path = T219 / "prediction.json"
    cls_path = T219 / "out" / "classify-t219.json"
    for p in (raw_path, pred_path, cls_path):
        if not p.exists():
            print(f"ERROR: missing input: {p}", file=sys.stderr)
            return 2

    try:
        raw = load_gz(raw_path)
        preds = {p["id"]: p for p in load_json(pred_path)}
        cls = load_json(cls_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print("T271 -- re-derivation of every P2 carrier in t219-g8-residual, from the RAW capture")
    print("=" * 100)
    print(f"  raw      : {raw_path.name}")
    print(f"  moneyHelperPrecision recorded in the capture : {raw.get('moneyHelperPrecision')!r}")
    print(f"  classify : {cls_path.name}  (read SECOND, only to check reproduction)")
    print()

    recorded = {r["id"]: r for r in cls["cells"]}
    carriers = [r for r in cls["cells"] if "P2_totalInterestEqualsNEplusB" in r]

    contradictions = []
    agree_reg = agree_corr = agree_uncond = struct_holds = reproduced = 0
    rows_out = []

    try:
        for cell in carriers:
            cid = cell["id"]
            cap = next((c for c in raw["captures"] if c["id"] == cid), None)
            if cap is None:
                raise RuleError(f"{cid}: carrier is in classify-t219.json but not in the raw capture")
            p = preds[cid]
            d = rederive(cap)

            n = require_int("n", p["n"])
            b = require_int("bMinor", p["bMinor"])
            e_obs = d["row1TotalMinor"]
            interest = d["sumInterestMinor"]
            principal = d["sumPrincipalMinor"]
            total_rep = d["sumTotalMinor"]

            # (a) do my raw sums reproduce the capture's own header totals?
            hdr_ok = (interest == d["hdrInterestMinor"]
                      and principal == d["hdrPrincipalMinor"]
                      and total_rep == d["hdrRepaymentMinor"])
            # (b) do my raw sums reproduce what classify_t219.py recorded?
            rec = recorded[cid]
            rec_ok = (rec["observedRepaymentRows"] == d["rows"]
                      and rec["observedPrincipalMinor"] == principal
                      and rec["observedInterestMinor"] == interest
                      and rec["observedRow1TotalMinor"] == e_obs
                      and rec["observedLastTotalMinor"] == d["lastTotalMinor"]
                      and rec["observedEmiDifferenceMinor"] == d["emiDifferenceMinor"])
            if hdr_ok and rec_ok:
                reproduced += 1
            else:
                contradictions.append(f"{cid}: header-sum ok={hdr_ok} recorded-field ok={rec_ok}")

            ne_plus_b = n * e_obs + b
            reg = (interest == ne_plus_b)
            corr = (interest == ne_plus_b - principal)
            uncond = (interest == total_rep - principal)
            # the row structure `totalRepayment == n*E + B` presumes:
            struct = (d["distinctTotalsExLast"] == [e_obs]
                      and d["lastTotalMinor"] == e_obs + b)
            emi_diff_eq_b = (d["emiDifferenceMinor"] == b)

            agree_reg += 1 if reg else 0
            agree_corr += 1 if corr else 0
            agree_uncond += 1 if uncond else 0
            struct_holds += 1 if struct else 0

            # the committed record must agree with my re-derivation of its OWN predicates
            if rec["P2_totalInterestEqualsNEplusB"] is not reg:
                contradictions.append(
                    f"{cid}: recorded P2_totalInterestEqualsNEplusB="
                    f"{rec['P2_totalInterestEqualsNEplusB']} but re-derives {reg}")
            if rec["P2_emiDifferenceEqualsB"] is not emi_diff_eq_b:
                contradictions.append(
                    f"{cid}: recorded P2_emiDifferenceEqualsB="
                    f"{rec['P2_emiDifferenceEqualsB']} but re-derives {emi_diff_eq_b}")
            # The structure test must EXPLAIN what it is a precondition FOR, and it is a
            # precondition for the REPAYMENT identity, not the INTEREST one.
            #   structure  =>  totalRepayment == (n-1)*E + (E + B) == n*E + B
            # and therefore, since interest == totalRepayment - principal unconditionally,
            #   structure  =>  interest == n*E + B - principal   (the CORRECTED form)
            # The REGISTERED form additionally needs principal == 0, which is a fact about the
            # cell, not about the structure. My first draft asserted `structure => REGISTERED`
            # and this check fired on B4499 and B3001 -- the instrument caught the same
            # repayment-vs-interest conflation the registered predicate is made of. Kept as the
            # sharper assertion rather than deleted.
            if struct and total_rep != ne_plus_b:
                contradictions.append(
                    f"{cid}: EMI-plus-balloon structure holds yet totalRepayment {total_rep} "
                    f"!= n*E + B {ne_plus_b} -- the stated precondition does not explain the "
                    "outcome")
            if struct and not corr:
                contradictions.append(
                    f"{cid}: EMI-plus-balloon structure holds yet the CORRECTED form fails")

            rows_out.append({
                "id": cid, "n": n, "E_obs": e_obs, "B": b, "P_rep": principal,
                "totalRep": total_rep, "nE_B": ne_plus_b, "nE_B_minus_P": ne_plus_b - principal,
                "interest": interest, "verdict": rec["verdict"],
                "REG": reg, "CORR": corr, "UNCOND": uncond, "STRUCT": struct,
                "emiDiffEqB": emi_diff_eq_b, "emiDiff": d["emiDifferenceMinor"],
                "prinRows": d["principalRowCount"], "prinAt": d["principalRowIndex1Based"],
                "distinctExLast": d["distinctTotalsExLast"][:6],
                "outcome": rec["observedOutcome"], "predOutcome": rec["predictedOutcome"],
                "predInterest": p["predictedTotalInterestMinor"],
            })
    except RuleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    hdr = (f"{'id':<26}{'n':>6}{'E':>7}{'B':>7}{'P':>7}{'totRep':>10}{'nE+B':>10}"
           f"{'nE+B-P':>10}{'interest':>10}  {'REG':<6}{'CORR':<6}{'UNCND':<6}{'STRUCT':<7}"
           f"{'emiD=B':<8}{'verdict':<14}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows_out:
        print(f"{r['id']:<26}{r['n']:>6}{r['E_obs']:>7}{r['B']:>7}{r['P_rep']:>7}"
              f"{r['totalRep']:>10}{r['nE_B']:>10}{r['nE_B_minus_P']:>10}{r['interest']:>10}  "
              f"{str(r['REG']):<6}{str(r['CORR']):<6}{str(r['UNCOND']):<6}{str(r['STRUCT']):<7}"
              f"{str(r['emiDiffEqB']):<8}{r['verdict']:<14}")
    print()
    print(f"  carriers                                  : {len(carriers)}")
    print(f"  re-derived == committed record            : {reproduced} of {len(carriers)}")
    print(f"  REGISTERED   interest == n*E + B          : {agree_reg} of {len(carriers)}")
    print(f"  CORRECTED    interest == n*E + B - P      : {agree_corr} of {len(carriers)}"
          "        <<< T259's ruling")
    print(f"  UNCONDITIONAL interest == totalRep - P    : {agree_uncond} of {len(carriers)}"
          "        <<< totalRep MEASURED, not modelled")
    print(f"  EMI-plus-balloon STRUCTURE holds          : {struct_holds} of {len(carriers)}")
    print()

    print("  THE ROW THAT FALSIFIES T259's EXPECTATION")
    print("  " + "-" * 96)
    odd = [r for r in rows_out if not r["CORR"]]
    for r in odd:
        print(f"  {r['id']}")
        print(f"    registered outcome  : {r['predOutcome']}     observed: {r['outcome']}")
        print(f"    registered total interest (prediction.json) : {r['predInterest']}"
              f"      OBSERVED: {r['interest']}")
        print(f"    repayment rows {r['n']}, but principal is repaid on row {r['prinAt']}"
              f" (rows carrying principal: {r['prinRows']})")
        print(f"    distinct row totals except the last : {r['distinctExLast']}"
              f"   last row total {r['emiDiff'] + r['E_obs']}")
        print(f"    emiDifference {r['emiDiff']} vs B {r['B']}  -> P2_emiDifferenceEqualsB false")
        print(f"    n*E + B = {r['nE_B']}, n*E + B - P = {r['nE_B_minus_P']},"
              f" MEASURED totalRepayment = {r['totalRep']}")
        print( "    => the EMI-plus-balloon structure the registered form presumes DOES NOT HOLD:")
        print( "       the loan amortises early and the remaining rows are all zero, so neither")
        print( "       the registered nor the CORRECTED form is applicable. Only the")
        print(f"       unconditional identity holds: {r['totalRep']} - {r['P_rep']}"
              f" == {r['interest']}  -> {r['UNCOND']}")
    if not odd:
        print("  none -- every carrier satisfies the corrected form")
    print()

    print("  THIS DOES NOT ESTABLISH: that any verdict is correct; that G-8's region is right or")
    print("  wrong; that delta <= 1; that any Go port reproduces any of this. It establishes only")
    print("  what the oracle's captured schedules sum to, in integer minor units.")

    if contradictions:
        print()
        print("  CONTRADICTIONS BETWEEN MY RE-DERIVATION AND THE COMMITTED RECORD:")
        for c in contradictions:
            print(f"    !! {c}")

    state = "REFUSED" if contradictions else "GREEN"
    print(f"{PROBE} {state} carriers={len(carriers)} reproduced={reproduced} "
          f"agreeREG={agree_reg} agreeCORR={agree_corr} agreeUNCOND={agree_uncond} "
          f"structureHolds={struct_holds} contradictions={len(contradictions)}")
    return 1 if contradictions else 0


if __name__ == "__main__":
    sys.exit(main())
