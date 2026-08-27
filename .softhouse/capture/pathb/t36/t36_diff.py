#!/usr/bin/env python3
"""T36 — number-by-number diff: the T36 re-capture at (19, HALF_UP) / Asia/Ulaanbaatar
versus the committed Path B corpus captured at (19, HALF_EVEN) / Asia/Kolkata.

Every JSON leaf is compared, not just the money totals. Money is read as EXACT
Decimal (parse_float=Decimal, parse_int=Decimal) and compared in INTEGER MINOR
UNITS; no binary float is ever constructed and no tolerance is applied anywhere.
A leaf that is textually different but numerically equal (e.g. `0` vs `0.00`) is
reported as a SCALE difference, distinct from a MOVED number.

Usage: t36_diff.py <committed.json> <recaptured.json> [label]
Exit:  0 = every number identical in minor units; 1 = at least one number moved.
"""
import json
import sys
from decimal import Decimal

SCALE = 2  # MNT minor units, ISO 4217 496 — asserted against currency.decimalPlaces


def load(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return json.loads(raw.decode("utf-8"), parse_float=Decimal, parse_int=Decimal), raw


def flatten(node, prefix=""):
    """Yield (path, value) for every leaf."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from flatten(v, "%s.%s" % (prefix, k) if prefix else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from flatten(v, "%s[%d]" % (prefix, i))
    else:
        yield prefix, node


def minor(v):
    """Exact minor-unit integer, or None if the value is not decimal money."""
    if not isinstance(v, Decimal):
        return None
    scaled = v * (10 ** SCALE)
    if scaled != scaled.to_integral_value():
        raise AssertionError("value %s is not representable in %d minor units" % (v, SCALE))
    return int(scaled)


def main(a_path, b_path, label):
    a, a_raw = load(a_path)
    b, b_raw = load(b_path)
    print("=" * 92)
    print("%s\n  committed : %s\n  recaptured: %s" % (label, a_path, b_path))

    dp_a = int(a["currency"]["decimalPlaces"])
    dp_b = int(b["currency"]["decimalPlaces"])
    assert dp_a == dp_b == SCALE, "currency.decimalPlaces %s/%s != %s" % (dp_a, dp_b, SCALE)

    fa = dict(flatten(a))
    fb = dict(flatten(b))
    keys = sorted(set(fa) | set(fb))

    moved, scale_only, structural, numbers = [], [], [], 0
    for k in keys:
        if k not in fa or k not in fb:
            structural.append(k)
            continue
        va, vb = fa[k], fb[k]
        ma, mb = minor(va), minor(vb)
        if ma is None or mb is None:
            if va != vb:
                structural.append("%s: %r -> %r" % (k, va, vb))
            continue
        numbers += 1
        if ma != mb:
            moved.append((k, va, vb, mb - ma))
        elif str(va) != str(vb):
            scale_only.append((k, va, vb))

    print("  numeric leaves compared (exact, integer minor units): %d" % numbers)
    print("  bytes identical: %s" % ("YES" if a_raw == b_raw else "NO"))
    if structural:
        print("  STRUCTURAL/NON-NUMERIC DIFFERENCES: %d" % len(structural))
        for s in structural:
            print("    ! %s" % s)
    else:
        print("  structural/non-numeric differences: NONE")
    if scale_only:
        print("  SCALE-ONLY differences (same money, different textual scale): %d" % len(scale_only))
        for k, va, vb in scale_only:
            print("    ~ %-52s %s -> %s" % (k, va, vb))
    else:
        print("  scale-only differences: NONE")
    if moved:
        print("  NUMBERS THAT MOVED: %d" % len(moved))
        for k, va, vb, d in moved:
            print("    * %-52s %s -> %s   (delta %+d minor units)" % (k, va, vb, d))
    else:
        print("  NUMBERS THAT MOVED: NONE — every number identical in minor units")
    return 0 if not moved and not structural else 1


if __name__ == "__main__":
    rc = main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "diff")
    sys.exit(rc)
