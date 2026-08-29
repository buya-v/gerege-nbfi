#!/usr/bin/env python3
"""T428 -- MONEY CHECK, second pass, scoped to the GRADED money cells.

SCOPE. A graded money cell in this schema is a `*_minor` field. Its sibling
`*_major_text` / `observed_amount_texts` fields hold the ORACLE'S RAW TEXT
byte-for-byte, as STRINGS, because T186 s7 A4 forbids re-scaling an observation:
they are deliberately NOT integers and are not asserted to be. They are reported
separately so the distinction is stated rather than assumed.

Nothing here calls int(), float() or Decimal(). json is decoded with
parse_float=str and parse_int=str, integrality is str.isdigit(), and the residue
is the last two characters of the string.
"""
import json, os, sys

ROOT = sys.argv[1]
VDIR = os.path.join(ROOT, ".softhouse/vectors/ledger")


def walk(n, p=""):
    if isinstance(n, dict):
        for k, v in n.items():
            yield from walk(v, p + "." + k)
    elif isinstance(n, list):
        for i, v in enumerate(n):
            yield from walk(v, p + "[%d]" % i)
    else:
        yield p, n


print("T428 MONEY CELL CHECK -- *_minor fields only, integer string surgery only")
print("root:", ROOT)
print()
bad, ok, raw, res = [], [], [], {}
for name in sorted(os.listdir(VDIR)):
    if not name.endswith(".json"):
        continue
    with open(os.path.join(VDIR, name)) as fh:
        doc = json.load(fh, parse_float=str, parse_int=str)
    for p, v in walk(doc):
        leaf = p.rsplit(".", 1)[-1].split("[")[0]
        if leaf.endswith("_minor"):
            if not isinstance(v, str):
                bad.append((name, p, repr(v), "NOT A STRING after parse_*=str"))
                continue
            if v == "":
                ok.append((name, p, v, "ABSENT (empty string)"))
                continue
            s = v[1:] if v.startswith("-") else v
            if not s.isdigit():
                bad.append((name, p, v, "NOT AN INTEGER STRING"))
                continue
            ok.append((name, p, v, "integer minor units"))
            if len(s) >= 2:
                res[s[-2:]] = res.get(s[-2:], 0) + 1
        elif "major_text" in leaf or "amount_texts" in leaf:
            raw.append((name, p, v))

print("*_minor leaves inspected   :", len(ok) + len(bad))
print("   integer or absent       :", len(ok))
print("   NOT integer minor units :", len(bad))
for r in bad:
    print("      OFFENDER", r)
print()
print("minor-unit residues (last two characters of the integer string):")
for k in sorted(res, key=lambda x: (-res[x], x)):
    print("   residue %s x%d" % (k, res[k]))
print()
print("raw oracle major-unit TEXT fields (strings, never integers):", len(raw))
print()
print("EVERY occurrence of the token 100.125 in the ledger store, with its field:")
for name in sorted(os.listdir(VDIR)):
    if not name.endswith(".json"):
        continue
    with open(os.path.join(VDIR, name)) as fh:
        doc = json.load(fh, parse_float=str, parse_int=str)
    for p, v in walk(doc):
        if isinstance(v, str) and "100.125" in v and len(v) < 24:
            print("   %-46s %-44s %r" % (name[:46], p, v))
print()
print("VERDICT:", "CLEAN -- every *_minor field is an integer string or absent"
      if not bad else "OFFENDERS PRESENT")
sys.exit(1 if bad else 0)
