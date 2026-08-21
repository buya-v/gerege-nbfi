#!/usr/bin/env python3
"""check_wire_float_roundtrip — T173. The AUTOMATIC half of T163's request-body float guard.

WHAT IT ENFORCES
----------------
    EVERY NUMERIC TOKEN IN EVERY CAPTURE REQUEST BODY IS BYTE-PRESERVED UNDER A
    BINARY-DOUBLE ROUND TRIP.

That is the exact property T163's `audit-req-float-roundtrip.py` measured by hand, over one
hard-coded rig directory.  This is the same property with the root DERIVED instead of named,
so a rig that has not been written yet is covered on the day it lands.

WHY THAT PROPERTY, AND WHAT IT IS NOT
-------------------------------------
The defect it exists to stop is P-25 as T163 found it: `json.load(...)` with no `parse_float`,
then `json.dumps(...)`.  Every number in the document makes a round trip through a binary
double and is re-emitted as `repr(float)`.  A literal survives byte-identically iff its own
text is already the shortest round-trip repr of its double.  `1200000` survives; `1200000.00`
comes back `1200000.0`; `12345678901234567890.12` comes back `1.2345678901234567e+19`, a
residue of -890.12 on the way TO the reference oracle.

IT IS NOT "no float-shaped token in a request body", AND THE DIFFERENCE IS MEASURED, NOT
ASSUMED.  When T173 wired this, 221 of the 320 committed request bodies already carried a
float-shaped token: 214 `interestRatePerPeriod` (`21.6`, `12.0` — a RATE, not money), 53
`amount` (charge percentages and flat charge amounts), and 11 `principal` (`1162502.5` — the
T149/T153 half-cent TIE probes, where the half-cent IS the observation).  A blanket ban would
refuse the entire committed corpus on its first run and make the harness permanently exit 2 —
a guard that refuses everything is not a guard.  So the blanket money-on-the-wire question is
recorded as a T173 follow-up with its measured population, and is NOT what this file claims to
enforce.  Read the census line: it prints how many float-shaped tokens are PRESENT alongside
how many are ALTERED, so the two numbers can never be confused for one another.

DETECTED WITH THE PARSER, NOT A REGEX (P-48 rule 1)
---------------------------------------------------
`json.loads` calls `parse_int`/`parse_float` with the ORIGINAL SOURCE TEXT of each numeric
token.  Hooking them yields every number exactly as written, with no regex guessing about what
is a number and what is digits inside a string.  A regex would fire on `"note": "1200000.00"`,
which is a string and cannot be mangled, and would miss a number nested where the pattern did
not reach.

Line numbers are located AFTERWARDS, by searching the source lines for the offending token, and
that locate is for the HUMAN ONLY — it can report `?` without affecting the verdict.  Detection
never depends on it.

THE ONE DELIBERATE `float()` (P-25)
-----------------------------------
The line marked SIMULATE calls `float()` on purpose: it SIMULATES THE DEFECT, which is the only
way to measure it.  No money conclusion is drawn from it — the comparison is between two
STRINGS.

GUARD SHAPE (P-35)
------------------
Counts are POSITIVE and PRINTED, with the root PRINTED, and ZERO IS AN ERROR on all three of
request bodies, rig directories and `req/` directories.  A file count alone cannot tell a
whole-tree walk apart from a single-directory walk, and the single-directory walk is exactly
the state T163's audit was in while printing a healthy-looking number (T166 made the same
correction on the Go side).

A FILE IN THE DERIVED SET THAT THE JSON PARSER REJECTS IS A REFUSAL, NOT A SKIP.  It is a
request body that is not a request body.  Nothing is swallowed into an `except: continue`
(the G-9 shape) — every such file is named with its exact parser error and the run refuses.

Usage:
  check_wire_float_roundtrip.py <repo-root>   exit 0 clean, exit 1 and name every site otherwise
  check_wire_float_roundtrip.py --selftest    drive it RED four ways (P-22)
"""
import json
import os
import re
import sys
import tempfile

CAPTURE_REL = os.path.join('.softhouse', 'capture')
PRUNE = {'.git', 'node_modules', 'build', '.gradle'}


def derive(root):
    """The inspected set, DERIVED by recursive walk — never a named subtree.

    A request body is (a) any *.json under a directory named `req`, at any depth, or
    (b) any *.req — the wire-bytes artefact cap8.sh commits alongside the response.
    Returns (files, rigs, reqdirs). `rigs` is the set of directory names directly under
    .softhouse/capture/ that contribute at least one body, so a new rig raises the count.
    """
    cap = os.path.join(root, CAPTURE_REL)
    files, reqdirs = [], set()
    for dirpath, dirnames, filenames in os.walk(cap):
        dirnames[:] = [d for d in dirnames if d not in PRUNE]
        in_req = os.path.basename(dirpath) == 'req'
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            if in_req and fn.endswith('.json'):
                files.append(p)
                reqdirs.add(dirpath)
            elif fn.endswith('.req'):
                files.append(p)
                reqdirs.add(dirpath)
    files.sort()
    rigs = set()
    for p in files:
        rel = os.path.relpath(p, cap)
        rigs.add(rel.split(os.sep)[0])
    return files, rigs, reqdirs


def tokens_of(text):
    """Every numeric token as the SOURCE TEXT the JSON parser saw, via the parser itself."""
    toks = []

    def hook(kind):
        def f(s):
            toks.append((kind, s))
            return s
        return f

    json.loads(text, parse_float=hook('float'), parse_int=hook('int'))
    return toks


