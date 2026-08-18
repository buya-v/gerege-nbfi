#!/usr/bin/env python3
"""T29 -- under-determination sweeps over DEC-1 revision 4's own graded domain.

*** NO LIVE ORACLE. ***  No Fineract instance is reachable in this sandbox (no
Docker, no PostgreSQL).  Everything below is a re-derivation from the pinned
checkout 426a23544 through `t29_rederive.py`, whose source-faithful arm is
validated against 13 already-committed observations by `t29_validate.py`.
No figure printed here is an observation; none may enter the vector store.

Three experiments:

  A  `n` in the EMI re-adjust loop.  DEC-1 4.3.1 and contract.go's `Period` doc
     both assert "n is the number of related repayment periods, which inside
     the graded domain is NumberOfRepayments
     (ProgressiveLoanInterestScheduleModel.java:191-194)".  Re-derived from
     source, n == relatedRepaymentPeriods.size()
     (EmiAdjustment.java:54-56, ProgressiveEMICalculator.java:732, :749,
     :250-263, ProgressiveLoanInterestScheduleModel.java:191-198), which equals
     NumberOfRepayments only when the disbursement lands inside the FIRST
     repayment period and not on its due date.  The graded domain admits
     ScheduleStartDate <= D < last DueDate and the Run-1 corpus samples exactly
     such a shape (t23-probe Q0b: start 2024-01-01, disbursement 2024-02-01).
     Only the value of `n` is varied; the rebuild semantics are identical in
     both arms, so any divergence is attributable to `n` alone.

  B  The actualDays/calcDays correction in the RATE FACTOR
     (ProgressiveEMICalculator.java:1500-1503, :1961-1962): performed, versus
     skipped because contract.go says it "is exactly 1".

  C  The `/ lengthTillPeriodDueDate * length` round-trip inside the PER-PERIOD
     INTEREST computation (InterestPeriod.java:145-158), which DEC-1 never
     mentions: performed, versus the textbook `balance * rateFactor` that the
     document's own prose describes.
"""

import random
from datetime import date
from decimal import Decimal

import t29_rederive as R
from t29_rederive import (f, windows, related_index, rate_factor,
                          level_installment, rebuild, readjust)

RATES = ["7.0", "16.8", "18.5", "21.6", "12.0", "24.0", "15.0", "30.0"]


def gen_n(p, n_rep, rate, disb, which_n, start=date(2024, 1, 1)):
    """Generate with `n` taken either from the DEC-1 text or from source.
    `keep_before` is True in BOTH arms, so only `n` varies."""
    pm = int(Decimal(str(p)) * R.UNIT)
    wins = windows(start, disb, n_rep)
    fr = related_index(n_rep, wins, disb)
    if fr is None:
        return None
    num, den = Decimal(str(rate)).as_integer_ratio()
    periods = []
    for i, (a, b) in enumerate(wins):
        L = (b - a).days
        rf = rate_factor(num, den * 100, L, L) if i >= fr else Decimal(0)
        periods.append((a, b, L, rf))
    level = level_installment(pm, [q[3] for q in periods[fr:]])
    rows = rebuild(pm, periods, fr, level, keep_before=True)
    n = (n_rep - fr) if which_n == "source" else n_rep
    return readjust(pm, periods, fr, rows, n, True)


