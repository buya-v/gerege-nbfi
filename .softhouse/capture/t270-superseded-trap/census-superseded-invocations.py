#!/usr/bin/env python3
"""T270 -- WHICH SUPERSEDED ARTEFACTS ARE STILL EXECUTED?

  python3 census-superseded-invocations.py [--root DIR]

  exit 0  every superseded artefact named by every register is executed by nothing
  exit 1  FAIL   -- at least one superseded artefact is still INVOKED by a live script
  exit 2  REFUSE -- the census could not honestly reach a verdict (see REFUSALS below)

THE DEFECT THIS GENERALISES
---------------------------
`.softhouse/reviews/A2-11/run-all.sh:36` invoked `prove-mkreq7-guard-red.py` -- a guard
T164 had already replaced, whose float arm is a whole-file source grep its own target's
docstring satisfies -- so every run of that harness printed
`ok  it parses JSON numbers as Decimal` / `16 assertions, 0 failed` / `exit=0`.

T114 requires the BYTES of an evidence-producing script be preserved.  It does NOT require
the file keep being EXECUTED as though it still graded something.  Conflating the two is
what produces the trap, and *one instance of a class is rarely one instance*, so this
census asks the same question of every superseded artefact this program has declared.

  PRESERVED  the bytes are on disk, unchanged, and nothing runs them.       <- the goal
  TRAP       the bytes are on disk, unchanged, and something still runs them and reads
             the result as a verdict.                                       <- the defect

METHOD, IN THREE TERMS, EACH REPORTED SEPARATELY (P-67)
-------------------------------------------------------
TERM 1 -- THE REGISTERS.  Every file under the root whose basename matches /supersed/i.
  Found by walking the tree, not from a hand-written list, so a register nobody told this
  script about is still found.  Two formats are parsed, and BOTH are printed in full:
    * `A -> B` lines (the `SUPERSEDED.txt` shape; `#` starts a comment).
    * markdown table rows `| `path` | STATUS... |` where STATUS carries one of
      RETAINED / DO NOT RUN / SUPERSEDED / AUTHORITATIVE (the `*-SUPERSEDES.md` shape),
      plus `# T<n> -- `A` is SUPERSEDED by `B`` title lines.
  A register that parses to ZERO artefacts is a REFUSAL, not a clean result: this census
  must not be kept green by failing to read its own input (P-22).

TERM 2 -- THE CALLERS.  Every `.sh`/`.bash`/`.zsh`/`.py`/`.mk`/`Makefile` under the root,
  plus every file under `.softhouse/bin/` whatever its suffix.  Counted and printed.

TERM 3 -- THE OCCURRENCES, each classified into one of THREE verdicts.
  For each superseded artefact BASENAME, every caller is scanned for that literal token.
  Each occurrence is then graded:

    EXECUTED       the artefact is run IN PLACE, as the committed file.  This is the
                   finding.  Shell: the basename is the SCRIPT OPERAND of an interpreter
                   (`python3 …/X`, `sh "$DIR/X"`, `source X`, `exec X`) or is invoked
                   directly (`./…/X`) in command position -- being an ARGUMENT to some
                   other program does not count.  Python: an AST walk locates a
                   `subprocess.{run,call,check_call,check_output,Popen}` / `os.system` /
                   `os.popen` / `runpy.run_path` / `os.exec*` call and marks ONLY THAT
                   CALL'S OWN LINE, so a docstring that describes the invocation is not
                   mistaken for the invocation.
    EXECUTED-COPY  the caller copies the artefact into a throwaway sandbox first
                   (`tempfile.mkdtemp`/`mktemp -d` plus a `shutil.copy`/`cp` of that
                   basename) and runs the COPY.  This is NOT a finding: T175's register
                   words the obligation as "RETAINED, BYTE-IDENTICAL, DO NOT RUN FOR A NEW
                   ANSWER", and a red-drive that runs a scratch copy to DEMONSTRATE the
                   defect is the remedy those registers prescribe, not a violation of it.
                   Counted and printed separately so the distinction is auditable rather
                   than assumed.
    MENTIONED      anything else -- a comment, a docstring, a path in prose, a sha256
                   line, a register entry, a name passed as an argument to a lookup.

  MENTIONED is never a finding.  Preserving the bytes REQUIRES naming the file.
  THE SANDBOX TEST IS FILE-LEVEL, NOT CALL-LEVEL, and therefore UNDER-REPORTS the
  EXECUTED bucket: a caller that runs the artefact in place AND separately sandboxes a
  copy of it would have both occurrences graded EXECUTED-COPY.  Stated because it is a
  hole in the direction of a false green.

WHAT THIS CENSUS WOULD MISS -- stated, and partly MEASURED rather than merely admitted
--------------------------------------------------------------------------------------
The previous fire's T332 found EIGHT twin sites where five had been named, and two of
them were invisible to any symbolic grep.  So the misses are enumerated here, and the
class that can be measured IS measured, in TERM 4:

  M1  INDISCRIMINATE INVOCATION.  `for f in "$DIR"/*.py; do python3 "$f"; done`, or
      `find … -name '*.py' -exec python3 {} \;`, executes a superseded artefact WITHOUT
      EVER NAMING IT.  No token search can see this.  --> TERM 4 measures it: it finds
      every dynamic-invocation construct and reports which of them could reach a
      directory that contains a superseded artefact.  A hit there is a MAYBE, not a
      verdict, and is reported as such.
  M2  NAME BUILT AT RUNTIME.  `S=prove-mkreq7; python3 "$S-guard-red.py"`, or a name
      assembled from an argv element or a JSON config.  NOT MEASURED.
  M3  INDIRECTION THROUGH A NON-SCANNED FILE TYPE.  A `.json`/`.yaml`/`.md` task or
      pipeline definition naming the script, executed by a harness this census reads as
      a caller but whose argument it cannot resolve.  NOT MEASURED.
  M4  BASENAME COLLISION.  Two files with the same basename in different directories are
      not distinguished; a hit is reported against the basename.  This over-reports, and
      over-reporting is stated rather than silently deduplicated.
  M5  REGISTERS THAT DO NOT SAY "SUPERSED".  A file recording a retirement under some
      other word (`RETIRED`, `DEPRECATED`, `FROZEN`, a paragraph in a handoff) is not in
      TERM 1's population.  TERM 5 reports the names it did find for those words, as a
      pointer, without claiming to have parsed them.
  M6  THE REGISTERS' OWN COMPLETENESS.  This census grades what has been DECLARED
      superseded.  A script that is dead and was never declared is invisible to it. That
      is a different question and this is not an answer to it.
  M7  SELF-REFERENCE HAZARD, HIT AND FIXED DURING T270: this census's OWN transcript
      must not be named to match /supersed/i, or TERM 1 picks it up as a register, fails
      to parse it and REFUSES. That is the guard behaving correctly on an unreadable
      register-named file, so it is not special-cased; the transcript is called
      CENSUS-T270-STILL-EXECUTED.txt instead.

READ-ONLY.  Writes nothing but stdout.  Contacts no oracle.  No `grep`, no `rg` (P-75) --
the token search is Python `str.find` over the file's own decoded text.
"""
import ast
import os
import re
import sys

