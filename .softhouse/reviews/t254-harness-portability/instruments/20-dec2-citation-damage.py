#!/usr/bin/env python3
"""T254 reviewer instrument: quantify the DEC-2 citation damage a shifting
conformance.sh diff would do.

P-75/P-80: pure python3 `re` over bytes read from an explicit path. No shell
grep, no rg, no `git grep -E` with \\b. Every non-match is a real measured
negative because we count over an enumerated population, not a filtered stream.

Usage: 20-dec2-citation-damage.py <dec2.md> <label> <shift_from_line> <shift_by>
"""
import re
import sys

path, label, shift_from, shift_by = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])

text = open(path, encoding="utf-8").read()
lines = text.splitlines()

# A citation into the harness is any mention of conformance.sh followed by a
# line number. Observed forms in this repo's ADRs:
#   conformance.sh:1481
#   conformance.sh:1481-1484
#   conformance.sh:1481,1482,1483
#   .softhouse/conformance.sh:1481
#   `conformance.sh` line 1481          (prose form)
# We match the token then harvest the numeric run that follows.
CITE = re.compile(
    r"conformance\.sh"           # the file
    r"(?:`|'|\"|\s)*"            # optional closing backtick / quote / space
    r"(?::|\s+(?:at\s+)?lines?\s+|\s+L)"   # separator: ':' or ' line(s) ' or ' L'
    r"\s*"
    r"([0-9]+(?:\s*[-–,]\s*[0-9]+)*)"  # the number run
)

NUM = re.compile(r"[0-9]+")

hits = []          # (docline, matchtext, [linenumbers])
for i, ln in enumerate(lines, 1):
    for m in CITE.finditer(ln):
        nums = [int(x) for x in NUM.findall(m.group(1))]
        hits.append((i, m.group(0).strip(), nums))

total_cites = len(hits)
total_numbers = sum(len(n) for _, _, n in hits)

rotted_cites = 0
rotted_numbers = 0
for _, _, nums in hits:
    bad = [n for n in nums if n >= shift_from]
    if bad:
        rotted_cites += 1
    rotted_numbers += len(bad)

print("=" * 74)
print(f"DEC-2 CITATION DAMAGE  --  {label}")
print(f"document: {path}  ({len(lines)} lines)")
print(f"hypothetical edit: insert {shift_by:+d} lines at conformance.sh line {shift_from}")
print("=" * 74)
print(f"TERM-1  conformance.sh line-citations in the document ....... {total_cites}")
print(f"TERM-2  distinct line NUMBERS inside those citations ........ {total_numbers}")
print(f"TERM-3  citations containing >=1 number at/below line {shift_from} .. {rotted_cites}")
print(f"TERM-4  individual line NUMBERS that would rot .............. {rotted_numbers}")
if total_numbers:
    print(f"        -> {100.0*rotted_numbers/total_numbers:.1f}% of harness line numbers rot")
print()
print("--- every citation, with rot verdict ---")
for docline, txt, nums in hits:
    bad = [n for n in nums if n >= shift_from]
    verdict = f"ROT ({','.join(str(n) for n in bad)} -> {','.join(str(n+shift_by) for n in bad)})" if bad else "ok"
    print(f"  DEC-2:{docline:<5} {txt:<44} {verdict}")
print()
print(f"--- P-40 SKIPPED: prose mentions of conformance.sh with NO line number ---")
bare = 0
for i, ln in enumerate(lines, 1):
    n_tok = ln.count("conformance.sh")
    n_cit = len(CITE.findall(ln))
    if n_tok > n_cit:
        bare += n_tok - n_cit
print(f"  {bare} un-numbered mentions (not counted as rot; nothing to rot)")
print("=" * 74)
