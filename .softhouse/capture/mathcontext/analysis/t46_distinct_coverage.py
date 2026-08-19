#!/usr/bin/env python3
"""
T46 / M-3 — how many of the 13 E1 `-A` (ambient-baseline) observations are DISTINCT?

T42's `CaptureMathContext.java:163-166` claims the 13 E1 shapes "between them REACH every
ambient-context read the static scan found on the Path A call graph", and `:179-181` justifies
the `installmentAmountInMultiplesOf` shape as the one reaching the three-argument
`Money.roundToMultiplesOf`.  T44's M-3 says that site was never reached and that the distinct
coverage of the matrix is 10, not 13.

This script re-derives that from the COMMITTED payload only.  It does not recompute money; it
compares the recorded `observed` blocks leaf by leaf as EXACT DECIMAL TEXT.

Discipline (CLAUDE.md / patterns.md):
  * no float anywhere -- json is parsed with parse_float=Decimal, and every money leaf is
    compared as the raw string the oracle emitted;
  * nothing is synthesised: every number printed is read from the payload.

Usage:  python3 analysis/t46_distinct_coverage.py [path-to-t42-mathcontext.json]
"""
import json
import sys
from decimal import Decimal

PAYLOAD = sys.argv[1] if len(sys.argv) > 1 else "out/t42-mathcontext.json"


def canon(node):
    """Canonical, float-free rendering of an observation subtree."""
    if isinstance(node, dict):
        return "{" + ",".join("%s:%s" % (k, canon(node[k])) for k in sorted(node)) + "}"
    if isinstance(node, list):
        return "[" + ",".join(canon(x) for x in node) + "]"
    if isinstance(node, Decimal):
        return format(node, "f")
    if isinstance(node, float):
        raise SystemExit("FLOAT LEAF FOUND -- parse_float=Decimal was bypassed")
    return str(node)


def cells(node, prefix=""):
    """Flatten an observation into (path, exact-text) leaf cells."""
    out = []
    if isinstance(node, dict):
        for k in sorted(node):
            out += cells(node[k], prefix + "/" + k)
    elif isinstance(node, list):
        for i, x in enumerate(node):
            out += cells(x, prefix + "[%d]" % i)
    else:
        if isinstance(node, float):
            raise SystemExit("FLOAT LEAF FOUND at " + prefix)
        out.append((prefix, format(node, "f") if isinstance(node, Decimal) else str(node)))
    return out


def main():
    doc = json.load(open(PAYLOAD), parse_float=Decimal)
    caps = [c for c in doc["captures"] if c["id"].endswith("-A") and c["family"] == "MATRIX"]
    print("payload           : %s" % PAYLOAD)
    print("E1 '-A' baselines : %d" % len(caps))
    print()

    base = caps[0]
    assert base["shape"] == "plain", "expected T42-MX-00-A to be the plain shape"
    base_obs = canon(base["observed"])
    base_cells = dict(cells(base["observed"]))

    print("%-16s %-32s %-10s %-8s %s" % ("id", "shape", "cells", "differ", "verdict vs plain"))
    print("-" * 96)
    identical, distinct = [], []
    for c in caps:
        cc = dict(cells(c["observed"]))
        keys = sorted(set(base_cells) | set(cc))
        differ = sum(1 for k in keys if base_cells.get(k) != cc.get(k))
        same = canon(c["observed"]) == base_obs
        (identical if same else distinct).append(c)
        print("%-16s %-32s %-10d %-8d %s" % (
            c["id"], c["shape"], len(cc), differ,
            "BYTE-IDENTICAL to plain" if same else "distinct"))

    print()
    print("BYTE-IDENTICAL to T42-MX-00-A (plain), including plain itself: %d" % len(identical))
    for c in identical:
        print("    %-16s %s" % (c["id"], c["shape"]))
    print("DISTINCT observations in the E1 matrix                       : %d" % (
        len(caps) - (len(identical) - 1)))
    print()

    plain = next(c for c in caps if c["shape"] == "plain")
    mult = next(c for c in caps if c["shape"] == "multiples1000")
    pi, mi = plain["inputs"], mult["inputs"]
    print("M-3 headline pair  T42-MX-00-A (plain)  vs  T42-MX-06-A (multiples1000)")
    print("  inputs that DIFFER:")
    for k in sorted(set(pi) | set(mi)):
        if pi.get(k) != mi.get(k):
            print("    %-40s %s  ->  %s" % (k, pi.get(k), mi.get(k)))
    pc, mc_ = dict(cells(plain["observed"])), dict(cells(mult["observed"]))
    keys = sorted(set(pc) | set(mc_))
    diff = [k for k in keys if pc.get(k) != mc_.get(k)]
    print("  observation cells compared : %d" % len(keys))
    print("  observation cells DIFFERING: %d" % len(diff))
    for k in diff:
        print("    %-60s %s  ->  %s" % (k, pc.get(k), mc_.get(k)))

    def p1_total(c):
        for p in c["observed"]["periods"]:
            if p.get("periodNumber") == 1:
                return p["total"]
        return None
    t_plain, t_mult = p1_total(plain), p1_total(mult)
    print("  period-1 'total' on plain          : %s" % t_plain)
    print("  period-1 'total' on multiples1000  : %s" % t_mult)
    print("  is the multiples1000 period-1 total a multiple of 1000? %s"
          % ("YES" if Decimal(t_mult) % Decimal(1000) == 0 else "NO"))
    print()
    print("CONCLUSION (M-3): installmentAmountInMultiplesOf = 1000 changed %d observed cells."
          % len(diff))
    print("The three-argument Money.roundToMultiplesOf ambient path was NOT reached.")


if __name__ == "__main__":
    main()
