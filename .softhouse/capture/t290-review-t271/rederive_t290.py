#!/usr/bin/env python3
"""T290 (reviewer) -- INDEPENDENT re-derivation of the T219 carrier money, written from the raw
capture only, without reading T271's instruments or `out/classify-t219.json`'s derived columns.

WHAT IT READS
  * `.softhouse/capture/t219-g8-residual/out/capture-t219-raw.json.gz`   (the ORACLE OUTPUT)
  * `.softhouse/capture/t219-g8-residual/prediction.json`                (the REGISTERED prediction)
It reads NOTHING ELSE.  In particular it never opens `out/classify-t219.json`, and it enforces
that with an `open`/`gzip.open` interposer that raises on any path whose name is forbidden.

MONEY.  Every monetary value is converted to INTEGER MINOR UNITS through `Decimal` and asserted
integral.  `json.loads(..., parse_float=Decimal)`.  `assert type(v) is int` on every arithmetic
operand.  There is no float in this file, including intermediates.  MNT, ISO 4217 numeric 496,
minor unit 2.

PROBE LINE (presence before value): `T290-REDERIVE: <STATE> ...`
EXIT 0 green, 1 a measured refusal, 2 error.  Never conflated.
"""
import builtins
import gzip
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T290-REDERIVE:"


def repo_root(p: Path) -> Path:
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: no .git ancestor", file=sys.stderr)
    raise SystemExit(2)


ROOT = repo_root(HERE)
CAP = ROOT / ".softhouse/capture/t219-g8-residual/out/capture-t219-raw.json.gz"
PRED = ROOT / ".softhouse/capture/t219-g8-residual/prediction.json"

# --- independence interposer: this instrument may not read the classification it is checking ---
_real_open = builtins.open
_real_gzopen = gzip.open
FORBIDDEN = ("classify", "acknowledged", "rederive_t219_carriers", "independent_recheck_t271")


def _guard(path):
    s = str(path)
    for bad in FORBIDDEN:
        if bad in s:
            raise RuntimeError("INDEPENDENCE VIOLATION: this instrument opened " + s)


def _open(file, *a, **k):
    _guard(file)
    return _real_open(file, *a, **k)


def _gzopen(filename, *a, **k):
    _guard(filename)
    return _real_gzopen(filename, *a, **k)


builtins.open = _open
gzip.open = _gzopen


def minor(s) -> int:
    """String money -> integer minor units.  Decimal only; refuses a non-integral result."""
    d = Decimal(str(s)) * 100
    if d != d.to_integral_value():
        raise ValueError("not an integral number of minor units: " + repr(s))
    v = int(d)
    assert type(v) is int
    return v


