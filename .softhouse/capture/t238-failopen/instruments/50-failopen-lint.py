#!/usr/bin/env python3
"""
T238 -- THE FAIL-OPEN LINTER.  This is the half of the fix that does not have to be remembered.

THE ARGUMENT FOR IT, WHICH IS THE WHOLE POINT OF THIS TASK
----------------------------------------------------------
A2-33 is the best-calibrated sweep in this chain. It published two-engine recall transcripts
with MISSES=0, it named its engine and flags, and it audited every one of its own 34 patterns
for \\b \\d \\s \\w before P-72 was a week old. On every axis T234 was dispatched to test,
A2-33 PASSES. And it still shipped a fail-open, because the defect was not in the regex layer
at all -- it was one unguarded `cd` in a subshell whose non-zero exit was caught by a `||` arm
that printed reassurance.

So: **a remedy that consists of asking the next author to be more careful cannot work here,
because it was already tried on the most careful author in the chain and it failed.**

That rules out discipline. It also rules out a library ON ITS OWN: sweeplib.sh is adoptable,
and anything adoptable is omittable by exactly the person who did not think they needed it.

A linter is different in kind. It does not ask the author to remember anything. It runs over
the tree afterwards and refuses instruments that can emit a negative they did not measure.
The author's carefulness stops being load-bearing. That is why the mechanism is a LINTER FIRST
and a LIBRARY SECOND: the library is what the linter tells you to adopt, not the fix itself.

HONEST LIMITATION, STATED LOUDLY (P-45, which now has FOUR instances in this program)
------------------------------------------------------------------------------------
This linter is NOT wired into .softhouse/conformance.sh, because that file is held by T243 and
T226 and is outside T238's scope. An unwired guard is precisely the P-45 shape, and shipping
one silently would be adding a fifth instance. It is therefore shipped with:
  - a RED drive and a GREEN drive, both committed (transcripts/40, transcripts/60);
  - the exact wiring line, in the handoff, for whoever holds conformance.sh next;
  - this paragraph, so nobody can cite it as an enforced control.

WHAT IT CHECKS -- the properties, not the spellings
---------------------------------------------------
  C1  NO DEAD ABSOLUTE PATH        an absolute path that does not exist NOW
  C2  NO REASSURING FAILURE ARM    a search/cd whose failure is swallowed and which is
                                   followed by a print the reader will take as a measurement,
                                   whether that print is an ARM of the construct (C2a) or an
                                   UNCONDITIONAL line after it (C2b)
  C3  CORPUS ASSERTION PRESENT     a repo-wide search instrument must assert its corpus is
                                   reachable and non-empty before searching
  C4  CALIBRATION PRESENT          P-72: a known positive must be proven findable before any
                                   negative is reported
  C5  ENGINE DECLARED              P-33/P-53: name the engine; and never use \\b \\d \\s \\w
                                   under `git grep -E`, which reads them as literals

SCOPE (P-66/P-70): every tracked .sh/.py in the repository. Exit 0 = clean, 1 = violations,
2 = the linter could not reach its own corpus (it fails closed too).

T248 -- THE WIDENING, AND WHY THE ORIGINAL BOUNDARY WAS WRONG (P-76)
--------------------------------------------------------------------
The driver drove T243's wiring of this linter RED and it DID NOT FIRE. T238 wrote both C1 and
C2 from ONE example -- A2-33's `sweep.sh` -- and the rules came out shaped like that example
rather than like the class. The second confirmed live site, `.softhouse/reviews/T138-evidence/
r11-hygiene.sh:77-79`, was flagged ZERO times. T248 MEASURED both boundaries black-box before
touching either (transcripts 10 and 20 under .softhouse/capture/t248-failopen-widen/):

  C1's REAL rule, as measured, was FOUR filesystem roots -- /Users /home /opt /var -- with a
  >=6-char tail and a lead character in [start-of-line = whitespace " ' (]. Every other root was
  INVISIBLE: /tmp, /private, /srv, /data, /mnt, /nonexistent all measured "no". `r11-hygiene.sh`
  dies on `cd /tmp/T138-merge`, so C1 could not see it AT ALL -- which is why widening C2 alone
  would have put it on the frontier at TIER 2, i.e. labelled "corpus reachable today" about an
  instrument whose corpus has not existed for days. Measured, not assumed: transcript 20, V1.

  C2's REAL rule was `|| echo` -- the reassurance had to be an ARM of the failing construct.
  r11's reassurance is an UNCONDITIONAL `echo` on the NEXT LINE. Same defect, same exit 0, same
  false sentence in the reader's face, different syntax.

So both halves are widened, and BOTH ARE STRICTLY ADDITIVE -- every string the old rules matched,
the new rules still match. Nothing that was inadmissible becomes admissible.

  C1 = (legacy 4-root rule, UNCHANGED)
       UNION
       (any absolute path of >=2 segments, in a LOCATION POSITION, that does not exist now)

     "LOCATION POSITION" is the load-bearing narrowing that pays for dropping the root list:
     the path must be the operand of something that READS a location -- cd/pushd/source/./ls/
     cat/stat/git -C/--git-dir=/--work-tree=/test -d/[ -d -- or the RHS of a variable
     assignment. A path merely MENTIONED (inside a grep pattern, a fixture string, a sentence)
     is not a corpus claim and is not flagged. Measured cost of NOT having this narrowing:
     conformance.sh itself would have been flagged three times on `"/contract/contract.go$"`
     (a grep PATTERN) and on two CENSUS fixture strings containing `/x/...`.
     Two further filters, both from measurement:
       * a literal containing `XXX` is a `mktemp` TEMPLATE, not a path (5 false hits removed);
       * a path the file itself OWNS -- one it creates or deletes with `>`/`>>`/rm/mkdir/
         touch/tee/mktemp -- is scratch, not corpus (removed the unearned TIER2->TIER1
         promotion of t239's 50-red-drive.sh on `/tmp/t239-red-index` and `/tmp/x.tar`).

  C2 = C2a (legacy `|| echo` arm, UNCHANGED)
       UNION
       C2b: an UNCONDITIONAL echo/printf whose text CLAIMS AN ABSENCE OR A COMPLETED SEARCH,
            appearing within THREE code lines after a construct whose failure is swallowed,
            with only other prints in between.

     "failure is swallowed" is deliberately restricted to a `cd` that does not terminate the
     script -- `cd X || exit`, `|| return`, `|| die`, `|| { ... exit` are fatal and exempt.
     The wider variant that also treats `git grep ... | sed ...` (a pipeline that discards the
     searcher's exit status) as swallowing was MEASURED and REJECTED for now: it adds two more
     frontier entries (t239's 21-crosscheck.sh, a2-33's sweep.sh) whose reassurance is real
     narration, and the marginal true positives it buys are already caught by C1+C2a. It is
     recorded as the next widening, not as a thing nobody thought of. See transcript 20, V4.

  WHY NOT A LOOSER RULE. 891 tracked .sh/.py are scanned and 39 are repo-wide search
  instruments; every extra frontier row is a source edit in `conformance.sh` for a human to
  read, so a rule that flags narration is a rule that gets pinned away. WHY NOT A TIGHTER ONE:
  because a tighter one is exactly what shipped, and it missed the site that motivated the task.
"""
import os
import re
import sys
import json
import subprocess

