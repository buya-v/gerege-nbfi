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

WHY THIS PROPERTY IS NECESSARY AND SUFFICIENT, NOT MERELY DEFENSIBLE (T186 §2.4, FU-7)
--------------------------------------------------------------------------------------
T173 justified byte-preservation as the honest weaker choice.  T186 measured something
stronger: `POST /charges` declares `private double amount` [T186 §2.4, citing
`ChargeRequest.java:41`], the ONE genuine Java `double` on a Fineract request path.  A token
survives that `double` unchanged exactly when its own text is already the shortest round-trip
repr of its binary64 value — which is this guard's predicate, character for character.  So the
property is not a proxy for the money question; on the one path where the reference oracle
really does narrow to a `double`, it IS the survival condition.

THE SECOND ARM — RECORDED REQUEST BLOCKS INSIDE CITED CAPTURE RECORDS (T193, T186 FU-2)
---------------------------------------------------------------------------------------
T186 §8 item 6 recorded the largest hole in its own coverage, and T193 re-derived it before
extending anything: **42 of the 43 stored parity vectors name a `capture-prod3*-raw.json` in
`provenance.capture_ref`, and the 43rd names a Path B raw** [T193, measured over
`.softhouse/vectors/**` by reading `provenance.capture_ref` as a FIELD, not by grepping prose].
Those Path A captures are driven in-process by `src/Capture3*.java`; their request never exists
as a committed `req/*.json`, so the walk above inspected **ZERO** of them.  The corpus carrying
the program's whole parity claim was the least inspected part of it.

The second arm closes that, and its DERIVATION IS THE STORE'S OWN CITATION — never a named
directory and never a `capture-prod3*` glob.  For every `*.json` under `.softhouse/vectors`
that carries a non-empty `provenance.capture_ref`, the referenced file is opened, and every
numeric token inside a RECORDED REQUEST BLOCK — the value of a key named `inputs` or `request`,
found at ANY depth by walking the PARSED document — is held to the same byte-preservation
predicate.  Cite a capture from a rig that does not exist yet and it is inspected on the day it
lands; rename `out/` and nothing moves.

WHAT THE SECOND ARM DELIBERATELY DOES NOT GRADE, STATED SO THE BLIND SPOT IS WRITTEN DOWN
-----------------------------------------------------------------------------------------
Cells OUTSIDE a recorded-request block in a cited capture record are READ AND COUNTED, and
their non-preserved tokens are PRINTED, but they do not decide the verdict.  They are ORACLE
OBSERVATIONS, and T186 §7 A4 rules that a response is never rewritten, never re-emitted through
a float and never scale-normalised — `1200000.000000` is not a typo for `1200000.0`, the scale
witnesses `DECIMAL(19,6)`.  Refusing a capture because a `json.dumps` WOULD damage a cell that
nothing re-serialises would refuse the evidence, and the evidence is pinned by digest anyway
(`admit.go` re-hashes every `capture_ref` against `provenance.capture_sha256`).  Measured at
T193: 59 such tokens in one record (`1162502.50` -> `1162502.5`, `0.00` -> `0.0`, all in the
Path B raw).  Printed every run, so the hole is stated rather than implied (P-22).

A2 IS NOT REOPENED.  T186 §7 A2 rules that "no float-shaped token in a request body" is WRONG
and must be rejected in review — it refuses 221 of 320 committed bodies.  The second arm
enforces the SAME predicate as the first (byte preservation), never a blanket ban, even though
the current float-shaped count inside recorded-request blocks happens to be zero.

Usage:
  check_wire_float_roundtrip.py <repo-root>   exit 0 clean, exit 1 and name every site otherwise
  check_wire_float_roundtrip.py --selftest    drive it RED ten ways (P-22)
