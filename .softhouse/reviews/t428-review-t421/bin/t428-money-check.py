#!/usr/bin/env python3
"""T428 -- prove that no money value in the ledger vectors is or ever becomes a
float, WITHOUT letting one become a float in the act of checking.

  * json is decoded with parse_float=str AND parse_int=str, so every scalar
    arrives as a Python str exactly as it appears in the file;
  * a money cell is admitted only if its characters are an optional '-' followed
    by decimal digits -- checked with str.isdigit(), never with int(), float() or
    Decimal();
  * the residue is read by INTEGER STRING SURGERY: the last two characters of the
    minor-unit string.
"""
import json, os, sys

ROOT = sys.argv[1]
VDIR = os.path.join(ROOT, ".softhouse/vectors/ledger")

MONEYISH = ("minor", "amount", "margin", "total", "balance")

def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + "." + k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, path + "[%d]" % i)
    else:
        yield path, node

bad, checked = [], 0
residues = {}
for name in sorted(os.listdir(VDIR)):
    if not name.endswith(".json"):
        continue
    with open(os.path.join(VDIR, name)) as fh:
        doc = json.load(fh, parse_float=str, parse_int=str)
    for p, v in walk(doc):
        leaf = p.rsplit(".", 1)[-1].split("[")[0].lower()
        if not any(m in leaf for m in MONEYISH):
            continue
        if not isinstance(v, str):
            bad.append((name, p, repr(v), "NOT A STRING after parse_*=str"))
            continue
        s = v[1:] if v.startswith("-") else v
        if not s.isdigit():
            bad.append((name, p, v, "NOT AN INTEGER STRING -- a decimal point or exponent"))
            continue
        checked += 1
        if len(s) >= 2:
            residues.setdefault(s[-2:], 0)
            residues[s[-2:]] += 1

print("T428 MONEY CELL CHECK -- integer string surgery only")
print("root:", ROOT)
print("money-shaped leaves checked:", checked)
print("OFFENDERS:", len(bad))
for row in bad:
    print("   ", row)
print()
print("minor-unit RESIDUES (last two characters), by frequency:")
for r in sorted(residues, key=lambda k: (-residues[k], k)):
    print("   residue %s x%d" % (r, residues[r]))
sys.exit(1 if bad else 0)