REGISTER_RE = re.compile(r"supersed", re.I)
CALLER_SUFFIXES = (".sh", ".bash", ".zsh", ".py", ".mk")
CALLER_NAMES = ("Makefile", "makefile", "GNUmakefile")
SCRIPTISH = (".py", ".sh", ".bash", ".zsh", ".pl", ".rb")

# Markdown status words that mean "this row names a superseded / retained artefact".
MD_STATUS = ("RETAINED", "DO NOT RUN", "SUPERSEDED", "AUTHORITATIVE")

# P-48 rule 3, the same shape census-json-float-siblings.py uses: candidates are found
# MECHANICALLY, and a candidate the parser cannot read is HAND-READ and DECLARED here --
# never silently skipped. A register that parses to 0 entries and is not declared here is
# a REFUSAL. Each declaration states who read it and what it names, so the next reader can
# check the reading rather than inherit it.
DECLARED_REGISTER_READS = {
    "capture/t284-schema2-callsites/SUPERSEDES.md": (
        "prose decision record, not a `A -> B` register and not a status table: its table "
        "columns are (site | committed files it produced | which of them are the output of "
        "the broken call), so no MD_STATUS word appears. HAND-READ BY T270 at "
        "SUPERSEDES.md:30-32 and :172-179.",
        [("t250-tenant-attestation/instruments/30-redB-mismatch-detected.sh",
          "t284-schema2-callsites/instruments/20-site1-schema1-replay.sh"),
         ("reviews/t261-tenant-attestation/instruments/t261-redB-attack.sh",
          "t284-schema2-callsites/successors/t284-redB-attack-v2.sh"),
         ("reviews/t261-tenant-attestation/instruments/t261-redC-wrap.sh",
          "t284-schema2-callsites/successors/t284-redC-residual-v2.sh")],
    ),
}

