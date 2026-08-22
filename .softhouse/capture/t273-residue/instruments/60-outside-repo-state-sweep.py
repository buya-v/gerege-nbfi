#!/usr/bin/env python3
"""T273 (4) — SWEEP FOR THE CLASS: what else can a graded run read from outside the repo?

The driver's instruction was "enumerate every other instrument whose behaviour depends on
state outside the repo — /tmp, $HOME, an env var, a previously-run sibling. State BOTH
TERMS (P-67) and where you looked (P-66/P-70). The driver expects this is not the only one."
It is not. This instrument measures the population; it decides nothing and repairs nothing.

WHERE IT LOOKED, stated before any count, because "not found" is a statement about the
search and never about the world:
  * CORPUS: every file `git ls-files` reports whose name ends .sh or .py, in this work
    tree. That is the same corpus the fail-open linter uses.
  * NOT LOOKED AT, and therefore claimed about by NOTHING below: Go sources under nexus/,
    Markdown, JSON, the vector store, `.claude/`, git hooks, the user's shell profile
    (which `bash` sources before conformance.sh's first line runs), the Fineract reference
    instance's own container state, and anything not tracked by git.
  * NOT DECIDABLE HERE: whether a given reference actually changes a graded VERDICT. Only
    the sites on the BAR's execution path can, and that path is reported separately below.

BOTH TERMS (P-67): every class reports the number of sites AND, where the reference is a
filesystem path, how many of those paths exist on THIS host at THIS moment. A site whose
path exists today and is absent tomorrow is the whole defect; reporting only one of the
two numbers would hide exactly the thing that bit this program.

ENGINE DECLARATION (P-33/P-53/P-75): `git ls-files` for the corpus and Python `re` for
every pattern. No bare `grep`, no `rg`, no shell globbing.
"""
import os
import re
import subprocess
import sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("T273 SWEEP ABORT (2): not inside a git work tree; the corpus is unreachable.")
    sys.exit(2)
os.chdir(ROOT)

files = [f for f in subprocess.run(["git", "ls-files"], capture_output=True, text=True)
         .stdout.split("\n") if f.endswith((".sh", ".py"))]
if not files:
    print("T273 SWEEP ABORT (2): zero tracked .sh/.py files. A sweep over nothing proves "
          "nothing (P-35).")
    sys.exit(2)

TEXT = {}
for f in files:
    try:
        TEXT[f] = open(f, encoding="utf-8", errors="replace").read()
    except OSError:
        pass

RE_REPOWIDE = re.compile(
    r'(git\s+(?:-[A-Za-z]\s+\S+\s+|--[A-Za-z-]+=\S+\s+|-[A-Za-z]+\s+)*(?:grep|ls-files)\b'
    r'|grep\s+-[a-zA-Z]*[rR]\b)')
LINT_CORPUS = set(f for f, t in TEXT.items() if RE_REPOWIDE.search(t))

CLASSES = [
    ("C-TMP        literal shared-temp path, ANY position",
     re.compile(r'/(?:tmp|private/tmp|var/tmp)/[A-Za-z0-9._/-]+'), True),
    ("C-TMP-ASSIGN the guarded shape: NAME=<shared-temp path>",
     re.compile(r'^[ \t]*(?:export[ \t]+)?[A-Za-z_][A-Za-z0-9_]*=["\']?'
                r'(/(?:tmp|private/tmp|var/tmp)/[A-Za-z0-9._/-]+)', re.M), True),
    ("C-WORKTREE   a sibling agent worktree, by absolute path",
     re.compile(r'/Users/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+/\.claude/worktrees/[A-Za-z0-9._-]+'), True),
    ("C-USERHOME   an absolute path under /Users (this Mac's home root)",
     re.compile(r'/Users/[A-Za-z0-9._/-]{6,}'), True),
    ("C-HOME       $HOME, ~/ or expanduser",
     re.compile(r'\$\{?HOME\b|(?:^|[\s"\'=:(])~/|expanduser\('), False),
    ("C-ENVREAD    a shell/python read of an environment variable",
     re.compile(r'\$\{[A-Za-z_][A-Za-z0-9_]*[:\-}]|os\.environ|os\.getenv\('), False),
]

print("### T273 — OUTSIDE-REPO STATE SWEEP")
print("  tree                 : %s" % ROOT)
print("  HEAD                 : %s" % subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip())
print("  corpus               : %d tracked .sh/.py" % len(files))
print("  of which the fail-open linter classifies : %d" % len(LINT_CORPUS))
print()