# SEVERITY, derived from MEASUREMENT (transcripts/20), not from taste.
#
#   C1 alone   = UNREPRODUCIBLE.  a2-31-dec2-rev4/probe-sweep.sh hard-codes a deleted worktree
#                AND exits 1. It is safe -- but it can never be re-run to CHECK its conclusion.
#                That is the "more dangerous half" only in the long run, so: WARN, not FAIL.
#   C1 AND C2  = FAIL-OPEN.  Cannot reach its corpus AND prints reassurance. This is the lethal
#                combination, and it is exactly the set my run-the-class transcript measured
#                as exit-0-with-"(no hits)". FAIL.
#   C2 alone   = FAIL-OPEN-CAPABLE. The corpus is reachable today, so the reassurance arm is
#                dormant -- but it is one deleted directory away from live. FAIL.
#
# SUPPRESSION. A probe whose PURPOSE is to test whether a path exists will trip C1 honestly.
# Such a line may carry a marker, which must state a reason:
#     # lint-failopen: ok -- <reason>
# The marker suppresses that ONE line. It is deliberately verbose so it cannot be used lazily,
# and every use is listed in the report so suppressions stay visible.
SEVERITY_FAIL = {"C2"}
RE_SUPPRESS = re.compile(r'#\s*lint-failopen:\s*ok\s*--\s*(\S.*)')
ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("LINT ABORT (2): not inside a git work tree; cannot reach the corpus.", file=sys.stderr)
    sys.exit(2)
os.chdir(ROOT)
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

files = [f for f in subprocess.run(["git", "ls-files"], capture_output=True, text=True)
         .stdout.split("\n") if f.endswith((".sh", ".py"))]
