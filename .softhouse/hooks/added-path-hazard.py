#!/usr/bin/env python3
"""added-path-hazard -- T453.  Does ADDING these paths move the dead-path frontier?

    added-path-hazard.py --commit <commit-ish> --paths-from <file> [--repo <root>]
    added-path-hazard.py --selftest

WHY THIS EXISTS, AND WHY IT IS A MEASUREMENT RATHER THAN A LIST
===============================================================================================
The driver push gate admits a cheap re-grade when the delta from an attested ancestor stays
inside an enumerated STATE set.  T412 built that set by asking, guard by guard, WHICH FILES DOES
IT READ.  That question has a right answer for a guard whose corpus is file CONTENT and no answer
at all for a guard whose corpus is the tree's INVENTORY.

`guard_dead_path_frontier` is the second kind.  It resolves every quoted `.softhouse/` literal in
every tracked `.softhouse/` instrument against `git ls-files` -- the TRACKED UNIVERSE, never the
disk -- and refuses if the frontier moves at all, in either direction, from the pinned set.  So
ADDING a tracked file can make a pinned-DEAD literal live, SHRINK the frontier, and take the
whole bar to EXIT 2 with no probe line.  Nothing about the added file is read.  Its mere
existence in the index is the whole mechanism.

MEASURED, on this repository: `.softhouse/uat.md` is UNTRACKED, is one of the 108 pinned dead
literals, and is ordinary driver work.  Adding it is a `*.md` under `.softhouse/`, which is
squarely inside T412's STATE set, and the gate allowed it while the bar refused it.

THE ALTERNATIVE THAT WAS REJECTED, AND THE NUMBER THAT DECIDED IT
===============================================================================================
The blunt remedy is "the cheap path admits MODIFICATIONS only", which is structurally sound and
needs no program at all.  Measured over the last 400 non-merge first-parent commits on `main`, it
takes cheap-path coverage from 88% to 71% -- and the single most common addition it would block
is `.softhouse/LOCK`, which the driver ADDS 34 times in those 400 commits at the START of a fire,
the most latency-sensitive push there is.  Trading a fail-open for a freeze is not a fix (P-98).

This program asks the narrower question instead, and it asks it OF THE PIN rather than of a
table: is any added path capable of making a PINNED DEAD LITERAL resolve?  Measured over the same
400 commits: 78 ADDED entries, 0 blocked.  Cheap-path coverage 84%.  The test is surgical, and it
cannot rot the way a hand-maintained table rots, because the pin it reads is the guard's own pin,
read out of THE PUSHED TREE.

THE PREDICATE IS A DELIBERATE SUPERSET, AND THE DIRECTION IS STATED
===============================================================================================
A literal L resolves iff it is a tracked file OR a directory prefix of one
[census_dead_paths.py, `tracked_universe`].  The census also consults two normalised spellings
before calling a literal dead -- trailing sentence punctuation stripped, and a trailing `:NN` /
`:NN-MM` line citation stripped -- and it collapses `.`/`..` lexically.  Rather than reimplement
that resolver, which is a second copy that would rot, this asks a WIDER question:

    added path P is a HAZARD if any pin literal L (in any of its normalised spellings) satisfies
        L == P              P is exactly the dead literal
        P starts with L/    P is inside a dead directory literal, which now gains a prefix
        L starts with P/    P is a directory prefix of the dead literal
        L starts with P     P plus a punctuation or citation suffix is the dead literal

The last two clauses are broader than the census.  That is the fail-CLOSED direction: this
program can only ever REFUSE a cheap re-grade that would have been safe, sending it to the full
bar, which is the correct answer to any doubt.  It can never admit one that is not.

EXIT CODES -- three different facts, three different codes (T238's rule)
===============================================================================================
    0   the pin was READ and NO added path is a hazard   -- a MEASUREMENT, not a default
    1   at least one added path IS a hazard              -- printed, one per line
    2   the pin could not be read, the pin is EMPTY, no paths were given, or the arguments are
        unusable.  NEVER conflated with 0: an empty pin would make every addition look safe, and
        that is precisely the negative this program must not be able to emit unmeasured.

ENGINE (P-33/P-53): /usr/bin/python3 and `git show`.  Declared, not assumed.  No regex search
over a corpus happens here, so P-53's backslash-class trap cannot apply.
"""

