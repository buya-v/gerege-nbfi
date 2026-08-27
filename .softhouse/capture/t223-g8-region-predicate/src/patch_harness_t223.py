#!/usr/bin/env python3
"""T223 — derive CaptureT223.java from T116's harness by (a) renaming the class and (b) replacing
the case list. Every attestation field, emitted column and emission rule of T116's rig (itself pass
3g's rig) is preserved byte-for-byte, which is what makes the two rig calibrations meaningful.

THE HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. The prediction lives in ../PREDICTION.md and
../prediction.json, committed in an ANCESTOR commit of the one carrying the capture.
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
text = open(src).read()
text = text.replace("CaptureT116", "CaptureT223")

CASES = '''        // ---- T223 PROBE CELLS ----
        // Emission order is deliberately SCRAMBLED so that predicted-family-B and predicted-clean
        // cells interleave: a rig artefact that tracked emission position could not reproduce the
        // registered prediction. Tenant ids are all new (t223_*), disjoint from every previous pass.
        // Registered predictions are in ../PREDICTION.md; this harness does not know them.
        cases.add(prodDates("T223-R300p0-N800-B2", "T223 G-8 region probe - 300.0 %% p.a., MNT 0.02, n = 800. 300.0 %% has never been asked above n = 260 by anyone.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 800, new BigDecimal("300.0"), "t223_r300p0_n800_b2"));
        cases.add(prodDates("T223-R36p0-N1323-B50", "T223 G-8 region probe - 36.0 %% p.a., MNT 0.50, n = 1323. 36.0 %% has never been asked above n = 600 by anyone.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(50).movePointLeft(2), 1323, new BigDecimal("36.0"), "t223_r36p0_n1323_b50"));
        cases.add(prodDates("T223-R21p6-N3000-B250", "T223 G-8 region probe - 21.6 %% p.a., MNT 2.50, n = 3000. 21.6 %% has never been asked above n = 56 by anyone.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(250).movePointLeft(2), 3000, new BigDecimal("21.6"), "t223_r21p6_n3000_b250"));
        cases.add(prodDates("T223-R36p0-N1324-B50", "T223 G-8 region probe - 36.0 %% p.a., MNT 0.50, n = 1324.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(50).movePointLeft(2), 1324, new BigDecimal("36.0"), "t223_r36p0_n1324_b50"));
        cases.add(prodDates("T223-R300p0-N1200-B2", "T223 G-8 region probe - 300.0 %% p.a., MNT 0.02, n = 1200.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 1200, new BigDecimal("300.0"), "t223_r300p0_n1200_b2"));
        cases.add(prodDates("T223-R36p0-N1500-B50", "T223 G-8 region probe - 36.0 %% p.a., MNT 0.50, n = 1500.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(50).movePointLeft(2), 1500, new BigDecimal("36.0"), "t223_r36p0_n1500_b50"));
        cases.add(prodDates("T223-R300p0-N500-B2", "T223 G-8 region probe - 300.0 %% p.a., MNT 0.02, n = 500.", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 500, new BigDecimal("300.0"), "t223_r300p0_n500_b2"));

'''

start = text.index("        // ---- T84 SECOND PROBE ----")
end = text.index("        StringBuilder sb = new StringBuilder();")
text = text[:start] + CASES.replace("%%", "%") + text[end:]
text = text.replace('"harness": \\"CaptureT223.java\\"', '"harness": \\"CaptureT223.java\\"')
assert "T223-R36p0-N1324-B50" in text
assert "T116-FAMB" not in text
open(dst, "w").write(text)
print("wrote", dst, len(text), "bytes")
