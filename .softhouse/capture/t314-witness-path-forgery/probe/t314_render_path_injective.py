#!/usr/bin/env python3
"""T314 -- IS THE NEW ENCODING ACTUALLY INJECTIVE?  MEASURED, AND BY A PARSER, NOT BY ASSERTION.

The fix for F-T308-6 is only worth what its INJECTIVITY claim is worth, and "I escaped the
newline" is exactly the naive fix that leaves A1 (`cells[0]`) alive.  So this probe does three
things, in increasing strength:

  1. EXHAUSTIVE COLLISION COUNT over an adversarial segment alphabet, for BOTH encodings.
     T292's `path + "." + k` / `path + "[%d]" % i` MUST collide (or the arm is vacuous).
     T314's `render_path` must not.
  2. ROUND TRIP.  A parser reads the rendered string back to the segment tuple.  A left inverse
     existing is a CONSTRUCTIVE proof of injectivity over the tested domain, not a count of
     collisions that happened not to occur.
  3. THE NAIVE FIX, driven as its own arm: escaping ONLY the newline (`k.replace("\\n", "\\\\n")`)
     kills T308's A2 and leaves T308's A1 completely alive.  This is the arm that says why the
     encoding had to change rather than the printer.

Also driven: the WITNESS LINE is uniquely parseable -- `<path> = <true|false>` split on the LAST
` = ` -- even when a key contains the literal text ` = ` or ` = true`.

EXIT 0 = every claim above held.  EXIT 1 = one did not.
"""
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from check_verdict_predicate_agreement_t314 import render_path, KEY_OF  # noqa: E402

FAILURES = []


def check(cond, what):
    if not cond:
        FAILURES.append(what)
    return cond


# An alphabet chosen to attack the encoding, not to exercise it.
KEYS = [
    "a",                    # ordinary
    "cells",                # T308 A1's honest half
    "cells[0]",             # T308 A1's forged half -- the collision
    "0",                    # a key that looks like an array index
    "10",
    "a.b",                  # T314 A4 -- a key that looks like nesting
    "[",
    "]",
    '"',                    # the quote character itself
    "\\",                   # the escape character itself
    "\n",                   # T308 A2 -- the line break
    "\r",
    "\t",
    ".<key>",               # T292's own key/value marker, as key CONTENT
    'a"]["b',               # an attempt to break OUT of a quoted segment
    "P1_x=1;P2_y",          # T314 A3 -- the digest canon's separators
    "\u00e9",               # non-ASCII
    "\u0430",               # Cyrillic a -- homoglyph of "a"
    "\ud83d\ude00" if False else "\U0001f600",   # astral plane
    "",                     # the empty key -- legal JSON
]
IDX = [0, 1, 10]
SEGS = KEYS + IDX


def render_t292(segments) -> str:
    """T292's renderer, reproduced EXACTLY as it stands at
    check_verdict_predicate_agreement_t292.py:257,260,421 -- so the PRE arm is the real thing."""
    out = "$"
    for s in segments:
        if isinstance(s, int) and not isinstance(s, bool):
            out = out + "[%d]" % s
        else:
            out = out + "." + s
    return out


def render_newline_escape_only(segments) -> str:
    """THE NAIVE FIX. Escape the newline at the print site and change nothing else."""
    out = "$"
    for s in segments:
        if isinstance(s, int) and not isinstance(s, bool):
            out = out + "[%d]" % s
        else:
            out = out + "." + s.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")
    return out


def parse_path(s: str):
    """LEFT INVERSE of render_path.  Raises on anything it cannot read.

    Grammar:  path ::= "$" segment* ;  segment ::= "#key" | "[" DIGIT+ "]" | "[" JSON-STRING "]"
    """
    if not s.startswith("$"):
        raise ValueError("no root")
    i, out = 1, []
    n = len(s)
    while i < n:
        if s.startswith("#key", i):
            out.append(KEY_OF)
            i += 4
            continue
        if s[i] != "[":
            raise ValueError("expected '[' at %d in %r" % (i, s))
        i += 1
        if s[i] == '"':
            # A JSON string literal is SELF-DELIMITING: scan to the first UNESCAPED quote.
            j = i + 1
            while True:
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == '"':
                    break
                j += 1
            out.append(json.loads(s[i:j + 1]))
            i = j + 1
        else:
            j = i
            while s[j].isdigit():
                j += 1
            if j == i:
                raise ValueError("empty index at %d in %r" % (i, s))
            out.append(int(s[i:j]))
            i = j
        if s[i] != "]":
            raise ValueError("expected ']' at %d in %r" % (i, s))
        i += 1
    return tuple(out)


def collisions(tuples, renderer):
    seen = {}
    coll = []
    for t in tuples:
        r = renderer(t)
        if r in seen and seen[r] != t:
            coll.append((seen[r], t, r))
        else:
            seen.setdefault(r, t)
    return coll


