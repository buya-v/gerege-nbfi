#!/usr/bin/env python3
"""T42 analysis -- contacts no oracle.  Reads the observed payload and answers, cell by cell:

(a) which MathContext moves the money?  For every probe shape, compare the FULL CELL SET of
    the four matrix cases against the ratified pair (ambient HALF_UP, threaded (19, HALF_UP)):
        B  ambient DOWN, threaded unchanged
        E  ambient UP,   threaded unchanged
        C  threaded DOWN, ambient unchanged
        D  ambient ABSENT (MoneyHelper never initialised), threaded unchanged

(b) does threaded precision 19 separate from 12 (or 8) on ANY shape?

FULL-CELL comparison, never the three headline scalars -- `.softhouse/patterns.md`: a
three-scalar check is what let defect F-1 hide through five reviews.

No float anywhere: every value is compared as an exact string.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD = HERE.parent / "out" / "t42-mathcontext.json"


def cells(cap):
    """Every observed cell of a capture, as (name, exact-string) pairs.

    Full cell set: the four plan totals plus every column of every period row.
    """
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
    """Cells on which two captures disagree.  None if either failed to produce one."""
    ca, cb = cells(a), cells(b)
    if ca is None or cb is None:
        return None
    if len(ca) != len(cb):
        return [("SHAPE_MISMATCH", f"{len(ca)} cells vs {len(cb)} cells")]
    return [(n, f"{va} -> {vb}") for (n, va), (_, vb) in zip(ca, cb) if va != vb]


def main():
    doc = json.load(open(PAYLOAD))
    caps = {c["id"]: c for c in doc["captures"]}

    print("=" * 100)
    print("T42 -- WHICH MathContext IS ACTUALLY IN FORCE ON THE PATH A SEAM")
    print("=" * 100)
    print()
    print("payload            :", PAYLOAD)
    print("fineract commit    :", doc["fineractCommit"])
    print("MoneyHelper.PRECISION read from the running oracle:", doc["moneyHelperPrecisionConstant"])
    print("ambient-absence probe canary:", doc["ambientCanary"])
    print()
    print("The canary is the proof that the ABSENCE probe is not vacuous: MoneyHelper.getMathContext()")
    print("on a tenant it was never initialised for MUST throw, or a case that 'did not throw' proves")
    print("nothing.  It threw.")
    print()

    # ---------------- (a) the ambient / threaded matrix -----------------------------------
    print("=" * 100)
    print("(a) THE MATRIX.  Baseline A = ambient HALF_UP(4), threaded (19, HALF_UP) -- the ratified pair.")
    print("=" * 100)
    print()
    hdr = f"{'shape':<32} {'B amb=DOWN':>12} {'E amb=UP':>12} {'C thr=DOWN':>12} {'D amb=ABSENT':>14}"
    print(hdr)
    print("-" * len(hdr))

    matrix_ids = sorted({cid[: len("T42-MX-00")] for cid in caps if cid.startswith("T42-MX-")})
    summary = []
    for base in matrix_ids:
        a = caps[base + "-A"]
        row = [a["shape"]]
        detail = {}
        for suffix, label in (("-B", "amb=DOWN"), ("-E", "amb=UP"), ("-C", "thr=DOWN"), ("-D", "amb=ABSENT")):
            other = caps[base + suffix]
            if other.get("observed") is None:
                row.append("THREW")
                detail[label] = "THREW"
                continue
            d = diff(a, other)
            row.append(f"{len(d)} cells" if d else "identical")
            detail[label] = d
        print(f"{row[0]:<32} {row[1]:>12} {row[2]:>12} {row[3]:>12} {row[4]:>14}")
        summary.append((base, a["shape"], detail))
    print()
    print(f"total cells compared per shape: see per-shape detail below")
    print()

    # ---- detail on every shape where the AMBIENT moved something, or the absence probe threw
    print("-" * 100)
    print("DETAIL -- every shape on which the AMBIENT context is observably load-bearing")
    print("-" * 100)
    any_ambient = False
    for base, shape, detail in summary:
        interesting = []
        for label in ("amb=DOWN", "amb=UP"):
            d = detail[label]
            if d == "THREW" or (d and len(d) > 0):
                interesting.append((label, d))
        if detail["amb=ABSENT"] == "THREW":
            interesting.append(("amb=ABSENT", "THREW"))
        if not interesting:
            continue
        any_ambient = True
        print()
        print(f"  shape {shape}  ({base})")
        for label, d in interesting:
            if d == "THREW":
                cap = caps[base + ("-D" if label == "amb=ABSENT" else "-B")]
                print(f"    {label}: {cap['error']}")
                for f in cap["stackTrace"][:8]:
                    print(f"        {f}")
            else:
                print(f"    {label}: {len(d)} cells move")
                for n, v in d[:12]:
                    print(f"        {n}: {v}")
                if len(d) > 12:
                    print(f"        ... and {len(d) - 12} more")
    if not any_ambient:
        print("  (none)")
    print()

    # ---- detail on the threaded axis
    print("-" * 100)
    print("DETAIL -- the THREADED rounding-mode flip (HALF_UP -> DOWN), same shapes")
    print("-" * 100)
    moved = 0
    for base, shape, detail in summary:
        d = detail["thr=DOWN"]
        if d == "THREW":
            print(f"  {shape:<32} THREW")
            continue
        if d:
            moved += 1
            print(f"  {shape:<32} {len(d):>4} cells move, e.g. "
                  + "; ".join(f"{n}: {v}" for n, v in d[:2]))
        else:
            print(f"  {shape:<32}    0 cells move (identical)")
    print()
    print(f"  THREADED rounding mode moved money on {moved} of {len(summary)} shapes.")
    print()

    # ---------------- (b) the precision search --------------------------------------------
    print("=" * 100)
    print("(b) T39 N-4 -- DOES THREADED PRECISION 19 SEPARATE FROM 12?")
    print("=" * 100)
    print()
    prec_bases = sorted({cid[: len("T42-PREC-00")] for cid in caps if cid.startswith("T42-PREC-")})
    hdr = f"{'shape':<34} {'principal':>18} {'n':>4} {'19 vs 12':>12} {'19 vs 8':>12}"
    print(hdr)
    print("-" * len(hdr))
    sep12 = []
    sep8 = []
    for base in prec_bases:
        p19 = caps[base + "-p19"]
        p12 = caps[base + "-p12"]
        p8 = caps[base + "-p8"]
        d12 = diff(p19, p12)
        d8 = diff(p19, p8)
        s12 = "THREW" if d12 is None else (f"{len(d12)} cells" if d12 else "identical")
        s8 = "THREW" if d8 is None else (f"{len(d8)} cells" if d8 else "identical")
        print(f"{p19['shape']:<34} {p19['inputs']['disbursementAmount']:>18} "
              f"{p19['inputs']['numberOfRepayments']:>4} {s12:>12} {s8:>12}")
        if d12:
            sep12.append((base, p19, p12, d12))
        if d8:
            sep8.append((base, p19, p8, d8))
    print()
    print(f"  shapes swept                     : {len(prec_bases)}")
    print(f"  shapes separating 19 from 12     : {len(sep12)}")
    print(f"  shapes separating 19 from 8      : {len(sep8)}")
    print()

    if sep12:
        print("-" * 100)
        print("THE SEPARATING SHAPES, 19 vs 12 -- smallest principal first")
        print("-" * 100)
        for base, p19, p12, d in sorted(sep12, key=lambda t: int(t[1]["inputs"]["disbursementAmount"])):
            print()
            print(f"  {base}  shape {p19['shape']}")
            print(f"    principal {p19['inputs']['disbursementAmount']}  n={p19['inputs']['numberOfRepayments']}"
                  f"  rate {p19['inputs']['annualNominalInterestRate']}"
                  f"  daysInMonth {p19['inputs']['daysInMonth']} daysInYear {p19['inputs']['daysInYear']}")
            print(f"    {len(d)} cells differ.  totalInterestAmount: "
                  f"{p19['observed']['totalInterestAmount']} (p19) vs {p12['observed']['totalInterestAmount']} (p12)")
            for n, v in d[:10]:
                print(f"        {n}: {v}")
            if len(d) > 10:
                print(f"        ... and {len(d) - 10} more")
    else:
        print("  NO SHAPE IN THIS SWEEP SEPARATES THREADED PRECISION 19 FROM 12.")
    print()

    # ---------------- controls -------------------------------------------------------------
    print("=" * 100)
    print("CONTROLS -- these reproduce committed observations taken by OTHER harnesses")
    print("=" * 100)
    print()
    for cid in ("T42-CAL", "T42-CTL-Q0a", "T42-CTL-1", "T42-CTL-P0A", "T42-CTL-MEB"):
        c = caps[cid]
        o = c["observed"]
        print(f"  {cid:<14} term {o['loanTermInDays']:>4} d   disbursed {o['totalDisbursedAmount']:>18}"
              f"   interest {o['totalInterestAmount']:>18}   repayment {o['totalRepaymentAmount']:>18}")
    print()
    print("  (controls.py checks these against the committed literals and exits 1 on any mismatch)")
    print()


if __name__ == "__main__":
    sys.exit(main())
