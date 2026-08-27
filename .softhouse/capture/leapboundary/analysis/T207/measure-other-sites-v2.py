#!/usr/bin/env python3
"""T207 -- SCRATCH SUCCESSOR to `T175-red/measure-other-sites.py`.  Closes T185's F-2 and F-3.

  python3 .softhouse/capture/leapboundary/analysis/T207/measure-other-sites-v2.py <repo-root>

T114'S STANDING RULING APPLIES AND IS THE REASON THIS IS A SEPARATE FILE
------------------------------------------------------------------------
`T175-red/measure-other-sites.py` produced `T175-red/measure-other-sites-output.txt`, which is
COMMITTED EVIDENCE: it is where the figures "12 pairs / 772 money deltas / 0 swallowed" and
"57 raw capture files considered / 0 silently skipped" were published.  Under T114 that file
is NOT edited in place.  It is left byte-identical; this is the scratch copy, re-run from
scratch, and BOTH transcripts are kept so the comparison is checkable.

WHAT T185 FOUND, AND THE CORRECTION T207 MAKES TO ITS PRESCRIPTION
------------------------------------------------------------------
F-2 said `measure-other-sites.py:85,86` -- `A = m.cells(json.load(open(fa)))` -- carry no
`parse_float=`, and that these two sit on the money-delta path that published 772 deltas.
Both halves of that are TRUE and were re-measured for T207 (`json-load-census.py`).

But "add `parse_float=`" is the WRONG repair here, and the reason matters:

    THIS SCRIPT'S JOB IS TO REPRODUCE THE SITE IT MEASURES.

`t55-prior-capture-assessment.py:50-52` and `t55-analyse.py:107-109` BOTH do
`json.load(fh)` with no `parse_float`  [VERIFIED: both files read this fire].  So lines 85-86
are a FAITHFUL REPRODUCTION of the defect under measurement, not a fresh instance of it.
Silently "fixing" them would make the measurer report what a hypothetical corrected tool would
see, and the published "0 swallowed" would become a claim about a tool that does not exist.

So T207 does not fix the reproduction.  It runs BOTH:

  * LEG A -- `json.load(open(f))`, byte-for-byte the target's own loading.  This is what the
    committed figure means, and it is preserved.
  * LEG B -- `json.load(open(f), parse_float=str)`, what the target WOULD see if T145 fixed
    it.  Nothing else differs.

and it prints the difference.  If A and B agree, the published figure is intact BY MEASUREMENT
rather than by the corpus happening to cooperate -- which is precisely F-3's complaint.

`parse_int=str` is deliberately NOT used in LEG B.  `cells()` keeps `str`/`bool` leaves, so
stringifying INTEGER leaves would make `cells()` start keeping cells it currently drops, and
LEG B would no longer be "the same tool with the float hazard removed" -- it would be a
different tool.  The integer leaves are counted and reported separately instead.

F-3 -- THE `cells()` DROP COUNTER, AND THE POPULATION STATEMENT
----------------------------------------------------------------
`t55-analyse.cells()` keeps a leaf only when it is `str` or `bool` (rows additionally keep
`list`, for date arrays).  A MONEYISH leaf that arrives as an `int` or a `float` is discarded
BEFORE the delta loop ever runs -- so the delta count can be honest and the coverage still be
zero.  T175 invented exactly this counter for `t55-invariants-v2.py` and did not carry it into
the tool that published the 772.  It is carried here, it is LOUD when nonzero, and the
POPULATION INSPECTED is stated in the output in the shape `guard_ledger_invariants` uses
[VERIFIED: `.softhouse/guards/ledgerguard/main.go:840,847,852` -- `NIL-COVERAGE — ... inspected
an empty population`].  A check that stops checking has to say so in writing.

READ-ONLY.  Writes nothing outside stdout.  Contacts no oracle.  No float on any money path:
every delta is `decimal.Decimal` built from exact text.  The `type()` inspections below are
STRUCTURAL -- they ask what a JSON parser BUILT, never what a number is worth.
"""
import importlib.util
import json
import os
import sys
from decimal import Decimal

ROOT = None
FAILURES = []


def rel(p):
    return os.path.relpath(p, ROOT)


