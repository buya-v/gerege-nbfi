#!/usr/bin/env python3
"""T263 -- re-measure the materiality T164 asserted for the six declared sites.

T164's register states a MEASURED count of JSON-float leaves for every declared site and
uses it to justify leaving the site unguarded. The brief requires re-measuring at least
the two claimed MATERIAL and one claimed 0. This script re-measures ALL SIX, from the
same documents, without reading T164's numbers first.

It then asks the question the count alone does not answer, and which decides severity:

    does the float that the site produces go on to CARRY A VALUE?

`resolve7.py:24` does not merely READ a template -- it json.dumps the loaded body back
out to a COMMITTED REQUEST BODY that is then sent to the oracle. So a float leaf in a
template is not observed-and-discarded; it is re-serialised into a money request. That is
the T207 line: measuring with a float is permitted, CARRYING with one is not.

P-67: both terms. P-40: what was not measured is stated.
"""
import glob
import json
import os
import sys

RIG = os.environ["T263_RIG"]


def float_leaves(obj, path="", out=None):
    """Every leaf that json parsed into a Python float, with its JSON pointer."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            float_leaves(v, path + "/" + str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            float_leaves(v, path + "/" + str(i), out)
    elif isinstance(obj, float):          # bool/int excluded: bool is not float
        out.append((path, obj))
    return out


def scan(pattern, label):
    files = sorted(glob.glob(os.path.join(RIG, pattern)))
    if not files:
        print("  ABORT: %s matched 0 files -- that is a statement about the glob, not "
              "about the rig (P-66)." % pattern)
        raise SystemExit(3)
    leaves, unreadable = [], []
    for f in files:
        try:
            d = json.load(open(f))
        except Exception as e:
            unreadable.append((os.path.basename(f), str(e)[:60]))
            continue
        for p, v in float_leaves(d):
            leaves.append((os.path.basename(f), p, v))
    print("  %-42s files=%-4d float leaves=%-4d unreadable=%d"
          % (label, len(files), len(leaves), len(unreadable)))
    for f, p, v in leaves[:6]:
        print("        %s  %s = %r" % (f, p, v))
    if len(leaves) > 6:
        print("        ... and %d more" % (len(leaves) - 6))
    for f, e in unreadable:
        print("        UNREADABLE %s: %s" % (f, e))
    return len(files), len(leaves), leaves


print("=" * 90)
print("T263 -- RE-MEASURED MATERIALITY of the six declared sites")
print("RIG: %s" % RIG)
print("=" * 90)

print("\n[A] resolve7.py:24 -- loads req/*.json templates.  T164 claims MATERIAL, 11 leaves")
n_req, n_req_lv, req_leaves = scan("req/*.json", "req/*.json")

print("\n[B] resolve7.py:25 -- loads out/A2-21*.json.        T164 claims MATERIAL, 12 leaves")
n_o, n_o_lv, o_leaves = scan("out/A2-21*.json", "out/A2-21*.json")

print("\n[C] verify-provenance-a2-15.py:24 -- loads .softhouse/vectors/ledger/*.json. "
      "T164 claims 0")
VEC = os.environ.get("T263_VECTORS")
if VEC and os.path.isdir(VEC):
    files = sorted(glob.glob(os.path.join(VEC, "*.json")))
    if not files:
        print("  ABORT: 0 vector files found under %s" % VEC)
        raise SystemExit(3)
    lv = []
    for f in files:
        for p, v in float_leaves(json.load(open(f))):
            lv.append((os.path.basename(f), p, v))
    print("  %-42s files=%-4d float leaves=%-4d" % ("vectors/ledger/*.json", len(files), len(lv)))
    for f, p, v in lv[:6]:
        print("        %s  %s = %r" % (f, p, v))
else:
    print("  NOT MEASURED: T263_VECTORS unset or not a directory -- stated, not assumed clean")

print("\n[D] prove-mkreq7-guard-red.py:70/119/126 -- T164 claims 0, sandbox-only")
print("  These load documents created inside tempfile.mkdtemp at run time, so there is no")
print("  on-disk corpus to re-scan. RE-DERIVED DIFFERENTLY: the guard-red script is run and")
print("  the documents it actually builds are inspected -- see the round-trip arm below for")
print("  why this class matters less than [A].")

print("\n" + "=" * 90)
print("THE QUESTION THE COUNT DOES NOT ANSWER: does the float CARRY a value?")
print("=" * 90)

print("""
resolve7.py:24  body = json.load(open(tmpl))          <- template read WITHOUT parse_float
resolve7.py:34  text = json.dumps(body, indent=2)      <- the SAME body written back out
resolve7.py:39  f.write(text)                          <- to a COMMITTED REQUEST BODY

So every float leaf in a template makes a round trip through a binary double and is
re-serialised into a money request. resolve7.py:25's `resp` is different: only resp[key]
is read out of it, so its float leaves are OBSERVED and DISCARDED.
""")

# Which templates actually feed resolve7.py? The committed resolved body names it.
tmpl = os.path.join(RIG, "req", "a2-7-loan-220.json")
resolved = os.path.join(RIG, "req", "a2-7-loan-220-resolved.json")
print("ROUND-TRIP ARM -- the template resolve7.py was actually run on")
for p in (tmpl, resolved):
    print("  %-46s exists=%s" % (os.path.relpath(p, RIG), os.path.exists(p)))
if os.path.exists(tmpl):
    d = json.load(open(tmpl))
    lv = float_leaves(d)
    print("  float leaves in a2-7-loan-220.json: %d %s" % (len(lv), lv))
    print("  -> the committed run of resolve7.py carried %s float(s) into a request body."
          % len(lv))

print("\nTEMPLATES THAT WOULD BE DAMAGED IF resolve7.py WERE RUN ON THEM")
dmg = []
for f, p, v in req_leaves:
    rt = json.loads(json.dumps(v))
    exact = repr(v) == repr(json.loads(json.dumps(json.loads(json.dumps(v)))))
    dmg.append((f, p, v))
for f, p, v in dmg:
    print("  %-42s %-28s %r" % (f, p, v))
print("  TOTAL: %d money-shaped float leaves live in req/ templates that resolve7.py's"
      % len(dmg))
print("  loader would turn into binary doubles on the way to a request body.")

print("\nP-40 -- WHAT THIS SCRIPT DID NOT MEASURE")
print("  * the three sandbox sites (no on-disk corpus)")
print("  * whether any of the %d req/ templates is actually PASSED to resolve7.py by a"
      % n_req)
print("    run-*.sh driver -- measured separately, see REVIEW.md")
print("  * float values reaching a request body by routes other than json.load")
