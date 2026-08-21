#!/usr/bin/env python3
"""T175 -- SUCCESSOR to the invariant leg of `t55-analyse.py`.  De-vacuumed.

WHY THIS FILE EXISTS
--------------------
`t55-analyse.py` is COMMITTED EVIDENCE and is left byte-identical (T114's ruling: committed
evidence is not edited in place).  It carries two silent swallows on a money path:

  t55-analyse.py:350-352   inside invariant I6, "every money cell is at most 2 dp (MNT minor
                           unit)":   `try: exp = -Decimal(v).as_tuple().exponent
                                      except Exception: continue`
                           A money cell whose text will not parse as Decimal is DROPPED and I6
                           passes WITHOUT it.  With every cell unparseable, I6 reports `ok` over
                           an empty denominator -- a vacuous pass on the FIRST non-negotiable in
                           CLAUDE.md ("money is integer minor units ... store 2").

  t55-analyse.py:164-167   inside `diff()`, computing the WORST money delta of a pair:
                           `try: delta = abs((Decimal(av) - Decimal(bv)) / MINOR)
                            except Exception: pass`
                           A money cell whose delta cannot be computed can never become the
                           worst, so the published "max minor u" column silently understates.

Neither prints anything.  Neither counts anything.  Both are the signature failure this program
keeps re-finding: a check that stops checking and says so nowhere (patterns.md P-22, P-35).

WHAT THIS SUCCESSOR CHANGES -- and NOTHING ELSE
-----------------------------------------------
1. Every skip is NAMED (capture id, cell key, the exact raw text, the exception type and
   message) and COUNTED, in a SKIP REGISTER printed on EVERY run including a clean one.
2. A non-zero swallow count FAILS the run.  It is never a pass and never a silence.
3. ZERO CELLS INSPECTED IS AN ERROR, not a pass (P-35).  Both the per-capture I6 denominator
   and the per-pair money-delta denominator are asserted non-zero and are PRINTED, so a future
   reader can see what the invariant actually looked at rather than trusting that it looked.
4. `cells()` itself drops any leaf that is not a `str`/`bool` (a JSON null, a bare number, a
   nested object) BEFORE I6 ever sees it -- a second, structurally different way for the
   denominator to shrink invisibly.  That drop is now measured and reported too.

The arithmetic is UNCHANGED: `decimal.Decimal` only, constructed from exact decimal text, money
differences in integer MINOR UNITS.  NO FLOAT anywhere, including intermediate calculation
(CLAUDE.md non-negotiable 1; patterns.md P-25 -- the rule binds analysis scripts).

This successor does NOT re-implement the discrimination table, the branch re-derivation, the
gradeability table or the T48 anchor.  Those legs of `t55-analyse.py` are untouched and remain
the authority for their own outputs.  It re-implements exactly the two swallowing legs, and it
re-runs the original's I1..I5/I7 unmodified so a violation elsewhere is still surfaced.

USAGE
    python3 t55-invariants-v2.py                  # runs over ../out
    T175_OUT=/some/scratch/dir python3 t55-invariants-v2.py
                                                  # runs over a scratch corpus; used by
                                                  # T175-red/ to drive both legs RED
Exit 0 = every invariant held, zero swallows, every denominator non-zero.
Exit 1 = an invariant was violated, OR something was swallowed, OR a denominator was empty.
"""
import importlib.util
import os
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ORIGINAL = os.path.join(HERE, "t55-analyse.py")

# Load the ORIGINAL as a module and reuse its loader, its flattener and its field list.  We do
# not fork a second copy of them: two copies of a claim is one claim and one time bomb
# (patterns.md P-27).  The module name has a hyphen, so importlib-by-path is the only route.
_spec = importlib.util.spec_from_file_location("t55_original", ORIGINAL)
t55 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(t55)

if os.environ.get("T175_OUT"):
    t55.OUT = os.path.abspath(os.environ["T175_OUT"])

MINOR = Decimal("0.01")          # MNT minor unit, ISO 4217 496

# ---------------------------------------------------------------- the skip register
SKIPS = []          # (leg, where, cell key, raw text, exception type, message)
FAILS = []


def skip(leg, where, key, raw, exc):
    """Record a swallow.  NAMED and COUNTED -- never a bare `continue`/`pass`."""
    SKIPS.append((leg, where, key, repr(raw), type(exc).__name__, str(exc)))


def fail(msg):
    FAILS.append(msg)
    print("  FAIL  " + msg)


