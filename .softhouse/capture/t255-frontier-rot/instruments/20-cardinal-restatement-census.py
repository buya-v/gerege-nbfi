#!/usr/bin/env python3
"""
T258 -- THE CARDINAL-RESTATEMENT CENSUS.  The half of P-80 that does not have to be remembered.

WHY THIS EXISTS RATHER THAN THREE EDITS
---------------------------------------
T248 moved the fail-open frontier 9 -> 10 and T252 moved it 10 -> 11. Both corrected the count
WHERE IT IS NAMED -- `FAILOPEN_PIN_FILE_LIST` in `.softhouse/conformance.sh` -- and neither
corrected it WHERE IT IS RESTATED. T252 found one restatement and could not touch it. T258 was
dispatched to fix that one site, and the fix that only fixes that one site is worthless: the
mechanism is "a cardinal is maintained in more than one place", and repairing three copies by
hand leaves the fourth copy free to be written tomorrow by an author who has never heard of P-80.

T238's argument for a linter applies here verbatim and is not restated: a remedy that consists of
asking the next author to be more careful was already tried on the most careful author in the
chain and it failed. So the remedy is a CENSUS that runs afterwards, not a rule anybody has to
remember.

WHAT IT LOOKS FOR -- the CLASS, not the spelling
------------------------------------------------
  R1  `all <N> rows`          the frontier equality sentence, cardinal typed
  R2  `pinned at <N>`         the census cardinal, typed
  R3  `frontier <N>`          the measured cardinal, typed
  R4  `frontier == pinned` on a line that also carries a literal digit run

Every one of these is a place where a number that LIVES in `FAILOPEN_PIN_FILE_LIST` has been
copied into a second file. The copy reads as authoritative and rots silently. The remedy in every
case is the same and is stated in the report: DERIVE the count, do not type it.

CORPUS, AND THE BOUNDARY THAT IS DELIBERATE (P-66/P-70 -- both terms, and where I looked)
-----------------------------------------------------------------------------------------
Corpus = every TRACKED `.sh` and `.py` in the repository, from `git ls-files`. That boundary is
chosen, not accidental, and it has an exact meaning:

  * COMMITTED TRANSCRIPTS ARE `.txt` AND ARE NEVER SCANNED. A run log that recorded
    `frontier == pinned (all 9 rows, by path).` on the day it was true is a HISTORICAL RECORD.
    Retro-editing it to agree with a later document is forbidden (T114/T176) and would destroy
    the evidence that the frontier ever was nine. There are dozens of these; they are correct.
  * MERGED HANDOFFS AND REVIEWS ARE `.md` AND ARE NEVER SCANNED, for the same reason.
    `.softhouse/patterns.md` quotes the rotted sentence in P-80's own text; that quotation is the
    record of the defect and must survive verbatim.
  * LIVE INSTRUMENTS ARE `.sh`/`.py` AND ARE ALWAYS SCANNED. An instrument is a thing that will
    be RUN AGAIN. A cardinal inside one is an assertion about the future, not a record of the past.
  * `.softhouse/conformance.sh` IS EXEMPT, because it is the SOURCE OF TRUTH. It is the one file
    entitled to hold the pin, and T300 already made its printed cardinal derive from the list by
    counting it. Exempting the source is the whole point; exempting a copy would be the defect.
  * COMMENT LINES ARE NOT ASSERTIONS. A `#` line quoting the rotted sentence is documentation --
    this file's own header does it, and so does the repaired instrument's. Only code is censused.
  * A PYTHON MODULE DOCSTRING IS A COMMENT TOO, and is skipped for `.py` files by locating it with
    `ast` rather than by guessing at quote characters. This was not foresight: the first draft
    censused docstrings, flagged `t238-failopen/instruments/50-failopen-lint.py:127` (which is
    PROSE describing a past measurement), and then flagged THIS FILE'S OWN header the moment the
    header started naming the numbers it had found. A rule that fires on its own documentation is
    a rule that will be switched off. `ast.parse` failing is FATAL, never a silent skip.

WHAT THIS CENSUS WOULD MISS, STATED BEFORE ANY RESULT IS REPORTED
------------------------------------------------------------------
This matters more than the hit list, because a census that does not publish its blind spots is a
fail-open wearing the word "complete".

  (a) A CARDINAL SPELLED IN WORDS. `frontier == pinned, ELEVEN rows` is a real line in
      `.softhouse/capture/t252-tier3/instruments/50-conformance-red-drive.py:119`, and R1-R4 --
      which all require a DIGIT -- cannot see it. It is a label string rather than a predicate
      there, so it is currently harmless, but the rule genuinely does not cover the word form.
  (b) A CARDINAL COMPUTED INTO A VARIABLE EARLIER AND ASSERTED LATER. Only the literal line is
      examined; no dataflow is tracked.
  (c) A RESTATEMENT ROTTED ON PUNCTUATION RATHER THAN ON THE NUMBER. This is not hypothetical and
      it is the finding of T258's sweep: two live instruments assert `pinned at 11.` WITH A
      TRAILING PERIOD, the count is still CORRECT, and T300's rewording removed the period, so
      both are FALSE TODAY. No search for a number can find that. It is caught only by the
      SECOND arm below, `--against <conformance transcript>`, which takes every cardinal literal
      this census found and asks whether that exact string still occurs in a real graded run.
  (d) A RESTATEMENT IN A FILE TYPE OUTSIDE `.sh`/`.py`. SEVERAL EXIST, they were found BY HAND
      and not by this census, and they are deliberately left to the driver:
        `.softhouse/state/DRIVER.STATE.json`  -- FIVE restatements (lines 18, 48, 53, 111, 112),
             not the one the brief named. All read 11 and are CORRECT today. DRIVER-MAINTAINED
             STATE; an agent must not edit it.
        `.softhouse/RESUME.md:24` -- the dispatch line for this very task describes the defect as
             "`all 9 rows` vs a frontier of 109". THE FAIL-OPEN FRONTIER IS 11. 109 is the
             DEAD-PATH frontier (T316/T323), a DIFFERENT pin. This is the same class one level
             up and the nastiest variant of it: the number is not stale, it is the RIGHT number
             for the WRONG frontier, so it survives every check that asks "is this count
             current?". Driver-maintained; reported, not edited.
        `.softhouse/gates.md:4434`, `program.json:2053,2194`, `tasks.json` (several) -- records of
             bars that were run, correct as history.
      The rule is extension-scoped BY CHOICE -- widening it to `.md`/`.json` would sweep in
      hundreds of correct historical records -- but the choice is a blind spot and is named here
      rather than left to be discovered.

ENGINE (P-33/P-53/P-75): pure Python `re` over bytes decoded as UTF-8, no shell, no `grep`, no
`git grep -E` -- so no `\\b`/`\\d` semantics are in play at all. The corpus comes from
`git ls-files -z` via `subprocess.run(..., check=True)`; a failure RAISES rather than yielding an
empty corpus that would read as a clean tree. CALIBRATION (P-72) is run first and is FATAL: a
known-positive line and a known-negative line are put through the same matchers, and if the
positive is not matched or the negative is, this census DIES without reporting any zero.

EXIT: 0 = the measured set equals the pin below; 1 = it does not; 2 = the census could not reach
or trust its own corpus. It fails closed in every direction.

STATUS -- READ THIS BEFORE CITING IT (P-45)
--------------------------------------------
THIS CENSUS IS NOT WIRED INTO `.softhouse/conformance.sh`. That file is held exclusively by T323
this batch and T258 may not touch it. Nobody may cite this as an enforced control until it is
wired. The exact wiring line is in T258's handoff under `## Follow-ups`, together with the two
source patches that would let the pin below go empty.
"""
import ast
import os
import re
import subprocess
import sys