def load_t55():
    """Import t55-analyse.py READ-ONLY for its `cells` and `MONEYISH`.  Never edited (T114:
    it produced committed evidence of its own)."""
    p = os.path.join(ROOT, ".softhouse", "capture", "leapboundary", "analysis", "t55-analyse.py")
    spec = importlib.util.spec_from_file_location("t55_for_T207", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ F-3: the drop counter
def moneyish_leaf_census(doc, moneyish):
    """What `cells()` is HANDED, and what it KEEPS, restricted to MONEYISH keys.

    Mirrors `cells()`'s own traversal exactly: top-level keys except `periods`/`currency`,
    then every key of every element of `periods`.  Returns
        (total, kept, dropped)  where dropped is a list of (cellname, python_type, repr)
    """
    total = kept = 0
    dropped = []

    def one(name, key, v):
        nonlocal total, kept
        if key not in moneyish:
            return
        total += 1
        # `cells()` keeps str/bool at plan level; str/bool/list at row level.  A list is never
        # a money leaf, so for MONEYISH the keep-test is the same at both levels.
        if isinstance(v, (str, bool)):
            kept += 1
        else:
            dropped.append((name, type(v).__name__, repr(v)))

    for k, v in doc.items():
        if k in ("periods", "currency"):
            continue
        one("plan." + k, k, v)
    for i, p in enumerate(doc.get("periods", [])):
        for k, v in sorted(p.items()):
            one("row%d.%s" % (i, k), k, v)
    return total, kept, dropped


def json_number_census(doc):
    """How many leaves anywhere in the document arrived as a python int / float.
    STRUCTURAL only: it inspects the TYPE the parser built, never the value."""
    ints = floats = 0

    def walk(x):
        nonlocal ints, floats
        if isinstance(x, bool):
            return
        if isinstance(x, int):
            ints += 1
        elif isinstance(x, float):
            floats += 1
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(doc)
    return ints, floats


# ------------------------------------------------------------------ site 1 (unchanged in substance)
def measure_t46_exacttext():
    ch = os.path.join(ROOT, ".softhouse", "capture", "charges")
    dirs = [os.path.join(ch, "out", d) for d in ("fc", "t46", "control", "attested")]
    considered, skipped = 0, []
    absent = []
    for d in dirs:
        if not os.path.isdir(d):
            absent.append(rel(d))
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
    return considered, skipped, absent


# ------------------------------------------------------------------ site 2, BOTH LEGS
PAIRS = []
for _sid in ("T48B-PUREB", "T48B-YEAR", "T48B-QTR"):
    for _a, _b in (("p7", "p4"), ("p3", "p4"), ("p7", "p3")):
        PAIRS.append(("%s-%s" % (_sid, _a), "%s-%s" % (_sid, _b), _sid))
PAIRS.append(("T48B-B03SHAPE-p7", "T48B-B04SHAPE-p4", "T48B-B03SHAPE x B04SHAPE"))
PAIRS.append(("T48B-B03SHAPE-p3", "T48B-B04SHAPE-p4", "T48B-B03SHAPE x B04SHAPE"))
PAIRS.append(("T48B-B03SHAPE-p7", "T48B-B03SHAPE-p3", "T48B-B03SHAPE"))


def measure_t55_prior(m, leg):
    """leg 'A' = json.load(f)                 -- reproduces t55-prior-capture-assessment.py:52
       leg 'B' = json.load(f, parse_float=str) -- the same tool with the float hazard removed
    """
    aa = os.path.join(ROOT, ".softhouse", "capture", "actualactual", "pathb", "out")
    minor = Decimal("0.01")
    considered, swallowed, absent = 0, [], []
    pairs = 0
    files_seen = set()
    leaves_total = leaves_kept = 0
    dropped_all = []
    bare_int_files, bare_float_files = set(), set()

    def rd(path):
        with open(path) as fh:
            if leg == "A":
                return json.load(fh)                       # EXACTLY the target's own call
            return json.load(fh, parse_float=str)          # the counterfactual

    for ida, idb, sid in PAIRS:
        fa = os.path.join(aa, "%s-exact.json" % ida)
        fb = os.path.join(aa, "%s-exact.json" % idb)
        if not (os.path.exists(fa) and os.path.exists(fb)):
            absent.append((sid, ida, idb))
            continue
        pairs += 1
        docs = {}
        for ident, path in ((ida, fa), (idb, fb)):
            doc = rd(path)
            docs[ident] = doc
            if path not in files_seen:
                files_seen.add(path)
                t, k, d = moneyish_leaf_census(doc, m.MONEYISH)
                leaves_total += t
                leaves_kept += k
                dropped_all.extend((rel(path), n, ty, r) for n, ty, r in d)
                ni, nf = json_number_census(doc)
                if ni:
                    bare_int_files.add(rel(path))
                if nf:
                    bare_float_files.add(rel(path))
        A = m.cells(docs[ida])
        B = m.cells(docs[idb])
        for k in sorted(set(A) | set(B)):
            av, bv = A.get(k), B.get(k)
            if av == bv:
                continue
            if k.split(".", 1)[1] not in m.MONEYISH:
                continue
            if not (av and bv):
                swallowed.append((sid, k, repr(av), repr(bv), "excluded by `av and bv`"))
                continue
            try:
                abs((Decimal(av) - Decimal(bv)) / minor)
            except Exception as exc:
                swallowed.append((sid, k, repr(av), repr(bv), type(exc).__name__))
                continue
            considered += 1
    return dict(pairs=pairs, considered=considered, swallowed=swallowed, absent=absent,
                files=len(files_seen), leaves_total=leaves_total, leaves_kept=leaves_kept,
                dropped=dropped_all, bare_int_files=sorted(bare_int_files),
                bare_float_files=sorted(bare_float_files))


def main(argv):
    global ROOT
    ROOT = os.path.abspath(argv[0]) if argv else os.getcwd()
    if not os.path.isfile(os.path.join(ROOT, "CLAUDE.md")):
        print("ROOT=%s is not the repo root" % ROOT)
        return 9
    m = load_t55()

    print("T207 -- SCRATCH SUCCESSOR to T175-red/measure-other-sites.py  (T185 F-2 + F-3)")
    print("root: %s" % ROOT)
    print()
    print("=" * 96)
    print("SITE  capture/charges/bin/t46-exacttext.py:108   `except json.JSONDecodeError: continue`")
    print("=" * 96)
    considered, skipped, absent = measure_t46_exacttext()
    for d in absent:
        print("    (directory absent, not counted: %s)" % d)
    print("  raw capture files it would consider : %d" % considered)
    print("  files it would SILENTLY SKIP        : %d" % len(skipped))
    for p, msg in skipped:
        print("      %s  --  %s" % (p, msg))
    if considered == 0:
        print("  NIL-COVERAGE — zero raw capture files matched this site's own file selection,")
        print("  so this site inspected an empty population and the 'DROPS 0 file(s)' line below")
        print("  would be vacuous. Treated as a FAILURE, not a clean report (P-35).")
        FAILURES.append("t46-exacttext site: considered 0 files")
    print("  VERDICT: LOAD-BEARING on the no-float non-negotiable (this is the tool that")
    print("           closes T44-X1 and its docstring claims 'identity is proved, not")
    print("           asserted'); DROPS %d file(s) TODAY, over a population of %d file(s)."
          % (len(skipped), considered))

    print()
    print("=" * 96)
    print("SITE  leapboundary/analysis/t55-prior-capture-assessment.py:103   `except Exception: pass`")
    print("=" * 96)
    print("  Run TWICE. LEG A reproduces the target's own `json.load(fh)` (no parse_float),")
    print("  which is what the committed 772 figure means. LEG B is the same tool with")
    print("  `parse_float=str`. Any figure that differs between the legs was float-dependent.")
    legs = {}
    for leg in ("A", "B"):
        r = measure_t55_prior(m, leg)
        legs[leg] = r
        print()
        print("  ---- LEG %s : json.load(fh%s) ----"
              % (leg, "" if leg == "A" else ", parse_float=str"))
        for sid, a, b in r["absent"]:
            print("    (pair absent, not counted: %s %s vs %s)" % (sid, a, b))
        print("    POPULATION INSPECTED   : %d pair(s) over %d distinct capture file(s)"
              % (r["pairs"], r["files"]))
        print("    pairs compared                      : %d" % r["pairs"])
        print("    money deltas CONSIDERED             : %d" % r["considered"])
        print("    money deltas SWALLOWED / excluded   : %d" % len(r["swallowed"]))
        for sid, k, av, bv, why in r["swallowed"][:20]:
            print("        %-16s %-42s %-12s %-12s %s" % (sid, k, av, bv, why))
        if len(r["swallowed"]) > 20:
            print("        ... %d more" % (len(r["swallowed"]) - 20))

        # ------------------------------------------------ F-3, the counter that was missing
        print("    F-3  cells() MONEYISH-leaf drop counter (absent from the committed tool):")
        print("      TRUE MONEYISH leaves in the corpus  : %d" % r["leaves_total"])
        print("      leaves cells() HANDS to the loop    : %d" % r["leaves_kept"])
        print("      SILENTLY DROPPED before any delta   : %d" % len(r["dropped"]))
        if r["leaves_total"] == 0:
            print("      NIL-COVERAGE — zero MONEYISH leaves exist in the %d file(s) walked, so"
                  % r["files"])
            print("      the drop counter inspected an empty population and the delta figures")
            print("      above are about nothing. This is an ERROR, not a clean report (P-35).")
            FAILURES.append("LEG %s: MONEYISH leaf population is empty" % leg)
        for path, name, ty, val in r["dropped"][:20]:
            print("      *** DROPPED  %s  %s  (python %s)  %s" % (path, name, ty, val))
        if r["dropped"]:
            print("      *** %d MONEYISH leaf/leaves were DISCARDED BY cells() BEFORE the delta"
                  % len(r["dropped"]))
            print("      *** loop ran. Every 'money deltas CONSIDERED' figure above is therefore")
            print("      *** a count over a NARROWED population, and the published 772 would be")
            print("      *** an UNDERSTATEMENT of the corpus, not a measurement of it.")
            FAILURES.append("LEG %s: cells() dropped %d MONEYISH leaf/leaves"
                            % (leg, len(r["dropped"])))
        print("      files carrying a bare JSON NUMBER (int)   : %d of %d  %s"
              % (len(r["bare_int_files"]), r["files"], r["bare_int_files"][:3] or ""))
        print("      files carrying a bare JSON NUMBER (float) : %d of %d  %s"
              % (len(r["bare_float_files"]), r["files"], r["bare_float_files"][:3] or ""))

    print()
    print("  ---- LEG A vs LEG B : which published number MOVES? ----")
    keys = (("pairs compared", "pairs"), ("money deltas CONSIDERED", "considered"),
            ("MONEYISH leaves total", "leaves_total"), ("MONEYISH leaves kept", "leaves_kept"))
    moved = []
    for label, k in keys:
        a, b = legs["A"][k], legs["B"][k]
        same = a == b
        print("    %-26s A=%-6d B=%-6d %s" % (label, a, b, "same" if same else "*** MOVED ***"))
        if not same:
            moved.append(label)
    for label, k in (("money deltas SWALLOWED", "swallowed"),
                     ("MONEYISH leaves DROPPED", "dropped")):
        a, b = len(legs["A"][k]), len(legs["B"][k])
        same = a == b
        print("    %-26s A=%-6d B=%-6d %s" % (label, a, b, "same" if same else "*** MOVED ***"))
        if not same:
            moved.append(label)
    print()
    if moved:
        print("    %d published figure(s) MOVE once the float hazard is removed: %s"
              % (len(moved), ", ".join(moved)))
        print("    The committed measure-other-sites-output.txt is therefore WRONG about them.")
        FAILURES.append("figures moved between legs: %s" % ", ".join(moved))
    else:
        print("    NO published figure moves. The committed 'pairs 12 / deltas 772 / swallowed 0'")
        print("    survives the fix -- and now survives it BY MEASUREMENT rather than by the")
        print("    corpus happening to store every money cell as a JSON string (T185 F-3).")

    print()
    print("=" * 96)
    if FAILURES:
        print("T207 measure-other-sites-v2: FINDINGS -- %d" % len(FAILURES))
        for f in FAILURES:
            print("  FINDING  " + f)
        return 1
    print("T207 measure-other-sites-v2: no finding. Population inspected and stated above;")
    print("this establishes ONLY what the two named sites drop on THIS tree, at THIS commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
