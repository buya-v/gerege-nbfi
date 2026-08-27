#!/usr/bin/env python3
"""T163 — the P-25-clean successor to resolve7.py.  Fill the one runtime-dependent field
in an A2-7 request body from an OBSERVED response, WITHOUT any number in the file ever
becoming a binary double.

  python3 resolve8.py <template.json> <observed-response.json> <key> <out.json>

WHY THIS FILE EXISTS INSTEAD OF AN EDIT TO resolve7.py
------------------------------------------------------
resolve7.py produced committed evidence — `req/a2-7-loan-220-resolved.json`, the body that
was POSTed to the reference oracle to produce out/A2-220..A2-231 — and it is hashed in
MANIFEST.sha256.  T114's standing ruling forbids editing such a script in place; the fix
goes in a scratch copy and the original stays byte-identical so the committed artefact
stays re-derivable from the script that actually made it.  Same precedent as
capture/t117-familyb/src/postcheck.py, which is T100's postcheck.py copied, not edited.
resolve7.py is therefore UNCHANGED by T163 and SUPERSEDED by this file; callers should
use resolve8.py.

THE DEFECT THIS FIXES  (raised by A2-11, driven RED in prove-resolve8-float-red.py)
-----------------------------------------------------------------------------------
resolve7.py:24-25 `json.load(open(...))` with no `parse_float`, then :36 `json.dumps(...)`.
Both the TEMPLATE and the OBSERVED RESPONSE go through a binary double, and json.dumps
re-emits `repr(float)`.  A decimal literal survives byte-identically only if its own text
is already the shortest round-trip repr of its double, so:

    1200000.00        ->  1200000.0        (MNT stored to 2 decimals, CLAUDE.md)
    1200000.000000    ->  1200000.0        (exactly what Fineract's numeric(19,6) emits)
    0.10              ->  0.1
    12345678901234567890.12  ->  1.2345678901234567e+19   <- VALUE LOST, not just form

and the last one is inside MathContext(19, HALF_UP), the ratified tenant setting.  This is
not an analysis-layer defect: resolve7.py's output IS THE REQUEST BODY POSTED TO THE
REFERENCE ORACLE (run-220-a2-7-runtime.sh:27-31).  T163 measured 236 occurrences of
mangling-prone literals in 21 committed RESPONSE captures (audit-req-float-roundtrip.py),
so a future resolve of a money-valued key from any of them corrupts the wire.

THE MECHANISM, AND WHY NOT `parse_float=Decimal` ALONE
-------------------------------------------------------
`parse_float=Decimal` fixes the READ.  It does not fix the WRITE: `json.dumps` cannot
serialise a Decimal, and the obvious `default=str` renders it as a JSON *string*
`"1200000.00"` — a WIRE TYPE CHANGE, which is a different corruption of the same body.
So this script DOES NOT RE-SERIALISE THE TEMPLATE AT ALL.  It performs a byte-level splice
of the placeholder span into the template's own bytes.  Every literal that is not the
placeholder is preserved BY CONSTRUCTION, because it is never converted to any numeric
type on the way out.  The JSON parser is used only to VALIDATE and to LOCATE, never to
re-render.

Numbers are read through `parse_int`/`parse_float`/`parse_constant` hooks that yield a
`JsonNumber` carrying the ORIGINAL SOURCE TEXT, so the value spliced in is the oracle's
own bytes.  `float` is never constructed anywhere in this file.  `parse_constant` REFUSES
`NaN` / `Infinity` / `-Infinity`, which are Python-json extensions that would otherwise be
the one remaining float ingress.

GUARD SHAPE (P-35): every check below is a POSITIVE assertion with a printed count, and a
zero count is a refusal, not a pass.  Nothing is written until every check has passed, and
the write is `os.replace` of a temp file in the same directory (atomic on POSIX, P-48).
"""
import decimal
import hashlib
import json
import os
import sys


class JsonNumber:
    """A JSON number that remembers exactly how it was written."""
    __slots__ = ("raw", "dec")

    def __init__(self, raw):
        self.raw = raw
        self.dec = decimal.Decimal(raw)

    def __repr__(self):
        return "JsonNumber(%s)" % self.raw

    def __eq__(self, other):
        if isinstance(other, JsonNumber):
            return self.dec == other.dec
        if isinstance(other, (int, decimal.Decimal, str)):
            return self.dec == decimal.Decimal(other)
        return NotImplemented

    def __hash__(self):
        return hash(self.dec)


class RefusedConstant(Exception):
    pass


def _refuse_constant(name):
    raise RefusedConstant(
        "the JSON contains %r, a Python-json extension that is NOT valid JSON and is a "
        "binary float in every implementation that accepts it" % name)


def load_exact(path):
    """Parse `path`, with every number kept as its source text.  No float is constructed."""
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    doc = json.loads(text,
                     parse_int=JsonNumber,
                     parse_float=JsonNumber,
                     parse_constant=_refuse_constant)
    return raw, text, doc


def walk(node):
    if isinstance(node, dict):
        for v in node.values():
            for x in walk(v):
                yield x
    elif isinstance(node, list):
        for v in node:
            for x in walk(v):
                yield x
    else:
        yield node


def render(value):
    """The exact bytes to splice in for an observed value."""
    if isinstance(value, JsonNumber):
        return value.raw                       # the oracle's own digits, verbatim
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool) or value is None:
        return json.dumps(value)
    raise TypeError("cannot splice a %s into a scalar placeholder" % type(value).__name__)


