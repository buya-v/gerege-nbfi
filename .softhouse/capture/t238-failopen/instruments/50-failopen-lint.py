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
  C6  CORPUS ENTRY IS FATAL       [T252] an instrument must not ENTER an absolute directory
                                   that does not exist and then carry on. Alone among these,
                                   C6 reads CONTROL FLOW and never words.

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

T252 -- A COUNT IS A CLAIM TOO, AND THE TIER THAT DECLARED SAFETY AND TESTED NOTHING
-------------------------------------------------------------------------------------
T248 reported a PROBABLE third live site and did not confirm it. It is confirmed. RUN, not
read: `.softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh` exits **0**, prints
`PROMOTED CELLS SWEPT: 0   NOT BYTE-PRESENT / ARITHMETIC FAIL: 0`, and reached no corpus at
all -- its `R=` worktree was pruned days ago, its `cd "$R"` at :24 runs under `set -u` with
no `-e` and no `||`, and its own P-72 calibration line printed an EMPTY count and did not
stop it (.softhouse/capture/t252-tier3/transcripts/10-verify-third-site.txt).

WHY THE OBVIOUS FIX IS THE WRONG ONE, MEASURED RATHER THAN ARGUED. T252's brief proposed a
NUMERIC-CLAIM detector: every widening so far keys on reassuring English, and `0` printed by
an instrument that never reached its corpus is indistinguishable from `0` measured honestly.
The observation is right. The implementation of it is inert. Fourteen count shapes were added
to RE_REASSURE and the linter re-run over the whole tree (transcripts/20-numeric-vocab-probe):

    frontier 10 -> 10.  GAINED 0.  LOST 0.  The confirmed site: STILL INVISIBLE.

It was not rejected for noise -- it produced none. It buys literally nothing, for two reasons
that are INDEPENDENT of each other, so neither rests on the other being right:
  (a) RE_UNCOND_PRINT is `^\s*(?:echo|printf)` -- SHELL ONLY. The false count is emitted by
      `print(...)` inside a `python3 - <<'PY'` heredoc. The line is never offered to any
      vocabulary, so no vocabulary can be widened enough to reach it. (17 shell prints, 12
      python prints in that one file -- both terms, P-67.)
  (b) C2B_WINDOW is 3 code lines. The `cd` is at :24 and the false count at :142 -- 110 code
      lines apart, 36x the window, with `python3 - "$R" <<'PY'` at :34 breaking the
      association long before it.
Widening the window to 110 lines would associate a `cd` with everything a script ever prints,
which is not a rule, and widening the print predicate to any language's print without an
association rule is worse. A vocabulary is the wrong AXIS, not the wrong wordlist.

  C6 -- CORPUS ENTRY IS NON-FATAL. The rule that does close it reads CONTROL FLOW and never
  words at all: a file that ENTERS an absolute directory that does not exist NOW -- `cd`,
  `pushd`, `git -C`, `--git-dir=`, `--work-tree=`, whether written as a literal or reached
  through a variable assigned a literal absolute path earlier in the same file -- and whose
  entry does not terminate it, is fail-open. Not "prints a reassuring sentence"; not "prints
  a suspicious number". EVERYTHING it prints after that line is printed about a directory it
  never entered, in whatever words, in whatever language, at whatever distance.

  Termination is ESTABLISHED, never assumed, by exactly two things, both checkable:
    * `errexit` in force at that line -- `set -e`, `set -euo pipefail`, `set -o errexit` --
      tracked forward through `set +e` so a disabled shell option cannot be read as a
      protection; or
    * a fatal arm ON the entry line: `|| exit`, `|| return`, `|| die`, `|| _sw_die`, `|| {`.
  Everything else is non-fatal and is flagged. The `XXX`-is-a-mktemp-template and the
  file-OWNS-the-path filters are inherited from C1 unchanged, so a `mkdir -p D && cd D` is
  scratch here exactly as it is there.

