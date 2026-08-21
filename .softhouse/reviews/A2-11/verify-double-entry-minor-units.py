#!/usr/bin/env python3
"""A2-11 (d) — verify the 2,450,000 double-entry claim IN INTEGER MINOR UNITS.

A2-7 compared as `Decimal`. CLAUDE.md's non-negotiable is INTEGER MINOR UNITS, so this
re-does the sum with Python `int` only: the oracle's decimal string is scaled to minor
units (MNT, ISO 4217 numeric 496, minor unit 2) by exact string arithmetic, and any
sub-minor-unit residue is a HARD FAILURE rather than something rounded away.

There is no float and no Decimal in the balance arithmetic here — only `int`. `Decimal`
appears once, as `parse_float=`, purely to stop `json` from ever constructing a double;
the values used are taken from the ORIGINAL BYTES via the JSON text, not from a parsed
number.

Reads my own live re-observation (obs/a2-11-get-je-loan5.json) and A2-7's committed
capture (out/A2-235-je-after-recovery.json) and requires them to agree.
"""
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = HERE.parents[1] / "capture" / "tierA-a2" / "out"
MINOR = 2                      # MNT minor unit, ISO 4217 numeric 496
fails = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        fails.append(label)


def to_minor_units(text):
    """'1200000.000000' -> 120000000 (int). Refuses anything with sub-minor-unit residue.

    Pure string/int arithmetic — the value never becomes a float or a Decimal.
    """
    m = re.fullmatch(r"(-?)(\d+)(?:\.(\d*))?", text.strip())
    if not m:
        raise ValueError("not a plain decimal literal: %r" % text)
    sign, whole, frac = m.group(1), m.group(2), (m.group(3) or "")
    kept, dropped = frac[:MINOR], frac[MINOR:]
    if dropped.strip("0"):
        raise ValueError("SUB-MINOR-UNIT RESIDUE in %r — %r digits below the minor unit"
                         % (text, dropped))
    kept = (kept + "0" * MINOR)[:MINOR]
    v = int(whole) * (10 ** MINOR) + int(kept)
    return -v if sign else v


def entries(path):
    """Pull (id, side, amount-as-TEXT) straight out of the JSON bytes."""
    raw = path.read_bytes().decode("utf-8")
    doc = json.loads(raw, parse_float=Decimal)
    rows = doc["pageItems"] if isinstance(doc, dict) and "pageItems" in doc else doc
    out = []
    for r in rows:
        # take the amount from the RAW TEXT for this entry id, so no number type is
        # involved at any point
        mm = re.search(r'"id"\s*:\s*%d\b.*?"amount"\s*:\s*(-?[0-9.]+)' % r["id"], raw, re.S)
        amt_text = mm.group(1) if mm else str(r["amount"])
        out.append((r["id"], r["entryType"]["value"], amt_text, r["glAccountCode"]))
    return out


for label, path in [("A2-7's committed A2-235", CAP / "A2-235-je-after-recovery.json"),
                    ("A2-11's live re-observation", HERE / "obs" / "a2-11-get-je-loan5.json")]:
    print("=== %s (%s) ===" % (label, path.name))
    try:
        rows = entries(path)
    except Exception as exc:                     # NAMED, not swallowed (P-40)
        check("could read %s" % path.name, False, repr(exc))
        continue
    debit = credit = 0
    residue_errors = []
    for eid, side, amt_text, glcode in rows:
        try:
            minor = to_minor_units(amt_text)
        except ValueError as exc:
            residue_errors.append((eid, amt_text, str(exc)))
            continue
        print("    je#%-4d %-6s %14s -> %12d minor units  gl %s" % (eid, side, amt_text, minor, glcode))
        if side == "DEBIT":
            debit += minor
        elif side == "CREDIT":
            credit += minor
        else:
            residue_errors.append((eid, side, "unknown entryType"))
    print("    entries: %d   DEBIT total = %d minor units   CREDIT total = %d minor units"
          % (len(rows), debit, credit))
    check("%s — every amount is a WHOLE number of minor units (no sub-minor residue)" % label,
          not residue_errors, str(residue_errors))
    check("%s — DEBIT == CREDIT in INTEGER minor units" % label, debit == credit,
          "debit=%d credit=%d delta=%d" % (debit, credit, debit - credit))
    check("%s — both sides are exactly 245,000,000 minor units == MNT 2,450,000" % label,
          debit == 245000000 and credit == 245000000, "debit=%d credit=%d" % (debit, credit))
    check("%s — the totals are Python ints, not floats or Decimals" % label,
          isinstance(debit, int) and isinstance(credit, int)
          and not isinstance(debit, bool),
          "%s / %s" % (type(debit).__name__, type(credit).__name__))
    print()

print("=== A2-7's capture and my live re-observation must agree entry for entry ===")
a = entries(CAP / "A2-235-je-after-recovery.json")
b = entries(HERE / "obs" / "a2-11-get-je-loan5.json")
check("same entry ids, sides, amounts and GL codes", sorted(a) == sorted(b),
      "A2-7=%s\n          A2-11=%s" % (sorted(a), sorted(b)))

print()
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)
sys.exit(1 if fails else 0)
