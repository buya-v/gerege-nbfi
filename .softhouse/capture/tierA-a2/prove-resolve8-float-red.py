#!/usr/bin/env python3
"""T163 — A2-11's prover, WIDENED, run against BOTH the pre-fix and the post-fix resolver.

  python3 prove-resolve8-float-red.py            # runs the battery against both, asserts
                                                 # resolve7.py RED and resolve8.py GREEN

DERIVED FROM, NOT REPLACING, `.softhouse/reviews/A2-11/prove-resolve7-float-red.py`.
A2-11 raised this defect and drove it red first; that file is left byte-identical (it is
A2-11's committed review evidence, T114's standing ruling).  This is a scratch copy with
the widenings listed below, each stated because a widened prover that does not say what it
widened is indistinguishable from a replaced one.

WHAT I WIDENED, AND WHY
-----------------------
W1  RIG PATH.  A2-11 hard-coded `RIG` to its own worktree
    (`.../agent-a3ac3d56d665ff7da/...`), which no longer exists, so the prover could not
    be re-run by anyone.  Resolved from this file's own directory now.

W2  BOTH SCRIPTS, ONE ARTEFACT.  A2-11 ran the battery against resolve7.py only.  T163's
    brief requires showing the SAME battery failing pre-fix and passing post-fix, so the
    battery is a function of the script under test and both runs are in one transcript.

W3  *** THE TWO TERMINAL ASSERTIONS WERE INVERTED, AND THIS IS THE MATERIAL WIDENING. ***
    A2-11 wrote  `check("RED: at least one realistic money literal is NOT byte-preserved",
    len(differed) > 0)`.  That PASSES when the defect is PRESENT, so A2-11's prover EXITS 0
    AGAINST THE DEFECTIVE SCRIPT and would EXIT 1 against a correct one.  As a
    demonstration of a defect that is fine and it is what A2-11 needed.  As a GUARD it is
    backwards, and it is precisely P-35's negative-assertion shape: it can only ever
    certify that the bug is still there.  Rephrased POSITIVELY — *every literal in the
    battery is byte-preserved, and the count of literals inspected is non-zero* — which
    fails pre-fix and passes post-fix, which is what P-22 asks for.

W4  TWO `check(..., True, ...)` CALLS THAT COULD NOT FAIL (P-22) were replaced by real
    measurements:
      * "no money value was corrupted by A2-7's own use of resolve7.py" was the literal
        constant `True`.  It now RE-RUNS the script under test on the committed template
        and the committed observed response and compares the output BYTE-FOR-BYTE against
        the committed `req/a2-7-loan-220-resolved.json`.
      * "it cannot refuse a float, exit 0" was the literal constant `True`.  Exit codes
        are now recorded and asserted.

W5  THE SECOND CORRUPTION PATH, WHICH A2-11 NEVER EXERCISED.  A2-11 varied only the
    TEMPLATE.  resolve7.py:25 also `json.load`s the OBSERVED RESPONSE with no
    `parse_float`, so a MONEY-VALUED key read out of a capture is corrupted on the way IN.
    That is not hypothetical: T163's audit found `1200000.000000` and 23 other
    mangling-prone literals in 236 places across 21 committed response captures
    (audit-req-float-roundtrip.py).  The battery now resolves from such a response.

W6  NESTED LITERALS.  A2-11 tested a top-level `principal` only.  resolve7.py
    re-serialises the WHOLE document, so a literal nested in an object or an array is
    reshaped too.  Added.

W7  VALUE LOSS, NOT ONLY FORM LOSS.  A2-11 listed `12345678901234567890.12` but never
    asserted that its residue is NON-ZERO.  The residue is now computed in `decimal` and
    asserted non-zero, which separates "the wire form changed" from "the number changed".

W8  `NaN` / `Infinity` INGRESS.  Python's `json` accepts these non-standard tokens by
    default and produces binary floats for them.  Neither script was ever tested on one.

W10 THE VALUE EXTRACTOR ITSELF WAS BROKEN AGAINST A CORRECT RESOLVER.  A2-11 read the
    emitted principal with `[l for l in out.split("\\n") if "principal" in l][0].split(":")[1]`
    — which assumes the output is `json.dumps(indent=2)`, one key per line.  Against a
    resolver that PRESERVES the template's formatting (the whole point of the fix) it reads
    the wrong span: it returned `46,"principal"` as the principal and reported the FIXED
    script as still broken.  A prover whose extractor only works on the defective output
    shape is P-22 aimed at the fix.  Replaced with a parse — see `raw_token`.

W9  WHOLE-DOCUMENT BYTE PRESERVATION.  Beyond the one literal under test, the battery
    asserts the output is the template with ONLY the placeholder span changed — which is
    the property that actually makes a capture rig trustworthy.

WHAT I DID NOT CHANGE: A2-11's retracted hypothesis about `4057599.35` is carried through
verbatim in substance, because a recorded wrong first guess is evidence and deleting it
would be the opposite of the honesty rule.

Runs in a temp dir against COPIES.  Never mutates the committed rig.  Never contacts the
reference oracle.
"""
import decimal
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