# --- shell: the basename must be the SCRIPT OPERAND, not merely somewhere on the line.
# `%s` is filled with the escaped basename.
_CMD_START = r"(?:^|[;&|(`{]|\$\(|&&|\|\||\bthen\b|\bdo\b|\belse\b|\btime\b)\s*(?:exec\s+)?"
_PATH_PREFIX = r"(?:[\w.$@{}/-]*/)?"          # $DIR/  ./  ../x/  a/b/  or nothing
SH_EXEC = (_CMD_START + r"(?:python3|python|bash|sh|zsh|ksh|source|\.)\s+"
           r"(?:-[A-Za-z]+\s+)*[\"']?" + _PATH_PREFIX + r"%s[\"']?(?=$|[\s\"'`);&|])")
SH_DIRECT = (_CMD_START + r"[\"']?(?:\.{1,2}|\$\{?\w+\}?)/" + _PATH_PREFIX +
             r"%s[\"']?(?=$|[\s\"'`);&|])")

PY_RUNNERS = {"run", "call", "check_call", "check_output", "Popen", "system", "popen",
              "run_path", "execv", "execvp", "execl", "spawnv", "spawnl"}
# A caller that builds a throwaway sandbox AND copies the artefact into it is running a
# COPY, which the supersession registers explicitly permit ("DO NOT RUN FOR A NEW ANSWER").
PY_SANDBOX = ("tempfile.mkdtemp", "tempfile.mkstemp", "TemporaryDirectory")
SH_SANDBOX = ("mktemp -d", "mktemp -dt", "$(mktemp")

DYNAMIC_RE = [
    (re.compile(r"for\s+\w+\s+in\s+[^\n;]*\*\.(py|sh|bash|zsh)"), "shell glob loop"),
    (re.compile(r"find\s[^\n]*-exec\s"), "find -exec"),
    (re.compile(r"find\s[^\n]*\|\s*(?:xargs|while)"), "find | xargs/while"),
    (re.compile(r"(?:python3?|bash|sh|zsh)\s+\"?\$\{?\w+\}?\"?"), "interpreter on a variable"),
    (re.compile(r"glob\.glob\(|Path\([^\n]*\)\.glob\(|os\.listdir\("), "python glob/listdir"),
]

REFUSALS = []
FINDINGS = []


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in filenames:
            yield os.path.join(dirpath, fn)


def read(path):
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", "replace")
    except OSError:
        return None


# ---------------------------------------------------------------- TERM 1: the registers
def parse_arrow(text):
    """`A -> B` lines, `#` starts a comment. The SUPERSEDED.txt shape."""
    out = []
    for raw in text.split("\n"):
        line = raw.split("#")[0].strip()
        if not line or "->" not in line:
            continue
        parts = [x.strip() for x in line.split("->")]
        if len(parts) == 2 and parts[0] and parts[1]:
            out.append((parts[0], parts[1], "arrow"))
    return out


def parse_markdown(text):
    """Table rows and `is SUPERSEDED by` title lines. The *-SUPERSEDES.md shape."""
    out = []
    for raw in text.split("\n"):
        line = raw.strip()
        m = re.search(r"`([^`]+)`\s+is\s+SUPERSEDED\s+by\s+`([^`]+)`", line, re.I)
        if m:
            out.append((m.group(1), m.group(2), "md-title"))
            continue
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        m = re.match(r"^\**`([^`]+)`\**$", cells[0])
        if not m:
            continue
        status = " ".join(cells[1:]).upper()
        if any(w in status for w in MD_STATUS):
            authoritative = "AUTHORITATIVE" in status
            out.append((m.group(1), "(authoritative)" if authoritative else "(see register)",
                        "md-row-authoritative" if authoritative else "md-row"))
    return out


def collect_registers(root):
    regs = []
    for p in walk(root):
        base = os.path.basename(p)
        if not REGISTER_RE.search(base):
            continue
        if os.path.splitext(base)[1] in (".py", ".sh", ".pyc"):
            continue          # an instrument ABOUT supersession is not a register
        text = read(p)
        if text is None:
            REFUSALS.append("cannot read candidate register %s" % p)
            continue
        entries = parse_arrow(text) + parse_markdown(text)
        regs.append((p, entries))
    return regs


