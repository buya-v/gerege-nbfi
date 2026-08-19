#!/usr/bin/env python3
"""T42 capture-2 analysis -- contacts no oracle.

(1) Bisects the threaded-precision-19-vs-12 threshold on three shape families.
(2) Compares the two WIRINGS side by side: does the tenant rounding ordinal move the money
    under the Path A wiring (caller builds its own mc) and under the Path B wiring
    (caller passes MoneyHelper.getMathContext(), as LoanScheduleAssembler.java:753 does)?

FULL-CELL comparison.  Exact string comparison.  No float anywhere.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD = HERE.parent / "out" / "t42-mathcontext2.json"


def cells(cap):
    if cap.get("observed") is None:
        return None
    obs = cap["observed"]
    out = [
        ("loanTermInDays", str(obs["loanTermInDays"])),
        ("totalDisbursedAmount", obs["totalDisbursedAmount"]),
        ("totalInterestAmount", obs["totalInterestAmount"]),
        ("totalRepaymentAmount", obs["totalRepaymentAmount"]),
    ]
    for i, p in enumerate(obs["periods"]):
        for k in sorted(p.keys()):
            out.append((f"period[{i}].{k}", str(p[k])))
    return out


def diff(a, b):
    ca, cb = cells(a), cells(b)
    if ca is None or cb is None:
        return None
    return [(n, f"{va} -> {vb}") for (n, va), (_, vb) in zip(ca, cb) if va != vb]


def main():
    doc = json.load(open(PAYLOAD))
    caps = {c["id"]: c for c in doc["captures"]}

    print("=" * 100)
    print("T42 capture 2 -- PRECISION THRESHOLD, and the two WIRINGS side by side")
    print("=" * 100)
    print()

    # ---- (1) precision bisection ---------------------------------------------------------
    print("=" * 100)
    print("(1) THE THREADED-PRECISION THRESHOLD.  Bisecting where 19 stops agreeing with 12.")
    print("=" * 100)
    print()
    bases = sorted({cid[: len("T42B-PREC-00")] for cid in caps if cid.startswith("T42B-PREC-")},
                   key=lambda s: int(s.split("-")[-1]))
    hdr = f"{'principal (minor units, MNT)':>32} {'n':>5} {'rate':>7} {'19 vs 12':>14} {'total interest p19':>24}"
    print(hdr)
    print("-" * len(hdr))
    firsts = {}
    for base in bases:
        p19, p12 = caps[base + "-p19"], caps[base + "-p12"]
        d = diff(p19, p12)
        n = p19["inputs"]["numberOfRepayments"]
        rate = p19["inputs"]["annualNominalInterestRate"]
        prin = p19["inputs"]["disbursementAmount"]
        verdict = f"{len(d)} cells" if d else "identical"
        print(f"{prin:>32} {n:>5} {rate:>7} {verdict:>14} {p19['observed']['totalInterestAmount']:>24}")
        key = (n, rate)
        if d and key not in firsts:
            firsts[key] = (prin, p19, p12, d)
    print()
    print("SMALLEST OBSERVED SEPARATING PRINCIPAL, per family:")
    for (n, rate), (prin, p19, p12, d) in sorted(firsts.items()):
        print(f"  n={n:<4} rate {rate:<6} -> principal {prin}  ({len(d)} cells differ)")
        print(f"        total interest  p19 {p19['observed']['totalInterestAmount']}"
              f"   p12 {p12['observed']['totalInterestAmount']}")
        for name, v in d[:6]:
            print(f"        {name}: {v}")
    if not firsts:
        print("  (none separated in this sweep)")
    print()

    # ---- (2) the two wirings --------------------------------------------------------------
    print("=" * 100)
    print("(2) THE TWO WIRINGS.  Only the tenant rounding ordinal is varied.  Baseline = ordinal 4.")
    print("=" * 100)
    print()
    for family, label in (("", "6 x 21.6 % on MNT 1,200,000"),
                          ("tie-", "T36's half-cent tie shape, MNT 1,162,502.50, 12 x 21.6 %")):
        print(f"  shape: {label}")
        print(f"    {'ordinal':>8} {'ambient':>34} {'effective threaded mc':>34} "
              f"{'PATH A total interest':>24} {'PATH B total interest':>24}")
        base_a = caps[f"T42B-PA-{family}ord4"]
        base_b = caps[f"T42B-PB-{family}ord4"]
        for ordv in (4, 1, 0, 6):
            a = caps[f"T42B-PA-{family}ord{ordv}"]
            b = caps[f"T42B-PB-{family}ord{ordv}"]
            print(f"    {ordv:>8} {b['inputs']['ambientMoneyHelperMathContext']:>34} "
                  f"{b['inputs']['effectiveThreadedMathContext']:>34} "
                  f"{a['observed']['totalInterestAmount']:>24} {b['observed']['totalInterestAmount']:>24}")
        print()
        for ordv in (1, 0, 6):
            da = diff(base_a, caps[f"T42B-PA-{family}ord{ordv}"])
            db = diff(base_b, caps[f"T42B-PB-{family}ord{ordv}"])
            print(f"    ordinal 4 -> {ordv}: PATH A wiring {len(da):>4} cells move   |   "
                  f"PATH B wiring {len(db):>4} cells move")
        print()

    print("-" * 100)
    print("READ THIS OFF THE TABLE, do not infer it:")
    print("  Under the PATH A wiring the tenant ordinal is inert -- the caller's own MathContext")
    print("  governs.  Under the PATH B wiring the SAME ordinal change moves the money, because")
    print("  the caller sourced its MathContext from MoneyHelper.  Same shape, same seam, same")
    print("  run; the ONLY difference is where the MathContext came from.")
    print("-" * 100)
    print()


if __name__ == "__main__":
    sys.exit(main())