TIER 3'S LABEL SAID "FAILS CLOSED" AND NOTHING EVER CHECKED IT. [the P-45 shape, one level up]
The old header read: `TIER 3 -- UNREPRODUCIBLE, but FAILS CLOSED ... safe to re-run -- it
exits non-zero`. That is an assertion about runtime behaviour, made about every member of the
tier, by a classifier that never checked it for any file -- and for one member it was simply
FALSE, which is how this task started. A tier that DECLARES safety and TESTS nothing is a
fail-open wearing the word "closed", and it is the more dangerous kind because it is the
sentence a reviewer stops reading at.

Both halves of the remedy are applied, because either alone is weaker:
  * C6 makes part of the label EARN itself -- "no dead path is entered non-fatally" is now
    a checked property, and every TIER 3 row prints WHICH of the three checkable grounds it
    rests on (errexit / fatal-entry / no-dead-entry);
  * the label stops claiming the part that is still unchecked. C6 watches corpus ENTRY. It
    does not model every route to a false negative, so the header no longer says "fails
    closed" or "exits non-zero" about anything. An honest "termination not verified" is
    worth more than a false "fails closed" -- the weaker true statement over the stronger
    unverified one, which is this program's standing rule.
"""
import os
import re
import sys
import json
import tempfile
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
SEVERITY_FAIL = {"C2", "C6"}
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

# --- C6 [T252] --------------------------------------------------------------
# CORPUS ENTRY, and whether failing to make it stops the script.
#
# C1 asks "is this path dead?". C6 asks the question C1 never did: "and does the file NOTICE?"
# Those are different questions and the second one is the one TIER 3's old label answered
# without checking. Nothing below looks at a single word of output -- deliberately, because
# the site that motivated this rule prints its false claim as a COUNT, in python, 110 code
# lines downstream, and no vocabulary and no window reaches it (transcripts/20).
RE_ENTER = re.compile(
    r'(?:^|[;&|(]\s*|&&\s*|\bthen\s+|\bdo\s+)(cd|pushd)\s+([^\s;&|)]+)'
    r'|\b(git)\s+-C\s+([^\s;&|)]+)'
    r'|(--git-dir|--work-tree)=([^\s;&|)]+)')
# A literal absolute path assigned to a NAME. This is the hop the site needs: the dead path is
# declared at :11 and entered at :24 through `"$R"`, and a rule that only reads the entry line
# sees a variable and stops. Single-assignment, literal RHS, first wins -- deliberately the
# narrowest resolution that reaches the specimen, because a fuller shell evaluator inside a
# linter is a second thing that can be wrong.
RE_ASSIGN_ABS = re.compile(
    r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=["\']?(/[A-Za-z0-9._/-]+)')
RE_VAR_REF = re.compile(r'^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?(/[A-Za-z0-9._/-]*)?$')
# TERMINATION, ESTABLISHED RATHER THAN ASSUMED -- exactly two grounds, both checkable.
RE_FATAL_ARM = re.compile(r'\|\|\s*(?:exit|return|die|_sw_die|\{)')
RE_ERREXIT_ON = re.compile(r'^\s*set\s+(?:-[a-zA-Z]*e[a-zA-Z]*(?:\s|$)|-o\s+errexit\b)')
RE_ERREXIT_OFF = re.compile(r'^\s*set\s+(?:\+[a-zA-Z]*e[a-zA-Z]*(?:\s|$)|\+o\s+errexit\b)')

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


def _abs_assignments(code):
    """NAME -> literal absolute path, from single literal assignments. First wins.

    A name assigned twice is dropped rather than guessed at: if the linter cannot say WHICH
    literal is in force at the entry, it must not report a dead entry it has not established.
    """
    seen = {}
    dup = set()
    for _i, l in code:
        m = RE_ASSIGN_ABS.match(l)
        if not m:
            continue
        name, val = m.group(1), m.group(2).rstrip('"\'`);,.')
        if name in seen and seen[name] != val:
            dup.add(name)
        seen.setdefault(name, val)
    for name in dup:
        seen.pop(name, None)
    return seen


def _resolve_entry(tok, assigns):
    """`/lit`, `"$R"`, `$R`, `"${R}"`, `"$R/sub"` -> an absolute literal, or None."""
    t = tok.strip().strip('"\'').rstrip(';')
    if not t:
        return None
    if t.startswith("/"):
        return t
    m = RE_VAR_REF.match(t)
    if m and m.group(1) in assigns:
        return assigns[m.group(1)] + (m.group(2) or "")
    return None


def _errexit_at(code):
    """{line_no: bool} -- is errexit in force when this code line runs?

    Tracked FORWARD through `set +e`, because a shell option that was turned back off is not
    a protection and reading the file for the string `set -e` alone would call it one.
    """
    state = {}
    on = False
    for i, l in code:
        state[i] = on
        if RE_ERREXIT_ON.match(l):
            on = True
        elif RE_ERREXIT_OFF.match(l):
            on = False
    return state


def _dead_entries(code, txt, assigns, errexit, only_nonfatal=True):
    """[(line_no, verb, path, declared_at)] -- entries into a dead absolute dir that do NOT stop.

    Inherits C1's two measured filters unchanged: an `XXX` literal is a mktemp TEMPLATE, and a
    path the file itself creates or deletes is scratch rather than corpus -- so `mkdir -p D &&
    cd D` is exempt here for exactly the reason it is exempt there.
    """
    out = []
    decl = {}
    for i, l in code:
        m = RE_ASSIGN_ABS.match(l)
        if m and m.group(1) in assigns:
            decl.setdefault(m.group(1), i)
    for i, l in code:
        if only_nonfatal and (RE_FATAL_ARM.search(l) or errexit.get(i)):
            continue                              # the entry TERMINATES: established, not assumed
        for m in RE_ENTER.finditer(l):
            g = [x for x in m.groups() if x is not None]
            if len(g) != 2:
                continue
            verb, tok = g
            p = _resolve_entry(tok, assigns)
            if not p or "XXX" in p or os.path.exists(p):
                continue
            if re.search(RE_OWNED_HEAD + re.escape(p), txt):
                continue
            vm = RE_VAR_REF.match(tok.strip().strip('"\'').rstrip(';'))
            out.append((i, verb, p, decl.get(vm.group(1)) if vm else None))
    return out


viol = []
suppressed = []
T3_GROUND = {}
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

    # C6 [T252] -- ENTERS A DEAD DIRECTORY AND CARRIES ON.
    #
    # No vocabulary, no window, no print predicate. If the file enters a directory that is not
    # there and does not stop, then EVERY line it prints afterwards -- sentence, count, table,
    # empty section, shell or python -- is about a place it never went. Confirmed live on
    # rederive-provenance.sh: exit 0, `NOT BYTE-PRESENT / ARITHMETIC FAIL: 0`, corpus never
    # reached (transcripts/10-verify-third-site.txt).
    _assigns = _abs_assignments(code)
    _errex = _errexit_at(code)
    # THE GROUND ON WHICH A TIER 3 ROW WILL REST, recorded HERE where the evidence exists.
    # The old TIER 3 header asserted "fails closed / it exits non-zero" for every member and
    # nothing computed it. This is the computation, and it is reported per row.
    _all_entries = _dead_entries(code, txt, _assigns, _errex, only_nonfatal=False)
    if any(_errex.values()):
        T3_GROUND[f] = "errexit in force (`set -e`) at the dead-path lines"
    elif _all_entries:
        T3_GROUND[f] = ("every dead-path ENTRY terminates -- fatal arm (`|| exit`/`die`) "
                        "on line(s) %s" % ",".join(str(i) for i, _, _, _ in _all_entries))
    else:
        T3_GROUND[f] = ("no dead path is in a position that ENTERS it -- narration, a probe "
                        "list, or an env var, not a corpus this file reads")
    for i, verb, dp, decl in _dead_entries(code, txt, _assigns, _errex):
        where = (" (declared at line %d)" % decl) if decl else ""
        v.append(("C6", i,
                  "ENTERS a directory that does not exist and CARRIES ON -- no errexit in "
                  "force and no fatal arm, so everything printed after this line is printed "
                  "about a corpus never reached: `%s` -> %s%s" % (verb, dp, where)))

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
# TIER 1B [T252]. A file already on the frontier as TIER1/TIER2 stays where it is -- C6 is
# ADDITIVE evidence about it, never a reclassification -- so this tier is exactly the files
# C6 makes visible that nothing else did.
entering = [(f, v) for f, v in viol if has(v, "C6")
            and not (has(v, "C1") and has(v, "C2"))
            and not (has(v, "C2") and not has(v, "C1"))]
unrepro = [(f, v) for f, v in viol if has(v, "C1") and not has(v, "C2") and not has(v, "C6")]
fails = lethal + dormant + entering

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

print("### TIER 1B — ENTERS A CORPUS THAT IS NOT THERE AND CARRIES ON  (C6) : %d" % len(entering))
print("###   [T252] the fail-open whose false claim is a COUNT, not a sentence. This tier is")
print("###   found by CONTROL FLOW, not vocabulary: no output words are read at all, so the")
print("###   claim's distance, phrasing and even its LANGUAGE are irrelevant to it.")
for f, v in sorted(entering):
    print("  %s" % f)
    for c, i, m in v:
        if c == "C6":
            print("      %s  :%s  %s" % (c, i, m))
print()

# TIER 3, RELABELLED. [T252]
#
# It used to read "UNREPRODUCIBLE, but FAILS CLOSED ... safe to re-run -- it exits non-zero".
# That is a claim about runtime behaviour, asserted over every member of the tier, by a
# classifier that checked it for none of them -- and for one member it was FALSE. Half of it
# is now CHECKED (C6: no dead path is entered non-fatally); the other half is WITHDRAWN
# rather than restated, because this linter still does not model a file's exit code.
# BOTH TERMS (P-67): the files and the dead-path findings inside them are DIFFERENT numbers,
# which is why quoting either alone misleads. Measured at 2871f17, before C6: 5 files / 7
# findings (00-engines.sh alone carries three). After C6 moved the confirmed site out to
# TIER 1B: 4 files / 6 findings.
_t3_findings = sum(1 for _f, _v in unrepro for c, _i, _m in _v if c == "C1")
print("### TIER 3 — UNREPRODUCIBLE: dead path, no reassuring arm, no non-fatal dead ENTRY")
print("###   : %d file(s) / %d dead-path finding(s)" % (len(unrepro), _t3_findings))
print("###   WHAT IS CHECKED: the path is dead (C1); nothing here PRINTS reassurance (no C2);")
print("###   and no dead path is ENTERED without terminating (no C6). The bracket on each row")
print("###   names which of those grounds it actually rests on.")
print("###   WHAT IS **NOT** CHECKED, AND IS NO LONGER CLAIMED: that these files exit non-zero.")
print("###   This label read 'but FAILS CLOSED' until T252 and NOTHING verified it for any file,")
print("###   ever; for one member it was false. 'Termination not verified' is the weaker TRUE")
print("###   statement, and it replaces the stronger unverified one.")
for f, v in sorted(unrepro):
    print("  %s" % f)
    print("      GROUND: %s" % T3_GROUND.get(f, "NOT CLASSIFIED"))
    for c, i, m in v:
        if c == "C1":
            print("      %s  :%s  %s" % (c, i, m))
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
for _t, _f in sorted([("TIER1", f) for f, _ in lethal] + [("TIER2", f) for f, _ in dormant]
                     + [("TIER1B", f) for f, _ in entering]):
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

# AND THE DEFAULT NO LONGER DIRTIES THE TREE.  [T299 -- additive; exit codes unchanged]
#
# T243 made the destination overridable and diverted its OWN call site, and stopped there.
# That left the trap armed for every other caller: a bare `python3 50-failopen-lint.py`
# OVERWROTE the tracked file above -- measured at 39d2156 in a scratch clone as
# `838 insertions(+), 37 deletions(-)` on a tree that was clean before the run. T256 hit it
# by hand and reverted it by hand; its handoff's remedy was "anyone debugging that guard by
# hand should set FAILOPEN_LINT_JSON first".
#
# A remedy that consists of asking the next author to remember an environment variable is
# the shape this very file's docstring rules out sixty lines up, and it is P-45 -- "a
# test-only guard is not a guard ... verify the path that ACTUALLY EXECUTES calls it, not
# merely that a test does" -- read on the safety rather than on the check: a protection that
# only operates when the caller remembers to invoke it protects nothing. The path that
# actually executes for a human at a terminal is the BARE one, and the bare one was unsafe.
#
# So the file decides, not the caller: THIS INSTRUMENT NEVER WRITES OVER A GIT-TRACKED PATH,
# whoever asks for it. Not the default, and not an override aimed at a tracked file by
# mistake -- the class, not the instance. The request is honoured to a scratch file instead
# and the diversion is ANNOUNCED on stdout, so it can never happen silently, which is the
# half of the defect that mattered: evidence recording a run nobody meant to take.
#
# The default is deliberately LEFT POINTING AT THE TRACKED FILE. Repointing it at scratch
# would silently falsify conformance.sh's own comment at its call site -- "The linter's
# default destination is a TRACKED file, and a harness that rewrote a tracked file on every
# graded run would dirty the tree it is grading" -- which is a sentence in a file this task
# may not touch. The sentence stays true and its diversion stays necessary.
#
# FAIL-SAFE DIRECTION: if trackedness cannot be DETERMINED, the destination is treated as
# tracked and diverted. MEASURED exit codes of `git ls-files --error-unmatch --  <p>`, from
# this repository at 39d2156 with git 2.50.1:
#     tracked path inside the work tree   -> 0
#     untracked path inside the work tree -> 1
#     ANY path outside the work tree      -> 128, `fatal: ... is outside repository at ...`
# so 1 is the ONLY code that means "no", and every other code diverts (P-81's shape: a search
# exits 1 on no-match and >1 on ERROR, and an error is never an empty result).
#
# BUT 128 IS NOT AN UNKNOWN, AND TREATING IT AS ONE IS A DEFECT THIS DRIVE CAUGHT IN THIS
# FILE'S OWN FIRST DRAFT. The first version asked git about every destination, so the ordinary
# scratch path that conformance.sh and nine archived rigs supply -- which lives under TMPDIR,
# OUTSIDE the work tree -- came back 128 and was diverted, i.e. the caller's explicit choice
# was silently overridden and the JSON went somewhere else. ARM 2 of
# `.softhouse/capture/t299-namespace-and-default-safety/instruments/20-drive-destination-safety.sh`
# is the arm that failed and is the reason this paragraph exists.
#
# A path outside the work tree is therefore settled WITHOUT asking git, by containment, which
# is a POSITIVE determination rather than a guess: git cannot be tracking what is not in the
# work tree. Only paths that really are inside it are put to `ls-files`.
def _dest_is_tracked(p):
    try:
        root = os.path.realpath(ROOT)
        dest = os.path.realpath(os.path.join(root, p))
        inside = (dest != root and os.path.commonpath([root, dest]) == root)
    except (ValueError, OSError):
        return True
    if not inside:
        return False
    try:
        r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", dest], cwd=root,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return True
    if r.returncode == 1:
        return False
    return True


if _dest_is_tracked(JSON_OUT):
    _fd, _scratch = tempfile.mkstemp(prefix="failopen-lint-", suffix=".json")
    os.close(_fd)
    print("JSON-DESTINATION DIVERTED [T299]")
    print("  requested : %s" % JSON_OUT)
    print("  it is a GIT-TRACKED path, and this instrument does not write over committed")
    print("  evidence. Set FAILOPEN_LINT_JSON to a scratch path to choose your own.")
    print("  written to: %s" % _scratch)
    print()
    JSON_OUT = _scratch

json.dump({"lethal": [f for f, _ in lethal], "dormant": [f for f, _ in dormant],
           "entering": [f for f, _ in entering],
           "unreproducible": [f for f, _ in unrepro],
           "unreproducible_ground": {f: T3_GROUND.get(f, "NOT CLASSIFIED") for f, _ in unrepro},
           "suppressed": suppressed,
           "detail": [{"file": f, "violations": v} for f, v in viol]},
          open(JSON_OUT, "w"), indent=1)

if fails:
    print("LINT: FAIL — %d instrument(s) can emit a negative they did not measure "
          "(%d live, %d dormant, %d entering-a-corpus-that-is-not-there)."
          % (len(fails), len(lethal), len(dormant), len(entering)))
    sys.exit(1)
print("LINT: PASS — no instrument in scope can emit a negative it did not measure.")
sys.exit(0)
