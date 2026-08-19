#!/usr/bin/env python3
"""T57 float scan over .softhouse/vectors/.

Not a grep. It TOKENISES each file with json.JSONDecoder's own scanner via a parse_float
hook, so it sees exactly what a JSON parser would see, and it separately re-lexes the raw
bytes for any bare number token containing '.', 'e' or 'E'. Money in this store is an
integer string in minor units; a bare JSON number carrying an exponent or a decimal point
anywhere in the store is a rejection.

Exits non-zero on the first offending token.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
VEC = os.path.join(ROOT, ".softhouse", "vectors")

# A bare JSON number token: not inside a string. Strip strings first, then look for numbers.
STRING = re.compile(r'"(?:[^"\\]|\\.)*"', re.S)
NUMBER = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')

bad = []
files = 0
tokens = 0

for dirpath, _, names in os.walk(VEC):
    for name in sorted(names):
        if not name.endswith(".json"):
            continue
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, ROOT)
        files += 1
        raw = open(path, encoding="utf-8").read()

        # (a) the parser's own view: any float the decoder constructs is a violation
        floats = []
        json.loads(raw, parse_float=lambda s: floats.append(s) or 0)
        for f in floats:
            bad.append((rel, "json.parse_float", f))

        # (b) an independent lex of the raw bytes with all string literals blanked out
        stripped = STRING.sub(lambda m: " " * (m.end() - m.start()), raw)
        for m in NUMBER.finditer(stripped):
            tokens += 1
            tok = m.group(0)
            if any(ch in tok for ch in ".eE"):
                line = raw.count("\n", 0, m.start()) + 1
                bad.append((rel, "bare token line %d" % line, tok))

print("scanned %d json files under %s" % (files, os.path.relpath(VEC, ROOT)))
print("bare JSON number tokens examined: %d" % tokens)
if bad:
    for rel, where, tok in bad:
        print("  FLOAT %s  %s  %r" % (rel, where, tok))
    sys.exit("FAIL: %d offending token(s)" % len(bad))
print("ZERO bare JSON number tokens containing '.', 'e' or 'E'. PASS.")