RIG = os.path.dirname(os.path.abspath(__file__))          # W1
DEC = decimal.Context(prec=60)


class _Raw(str):
    """A JSON number kept as its exact source text."""


def raw_token(text, key):
    """The EXACT source text of `text`'s top-level `key` number.  W10.

    A2-11's extractor was `[l for l in out.split("\\n") if "principal" in l][0].split(":")[1]`,
    which silently assumes the output is `json.dumps(indent=2)` — one key per line.  Against
    a resolver that PRESERVES the template's own formatting (which is the whole point of the
    fix) it reads the wrong span and returned `46,"principal"` as the principal.  A value
    extractor that mis-reads correct output is the P-22 shape pointed at the fix instead of
    the defect, so it is replaced with a parse: `json.loads` hands `parse_int`/`parse_float`
    the ORIGINAL TOKEN TEXT, which is exactly what is wanted and is format-independent.
    """
    doc = json.loads(text, parse_int=_Raw, parse_float=_Raw,
                     parse_constant=lambda n: _Raw(n))
    v = doc.get(key)
    return str(v) if v is not None else None


def battery(script):
    """Run the whole battery against `script`.  Returns (rows, notes).

    rows  : list of (label, ok, detail) — every one a POSITIVE assertion (W3).
    notes : list of printable observation lines that are evidence, not assertions.
    """
    rows, notes = [], []

    def check(label, cond, detail=""):
        rows.append((label, bool(cond), detail))

    d = tempfile.mkdtemp(prefix="t163-%s-" % os.path.splitext(script)[0])
    shutil.copy(os.path.join(RIG, script), d)

    def run(tmpl_text, obs_obj, key="resourceId"):
        t = os.path.join(d, "t.json")
        o = os.path.join(d, "o.json")
        ob = os.path.join(d, "obs.json")
        with open(t, "w") as fh:
            fh.write(tmpl_text)
        with open(ob, "w") as fh:
            fh.write(obs_obj if isinstance(obs_obj, str) else json.dumps(obs_obj))
        if os.path.exists(o):
            os.remove(o)
        r = subprocess.run([sys.executable, os.path.join(d, script), t, ob, key, o],
                           capture_output=True, text=True)
        got = open(o).read() if os.path.exists(o) else None
        return r.returncode, got, (r.stderr or "").strip()

    def one_literal(literal):
        """Resolve a template whose `principal` is `literal`; return the emitted bytes."""
        rc, out, err = run('{"productId":"__PRODUCT_ID__","principal":%s}\n' % literal,
                           {"resourceId": 46})
        if out is None:
            return rc, None, err
        return rc, raw_token(out, "principal"), err

    # ---------------- CONTROL, from A2-11: the real A2-7 template was unharmed ----------
    with open(os.path.join(RIG, "req", "a2-7-loan-220.json"), "rb") as fh:
        real = json.loads(fh.read().decode(), parse_float=decimal.Decimal)
    check("CONTROL: a2-7-loan-220.json principal is an int, not a decimal literal",
          isinstance(real["principal"], int),
          "principal=%r (%s)" % (real["principal"], type(real["principal"]).__name__))

    # ---- W4: this was the literal constant `True` in A2-11's prover. Now measured. ------
    tmplp = os.path.join(RIG, "req", "a2-7-loan-220.json")
    obsp = os.path.join(RIG, "out", "A2-210-create-cash-nine-mandatory.json")
    committed = open(os.path.join(RIG, "req", "a2-7-loan-220-resolved.json"), "rb").read()
    o2 = os.path.join(d, "reproduce.json")
    r2 = subprocess.run([sys.executable, os.path.join(d, script), tmplp, obsp, "resourceId", o2],
                        capture_output=True, text=True)
    got2 = open(o2, "rb").read() if os.path.exists(o2) else b""
    check("W4: re-running THIS script on the two committed inputs reproduces the committed "
          "req/a2-7-loan-220-resolved.json BYTE-FOR-BYTE (measured, not asserted)",
          r2.returncode == 0 and got2 == committed,
          "rc=%d  emitted sha256=%s  committed sha256=%s"
          % (r2.returncode, hashlib.sha256(got2).hexdigest(),
             hashlib.sha256(committed).hexdigest()))

    # ---------------- A2-11's RETRACTED HYPOTHESIS, carried verbatim in substance --------
    rc, got, _e = one_literal("4057599.35")
    notes.append("A2-11's retracted hypothesis: template 4057599.35 -> emitted %s (rc=%d). "
                 "repr() round-trips it byte-identically, so A2-11's first RED was wrong "
                 "and A2-11 recorded that rather than deleting it." % (got, rc))
    exact = decimal.Decimal("4057599.35")
    binary = decimal.Decimal(float("4057599.35"))
    notes.append("  the double actually held in memory is %s; residue (double - exact) = %s"
                 % (binary, binary - exact))

    # ---------------- W3: the battery, phrased POSITIVELY ------------------------------
    cases = [
        ("1200000.00", "MNT stored to 2 decimals (CLAUDE.md non-negotiable)"),
        ("1200000.000000", "exactly what Fineract's numeric(19,6) emits"),
        ("0.10", "ten mongo"),
        ("12345678901234567890.12", "past double precision; MathContext(19,HALF_UP) permits 19"),
    ]
    differed, inspected = [], 0
    notes.append("")
    notes.append("  %-26s %-26s %-10s %s" % ("template literal", "bytes the script writes",
                                             "identical", "note"))
    for lit, note in cases:
        rc, got, _e = one_literal(lit)
        inspected += 1
        same = (got == lit)
        if not same:
            differed.append((lit, got))
        notes.append("  %-26s %-26s %-10s %s" % (lit, got, "yes" if same else "NO", note))

    check("W3 (POSITIVE): every realistic money literal is emitted BYTE-IDENTICALLY",
          len(differed) == 0,
          "; ".join("%s -> %s" % c for c in differed) or "all %d preserved" % inspected)
    check("W3: the battery inspected a NON-ZERO number of literals — a battery that "
          "inspected none would be an ERROR, not a pass",
          inspected == len(cases), "%d of %d" % (inspected, len(cases)))

    # ---------------- W7: value loss, not only form loss --------------------------------
    big = "12345678901234567890.12"
    rc, got, _e = one_literal(big)
    if got is None:
        check("W7: the >17-significant-digit literal survives with ZERO residue", False,
              "no output was produced (rc=%d)" % rc)
    else:
        try:
            residue = DEC.create_decimal(got) - DEC.create_decimal(big)
        except decimal.InvalidOperation:
            residue = None
        check("W7: the >17-significant-digit literal survives with ZERO residue — this "
              "separates a changed WIRE FORM from a changed NUMBER",
              residue == 0,
              "emitted %s ; residue = %s" % (got, residue))

    # ---------------- W5: the OBSERVED-RESPONSE path, never exercised by A2-11 -----------
    # `1200000.000000` is a literal that really occurs in 21 committed response captures.
    rc, out, err = run('{"productId":"__PRODUCT_ID__"}\n',
                       '{"resourceId": 1200000.000000}\n')
    emitted = raw_token(out, "productId") if out is not None else None
    notes.append("")
    notes.append("  W5 observed-response path: resp resourceId 1200000.000000 -> emitted %r "
                 "(rc=%d)" % (emitted, rc))
    check("W5: a MONEY-VALUED key read OUT OF A COMMITTED CAPTURE is spliced into the "
          "request body byte-for-byte (1200000.000000, which occurs in 21 captures)",
          emitted == "1200000.000000",
          "emitted %r" % emitted)

    # ---------------- W6: nested literals -----------------------------------------------
    nested = ('{"productId":"__PRODUCT_ID__",'
              '"charges":[{"amount":1200000.00}],'
              '"terms":{"rate":0.10}}\n')
    rc, out, err = run(nested, {"resourceId": 46})
    ok_nested = out is not None and "1200000.00" in out and "0.10" in out
    notes.append("  W6 nested literals: emitted %r" % (out.replace("\n", " ") if out else None))
    check("W6: literals NESTED in an array and an object are preserved too — the script "
          "re-serialises the whole document, so top-level is not the boundary",
          ok_nested, "emitted contains 1200000.00 and 0.10: %s" % ok_nested)

    # ---------------- W8: NaN / Infinity ingress ----------------------------------------
    rc, out, err = run('{"productId":"__PRODUCT_ID__","principal":NaN}\n', {"resourceId": 46})
    notes.append("  W8 NaN ingress: rc=%d, wrote a body: %s" % (rc, out is not None))
    check("W8: a non-standard NaN/Infinity token is REFUSED (rc!=0) and NO body is "
          "written — these are binary floats in every parser that accepts them",
          rc != 0 and out is None, "rc=%d, body written=%s" % (rc, out is not None))

    # ---------------- W9: whole-document byte preservation -------------------------------
    doc = ('{\n  "productId": "__PRODUCT_ID__",\n  "principal": 1200000.00,\n'
           '  "note": "spacing   and   order   must   survive",\n  "z": 1,\n  "a": 2\n}\n')
    rc, out, err = run(doc, {"resourceId": 46})
    expect = doc.replace('"__PRODUCT_ID__"', "46")
    check("W9: the output is the template with ONLY the placeholder span changed — "
          "whitespace, key order and every other literal byte-identical",
          out == expect,
          "emitted sha256=%s expected sha256=%s"
          % (hashlib.sha256((out or "").encode()).hexdigest(),
             hashlib.sha256(expect.encode()).hexdigest()))

    shutil.rmtree(d)
    return rows, notes


