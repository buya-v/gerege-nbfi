#!/usr/bin/env python3
"""T163 — VERIFY, do not accept on report, A2-11's claim that NO COMMITTED CAPTURE IS
AFFECTED by the `resolve7.py` P-25 defect.

The defect: resolve7.py:24-25 `json.load(open(...))` with no `parse_float`, then :36
`json.dumps(...)`.  Every number in the template makes a round trip through a binary
double, and json.dumps re-emits `repr(float)`.  A literal survives BYTE-IDENTICALLY iff
its own text is already the shortest round-trip repr of its double.  `1200000` (int) is
safe; `1200000.00` is NOT — it comes back `1200000.0`.

WHAT THIS AUDITS, and it is deliberately WIDER than resolve7.py's own output
--------------------------------------------------------------------------
resolve7.py wrote exactly one committed artefact.  Auditing only that artefact would
answer "did THIS script corrupt something", which is the narrow question.  The question
that matters is the CLASS question: *does any committed artefact in this capture carry a
numeric token that a Python float round trip would not reproduce byte-for-byte?*  So this
walks the WHOLE capture — req/, out/, sql/ and the top level — and inspects every numeric
token in every file the JSON parser accepts.

HOW THE TOKENS ARE OBTAINED — not by regex (P-48 rule 1)
--------------------------------------------------------
`json.loads` calls `parse_int`/`parse_float` with the ORIGINAL SOURCE TEXT of each numeric
token.  Hooking them yields every number exactly as written, from the real parser, with no
regex guessing about what is a number and what is text inside a string.

THE ONE DELIBERATE USE OF `float` (P-25)
----------------------------------------
The line marked SIMULATE below calls `float()` on purpose: it is SIMULATING THE DEFECT,
which is the only way to measure it.  No money conclusion is drawn from a float here — the
comparison is between two STRINGS, and the residue is computed in `decimal`.

GUARD SHAPE (P-35): every assertion is POSITIVE — "N files were enumerated, N tokens were
inspected, and each token's text equals its float round-trip text".  ZERO FILES
ENUMERATED IS AN ERROR, not a pass.  Nothing is swallowed: every file that is not parsed
as JSON is named in the SKIP REGISTER with the exact reason, and the registers are printed
in full, not counted.
"""
import decimal
import hashlib
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
FAILS = []
DEC = decimal.Context(prec=60)


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        FAILS.append(label)


def numeric_tokens(text):
    """Every numeric token in `text`, as the source text the JSON parser saw."""
    toks = []

    def hook(kind):
        def f(s):
            toks.append((kind, s))
            return decimal.Decimal(s) if kind == "float" else int(s)
        return f

    json.loads(text, parse_float=hook("float"), parse_int=hook("int"))
    return toks


def defect_render(kind, tok):
    """Exactly what resolve7.py's json.load->json.dumps round trip re-emits for `tok`."""
    if kind == "int":
        return json.dumps(int(tok))
    return json.dumps(float(tok))            # SIMULATE the defect. Deliberate float.


# ---------------------------------------------------------------- enumerate
files = []
for sub in ("req", "out", "sql"):
    root = os.path.join(DIR, sub)
    if not os.path.isdir(root):
        print("ERROR: expected directory missing: %s" % sub, file=sys.stderr)
        sys.exit(2)
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            files.append(os.path.relpath(os.path.join(dp, f), DIR))
for f in sorted(os.listdir(DIR)):
    if os.path.isfile(os.path.join(DIR, f)):
        files.append(f)
files = sorted(set(files))

parsed, skipped, tokens, offenders = [], [], [], []
for rel in files:
    p = os.path.join(DIR, rel)
    try:
        raw = open(p, "rb").read()
    except OSError as e:
        skipped.append((rel, "UNREADABLE: %s" % e))
        continue
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        skipped.append((rel, "NOT-UTF8: %s" % e))
        continue
    try:
        toks = numeric_tokens(text)
    except Exception as e:                    # named and registered, never swallowed
        skipped.append((rel, "NOT-JSON: %s: %s" % (type(e).__name__, e)))
        continue
    parsed.append(rel)
    for kind, tok in toks:
        tokens.append((rel, kind, tok))
        emitted = defect_render(kind, tok)
        if emitted != tok:
            exact = DEC.create_decimal(tok)
            residue = DEC.create_decimal(emitted) - exact
            offenders.append((rel, kind, tok, emitted, str(residue)))

print("=" * 78)
print("T163 — float-round-trip audit of the WHOLE committed tierA-a2 capture")
print("=" * 78)
print()
print("POPULATION")
print("  files walked (req/ out/ sql/ + top level) : %d" % len(files))
print("  files the JSON parser ACCEPTED           : %d" % len(parsed))
print("  files registered as SKIPPED              : %d" % len(skipped))
print("  numeric tokens inspected                 : %d" % len(tokens))
print()
print("SKIP REGISTER — printed in full, never counted-and-hidden (P-35 / the G-9 failure)")
if not skipped:
    print("  (empty)")
by_reason = {}
for rel, why in skipped:
    by_reason.setdefault(why.split(":")[0], []).append((rel, why))