def main(argv):
    if len(argv) != 5:
        print(__doc__, file=sys.stderr)
        return 2
    tmpl, observed, key, out = argv[1:]

    try:
        _traw, ttext, body = load_exact(tmpl)
        _oraw, _otext, resp = load_exact(observed)
    except RefusedConstant as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        return 1

    if not isinstance(resp, dict) or key not in resp:
        keys = sorted(resp) if isinstance(resp, dict) else "<not an object>"
        print(f"REFUSING: {observed} has no {key!r} — no observation to resolve from. "
              f"keys present: {keys}", file=sys.stderr)
        return 1
    if not isinstance(body, dict):
        print(f"REFUSING: {tmpl} is not a JSON object.", file=sys.stderr)
        return 1

    # ---- POSITIVE ASSERTION 1: no float exists anywhere in either document.
    nodes = list(walk(body)) + list(walk(resp))
    floats = [n for n in nodes if isinstance(n, float)]
    numbers = [n for n in nodes if isinstance(n, JsonNumber)]
    if floats:
        print("REFUSING: %d float object(s) were constructed while parsing — the P-25 "
              "defect is present in THIS script." % len(floats), file=sys.stderr)
        return 1
    print(f"  inspected {len(nodes)} scalar node(s); {len(numbers)} are numbers; "
          f"0 are float")

    placeholders = [k for k, v in body.items() if isinstance(v, str) and v.startswith("__")]
    if not placeholders:
        print(f"REFUSING: {tmpl} has no __PLACEHOLDER__ field to resolve.", file=sys.stderr)
        return 1

    value = resp[key]
    try:
        sub = render(value)
    except TypeError as e:
        print(f"REFUSING: {e}", file=sys.stderr)
        return 1

    # ---- locate every placeholder span in the TEMPLATE'S OWN BYTES.
    spans = []
    for k in placeholders:
        token = json.dumps(body[k])
        n = ttext.count(token)
        if n != 1:
            print(f"REFUSING: placeholder token {token} occurs {n} times in {tmpl}; "
                  f"a byte-level splice needs exactly 1.", file=sys.stderr)
            return 1
        i = ttext.index(token)
        spans.append((i, i + len(token), k, token))
    spans.sort()

    # ---- POSITIVE ASSERTION 2: exactly len(placeholders) spans, none overlapping.
    if len(spans) != len(placeholders):
        print("REFUSING: located %d span(s) for %d placeholder(s)."
              % (len(spans), len(placeholders)), file=sys.stderr)
        return 1
    for (a0, a1, _k, _t), (b0, _b1, _k2, _t2) in zip(spans, spans[1:]):
        if b0 < a1:
            print("REFUSING: placeholder spans overlap.", file=sys.stderr)
            return 1

    # ---- splice, recording exactly where each substituted span lands in the OUTPUT.
    pieces, cursor, sub_at, outlen = [], 0, [], 0
    for s, e, _k, _t in spans:
        seg = ttext[cursor:s]
        pieces.append(seg)
        outlen += len(seg)
        sub_at.append(outlen)
        outlen += len(sub)
        cursor = e
    pieces.append(ttext[cursor:])
    text = sub.join(pieces)

    # ---- POSITIVE ASSERTION 3: the OUTPUT is the TEMPLATE outside the recorded spans.
    # Re-derive the template from the output by putting the placeholder tokens back at the
    # recorded offsets.  If a single byte outside a span moved, this reconstruction fails.
    rebuilt, prev = [], 0
    for at, (_s, _e, _k, token) in zip(sub_at, spans):
        rebuilt.append(text[prev:at])
        rebuilt.append(token)
        prev = at + len(sub)
    rebuilt.append(text[prev:])
    rebuilt = "".join(rebuilt)
    if rebuilt != ttext:
        print("REFUSING: the splice changed bytes outside the placeholder span(s). "
              "template sha256=%s, re-derived sha256=%s"
              % (hashlib.sha256(ttext.encode()).hexdigest(),
                 hashlib.sha256(rebuilt.encode()).hexdigest()), file=sys.stderr)
        return 1
    untouched_bytes = len(ttext) - sum(len(t) for _s, _e, _k, t in spans)
    print(f"  spliced {len(spans)} placeholder span(s); {untouched_bytes} byte(s) of the "
          f"template carried through unchanged and re-derived byte-for-byte")

    # ---- POSITIVE ASSERTION 4: the result is valid JSON, and the resolved field equals
    #      the OBSERVED value exactly, compared in decimal, never in float.
    try:
        _r, _t2, check_doc = load_exact_text(text)
    except RefusedConstant as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"REFUSING: the spliced body is not valid JSON: {e}", file=sys.stderr)
        return 1
    for k in placeholders:
        got = check_doc.get(k)
        if not (got == value):
            print(f"REFUSING: resolved {k!r} = {got!r}, expected the observed {value!r}.",
                  file=sys.stderr)
            return 1
    print(f"  re-parsed the spliced body; {len(placeholders)} resolved field(s) each equal "
          f"the observed value in exact decimal")

    if os.path.exists(out) and open(out, "rb").read().decode("utf-8") != text:
        print(f"REFUSING: {out} exists with different content (defect D-1).", file=sys.stderr)
        return 1

    tmp = out + ".tmp.%d" % os.getpid()
    with open(tmp, "wb") as f:
        f.write(text.encode("utf-8"))
    os.replace(tmp, out)                                        # atomic (P-48 rule 4)
    print(f"resolved {placeholders} = {sub} (from {observed}) -> {out}")
    print(f"  out sha256 {hashlib.sha256(text.encode()).hexdigest()}")
    return 0


def load_exact_text(text):
    doc = json.loads(text,
                     parse_int=JsonNumber,
                     parse_float=JsonNumber,
                     parse_constant=_refuse_constant)
    return text.encode("utf-8"), text, doc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
