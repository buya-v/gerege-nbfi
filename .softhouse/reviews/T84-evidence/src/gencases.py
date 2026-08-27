from fractions import Fraction
from decimal import Decimal
import json

def a_of(rate_str, n):
    r = Fraction(Decimal(rate_str)) / 100 / 12
    if r == 0:
        return Fraction(1, n)
    return r / (1 - (1 + r) ** (-n))

def thr(rate_str, n):
    """largest integer B with B*a < 1/2  (0 if none)"""
    a = a_of(rate_str, n)
    Bs = Fraction(1, 2) / a
    B = int(Bs)
    while B * a >= Fraction(1, 2) and B > 0:
        B -= 1
    while (B + 1) * a < Fraction(1, 2):
        B += 1
    return B

cases = []   # (id, tenant, principal_minor, n, rate_str, purpose_tag)

def add(tag, rate, n, B):
    rid = "T84-%s-R%s-N%d-B%d" % (tag, str(rate).replace('.', 'p'), n, B)
    cases.append((rid, rid.lower().replace('-', '_'), B, n, str(rate), tag))

# 2. tenant/order independence re-probe of T83 boundary cells (different tenant ids, reversed order)
REPROBE = [("21.6", 6, 2), ("21.6", 6, 3), ("7.0", 56, 23), ("7.0", 56, 24),
           ("36.0", 12, 4), ("36.0", 12, 5), ("16.8", 24, 10), ("16.8", 24, 11),
           ("21.6", 2, 1), ("21.6", 56, 17), ("21.6", 56, 18), ("36.0", 3, 1)]
for rate, n, B in reversed(REPROBE):
    add("RP", rate, n, B)

# 4. far above the swept top -- does the region reappear?
for rate, n in [("21.6", 6), ("7.0", 56), ("36.0", 12), ("16.8", 36)]:
    for B in [30, 50, 100, 1000, 10000, 100000]:
        add("FAR", rate, n, B)

# 5. un-sampled RATES
for rate in ["1.2", "3.6", "12.0", "48.0", "96.0"]:
    for n in [6, 12, 56]:
        t = thr(rate, n)
        for B in range(max(1, t - 2), t + 4):
            add("RATE", rate, n, B)

# 6. un-sampled TERMS at a sampled rate
for n in [1, 5, 7, 30, 60, 120, 240, 360]:
    t = thr("21.6", n)
    for B in range(max(1, t - 2), t + 4):
        add("TERM", "21.6", n, B)

# 7. the boundedness attack: low rate x long term -> is the region really below MNT 0.25?
for rate in ["0.12", "1.2", "3.6"]:
    for n in [120, 240, 360]:
        t = thr(rate, n)
        for B in range(max(1, t - 2), t + 4):
            add("LONG", rate, n, B)

# 8. near-tie family: r = 1/(2B) exactly, so B*a -> 1/2 from ABOVE as n grows
for n in [60, 90, 108, 120, 150, 200]:
    for B in [1, 2]:
        add("TIE", "600.0", n, B)
for n in [100, 150, 175, 196, 220, 260]:
    for B in [1, 2, 3]:
        add("TIE", "300.0", n, B)

# predictions from the closed form, computed BEFORE the probe runs
pred = {}
for rid, tenant, B, n, rate, tag in cases:
    pred[rid] = {"rate": rate, "n": n, "B": B,
                 "predictedFails": bool(Fraction(B) * a_of(rate, n) < Fraction(1, 2)),
                 "BtimesA": float(Fraction(B) * a_of(rate, n))}
json.dump(pred, open('/tmp/t84-prediction.json', 'w'), indent=1, sort_keys=True)

print("cases:", len(cases))
print("thresholds (largest failing B by closed form):")
for rate in ["0.12", "1.2", "3.6", "21.6"]:
    print(" ", rate, {n: thr(rate, n) for n in [6, 12, 56, 120, 240, 360]})

java = []
for rid, tenant, B, n, rate, tag in cases:
    java.append('        cases.add(prodDates("%s", "T84 independent re-probe (%s): MNT %s / %d x %s%%",'
                ' LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(%d).movePointLeft(2),'
                ' %d, new BigDecimal("%s"), "%s"));' % (rid, tag, Decimal(B).scaleb(-2), n, rate, B, n, rate, tenant))
open('/tmp/t84-cases.java', 'w').write("\n".join(java) + "\n")
open('/tmp/t84-ids.json', 'w').write(json.dumps([c[0] for c in cases]))
