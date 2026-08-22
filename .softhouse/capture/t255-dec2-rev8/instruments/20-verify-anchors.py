#!/usr/bin/env python3
"""T255 / DEC-2 revision 8 — THE ROT MECHANISM FIX, and its checker.

WHAT IS BROKEN
--------------
Three consecutive passes of DEC-2 shipped stale `.softhouse/conformance.sh`
line citations. Revision 7's OWN re-measured citations went stale before it
could land, because an unrelated merge inserted lines ABOVE them. A line
number is a perishable identifier: it is invalidated by every edit above it,
including edits that change nothing it refers to. Worse, a dead line number
does not resolve to nothing -- it resolves to a plausible-looking neighbouring
line, so a reader following it is MISLED rather than STOPPED.

WHAT REVISION 8 DOES INSTEAD
----------------------------
It ELIMINATES the perishable identifier at every site it touches:

  ANCHOR    a citation is bound to an EXACT, UNIQUE SUBSTRING of the cited
            file, written inline as

                [ANCHOR <path> :: `<exact substring>`]

            It cannot rot from an insertion above it, because it contains no
            position. It rots only when the cited THING changes -- which is
            when a citation SHOULD rot.

  DERIVED   a fact that is a property of the source (how many guards
            `run_guards` invokes, in what order, which one is tallied Nth) is
            not restated in prose at all. It is written ONCE, in a fenced
            block carrying the sentinel

                DERIVED-FROM-SOURCE: run_guards()

            and this instrument RE-DERIVES it from the source and compares.
            Every other site in the document points AT that block by section
            number instead of restating the number (P-79: never fix a rotted
            number; make the second site READ the first).

WHY NOT "WIRE verify-line-numbers.py INTO THE HARNESS"
-----------------------------------------------------
Because a wired LINE-NUMBER checker fires on every unrelated edit above every
citation. T253 rewrote ten `mktemp -t` sites in `conformance.sh` in this same
fire, the first four of them above every guard citation DEC-2 carries. A wired
line-number gate would have turned every graded run in the program RED for a
reason that has nothing to do with what the citations say. A gate with that
false-positive rate is a gate that gets pinned into an amnesty list within two
fires -- which is the shape `FAILOPEN_PIN_FILE_LIST` already documents in this
very harness. An ANCHOR check has a near-zero false-positive rate, which is the
property that makes wiring survivable at all.

And the deeper reason: an anchored document is CORRECT WITH NOTHING RUNNING.
A checker is a control, and a control that must be remembered is P-45 -- which
this program has hit five times, `manifest.py verify` silently RED across two
merges being the canonical one. Elimination needs no runner. The checker below
is a second line, not the line.

POPULATION IS DERIVED, NOT REMEMBERED
-------------------------------------
`verify-line-numbers.py` checks a hand-written list. MEASURED at this commit:
its `SH_ROWS` holds 4 rows while DEC-2 carries 115 `path:NNNN` citations, 90 of
them into files in this repo. It answers a question about its author's memory.
This instrument reads its whole population OUT OF THE DOCUMENT, so a citation
nobody remembered cannot be silently unchecked (P-66/P-70).

NO NETWORK. NO `cd`. NO `|| true`, NO `|| echo`, NO bare `grep`, NO `rg`.
Exit status:
    0  every anchor unique and present, every derived fact re-derived and equal
    1  a REAL measured negative: rot, ambiguity, or a derived mismatch
    2  the instrument could not do its job -- calibration failed, file missing,
       document shape not recognised. NEVER printed as an absence.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
ADR_REL = "docs/adr/DEC-2-gl-accounting-adapter.md"
SH_REL = ".softhouse/conformance.sh"

ANCHOR_RE = re.compile(r"\[ANCHOR\s+(\S+?)\s+::\s+`([^`]+)`\]")
# The sentinel is the FULL fence header, not the short form: the short form also
# occurs in the prose that DESCRIBES the mechanism (twice), and a sentinel that
# matches its own documentation selects the wrong block. P-76: check the
# SELECTOR before you trust the CONDITIONS.
FENCE_SENTINEL = "DERIVED-FROM-SOURCE: run_guards() in .softhouse/conformance.sh"
DERIVED_RE = re.compile(
    r"\[DERIVED:\s+run_guards invokes (\d+) \| tallies (\d+) \| "
    r"`([a-z_]+)` is invocation #(\d+) and tallied #(\d+)\]"
)

# A sentinel that MUST NOT be found. If the search machinery below is broken --
# wrong file, empty read, exception swallowed -- this row will "pass" and every
# other verdict is void. P-22/P-35.
NEG_ANCHOR = ("docs/adr/DEC-2-gl-accounting-adapter.md", "ZZQQ-T255-THIS-MUST-NOT-MATCH")


def read(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        raise IOError("not a file: %s" % path)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def occurrences(haystack, needle):
    """Count non-overlapping exact-substring occurrences. No regex, so there is
    no `\\b`-reads-as-literal-b fabrication class to worry about (P-75)."""
    return haystack.count(needle)


def derive_run_guards(sh_text):
    """Re-derive the guard census from `run_guards()`' own body.

    Returns (invoked_names_in_order, short_circuiting, tallied_names).
    Raises on any shape it does not recognise -- it never guesses.
    """
    lines = sh_text.split("\n")
    starts = [i for i, l in enumerate(lines) if l.rstrip() == "run_guards() {"]
    if len(starts) != 1:
        raise ValueError("expected exactly 1 `run_guards() {` definition, found %d" % len(starts))
    i = starts[0]
    body = []
    depth = 0
    for l in lines[i:]:
        body.append(l)
        depth += l.count("{") - l.count("}")
        if depth == 0 and len(body) > 1:
            break
    else:
        raise ValueError("`run_guards()` body never closed")

    tallied_re = re.compile(r"^\s*(guard_[a-z0-9_]+)\s*\|\|\s*failed=1\s*$")
    short_re = re.compile(r"^\s*(guard_[a-z0-9_]+)\s*\|\|\s*\{\s*$")
    invoked, tallied, short = [], [], []
    for l in body:
        m = tallied_re.match(l)
        if m:
            invoked.append(m.group(1))
            tallied.append(m.group(1))
            continue
        m = short_re.match(l)
        if m:
            invoked.append(m.group(1))
            short.append(m.group(1))
    if not invoked:
        raise ValueError("no guard invocation recognised inside `run_guards()` -- shape changed")
    return invoked, short, tallied


def parse_fence(adr_text):
    """Pull the guard names out of DEC-2's DERIVED-FROM-SOURCE fenced block."""
    lines = adr_text.split("\n")
    hits = [i for i, l in enumerate(lines) if FENCE_SENTINEL in l]
    if len(hits) != 1:
        raise ValueError("expected exactly 1 `%s` sentinel in DEC-2, found %d" % (FENCE_SENTINEL, len(hits)))
    i = hits[0]
    # walk back to the opening fence, forward to the closing one
    open_i = None
    for j in range(i, -1, -1):
        if lines[j].strip().startswith("```"):
            open_i = j
            break
    if open_i is None:
        raise ValueError("sentinel is not inside a fenced block")
    names = []
    for l in lines[open_i + 1:]:
        if l.strip().startswith("```"):
            break
        m = re.match(r"^\s*(guard_[a-z0-9_]+)\b", l)
        if m:
            names.append(m.group(1))
    if not names:
        raise ValueError("DERIVED-FROM-SOURCE fence lists no guard names")
    return names