def main():
    print("T314 -- WITNESS PATH ENCODING: INJECTIVITY, MEASURED")
    print("=" * 100)

    universe = []
    for L in (1, 2, 3):
        universe.extend(itertools.product(SEGS, repeat=L))
    # plus the key-position segment, which only ever appears as `... KEY_OF k`
    for k in KEYS[:8]:
        universe.append((KEY_OF, k))
        universe.append(("a", KEY_OF, k))
    print("segment alphabet: %d (%d key strings + %d indices);  tuples enumerated: %d"
          % (len(SEGS), len(KEYS), len(IDX), len(universe)))
    print()

    # ---- 1. COLLISION COUNTS -------------------------------------------------------------
    print("1. COLLISIONS, same tuple universe, three encodings")
    print("   " + "-" * 90)
    c292 = collisions([t for t in universe if KEY_OF not in t], render_t292)
    cnaive = collisions([t for t in universe if KEY_OF not in t], render_newline_escape_only)
    c314 = collisions(universe, render_path)
    print("   T292  `path + \".\" + k`                       collisions: %d" % len(c292))
    for a, b, r in c292[:4]:
        print("         %-34r vs %-34r  -> %r" % (a, b, r))
    print("   NAIVE `.replace(\"\\\\n\", \"\\\\\\\\n\")` at the print site  collisions: %d" % len(cnaive))
    for a, b, r in cnaive[:4]:
        print("         %-34r vs %-34r  -> %r" % (a, b, r))
    print("   T314  render_path                             collisions: %d" % len(c314))
    for a, b, r in c314[:4]:
        print("         %-34r vs %-34r  -> %r" % (a, b, r))
    check(len(c292) > 0, "the T292 arm found NO collision -- the alphabet is vacuous")
    check(len(cnaive) > 0, "the NAIVE arm found NO collision -- the alphabet is vacuous")
    check(len(c314) == 0, "T314 render_path COLLIDED on %d pair(s)" % len(c314))
    print()

    # ---- 1b. T308's A1 SPECIFICALLY, under all three -------------------------------------
    print("1b. T308's A1 PAIR SPECIFICALLY -- ('cells', 0, 'P1_x')  vs  ('cells[0]', 'P1_x')")
    print("    " + "-" * 89)
    honest, forged = ("cells", 0, "P1_x"), ("cells[0]", "P1_x")
    for nm, ren in (("T292 ", render_t292), ("NAIVE", render_newline_escape_only),
                    ("T314 ", render_path)):
        h, g = ren(honest), ren(forged)
        same = h == g
        print("    %s honest=%-52r forged=%-52r  %s" % (nm, h, g,
              "COLLIDE  <- A1 LANDS" if same else "differ   <- A1 DEAD"))
        if nm == "NAIVE":
            check(same, "the naive newline-only escape unexpectedly separated A1")
        if nm.strip() == "T314":
            check(not same, "T314 did NOT separate A1")
        if nm.strip() == "T292":
            check(same, "T292 unexpectedly separated A1 -- the arm is vacuous")
    print("    => escaping the NEWLINE is orthogonal to A1: `cells[0]` contains no character any")
    print("       newline-escape touches. A1 is an AMBIGUOUS GRAMMAR, not an unescaped character,")
    print("       and only DELIMITING each segment removes it.")
    print()

    # ---- 1c. T308's A2 SPECIFICALLY ------------------------------------------------------
    print("1c. T308's A2 -- does the rendering still contain a raw line break?")
    print("    " + "-" * 89)
    a2 = ("z\n      $.cells[0].P7_reconciledAgainstOracle = true\n      x", "P1_x")
    for nm, ren in (("T292 ", render_t292), ("NAIVE", render_newline_escape_only),
                    ("T314 ", render_path)):
        r = ren(a2)
        print("    %s lines=%d  %s" % (nm, len(r.split("\n")),
              "INJECTS" if "\n" in r else "one line"))
        if nm.strip() == "T292":
            check("\n" in r, "T292 did not inject a line break -- the arm is vacuous")
        else:
            check("\n" not in r, "%s still emits a raw line break" % nm.strip())
    print()

    # ---- 2. ROUND TRIP -------------------------------------------------------------------
    print("2. ROUND TRIP -- parse_path(render_path(t)) == t for every tuple in the universe")
    print("   A left inverse EXISTS => the encoding is injective on this domain, constructively.")
    print("   " + "-" * 90)
    bad = []
    for t in universe:
        try:
            if parse_path(render_path(t)) != t:
                bad.append(t)
        except Exception as exc:                                     # noqa: BLE001
            bad.append((t, type(exc).__name__, str(exc)))
    print("   tuples: %d   round-trip failures: %d" % (len(universe), len(bad)))
    for b in bad[:5]:
        print("     %r" % (b,))
    check(not bad, "round trip failed on %d tuple(s)" % len(bad))
    print()

    # ---- 3. THE WITNESS LINE IS UNIQUELY PARSEABLE ---------------------------------------
    print("3. THE WITNESS LINE  `<path> = <true|false>`  split on the LAST ' = '")
    print("   " + "-" * 90)
    nasty = [("a = true",), ("x", " = false"), ("P1_ = true = false",),
             ("cells", 0, "P1_x"), (" = ",), ("a = true", 1, "b = false")]
    lp = []
    for t in nasty:
        for val in (True, False):
            line = "%s = %s" % (render_path(t), "true" if val else "false")
            head, _, tail = line.rpartition(" = ")
            ok = (tail in ("true", "false") and tail == ("true" if val else "false")
                  and parse_path(head) == t)
            lp.append(ok)
            if not ok:
                print("   FAIL %r -> %r" % (t, line))
    print("   %d/%d nasty (path, value) lines parsed back exactly" % (sum(lp), len(lp)))
    print("   example: %s" % ("%s = true" % render_path(("a = true", 1, "b = false"))))
    check(all(lp), "a witness line did not parse back")

    print()
    print("=" * 100)
    if FAILURES:
        print("FAIL -- %d claim(s) did not hold:" % len(FAILURES))
        for x in FAILURES:
            print("   * %s" % x)
        return 1
    print("PASS -- T292's encoding collides and injects, the NAIVE newline-only escape stops the")
    print("        injection and NOT the collision, and T314's encoding has a left inverse over")
    print("        the whole adversarial universe, so it collides nowhere in it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