if not files:
    print("LINT ABORT (2): corpus reachable but contains ZERO .sh/.py files. "
          "Linting nothing proves nothing (P-35).", file=sys.stderr)
    sys.exit(2)

ONLY = sys.argv[1:] or None
if ONLY:
    files = [f for f in files if any(f.startswith(p) or f == p for p in ONLY)]

# --- C1 ---------------------------------------------------------------------
# LEGACY, byte-for-byte as T238 shipped it. Kept so the widening is provably ADDITIVE:
# no path this expression used to flag can stop being flagged.
RE_ABSPATH = re.compile(r'(?:^|[=\s"\'(])(/(?:Users|home|opt|var)/[A-Za-z0-9._/-]{6,})')
# T248 ADDITION: any root, but only in a position that READS a location.
# `/` is deliberately absent from the lead alternatives, which is what keeps
# `https://host/path` out without naming URLs anywhere.
RE_ABSPATH_LOC = re.compile(
    r'(?:\bcd\b|\bpushd\b|\bsource\b|\bls\b|\bcat\b|\bstat\b|\bgit\s+-C\b|\s-C\b|'
    r'--git-dir=|--work-tree=|\[\s*-[a-zA-Z]\s|\btest\s+-[a-zA-Z]\s|'
    r'(?:^|[;&|(]\s*)\.\s|(?:^|[;&|(\s])(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*=)'
    r'\s*["\']?(/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+)')
# A path the instrument CREATES or DELETES is its own scratch, not the corpus it reads.
RE_OWNED_HEAD = r'(?:>>?|\brm\b|\bmkdir\b|\btouch\b|\btee\b|\bmktemp\b)\s*(?:-\S+\s+)*["\']?'

# THE CORPUS SELECTOR, AND THE THIRD BLIND SPOT T248's RED DRIVE FOUND.
#
# Everything above only ever runs on a file this expression recognises as a repo-wide search
# instrument. The shipped spelling required the literal `git grep` / `git ls-files`, so
#     git -C /nonexistent/worktree/agent-adeadbeef grep -n -E 'pattern' -- . || echo "(no hits)"
# -- a dead path AND a reassuring `|| echo` arm, both conditions the linter already had --
# was not merely unclassified, it was NEVER LOOKED AT: the file did not enter the inspected
# set at all. Found by driving shape R4, which is the driver's own probe-1 idiom moved off
# `cd` and onto `git -C`. That is worth stating plainly, because it is the general lesson of
# P-76 in its sharpest form: a rule's blind spots are not only in its conditions, they are in
# how it chose the population to apply them to, and a census of 891 files that reports "38
# instruments" has already made an unexamined decision about the other 853.
RE_REPOWIDE = re.compile(
    r'(git\s+(?:-[A-Za-z]\s+\S+\s+|--[A-Za-z-]+=\S+\s+|-[A-Za-z]+\s+)*(?:grep|ls-files)\b'
    r'|grep\s+-[a-zA-Z]*[rR]\b)')

# --- C2 ---------------------------------------------------------------------
RE_SWALLOW = re.compile(r'\|\|\s*(?:echo|printf)\b')          # C2a, unchanged
# C2b. A `cd` whose failure does NOT terminate: the script carries on and whatever
# it prints next is printed about a directory it never entered.
RE_CD = re.compile(r'(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+)cd\s+\S')
RE_CD_FATAL = re.compile(r'cd\s[^;&|]*\|\|\s*(?:exit|return|die|_sw_die|\{)')
RE_UNCOND_PRINT = re.compile(r'^\s*(?:echo|printf)\b')
# THE REASSURANCE VOCABULARY. It is about the CLAIM, not the tone: every entry is a way of
# saying "there was nothing" or "I looked". Derived from the two live specimens' actual text
# -- "(no hits)", "(searched the MERGED tree)", "(nothing above, or only prose, = clean)",
# "(only GUARDS-RED.txt / new files expected above)" -- and generalised one step, no further.
#
# TIGHTENED BY ITS OWN RED DRIVE. The first draft carried bare `\bzero\b`, bare `\babove\b`
# and bare `\bempty\b`, and driving shape R2 (below) widened the window enough that those
# bare words reached `a2-34-review-a2-15/rederive-provenance.sh:28` -- a SECTION HEADER
# reading "CALIBRATION (P-72): instrument must show non-zero recall AND a true zero". A
# heading that DISCUSSES zeros is not a sentence CLAIMING one, and promoting a file to
# TIER 1 on it would be this linter asserting something it had not established. Every
# alternative below is now a claim shape, not a word.
RE_REASSURE = re.compile(
    r'\(\s*no\b|\bno hits\b|\bno match|\bnot found\b|\bnothing\b|\bnone\b|'
    r'\bzero (?:hits|matches|results|rows|findings|violations)\b|'
    r'\b0 (?:hits|matches|results|rows|findings|violations)\b|'
    r'\bclean\b|\bsearched\b|\ball clear\b|\b(?:is|are|was|were) empty\b|'
    r'\bexpected above\b|\bno other\b|\bno further\b|\bno remaining\b', re.I)