# ---------------------------------------------------------------- denominator census
def money_leaf_census(doc):
    """How many MONEYISH leaves exist in the raw document, and how many survive `cells()`?

    `cells()` keeps only `str`/`bool` leaves.  A JSON null, a bare JSON number or a nested
    object is dropped there, silently, before any invariant runs.  Measure the loss."""
    present = 0
    for k in doc:
        if k in ("periods", "currency"):
            continue
        if k in t55.MONEYISH:
            present += 1
    for p in doc.get("periods", []):
        for k in p:
            if k in t55.MONEYISH:
                present += 1
    survived = sum(1 for k in t55.cells(doc) if k.split(".", 1)[1] in t55.MONEYISH)
    return present, survived


# ---------------------------------------------------------------- I6, de-vacuumed
def i6(cid, doc):
    """I6 -- every money cell is at most 2 dp (MNT minor unit).

    Returns (ok, detail, inspected, swallowed, dropped_by_cells).
    UNPARSEABLE IS A VIOLATION, NOT A SKIP: a money cell whose text is not an exact decimal
    fails the non-negotiable just as surely as one carrying three decimal places does."""
    present, survived = money_leaf_census(doc)
    dropped = present - survived
    inspected = 0
    swallowed = 0
    det = []
    for k, v in t55.cells(doc).items():
        fld = k.split(".", 1)[1]
        if fld not in t55.MONEYISH:
            continue
        try:
            exp = -Decimal(v).as_tuple().exponent
        except Exception as exc:                       # NAMED AND COUNTED -- never `continue`
            swallowed += 1
            skip("I6", cid, k, v, exc)
            det.append("%s=%r UNPARSEABLE AS DECIMAL (%s)" % (k, v, type(exc).__name__))
            continue
        inspected += 1
        if exp > 2:
            det.append("%s=%s has %d dp" % (k, v, exp))
    ok = (swallowed == 0) and not det
    return ok, det, inspected, swallowed, dropped


# ---------------------------------------------------------------- worst money delta, de-vacuumed
def worst_delta(a_id, b_id):
    """The `diff()` leg of t55-analyse.py:150-168, with the :167 swallow named and counted.

    Returns (n_keys, n_differ, worst, worst_cell, considered, swallowed)."""
    A, B = t55.cells(t55.load(a_id)), t55.cells(t55.load(b_id))
    keys = sorted(set(A) | set(B))
    differ = 0
    worst, worst_cell = 0, None
    considered = 0
    swallowed = 0
    pair = "%s vs %s" % (a_id, b_id)
    for k in keys:
        av, bv = A.get(k), B.get(k)
        if av == bv:
            continue
        differ += 1
        fld = k.split(".", 1)[1]
        if fld not in t55.MONEYISH:
            continue
        if av is None or bv is None:
            # A money cell present on one side and ABSENT on the other is not a computable
            # delta -- and it is not nothing either.  Name it.
            swallowed += 1
            skip("worst-delta", pair, k, "%r vs %r" % (av, bv),
                 ValueError("money cell present on one side only"))
            continue
        try:
            delta = abs((Decimal(av) - Decimal(bv)) / MINOR)
        except Exception as exc:                       # NAMED AND COUNTED -- never `pass`
            swallowed += 1
            skip("worst-delta", pair, k, "%r vs %r" % (av, bv), exc)
            continue
        considered += 1
        if delta > worst:
            worst, worst_cell = delta, k
    return len(keys), differ, worst, worst_cell, considered, swallowed


