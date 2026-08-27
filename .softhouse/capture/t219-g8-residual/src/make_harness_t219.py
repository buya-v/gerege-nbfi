#!/usr/bin/env python3
"""T219 — build CaptureT219.java from T223's committed CaptureT223.java by replacing ONLY the
probe-cell block and the class/pass names. Every attestation field, every emitted column and every
emission rule of the T223 rig (which is pass 3g's rig) is preserved byte-for-byte, so the two rig
calibrations P-CAL-ZPA / P-CAL-ZPB remain meaningful.

No floating point anywhere; the principals are written as BigDecimal(minorUnits).movePointLeft(2),
exactly as T223 wrote them, so no decimal string is ever parsed through a double.
"""
import json
import re
import sys

SRC = sys.argv[1]
CELLS = sys.argv[2]
DST = sys.argv[3]

src = open(SRC).read()

cells = json.load(open(CELLS))
cells = [c for c in cells if c["id"].startswith("T219-")]
# Emission order deliberately SCRAMBLED so predicted-family-B and predicted-rescued cells
# interleave: a rig artefact that tracked emission position could not reproduce the registered
# prediction. This order is fixed here, in the harness builder, and does not consult the prediction.
ORDER = ["T219-R600p0-N3000-B4501", "T219-R600p0-N104-B1", "T219-R600p0-N3000-B2999",
         "T219-R600p0-N103-B1", "T219-R600p0-N3000-B1001", "T219-R600p0-N3000-B4499",
         "T219-R600p0-N108-B1", "T219-R600p0-N3000-B3001", "T219-R600p0-N3000-B1999"]
assert sorted(ORDER) == sorted(c["id"] for c in cells), "order list must cover every T219 cell"
by_id = {c["id"]: c for c in cells}

lines = []
for cid in ORDER:
    c = by_id[cid]
    tenant = cid.lower().replace("-", "_").replace("t219_", "t219_")
    purpose = ("T219 G-8 residual-record probe - %s %% p.a., %s minor units, n = %d. "
               "This harness asserts nothing and predicts nothing; the registered prediction is in "
               "../PREDICTION.md, committed in an ANCESTOR commit." % (c["rate"], c["bMinor"], c["n"]))
    lines.append(
        '        cases.add(prodDates("%s", "%s", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), '
        'new BigDecimal(%d).movePointLeft(2), %d, new BigDecimal("%s"), "%s"));'
        % (cid, purpose, c["bMinor"], c["n"], c["rate"], tenant))

block = "\n".join(lines)

start = src.index("        // ---- T229 PROBE CELLS ----")
end = src.index("        StringBuilder sb = new StringBuilder();")
header = ("        // ---- T219 PROBE CELLS ----\n"
          "        // Emission order is deliberately SCRAMBLED so that predicted-family-B and\n"
          "        // predicted-rescued cells interleave. Tenant ids are all new (t219_*), disjoint from\n"
          "        // every previous pass. THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING.\n")
src = src[:start] + header + block + "\n\n" + src[end:]

src = src.replace("CaptureT229", "CaptureT219")
src = src.replace('"harness\\": \\"CaptureT219.java', '"harness\\": \\"CaptureT219.java')
open(DST, "w").write(src)
print("wrote", DST, len(src), "bytes;", len(ORDER), "probe cells")
