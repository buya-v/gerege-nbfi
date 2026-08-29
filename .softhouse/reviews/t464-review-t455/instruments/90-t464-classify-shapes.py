"""T464 — the F-6 MATERIAL/PROSE classifier, driven on nine shapes including its blind spot.

T455's controls (h)-(k) drive four shapes. This drives those four plus five more, to find where
the "is it whitespace?" discriminator stops discriminating. The function is LIFTED from the
shipped adjudicator by source extraction, not re-implemented.

    python3 90-t464-classify-shapes.py <path-to-adjudicate-section1.py>

The adjudicator's path is an ARGUMENT, not a literal.

EXIT 0  every shape classified as recorded.  EXIT 1  one did not.  EXIT 3  REFUSED.
"""
import json
import re
import sys

src = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"def classify_occurrences.*?\n    return material, prose\n", src, re.S)
if not m:
    print("REFUSED: classify_occurrences is not in this file; nothing to drive.")
    sys.exit(3)
ns = {"json": json}
exec(m.group(0), ns)
c = ns["classify_occurrences"]
T = "paymentChannelToFundSourceMappings"

# (label, fixture, expected bucket)   MATERIAL | PROSE | NEITHER
CASES = [
    ("(h) token as an object KEY", '{"expected":{"%s":[1,2]}}' % T, "MATERIAL"),
    ("(i) identifier-shaped VALUE", '{"provenance":{"capture_ref":"A2-99-%s"}}' % T, "MATERIAL"),
    ("(j) inside a PROSE sentence", '{"evidence":"product 63 has no %s at all"}' % T, "PROSE"),
    ("(k) file that will not parse as JSON", "# a shell fragment naming %s\n" % T, "MATERIAL"),
    ("    top-level bare string identifier", '"%s"' % T, "MATERIAL"),
    ("    JSON list of identifiers", '["%s"]' % T, "MATERIAL"),
    ("    empty file", "", "NEITHER"),
    ("    identifier value + ONE TRAILING SPACE", '{"provenance":{"capture_ref":"A2-99-%s "}}' % T,
     "PROSE"),
    ("    identifier value + an escaped newline", '{"provenance":{"capture_ref":"A2-99-%s\\n"}}' % T,
     "PROSE"),
]

print("############ T464 — THE F-6 STRUCTURAL CLASSIFIER, NINE SHAPES")
bad = []
for label, fixture, want in CASES:
    mm, pp = c(fixture, T)
    got = "MATERIAL" if mm else ("PROSE" if pp else "NEITHER")
    flag = "OK  " if got == want else "BAD "
    if got != want:
        bad.append(label)
    print("  %s %-44s -> %-8s  material=%s prose=%s" % (flag, label, got, mm, pp))
print()
print("  READ THE LAST TWO ROWS. Materiality turns on `any(ch.isspace() for ch in node)`, so an")
print("  identifier-shaped value with ONE trailing space is demoted to PROSE, i.e. IMMATERIAL.")
print("  It is a weak attack — a ref with a space in it is not a ref the harness compares — but")
print("  P-29 asks for the edit that should trip it and won't to be PUBLISHED beside the")
print("  classifier, and it is not. State the limit; it costs one comment.")
print()
if bad:
    print("T464 CLASSIFIER SHAPES: %d shape(s) did not classify as recorded: %s" % (len(bad), bad))
    sys.exit(1)
print("T464 CLASSIFIER SHAPES: all nine as recorded. EXIT 0")
