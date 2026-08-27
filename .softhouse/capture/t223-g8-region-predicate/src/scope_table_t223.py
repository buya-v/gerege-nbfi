#!/usr/bin/env python3
"""
T223 — STANDING RULE item 1: rebuild the sentence-by-sentence scope table for the whole G-8 section
BEFORE editing it. Not a grep for the sentence being changed: every sentence in the section is
enumerated, and each is asked what it asserts and over what domain.

The mechanical part (enumeration, and the domain-token extraction that flags a sentence as
scope-bearing) is done here; the disposition of each flagged row is recorded by hand in
../SCOPE-TABLE-T223.md. Item 3 -- sweep for the CONCEPT, not the wording -- is implemented as the
CONCEPT_PATTERNS below, which is deliberately wider than "the sentence I am changing": it catches
every restatement of "family B lives at 600 %", "no other rate", "one annual rate", and every
statement of the region in rates or terms.

No float anywhere (P-25). This script computes no money.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
GATES = os.path.join(REPO, ".softhouse", "gates.md")

# The CONCEPT, in every wording it has ever taken in this file -- not the wording of one sentence.
CONCEPT_PATTERNS = [
    (r"600\.0\s*%", "names the rate 600.0 %"),
    (r"600\s*%", "names the rate 600 %"),
    (r"\bone annual rate\b", "'one annual rate' -- a cardinality claim about family B's rates"),
    (r"no other rate", "'no other rate' -- a universal over rates"),
    (r"any other RATE|any other rate", "'any other rate' -- an open-question framing"),
    (r"narrower in \*\*rate\*\*|narrower in rate", "the narrower-in-rate comparison"),
    (r"n\s*[>=≥]\s*104|n = 104|104 ≤ n", "states the region by a term threshold"),
    (r"eleven|\b11 of the 12\b|twelve annual rates|12 rates", "the rate-count claims"),
    (r"largest failing principal|largest unamortized residual|MNT 10\.01|MNT 5\.01|MNT 2\.91|MNT 0\.23",
     "a bound on the failing principal / residual"),
    (r"family B is|Family B is|family-B region", "a definitional statement about family B"),
    (r"n = 3000|n = 1000|n = 600|n = 250", "states a term as a domain edge"),
]


def sentences(block):
    out = []
    for lineno, line in enumerate(block, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        # keep table rows and bullets whole -- they are single claims
        if stripped.startswith("|") or re.match(r"^[-*>#]", stripped):
            out.append((lineno, stripped))
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z*`\[])", stripped):
            if s.strip():
                out.append((lineno, s.strip()))
    return out


def main():
    lines = open(GATES).read().split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## G-8 — TWO phenomena"))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith("## G-8-NOTICE"))
    block = lines[start:end]
    sents = sentences(block)
    flagged = []
    for lineno, s in sents:
        hits = [why for pat, why in CONCEPT_PATTERNS if re.search(pat, s)]
        if hits:
            flagged.append({"lineInSection": lineno, "absLine": start + lineno,
                            "why": hits, "text": s})
    summary = {"sectionStartLine": start + 1, "sectionEndLine": end,
               "sectionLines": len(block), "sentences": len(sents),
               "scopeBearingSentences": len(flagged)}
    outdir = os.path.join(HERE, "..", "out")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "scope-table-t223.json"), "w") as fh:
        json.dump({"summary": summary, "rows": flagged}, fh, indent=1, sort_keys=True)
    print(json.dumps(summary, sort_keys=True))
    for r in flagged:
        print("L%-5d %s" % (r["absLine"], r["text"][:190]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