print("### THE POPULATION, BY CLASS — BOTH TERMS")
print("  %-58s %6s %6s %8s %8s" % ("CLASS", "FILES", "SITES", "IN-LINT", "EXIST-NOW"))
for name, rx, is_path in CLASSES:
    hit_files, sites, in_lint, exists = set(), 0, 0, 0
    for f, t in TEXT.items():
        n = 0
        for m in rx.finditer(t):
            p = m.group(1) if (rx.groups and m.lastindex) else m.group(0)
            if is_path and "XXX" in p:
                continue          # a mktemp TEMPLATE is not a path
            n += 1
            if is_path and os.path.exists(p.rstrip('"\'`);,.')):
                exists += 1
        if n:
            hit_files.add(f)
            sites += n
            if f in LINT_CORPUS:
                in_lint += n
    print("  %-58s %6d %6d %8d %8s"
          % (name, len(hit_files), sites, in_lint, (exists if is_path else "n/a")))
print()
print("  EXIST-NOW is the second term. For C-TMP it is the number of shared-temp paths a")
print("  tracked instrument names that HAPPEN TO BE ON THIS HOST RIGHT NOW. Every one of")
print("  them is a fact no commit records and macOS deletes on reboot.")
print()

# --- WHAT THE BAR ACTUALLY EXECUTES ----------------------------------------
# Only a site the graded run REACHES can change a graded verdict. Everything above is
# population; this is exposure.
print("### THE BAR'S OWN EXECUTION PATH — the only sites that can change a VERDICT")
conf = TEXT.get(".softhouse/conformance.sh", "")
if not conf:
    print("  .softhouse/conformance.sh is not in the corpus. Nothing below is admissible.")
    sys.exit(2)
# EVERY repo-relative .sh/.py path conformance.sh NAMES, on a code line, whatever verb
# reaches it. Keying on the VERB (`bash …`, `python3 …`) was the first draft and it was
# too narrow: the two capture-rig guards are invoked as `python3 "$script"` after
# `script="$REPO_ROOT/.softhouse/…"` three lines earlier, so a verb-keyed search reported
# 3 files when the true figure is larger. Keying on the PATH finds them regardless.
RE_PATH = re.compile(r'\$(?:REPO_ROOT|SCRIPT_DIR)"?(/[A-Za-z0-9._/-]+\.(?:sh|py))')
code = "\n".join(l for l in conf.splitlines() if not l.lstrip().startswith("#"))
invoked = sorted(set(m.group(1).lstrip("/") for m in RE_PATH.finditer(code)))
# NAMED BY A VARIABLE AND THEREFORE INVISIBLE TO THE PATTERN ABOVE. conformance.sh:943
# reads `local script="$REPO_ROOT/.softhouse/capture/lib/$1"`, so the two capture-rig
# guards are reached through a parameter and no path-literal search can find them. They
# are added here BY NAME, from their own call sites, rather than left to be missed —
# an incomplete list that looks complete is the defect this whole task is about.
for extra in (".softhouse/capture/lib/check_wire_float_roundtrip.py",
              ".softhouse/capture/lib/check_no_narrow_catch.py"):
    if extra not in invoked:
        invoked.append(extra)
invoked = sorted(invoked)
if not invoked:
    print("  the invocation pattern matched NOTHING. That is a broken search, not an empty")
    print("  execution path — treat this section as UNMEASURED (P-35).")
else:
    for p in invoked:
        t = TEXT.get(p)
        if t is None:
            state = "not a tracked .sh/.py in this corpus (or absent)"
        else:
            # CODE LINES ONLY here. A class that fires on a COMMENT is narration about
            # the shape, not the shape, and this section is about what a graded run can
            # READ — reporting the two together is how a prose mention gets counted as
            # an exposure.
            tc = "\n".join(l for l in t.splitlines() if not l.lstrip().startswith("#"))
            marks = []
            for name, rx, is_path in CLASSES:
                if rx.search(tc):
                    marks.append(name.split()[0])
            state = ", ".join(marks) if marks else "no outside-repo state on a code line"
        print("  %-72s %s" % (p, state))
print()
print("  READ THIS EXACTLY: a class name against a file on this list means the file CONTAINS")
print("  that shape, NOT that the shape changes a verdict. C-ENVREAD in particular fires on")
print("  ${TMPDIR:-/tmp} and ${1:?usage}, which are the CORRECT idioms. The one shape this")
print("  task PROVED can flip a verdict is C-TMP-ASSIGN inside the linter's corpus, and that")
print("  is what conformance.sh now pins.")
sys.exit(0)