for reason in sorted(by_reason):
    rows = by_reason[reason]
    print("  %-12s %d file(s)" % (reason, len(rows)))
    for rel, why in sorted(rows):
        print("      %-58s %s" % (rel, why[:70]))
print()

# ---------------------------------------------------------------- assertions
check("ENUMERATION IS NON-EMPTY — zero files walked would be an ERROR, not a pass",
      len(files) > 0, "%d files walked" % len(files))
check("PARSE SET IS NON-EMPTY — zero JSON files would be an ERROR, not a pass",
      len(parsed) > 0, "%d files parsed as JSON" % len(parsed))
check("TOKEN SET IS NON-EMPTY — an audit that inspected zero numbers proves nothing",
      len(tokens) > 0, "%d numeric tokens inspected" % len(tokens))
check("EVERY SKIPPED FILE IS ACCOUNTED FOR BY NAME AND REASON",
      len(skipped) == sum(len(v) for v in by_reason.values()),
      "%d skipped, %d registered" % (len(skipped), sum(len(v) for v in by_reason.values())))

print()
print("THE CLASS QUESTION — is any committed numeric token NOT byte-preserved by a float")
print("round trip?  (i.e. would the defect have altered it, had it passed through)")
print()
print("  resolve7.py touches numbers on BOTH sides, so the population is split on both:")
print("    REQUEST  side  req/**  — bodies resolve7.py/mkreq*.py WRITE and cap.sh POSTs.")
print("                             A defect here is CORRUPTION OF A COMMITTED ARTEFACT.")
print("    RESPONSE side  out/**  — raw curl bytes from the oracle. No Python wrote them,")
print("                             so they CANNOT be corrupted by this defect — but")
print("                             resolve7.py:25 json.load()s them with no parse_float,")
print("                             so a value read from here and injected into a request")
print("                             is corrupted ON THE WAY BACK OUT.  These rows are the")
print("                             AMMUNITION: they prove the mangling-prone literals are")
print("                             really present in this corpus.")
print()
req_off = [o for o in offenders if o[0].startswith("req/")]
out_off = [o for o in offenders if not o[0].startswith("req/")]

distinct = sorted({(k, t, e, r) for _f, k, t, e, r in offenders})
print("  DISTINCT offending literals across the whole capture (%d distinct, %d occurrences):"
      % (len(distinct), len(offenders)))
print("    %-6s %-26s %-26s %s" % ("kind", "as committed", "as the defect emits", "exact residue"))
for k, t, e, r in distinct:
    print("    %-6s %-26s %-26s %s" % (k, t, e, r))
print()
percol = {}
for f, k, t, e, r in offenders:
    percol[f] = percol.get(f, 0) + 1
print("  FILES CARRYING AT LEAST ONE (%d files) — full list, not a sample:" % len(percol))
for f in sorted(percol):
    print("    %-62s %4d token(s)   [%s]"
          % (f, percol[f], "REQUEST" if f.startswith("req/") else "RESPONSE"))
print()

check("REQUEST SIDE: NO COMMITTED REQUEST BODY CARRIES A TOKEN THE DEFECT WOULD ALTER "
      "— this is A2-11's exculpatory claim, and it HOLDS",
      len(req_off) == 0,
      "%d offending token(s) in req/ out of %d tokens inspected there"
      % (len(req_off), sum(1 for f, _k, _t in tokens if f.startswith("req/"))))
check("RESPONSE SIDE IS NON-EMPTY — the danger is CONCRETE, not hypothetical: the oracle "
      "really does emit numeric(19,6) literals that a float round trip reshapes",
      len(out_off) > 0,
      "%d occurrences across %d response captures"
      % (len(out_off), len({o[0] for o in out_off})))
check("ALL residues are EXACTLY ZERO — the reshaping here is of the TEXT, not of the value; "
      "the defect's damage in this corpus is to the WIRE FORM, and value loss needs >17 "
      "significant digits, which MathContext(19, HALF_UP) permits",
      all(DEC.create_decimal(r) == 0 for *_x, r in offenders),
      "max |residue| = %s" % max([abs(DEC.create_decimal(r)) for *_x, r in offenders] or [0]))

# --------------------------------------------- the narrow question, on resolve7's output
print()
print("THE NARROW QUESTION — the artefacts resolve7.py itself WROTE")
produced = sorted(f for f in os.listdir(os.path.join(DIR, "req")) if "resolved" in f)
print("  resolve7.py's output convention is req/*-resolved.json; found: %r" % produced)
check("resolve7.py produced EXACTLY ONE committed artefact",
      produced == ["a2-7-loan-220-resolved.json"], "found %r" % produced)

tmpl = os.path.join(DIR, "req", "a2-7-loan-220.json")
res = os.path.join(DIR, "req", "a2-7-loan-220-resolved.json")
obs = os.path.join(DIR, "out", "A2-210-create-cash-nine-mandatory.json")
tb, rb, ob = (open(p, "rb").read() for p in (tmpl, res, obs))
print("  template  %-34s sha256 %s" % (os.path.basename(tmpl), hashlib.sha256(tb).hexdigest()))
print("  resolved  %-34s sha256 %s" % (os.path.basename(res), hashlib.sha256(rb).hexdigest()))
print("  observed  %-34s sha256 %s" % (os.path.basename(obs), hashlib.sha256(ob).hexdigest()))

