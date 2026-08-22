#!/usr/bin/env python3
"""T260 LEG B — normative-sentence set difference with a DELIBERATELY BROADER predicate than T255's.

T255's LEG 2 collected lines matching {must, shall, obliges, may not, is NORMATIVE,
normative requirement} and reported 87 -> 95 with 8 accounted losses. T255 itself flags as
[UNVERIFIED] that "an obligation expressed WITHOUT a modal verb would escape LEG 2 entirely".
This instrument goes after exactly that.

It works at SENTENCE granularity, not line granularity, because DEC-2 hard-wraps prose: a
line-level set difference reports a re-wrap as a lost obligation and reports a re-worded
obligation inside a re-wrapped line as nothing at all. Sentences are re-joined across the wrap
first, so a pure re-flow is invisible and a genuine rewording is visible.

The predicate has two tiers:
  MODAL     - T255's set (superset of it, in fact)
  NON-MODAL - the class T255 could not see:
              * deontic-by-negation:  never, always, no ... may, is prohibited, is forbidden,
                                      is not permitted, refuses, must-equivalent "is required to"
              * bare-present normative: "the port <verbs>", "a conformant/conforming
                implementation <verbs>", "the adapter <verbs>", "an implementation <verbs>"
              * imperative openers:   Use, Emit, Store, Compare, Derive, Reject, Refuse, Treat,
                                      Return, Encode, Never, Always, Do not
              * requirement nouns:    requirement, precondition, obligation, mandatory, binding

Exit: 0 always (census). The adjudication of the LOST set is the reviewer's, by hand.
"""
import re
import sys

MODAL = re.compile(
    r"\b(must|MUST|shall|SHALL|obliges|obliged|may not|MAY NOT|is NORMATIVE|"
    r"normative requirement|NORMATIVE)\b"
)

NONMODAL_PATTERNS = [
    (r"\bnever\b|\bNEVER\b", "never"),
    (r"\balways\b|\bALWAYS\b", "always"),
    (r"\bis required to\b|\bare required to\b|\bis required\b|\bare required\b", "is-required"),
    (r"\bis prohibited\b|\bare prohibited\b|\bis forbidden\b|\bis not permitted\b"
     r"|\bare not permitted\b", "prohibited"),
    (r"\bmandatory\b|\bMANDATORY\b", "mandatory"),
    (r"\brequirement\b|\brequirements\b|\bprecondition\b|\bpreconditions\b", "requirement-noun"),
    (r"\bobligation\b|\bobligations\b", "obligation-noun"),
    (r"\b(the port|a port|the adapter|the Go port|a conformant implementation|"
     r"a conforming implementation|an implementation|the implementation|a conforming port|"
     r"a conformant port)\b", "subject-of-duty"),
    (r"^\s*[-*>|\s]*(Use|Emit|Store|Compare|Derive|Reject|Refuse|Treat|Return|Encode|Do not|"
     r"Never|Always|Cite|Resolve|Read)\b", "imperative-opener"),
]


def load(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def unwrap(text):
    """Re-join hard-wrapped prose into sentences, preserving table rows and fenced blocks as
    single units (a table row IS a sentence for this purpose -- it states a rule per cell)."""
    lines = text.split("\n")
    out = []
    fence = False
    buf = []

    def flush():
        if buf:
            out.append(" ".join(x.strip() for x in buf).strip())
            buf.clear()

    for l in lines:
        stripped = l.lstrip("> ").rstrip()
        if stripped.startswith("```"):
            flush()
            fence = not fence
            out.append(l.strip())
            continue
        if fence:
            out.append(l.strip())
            continue
        if l.strip().startswith("|"):
            flush()
            out.append(l.strip())
            continue
        if not l.strip():
            flush()
            continue
        if re.match(r"^#{1,4} ", l):
            flush()
            out.append(l.strip())
            continue
        buf.append(l.lstrip("> ").rstrip())
    flush()

    # now split the joined paragraphs into sentences
    sents = []
    for chunk in out:
        if chunk.startswith("|") or chunk.startswith("```") or chunk.startswith("#"):
            sents.append(chunk)
            continue
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z*`\[“\"(**])", chunk)
        for p in parts:
            p = p.strip()
            if p:
                sents.append(p)
    return sents


def norm(s):
    """Normalise away the things a citation-only edit is ALLOWED to change, so that a sentence
    whose only delta is its citation does not read as a lost obligation."""
    s = re.sub(r"\[(ANCHOR|VERIFIED|MEASURED|RE-MEASURED|RE-VERIFIED|TRANSCRIBED)[^\]]*\]", "[CIT]", s)
    s = re.sub(r"`[^`]*\.(sh|go|py|json|java|md)(:\d+(-\d+)?)?`", "`FILE`", s)
    s = re.sub(r":\d+(-\d+)?", ":N", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def classify(s):
    tags = []
    if MODAL.search(s):
        tags.append("MODAL")
    for pat, name in NONMODAL_PATTERNS:
        if re.search(pat, s):
            tags.append(name)
    return tags


def main():
    a = unwrap(load(sys.argv[1]))
    b = unwrap(load(sys.argv[2]))

    def sel(sents):
        d = {}
        for s in sents:
            t = classify(s)
            if t:
                d.setdefault(norm(s), (s, t))
        return d

    A = sel(a)
    B = sel(b)

    lost = [k for k in A if k not in B]
    gained = [k for k in B if k not in A]

    # split by tier
    def tier(k, D):
        return "MODAL" if "MODAL" in D[k][1] else "NONMODAL"

    lm = [k for k in lost if tier(k, A) == "MODAL"]
    ln = [k for k in lost if tier(k, A) == "NONMODAL"]
    gm = [k for k in gained if tier(k, B) == "MODAL"]
    gn = [k for k in gained if tier(k, B) == "NONMODAL"]

    print("T260 LEG B — BROAD normative set difference (sentence granularity, citation-normalised)")
    print("=" * 100)
    print(f"rev7 normative sentences : {len(A)}  (MODAL {sum(1 for k in A if tier(k,A)=='MODAL')}, "
          f"NON-MODAL {sum(1 for k in A if tier(k,A)=='NONMODAL')})")
    print(f"rev8 normative sentences : {len(B)}  (MODAL {sum(1 for k in B if tier(k,B)=='MODAL')}, "
          f"NON-MODAL {sum(1 for k in B if tier(k,B)=='NONMODAL')})")
    print(f"LOST   : {len(lost)}  (MODAL {len(lm)}, NON-MODAL {len(ln)})")
    print(f"GAINED : {len(gained)}  (MODAL {len(gm)}, NON-MODAL {len(gn)})")
    print()
    print("### LOST — MODAL  (T255's LEG 2 would also see these)")
    for i, k in enumerate(lm, 1):
        print(f"[L-M{i:02d}] tags={A[k][1]}")
        print("        " + A[k][0][:400])
    print()
    print("### LOST — NON-MODAL  (T255's LEG 2 is BLIND to these; this is the class it flagged)")
    for i, k in enumerate(ln, 1):
        print(f"[L-N{i:02d}] tags={A[k][1]}")
        print("        " + A[k][0][:400])
    print()
    print("### GAINED — MODAL")
    for i, k in enumerate(gm, 1):
        print(f"[G-M{i:02d}] " + B[k][0][:300])
    print()
    print("### GAINED — NON-MODAL")
    for i, k in enumerate(gn, 1):
        print(f"[G-N{i:02d}] " + B[k][0][:300])


if __name__ == "__main__":
    main()
