"""
T38 (G) -- how much MONEY the periodRatio correction moves.

Independently re-derived by this task, over the January-2024 drifted date shapes
x terms x rates x principals, mirroring the sweep re-review T34 reported as
480/480.  Running it again from an independent transcription is the point:
either the number reproduces or it does not.

EVERY NUMBER HERE IS A RE-DERIVATION, recorded as a candidate shape to capture.
No oracle was contacted; nothing here may be promoted to the vector store.
"""
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t38_model import Request, generate, totals, m2s, MINOR, repayment_boundaries, period_ratio

TERMS = [6, 12, 18, 36]
RATES = ["7.0", "16.8", "18.5", "21.6"]
PRINCIPALS = [100, 1_200_000, 4_999_999, 5_000_000, 50_000_000]


def drifted_january_pairs():
    out = []
    for sd in range(1, 32):
        for dd in range(sd, 32):
            start, disb = date(2024, 1, sd), date(2024, 1, dd)
            bounds = repayment_boundaries(start, disb, 6, 1)
            if not (start <= disb < bounds[-1][1]):
                continue
            if any(period_ratio(start, f, d, 1) != Decimal(1) for f, d in bounds):
                out.append((start, disb))
    return out


def main():
    pairs = drifted_january_pairs()
    print("=" * 78)
    print("G  Money divergence: periodRatio (revision 7) vs RepaymentEvery")
    print("   (the reading revision 6 wrote), over the drifted January-2024 date")
    print("   shapes x 4 terms x 4 rates x 5 principals.")
    print("   RE-DERIVATION ONLY -- no oracle contacted.")
    print("=" * 78)
    print(f"\ndrifted January-2024 (start, disbursement) pairs: {len(pairs)}")
    for s, d in pairs:
        print(f"    {s} / {d}")

    total = 0
    diverge = 0
    worst = None
    for start, disb in pairs:
        for n in TERMS:
            for r in RATES:
                for p in PRINCIPALS:
                    req = Request(start=start, disb=disb, principal_minor=p * MINOR,
                                  n=n, rate_pct=Decimal(r))
                    a = generate(req)
                    b = generate(req, till_multiplier="repaymentEvery")
                    ta, tb = totals(a)[1], totals(b)[1]
                    cells_a = [(x.due, x.principal_minor, x.interest_minor,
                                x.outstanding_minor) for x in a]
                    cells_b = [(x.due, x.principal_minor, x.interest_minor,
                                x.outstanding_minor) for x in b]
                    total += 1
                    if cells_a != cells_b or ta != tb:
                        diverge += 1
                        gap = abs(ta - tb)
                        if worst is None or gap > worst[0]:
                            worst = (gap, start, disb, p, n, r, ta, tb)
    pct = (Decimal(diverge) * 100 / Decimal(total)).quantize(Decimal("0.01"))
    print(f"\nswept {total} in-graded-domain shapes")
    print(f"different money on {diverge} of {total} ({pct} %)")
    if worst:
        gap, start, disb, p, n, r, ta, tb = worst
        print(f"\nworst total-interest gap: MNT {m2s(gap)}")
        print(f"    schedule start {start}, disbursement {disb}, "
              f"MNT {p:,}, {n} x {r} %")
        print(f"    revision 7 (periodRatio)      total interest {m2s(ta)}")
        print(f"    revision 6 (RepaymentEvery)   total interest {m2s(tb)}")

    print("\n" + "-" * 78)
    print("The DEC-1 8 item 3e capture candidate, worked out (RE-DERIVED):")
    req = Request(start=date(2024, 1, 28), disb=date(2024, 1, 31),
                  principal_minor=1_200_000 * MINOR, n=6, rate_pct=Decimal("21.6"))
    a = generate(req)
    b = generate(req, till_multiplier="repaymentEvery")
    print("    MNT 1,200,000 / 6 x 21.6 %, start 2024-01-28, disbursement 2024-01-31")
    print(f"    {'#':<3} {'window':<26} {'rev7 P':>13} {'rev7 I':>11} "
          f"{'rev6 P':>13} {'rev6 I':>11}")
    for i, (x, y) in enumerate(zip(a, b), start=1):
        print(f"    {i:<3} {str(x.frm)+' -> '+str(x.due):<26} "
              f"{m2s(x.principal_minor):>13} {m2s(x.interest_minor):>11} "
              f"{m2s(y.principal_minor):>13} {m2s(y.interest_minor):>11}")
    print(f"    total interest: revision 7 {m2s(totals(a)[1])}   "
          f"revision 6 {m2s(totals(b)[1])}   "
          f"gap {m2s(abs(totals(a)[1] - totals(b)[1]))}")
    print("\n    periodRatio per repayment period (revision 7):")
    for i, (f, d) in enumerate(repayment_boundaries(req.start, req.disb, req.n, 1), 1):
        print(f"      period {i} [{f} -> {d}]  periodRatio = "
              f"{period_ratio(req.start, f, d, 1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
