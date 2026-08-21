#!/usr/bin/env python3
"""T175 -- measure, for the swallow sites OTHER than the two this task supersedes, whether the
swallow actually drops anything on today's committed tree.

"Load-bearing" is a claim about the site's REACH; "swallows something today" is a separate,
measurable claim.  Both are reported, and where a site's input cannot be reconstructed without
running its owning tool, that is stated rather than guessed.

Read-only.  Writes nothing outside stdout.  No float.
Usage:  python3 measure-other-sites.py [repo-root]
"""
import json
import os
import sys

ROOT = None


def rel(p):
    return os.path.relpath(p, ROOT)


def measure_t46_exacttext():
    """capture/charges/bin/t46-exacttext.py:108 -- `except json.JSONDecodeError: continue`
    in the EXACT-TEXT SIDECAR generator, the tool whose whole purpose is closing T44-X1 (the
    no-floating-point non-negotiable).  A raw capture that will not parse gets no sidecar, no
    table row and no identity check -- and its own docstring point 4 says 'Identity is proved,
    not asserted'.  Reproduce its file selection and count what it would drop."""
    ch = os.path.join(ROOT, ".softhouse", "capture", "charges")
    dirs = [os.path.join(ch, "out", d) for d in ("fc", "t46", "control", "attested")]
    considered, skipped = 0, []
    for d in dirs:
        if not os.path.isdir(d):
            print("    (directory absent, not counted: %s)" % rel(d))
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json") or f.endswith("-exact.json"):
                continue
            considered += 1
            p = os.path.join(d, f)
            try:
                json.loads(open(p).read(), parse_float=str, parse_int=str)
            except json.JSONDecodeError as exc:
                skipped.append((rel(p), str(exc)))
    return considered, skipped


def measure_t55_prior():
    """leapboundary/analysis/t55-prior-capture-assessment.py:103 -- the SAME worst-money-delta
    swallow as t55-analyse.py:167, in a script whose committed output publishes 'max N minor
    units' four times.  Reproduce its comparison and count uncomputable money deltas."""
    sys.path.insert(0, os.path.join(ROOT, ".softhouse", "capture", "leapboundary", "analysis"))
    import importlib.util
    from decimal import Decimal
    spec = importlib.util.spec_from_file_location(
        "t55_for_prior",
        os.path.join(ROOT, ".softhouse", "capture", "leapboundary", "analysis",
                     "t55-analyse.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    aa = os.path.join(ROOT, ".softhouse", "capture", "actualactual", "pathb", "out")
    minor = Decimal("0.01")
    considered, swallowed = 0, []
    pairs = 0
    # The B03SHAPE set has NO -p4 leg: its committed row (T55-PRIOR-CAPTURE-ASSESSMENT.txt:38)
    # is the CROSS-SET pair `T48B-B03SHAPE-p7 vs T48B-B04SHAPE-p4`.  The first draft of this
    # measurement assumed same-set pairs throughout and reported those two as "absent"; the
    # assumption was wrong, not the corpus.  Enumerated explicitly now.
    PAIRS = []
    for sid in ("T48B-PUREB", "T48B-YEAR", "T48B-QTR"):
        for a, b in (("p7", "p4"), ("p3", "p4"), ("p7", "p3")):
            PAIRS.append(("%s-%s" % (sid, a), "%s-%s" % (sid, b), sid))
    PAIRS.append(("T48B-B03SHAPE-p7", "T48B-B04SHAPE-p4", "T48B-B03SHAPE x B04SHAPE"))
    PAIRS.append(("T48B-B03SHAPE-p3", "T48B-B04SHAPE-p4", "T48B-B03SHAPE x B04SHAPE"))
    PAIRS.append(("T48B-B03SHAPE-p7", "T48B-B03SHAPE-p3", "T48B-B03SHAPE"))
    if True:
        for ida, idb, sid in PAIRS:
            fa = os.path.join(aa, "%s-exact.json" % ida)
            fb = os.path.join(aa, "%s-exact.json" % idb)
            a, b = ida, idb
            if not (os.path.exists(fa) and os.path.exists(fb)):
                print("    (pair absent, not counted: %s %s vs %s)" % (sid, a, b))
                continue
            pairs += 1
            A = m.cells(json.load(open(fa)))
            B = m.cells(json.load(open(fb)))
            for k in sorted(set(A) | set(B)):
                av, bv = A.get(k), B.get(k)
                if av == bv:
                    continue
                if k.split(".", 1)[1] not in m.MONEYISH:
                    continue
                # NOTE the extra `and av and bv` guard the prior-assessment script carries at
                # its line 98: a money cell that is the empty string, or absent on one side, is
                # excluded from the worst-delta BEFORE the try even runs -- a second, silent
                # narrowing that is not an exception at all.
                if not (av and bv):
                    swallowed.append((sid, k, repr(av), repr(bv), "excluded by `av and bv`"))
                    continue
                try:
                    abs((Decimal(av) - Decimal(bv)) / minor)
                except Exception as exc:
                    swallowed.append((sid, k, repr(av), repr(bv), type(exc).__name__))
                    continue
                considered += 1
    return pairs, considered, swallowed


def main(argv):
    global ROOT
    ROOT = os.path.abspath(argv[0]) if argv else os.getcwd()
    print("T175 -- does each OTHER swallow site drop anything on today's committed tree?")
    print("root: %s" % ROOT)

    print()
    print("=" * 96)
    print("SITE  capture/charges/bin/t46-exacttext.py:108   `except json.JSONDecodeError: continue`")
    print("=" * 96)
    considered, skipped = measure_t46_exacttext()
    print("  raw capture files it would consider : %d" % considered)
    print("  files it would SILENTLY SKIP        : %d" % len(skipped))
    for p, msg in skipped:
        print("      %s  --  %s" % (p, msg))
    print("  VERDICT: LOAD-BEARING on the no-float non-negotiable (this is the tool that")
    print("           closes T44-X1 and its docstring claims 'identity is proved, not")
    print("           asserted'); DROPS %d file(s) TODAY." % len(skipped))

    print()
    print("=" * 96)
    print("SITE  leapboundary/analysis/t55-prior-capture-assessment.py:103   `except Exception: pass`")
    print("=" * 96)
    pairs, considered, swallowed = measure_t55_prior()
    print("  pairs compared                      : %d" % pairs)
    print("  money deltas CONSIDERED             : %d" % considered)
    print("  money deltas SWALLOWED / excluded   : %d" % len(swallowed))
    for sid, k, av, bv, why in swallowed[:20]:
        print("      %-16s %-42s %-12s %-12s %s" % (sid, k, av, bv, why))
    if len(swallowed) > 20:
        print("      ... %d more" % (len(swallowed) - 20))
    print("  VERDICT: same shape as t55-analyse.py:167, and its committed output")
    print("           T55-PRIOR-CAPTURE-ASSESSMENT.txt publishes 'max N minor units' four")
    print("           times, so it IS load-bearing on a published magnitude.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