BANNER = "T258 CARDINAL-RESTATEMENT CENSUS"

# The one file entitled to hold the cardinal: it IS the pin.
SOURCE_OF_TRUTH = ".softhouse/conformance.sh"

# ---------------------------------------------------------------------------
# TWO RULE SETS, AND THE NARROWING IS MEASURED RATHER THAN ASSERTED.  [T248's method]
# ---------------------------------------------------------------------------
# WIDE is the rule as first written. It was run over the whole tree before any narrowing, and it
# produced FOUR hits that are not this defect at all:
#
#   capture/audit-t44/charges/bin/spotcheck.py:20        "... worked example, all 13 rows"
#   capture/pathb/t149/promote-vector.py:151             "... apart on all 12 rows, period 12's"
#       -- SCHEDULE row counts. A loan schedule has rows too. Nothing to do with any frontier.
#   capture/t238-failopen/instruments/50-failopen-lint.py:127   "frontier 10 -> 10. GAINED 0."
#       -- PROSE INSIDE THE MODULE DOCSTRING. It is documentation exactly as a `#` comment is,
#          but it is not a `#` line, so the comment filter cannot see it.
#   capture/t64-zeroprincipal/src/T64-promote-vectors.py:167    "balance pinned at 0.28 through"
#       -- A MONEY FIGURE. `[0-9]+` matched the `0` of `0.28`.
#
# NARROW adds exactly three conditions, each aimed at one of those and at nothing else:
#   N1  `all <N> rows` counts only if `frontier` or `pinned` also appears on the line.
#   N2  `pinned at <N>` counts only if <N> is an INTEGER -- a following `.<digit>` disqualifies it.
#   N3  `frontier <N>` counts only if the line carries a QUOTE character, i.e. the cardinal is
#       inside a string literal being compared or printed, not inside running prose.
#
# BOTH SETS ARE RUN AND BOTH TALLIES ARE PRINTED (P-67 -- state both terms). The narrowing is
# therefore auditable: a reader sees exactly what it dropped and can disagree with it. What the
# narrowing is NOT allowed to do is drop a real site, and every row it drops is listed by name.
# A rule is (tag, CORE pattern, CONTEXT pattern or None). The CORE must match somewhere in the
# line; the CONTEXT, when present, must ALSO match somewhere in the line. Keeping the two apart
# is not style -- the first draft folded the context into a lookahead, the lookahead anchored at
# the CORE's match position instead of at the line, and the FATAL CALIBRATION below caught it on
# the very next run. That is what the calibration is for, and it is why it is fatal.
RULES_WIDE = (
    ("R1", re.compile(r"all\s+[0-9]+\s+rows"), None),
    ("R2", re.compile(r"pinned\s+at\s+[0-9]+"), None),
    ("R3", re.compile(r"frontier\s+[0-9]+"), None),
    ("R4", re.compile(r"frontier\s*==\s*pinned.*[0-9]"), None),
)
RULES = (
    ("R1", re.compile(r"all\s+[0-9]+\s+rows"), re.compile(r"frontier|pinned")),
    ("R2", re.compile(r"pinned\s+at\s+[0-9]+(?![0-9]*\.[0-9])"), None),
    ("R3", re.compile(r"frontier\s+[0-9]+"), re.compile(r"[\"']")),
    # N4: WIDE R4 is "frontier == pinned" plus a digit ANYWHERE on the line, and this looseness
    # was found by the rule FIRING ON ITSELF -- it matched this file's own calibration line
    # because the expected-tag set `{"R1", "R4"}` sitting after the sentence contains digits.
    # The cardinal in this sentence always sits immediately after the phrase, so NARROW R4 wants
    # the digit within 30 characters with no digit in between. The calibration positive still
    # matches (six characters of " (all " separate them), which the FATAL CAL+ check re-proves on
    # every run -- so this narrowing cannot quietly turn R4 off.
    ("R4", re.compile(r"frontier\s*==\s*pinned[^0-9\n]{0,30}[0-9]"), None),
)

