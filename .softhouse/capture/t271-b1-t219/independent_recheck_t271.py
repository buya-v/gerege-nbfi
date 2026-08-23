#!/usr/bin/env python3
"""T271 -- INDEPENDENT re-check of the 6-of-7, written as a SECOND instrument on purpose.

WHY A SECOND ONE. `rederive_t219_carriers.py` (rescued from the killed 20260822-140002 worker)
already re-derives the carriers. A rescued artefact is EVIDENCE, not a conclusion: its
completeness is unverified and it is where a dead worker stood. P-83 -- *two independent
movements of one pinned number reconcile BY RUNNING, never by arithmetic* -- so the 6-of-7 is
re-measured here by code written without reusing that file's derivations, and the two probe lines
are compared by `run.sh`.

DELIBERATELY DIFFERENT, so agreement is evidence and not an echo:
  * it selects carriers from the RAW CAPTURE (every non-throwing cell registered in
    `prediction.json`), never from `classify-t219.json`'s `cells[]`. If the classifier had
    silently dropped a carrier, this file would still see it.
  * it derives E TWO WAYS -- the row-1 total, and the modal total over every row except the last
    -- and prints both. Where they differ the EMI-plus-balloon shape is absent, which is the whole
    question on the failing row.
  * it reconstructs total repayment / principal / interest by SUMMING THE SCHEDULE and separately
    from the capture's own header totals, and refuses if the two disagree.
  * it opens `classify-t219.json` only at the very end, as a separate reproduction assertion.

NO FLOATING POINT, including intermediates (project non-negotiable; T145): `parse_float=Decimal`
on every read, every money value through an integral `Decimal` to int minor units, every
arithmetic operand asserted `type(v) is int`.

EXIT CODES, never conflated (P-80 / the exit-code half of P-81):
    0  GREEN    -- every re-derivation reproduced the committed record
    1  REFUSED  -- a REAL measured negative: a re-derived figure contradicts the record
    2  ERROR    -- usage, IO or parse. NEVER used to report an absence.

PROBE LINE, last line always:
    T271-INDEP: <STATE> carriers=.. agreeREG=.. agreeCORR=.. agreeUNCOND=.. structureHolds=..
                contradictions=..
Test its PRESENCE before its VALUE (P-83/P-84).
"""
import gzip
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T271-INDEP:"


class Err(Exception):
    """An ERROR (exit 2), never a measured negative."""


def loadgz(p: Path):
    with gzip.open(p, "rt") as fh:
        return json.loads(fh.read(), parse_float=Decimal)


def load(p: Path):
    return json.loads(p.read_text(), parse_float=Decimal)


def m(v) -> int:
    """Decimal-only conversion to integer minor units."""
    if isinstance(v, float):
        raise Err(f"float reached m(): {v!r} -- parse_float=Decimal was not applied")
    d = Decimal(str(v)) * 100
    if d != d.to_integral_value():
        raise Err(f"not an integral number of minor units: {v!r}")
    return int(d)