def report(script, expect_pass):
    print("=" * 78)
    print("BATTERY vs %s      (expected: %s)" % (script, "GREEN" if expect_pass else "RED"))
    print("=" * 78)
    rows, notes = battery(script)
    for n in notes:
        print(n)
    print()
    for label, ok, detail in rows:
        print(("  PASS  " if ok else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    failed = [l for l, ok, _d in rows if not ok]
    print()
    print("  -> %d assertion(s), %d FAILED  => %s"
          % (len(rows), len(failed), "GREEN" if not failed else "RED"))
    print()
    return len(failed) == 0


if __name__ == "__main__":
    pre_green = report("resolve7.py", expect_pass=False)
    post_green = report("resolve8.py", expect_pass=True)

    print("=" * 78)
    print("P-22 VERDICT — the prover must be FALSIFIABLE, so it must go RED on the "
          "pre-fix bytes")
    print("=" * 78)
    verdict = []
    print(("  PASS  " if not pre_green else "  FAIL  ")
          + "resolve7.py (PRE-FIX, unchanged by T163) drives the battery RED")
    if pre_green:
        verdict.append("resolve7.py did not go red — the prover proves nothing")
    print(("  PASS  " if post_green else "  FAIL  ")
          + "resolve8.py (POST-FIX) drives the same battery GREEN")
    if not post_green:
        verdict.append("resolve8.py is not green — the fix is incomplete")
    print()
    print("FAILURES: %d" % len(verdict))
    for v in verdict:
        print("  - " + v)
    sys.exit(1 if verdict else 0)