# ---------------------------------------------------------------------------
# THE PIN.  Same idiom, and deliberately the same terms, as FAILOPEN_PIN_FILE_LIST.
# ---------------------------------------------------------------------------
# These are the restatements that EXIST TODAY and that T258 was not permitted to repair: both
# live outside T258's `files_hint`, and repairing another task's instrument unasked is the error
# this program keeps punishing (P-40). They are recorded here, visible, and refusing to grow.
#
# IT IS A FRONTIER, NOT AN AMNESTY. When the patches in T258's handoff land, each row must leave
# this list IN THE SAME COMMIT -- a row still pinned after its site is repaired is this list
# excusing a weakness that is no longer there, which is the exact sentence
# `FAILOPEN_PIN_FILE_LIST` uses about itself.
# EVERY ROW IS ADJUDICATED, AND THE THREE VERDICTS ARE DIFFERENT THINGS:
#
#   ROT -- a live assertion whose cardinal is copied and will rot. Must be repaired; the exact
#          patch is in T258's handoff. Outside T258's files_hint, so pinned, not touched (P-40).
#     R1/R2/R4  capture/t252-tier3/instruments/50-conformance-red-drive.py:120,121
#     R1/R2/R3/R4  reviews/t262-verdict-predicate/bar_check_t262.sh:55,56
#          BOTH of these are ALREADY FALSE, and not on the number. They assert `pinned at 11.`
#          WITH A TRAILING PERIOD; T300 reworded that harness line and the period is gone. RUN,
#          not read: bar_check_t262.sh over a graded run at T258's commit prints
#          `MISMATCH frontier count   expected: frontier 11, pinned at 11.`
#          (transcript: transcripts/30-t262-barcheck-rotted-today.txt). The count 11 is still
#          correct. This is the half of the class that no search for a number can find.
#     R3   capture/t328-date-rule-promotion/instruments/95-frontier-delta.sh:120
#          A DIFFERENT frontier -- the DEAD-PATH frontier (T316/T323), not the fail-open one --
#          and the same defect one pin over: the script MEASURES the count into `$bd`/`$dd`/`$ad`
#          and then prints an UNCONDITIONAL `CONCLUSION: dead-path frontier 109 == pinned 109`
#          in which the 109 is typed. Move the frontier and that sentence still says 109. Patch:
#          print the measured variable.
#
#   SPECIMEN -- pinned PERMANENTLY, repairing it would destroy the evidence it exists to be.
#          The identical status `sweep-ORIGINAL.sh` holds on FAILOPEN_PIN_FILE_LIST.
#     R2   capture/t300-census-cardinal/instruments/10-cardinal-sweep.sh:120,121
#     R2   capture/t300-census-cardinal/instruments/50-red-drive.sh:114
#          The first GENERATES a synthetic conformance.sh carrying a typed cardinal, as the
#          SUBJECT of T300's own red drive; the second greps that generated subject for it.
#          Neither cardinal is ever compared against a real graded run, and the generator and
#          the grep are the same task's two halves, so they cannot drift apart. Repairing them
#          would delete T300's red drive.
#
#   ACCEPTED BY DESIGN -- a restatement that carries its own provenance and is printed BESIDE
#          the live reading, which is the correct handling of a baseline rather than the defect.
#     R3   reviews/t254-harness-portability/instruments/42-bar-extract.py:51
#          The literal is labelled `driver baseline @ c0e88c6` -- COMMIT-QUALIFIED -- and the
#          four `one(...)` calls immediately below it re-read the same figures LIVE out of the
#          transcript and print them next to it. A reader is shown both terms and cannot mistake
#          the baseline for a current measurement. Left alone deliberately, not overlooked.
# THE SECOND ARM ASKS A NARROWER QUESTION THAN THE PIN DOES, and this set is the difference.
# The pin asks "is a cardinal typed here?". The second arm asks "does this exact literal still
# occur in a graded run?" -- and that question is simply NOT APPLICABLE to a literal that was
# never supposed to occur in one:
#   * a SPECIMEN's literal is compared against a subject the same task GENERATES (t300);
#   * a commit-qualified BASELINE is a record of another commit and must not match today (t254);
#   * an INSTRUMENT'S OWN conclusion line is its own output, never the harness's (t328) -- note
#     that t328 IS adjudicated ROT by the pin above; it is excluded HERE only because the second
#     arm's question does not reach it. Membership here is NOT an acquittal.
# Rows in this set are still LISTED, labelled `by-design`, because a suppression nobody can see
# is worse than the noise it removes.
NOT_EXPECTED_IN_A_GRADED_RUN = frozenset((
    ".softhouse/capture/t300-census-cardinal/instruments/10-cardinal-sweep.sh",
    ".softhouse/capture/t300-census-cardinal/instruments/50-red-drive.sh",
    ".softhouse/reviews/t254-harness-portability/instruments/42-bar-extract.py",
    ".softhouse/capture/t328-date-rule-promotion/instruments/95-frontier-delta.sh",
))