C2B_WINDOW = 3
RE_CORPUS_ASSERT = re.compile(
    r'rev-parse\s+--show-toplevel|ls-files\s*\|\s*wc|SWEEP ABORT|_sw_die|sweep_root|'
    r'\|\|\s*exit\b|\|\|\s*\{[^}]*exit|os\.path\.isdir|check=True|exit\(2\)|sys\.exit')
RE_CALIB = re.compile(r'calibrat|CALIB|known positive|P-72', re.I)
RE_ENGINE_DECL = re.compile(r'ENGINE|git --version|grep --version|engine', re.I)
RE_ESCAPE_IN_ERE = re.compile(r'git\s+grep[^|\n]*-[a-zA-Z]*E[a-zA-Z]*\s[^|\n]*\\[bBdDsSwW<>]')
SELF = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"


def _is_code(l):
    return bool(l.strip()) and not l.lstrip().startswith("#") and not RE_SUPPRESS.search(l)


def _logical(lines):
    """[(first_idx0, last_idx0, joined_text)] honouring backslash continuations.

    A `cd X 2>/dev/null && \\` + `git grep ...` is ONE construct, and the reassurance that
    follows it follows the SECOND physical line. Reading physical lines only is how the
    original C2 could look straight at r11-hygiene.sh:77 and see nothing after it.
    """
    out = []
    i = 0
    n = len(lines)
    while i < n:
        j = i
        buf = [lines[i]]
        while lines[j].rstrip().endswith("\\") and j + 1 < n:
            j += 1
            buf.append(lines[j])
        out.append((i, j, " ".join(x.rstrip().rstrip("\\") for x in buf)))
        i = j + 1
    return out


def _dead_paths(line, txt):
    """Absolute path literals on `line` that do not exist NOW.

    UNION of the legacy 4-root rule and the T248 location-position rule; additive by
    construction. Three filters, all earned by measurement (see the module docstring):
    `mktemp` templates are not paths; a path the file itself creates or deletes is scratch
    rather than corpus; and a path that appears only inside an `echo`/`printf` argument is
    being DISPLAYED, not visited.

    THE PRINT FILTER APPLIES TO THE T248 RULE ONLY, NEVER TO THE LEGACY ONE. That asymmetry
    is deliberate and is what keeps the widening provably additive: a legacy match cannot be
    filtered away by anything added here, so no path that used to be flagged stops being
    flagged. Measured consequence of getting this wrong: t239's `51-run-r11-verbatim.sh`
    QUOTES r11's broken `cd /tmp/T138-merge ...` line inside an `echo` in order to explain the
    defect, and probes the same directory with `[ -d ... ]` in order to report it. Both are
    narration about a dead path, not an attempt to read one, and promoting that file from
    TIER2 to TIER1 on them would be this linter committing the error it exists to detect.
    """
    out = []
    cands = [(p, False) for p in RE_ABSPATH.findall(line)]
    for m in RE_ABSPATH_LOC.finditer(line):
        if re.search(r'\b(?:echo|printf)\b', line[:m.start()]):
            continue                          # displayed, not visited
        cands.append((m.group(1), True))
    for p, _t248 in cands:
        p = p.rstrip('"\'`);,.')
        if not p or p in out:
            continue
        if "XXX" in p:                       # a mktemp TEMPLATE is not a path
            continue
        if os.path.exists(p):
            continue
        if re.search(RE_OWNED_HEAD + re.escape(p), txt):   # the file owns it
            continue
        out.append(p)
    return out


