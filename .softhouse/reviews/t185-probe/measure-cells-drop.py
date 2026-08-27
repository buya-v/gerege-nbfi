#!/usr/bin/env python3
"""T185 -- does `measure-other-sites.py` publish '772 money deltas, 0 swallowed' over a
denominator that cells() silently shrank?

t55-analyse.py:133 cells() keeps only str/bool leaves. measure-other-sites.py:85-86 feeds it
`json.load(open(f))` with NO parse_float, so any BARE JSON NUMBER in a money field becomes a
binary double and is dropped by cells() before the delta loop ever sees it -- exactly the
narrowing T175 DID instrument in t55-invariants-v2.py ('MONEYISH leaves dropped by cells()')
and did NOT instrument here.

Measures the actual drop on the corpus that produced the committed 12/12 pairs, 772 deltas.
"""
import importlib.util, json, os, sys

W = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac71271ab074115ac"
ANALYSIS = os.path.join(W, ".softhouse/capture/leapboundary/analysis")
AA = os.path.join(W, ".softhouse/capture/actualactual/pathb/out")

spec = importlib.util.spec_from_file_location("t55m", os.path.join(ANALYSIS, "t55-analyse.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

PAIRS = []
for sid in ("T48B-PUREB", "T48B-YEAR", "T48B-QTR"):
    for a, b in (("p7", "p4"), ("p3", "p4"), ("p7", "p3")):
        PAIRS.append(("%s-%s" % (sid, a), "%s-%s" % (sid, b)))
PAIRS += [("T48B-B03SHAPE-p7", "T48B-B04SHAPE-p4"),
          ("T48B-B03SHAPE-p3", "T48B-B04SHAPE-p4"),
          ("T48B-B03SHAPE-p7", "T48B-B03SHAPE-p3")]


def moneyish_leaves(o, prefix=""):
    """Every MONEYISH leaf, regardless of python type -- the true denominator."""
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                out.update(moneyish_leaves(v, prefix + k + "."))
            elif k in m.MONEYISH:
                out[prefix + k] = v
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out.update(moneyish_leaves(v, prefix + "row%d." % i))
    return out


tot_true = tot_kept = 0
files = set()
for ida, idb in PAIRS:
    for cid in (ida, idb):
        f = os.path.join(AA, "%s-exact.json" % cid)
        if not os.path.exists(f) or f in files:
            continue
        files.add(f)
        raw_float = json.load(open(f))                     # what measure-other-sites.py does
        kept = {k: v for k, v in m.cells(raw_float).items()
                if k.split(".", 1)[1] in m.MONEYISH}
        true = moneyish_leaves(raw_float)
        tot_true += len(true)
        tot_kept += len(kept)
        if len(true) != len(kept):
            print("  DROP %-28s true MONEYISH leaves=%d  kept by cells()=%d"
                  % (cid, len(true), len(kept)))

print()
print("files inspected                                  : %d" % len(files))
print("TRUE MONEYISH leaves in the corpus               : %d" % tot_true)
print("leaves cells() actually hands to the delta loop  : %d" % tot_kept)
print("SILENTLY DROPPED before any delta is computed    : %d" % (tot_true - tot_kept))
print()
bare = 0
for f in sorted(files):
    txt = open(f).read()
    d = json.load(open(f))
    if m._has_number(d):
        bare += 1
print("files containing at least one BARE JSON NUMBER   : %d of %d" % (bare, len(files)))
print()
if tot_true == tot_kept:
    print("=> the published '772 money deltas, 0 swallowed' is NOT understated ON THIS CORPUS.")
    print("   It holds because every money cell here happens to be a JSON STRING, not because")
    print("   measure-other-sites.py checks. It reports no drop counter at all: a corpus with")
    print("   one bare number would shrink the denominator with no line of output saying so.")
else:
    print("=> the published figure IS over a silently shrunken denominator.")