# ---------------------------------------------------------------- TERM 3: classification
def spawn_selector(tree):
    """(module aliases, bare names) that actually reach a process spawn IN THIS FILE.

    Resolved from the file's OWN imports (P-76: check the selector before the condition).
    A bare `run(...)` is NOT a spawn unless the file did `from subprocess import run` --
    without this, every local helper named `run` is graded as a subprocess call, which is
    the shape that produced 4 false findings on the first pass of this census.
    """
    mods, bare = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] in ("subprocess", "os", "runpy"):
                    mods.add(a.asname or a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module in ("subprocess", "os", "runpy"):
            for a in n.names:
                if a.name in PY_RUNNERS:
                    bare.add(a.asname or a.name)
    return mods, bare


SELECTOR_SELFTEST = '''\
"""decoy 1: subprocess.run("victim.py") named in a DOCSTRING."""
import subprocess
import os
from subprocess import check_output
# decoy 2: subprocess.run("victim.py") in a COMMENT
DECOY3 = "subprocess.run(\\'victim.py\\')"
def run(d, script):        # decoy 4: a LOCAL helper called run
    return d + script
run("x", "victim.py")
subprocess.run(["python3", "victim.py"])
os.system("python3 victim.py")
check_output(["sh", "victim.py"])
'''


def py_exec_lines(text, path):
    """{basename: {lineno, ...}} -- ONLY the lines of real process-spawning calls.

    Marking the call's own line, rather than every line that mentions the basename, is
    what keeps a docstring describing an invocation from being graded as one.
    """
    found = {}
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as e:
        REFUSALS.append("%s will not parse (%s) -- a caller the census cannot read is not "
                        "a caller it may skip" % (path, e))
        return found
    mods, bare = spawn_selector(tree)
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Attribute) and f.attr in PY_RUNNERS:
            base = f.value
            while isinstance(base, ast.Attribute):
                base = base.value
            if not (isinstance(base, ast.Name) and base.id in mods):
                continue
        elif isinstance(f, ast.Name) and f.id in bare:
            pass
        else:
            continue
        lines = {n.lineno}
        for sub in ast.walk(n):
            lines.add(getattr(sub, "lineno", n.lineno))
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value:
                v = sub.value
                for tok in [v] + v.replace("'", " ").replace('"', " ").split():
                    b = os.path.basename(tok)
                    if b:
                        found.setdefault(b, set()).update(lines)
    return found


def selector_selftest():
    """The selector must find the 3 real spawns and none of the 4 decoys, or REFUSE.

    A selector that has stopped selecting produces a clean-looking census that is a
    statement about the search, not about the tree (P-66/P-70). Nil coverage is an error.
    """
    saved = list(REFUSALS)
    found = py_exec_lines(SELECTOR_SELFTEST, "<selector-selftest>")
    del REFUSALS[:]
    REFUSALS.extend(saved)
    lines = sorted(found.get("victim.py", set()))
    want = [10, 11, 12]          # the three real spawns
    decoys = [1, 5, 6, 9]        # docstring, comment, string literal, LOCAL `run` helper
    if lines != want:
        raise SystemExit("SELECTOR SELF-TEST FAILED: expected spawns on lines %s, found "
                         "%s. Refusing to run a census on a selector that does not "
                         "select." % (want, lines))
    if set(lines) & set(decoys):
        raise SystemExit("SELECTOR SELF-TEST FAILED: a decoy line %s was graded as a "
                         "spawn." % sorted(set(lines) & set(decoys)))
    return len(want), len(decoys)


def sandboxes(text, is_py, basename):
    """True if this caller copies `basename` into a throwaway dir before running it."""
    makers = PY_SANDBOX if is_py else SH_SANDBOX
    if not any(m in text for m in makers):
        return False
    for line in text.split("\n"):
        if basename not in line:
            continue
        if is_py and ("shutil.copy" in line or "shutil.copyfile" in line):
            return True
        if not is_py and re.search(r"\bcp\b|\binstall\b", line):
            return True
    return False