def main() -> int:
    raw = json.loads(gzip.open(CAP, "rt").read(), parse_float=Decimal)
    preds = {p["id"]: p for p in json.loads(open(PRED).read(), parse_float=Decimal)}
    caps = {c["id"]: c for c in raw["captures"]}

    print("T290 -- independent re-derivation of the T219 carriers, integer minor units only")
    print("=" * 108)
    print("  capture      : %s" % CAP.relative_to(ROOT))
    print("  registration : %s" % PRED.relative_to(ROOT))
    print("  precision    : moneyHelperPrecision=%s" % raw.get("moneyHelperPrecision"))
    print()

    # CARRIER SELECTION, from the RAW capture and the REGISTRATION only: a cell that is registered,
    # is not a calibration, did not throw, and is not RESCUED_BY_SITE3 (the classifier writes no
    # P2_* key for a rescued cell, so a rescued cell can carry no P2 disagreement).
    carriers = []
    for cid, c in caps.items():
        p = preds.get(cid)
        if p is None:
            continue
        if c.get("outcome") == "threw" or c.get("observed") is None:
            continue
        if p["predictedOutcome"] == "RESCUED_BY_SITE3":
            continue
        carriers.append(cid)
    carriers.sort()

    hdr = ("%-28s%6s%8s%8s%7s%8s%8s%11s%11s%10s%10s%11s%11s  REG CORR UNCND STRUCT"
           % ("id", "n", "B", "E_reg", "E_r1", "E_mode", "P", "sumTot", "hdrTot",
              "int_row", "int_hdr", "nE+B", "nE+B-P"))
    print(hdr)
    print("-" * len(hdr))

    agree_reg = agree_corr = agree_uncond = structure = 0
    sums_match = 0
    detail = {}
    for cid in carriers:
        c, p = caps[cid], preds[cid]
        o = c["observed"]
        reps = [r for r in o["periods"] if r["type"] == "REPAYMENT"]
        n_reg = int(p["n"])
        B = int(p["bMinor"])
        E_reg = int(p["emiMinorPredicted"])
        assert type(n_reg) is int and type(B) is int and type(E_reg) is int

        tot = [minor(r["total"]) for r in reps]
        interest_rows = [minor(r["interest"]) for r in reps]
        principal_rows = [minor(r["principal"]) for r in reps]
        fee_rows = [minor(r["feeAmount"]) for r in reps]
        pen_rows = [minor(r["penaltyAmount"]) for r in reps]

        sum_tot = sum(tot)
        sum_int = sum(interest_rows)
        sum_prin = sum(principal_rows)
        sum_fee = sum(fee_rows)
        sum_pen = sum(pen_rows)
        for v in (sum_tot, sum_int, sum_prin, sum_fee, sum_pen):
            assert type(v) is int

        hdr_tot = minor(o["totalRepaymentAmount"])
        hdr_int = minor(o["totalInterestAmount"])
        hdr_prin = minor(o["totalPrincipalAmount"])
        hdr_disb = minor(o["totalDisbursedAmount"])

        # cross-check: the rows must sum to the capture's own header totals
        ok_sums = (sum_tot == hdr_tot and sum_int == hdr_int and sum_prin == hdr_prin)
        sums_match += 1 if ok_sums else 0

        E_r1 = tot[0]
        mode = Counter(tot[:-1]).most_common(1)[0][0] if len(tot) > 1 else tot[0]
        P = hdr_prin                       # principal actually repaid, MEASURED
        nEB = n_reg * E_r1 + B
        nEBP = nEB - P
        assert type(nEB) is int and type(nEBP) is int

        a_reg = (hdr_int == nEB)
        a_corr = (hdr_int == nEBP)
        a_unc = (hdr_int == sum_tot - P)
        # EMI-plus-balloon STRUCTURE, stated as P2's OWN first two conjuncts:
        #   every repayment row except the last totals E, and the last totals E + B.
        struct = (len(set(tot[:-1])) == 1 and tot[0] == mode and tot[-1] == tot[0] + B)
        agree_reg += a_reg
        agree_corr += a_corr
        agree_uncond += a_unc
        structure += struct

        print("%-28s%6d%8d%8d%7d%8d%8d%11d%11d%10d%10d%11d%11d  %-4s%-5s%-6s%s"
              % (cid, n_reg, B, E_reg, E_r1, mode, P, sum_tot, hdr_tot, sum_tot - P, hdr_int,
                 nEB, nEBP, str(a_reg)[0], str(a_corr)[0], str(a_unc)[0], str(struct)[0]))
        detail[cid] = dict(n=n_reg, B=B, P=P, E_r1=E_r1, E_mode=mode, sum_tot=sum_tot,
                           hdr_int=hdr_int, nEB=nEB, nEBP=nEBP, reps=len(reps),
                           interest_rows=interest_rows, principal_rows=principal_rows,
                           tot=tot, ok_sums=ok_sums, disb=hdr_disb, fee=sum_fee, pen=sum_pen)

    k = len(carriers)
    print()
    print("  REGISTERED    interest == n*E + B         : %d of %d" % (agree_reg, k))
    print("  CORRECTED     interest == n*E + B - P     : %d of %d" % (agree_corr, k))
    print("  UNCONDITIONAL interest == sumTotal - P    : %d of %d   (sumTotal MEASURED)"
          % (agree_uncond, k))
    print("  EMI-plus-balloon STRUCTURE holds          : %d of %d" % (structure, k))
    print("  row sums == the capture's OWN header totals: %d of %d" % (sums_match, k))

    # --- the failing row, in full ---
    target = "T219-R600p0-N103-B1"
    if target in detail:
        d = detail[target]
        nz_int = [i + 1 for i, v in enumerate(d["interest_rows"]) if v != 0]
        nz_prin = [i + 1 for i, v in enumerate(d["principal_rows"]) if v != 0]
        nz_tot = [i + 1 for i, v in enumerate(d["tot"]) if v != 0]
        print()
        print("  ROW-BY-ROW, %s   (all figures integer minor units, MNT)" % target)
        print("    repayment rows                 : %d   (registered n = %d)" % (d["reps"], d["n"]))
        print("    disbursed                      : %d" % d["disb"])
        print("    rows with NONZERO interest     : %s" % nz_int)
        print("      each carries                 : %s"
              % sorted(set(d["interest_rows"][i - 1] for i in nz_int)))
        print("      count x value = sum          : %d x 1 = %d" % (len(nz_int),
                                                                    sum(d["interest_rows"])))
        print("    rows with NONZERO principal    : %s  value %s"
              % (nz_prin, [d["principal_rows"][i - 1] for i in nz_prin]))
        print("    rows with NONZERO total        : %s" % nz_tot)
        print("    rows %d..%d are ALL ZERO        : %s"
              % (max(nz_tot) + 1, d["reps"], all(v == 0 for v in d["tot"][max(nz_tot):])))
        print("    fees %d, penalties %d" % (d["fee"], d["pen"]))
        print("    E from row 1                   : %d" % d["E_r1"])
        print("    E as the MODE of rows 1..n-1   : %d" % d["E_mode"])
        print("    last row total                 : %d   emiDifference = %d   vs registered B = %d"
              % (d["tot"][-1], d["tot"][-1] - d["E_r1"], d["B"]))
        print("    n*E + B                        : %d * %d + %d = %d"
              % (d["n"], d["E_r1"], d["B"], d["nEB"]))
        print("    n*E + B - P                    : %d - %d = %d" % (d["nEB"], d["P"], d["nEBP"]))
        print("    MEASURED total repayment       : %d" % d["sum_tot"])
        print("    MEASURED principal repaid      : %d" % d["P"])
        print("    OBSERVED total interest        : %d" % d["hdr_int"])
        print("    totalRepayment - principal     : %d - %d = %d"
              % (d["sum_tot"], d["P"], d["sum_tot"] - d["P"]))
        print("    rows that ever charge interest : %d of %d  => n*E prices %d rows that charge "
              "nothing" % (len(nz_int), d["reps"], d["reps"] - len(nz_int)))

    refused = (sums_match != k) or k == 0
    state = "REFUSED" if refused else "GREEN"
    print()
    print("%s %s carriers=%d sumsMatchHeader=%d agreeREG=%d agreeCORR=%d agreeUNCOND=%d "
          "structureHolds=%d" % (PROBE, state, k, sums_match, agree_reg, agree_corr,
                                 agree_uncond, structure))
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