import argparse
import os
import re
import subprocess
import sys

PROBE = "ADDED-PATH-HAZARD:"

# The pin is the dead-path guard's OWN pin, read out of the pushed tree. Named once, here.
PIN_PATH = ".softhouse/guards/dead-path-frontier.pin"

# The census's two normalisations, kept in the same spellings it uses so a reader can compare
# them side by side: census_dead_paths.py, TRAILING_PUNCT and CITATION_RE.
TRAILING_PUNCT = ")}],;:.…"
CITATION_RE = re.compile(r":\d+(?:-\d+)?$")


def normalise(literal):
    """Every spelling of one pin literal that could name a real path. Returns a set."""
    out = set()
    for form in (literal, literal.rstrip(TRAILING_PUNCT), CITATION_RE.sub("", literal)):
        form = form.strip()
        if not form:
            continue
        form = os.path.normpath(form)
        # A literal that escapes the repository root can never be a path inside it.
        if not form or form == "." or form.startswith(".."):
            continue
        out.add(form)
    return out


def pin_literals(text):
    """The dead literals of a pin file. Row shape: `<instrument> | <literal>`, `#` is a comment."""
    lits = set()
    rows = 0
    for line in text.splitlines():
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "|" not in line:
            continue
        rows += 1
        lits |= normalise(line.split("|", 1)[1])
    return lits, rows


def hazards(added, lits):
    """Pairs (added path, the pin literal it would resolve). SUPERSET -- see the header."""
    found = []
    for p in added:
        q = os.path.normpath(p.strip())
        if not q or q == ".":
            continue
        for lit in sorted(lits):
            if lit == q or q.startswith(lit + "/") or lit.startswith(q + "/") or lit.startswith(q):
                found.append((p, lit))
                break
    return found