tt = numeric_tokens(tb.decode())
rt = numeric_tokens(rb.decode())
check("EVERY numeric token in the TEMPLATE is an int — none can be float-mangled",
      all(k == "int" for k, _ in tt),
      "%d tokens, kinds=%s" % (len(tt), sorted({k for k, _ in tt})))
check("EVERY numeric token in the RESOLVED BODY THAT WAS POSTED is an int",
      all(k == "int" for k, _ in rt),
      "%d tokens: %s" % (len(rt), ", ".join(t for _, t in rt)))
resolved_doc = json.loads(rb.decode(), parse_float=decimal.Decimal)
check("the POSTed body carries principal 1200000 EXACTLY, as an int",
      resolved_doc.get("principal") == 1200000 and isinstance(resolved_doc.get("principal"), int),
      "principal=%r (%s)" % (resolved_doc.get("principal"), type(resolved_doc.get("principal")).__name__))
ot = numeric_tokens(ob.decode())
check("EVERY numeric token in the OBSERVED RESPONSE resolve7.py read is an int too — "
      "the SECOND corruption path (resp[key] is also json.load()ed with no parse_float) "
      "was not exercised either",
      all(k == "int" for k, _ in ot),
      "%d tokens: %s" % (len(ot), ", ".join(t for _, t in ot)))
observed_doc = json.loads(ob.decode(), parse_float=decimal.Decimal)
check("the resolved productId equals the OBSERVED resourceId — not a guessed value",
      resolved_doc.get("productId") == observed_doc.get("resourceId"),
      "resolved productId=%r, observed resourceId=%r"
      % (resolved_doc.get("productId"), observed_doc.get("resourceId")))

# the template and the resolved body must differ ONLY in the placeholder span
rebuilt = tb.decode().replace('"__PRODUCT_ID__"', json.dumps(observed_doc["resourceId"]))
check("the committed resolved body IS the template with ONLY the placeholder substituted "
      "— byte-for-byte, so no other literal was reshaped",
      rebuilt == rb.decode(),
      "rebuilt sha256 %s vs committed %s"
      % (hashlib.sha256(rebuilt.encode()).hexdigest(), hashlib.sha256(rb).hexdigest()))

# --------------------------------------------------------------- wire-bytes census
# Measured separately in prove-cap8-wire-bytes.py: `curl -d @FILE`, which cap.sh uses,
# STRIPS carriage returns and newlines out of a file body.  So for every committed capture
# that carried a body, the bytes in req/ are NOT the bytes that reached the oracle.  This
# section states the size of that gap and, more importantly, whether it touched a NUMBER.
print()
print("WIRE-BYTES CENSUS — for how many committed captures do the req/ bytes differ from")
print("what cap.sh actually put on the wire, and did that ever alter a numeric token?")
bodied, wire_differs, wire_token_differs = [], [], []
outdir = os.path.join(DIR, "out")
for h in sorted(os.listdir(outdir)):
    if not h.endswith(".http"):
        continue
    rec = open(os.path.join(outdir, h)).read()
    bf = [l.split(": ", 1)[1] for l in rec.split("\n") if l.startswith("body-file: ")]
    if not bf:
        continue
    bodied.append(h)
    p = os.path.join(DIR, bf[0])
    if not os.path.exists(p):
        skipped.append((bf[0], "BODY-FILE-MISSING: referenced by out/%s" % h))
        continue
    fb = open(p, "rb").read()
    wire = fb.replace(b"\r", b"").replace(b"\n", b"")     # exactly what `curl -d @` does
    if wire != fb:
        wire_differs.append(h)
        try:
            if numeric_tokens(fb.decode()) != numeric_tokens(wire.decode()):
                wire_token_differs.append(h)
        except Exception as e:
            skipped.append((bf[0], "WIRE-REPARSE-FAILED: %s" % e))
print("  captures that carried a request body        : %d" % len(bodied))
print("  ... whose wire bytes differ from the file   : %d" % len(wire_differs))
print("  ... where a NUMERIC TOKEN differs           : %d" % len(wire_token_differs))
check("WIRE-BYTES CENSUS IS NON-EMPTY — a census over zero captures would be an ERROR",
      len(bodied) > 0, "%d bodied captures" % len(bodied))
check("THE WIRE/FILE GAP IS REAL AND CORPUS-WIDE — it is not a hypothetical, and it is "
      "why 'the committed req/ file' was never a record of what was SENT",
      len(wire_differs) > 0,
      "%d of %d bodied captures" % (len(wire_differs), len(bodied)))
check("THE GAP IS WHITESPACE ONLY — NO numeric token differs between file and wire on "
      "any committed capture, so no observation is invalidated by it",
      len(wire_token_differs) == 0,
      "%d capture(s) with a differing numeric token: %s"
      % (len(wire_token_differs), wire_token_differs[:10]))

print()
print("FAILURES: %d" % len(FAILS))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
