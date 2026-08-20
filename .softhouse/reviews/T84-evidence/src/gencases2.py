from fractions import Fraction
from decimal import Decimal
import json

# SECOND PROBE: locate the n-boundary at 600% / B=1 and 300% / B=2 exactly,
# where B*a -> 1/2 from above and the gap crosses the precision-19 floor.
cases = []
def add(tag, rate, n, B):
    rid = "T84B-%s-R%s-N%d-B%d" % (tag, str(rate).replace('.', 'p'), n, B)
    cases.append((rid, rid.lower().replace('-', '_'), B, n, str(rate)))

for n in range(88, 122):
    add("NSW", "600.0", n, 1)
for n in range(170, 205):
    add("NSW", "300.0", n, 2)
# and the low-rate/long-term family, wider, to bound the region's true extent
for rate, ns in [("0.12", [480, 600]), ("1.2", [480, 600]), ("3.6", [480, 600])]:
    for n in ns:
        r = Fraction(Decimal(rate)) / 100 / 12
        a = r / (1 - (1 + r) ** (-n))
        t = int(Fraction(1, 2) / a)
        while (t + 1) * a < Fraction(1, 2): t += 1
        while t * a >= Fraction(1, 2) and t > 0: t -= 1
        for B in [t - 1, t, t + 1, t + 2]:
            if B >= 1: add("XL", rate, n, B)

pred = {}
for rid, tenant, B, n, rate in cases:
    r = Fraction(Decimal(rate)) / 100 / 12
    a = r / (1 - (1 + r) ** (-n))
    pred[rid] = {"rate": rate, "n": n, "B": B, "predictedFails": bool(Fraction(B) * a < Fraction(1, 2)),
                 "gap": float(Fraction(B) * a - Fraction(1, 2))}
json.dump(pred, open('/tmp/t84b-prediction.json', 'w'), indent=1, sort_keys=True)
java = ['        cases.add(prodDates("%s", "T84 second probe", LocalDate.of(2024, 1, 1), '
        'LocalDate.of(2024, 1, 1), new BigDecimal(%d).movePointLeft(2), %d, new BigDecimal("%s"), "%s"));'
        % (rid, B, n, rate, tenant) for rid, tenant, B, n, rate in cases]
open('/tmp/t84b-cases.java', 'w').write("\n".join(java) + "\n")
open('/tmp/t84b-ids.json', 'w').write(json.dumps([c[0] for c in cases]))
print("cases:", len(cases))