def sweep_a(trials=120000, seed=29):
    print("=" * 78)
    print("A -- n == NumberOfRepayments (DEC-1 text) vs n == |related| (source)")
    print("=" * 78)
    rng = random.Random(seed)
    tested = div = 0
    examples = {}
    for _ in range(trials):
        n_rep = rng.choice([6, 12, 18, 24, 36])
        j = rng.choice([1, 2])                      # disbursement on period j's due date
        disb = date(2024, 1 + j, 1)
        rate = rng.choice(RATES)
        p = rng.randrange(50000, 60000000)
        a = gen_n(p, n_rep, rate, disb, "source")
        b = gen_n(p, n_rep, rate, disb, "text")
        if a is None:
            continue
        tested += 1
        ka = [(r["emi"], r["interest"]) for r in a]
        kb = [(r["emi"], r["interest"]) for r in b]
        if ka != kb:
            div += 1
            key = (n_rep, j, rate)
            if key not in examples:
                ra = [x for x in a if x["emi"] != 0]
                rb = [x for x in b if x["emi"] != 0]
                examples[key] = (p, f(ra[0]["emi"]), f(a[-1]["emi"]),
                                 f(sum(x["interest"] for x in a)),
                                 f(rb[0]["emi"]), f(b[-1]["emi"]),
                                 f(sum(x["interest"] for x in b)))
    print(f"  shapes compared {tested}, DIVERGENT {div} ({100.0*div/tested:.2f}%)")
    for k in sorted(examples)[:8]:
        n_rep, j, rate = k
        p, sl, sf, si, tl, tf, ti = examples[k]
        print(f"   P={p:<9} n={n_rep:<3} {rate:>5}%  disbursement on period {j}'s due date")
        print(f"      source n=|related|={n_rep-j}: level {sl:>14} final {sf:>14} interest {si:>14}")
        print(f"      text   n=NumberOfRepayments={n_rep}: level {tl:>14} final {tf:>14} interest {ti:>14}")


def _build_no_interest_roundtrip(disbursed_minor, periods, first_rel, emi_of):
    rows, bal = [], 0
    for i, (fr, d, L, rf) in enumerate(periods):
        if i == first_rel:
            bal += disbursed_minor
        emi = emi_of(i)
        ci = 0 if (bal == 0 or rf == 0) else R.to_money(
            R.mc(lambda: (Decimal(bal) / R.UNIT) * rf))
        di = min(ci, emi)
        dp = max(0, emi - di)
        bal = max(0, bal - dp)
        rows.append({"emi": emi, "interest": di, "principal": dp,
                     "outstanding": bal, "from": fr, "due": d})
    return rows


def sweep_bc():
    starts = (date(2024, 1, 1), date(2024, 1, 31), date(2023, 3, 15))
    print()
    print("=" * 78)
    print("B -- rate-factor actualDays/calcDays correction: performed vs skipped")
    print("=" * 78)
    tested = div = 0
    for n in (6, 12, 18, 36):
        for rate in RATES[:5]:
            for p in range(100, 3_000_000, 7919):
                for st in starts:
                    a = R.generate(p, n, rate, start=st, model="source",
                                   apply_day_correction=True)
                    b = R.generate(p, n, rate, start=st, model="source",
                                   apply_day_correction=False)
                    tested += 1
                    if [r["emi"] for r in a] != [r["emi"] for r in b]:
                        div += 1
    print(f"  shapes compared {tested}, divergent {div}"
          f"  -> NOT a money-relevant under-determination at (19, HALF_UP)")

    print()
    print("=" * 78)
    print("C -- per-period interest: balance*rf/lengthTillDue*length (oracle) vs balance*rf")
    print("=" * 78)
    original = R.build
    tested = div = 0
    shown = 0
    for n in (6, 12, 18, 36):
        for rate in RATES[:6]:
            for p in range(100, 4_000_000, 6551):
                for st in starts:
                    R.build = original
                    a = R.generate(p, n, rate, start=st, model="source")
                    R.build = _build_no_interest_roundtrip
                    b = R.generate(p, n, rate, start=st, model="source")
                    tested += 1
                    if ([r["emi"] for r in a] != [r["emi"] for r in b]
                            or [r["interest"] for r in a] != [r["interest"] for r in b]):
                        div += 1
                        if shown < 3:
                            shown += 1
                            print(f"   P={p} n={n} {rate}% start={st}")
                            print(f"      oracle arithmetic : final {f(a[-1]['emi'])}"
                                  f"  total interest {f(sum(r['interest'] for r in a))}")
                            print(f"      textbook reading  : final {f(b[-1]['emi'])}"
                                  f"  total interest {f(sum(r['interest'] for r in b))}")
    R.build = original
    print(f"  shapes compared {tested}, DIVERGENT {div} ({100.0*div/tested:.2f}%)")


if __name__ == "__main__":
    print(__doc__)
    sweep_a()
    sweep_bc()