CARDINAL_PIN = """R1 .softhouse/capture/t252-tier3/instruments/50-conformance-red-drive.py
R2 .softhouse/capture/t252-tier3/instruments/50-conformance-red-drive.py
R4 .softhouse/capture/t252-tier3/instruments/50-conformance-red-drive.py
R2 .softhouse/capture/t300-census-cardinal/instruments/10-cardinal-sweep.sh
R2 .softhouse/capture/t300-census-cardinal/instruments/50-red-drive.sh
R3 .softhouse/capture/t328-date-rule-promotion/instruments/95-frontier-delta.sh
R3 .softhouse/reviews/t254-harness-portability/instruments/42-bar-extract.py
R1 .softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh
R2 .softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh
R3 .softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh
R4 .softhouse/reviews/t262-verdict-predicate/bar_check_t262.sh"""

# CALIBRATION (P-72). Fatal, and run before any negative is reported.
#
# ASSEMBLED, NOT PASTED, and that is not style. The P-72 positive has to BE a real instance of
# the thing detected, so written out literally it makes this census flag ITSELF -- MEASURED, it
# did, at :238 under R1 and R4. A detector cannot be its own frontier row without either
# measuring itself or acquiring an exemption, and an exemption on the detector is the worst place
# in the system to put one. T243's planted fail-open sweep is assembled from variables for
# exactly this reason. The literal exists only at run time and the CAL+ line prints it in full,
# so nothing is hidden -- it is moved out of the corpus, not out of sight.
_CAL_N = 9
CAL_POSITIVE = ("frontier == pinned (all %d rows, by path)." % _CAL_N, {"R1", "R4"})
CAL_NEGATIVE = ('the frontier equals the pin, by path, with no cardinal here', set())