def defect_render(kind, tok):
    """Exactly what a `json.load` -> `json.dumps` round trip with no parse_float re-emits."""
    if kind == 'int':
        return json.dumps(int(tok))
    return json.dumps(float(tok))          # SIMULATE the defect. Deliberate float (P-25).


def locate(lines, tok):
    """First 1-based line whose text carries `tok` as a standalone numeric token, or None.

    REPORTING ONLY. Returning None costs a line number and never a verdict.
    """
    pat = re.compile(r'(?<![0-9A-Za-z_.+-])' + re.escape(tok) + r'(?![0-9])')
    for n, line in enumerate(lines):
        if pat.search(line):
            return n + 1
    return None


def check(root):
    root = os.path.abspath(root)
    cap = os.path.join(root, CAPTURE_REL)
    files, rigs, reqdirs = derive(root)

    unparsed, altered = [], []
    ntok = nfloat = 0
    for p in files:
        rel = os.path.relpath(p, root)
        try:
            text = open(p, 'rb').read().decode('utf-8')
            toks = tokens_of(text)
        except Exception as e:                                  # named, never swallowed
            unparsed.append((rel, '%s: %s' % (type(e).__name__, str(e)[:120])))
            continue
        lines = text.split('\n')
        for kind, s in toks:
            ntok += 1
            if kind == 'float':
                nfloat += 1
            rendered = defect_render(kind, s)
            if rendered != s:
                altered.append((rel, locate(lines, s), s, rendered))

    print('CENSUS wire-float round-trip — inspected %d request bodies / %d numeric tokens '
          'across %d capture rigs / %d req directories under %s (recursive, whole capture tree)'
          % (len(files), ntok, len(rigs), len(reqdirs), cap))
    print('CENSUS float-shaped tokens PRESENT %d (rates, charge percentages, tie probes — see the '
          'module docstring), ALTERED by a binary-double round trip %d' % (nfloat, len(altered)))

    if not files or not rigs or not reqdirs:
        print('REFUSED — INSPECTED %d BODIES / %d RIGS / %d REQ DIRECTORIES under %s.'
              % (len(files), len(rigs), len(reqdirs), cap))
        print('A guard that inspects nothing passes everything. This is an ERROR, not a pass (P-35).')
        return 1

    rc = 0
    if unparsed:
        print('REFUSED — a file in the derived request-body set is not parseable as JSON. '
              'A request body that is not a request body cannot be certified clean.')
        for rel, why in unparsed:
            print('  %s  %s' % (rel, why))
        rc = 1
    if altered:
        print('REFUSED — a numeric token in a capture request body is NOT byte-preserved under a '
              'binary-double round trip. This is the P-25 defect T163 found in resolve7.py: the '
              'money that reaches the reference oracle is not the money that was written.')
        for rel, line, src, rendered in altered:
            print('  %s:%s  %s  ->  %s' % (rel, line if line else '?', src, rendered))
        print('Fix: never re-serialise a request body through json.dumps of a parsed number. '
              'Splice the placeholder into the template bytes '
              '(.softhouse/capture/tierA-a2/resolve8.py is the worked example).')
        rc = 1
    if rc == 0:
        print('clean: every numeric token in every capture request body is byte-preserved.')
    return rc


# ---------------------------------------------------------------------------------------------
def _rig(tmp, rigname, name, body):
    d = os.path.join(tmp, CAPTURE_REL, rigname, 'req')
    if not os.path.isdir(d):
        os.makedirs(d)
    open(os.path.join(d, name), 'w').write(body)
    return d


def selftest():
    """P-22, both halves (P-50): it must REFUSE the defect AND PASS the clean tree."""
    fails = []
    CLEAN = '{\n  "principal": 1200000,\n  "interestRatePerPeriod": 21.6,\n  "note": "1200000.00"\n}\n'

    # (a) a NEW rig whose body carries a literal a double round trip rewrites -> REFUSE
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', '{\n  "principal": 1200000.00\n}\n')
        print('--- (a) a body carrying 1200000.00 ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(a) a body carrying 1200000.00 was NOT refused')

    # (b) the SAME shape written as an integer, plus a float-shaped RATE and a float
    #     INSIDE A STRING -> must PASS. A guard that refuses everything is not a guard,
    #     and a regex would have fired on the string.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        print('--- (b) integer money + float-shaped rate + a float inside a string ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 0:
            fails.append('(b) a clean body was refused anyway — the guard is over-broad')

    # (c) ZERO bodies -> ERROR, never a pass over no input (P-35)
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, CAPTURE_REL))
        print('--- (c) an empty capture tree ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(c) an empty capture tree PASSED — the guard is vacuous on no input')

    # (d) a file in the derived set that is not JSON -> named and REFUSED, never skipped
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        _rig(tmp, 'newrig', 'broken.json', '{ "principal": {{PLACEHOLDER}} }\n')
        print('--- (d) an unparseable file in the derived set ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(d) an unparseable request body was not refused')

    # (e) the DERIVATION itself: a body in a rig nobody named, nested two levels deeper,
    #     must be reached. This is the T166 defect in its capture-rig form.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        _rig(tmp, os.path.join('otherrig', 'sub', 'deeper'), 'body.json',
             '{\n  "principal": 0.10\n}\n')
        print('--- (e) a deeply nested rig nobody named ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(e) a body two directories deeper in an unnamed rig was NOT reached')

    print()
    print('check_wire_float_roundtrip selftest: %d failure(s)' % len(fails))
    for f in fails:
        print('  FAIL ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    sys.exit(check(sys.argv[1]))