viol = []
suppressed = []
inspected = 0
for f in files:
    if f == SELF:
        continue
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    if len(txt) > 4_000_000:
        continue
    lines = txt.splitlines()
    for i, l in enumerate(lines, 1):
        m = RE_SUPPRESS.search(l)
        if m:
            suppressed.append((f, i, m.group(1).strip()))
    code = [(i, l) for i, l in enumerate(lines, 1)
            if not l.lstrip().startswith("#") and not RE_SUPPRESS.search(l)]
    if not RE_REPOWIDE.search(txt):
        continue                                  # not a repo-wide search instrument
    inspected += 1
    v = []

    # C1 -- dead absolute path
    for i, l in code:
        dead = _dead_paths(l, txt)
        if dead:
            v.append(("C1", i, "dead absolute path: %s" % dead[0]))

    # C2a -- a failure arm that PRINTS
    for i, l in code:
        if RE_SWALLOW.search(l) and (RE_REPOWIDE.search(l) or re.search(r'\bcd\b|\bgrep\b|\bsed\b', l)):
            v.append(("C2", i, "failure arm PRINTS instead of exiting: %s" % l.strip()[:110]))

    # C2a-continued [T248] -- the SAME arm, with the `||` moved onto a backslash continuation.
    #
    # Found by red drive, shape R5. C2a reads PHYSICAL lines and demands that the search and
    # its `|| echo` share one, so `( cd "$WT" && git grep ... ) \` + `  || echo "(no hits)"`
    # slipped through a rule that already had both halves. Nothing subtle is wrong with C2a;
    # it was simply written against a specimen whose construct happened to fit on one line --
    # which is R4's lesson repeated, and the reason this pass reads LOGICAL lines everywhere.
    # Strictly ADDITIVE: it only reports where the physical-line pass reported nothing in the
    # same block, so no existing detection is renumbered or restated.
    _c2_lines = set(i for c, i, _ in v if c == "C2")
    for (a, b, txt_l) in _logical(lines):
        if b == a or not _is_code(txt_l):
            continue                                  # single-line blocks: C2a already saw them
        if not RE_SWALLOW.search(txt_l):
            continue
        if not (RE_REPOWIDE.search(txt_l) or re.search(r'\bcd\b|\bgrep\b|\bsed\b', txt_l)):
            continue
        if any(i in _c2_lines for i in range(a + 1, b + 2)):
            continue
        hit = next((k for k in range(a, b + 1) if RE_SWALLOW.search(lines[k])), b)
        v.append(("C2", hit + 1,
                  "failure arm PRINTS instead of exiting -- the arm is on a CONTINUATION of "
                  "the construct that begins at line %d: %s"
                  % (a + 1, lines[hit].strip()[:100])))

    # C2b [T248] -- an UNCONDITIONAL reassuring print after a swallowed `cd`.
    #
    # This is the shape the driver's red drive of T243 proved invisible, and it is the shape
    # of the SECOND confirmed live site. The reassurance is not an arm of anything; it is the
    # next line, and it runs whether or not the directory was ever entered.
    for (a, b, txt_l) in _logical(lines):
        if not _is_code(txt_l):
            continue
        if not RE_CD.search(txt_l) or RE_CD_FATAL.search(txt_l):
            continue                                  # fatal `cd` cannot leave a false claim
        seen = 0
        for k in range(b + 1, len(lines)):
            l = lines[k]
            if not _is_code(l):
                continue                              # blanks and comments do not break it
            is_print = bool(RE_UNCOND_PRINT.match(l))
            # The SEARCH ITSELF may sit between the `cd` and the sentence about it -- that is
            # r11-hygiene.sh's shape with the search moved off the continuation onto its own
            # line, and it was found by RED-DRIVING this rule on a shape it was not built
            # from (T248 shape R2). Anything that is neither the search nor narration breaks
            # the association, because past that point the claim is about something else.
            if not is_print and not RE_REPOWIDE.search(l):
                break
            seen += 1
            if seen > C2B_WINDOW:
                break
            if is_print and RE_REASSURE.search(l) and "||" not in l:
                v.append(("C2", k + 1,
                          "UNCONDITIONAL print CLAIMS A MEASUREMENT after a `cd` at line %d "
                          "whose failure is swallowed -- it runs whether or not that directory "
                          "was entered: %s" % (a + 1, l.strip()[:110])))
                break

    # C3/C4/C5 -- advisory properties
    if not RE_CORPUS_ASSERT.search(txt):
        v.append(("C3", 0, "no corpus-reachability assertion anywhere in the file"))
    if not RE_CALIB.search(txt):
        v.append(("C4", 0, "no calibration on a known positive (P-72)"))
    if not RE_ENGINE_DECL.search(txt):
        v.append(("C5", 0, "engine not declared (P-33/P-53)"))
    for i, l in code:
        if RE_ESCAPE_IN_ERE.search(l):
            v.append(("C5", i, "backslash-class under `git grep -E`, which reads it as a LITERAL "
                               "and returns zero SILENTLY: %s" % l.strip()[:90]))
    if v:
        viol.append((f, v))