def die(msg, code=2):
    print("%s: REFUSED -- %s" % (BANNER, msg))
    sys.exit(code)


def docstring_lines(rel, raw):
    """The 1-based line numbers of the module docstring of a .py file, as a set. A parse failure
    is FATAL: a census that silently treats an unparseable file as having no documentation would
    report its prose as assertions, which is a false positive, and one that trains readers to
    ignore the report."""
    if not rel.endswith(".py"):
        return frozenset()
    try:
        tree = ast.parse(raw)
    except SyntaxError as e:
        die("%s does not parse as Python (%s), so its documentation cannot be told from its "
            "assertions." % (rel, e))
    if not tree.body:
        return frozenset()
    n0 = tree.body[0]
    if not (isinstance(n0, ast.Expr) and isinstance(n0.value, ast.Constant)
            and isinstance(n0.value.value, str)):
        return frozenset()
    return frozenset(range(n0.lineno, (n0.end_lineno or n0.lineno) + 1))


def matchers(line, rules=RULES):
    out = set()
    for tag, core, ctx in rules:
        if core.search(line) and (ctx is None or ctx.search(line)):
            out.add(tag)
    return out


def calibrate():
    pos_line, pos_want = CAL_POSITIVE
    neg_line, neg_want = CAL_NEGATIVE
    pos_got, neg_got = matchers(pos_line), matchers(neg_line)
    print("CALIBRATION (P-72), fatal:")
    print("  CAL+  %-62r -> %s (want %s)" % (pos_line, sorted(pos_got), sorted(pos_want)))
    print("  CAL-  %-62r -> %s (want %s)" % (neg_line, sorted(neg_got), sorted(neg_want)))
    if not pos_want.issubset(pos_got):
        die("the known-positive calibration line was NOT matched. Every zero below would be a "
            "silent matcher failure rather than a measured absence.")
    if neg_got != neg_want:
        die("the known-negative calibration line WAS matched. The matchers are not the rule.")
    print("  calibration OK -- a zero from this run is a real zero.")
    print()


def corpus(root):
    r = subprocess.run(["git", "-C", root, "ls-files", "-z", "*.sh", "*.py"],
                       capture_output=True, check=True)
    files = [f for f in r.stdout.decode("utf-8").split("\0") if f]
    return files


