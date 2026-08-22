#!/usr/bin/env python3
"""T255 — PROVE that revision 8 moved no obligation. Mechanically, so `T260` can
re-derive it rather than read my assurance.

G-14's recorded scope is NOTHING BUT DEC-2 ITSELF, and within that: evidence,
citations and false statements of fact may be corrected; **nothing a conformant
implementation must DO may move.** This instrument tests that three ways.

  LEG 1  BLOCK IDENTITY. The blocks that carry obligations -- §4.2's predicates,
         §5.2's requirements 1-7, §5.3's ten-row precondition table, §4.6's
         admissibility rules, §4.10's registry rules -- are extracted from the
         PRE-revision-8 blob and from the working tree and compared BYTE FOR
         BYTE. Not "looks the same": identical sha256.

  LEG 2  MODAL-SENTENCE SET DIFFERENCE. Every line in the document carrying
         normative modal language is collected from both sides and the sets are
         differenced. A modal line PRESENT BEFORE and ABSENT AFTER is a
         candidate obligation removal and must be explained one by one. This is
         the arm that catches an obligation deleted somewhere nobody thought to
         name a block for.

  LEG 3  THE TWO H-10 OBLIGATIONS, VERBATIM. The rule paragraph welds two
         obligations to one FACT. The fact was false and moves; the obligations
         must appear character-for-character on both sides.

Baseline is `git show HEAD:docs/adr/...` -- the blob revision 8 was applied to.
No `cd`, no `|| true`, no bare `grep`. Exit 0 = no obligation moved;
1 = at least one did, or one could not be accounted for; 2 = could not run.
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
ADR_REL = "docs/adr/DEC-2-gl-accounting-adapter.md"

# (label, start-substring, end-substring). Both must occur exactly once on each
# side; the block is everything between them, inclusive.
BLOCKS = [
    ("§4.2 the graded domain, predicate by predicate",
     "### 4.2 The graded domain, predicate by predicate",
     "**A predicate that is inert by scope is not a vacuous predicate (P-35).**"),
    ("§4.6 G-10 and the admissibility constraint (A-1..A-4)",
     "### 4.6 G-10 as a stated hazard, and the constraint it puts on admissibility",
     "### 4.7 The creation-set / posting-set divergence"),
    ("§4.10 the capability registry and default-deny discipline",
     "### 4.10 The capability registry for this context, and the default-deny discipline",
     "next reader does not mistake the omission for an oversight."),
    ("§5.2 requirements 1-7 (NORMATIVE — the standard A2-15 is judged against)",
     "**First — the extension is a SECOND vector schema and a SECOND comparator, not a widening of the",
     "**Third — Disposition 3 survives, on a different argument.**"),
    ("§5.3 the TEN-ROW precondition table",
     "| order | # | precondition | why, in one line | depends on |",
     "independent of all the above — that independence is what licensed it to be built first**"),
    ("§5.5 the graded_against requirement",
     "### 5.5 The `graded_against` requirement, restated with its true cost",
     "## 6. Forward-compatibility analysis"),
]

# Rows of §4.4's invariant table that revision 8 edits. For each, the cell index
# revision 8 is ALLOWED to change; EVERY OTHER CELL must be byte-identical --
# in particular column 4, which is where the obligations live.
TABLE_ROWS = [
    ("I-1", "| **I-1** | Debits equal credits |", 5),
    ("I-2", "| **I-2** | Splits sum to whole |", 5),
    ("I-3", "| **I-3** | Balances are DERIVED, never written |", 5),
    ("I-4", "| **I-4** | The ledger is append-only |", None),
    ("I-5", "| **I-5** | Corrections are reversing entries |", None),
    ("I-6", "| **I-6** | Holds are postings and alter `available` only", None),
    ("I-7", "| **I-7** | `Idempotency-Key` on every money-movement POST |", 5),
]

MODAL = re.compile(
    r"\b(?:must|MUST|shall|SHALL|obliges|OBLIGES|obliged|is required to|are required to|"
    r"may not|MAY NOT|must not|MUST NOT|is NORMATIVE|are NORMATIVE|normative requirement)\b"
)

H10_OBLIGATIONS = [
    "DEC-2 **obliges** I-1 through I-5 on any implementation of the\nGL/accounting context",
    "**I-3 and I-4 must be enforced by a\nharness-level source guard, not by a vector**",
]

# Modal lines that revision 8 legitimately REWROTE (their obligation is carried
# forward in the new text, verbatim or strictly strengthened). Each is listed
# with the hunk that owns it, so `T260` can check them one at a time instead of
# taking a bulk assurance.
ACCOUNTED = {
    "### 8.3 If ratified, these remain true and must not be misread":
        "H-15b — heading only: 'If ratified,' dropped because it IS ratified. "
        "'these remain true and must not be misread' is carried forward verbatim.",
    "> exists. Ratification is not coverage, and this document must never be cited as though it were.":
        "H-2 — the caution is CARRIED AND STRENGTHENED: the new text reads 'Ratification is not "
        "coverage, and neither is a green ledger section' and 'this document must never be cited as "
        "evidence that the GL/accounting context is correct'. Nothing an implementation must DO.",
    "GL/accounting context, and **grades none of them today.** **I-3 and I-4 must be enforced by a":
        "H-10 — LINE-WRAP ONLY for the obligation half. LEG 3 proves both obligations appear "
        "verbatim on both sides. The clause DELETED is the FACT 'and grades none of them today', "
        "which was false.",
    "and §5.3 names work that must land before `A2-15` could succeed even against a ratified contract.":
        "H-3 — a FACT about §5.3's status, false at a71c140 (A2-15 is done and has promoted six "
        "vectors). §5.3's ten-row table is proved byte-identical in LEG 1.",
    "must never be confused, and a citation of this document as evidence of ledger coverage is a":
        "H-14d — carried forward and widened: 'a citation of this document, OR OF A GREEN LEDGER "
        "SECTION, as evidence of ledger coverage is a misreading of both.'",
    "> *must* do. **Not one of them is currently checked by anything.** Four separate facts, each":
        "H-1a — LINE SPLIT. The framing clause 'what a conforming port *must* do' is carried "
        "forward verbatim on its own line (see GAINED). What was removed is the FACT 'Not one of "
        "them is currently checked by anything', which is false and is restated in the retraction.",
    "| **I-3** | Balances are DERIVED, never written | No write path to any balance column exists "
    "in the Go tree | **NO — STRUCTURAL ONLY.** A vector is a snapshot of oracle output; it cannot "
    "observe the *absence* of a write path. Gradeable only by a source-level guard over the Go "
    "tree. And the oracle is **not** a positive example: `m_trial_balance.closing_balance` is a "
    "written, stored, **unsigned** sum wearing a balance's name [VERIFIED BY A2-2's re-derivation "
    "of `UpdateTrialBalanceDetailsTasklet.java:81` reading `JournalEntryRepository.java:61`, NOT "
    "RE-OPENED HERE]. It is deliberately **not ported** (§7). | **NO BY A VECTOR — AND, SINCE "
    "REVISION 2, YES BY A SOURCE GUARD, PARTIALLY.**":
        "C-2 — see LEG 1b: cell 5 only.",
}

# The two §4.4 table rows below are single lines several thousand characters
# long, so listing them verbatim above is impractical. They are accounted by
# PREFIX instead, and LEG 1b has already proved cell-by-cell that only column 5
# moved on each -- which is a strictly stronger statement than this arm makes.
ACCOUNTED_PREFIX = {
    "| **I-3** | Balances are DERIVED, never written |":
        "C-2 — LEG 1b proves cell 5 is the only cell that changed; column 4 sha is identical.",
    "| **I-7** | `Idempotency-Key` on every money-movement POST |":
        "H-9 — LEG 1b proves cell 5 is the only cell that changed; column 4 sha is identical.",
}


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def head_blob():
    p = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + ADR_REL], capture_output=True, text=True)
    if p.returncode != 0:
        raise IOError("git show HEAD:%s failed: %s" % (ADR_REL, p.stderr.strip()))
    return p.stdout


def extract(text, start, end, label, side):
    i = text.find(start)
    j = text.find(end)
    if i < 0 or j < 0 or j < i:
        raise ValueError("%s: could not delimit block on the %s side (start@%d end@%d)" % (label, side, i, j))
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("%s: delimiters are not unique on the %s side" % (label, side))
    return text[i:j]


def modal_lines(text):
    out = {}
    for l in text.split("\n"):
        s = l.strip()
        if s and MODAL.search(s):
            out.setdefault(s, 0)
            out[s] += 1
    return out


def main():
    try:
        before = head_blob()
    except IOError as exc:
        print("REFUSE (exit 2): %s" % exc)
        return 2
    path = os.path.join(ROOT, ADR_REL)
    if not os.path.isfile(path):
        print("REFUSE (exit 2): %s missing" % path)
        return 2
    with open(path, encoding="utf-8") as fh:
        after = fh.read()

    if before == after:
        print("REFUSE (exit 2): the working tree DEC-2 is byte-identical to HEAD's.")
        print("                 There is nothing to prove; revision 8 was not applied.")
        return 2

    print("BEFORE (HEAD blob) sha256 %s  %d lines" % (sha(before), before.count("\n") + 1))
    print("AFTER  (worktree)  sha256 %s  %d lines" % (sha(after), after.count("\n") + 1))
    print("")

    bad = 0

    # ------------------------------------------------------------------ LEG 1
    print("=== LEG 1 — BLOCK IDENTITY (byte-for-byte, not 'looks the same') ===")
    for label, start, end in BLOCKS:
        try:
            b = extract(before, start, end, label, "BEFORE")
            a = extract(after, start, end, label, "AFTER")
        except ValueError as exc:
            bad += 1
            print("  ERROR   %s" % exc)
            continue
        if sha(a) == sha(b):
            print("  IDENTICAL  %-58s sha256 %s  (%d chars)" % (label, sha(a)[:16], len(a)))
        else:
            bad += 1
            print("  *** CHANGED *** %s" % label)
            print("      before sha256 %s (%d chars)" % (sha(b)[:16], len(b)))
            print("      after  sha256 %s (%d chars)" % (sha(a)[:16], len(a)))
    print("")

    # ----------------------------------------------------------------- LEG 1b
    print("=== LEG 1b — §4.4 INVARIANT TABLE, CELL BY CELL ===")
    print("Revision 8 edits column 5 ('Graded today?') of three rows and the supporting")
    print("citation inside I-3's column 5. EVERY OTHER CELL OF EVERY ROW, and in particular")
    print("column 4 where the obligations live, must be byte-identical.")

    def row(text, key, side):
        hits = [l for l in text.split("\n") if l.startswith(key)]
        if len(hits) != 1:
            raise ValueError("%s: %d matching rows on the %s side" % (key[:24], len(hits), side))
        return hits[0].split("|")

    for label, key, allowed in TABLE_ROWS:
        try:
            rb, ra = row(before, key, "BEFORE"), row(after, key, "AFTER")
        except ValueError as exc:
            bad += 1
            print("  ERROR   %s" % exc)
            continue
        if len(rb) != len(ra):
            bad += 1
            print("  *** %s: cell COUNT changed, %d -> %d ***" % (label, len(rb), len(ra)))
            continue
        diffs = [i for i in range(len(rb)) if rb[i] != ra[i]]
        expected = [allowed] if allowed is not None else []
        if diffs == expected:
            print("  ok      %-4s %d cells, changed: %s  (obligation column 4 IDENTICAL, sha %s)"
                  % (label, len(rb), diffs if diffs else "NONE", sha(ra[4])[:12]))
        else:
            bad += 1
            print("  *** %s: cells changed %s, expected %s ***" % (label, diffs, expected))
            for i in diffs:
                if i not in expected:
                    print("      cell %d BEFORE: %s" % (i, rb[i].strip()[:110]))
                    print("      cell %d AFTER : %s" % (i, ra[i].strip()[:110]))
    print("")

    # ------------------------------------------------------------------ LEG 2
    print("=== LEG 2 — MODAL-SENTENCE SET DIFFERENCE ===")
    mb, ma = modal_lines(before), modal_lines(after)
    print("  modal lines BEFORE: %d distinct   AFTER: %d distinct   (both terms, P-67)" % (len(mb), len(ma)))
    lost = sorted(set(mb) - set(ma))
    gained = sorted(set(ma) - set(mb))
    print("  LOST (present before, absent after): %d" % len(lost))
    for l in lost:
        tag = ACCOUNTED.get(l)
        if tag is None:
            for pref, why in ACCOUNTED_PREFIX.items():
                if l.startswith(pref):
                    tag = why
                    break
        print("    %s %s" % ("[accounted: %s]" % tag if tag else "[UNACCOUNTED]", l[:150]))
        if tag is None:
            bad += 1
    print("  GAINED (new modal lines): %d — these are ADDITIONS; an addition cannot" % len(gained))
    print("  relax an obligation, but each is listed so a reviewer can check none INVENTS one:")
    for l in gained:
        print("    + %s" % l[:150])
    print("")

    # ------------------------------------------------------------------ LEG 3
    print("=== LEG 3 — the two obligations welded into §4.4's rule paragraph, VERBATIM ===")
    for ob in H10_OBLIGATIONS:
        nb, na = before.count(ob), after.count(ob)
        state = "ok" if (nb >= 1 and na >= 1) else "*** MOVED ***"
        if nb < 1 or na < 1:
            bad += 1
        print("  %-14s before %d / after %d :: %s" % (state, nb, na, ob.replace("\n", " ")[:96]))
    print("")

    print("%s: %d finding(s)" % ("*** AN OBLIGATION MOVED ***" if bad else "NO OBLIGATION MOVED", bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
