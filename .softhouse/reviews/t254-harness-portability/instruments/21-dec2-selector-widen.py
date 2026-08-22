#!/usr/bin/env python3
"""T254 reviewer SELF-CHECK: is instrument 20's selector too narrow?

P-76 addendum says check the SELECTOR before the conditions. Instrument 20
matched `conformance.sh` FOLLOWED BY a number. This widens to every line that
mentions conformance.sh AT ALL and prints those that contain any 3-4 digit
number anywhere on the line -- including the REVERSE form ("line 1152 of
conformance.sh") which instrument 20 cannot see.

Usage: 21-dec2-selector-widen.py <dec2.md>
"""
import re
import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()

FWD = re.compile(
    r"conformance\.sh(?:`|'|\"|\s)*(?::|\s+(?:at\s+)?lines?\s+|\s+L)\s*([0-9]+(?:\s*[-–,]\s*[0-9]+)*)"
)
ANYNUM = re.compile(r"\b[0-9]{3,4}\b")

mentions = [(i, ln) for i, ln in enumerate(lines, 1) if "conformance.sh" in ln]
print(f"WIDE population: lines mentioning conformance.sh = {len(mentions)}")

fwd_lines = {i for i, ln in mentions if FWD.search(ln)}
print(f"  of which instrument-20 (forward form) matched   = {len(fwd_lines)}")

suspects = []
for i, ln in mentions:
    if i in fwd_lines:
        continue
    nums = ANYNUM.findall(ln)
    if nums:
        suspects.append((i, nums, ln.strip()))

print(f"  UNMATCHED but carrying a 3-4 digit number       = {len(suspects)}")
print()
print("--- every unmatched mention that carries a number (manual adjudication) ---")
for i, nums, ln in suspects:
    print(f"DEC-2:{i}  nums={nums}")
    print(f"    {ln[:200]}")
print()
print("--- P-40: unmatched mentions with NO number at all (nothing to rot) ---")
n_clean = len(mentions) - len(fwd_lines) - len(suspects)
print(f"    {n_clean} lines skipped as un-numbered prose")