def I(name: str, v):
    if type(v) is not int:
        raise Err(f"{name} is {type(v).__name__}, not int: {v!r}")
    return v


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    t219 = Path(argv[0]).resolve() if argv else (HERE / ".." / "t219-g8-residual").resolve()
    raw_p = t219 / "out" / "capture-t219-raw.json.gz"
    pred_p = t219 / "prediction.json"
    cls_p = t219 / "out" / "classify-t219.json"
    for p in (raw_p, pred_p, cls_p):
        if not p.exists():
            print(f"ERROR: missing input: {p}", file=sys.stderr)
            return 2
    try:
        raw = loadgz(raw_p)
        preds = {p["id"]: p for p in load(pred_p)}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print("T271 -- INDEPENDENT re-check of the t219 carriers, from the RAW capture only")
    print("=" * 118)
    print(f"  raw       : {raw_p.name}")
    print(f"  precision recorded in the capture : {raw.get('moneyHelperPrecision')!r}")
    print()
    hdr = (f"{'id':<26}{'n':>6}{'E_row1':>8}{'E_modal':>8}{'B':>6}{'P':>7}{'sumTot':>10}"
           f"{'hdrTot':>10}{'interest':>10}  {'REG':<6}{'CORR':<6}{'UNCOND':<7}{'STRUCT':<7}"
           f"{'emiD=B':<7}")
    print(hdr)
    print("-" * len(hdr))

    agreeREG = agreeCORR = agreeUNCOND = struct = 0
    carriers = []
    bad = []
    try:
        for cap in raw["captures"]:
            cid = cap["id"]
            if cid not in preds:
                continue
            if cap.get("outcome") == "threw" or cap.get("observed") is None:
                continue
            o = cap["observed"]
            reps = [r for r in o["periods"] if r["type"] == "REPAYMENT"]
            if not reps:
                raise Err(f"{cid}: no REPAYMENT rows in the raw capture")
            tot = [m(r["total"]) for r in reps]
            pri = [m(r["principal"]) for r in reps]
            itr = [m(r["interest"]) for r in reps]
            n = I("n", preds[cid]["n"])
            B = I("B", preds[cid]["bMinor"])
            sumTot = I("sumTot", sum(tot))
            sumPri = I("sumPri", sum(pri))
            sumItr = I("sumItr", sum(itr))
            hdrTot, hdrPri, hdrItr = (m(o["totalRepaymentAmount"]),
                                      m(o["totalPrincipalAmount"]),
                                      m(o["totalInterestAmount"]))
            if (sumTot, sumPri, sumItr) != (hdrTot, hdrPri, hdrItr):
                bad.append(f"{cid}: schedule sums {(sumTot, sumPri, sumItr)} "
                           f"!= capture header {(hdrTot, hdrPri, hdrItr)}")
            if len(reps) != n:
                bad.append(f"{cid}: {len(reps)} repayment rows but registered n={n}")
            e_row1 = tot[0]
            exlast = set(tot[:-1])
            e_modal = Counter(tot[:-1]).most_common(1)[0][0]
            ne_b = I("ne_b", n * e_row1 + B)
            REG = (sumItr == ne_b)
            CORR = (sumItr == ne_b - sumPri)
            UNCOND = (sumItr == sumTot - sumPri)
            STRUCT = (exlast == {e_row1} and tot[-1] == e_row1 + B)
            emiDB = ((tot[-1] - tot[0]) == B)
            agreeREG += REG
            agreeCORR += CORR
            agreeUNCOND += UNCOND
            struct += STRUCT
            carriers.append({"id": cid, "REG": REG, "CORR": CORR, "UNCOND": UNCOND,
                             "STRUCT": STRUCT, "emiDB": emiDB, "tot": tot, "pri": pri,
                             "itr": itr, "n": n, "B": B, "e1": e_row1, "sumTot": sumTot,
                             "sumPri": sumPri, "sumItr": sumItr})
            print(f"{cid:<26}{n:>6}{e_row1:>8}{e_modal:>8}{B:>6}{sumPri:>7}{sumTot:>10}"
                  f"{hdrTot:>10}{sumItr:>10}  {str(REG):<6}{str(CORR):<6}{str(UNCOND):<7}"
                  f"{str(STRUCT):<7}{str(emiDB):<7}")
    except Err as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    N = len(carriers)
    if N == 0:
        print("  REFUSED  NIL COVERAGE -- no carrier was inspected. An empty measurement REFUTES")
        print("           rather than passes through.")
        print(f"{PROBE} REFUSED carriers=0 agreeREG=0 agreeCORR=0 agreeUNCOND=0 "
              "structureHolds=0 contradictions=1")
        return 1

    print()
    print(f"  carriers (non-throwing registered cells)  : {N}")
    print(f"  REGISTERED    interest == n*E + B         : {agreeREG} of {N}")
    print(f"  CORRECTED     interest == n*E + B - P     : {agreeCORR} of {N}"
          "        <<< T259's ruling")
    print(f"  UNCONDITIONAL interest == sumTotal - P    : {agreeUNCOND} of {N}"
          "        <<< sumTotal MEASURED, not modelled")
    print(f"  EMI-plus-balloon STRUCTURE holds          : {struct} of {N}")
    print()

    odd = [c for c in carriers if not c["CORR"]]
    for c in odd:
        itr, pri, tot = c["itr"], c["pri"], c["tot"]
        nz_i = [i + 1 for i, v in enumerate(itr) if v != 0]
        nz_p = [i + 1 for i, v in enumerate(pri) if v != 0]
        nz_t = [i + 1 for i, v in enumerate(tot) if v != 0]
        print(f"  THE ROW WHERE THE CORRECTED FORM ALSO FAILS: {c['id']}")
        print(f"    rows with nonzero INTEREST  : {nz_i}")
        print(f"    rows with nonzero PRINCIPAL : {nz_p}")
        print(f"    rows with nonzero TOTAL     : {nz_t}")
        print(f"    row-1 total E {c['e1']}, last row total {tot[-1]}, "
              f"emiDifference {tot[-1] - tot[0]} vs B {c['B']}")
        print(f"    n*E+B = {c['n'] * c['e1'] + c['B']}; "
              f"n*E+B-P = {c['n'] * c['e1'] + c['B'] - c['sumPri']}; "
              f"MEASURED total repayment = {c['sumTot']}; interest = {c['sumItr']}")
        print(f"    only {len(nz_i)} of {c['n']} rows ever charge interest, so n*E prices "
              f"{c['n'] - len(nz_i)} rows that charge nothing.")
        print()
    if not odd:
        print("  none -- every carrier satisfies the corrected form")
        print()

    try:
        cls = load(cls_p)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    rec = {r["id"]: r for r in cls.get("cells", [])}
    reproduced = 0
    for c in carriers:
        r = rec.get(c["id"])
        if r is None:
            bad.append(f"{c['id']}: carrier is in the raw capture but NOT in classify-t219.json")
            continue
        ok = True
        if (r.get("observedPrincipalMinor"), r.get("observedInterestMinor"),
                r.get("observedRow1TotalMinor"), r.get("observedLastTotalMinor")) != (
                c["sumPri"], c["sumItr"], c["e1"], c["tot"][-1]):
            bad.append(f"{c['id']}: committed observed* fields disagree with this re-derivation")
            ok = False
        if r.get("P2_totalInterestEqualsNEplusB") is not c["REG"]:
            bad.append(f"{c['id']}: recorded P2_totalInterestEqualsNEplusB="
                       f"{r.get('P2_totalInterestEqualsNEplusB')} re-derives {c['REG']}")
            ok = False
        if r.get("P2_emiDifferenceEqualsB") is not c["emiDB"]:
            bad.append(f"{c['id']}: recorded P2_emiDifferenceEqualsB="
                       f"{r.get('P2_emiDifferenceEqualsB')} re-derives {c['emiDB']}")
            ok = False
        reproduced += 1 if ok else 0

    print(f"  committed classify-t219.json reproduced   : {reproduced} of {N} carriers")
    print()
    print("  THIS DOES NOT ESTABLISH: that any verdict is correct; that G-8's region is right or")
    print("  wrong; that any Go port reproduces any of it. Only what the oracle's captured")
    print("  schedules sum to, in integer minor units.")
    if bad:
        print()
        print("  CONTRADICTIONS:")
        for b in bad:
            print(f"    !! {b}")
    state = "REFUSED" if bad else "GREEN"
    print(f"{PROBE} {state} carriers={N} agreeREG={agreeREG} agreeCORR={agreeCORR} "
          f"agreeUNCOND={agreeUNCOND} structureHolds={struct} contradictions={len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
