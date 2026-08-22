#!/usr/bin/env python3
"""
T241 — STANDING RULE item 1: rebuild the sentence-by-sentence scope table for the whole G-8 section.

SUCCESSOR TO `.softhouse/capture/t223-g8-region-predicate/src/scope_table_t223.py`, which is NOT
edited (T114/T176: committed evidence gets a successor, never a silent edit). The enumeration and
the section boundaries are T223's, unchanged, so the two runs are comparable. What T241 adds is the
CONCEPT set: T223's patterns were built around the concept T223 was killing ("family B lives at
600 %"), and a scope table is only as wide as its concept set. T219's edit moved the RESIDUAL RECORD
and added the seventh mechanism (a sentence WITH a scope whose scope is on the WRONG AXIS), so the
concepts that must now be flagged are:

  * every residual / record / bound figure, in any of its historical values;
  * every sentence that attaches a TERM (n = …) to a residual — the wrong-axis shape itself;
  * the rescue ceiling in all three of its historical forms (n/2, (δ+½)·n, 1.5·n);
  * the `δ ≤ 1` conjecture the conservative superset rests on;
  * the options (b)/(c) prohibition, because it is a `user`-gate boundary;
  * the TOTAL-INTEREST law `n·E + B`, which T241 is here to correct in the instrument;
  * the rate/term cardinality universals T223 killed (kept, so nothing T223 caught is lost);
  * the port-grading claims, whose domain is the set of cells anyone ran.

It also enumerates the `## G-8-NOTICE` superseded-history block SEPARATELY (T223's run stopped at
its heading), because T241 must decide whether that block needs a pointer, and a decision about a
block is not creditable without an enumeration of it.

No float anywhere (P-25). This script computes no money.

Run:  python3 scope_table_t241.py                          # the live gates.md -> ../out/scope-table-t241.json
      python3 scope_table_t241.py FILE OUTNAME             # any gates.md revision -> ../out/OUTNAME
The second form is how the PRE-EDIT run is reproduced: write `git show <rev>:.softhouse/gates.md`
to a file and pass it. Re-running on the EDITED file and diffing the flagged sets is also the
cheapest check that an edit did not silently DROP a scope-bearing claim (T223's practice, kept).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
GATES = os.path.join(REPO, ".softhouse", "gates.md")

# ---------------------------------------------------------------------------------------------
# The CONCEPT set. T223's eleven patterns are kept VERBATIM as C-01..C-11 so that anything T223's
# rebuild flagged is still flagged here; T241 adds C-12..C-22.
# ---------------------------------------------------------------------------------------------
CONCEPT_PATTERNS = [
    ("C-01", r"600\.0\s*%", "names the rate 600.0 %"),
    ("C-02", r"600\s*%", "names the rate 600 %"),
    ("C-03", r"\bone annual rate\b", "'one annual rate' — a cardinality claim about family B's rates"),
    ("C-04", r"no other rate", "'no other rate' — a universal over rates"),
    ("C-05", r"any other RATE|any other rate", "'any other rate' — an open-question framing"),
    ("C-06", r"narrower in \*\*rate\*\*|narrower in rate", "the narrower-in-rate comparison"),
    ("C-07", r"n\s*[>=≥]\s*104|n = 104|104 ≤ n", "states the region by a term threshold"),
    ("C-08", r"eleven|\b11 of the 12\b|twelve annual rates|12 rates", "the rate-count claims"),
    ("C-09", r"largest failing principal|largest unamortized residual|MNT 10\.01|MNT 5\.01|MNT 2\.91|MNT 0\.23",
     "a bound on the failing principal / residual (T223's form)"),
    ("C-10", r"family B is|Family B is|family-B region", "a definitional statement about family B"),
    ("C-11", r"n = 3000|n = 1000|n = 600|n = 250", "states a term as a domain edge"),
    # ---- T241 additions -------------------------------------------------------------------
    ("C-12", r"MNT\s*(30\.00|29\.99|44\.99|2\.99|5\.40|1\.80|0\.50|15,?010\.01|2,?505\.01)",
     "a residual / ceiling / interest figure in one of its other historical values"),
    ("C-13", r"largest|record|ceiling|\bbound\b|bounded|not a bound|upper bound",
     "a superlative or bound — the shape that acquires a wrong axis"),
    ("C-14", r"WITH ITS TERM|with its term|at n = \d|at n=\d",
     "attaches a TERM to a figure — the seventh mechanism's exact shape"),
    ("C-15", r"n\s*/\s*2|n/200|⌊n/2⌋|1\.5\s*·\s*n|1\.5\*n|\(δ\s*\+\s*½\)\s*·\s*n|δ \+ ½",
     "states the rescue ceiling"),
    ("C-16", r"δ\s*≤\s*1|delta <= 1|δ ≥ 2|delta >= 2|conjecture", "the δ conjecture the superset rests on"),
    ("C-17", r"option[s]? \(b\)|option[s]? \(c\)|\(b\) and \(c\)|\(b\)/\(c\)",
     "the options (b)/(c) user-gate prohibition"),
    ("C-18", r"n·E|n\*E|n\s*·\s*E\s*\+\s*B|TOTAL INTEREST|total interest",
     "the TOTAL-INTEREST law — the claim T241 corrects in the instrument"),
    ("C-19", r"the port|Go port|port agrees|port diverge|graded|ungraded",
     "a claim about the PORT, whose domain is the set of cells anyone ran"),
    ("C-20", r"every|Every|never|Never|always|Always|all \d|no cell|nothing above|nobody has",
     "an unscoped universal or negative-existence claim (P-66/P-70)"),
    ("C-21", r"\b(measured|observed|swept|asked)\b", "asserts a measurement — must carry its domain"),
    ("C-22", r"δ\s*=\s*\d|delta = \d|I₁q|E =|EMI", "states an instalment / δ value — an INPUT to the law"),
]

COMPILED = [(cid, re.compile(pat), why) for cid, pat, why in CONCEPT_PATTERNS]


def sentences(block, first_lineno):
    """T223's splitter, unchanged: table rows and bullets are single claims; prose splits at
    sentence boundaries."""
    out = []
    for offset, line in enumerate(block):
        lineno = first_lineno + offset
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|") or re.match(r"^[-*>#]", stripped):
            out.append((lineno, stripped))
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z*`\[])", stripped):
            if s.strip():
                out.append((lineno, s.strip()))
    return out


def enumerate_block(lines, start_idx, end_idx, name):
    block = lines[start_idx:end_idx]
    sents = sentences(block, start_idx + 1)          # absolute 1-based line numbers
    flagged = []
    for lineno, s in sents:
        hits = [(cid, why) for cid, rx, why in COMPILED if rx.search(s)]
        if hits:
            flagged.append({"block": name, "absLine": lineno,
                            "concepts": [c for c, _ in hits],
                            "why": [w for _, w in hits],
                            "text": s})
    return {"block": name, "startLine": start_idx + 1, "endLine": end_idx,
            "lines": len(block), "claims": len(sents), "scopeBearingClaims": len(flagged)}, flagged


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else GATES
    outname = sys.argv[2] if len(sys.argv) > 2 else "scope-table-t241.json"
    lines = open(path).read().split("\n")
    live_start = next(i for i, l in enumerate(lines) if l.startswith("## G-8 — TWO phenomena"))
    notice = next(i for i, l in enumerate(lines) if i > live_start and l.startswith("## G-8-NOTICE"))
    notice_end = next((i for i, l in enumerate(lines)
                       if i > notice and re.match(r"^#{1,2} ", l)), len(lines))

    s1, f1 = enumerate_block(lines, live_start, notice, "LIVE G-8")
    s2, f2 = enumerate_block(lines, notice, notice_end, "G-8-NOTICE (superseded history)")

    payload = {"summary": {"gatesFile": path, "blocks": [s1, s2],
                           "conceptPatterns": len(CONCEPT_PATTERNS),
                           "totalClaims": s1["claims"] + s2["claims"],
                           "totalScopeBearing": s1["scopeBearingClaims"] + s2["scopeBearingClaims"]},
               "rows": f1 + f2}
    outdir = os.path.join(HERE, "..", "out")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, outname), "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
    print(json.dumps(payload["summary"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