def main():
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()
    print(BANNER)
    print("root   : %s" % root)
    print("commit : %s" % subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                                         capture_output=True, text=True,
                                         check=True).stdout.strip())
    print()
    calibrate()

    files = corpus(root)
    # C3: the corpus assertion. A census over nothing passes everything.
    if len(files) < 1:
        die("git ls-files returned NO tracked .sh/.py at all.")
    print("corpus : %d tracked .sh/.py file(s) (git ls-files, whole repository)" % len(files))
    print("exempt : %s -- the SOURCE OF TRUTH, the one file entitled to hold the cardinal" %
          SOURCE_OF_TRUTH)
    print()

    hits = []          # (rule, path, lineno, text) -- NARROW
    dropped = []       # (rule, path, lineno, text) -- WIDE minus NARROW
    scanned = 0
    for rel in sorted(files):
        if rel == SOURCE_OF_TRUTH:
            continue
        ap = os.path.join(root, rel)
        try:
            with open(ap, "rb") as fh:
                raw = fh.read()
        except OSError as e:
            die("could not read a corpus file that git lists: %s (%s)" % (rel, e))
        scanned += 1
        text = raw.decode("utf-8", "replace")
        doc = docstring_lines(rel, text)
        for n, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#") or n in doc:
                continue            # documentation, not an assertion
            wide = matchers(line, RULES_WIDE)
            narrow = matchers(line, RULES)
            for tag in sorted(narrow):
                hits.append((tag, rel, n, line.strip()))
            for tag in sorted(wide - narrow):
                dropped.append((tag, rel, n, line.strip()))

    print("scanned: %d file(s) after the exemption" % scanned)
    print()
    print("WIDE minus NARROW -- what the narrowing DROPPED, listed so it can be disputed:")
    if not dropped:
        print("  (none)")
    for tag, rel, n, text in dropped:
        print("  %-3s %s:%d" % (tag, rel, n))
        print("      | %s" % text[:150])
    print("  WIDE total %d, NARROW total %d, dropped %d" %
          (len(hits) + len(dropped), len(hits), len(dropped)))
    print()
    print("MEASURED restatements (rule, file:line):")
    if not hits:
        print("  (none)")
    for tag, rel, n, text in hits:
        print("  %-3s %s:%d" % (tag, rel, n))
        print("      | %s" % text[:150])
    print()

    got = sorted({"%s %s" % (tag, rel) for tag, rel, _n, _t in hits})
    want = sorted(l.strip() for l in CARDINAL_PIN.splitlines() if l.strip())
    print("PIN COMPARISON (- pinned, + measured), by (rule, file):")
    added = [x for x in got if x not in want]
    removed = [x for x in want if x not in got]
    for x in removed:
        print("  -%s" % x)
    for x in added:
        print("  +%s" % x)
    if not added and not removed:
        print("  frontier == pinned (all %d rows, by rule and path)" % len(want))

    # NOTE, and it is deliberate: the line above is the ONLY cardinal this file prints, and it is
    # `len(want)` -- COUNTED from CARDINAL_PIN, never typed. This census does not get to commit
    # the defect it exists to detect.

    print()
    if added:
        print("A '+' row is a NEW restatement of a cardinal that lives in FAILOPEN_PIN_FILE_LIST.")
        print("DERIVE the count from the pin at run time; do not type it. The repaired shape is")
        print(".softhouse/capture/t243-wiring/instruments/20-failopen-red-drive.sh (T258).")
    if removed:
        print("A '-' row is a restatement that was REPAIRED or DELETED. That is GOOD NEWS and this")
        print("pin must lose the row IN THE SAME COMMIT, or the pin starts excusing a weakness")
        print("that is no longer there. IT IS A FRONTIER, NOT AN AMNESTY.")

    # ---- SECOND ARM: the rot that carries no wrong number ----------------
    rc = 1 if (added or removed) else 0
    against = None
    for i, a in enumerate(sys.argv):
        if a == "--against" and i + 1 < len(sys.argv):
            against = sys.argv[i + 1]
    if against:
        print()
        print("SECOND ARM -- every cardinal literal above, checked against a REAL graded run.")
        print("This is the arm that catches a restatement rotted on PUNCTUATION rather than on")
        print("the number, which no search for a number can find.")
        print("transcript: %s" % against)
        try:
            with open(against, "rb") as fh:
                bar = fh.read().decode("utf-8", "replace")
        except OSError as e:
            die("--against transcript unreadable: %s" % e)
        if "CENSUS fail-open instruments" not in bar:
            die("--against transcript carries no fail-open census banner, so it is not a graded "
                "run and an absence measured over it would mean nothing.")
        stale = 0
        seen = set()
        for tag, rel, n, text in hits:
            for rx in (r'"([^"]*(?:all [0-9]+ rows|pinned at [0-9]+|frontier [0-9]+)[^"]*)"',):
                for lit in re.findall(rx, text):
                    # A line matched by two rules is ONE restatement, not two. Counting it twice
                    # would inflate a published cardinal, in a census about published cardinals.
                    if (rel, n, lit) in seen:
                        continue
                    seen.add((rel, n, lit))
                    present = lit in bar
                    if present:
                        label = "live"
                    elif rel in NOT_EXPECTED_IN_A_GRADED_RUN:
                        label = "by-design"   # specimen subject, or a commit-qualified baseline
                    else:
                        label = "STALE"
                        stale += 1
                    print("  %-9s %s:%d  %r" % (label, rel, n, lit))
        print("  literals asserted that DO NOT OCCUR in that graded run: %d" % stale)
        if stale:
            rc = 1
            print("  Each is a live assertion that is FALSE TODAY. Note the count in it may still")
            print("  be right -- the sentence around it moved.")

    print()
    print("%s: %s" % (BANNER, "PIN MATCHED" if rc == 0 else "REFUSED"))
    sys.exit(rc)


if __name__ == "__main__":
    main()
