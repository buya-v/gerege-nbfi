#!/usr/bin/env python3
"""T100 — generate the case list and the registered prediction for the T100 discriminator probe.

Writes:
  prediction.json                 predicted fails/family per case (registered before the run)
  /tmp/t100-cases.java            the cases.add(...) block spliced into CaptureT100.java
  /tmp/t100-ids.json              the exact id list run-t100.sh requires the capture to carry

Order is deliberately scrambled relative to any natural sweep order, and every tenant id differs
from T83's and T84's, so that a reproduction here is not a reproduction of their ordering.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# (id-tail, rate, n, principal in MINOR UNITS, predicted fails, predicted family, note)
CASES = [
    ("FAMB-R600p0-N200-B1",  "600.0", 200, 1,         True,  "B", "T84 measured"),
    ("FAMA-R3p6-N360-B110",  "3.6",   360, 110,       False, None, "T84 measured clean"),
    ("FAMB-R600p0-N104-B1",  "600.0", 104, 1,         True,  "B", "T84 measured"),
    ("CTRL-R21p6-N12-B120000000", "21.6", 12, 120000000, False, None, "ordinary MNT 1,200,000 loan"),
    ("FAMB-R600p0-N103-B1",  "600.0", 103, 1,         False, None, "T84 measured clean"),
    ("FAMA-R3p6-N360-B109",  "3.6",   360, 109,       True,  "A", "T84 measured; MNT 1.09"),
    ("FAMB-R600p0-N121-B1",  "600.0", 121, 1,         True,  "B", "T84's top swept n"),
    ("FAMA-R21p6-N6-B2",     "21.6",  6,   2,         True,  "A", "T75/T83 measured"),
    ("FAMB-R600p0-N150-B1",  "600.0", 150, 1,         True,  "B", "T84 measured"),
    ("FAMA-R21p6-N6-B3",     "21.6",  6,   3,         False, None, "T83 measured clean"),
    ("FAMB-R600p0-N108-B1",  "600.0", 108, 1,         True,  "B", "T84 measured"),
    ("FAMB-R600p0-N122-B1",  "600.0", 122, 1,         True,  "B", "EXTRAPOLATION above T84's top"),
    ("FAMB-R600p0-N250-B1",  "600.0", 250, 1,         True,  "B", "EXTRAPOLATION above T84's top"),
    ("FAMA-R0p12-N600-B291", "0.12",  600, 291,       True,  "A", "T84 measured; MNT 2.91"),
    ("FAMA-R0p12-N600-B292", "0.12",  600, 292,       False, None, "T84 measured clean"),
]

pred, java, ids = {}, [], []
for tail, rate, n, b, fails, fam, note in CASES:
    rid = "T100-" + tail
    ids.append(rid)
    pred[rid] = {"rate": rate, "n": n, "B_minor": b, "predictedFails": fails,
                 "predictedFamily": fam, "basis": note}
    java.append(
        '        cases.add(prodDates("%s", "T100 discriminator probe — %s", '
        'LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(%d).movePointLeft(2), '
        '%d, new BigDecimal("%s"), "%s"));' % (rid, note, b, n, rate, rid.lower().replace('-', '_')))

json.dump(pred, open(os.path.join(ROOT, 'prediction.json'), 'w'), indent=1, sort_keys=True)
open('/tmp/t100-cases.java', 'w').write("\n".join(java) + "\n")
json.dump(ids, open('/tmp/t100-ids.json', 'w'))
print("cases: %d" % len(CASES))