def classify(path, text, basename, py_lines):
    """[(lineno, verdict, line)] for every occurrence of `basename` in this caller."""
    hits = []
    esc = re.escape(basename)
    sh_exec = re.compile(SH_EXEC % esc)
    sh_direct = re.compile(SH_DIRECT % esc)
    is_py = path.endswith(".py")
    sandboxed = sandboxes(text, is_py, basename)
    exec_verdict = "EXEC-COPY" if sandboxed else "EXECUTED"
    exec_lines = py_lines.get(basename, set())
    for i, line in enumerate(text.split("\n"), 1):
        if basename not in line:
            continue
        stripped = line.strip()
        if is_py:
            verdict = exec_verdict if i in exec_lines else "MENTIONED"
        else:
            if stripped.startswith("#"):
                verdict = "MENTIONED"
            elif sh_exec.search(line) or sh_direct.search(line):
                verdict = exec_verdict
            else:
                verdict = "MENTIONED"
        hits.append((i, verdict, stripped[:150]))
    return hits


def main(argv):
    default_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "..", ".."))
    root = default_root
    if len(argv) >= 3 and argv[1] == "--root":
        root = os.path.abspath(argv[2])
    elif len(argv) > 1:
        sys.stderr.write(__doc__)
        return 2
    scratch_root = root != default_root

    print("=" * 78)
    print("T270 -- census: which SUPERSEDED artefacts are still EXECUTED?")
    print("=" * 78)
    print("ROOT: %s" % root)
    print()

    n_real, n_decoy = selector_selftest()
    print("SELECTOR SELF-TEST: %d synthetic process spawns found, %d decoys rejected"
          % (n_real, n_decoy))
    print("  (the token in a docstring, a comment, a string literal, and as an argument to")
    print("   a LOCAL helper function named `run` -- all four invisible to the selector)")
    print()

    # ---- TERM 1
    registers = collect_registers(root)
    print("TERM 1 -- SUPERSESSION REGISTERS FOUND BY WALKING THE TREE (basename =~ /supersed/i)")
    if not registers:
        REFUSALS.append("0 supersession registers found under %s. A census that read no "
                        "register cannot report a clean result (P-22)." % root)
    frozen = {}          # basename -> [(register, original-as-written, replacement, shape)]
    declared_used = []
    for p, entries in registers:
        rel = os.path.relpath(p, root)
        decl = DECLARED_REGISTER_READS.get(rel)
        print("  %-72s %d entr(ies)%s"
              % (rel, len(entries), "  [+ HAND-READ]" if decl else ""))
        if not entries and not decl:
            REFUSALS.append("%s matched the register name pattern but parsed to 0 "
                            "entries and is not declared in DECLARED_REGISTER_READS -- "
                            "either the parser does not understand its format or it is "
                            "not a register. Either way this is an ERROR, not a clean "
                            "result." % rel)
        for orig, repl, shape in entries:
            if shape == "md-row-authoritative":
                continue        # the SUCCESSOR, not a superseded artefact
            frozen.setdefault(os.path.basename(orig), []).append((rel, orig, repl, shape))
        if decl:
            why, pairs = decl
            declared_used.append((rel, why, pairs))
            for orig, repl in pairs:
                frozen.setdefault(os.path.basename(orig), []).append(
                    (rel, orig, repl, "hand-read"))
    print()

    print("REGISTERS THE PARSER CANNOT READ, HAND-READ AND DECLARED (P-48 rule 3) -- %d"
          % len(declared_used))
    if not declared_used:
        print("  (none)")
    for rel, why, pairs in declared_used:
        print("  %s" % rel)
        print("      why: %s" % why)
        for orig, repl in pairs:
            print("      names: %s -> %s" % (orig, repl))
    # STALE HAND-READING IS AN ERROR -- but only against the tree the declarations are
    # written for. Under `--root <scratch>` (the red-drive) they are inapplicable by
    # construction, and refusing there would make every red arm exit 2 for the wrong
    # reason. The scope of the check is therefore stated rather than assumed.
    stale_decl = sorted(set(DECLARED_REGISTER_READS) - {r for r, _w, _p in declared_used})
    if stale_decl and not scratch_root:
        REFUSALS.append("DECLARED_REGISTER_READS names %s, which is not in the register "
                        "population -- a stale hand-reading is an ERROR, not a skip: "
                        "remove it or fix the path." % stale_decl)
    elif stale_decl:
        print("  (%d declaration(s) inapplicable under --root: %s. The staleness check is "
              "scoped to the default root.)" % (len(stale_decl), stale_decl))
    print()

    print("SUPERSEDED ARTEFACTS DECLARED (%d distinct basename(s)) -- every one printed"
          % len(frozen))
    for b in sorted(frozen):
        for rel, orig, repl, shape in frozen[b]:
            print("  %-34s <- %-14s %s -> %s" % (b, shape, orig, repl))
    print()
    if not frozen:
        REFUSALS.append("0 superseded artefacts parsed out of %d register(s)."
                        % len(registers))

    # ---- TERM 2
    callers = []
    for p in walk(root):
        base = os.path.basename(p)
        if base.endswith(CALLER_SUFFIXES) or base in CALLER_NAMES \
                or os.sep + ".softhouse" + os.sep + "bin" + os.sep in p:
            callers.append(p)
    callers.sort()
    by_suffix = {}
    for p in callers:
        by_suffix[os.path.splitext(p)[1] or "(none)"] = \
            by_suffix.get(os.path.splitext(p)[1] or "(none)", 0) + 1
    print("TERM 2 -- CALLER POPULATION: %d file(s)" % len(callers))
    for k in sorted(by_suffix):
        print("  %-10s %d" % (k, by_suffix[k]))
    print()
    if not callers:
        REFUSALS.append("0 caller files found -- the census inspected nothing.")

    # ---- TERM 3
    print("TERM 3 -- EVERY OCCURRENCE OF A SUPERSEDED ARTEFACT IN A CALLER, GRADED")
    print("  (MENTIONED is never a finding: preserving the bytes requires naming the file)")
    print()
    n_exec = n_copy = n_ment = 0
    per_artefact = {}
    for p in callers:
        text = read(p)
        if text is None:
            REFUSALS.append("cannot read caller %s" % p)
            continue
        rel = os.path.relpath(p, root)
        py_lines = py_exec_lines(text, rel) if p.endswith(".py") else {}
        for b in sorted(frozen):
            if b not in text:
                continue
            if os.path.basename(p) == b:
                continue        # a file is not its own caller
            for lineno, verdict, line in classify(rel, text, b, py_lines):
                per_artefact.setdefault(b, []).append((rel, lineno, verdict, line))
                if verdict == "EXECUTED":
                    n_exec += 1
                    FINDINGS.append("%s:%d EXECUTES the superseded %s IN PLACE\n        %s"
                                    % (rel, lineno, b, line))
                elif verdict == "EXEC-COPY":
                    n_copy += 1
                else:
                    n_ment += 1

    for b in sorted(frozen):
        rows = per_artefact.get(b, [])
        ex = [r for r in rows if r[2] == "EXECUTED"]
        cp = [r for r in rows if r[2] == "EXEC-COPY"]
        print("  %s" % b)
        print("      status: %s"
              % ("*** STILL EXECUTED IN PLACE -- TRAP ***" if ex
                 else ("PRESERVED (run only as a sandbox COPY)" if cp
                       else "PRESERVED, not executed")))
        print("      %d executed-in-place, %d executed-as-copy, %d mentioned, across %d "
              "caller file(s)" % (len(ex), len(cp), len(rows) - len(ex) - len(cp),
                                  len({r[0] for r in rows})))
        for rel, lineno, verdict, line in rows:
            if verdict in ("EXECUTED", "EXEC-COPY"):
                print("      %-9s %s:%d" % (verdict, rel, lineno))
                print("                %s" % line)
        ment_files = sorted({r[0] for r in rows if r[2] == "MENTIONED"})
        if ment_files:
            print("      mentioned in: %s" % ", ".join(ment_files))
    print()
    print("  TOTALS: %d EXECUTED-IN-PLACE, %d EXECUTED-AS-COPY, %d MENTIONED, over %d "
          "artefact(s) and %d caller(s)." % (n_exec, n_copy, n_ment, len(frozen),
                                             len(callers)))
    print()

    # ---- TERM 4: what a symbolic search cannot see, measured as far as it can be
    print("TERM 4 -- INDISCRIMINATE INVOCATION (miss M1), MEASURED NOT MERELY ADMITTED")
    print("  A loop or a `find -exec` runs a superseded artefact WITHOUT NAMING IT, so no")
    print("  token search above can see it. Each construct below is reported with whether")
    print("  its own directory holds a superseded artefact. A hit is a MAYBE -- this census")
    print("  does not execute anything to find out.")
    frozen_dirs = {}
    for p in walk(root):
        b = os.path.basename(p)
        if b in frozen:
            frozen_dirs.setdefault(os.path.dirname(os.path.relpath(p, root)), set()).add(b)
    maybe = []
    dyn_total = 0
    for p in callers:
        if not p.endswith(SCRIPTISH):
            continue
        text = read(p)
        if text is None:
            continue
        rel = os.path.relpath(p, root)
        d = os.path.dirname(rel)
        for i, line in enumerate(text.split("\n"), 1):
            if line.strip().startswith("#"):
                continue
            for rx, why in DYNAMIC_RE:
                if rx.search(line):
                    dyn_total += 1
                    if d in frozen_dirs:
                        maybe.append((rel, i, why, sorted(frozen_dirs[d]), line.strip()[:120]))
                    break
    print("  dynamic-invocation constructs found in callers ......... %d" % dyn_total)
    print("  ... of which sit in a directory holding a superseded file %d" % len(maybe))
    for rel, i, why, arts, line in maybe:
        print("      MAYBE  %s:%d  (%s)  could reach: %s" % (rel, i, why, ", ".join(arts)))
        print("             %s" % line)
    if not maybe:
        print("      (none)")
    print()

    # ---- TERM 5: registers this census's own name pattern cannot see
    print("TERM 5 -- POINTER ONLY: files naming a retirement WITHOUT the word 'supersed'")
    print("  (miss M5. These are NOT parsed and NOT graded; they are printed so the next")
    print("  reader knows where else to look.)")
    other = []
    for p in walk(root):
        b = os.path.basename(p)
        if REGISTER_RE.search(b):
            continue
        if re.search(r"(?i)\b(RETIRED|DEPRECATED|FROZEN|OBSOLETE)\b", b) or \
           re.search(r"(?i)(RETIRED|DEPRECATED|FROZEN|OBSOLETE)", b):
            other.append(os.path.relpath(p, root))
    for o in sorted(other):
        print("      %s" % o)
    if not other:
        print("      (none found by basename)")
    print()

    # ---- verdict
    print("MISSES, RESTATED AT THE VERDICT SO THIS IS NOT READ AS EXHAUSTIVE (P-26/P-66):")
    print("  M1 indiscriminate invocation ....... partly measured, TERM 4")
    print("  M2 name built at runtime ........... NOT MEASURED")
    print("  M3 indirection via .json/.yaml/.md . NOT MEASURED")
    print("  M4 basename collision .............. over-reports; not deduplicated")
    print("  M5 registers not named 'supersed' .. pointer only, TERM 5")
    print("  M6 dead-but-never-declared scripts . a DIFFERENT question; not answered here")
    print("  M7 this transcript must not be named /supersed/i or TERM 1 refuses on it")
    print()

    # FINDINGS ARE PRINTED EVEN WHEN THE CENSUS REFUSES. A refusal says "there is a hole
    # in my coverage", not "what I did measure is void" -- collapsing the two would let one
    # unreadable register suppress every real finding, which is the fail-open shape this
    # whole task is about.
    if FINDINGS:
        print("FAIL: %d live in-place invocation(s) of a superseded artefact."
              % len(FINDINGS), file=sys.stderr)
        for f in FINDINGS:
            print("  * %s" % f, file=sys.stderr)
        print("\nA superseded artefact that still runs -- and, if it is a guard, still "
              "prints PASS -- is not preserved evidence, it is a trap. T114 binds the "
              "BYTES; it does not require the file keep being EXECUTED. Preserve the "
              "bytes; stop the execution.", file=sys.stderr)

    if REFUSALS:
        print("\nREFUSING TO REACH A VERDICT -- %d coverage problem(s). The findings above "
              "(if any) still stand; this says the census cannot claim to be COMPLETE:"
              % len(REFUSALS), file=sys.stderr)
        for r in REFUSALS:
            print("  * %s" % r, file=sys.stderr)
        return 2
    if FINDINGS:
        return 1
    print("PASS -- %d superseded artefact(s) declared across %d register(s); %d caller(s) "
          "inspected; 0 of them execute a superseded artefact IN PLACE. %d run a sandbox "
          "COPY (permitted) and %d MENTION one, which is what preservation looks like."
          % (len(frozen), len(registers), len(callers), n_copy, n_ment))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