# ---------------------------------------------------------------- main
def main():
    print("=" * 100)
    print("T175 SUCCESSOR -- t55 invariants + worst-money-delta, every skip NAMED and COUNTED")
    print("  supersedes the swallowing legs of t55-analyse.py (:352 in I6, :167 in diff())")
    print("  corpus: %s" % t55.OUT)
    print("=" * 100)

    caps = ["%s-%s" % (sid, suf) for sid, _ in t55.SHAPES for suf in ("p7", "p3", "p4")]
    print()
    print("== INVARIANTS -- per capture, with I6's DENOMINATOR PRINTED ==")
    print("  %-16s %-8s %8s %9s %8s  %s"
          % ("capture", "I6", "inspect", "swallow", "dropped", "detail"))
    total_inspected = 0
    total_swallowed = 0
    total_dropped = 0
    captures_seen = 0
    for cid in caps:
        try:
            doc = t55.load(cid)
        except Exception as exc:
            # A capture that will not load is an ERROR, not one fewer row in the table.
            skip("load", cid, "<whole capture>", cid, exc)
            fail("%s: capture would not load (%s: %s) -- a missing capture is not a pass"
                 % (cid, type(exc).__name__, exc))
            continue
        captures_seen += 1

        # I1..I5 and I7 come from the ORIGINAL, unmodified -- this successor owns only I6 and
        # the worst-delta.  Run them so a violation elsewhere is still surfaced; I6's verdict
        # from the original is deliberately ignored, because that is the vacuous one.
        try:
            for name, ok_o, det_o in t55.invariants(cid):
                if not ok_o and not name.startswith("I6"):
                    fail("%s %s : %s" % (cid, name, det_o))
        except Exception as exc:
            skip("original-invariants", cid, "<I1..I5,I7>", cid, exc)
            fail("%s: the original invariants() raised %s: %s -- an exception is an ERROR, not "
                 "a skipped row" % (cid, type(exc).__name__, exc))

        ok, det, inspected, swallowed, dropped = i6(cid, doc)
        total_inspected += inspected
        total_swallowed += swallowed
        total_dropped += dropped
        print("  %-16s %-8s %8d %9d %8d  %s"
              % (cid, "ok" if ok else "VIOLATED", inspected, swallowed, dropped,
                 "; ".join(det)[:110] or "all cells 2 dp or fewer"))
        if not ok:
            fail("%s I6 VIOLATED -- %s" % (cid, "; ".join(det)))
        if inspected == 0:
            fail("%s I6 INSPECTED ZERO MONEY CELLS -- a guard that inspects nothing is an "
                 "ERROR, not a pass (P-35)" % cid)
        if dropped:
            fail("%s: %d MONEYISH leaf/leaves dropped by cells() before I6 could see them "
                 "(not a str/bool leaf) -- the denominator shrank invisibly" % (cid, dropped))

    print()
    print("  captures loaded            : %d of %d requested" % (captures_seen, len(caps)))
    print("  money cells I6 INSPECTED   : %d      <-- I6's denominator; zero would be an ERROR"
          % total_inspected)
    print("  money cells I6 SWALLOWED   : %d      <-- t55-analyse.py:352 discarded these silently"
          % total_swallowed)
    print("  MONEYISH leaves dropped by cells() before I6: %d" % total_dropped)
    if captures_seen == 0:
        fail("ZERO captures loaded -- the invariant suite inspected nothing at all (P-35)")
    if total_inspected == 0:
        fail("ZERO money cells inspected across the whole corpus -- I6 is VACUOUS (P-35)")

    print()
    print("== WORST MONEY DELTA -- per pair, with the delta DENOMINATOR PRINTED ==")
    print("  %-12s %-10s %7s %7s %10s %9s %14s  %s"
          % ("shape", "pair", "cells", "differ", "considrd", "swallowed", "max minor u", "cell"))
    delta_considered = 0
    delta_swallowed = 0
    pairs_seen = 0
    for sid, _why in t55.SHAPES:
        for a, b, _label in t55.PAIRS:
            try:
                n, nd, worst, wc, considered, sw = worst_delta("%s-%s" % (sid, a),
                                                               "%s-%s" % (sid, b))
            except Exception as exc:
                skip("worst-delta", "%s %s vs %s" % (sid, a, b), "<whole pair>", "", exc)
                fail("%s %s vs %s: pair would not load (%s: %s)"
                     % (sid, a, b, type(exc).__name__, exc))
                continue
            pairs_seen += 1
            delta_considered += considered
            delta_swallowed += sw
            print("  %-12s %-10s %7d %7d %10d %9d %14s  %s"
                  % (sid, "%s vs %s" % (a, b), n, nd, considered, sw,
                     worst if nd else "-", wc or "-"))
    print()
    print("  money deltas CONSIDERED    : %d" % delta_considered)
    print("  money deltas SWALLOWED     : %d      <-- t55-analyse.py:167 discarded these silently"
          % delta_swallowed)
    if pairs_seen == 0:
        fail("ZERO pairs compared -- the worst-delta leg inspected nothing (P-35)")

    # ---------------------------------------------------------------- SKIP REGISTER
    print()
    print("=" * 100)
    print("SKIP REGISTER -- %d swallowed item(s).  Printed on EVERY run, including a clean one,"
          % len(SKIPS))
    print("so a reader never has to infer a zero from a silence.")
    print("=" * 100)
    if not SKIPS:
        print("  0 items swallowed.  Every money cell handed to I6 parsed as an exact Decimal,")
        print("  and every money delta was computable.  The denominators above say what that")
        print("  zero was measured OVER.")
    else:
        for leg, where, key, raw, etype, emsg in SKIPS:
            print("  [%s] %s :: %s = %s  --  %s: %s" % (leg, where, key, raw, etype, emsg))
        fail("%d item(s) were swallowed.  A swallow is a FAILURE of this run, never a skip."
             % len(SKIPS))

    print()
    if FAILS:
        print("T175 SUCCESSOR: FAILED -- %d breach(es):" % len(FAILS))
        for f in FAILS:
            print("  " + f)
        return 1
    print("T175 SUCCESSOR: PASS -- %d captures, %d money cells inspected, %d money deltas "
          "considered, 0 swallowed." % (captures_seen, total_inspected, delta_considered))
    return 0


if __name__ == "__main__":
    sys.exit(main())