def main():
    print("T255 anchor + derived-fact verifier")
    print("ROOT: %s" % ROOT)
    try:
        adr = read(ADR_REL)
        sh = read(SH_REL)
    except IOError as exc:
        print("REFUSE (exit 2): %s" % exc)
        return 2

    # ---------------------------------------------------------------- NEGATIVE
    neg_hay = read(NEG_ANCHOR[0])
    if occurrences(neg_hay, NEG_ANCHOR[1]) != 0:
        print("CALIBRATION FAIL (exit 2): the negative control MATCHED. Results are void.")
        return 2
    # ...and a POSITIVE control, because a search that finds nothing anywhere
    # would also "pass" the negative arm (P-35).
    if occurrences(neg_hay, "DEC-2") < 1:
        print("CALIBRATION FAIL (exit 2): the positive control found nothing. Results are void.")
        return 2
    print("calibration: negative control 0 hits, positive control >=1 hit. OK.")
    print("")

    bad = 0

    # ------------------------------------------------------------- ANCHOR ROWS
    anchors = ANCHOR_RE.findall(adr)
    print("=== ANCHORS (population DERIVED from %s, not from a hand-written list) ===" % ADR_REL)
    print("anchors found in the document: %d" % len(anchors))
    if not anchors:
        print("CALIBRATION FAIL (exit 2): zero [ANCHOR ...] citations in a document that must carry them.")
        return 2
    cache = {}
    for rel, needle in anchors:
        if rel not in cache:
            try:
                cache[rel] = read(rel)
            except IOError as exc:
                print("  ERROR   %s :: cited file unreadable (%s)" % (rel, exc))
                return 2
        n = occurrences(cache[rel], needle)
        if n == 1:
            print("  ok      %s :: %s" % (rel, needle[:78]))
        elif n == 0:
            bad += 1
            print("  ROT     %s :: NOT PRESENT -- %r" % (rel, needle[:78]))
        else:
            bad += 1
            print("  AMBIG   %s :: %d occurrences (an anchor must be unique) -- %r" % (rel, n, needle[:78]))
    print("")

    # ------------------------------------------------------------ DERIVED FACT
    print("=== DERIVED: run_guards() re-derived from %s ===" % SH_REL)
    try:
        invoked, short, tallied = derive_run_guards(sh)
    except ValueError as exc:
        print("REFUSE (exit 2): could not re-derive run_guards(): %s" % exc)
        return 2
    print("  invoked  (%d): %s" % (len(invoked), ", ".join(invoked)))
    print("  short-circuits (%d): %s" % (len(short), ", ".join(short)))
    print("  tallied  (%d): %s" % (len(tallied), ", ".join(tallied)))

    try:
        fence = parse_fence(adr)
    except ValueError as exc:
        print("REFUSE (exit 2): could not read DEC-2's DERIVED-FROM-SOURCE fence: %s" % exc)
        return 2
    print("  DEC-2 fence  (%d): %s" % (len(fence), ", ".join(fence)))
    if fence != invoked:
        bad += 1
        print("  MISMATCH the fence is not the source's invocation list, in order.")
        print("           source: %s" % invoked)
        print("           DEC-2 : %s" % fence)
    else:
        print("  ok      the fence equals the source's invocation list, in order.")

    dm = DERIVED_RE.search(adr)
    if dm is None:
        print("REFUSE (exit 2): DEC-2 carries no [DERIVED: run_guards invokes ...] token.")
        return 2
    if len(DERIVED_RE.findall(adr)) != 1:
        bad += 1
        print("  MISMATCH more than one [DERIVED: run_guards ...] token -- P-79 requires exactly one.")
    d_inv, d_tal = int(dm.group(1)), int(dm.group(2))
    d_name, d_iord, d_ord = dm.group(3), int(dm.group(4)), int(dm.group(5))
    print("  DEC-2 token: invokes %d | tallies %d | `%s` invocation #%d, tallied #%d"
          % (d_inv, d_tal, d_name, d_iord, d_ord))
    if d_inv != len(invoked):
        bad += 1
        print("  MISMATCH invoked count: DEC-2 says %d, source has %d" % (d_inv, len(invoked)))
    if d_tal != len(tallied):
        bad += 1
        print("  MISMATCH tallied count: DEC-2 says %d, source has %d" % (d_tal, len(tallied)))
    if d_name not in invoked:
        bad += 1
        print("  MISMATCH `%s` is not invoked in the source at all" % d_name)
    else:
        if invoked.index(d_name) + 1 != d_iord:
            bad += 1
            print("  MISMATCH `%s` INVOCATION ordinal: DEC-2 says #%d, source has #%d"
                  % (d_name, d_iord, invoked.index(d_name) + 1))
        if d_name not in tallied:
            bad += 1
            print("  MISMATCH `%s` is invoked but not tallied in the source" % d_name)
        elif tallied.index(d_name) + 1 != d_ord:
            bad += 1
            print("  MISMATCH `%s` TALLIED ordinal: DEC-2 says #%d, source has #%d"
                  % (d_name, d_ord, tallied.index(d_name) + 1))
    if bad == 0:
        print("  ok      every derived fact re-derived from source and equal.")
    print("")

    # ------------------------------------------- residual line-number citations
    resid = [(i, l) for i, l in enumerate(adr.split("\n"), 1)
             if re.search(r"conformance\.sh:\d", l)]
    print("=== RESIDUAL `conformance.sh:NNNN` line citations still in DEC-2: %d line(s) ===" % len(resid))
    print("EVERY ONE IS PRINTED, so a reviewer classifies them rather than trusting a count.")
    print("Revision 8 converted every LIVE one; what remains must all be HISTORY — a quotation")
    print("of what a past revision wrote, which may not be reworded without falsifying the record.")
    for i, l in resid:
        print("    L%-5d %s" % (i, l.strip()[:150]))
    print("")

    print("%s: %d failing row(s)" % ("ROT DETECTED" if bad else "ALL ANCHORS AND DERIVED FACTS HOLD", bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
