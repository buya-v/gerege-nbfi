#!/usr/bin/env python3
"""
T241 — G-8 STANDING RULE item 1: the sentence-by-sentence scope-table rebuild, run BEFORE editing
the section.

STANDING RULE 1, quoted verbatim from `.softhouse/gates.md`:

    1. **Nobody edits this section without rebuilding the sentence-by-sentence scope table.** Not a
       grep for the sentence you are changing -- a rebuild, claim by claim, of what every sentence
       asserts and the domain it was measured over. T129's rebuild ran to 117 rows and found six
       failures, **all six of them scope or disposition statements in a section whose measurements
       are perfect**. That ratio is the whole reason for this rule.

WHAT THIS SCRIPT DOES AND DOES NOT DO.  The MECHANICAL half -- enumerating every sentence and
flagging the scope-bearing ones -- is here.  The JUDGEMENT half -- what each flagged sentence
asserts, the domain it was measured over, and whether that domain is on the RIGHT AXIS -- is
recorded BY HAND in `SCOPE-TABLE-T241.md` beside this file.  A script cannot discharge rule 1; it
can only produce the denominator honestly.

TWO SECTIONS ARE ENUMERATED SEPARATELY, because they have different statuses:
  * the LIVE G-8 section        `## G-8 - TWO phenomena ...`  ->  the next `## ` heading
  * the SUPERSEDED history block `## G-8-NOTICE ...`          ->  the next `## ` heading

A NOTE ON T223's INSTRUMENT, recorded because it bears on how much of the section prior rebuilds
actually covered.  `.softhouse/capture/t223-g8-region-predicate/src/scope_table_t223.py` bounds the
section as `## G-8 - TWO phenomena` .. `## G-8-NOTICE`.  In `gates.md` AS IT STANDS TODAY there are
TWO other `## ` sections between those markers (`## G-9` and `## G-10`), so that boundary would
today swallow both.  T241 does NOT claim this was true when T223 ran -- G-9 and G-10 may have been
added afterwards, and T241 did not check.  [UNVERIFIED: whether T223's run was over-scoped.]
This script takes the next `## ` heading instead, so it cannot have that failure mode.

P-58: this census is cross-checked with a SECOND named engine (`git grep -P`) by the sibling script
`census_two_engines_t241.sh`; both figures are reported in `SCOPE-TABLE-T241.md`.
P-72: the concept nets below are calibrated on a known POSITIVE and a known NEGATIVE that are not
substrings of one another; `--calibrate` runs that check and exits non-zero if it fails.
P-75: no bare `grep` and no `rg` anywhere in this instrument -- it uses python `re` only.
P-25: this script computes no money and contains no float.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
GATES = os.path.join(REPO, ".softhouse", "gates.md")

LIVE_START = "## G-8 — TWO phenomena"
HIST_START = "## G-8-NOTICE"

# ---------------------------------------------------------------------------------------------
# THE CONCEPT NETS.  Deliberately wider than "the sentences T241 is changing" (STANDING RULE 3).
# A sentence is SCOPE-BEARING if it hits any net: it then makes a claim whose truth depends on a
# domain, and rule 1 requires that domain to be named and checked.
# ---------------------------------------------------------------------------------------------
NETS = [
    # --- the three records T219 moved: this is the population rule 1 fires over for T241 ---
    (r"largest\s+(unamortized\s+)?residual", "R1 states the largest residual"),
    (r"largest\s+failing\s+(principal|disbursement)", "R2 states the largest failing principal/disbursement"),
    (r"MNT\s*[\d,]+\.\d\d", "R3 quotes a money figure in MNT"),
    (r"\b\d{1,5}\s*minor\s*units?\b", "R4 quotes a figure in minor units"),
    # --- the total-interest formula, T241's own correction ---
    (r"n\s*[·*]\s*E\s*\+\s*B|n\*E\s*\+\s*B|TOTAL\s+INTEREST|totalInterestAmount",
     "R5 states or uses the total-interest / n.E+B identity"),
    # --- the ceiling and the region, i.e. what a reader would carry to Buyan ---
    (r"ceiling|bounded by|upper bound|no upper bound", "R6 states a bound or a ceiling"),
    (r"B_minor|1\.5\s*·?\s*n|\(\s*δ\s*\+\s*(1/2|½)\s*\)", "R7 states the region in its own variables"),
    (r"δ\s*[≤<=≥>]|delta\s*[≤<=≥>]|δ\s*∈|δ\s*≥\s*2", "R8 makes a claim about δ"),
    # --- domain axes: rate, term, principal ---
    (r"\b\d{2,4}(\.\d)?\s*%", "R9 names an annual rate"),
    (r"\bn\s*=\s*\d+|\bn\s*[≤≥<>]\s*\d+", "R10 names a term"),
    # --- universals and cardinalities: the fifth mechanism's signature ---
    (r"\bno other\b|\bnever\b|\bevery\b|\balways\b|\bonly\b|\bnothing\b|\bnobody\b|\ball \d",
     "R11 universal / cardinality quantifier"),
    # --- dispositions: the class that produced all six of T129's failures ---
    (r"\bCLOSED\b|\bOPEN\b|\bSUPERSEDED\b|\bREFUTED\b|\bFALSIFIED\b|\bAPPROVED\b|\bRATIFIED\b|"
     r"\bmust not\b|\bMUST NOT\b|\bmust\b", "R12 a disposition or an imperative"),
    # --- named cells: a claim anchored to a measurement ---
    (r"\bT\d{2,3}[A-Za-z0-9]*-R\d+p\d+-N\d+-B\d+", "R13 names a measured cell"),
    (r"\[UNVERIFIED\]?|\[VERIFIED", "R14 carries a verification stamp"),
]

# P-72 calibration.  The positive and the negative are NOT substrings of one another.
CAL_POSITIVE = ("the largest unamortized residual is MNT 30.00 at n = 3000", "R1")
CAL_NEGATIVE = ("This paragraph introduces the reader to the shape of the document.", None)


def split_sentences(block):
    """Enumerate claim units.  Table rows, bullets, headings and block quotes are kept WHOLE --
    each is a single claim -- and running prose is split on sentence boundaries."""
    out = []
    for offset, line in enumerate(block):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|") or re.match(r"^([-*>#]|\d+\.)", stripped):
            out.append((offset, stripped))
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z*`\[\"(])", stripped):
            if s.strip():
                out.append((offset, s.strip()))
    return out


def nets_hit(text):
    return [why for pat, why in NETS if re.search(pat, text)]


def bounds(lines, start_marker):
    """End the section at the next GATE heading (`## G-<n>`), not at the next `## ` of any kind.

    Both naive rules are wrong on this file, and T241 measured both:
      * "next `## `"        -- G-8 contains TEN `## ` sub-headings of its own (THE THIRD OUTCOME,
                               FAMILY A, FAMILY B, Option (a), THE REGION, SITE 3, THE RESIDUAL
                               RECORD, The bound, The closed form, The three options), so this rule
                               covers 279 of G-8's 2088 lines -- 13 %.
      * "next `## G-8-NOTICE`" (T223's rule) -- swallows `## G-9` and `## G-10` entirely.
    """
    start = next(i for i, l in enumerate(lines) if l.startswith(start_marker))
    end = next((i for i, l in enumerate(lines)
                if i > start and re.match(r"^## G-\d", l)), len(lines))
    return start, end


def calibrate():
    pos_text, pos_expect = CAL_POSITIVE
    neg_text, _ = CAL_NEGATIVE
    assert pos_text not in neg_text and neg_text not in pos_text, \
        "P-72: calibration strings must not be substrings of one another"
    pos_hits = nets_hit(pos_text)
    neg_hits = nets_hit(neg_text)
    ok = bool(pos_hits) and not neg_hits
    print("P-72 CALIBRATION")
    print("  KNOWN POSITIVE : %r" % pos_text)
    print("    -> %d net(s): %s" % (len(pos_hits), pos_hits))
    print("  KNOWN NEGATIVE : %r" % neg_text)
    print("    -> %d net(s): %s" % (len(neg_hits), neg_hits))
    print("  DISCRIMINATES  : %s" % ("YES" if ok else "NO -- INSTRUMENT IS VOID"))
    return 0 if ok else 1


def main():
    if "--calibrate" in sys.argv:
        return calibrate()
    rc = calibrate()
    if rc:
        return rc
    print()
    with open(GATES) as fh:
        lines = fh.read().split("\n")
    report = {"gatesFile": ".softhouse/gates.md", "sections": {}}
    for name, marker in (("LIVE", LIVE_START), ("G-8-NOTICE", HIST_START)):
        start, end = bounds(lines, marker)
        block = lines[start:end]
        units = split_sentences(block)
        flagged = []
        for offset, text in units:
            hits = nets_hit(text)
            if hits:
                flagged.append({"absLine": start + offset + 1, "nets": hits, "text": text})
        report["sections"][name] = {
            "startLine": start + 1, "endLine": end, "lines": len(block),
            "claimUnits": len(units), "scopeBearing": len(flagged),
            "notScopeBearing": len(units) - len(flagged),
            "rows": flagged,
        }
        print("=== %s section  lines %d..%d  (%d lines)" % (name, start + 1, end, len(block)))
        print("    claim units enumerated : %d" % len(units))
        print("    SCOPE-BEARING (rows)   : %d" % len(flagged))
        print("    not scope-bearing      : %d   [P-67: both terms of the ratio]" % (len(units) - len(flagged)))
        by_net = {}
        for r in flagged:
            for w in r["nets"]:
                by_net[w] = by_net.get(w, 0) + 1
        for w in sorted(by_net, key=lambda k: (-by_net[k], k)):
            print("      %-4s %s" % (by_net[w], w))
        print()
    out = os.path.join(HERE, "scope-table-t241.json")
    with open(out, "w") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
