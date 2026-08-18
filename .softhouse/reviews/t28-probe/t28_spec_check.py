#!/usr/bin/env python3
"""T28 self-check on DEC-1 revision 4 section 4.3.1.

WHAT THIS IS. The EMI re-adjust loop body is transcribed here EXACTLY as
revision 4 section 4.3.1 states it -- steps 1 through 8, in PURE INTEGER MINOR
UNITS, no float and no Decimal anywhere in the loop -- and checked against the
three oracle observations already COMMITTED by task T23 under
`.softhouse/reviews/t23-probe/`. Its purpose is to demonstrate that the
specification as WRITTEN is sufficient to determine the money, which is the
whole point of P0-T26-1.

NOT AN OBSERVATION, NOT A VECTOR. No live oracle is reachable in this sandbox
(no Docker, no PostgreSQL). Nothing here was measured; the three expected
triples are quoted from T23's committed captures and are labelled as such.
Nothing in this file may be promoted to the vector store.

The surrounding schedule machinery (rate factor, level EMI, interest-first
split, final-period residual) is imported UNCHANGED from T26's independent
model `.softhouse/reviews/t26-probe/t26_rederive.py`, so that the only thing
under test is the loop text T28 wrote.

Run: python3 .softhouse/reviews/t28-probe/t28_spec_check.py
"""
import sys
from decimal import Decimal
sys.path.insert(0, "/home/user/wt-T28/.softhouse/reviews/t26-probe")
import t26_rederive as R

CENT = Decimal("0.01")
def to_minor(d):  # exact: every row value is already at 2dp
    v = (d / CENT)
    assert v == v.to_integral_value(), v
    return int(v)
def to_major(i):
    return Decimal(i) * CENT

def rebuild_minor(principal, rfs, lengths, level_minor):
    rows = R.rebuild(Decimal(principal), rfs, [to_major(level_minor)] * len(rfs), lengths)
    return [to_minor(r["emi"]) for r in rows], rows

def loop_per_spec(principal, rfs, lengths, rows):
    """Steps 1-8 of DEC-1 rev4 sec 4.3.1, integer minor units only."""
    emis = [to_minor(r["emi"]) for r in rows]
    cur_rows = rows
    n = len(emis)
    adjust_counter = 1
    while True:
        # 1
        if n < 2:
            break
        original = emis[n - 2]
        emi_difference = emis[n - 1] - original
        # 2
        lower_half = n // 2
        if not (lower_half > 0 and emi_difference != 0
                and abs(emi_difference) * 100 > lower_half * 10 ** 2):
            break
        # 3  uncountablePeriods == 0 (nothing paid)
        d = max(1, n - 0)
        sign = 1 if emi_difference > 0 else -1
        adjustment = sign * ((2 * abs(emi_difference) + d) // (2 * d))
        # 4  (installment-multiple pass is the identity in the graded domain)
        adjusted = original + adjustment
        # 5
        if adjusted == original:
            break
        # 6
        trial_emis, trial_rows = rebuild_minor(principal, rfs, lengths, adjusted)
        # 7
        new_difference = trial_emis[n - 1] - trial_emis[n - 2]
        if not (abs(new_difference) < abs(emi_difference)):
            break
        # 8
        emis, cur_rows = trial_emis, trial_rows
        adjust_counter += 1
        if adjust_counter > 3:
            break
    return emis, cur_rows

def run(principal, n, rate, expect_level, expect_final, expect_interest):
    periods = R.due_dates(R.date(2024, 1, 1), R.date(2024, 1, 1), n)
    lengths = [(dd - f).days for f, dd in periods]
    rfs = [R.rate_factor(rate, L, L) for L in lengths]
    level = R.level_emi(Decimal(principal), rfs)
    rows = R.rebuild(Decimal(principal), rfs, [level] * n, lengths)
    emis, rows = loop_per_spec(principal, rfs, lengths, rows)
    interest = sum((r["interest"] for r in rows), Decimal(0))
    ok = (to_major(emis[0]) == Decimal(expect_level)
          and to_major(emis[-1]) == Decimal(expect_final)
          and interest == Decimal(expect_interest))
    print(f"MNT {principal} / {n} x {rate}%: level {to_major(emis[0])}, "
          f"final {to_major(emis[-1])}, total interest {interest}  -> "
          f"{'MATCH' if ok else 'MISMATCH'} vs committed T23 observation "
          f"({expect_level} / {expect_final} / {expect_interest})")
    return ok

a = run(1014632, 6, "7.0", "172574.64", "172574.62", "20815.82")
b = run(127704, 36, "16.8", "4540.30", "4540.06", "35746.56")
c = run(100, 6, "7.0", "17.01", "17.00", "2.05")
print("ALL MATCH" if (a and b and c) else "FAILED")