"""
import json
import os
import re
import sys
import tempfile

CAPTURE_REL = os.path.join('.softhouse', 'capture')
VECTORS_REL = os.path.join('.softhouse', 'vectors')
PRUNE = {'.git', 'node_modules', 'build', '.gradle'}

# The keys whose VALUE is a recorded request.  `inputs` is what every Path A `Capture3*.java`
# emits alongside `observed`; `request` is the spelling a Path B record uses when it echoes the
# body it posted.  Both are matched at ANY depth — a capture file is a BUNDLE of cases, so the
# blocks live at `captures[i].inputs`, and a future bundle shape that nests them deeper is
# reached without editing this list.
REQUEST_BLOCK_KEYS = ('inputs', 'request')


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


class Tok(object):
    """One numeric token, carrying the SOURCE TEXT the JSON parser saw.

    Returned in place of the parsed number so the document can be walked STRUCTURALLY —
    which key is this token under? — without a regex ever guessing where a number is.
    """
    __slots__ = ('kind', 'text')

    def __init__(self, kind, text):
        self.kind = kind
        self.text = text


def parse_tokens(text):
    """Parse, replacing every number by a Tok. Raises exactly what json.loads raises."""
    def hook(kind):
        def f(s):
            return Tok(kind, s)
        return f
    return json.loads(text, parse_float=hook('float'), parse_int=hook('int'))


def split_tokens(node, path='$', inside=False, graded=None, other=None, blocks=None):
    """Walk the PARSED document and split its tokens by whether they sit in a request block.

    `graded` collects (json_path, Tok) for tokens under a REQUEST_BLOCK_KEYS subtree;
    `other` collects the rest; `blocks` collects the json_path of each request block found.
    Recursion, not a regex over the text — a key named `inputs` nested inside a string, or a
    number written inside a string, cannot reach either list.
    """
    if graded is None:
        graded, other, blocks = [], [], []
    if isinstance(node, Tok):
        (graded if inside else other).append((path, node))
    elif isinstance(node, dict):
        for k in node:
            v = node[k]
            sub = inside
            if not inside and k in REQUEST_BLOCK_KEYS and isinstance(v, (dict, list)):
                sub = True
                blocks.append('%s.%s' % (path, k))
            split_tokens(v, '%s.%s' % (path, k), sub, graded, other, blocks)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            split_tokens(v, '%s[%d]' % (path, i), inside, graded, other, blocks)
    return graded, other, blocks


def cited_captures(root):
    """The capture records the VECTOR STORE ITSELF names, and the vectors that name them.

    Returns (store_present, nvectors, refs, problems):
      store_present  False when there is no .softhouse/vectors at this root at all
      nvectors       how many *.json the store walk opened
      refs           {capture_ref (as written) -> [vector relpaths that cite it]}, insertion
                     order, EMPTY refs dropped (a hand-authored or contract vector correctly
                     has none — admit.go requires the citation only of a PARITY vector)
      problems       named failures: an unparseable store file, an escaping ref, a ref that
                     does not resolve. Each is a REFUSAL, never a skip — a citation this
                     function cannot follow is a capture record nothing inspects, which is
                     precisely the hole T193 exists to close.
    """
    vroot = os.path.join(root, VECTORS_REL)
    if not os.path.isdir(vroot):
        return False, 0, {}, []
    refs, problems = {}, []
    nvectors = 0
    for dirpath, dirnames, filenames in os.walk(vroot):
        dirnames[:] = [d for d in dirnames if d not in PRUNE]
        for fn in sorted(filenames):
            if not fn.endswith('.json'):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            nvectors += 1
            try:
                doc = json.loads(open(p, 'rb').read().decode('utf-8'))
            except Exception as e:                                  # named, never swallowed
                problems.append((rel, 'is in the vector store and does not parse as JSON, so '
                                      'any capture_ref it carries is UNREACHABLE: %s: %s'
                                 % (type(e).__name__, str(e)[:120])))
                continue
            if not isinstance(doc, dict):
                continue
            prov = doc.get('provenance')
            if not isinstance(prov, dict):
                continue
            ref = prov.get('capture_ref')
            if not isinstance(ref, str) or ref == '':
                continue
            if os.path.isabs(ref) or '..' in ref.replace('\\', '/').split('/'):
                problems.append((rel, 'cites capture_ref %r, which is absolute or escapes the '
                                      'repository; it cannot be resolved against this root' % ref))
                continue
            if not os.path.isfile(os.path.join(root, ref)):
                problems.append((rel, 'cites capture_ref %r, which is not a file at this root' % ref))
                continue
            refs.setdefault(ref, []).append(rel)
    return True, nvectors, refs, problems


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

    # ---- ARM 2: the recorded request blocks inside the capture records the STORE cites ------
    (store_present, nvectors, refs, cite_problems) = cited_captures(root)
    rec_unparsed, rec_altered, rec_blockless = [], [], []
    rec_ntok = rec_nfloat = rec_blocks = 0
    ungraded_ntok = 0
    ungraded_altered = []                 # measured and PRINTED, never a verdict (T186 §7 A4)
    for ref in refs:
        p = os.path.join(root, ref)
        try:
            text = open(p, 'rb').read().decode('utf-8')
            doc = parse_tokens(text)
        except Exception as e:                                  # named, never swallowed
            rec_unparsed.append((ref, '%s: %s' % (type(e).__name__, str(e)[:120])))
            continue
        graded, other, blocks = split_tokens(doc)
        lines = text.split('\n')
        rec_blocks += len(blocks)
        if not blocks:
            rec_blockless.append((ref, len(refs[ref])))
        for jpath, t in graded:
            rec_ntok += 1
            if t.kind == 'float':
                rec_nfloat += 1
            rendered = defect_render(t.kind, t.text)
            if rendered != t.text:
                rec_altered.append((ref, locate(lines, t.text), jpath, t.text, rendered))
        for jpath, t in other:
            ungraded_ntok += 1
            rendered = defect_render(t.kind, t.text)
            if rendered != t.text:
                ungraded_altered.append((ref, jpath, t.text, rendered))

    print('CENSUS wire-float round-trip — inspected %d documents / %d numeric tokens: %d request '
          'bodies (*.json under a req/ dir, plus *.req) across %d capture rigs / %d req '
          'directories under %s, and %d capture records cited by the vector store (recursive, '
          'whole capture tree)'
          % (len(files) + len(refs), ntok + rec_ntok + ungraded_ntok, len(files),
             len(rigs), len(reqdirs), cap, len(refs)))
    print('CENSUS float-shaped tokens PRESENT %d (rates, charge percentages, tie probes — see the '
          'module docstring), ALTERED by a binary-double round trip %d' % (nfloat, len(altered)))
    if store_present:
        print('CENSUS recorded-request blocks — %d capture records DERIVED from provenance.capture_ref '
              'across %d *.json in %s; %d of those records carry a recorded-request block and %d '
              'carry none; %d blocks (key `inputs` or `request`, any depth, located by parser walk) '
              '/ %d numeric tokens GRADED, float-shaped PRESENT %d, ALTERED %d'
              % (len(refs), nvectors, os.path.join(root, VECTORS_REL),
                 len(refs) - len(rec_blockless), len(rec_blockless),
                 rec_blocks, rec_ntok, rec_nfloat, len(rec_altered)))
    else:
        print('CENSUS recorded-request blocks — NIL-COVERAGE: there is no %s at this root, so the '
              'store-cited arm inspected an EMPTY POPULATION and graded nothing. It reports no '
              'coverage rather than a clean pass (P-35). In the repository this figure is carried '
              'by conformance.sh\'s DERIVED floor, which counts the same citations with git grep: '
              'a store that disappears drops the census below the floor and the run refuses.'
              % os.path.join(root, VECTORS_REL))
    for ref, ncites in rec_blockless:
        print('CENSUS   NOT COVERED BY THE RECORDED-REQUEST ARM: %s — cited by %d vector(s), carries '
              'no `inputs`/`request` block. Its request body is a separate artefact and is graded '
              'only if it lies in the req/ population above.' % (ref, ncites))
    if ungraded_altered:
        by_file = {}
        for ref, jpath, src, rendered in ungraded_altered:
            by_file[ref] = by_file.get(ref, 0) + 1
        print('CENSUS   READ BUT NOT GRADED: %d numeric tokens in cited capture records sit OUTSIDE '
              'any recorded-request block; %d of them are NOT byte-preserved (%s). These are ORACLE '
              'OBSERVATIONS and T186 §7 A4 forbids rewriting, re-emitting or scale-normalising one, '
              'so byte-fidelity is not the verdict property for them — the count is printed so the '
              'blind spot is STATED, not implied. Example: %s %s -> %s'
              % (ungraded_ntok, len(ungraded_altered),
                 '; '.join('%s x%d' % (k, v) for k, v in sorted(by_file.items())),
                 ungraded_altered[0][1], ungraded_altered[0][2], ungraded_altered[0][3]))
    elif refs:
        print('CENSUS   READ BUT NOT GRADED: %d numeric tokens in cited capture records sit OUTSIDE '
              'any recorded-request block; 0 of them are altered by a binary-double round trip.'
              % ungraded_ntok)

    if not files or not rigs or not reqdirs:
        print('REFUSED — INSPECTED %d BODIES / %d RIGS / %d REQ DIRECTORIES under %s.'
              % (len(files), len(rigs), len(reqdirs), cap))
        print('A guard that inspects nothing passes everything. This is an ERROR, not a pass (P-35).')
        return 1

    # NAMED BEFORE THE POPULATION CHECKS, DELIBERATELY. A dangling or escaping citation drops
    # that record out of `refs`, so an unfollowable citation can arrive at the zero-population
    # branch below wearing the costume of an empty store. Both are refusals; only this one
    # names the vector and the path, and the diagnostic is the whole value of the refusal.
    if cite_problems:
        print('REFUSED — a vector store file names a capture record this guard cannot follow. An '
              'unfollowable citation is a capture record NOTHING inspects, which is the exact hole '
              'T193 closed; it is a refusal, never a skip.')
        for rel, why in cite_problems:
            print('  %s  %s' % (rel, why))
        return 1

    if store_present and (nvectors == 0 or not refs):
        print('REFUSED — A VECTOR STORE IS PRESENT AT %s AND THE STORE-CITED ARM DERIVED %d CAPTURE '
              'RECORD(S) FROM %d STORE FILE(S).' % (os.path.join(root, VECTORS_REL), len(refs), nvectors))
        print('Every parity vector must cite provenance.capture_ref (admit.go enforces it), so zero '
              'citations means either the store holds no parity vector or the derivation stopped '
              'deriving. Both are an ERROR, not a pass (P-35).')
        return 1

    if store_present and refs and rec_blocks == 0:
        print('REFUSED — %d CITED CAPTURE RECORD(S) YIELDED ZERO RECORDED-REQUEST BLOCKS.'
              % len(refs))
        print('The arm exists to grade the requests those records carry. Zero blocks means the key '
              'this walk looks for (%s) is no longer the key the capture harness writes, and the arm '
              'has silently stopped checking. That is the vacuous guard (P-22/P-35), not a pass.'
              % ', '.join('`%s`' % k for k in REQUEST_BLOCK_KEYS))
        return 1

    rc = 0
    if rec_unparsed:
        print('REFUSED — a capture record cited by a stored vector is not parseable as JSON. The '
              'evidence a parity vector was transcribed FROM cannot be certified clean.')
        for ref, why in rec_unparsed:
            print('  %s  %s' % (ref, why))
        rc = 1
    if rec_altered:
        print('REFUSED — a numeric token in a RECORDED REQUEST inside a cited capture record is NOT '
              'byte-preserved under a binary-double round trip. This is the request that produced a '
              'promoted parity vector: the money the reference oracle was asked about is not the '
              'money the record says it was asked about.')
        for ref, line, jpath, src, rendered in rec_altered:
            print('  %s:%s  %s  %s  ->  %s' % (ref, line if line else '?', jpath, src, rendered))
        print('Fix: emit the value as a JSON string of the BigDecimal\'s own toPlainString() (every '
              'Capture3*.java already does — see Capture3b.java:339-340, `pl()`), or write the token '
              'so its text is already the shortest round-trip repr of its double.')
        rc = 1
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
        print('clean: every numeric token in every capture request body is byte-preserved, and so '
              'is every numeric token in every recorded request inside a capture record the vector '
              'store cites.')
    return rc


# ---------------------------------------------------------------------------------------------
def _rig(tmp, rigname, name, body):
    d = os.path.join(tmp, CAPTURE_REL, rigname, 'req')
    if not os.path.isdir(d):
        os.makedirs(d)
    open(os.path.join(d, name), 'w').write(body)
    return d


def _record(tmp, relparts, body):
    """Write a capture RECORD (not a req/ body) at .softhouse/capture/<relparts>."""
    rel = os.path.join(CAPTURE_REL, *relparts)
    p = os.path.join(tmp, rel)
    d = os.path.dirname(p)
    if not os.path.isdir(d):
        os.makedirs(d)
    open(p, 'w').write(body)
    return rel.replace(os.sep, '/')


def _vector(tmp, name, capture_ref, cls='parity'):
    """Write a stored vector that CITES a capture record. The citation is the derivation."""
    d = os.path.join(tmp, VECTORS_REL, 'loanschedule')
    if not os.path.isdir(d):
        os.makedirs(d)
    doc = {'schema': 'gerege.loanschedule.vector/v1', 'case_id': name, 'class': cls,
           'provenance': {'kind': 'oracle-capture', 'capture_ref': capture_ref,
                          'capture_case_id': name}}
    open(os.path.join(d, name + '.json'), 'w').write(json.dumps(doc, indent=2) + '\n')


# A Path A capture record in the shape Capture3*.java emits: a BUNDLE of cases, each with an
# `inputs` block (the recorded request) and an `observed` block (the oracle's answer). Money
# and rates leave the harness through BigDecimal.toPlainString(), so they are JSON STRINGS.
_REC_CLEAN = """{
  "pass": "3z",
  "moneyHelperPrecision": 19,
  "captures": [
    {
      "id": "P-ZZ",
      "inputs": {
        "disbursementAmount": "1200000",
        "annualNominalInterestRate": "21.6",
        "numberOfRepayments": 12,
        "mathContextPrecision": 19
      },
      "observed": {
        "totalInterestAmount": "142860.00",
        "loanTermInDays": 366
      }
    }
  ]
}
"""


def _rec_with(inputs_line):
    return _REC_CLEAN.replace('"disbursementAmount": "1200000",', inputs_line)


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

    # ---- the T193 arm: capture records the STORE cites ---------------------------------------
    # Cases (a)-(e) above carry NO vector store, so they also assert the NIL-COVERAGE branch
    # does not turn a clean tree red. Every case below plants one clean req/ body as well, so
    # a refusal can only have come from the arm under test.

    # (f) THE T193 DEFECT IN ITS EXACT LOCATION. A Path A capture record cited by a stored
    #     parity vector, whose RECORDED REQUEST carries money as a JSON number a double round
    #     trip rewrites. Before T193 the walk reached zero such files. -> REFUSE.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        ref = _record(tmp, ('out', 'capture-prod3z-raw.json'),
                      _rec_with('"disbursementAmount": 1200000.00,'))
        _vector(tmp, 'P-ZZ', ref)
        print('--- (f) a cited capture record whose recorded request carries 1200000.00 ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(f) a float-mangling token in a CITED capture record\'s recorded request '
                         'was NOT refused — the T193 arm is vacuous')

    # (g) THE BOUNDARY, asserted so nobody widens the arm to whole-document byte-fidelity by
    #     accident. The recorded request is clean (money as strings, the shape every
    #     Capture3*.java writes) and an OBSERVED cell is a JSON number a round trip rewrites.
    #     T186 §7 A4: a response is an observation, never rewritten and never scale-normalised.
    #     -> PASS, with the READ-BUT-NOT-GRADED census line naming the count.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        ref = _record(tmp, ('out', 'capture-prod3z-raw.json'),
                      _REC_CLEAN.replace('"totalInterestAmount": "142860.00",',
                                         '"totalInterestAmount": 142860.00,'))
        _vector(tmp, 'P-ZZ', ref)
        print('--- (g) clean recorded request + a non-preserved OBSERVED cell (T186 A4) ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 0:
            fails.append('(g) an ORACLE OBSERVATION was graded as if it were a request — T186 §7 A4 '
                         'forbids that verdict and the arm has become over-broad')

    # (h) THE DERIVATION IS THE CITATION, NOT A GLOB. The same defect in a record that is not
    #     under `out/`, is not named `capture-prod3*`, and sits three directories nobody named
    #     deep. It is reached because a VECTOR POINTS AT IT. -> REFUSE.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        ref = _record(tmp, ('somerig', 'nested', 'deeper', 'whatever.json'),
                      _rec_with('"disbursementAmount": 1200000.00,'))
        _vector(tmp, 'P-ZZ', ref)
        print('--- (h) the same defect in an unnamed directory, reached by citation ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(h) a cited record outside out/ and outside the capture-prod3* naming was '
                         'NOT reached — the derivation has become a glob')

    # (i) A CITATION THIS GUARD CANNOT FOLLOW IS A REFUSAL, NEVER A SKIP. A dangling
    #     capture_ref means a capture record nothing inspects, which is the hole itself.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        _vector(tmp, 'P-ZZ', '.softhouse/capture/out/capture-that-does-not-exist.json')
        print('--- (i) a vector citing a capture record that is not there ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(i) a dangling capture_ref was skipped instead of refused')

    # (j) A STORE THAT CITES NOTHING IS AN ERROR, NOT A PASS (P-35). Every parity vector must
    #     cite provenance.capture_ref, so zero citations means either no parity vector or a
    #     derivation that stopped deriving.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        d = os.path.join(tmp, VECTORS_REL, 'loanschedule')
        os.makedirs(d)
        open(os.path.join(d, 'HAND-01.json'), 'w').write(
            '{"case_id": "HAND-01", "class": "selftest", '
            '"provenance": {"kind": "hand-authored", "capture_ref": ""}}\n')
        print('--- (j) a vector store present and citing nothing ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(j) a store with zero citations PASSED — the arm is vacuous on no input')

    # (k) A CITED RECORD SET THAT YIELDS ZERO REQUEST BLOCKS IS AN ERROR. This is what a
    #     renamed `inputs` key looks like: the arm keeps running and silently grades nothing.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        ref = _record(tmp, ('out', 'capture-prod3z-raw.json'),
                      _REC_CLEAN.replace('"inputs"', '"parameters"'))
        _vector(tmp, 'P-ZZ', ref)
        print('--- (k) every cited record renamed its `inputs` key ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(k) cited records yielding ZERO request blocks PASSED — the arm stopped '
                         'checking without saying so')

    # (l) DEPTH AND STRING-IMMUNITY IN ONE. The request block is a `request` key nested two
    #     objects down, and a SIBLING string is spelled `"inputs"` as a VALUE — a text scan
    #     would fire on it, a parser walk cannot. -> REFUSE, and for the nested token only.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        ref = _record(tmp, ('out', 'nested-raw.json'),
                      '{\n  "note": "inputs",\n  "arms": [\n    {"leg": {\n'
                      '      "request": {"principal": 1200000.00}\n    }}\n  ]\n}\n')
        _vector(tmp, 'P-ZZ', ref)
        print('--- (l) a `request` block two levels down, beside the word "inputs" in a string ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('(l) a request block nested two objects deep was NOT reached')

    # (m) THE CLEAN CORPUS SHAPE MUST PASS (P-50). Money and rate as toPlainString() strings,
    #     integers as integers: exactly what every committed capture-prod3*-raw.json carries.
    with tempfile.TemporaryDirectory() as tmp:
        _rig(tmp, 'newrig', 'body.json', CLEAN)
        ref = _record(tmp, ('out', 'capture-prod3z-raw.json'), _REC_CLEAN)
        _vector(tmp, 'P-ZZ', ref)
        _vector(tmp, 'P-YY', ref)          # two vectors, one record: opened once, counted once
        print('--- (m) the committed corpus shape, two vectors citing one record ---')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 0:
            fails.append('(m) the shape the real corpus is written in was REFUSED — the arm is '
                         'over-broad and would pin conformance.sh at exit 2')

    print()
    print('check_wire_float_roundtrip selftest: %d failure(s)' % len(fails))
    for f in fails:
        print('  FAIL ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    sys.exit(check(sys.argv[1]))
