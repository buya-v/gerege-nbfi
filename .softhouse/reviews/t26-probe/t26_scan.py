#!/usr/bin/env python3
"""T26: scan for in-graded-domain shapes where two loop bodies both consistent
with DEC-1 rev 3's TEXT disagree on money. Re-derivation only; no live oracle."""
from decimal import Decimal
from datetime import date
from t26_rederive import (rate_factor, level_emi, rebuild, should_be_adjusted,
                          due_dates, money, mc)
from t26_variants import loop, VARIANTS

names = list(VARIANTS)
hits = {n: 0 for n in names[1:]}
fired = 0
examples = {n: None for n in names[1:]}
for n_per, pct in [(6, "7.0"), (12, "16.8"), (18, "18.5"), (24, "21.6"), (36, "16.8"), (60, "7.0")]:
    per = due_dates(date(2024, 1, 1), date(2024, 1, 1), n_per)
    lengths = [(d - f).days for f, d in per]
    rfs = [rate_factor(pct, L, L) for L in lengths]
    for p in range(100000, 100000 + 4000):
        P = Decimal(p)
        base = rebuild(P, rfs, [level_emi(P, rfs)] * n_per, lengths)
        f, d0, _ = should_be_adjusted(base)
        if not f:
            continue
        fired += 1
        ref = loop(P, rfs, lengths, base, *VARIANTS[names[0]])
        refkey = (ref[0]["emi"], ref[-1]["emi"])
        for nm in names[1:]:
            alt = loop(P, rfs, lengths, base, *VARIANTS[nm])
            if (alt[0]["emi"], alt[-1]["emi"]) != refkey:
                hits[nm] += 1
                if examples[nm] is None:
                    examples[nm] = (p, n_per, pct, refkey, (alt[0]["emi"], alt[-1]["emi"]))
print(f"shapes scanned where the guard FIRES: {fired}")
for nm in names[1:]:
    print(f"\n{nm}\n   disagrees with the oracle body on {hits[nm]} of them")
    if examples[nm]:
        p, n_per, pct, r, a = examples[nm]
        print(f"   first: MNT {p} / {n_per} x {pct}%  oracle-body {r}  vs  variant {a}")