def has(v, c):
    return any(x == c for x, _, _ in v)


lethal = [(f, v) for f, v in viol if has(v, "C1") and has(v, "C2")]
dormant = [(f, v) for f, v in viol if has(v, "C2") and not has(v, "C1")]
unrepro = [(f, v) for f, v in viol if has(v, "C1") and not has(v, "C2")]
fails = lethal + dormant

print("T238 FAIL-OPEN LINT")
print("commit    : %s" % HEAD)
print("corpus    : %d tracked .sh/.py; %d are repo-wide search instruments" % (len(files), inspected))
print("scope     : %s" % (", ".join(ONLY) if ONLY else "whole repository"))
print()

print("### TIER 1 — FAIL-OPEN, LIVE  (C1 dead path AND C2 reassuring failure arm) : %d" % len(lethal))
print("###   measured behaviour of this tier: exit 0, prints a negative, measured nothing")
for f, v in sorted(lethal):
    print("  %s" % f)
    for c, i, m in v:
        if c in ("C1", "C2"):
            print("      %s  :%s  %s" % (c, i, m))
print()

print("### TIER 2 — FAIL-OPEN-CAPABLE  (C2 only; corpus reachable TODAY) : %d" % len(dormant))
print("###   one deleted directory away from Tier 1")
for f, v in sorted(dormant):
    print("  %s" % f)
    for c, i, m in v:
        if c == "C2":
            print("      %s  :%s  %s" % (c, i, m))
print()

print("### TIER 3 — UNREPRODUCIBLE, but FAILS CLOSED  (C1 only) : %d" % len(unrepro))
print("###   safe to re-run -- it exits non-zero -- but its conclusion can never be re-checked")
for f, v in sorted(unrepro):
    for c, i, m in v:
        if c == "C1":
            print("  %-76s :%s  %s" % (f, i, m))
print()

print("### ADVISORY (C3 no corpus assertion / C4 no calibration / C5 engine undeclared)")
adv = {}
for f, v in viol:
    for c, i, m in v:
        if c in ("C3", "C4", "C5"):
            adv.setdefault(c, []).append(f)
for c in sorted(adv):
    print("  %s : %d instrument(s)" % (c, len(set(adv[c]))))
print()

if suppressed:
    print("### SUPPRESSIONS IN FORCE (every one is listed; they never go quiet) : %d" % len(suppressed))
    for f, i, why in suppressed:
        print("  %-70s :%s  %s" % (f, i, why))
    print()

# THE FRONTIER, IN A SHAPE A GATE CAN READ.  [T243 -- wiring, additive]
#
# conformance.sh compares this set against a pin held in conformance.sh, in BOTH
# directions, on every graded run. It is printed on stdout rather than read out
# of the JSON below so that the gate consumes the SAME BYTES a human reads, and
# so that a linter which died before finishing emits no frontier at all instead
# of a stale file that still parses.
for _t, _f in sorted([("TIER1", f) for f, _ in lethal] + [("TIER2", f) for f, _ in dormant]):
    print("FAILOPEN-FRONTIER %s %s" % (_t, _f))
print()

# THE JSON DESTINATION IS OVERRIDABLE.  [T243 -- wiring, additive]
#
# Default unchanged, so every T238 transcript re-runs identically. It has to be
# overridable because conformance.sh now runs this linter on EVERY graded run,
# and a harness that rewrites a tracked file each time it grades would dirty the
# working tree it is grading -- which is a defect of exactly the kind this
# program keeps finding, one level up from the one this linter detects.
JSON_OUT = os.environ.get("FAILOPEN_LINT_JSON") or \
    ".softhouse/capture/t238-failopen/evidence/lint.json"
json.dump({"lethal": [f for f, _ in lethal], "dormant": [f for f, _ in dormant],
           "unreproducible": [f for f, _ in unrepro],
           "suppressed": suppressed,
           "detail": [{"file": f, "violations": v} for f, v in viol]},
          open(JSON_OUT, "w"), indent=1)

if fails:
    print("LINT: FAIL — %d instrument(s) can emit a negative they did not measure "
          "(%d live, %d dormant)." % (len(fails), len(lethal), len(dormant)))
    sys.exit(1)
print("LINT: PASS — no instrument in scope can emit a negative it did not measure.")
sys.exit(0)