def read_pin(repo, commit):
    """The pin AS IT IS IN THE PUSHED TREE. An error is never an empty pin (P-81)."""
    proc = subprocess.run(["git", "show", "%s:%s" % (commit, PIN_PATH)],
                          cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        return None, ("`git show %s:%s` exited %d: %s"
                      % (commit, PIN_PATH, proc.returncode, proc.stderr.strip()))
    return proc.stdout, None


# THE SELFTEST FIXTURE IS ASSEMBLED, NOT SPELLED, AND THAT IS T323'S RULE APPLIED RATHER THAN
# QUOTED. This file is a tracked `.softhouse/*.py`, so it is IN the dead-path census's own corpus,
# and a selftest whose fixture spelled the untracked uat path as a QUOTED literal would have
# GROWN the frontier by seven rows -- the instrument perturbing the very measurement its caller
# protects. Measured, on this branch, before this repair: deadOccurrences 108 -> 116, and 109
# after a first pass that repaired the fixture but left this very sentence quoting one of the
# spellings, which is T323's finding happening a third time and is why it is written out here.
#
# T323's test decides it: CAN THE INSTRUMENT STILL DO ITS JOB IF THE LITERAL GOES AWAY? Yes. The
# selftest needs *a* dead literal of each SHAPE, never those spellings. So REPAIR, do not pin.
# `SOFT` below carries no trailing slash, which is what keeps it out of the census's selector.
SOFT = ".softhouse"


def selftest():
    """P-22: a guard that cannot be shown to fail is worse than none, because it is believed.
    BOTH polarities, and the ABORT arm too -- an empty pin must refuse, not report `clean`."""
    fake = "\n".join([
        "# a comment row that must not become a literal",
        "%s/a/instrument.sh | %s/uat.md" % (SOFT, SOFT),
        "%s/a/instrument.sh | %s/toolchain" % (SOFT, SOFT),
        "%s/b/instrument.py | %s/vectors/PIN.json:dec1_revision" % (SOFT, SOFT),
        "%s/b/instrument.py | %s/x/y/deep/note.txt)" % (SOFT, SOFT),
    ])
    lits, rows = pin_literals(fake)
    cases = []

    def case(label, added, want_hazard, over=None):
        got = hazards(added, lits if over is None else over)
        ok = bool(got) == want_hazard
        cases.append((label, ok, got))
        print("  -> exit %d  %s%s" % (0 if ok else 1, label,
                                      ("  " + repr(got)) if got else ""))
        return ok

    if rows != 4:
        print("%s SELFTEST ABORT -- the fixture pin parsed %d rows, expected 4." % (PROBE, rows))
        return 2
    ok = True
    # RED: each of the spellings the census can resolve must be caught.
    ok &= case("RED exact literal", [SOFT + "/uat.md"], True)
    ok &= case("RED inside a dead directory literal", [SOFT + "/toolchain/go/bin/go"], True)
    ok &= case("RED a directory prefix of a dead literal", [SOFT + "/x/y"], True)
    ok &= case("RED a punctuation-stripped dead literal", [SOFT + "/x/y/deep/note.txt"], True)
    ok &= case("RED a citation-stripped dead literal", [SOFT + "/vectors/PIN.json"], True)
    # GREEN: the additions the driver actually makes must NOT be caught, or this is a freeze.
    ok &= case("GREEN the fire lock", [SOFT + "/LOCK"], False)
    ok &= case("GREEN an observation note", [SOFT + "/observations/note.md"], False)
    ok &= case("GREEN a handoff", [SOFT + "/handoff/some-handoff.md"], False)
    ok &= case("GREEN a comment row is not a literal", [SOFT + "/a/instrument.sh"], False)
    # THE ABORT ARM, DRIVEN AND NOT ASSERTED IN PROSE. An empty pin clears EVERY addition it is
    # asked about -- `hazards()` over an empty literal set returns nothing, which reads exactly
    # like a clean tree. That is why `main()` refuses on `rows < 1 or not lits` BEFORE calling
    # `hazards()` at all, and this case exists to show the trap is real rather than hypothetical:
    # the same input that is RED against the real pin comes back EMPTY against an empty one.
    empty, erows = pin_literals("# only comments\n\n")
    ok &= (erows == 0 and not empty)
    ok &= case("ABORT-ARM an empty pin clears a known-dead literal (hence main() refuses first)",
               [SOFT + "/uat.md"], False, over=empty)
    if not ok:
        print("%s SELFTEST FAILED -- at least one case did not behave as stated." % PROBE)
        return 1
    print("%s SELFTEST OK -- %d cases, both polarities driven." % (PROBE, len(cases)))
    return 0


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--commit")
    ap.add_argument("--paths-from")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not args.commit or not args.paths_from:
        print("%s ABORT(2) -- --commit and --paths-from are both required." % PROBE)
        return 2
    try:
        with open(args.paths_from, "r", encoding="utf-8") as fh:
            added = [l.strip() for l in fh if l.strip()]
    except OSError as exc:
        print("%s ABORT(2) -- could not read the added-path list: %s" % (PROBE, exc))
        return 2
    if not added:
        # Zero added paths is a legitimate question with a legitimate answer, and the CALLER is
        # expected not to ask it. Refusing here rather than printing a clean line keeps "nothing
        # was checked" from ever reading like "nothing was found".
        print("%s ABORT(2) -- the added-path list is EMPTY. A sweep over nothing proves nothing "
              "(P-35); the caller must not consult this program when there is nothing to ask "
              "about." % PROBE)
        return 2

    text, err = read_pin(args.repo, args.commit)
    if err is not None:
        print("%s ABORT(2) -- the dead-path pin could not be read out of the pushed tree. An "
              "error is never an empty pin, and an empty pin would make every addition look "
              "safe. %s" % (PROBE, err))
        return 2
    lits, rows = pin_literals(text)
    if rows < 1 or not lits:
        print("%s ABORT(2) -- the dead-path pin at %s parsed %d row(s) / %d literal(s) in the "
              "pushed tree. A pin that yields nothing would clear every addition it was asked "
              "about. REFUSING." % (PROBE, PIN_PATH, rows, len(lits)))
        return 2

    found = hazards(added, lits)
    print("%s pin=%s rows=%d literals=%d added=%d hazards=%d"
          % (PROBE, PIN_PATH, rows, len(lits), len(added), len(found)))
    if found:
        for path, lit in found:
            print("%s   HAZARD  %s  would make the pinned dead literal `%s` RESOLVE"
                  % (PROBE, path, lit))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
