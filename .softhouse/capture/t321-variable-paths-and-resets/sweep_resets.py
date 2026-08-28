#!/usr/bin/env python3
"""T321 part 2 -- THE DECORATIVE-RESET SWEEP. How many mutate-and-restore drives in this repo
have a reset that does not reset?

WHY THIS EXISTS. T316's own red drive used `git checkout -- .` + `git clean -fd` between arms.
That pair does NOT clear a STAGED ADDITION: `git checkout -- .` rewrites the worktree FROM THE
INDEX, so a staged new file survives it in both index and worktree, and `git clean -fd` will not
touch a path the index knows about. T316's arm G2 planted a file and staged it; the plant carried
into G3. Its own post-reset `git status --porcelain` assertion caught this and the drive ABORTED
rather than reporting eleven green arms of which two were contaminated. The failure is RECORDED,
not hypothetical (T316 handoff, "Three defects I shipped and then caught", item 3; FU-T316-6).

A drive whose arms can contaminate each other reports results that are not what they say they
are, and this program grades money on drives.

THE SELECTOR, PRINTED BESIDE EVERY FIGURE (P-66/P-70: `not found` is a statement about the
SEARCH, so the search is stated):

    corpus       `git ls-files '.softhouse/'` restricted to suffixes .py .sh .zsh .bash --
                 TRACKED files only. Untracked files, other workers' live worktrees, and any
                 drive written in a language this selector does not read are OUT. That is a
                 limit of the census, never a fact about the world.

    population   a corpus file is IN if it contains at least one RESTORE SITE -- a line matching
                 one of the RESTORE_IDIOMS below, after line comments are stripped so that PROSE
                 ABOUT a reset is not counted as a reset. Files that mutate and NEVER restore
                 are NOT in the population; that is a different (and worse) class and this sweep
                 does not claim to have counted it.

    classify     per FILE, three independent readings, all derived from the file's own text:
                   MUTATIONS  -- which state classes the file is capable of dirtying
                   RESTORES   -- which classes its restore sites can clear
                   REPETITION -- whether the restore sites, and the fresh-repo sites, are
                                 reached MORE THAN ONCE (see MULTIPLICITY below)

THE SIX STATE CLASSES a repo can be left in, and what actually clears each. Every row is DRIVEN
in `drive-reset-contamination-t321.py` -- none of it is quoted from the git manual:

    W  worktree edit of a TRACKED file     <- `git checkout -- .` / `git restore .` / `reset --hard`
    S  STAGED ADDITION (`git add` newfile) <- `git reset --hard` ONLY.  NOT `checkout -- .`+`clean -fd`
    U  UNTRACKED file                      <- `git clean -f` (`-d` for directories)
    I  IGNORED file                        <- `git clean -fdx` / `-fdX` ONLY
    C  COMMIT on the checked-out branch    <- `git reset --hard <ref>` naming a ref, or re-clone
    R  REF created/deleted, or HEAD moved  <- explicit branch restore, or re-clone

MULTIPLICITY, and why a naive sweep gets this exactly backwards. A drive that builds a FRESH
SCRATCH REPO PER ARM has no inter-arm state, so its reset sites are teardown and not containment;
calling those drives defective would be the wolf-cry that gets the whole sweep pinned away in one
fire (T325 arm G5's lesson: *a check that reports ordinary pipeline work as damage will be
disabled within two fires*). Both shapes exist here and they are NOT distinguishable by counting
`git clone` occurrences -- T316 clones once and resets between arms; T325 clones inside `mk()`,
called once from `arm()`, called 22 times.

So multiplicity is computed over the CALL GRAPH, textually:
    mult(top level) = 1
    mult(f) = sum over call sites of  mult(enclosing scope) * (LOOP_FACTOR if the site is inside
              a for/while body else 1)
    a SITE's multiplicity is mult(its enclosing scope) * (LOOP_FACTOR if in a loop)
Then:
    fresh-repo site with multiplicity >= 2  =>  ISOLATED (a new repo per arm)
    restore site   with multiplicity >= 2  =>  the reset is LOAD-BEARING (it runs between arms)
This reproduces both recorded cases, and both are ENFORCED as calibration below.

VERDICTS
    ISOLATED     a fresh repo is built more than once; inter-arm reset is not load-bearing
    TEARDOWN     the file's restore sites are reached at most once -- cleanup, not containment
    SUFFICIENT   the reset is load-bearing and clears every class the file can dirty
    DECORATIVE   the reset is load-bearing and does NOT clear some class the file can dirty:
                 CONTAMINATION IS POSSIBLE between arms.

    ** DECORATIVE IS A CANDIDATE, NOT A FINDING. ** P-95's rule, in its own words:
    "A FALLBACK AND A FAIL-OPEN ARE INDISTINGUISHABLE BY READING ... the disconfirming
    experiment is two lines -- remove the dependency and run it." The same holds one level
    over: a reset is only proven insufficient by DRIVING it. Reading nominates; the drive
    convicts. `drive-reset-contamination-t321.py` is the conviction.

CONSERVATIVE IN THE ACCUSING DIRECTION, stated so nobody has to discover it: a file-write is
counted as dirtying BOTH W and U, because static text cannot tell `write_text` on a tracked
file from `write_text` on a new one. That inflates DECORATIVE and cannot deflate it -- which is
the correct direction for a CANDIDATE list whose every row is then driven.

EXIT: 0 sweep completed; 2 corpus or calibration failure. Never conflated (P-80).
CALIBRATION IS ENFORCED and there are three anchors, two from the tree and one from the record:
    NEG-ISOLATED  T325's fire-writ drive     -> ISOLATED     (fresh fixture per arm)
    NEG-FIXED     T316's SHIPPED red drive   -> not DECORATIVE (T316 FIXED it before shipping;
                  the shipped bytes use `git reset --hard` + `git clean -fdq` + a porcelain
                  assertion, so a sweep that still called it decorative would be reading the
                  handoff instead of the file)
    POS-RECORDED  T316's PRE-FIX reset, reproduced verbatim from the record as an in-memory
                  fixture -> DECORATIVE, uncleared class S
A calibration failure ABORTS at exit 2 with NO probe line rather than reporting a clean tree
(P-84: "'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE.").

Probe line: `T321-RESET-SWEEP:` -- printed on every path that reaches a count, and on no other.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROBE = "T321-RESET-SWEEP:"
SUFFIXES = (".py", ".sh", ".zsh", ".bash")
LOOP_FACTOR = 4          # "inside a loop" means "more than once"; the exact number is not used

# --------------------------------------------------------------------------------------------
# GIT INVOCATION TOKENISER
#
# A LINE-LEVEL regex over `git ... reset ...` is not good enough and the first version of this
# sweep proved it on its own calibration fixture: `run(["git", "checkout", "--", "."], clone)`
# matched a FRESH-REPO pattern of the shape `git .* clone`, because `clone` was the name of a
# PYTHON VARIABLE eleven characters later. The classifier called T316's recorded decorative
# reset ISOLATED. So git commands are TOKENISED and the subcommand is read by ADJACENCY:
# tokens after `git`, skipping `-C <dir>` / `-c <k=v>` / `--git-dir=...`, first non-option token
# is the subcommand. Works identically for shell (`git reset --hard`) and for a Python argv
# list (`["git", "reset", "--hard"]`), which is why both drive styles in this repo are read.
# --------------------------------------------------------------------------------------------
TOKEN_RE = re.compile(r"[-\w./=]+")
QUOTED_RE = re.compile(r"""['"]([^'"]*)['"]""")
QUOTED_GIT_RE = re.compile(r"""['"]git['"]""")


def git_invocations(line):
    """-> list of (subcommand, [remaining tokens]). Empty when the line invokes no git.

    TWO TOKENISERS, and the second one is not a refinement -- it is a defect fix that the
    calibration forced. A Python argv list `run(["git", "reset", "--hard", "--quiet"], clone)`
    tokenised as bare words yields `... --hard --quiet clone`, and `clone` -- A LOCAL VARIABLE
    NAME -- reads as the REF argument of `reset --hard`, which promotes the reset to "also
    clears a commit". That silently made T316's drive look stronger than it is. So: when the
    line quotes `git`, ONLY QUOTED TOKENS COUNT; the argv list ends at the closing bracket and
    every python identifier after it is out of frame."""
    toks = QUOTED_RE.findall(line) if QUOTED_GIT_RE.search(line) else TOKEN_RE.findall(line)
    out = []
    for i, t in enumerate(toks):
        if t != "git":
            continue
        j = i + 1
        while j < len(toks):
            if toks[j] in ("-C", "-c"):
                j += 2
                continue
            if toks[j].startswith("-"):
                j += 1
                continue
            break
        if j < len(toks):
            out.append((toks[j], toks[j + 1:]))
    return out


def restore_idioms_on(line):
    """Which RESTORE classes this line performs. Derived from the tokenised subcommand."""
    found = []
    for sub, rest in git_invocations(line):
        if sub == "reset":
            if any(t == "--hard" for t in rest):
                found.append("reset_hard")
            else:
                found.append("reset_mixed")
        elif sub == "checkout":
            if any(t in ("--", ".") for t in rest):
                found.append("checkout_wt")
        elif sub == "restore":
            found.append("restore_wt")
        elif sub == "clean":
            flags = "".join(t for t in rest if t.startswith("-"))
            found.append("clean_x" if ("x" in flags or "X" in flags) else "clean_plain")
        elif sub == "stash":
            if any(t in ("pop", "apply") for t in rest):
                found.append("stash_pop")
    if BACKUP_RESTORE_RE.search(line):
        found.append("backup_copy")
    if RM_TARGETED_RE.search(line):
        found.append("rm_targeted")
    return found


# TARGETED REMOVAL. `rm -f "$FIX/$f.json"` in a cleanup trap clears exactly the untracked files
# it NAMES -- and nothing else. It is a real restore and leaving it out produced four DECORATIVE
# rows in the first run of this sweep that were false accusations: T291's probe removes its
# fixtures by name in a `cleanup()` trap and then `git checkout --`s the one tracked file it
# moved. So it counts -- but it earns its OWN verdict, never a clean SUFFICIENT, because whether
# the removal list COVERS what the arm creates cannot be read off the text. That question is
# settled by driving, which is the whole point (P-95).
RM_TARGETED_RE = re.compile(
    r"(\brm\s+-[a-zA-Z]*f|\brm\s+-[a-zA-Z]*r|\bos\.remove\s*\(|\bos\.unlink\s*\("
    r"|\.unlink\s*\(|shutil\.rmtree\s*\()")


BACKUP_RESTORE_RE = re.compile(
    r"(shutil\.(copy2?|copyfile|move)\s*\([^\n]*(bak|backup|orig|saved)"
    r"|\bcp\s+-[a-zA-Z]*\s*[^\n]*\.(bak|orig)\b"
    r"|\bmv\s+[^\n]*\.(bak|orig)\b)", re.I)

RESTORE_NAMES = ["reset_hard", "reset_mixed", "checkout_wt", "restore_wt", "clean_x",
                 "clean_plain", "stash_pop", "backup_copy", "rm_targeted"]

# What each restore idiom CLEARS -- every row driven in the K block of the contamination drive.
RESTORE_CLEARS = {
    "reset_hard":  {"W", "S"},      # + C only when a REF is named -- see named_ref_reset()
    "reset_mixed": {"S"},           # unstages; the file stays in the worktree, now UNTRACKED
    "checkout_wt": {"W"},           # rebuilds the worktree FROM THE INDEX: a staged add SURVIVES
    "restore_wt":  {"W"},
    "clean_x":     {"U", "I"},
    "clean_plain": {"U"},
    "stash_pop":   set(),           # restores a stash; it does not undo anything
    "backup_copy": {"W"},
    "rm_targeted": {"U"},           # ONLY the paths it names -- see SUFFICIENT-TARGETED
}

# --------------------------------------------------------------------------------------------
# MUTATION IDIOMS -- what dirties a repo.
# --------------------------------------------------------------------------------------------
FILE_WRITE_RE = re.compile(
    r"(\.write_text\s*\(|\.write_bytes\s*\(|\bopen\s*\([^\n]*['\"][wa]"
    r"|shutil\.copy|shutil\.move|\bsed\s+-i|\btouch\b|\btee\b"
    r"|\bcat\s*>|\bprintf\b[^\n]*\s>|\becho\b[^\n]*\s>)")
IGNORE_WRITE_RE = re.compile(r"\.gitignore[^\n]*(write_text|>>|>)|>>?[^\n]*\.gitignore")
FRESH_TMP_RE = re.compile(r"\bmkdtemp\b|\bmktemp\s+-d\b|\bTemporaryDirectory\b")


def mutation_classes_on(line):
    """Which state classes this line can dirty. Tokenised for git; regex for file writes."""
    found = set()
    for sub, rest in git_invocations(line):
        if sub == "add":
            found.add("S")
        elif sub == "commit":
            found.add("C")
        elif sub in ("update-ref", "push"):
            found.add("R")
        elif sub == "checkout" and "-b" in rest:
            found.add("R")
        elif sub == "switch" and "-c" in rest:
            found.add("R")
        elif sub == "branch" and any(t in ("-d", "-D", "-m", "-M") for t in rest):
            found.add("R")
        elif sub == "tag" and rest and not any(t in ("-l", "--list") for t in rest):
            found.add("R")
        elif sub == "notes" and "add" in rest:
            found.add("R")
        elif sub == "worktree" and "add" in rest:
            found.add("R")
    # a file write dirties BOTH W and U -- see "CONSERVATIVE IN THE ACCUSING DIRECTION"
    if FILE_WRITE_RE.search(line):
        found.add("W")
        found.add("U")
    if IGNORE_WRITE_RE.search(line):
        found.add("I")
    return found


def fresh_repo_on(line):
    for sub, _rest in git_invocations(line):
        if sub in ("clone", "init"):
            return True
    return bool(FRESH_TMP_RE.search(line))

CALIB_NEG_ISOLATED = ".softhouse/capture/t325-adopt-attestation/instruments/20-fire-writ-drive.sh"
CALIB_NEG_FIXED = ".softhouse/capture/t316-dead-path-guards/drive-red-t316.py"

# T316's PRE-FIX reset, as the record states it, plus the arm that carried into the next one.
CALIB_POS_TEXT = '''
def reset(clone):
    run(["git", "checkout", "--", "."], clone)
    run(["git", "clean", "-fd"], clone)

def main():
    for name in ARMS:
        reset(clone)
        planted = clone / "planted_regression.py"
        planted.write_text("x")
        run(["git", "add", "-f", str(planted)], clone)

sys.exit(main())
'''


def repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: no .git ancestor of this file. REFUSING.", file=sys.stderr)
    raise SystemExit(2)


def corpus(root: Path):
    proc = subprocess.run(["git", "ls-files", "-z", ".softhouse/"],
                          cwd=str(root), capture_output=True, text=True)
    if proc.returncode != 0:
        print("ERROR: git ls-files exited %d: %s" % (proc.returncode, proc.stderr.strip()),
              file=sys.stderr)
        raise SystemExit(2)
    files = [f for f in proc.stdout.split("\0") if f.strip() and f.endswith(SUFFIXES)]
    if not files:
        print("ERROR: the corpus is EMPTY. That is a selector failure, not a clean tree.",
              file=sys.stderr)
        raise SystemExit(2)
    return sorted(files)


def strip_comment(line: str) -> str:
    """Drop a line comment so PROSE ABOUT a reset is not counted as a reset. Crude and
    deliberately conservative: a `#` inside a string truncates the line, which can only ever
    REMOVE a match, never invent one."""
    out, q = [], None
    for ch in line:
        if q:
            out.append(ch)
            if ch == q:
                q = None
            continue
        if ch in "'\"":
            q = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out)


# --------------------------------------------------------------------------------------------
# SCOPES AND MULTIPLICITY
# --------------------------------------------------------------------------------------------
PY_DEF = re.compile(r"^(\s*)def\s+([A-Za-z_]\w*)\s*\(")
SH_DEF = re.compile(r"^\s*(?:function\s+)?([A-Za-z_]\w*)\s*\(\s*\)\s*\{")
PY_LOOP = re.compile(r"^(\s*)(for|while)\b")
SH_LOOP = re.compile(r"^\s*(for|while)\b|\bdo\b\s*$")


def scopes_and_loops(lines, is_py):
    """Return (scope_of_line, in_loop_of_line, def_lines) -- scope name per 1-based line."""
    n = len(lines)
    scope = ["<top>"] * (n + 1)
    inloop = [False] * (n + 1)
    defs = {}
    if is_py:
        stack = []   # (indent, name)
        loopstack = []
        for i, raw in enumerate(lines, 1):
            if not raw.strip():
                scope[i] = stack[-1][1] if stack else "<top>"
                inloop[i] = bool(loopstack)
                continue
            ind = len(raw) - len(raw.lstrip())
            while stack and ind <= stack[-1][0]:
                stack.pop()
            while loopstack and ind <= loopstack[-1]:
                loopstack.pop()
            m = PY_DEF.match(raw)
            if m:
                defs[m.group(2)] = i
                scope[i] = stack[-1][1] if stack else "<top>"
                inloop[i] = bool(loopstack)
                stack.append((len(m.group(1)), m.group(2)))
                continue
            scope[i] = stack[-1][1] if stack else "<top>"
            inloop[i] = bool(loopstack)
            if PY_LOOP.match(raw):
                loopstack.append(ind)
        return scope, inloop, defs
    # SHELL. A function body ends at the first `}` ALONE ON ITS LINE. Brace COUNTING was tried
    # first and it is wrong: `${TMPDIR:-/tmp}` and every other parameter expansion carries braces,
    # so the count never returns to zero and every later `name() {` is swallowed by the first
    # function. Measured, not assumed: under brace counting this file saw 2 of the 6 functions in
    # T325's fire-writ drive and put `arm`'s body inside `mk`, which is what made the enforced
    # NEG-ISOLATED calibration abort. The alone-on-its-line rule is the shell style every drive
    # in this repo is written in, and a file that violates it degrades to `<top>` -- i.e. to
    # multiplicity 1, i.e. to TEARDOWN, which is the NON-accusing direction.
    cur = None
    loopdepth = 0
    for i, raw in enumerate(lines, 1):
        m = SH_DEF.match(raw)
        if m and cur is None:
            defs[m.group(1)] = i
            scope[i] = "<top>"
            cur = m.group(1)
            # ONE-LINER: `snap()  { bash "$GUARD" snapshot "$1" "$2"; }` closes on its own line.
            # Without this the next twenty functions are swallowed and every one of them scores
            # multiplicity 0. Measured on T325's fire-writ drive, where `snap()` at line 76 hid
            # `arm()` at line 90 and the enforced NEG-ISOLATED calibration aborted.
            if re.search(r"\}\s*$", raw):
                cur = None
            continue
        scope[i] = cur or "<top>"
        inloop[i] = loopdepth > 0
        if cur and re.match(r"^\s*\}\s*$", raw):
            cur = None
        if re.match(r"^\s*(for|while|until)\b", raw):
            loopdepth += 1
        if re.match(r"^\s*done\b", raw):
            loopdepth = max(0, loopdepth - 1)
    return scope, inloop, defs


def multiplicities(lines, scope, inloop, defs, is_py):
    """Fixpoint over the textual call graph. mult('<top>') == 1."""
    call_sites = {name: [] for name in defs}
    for name in defs:
        if is_py:
            rx = re.compile(r"(?<![\w.])" + re.escape(name) + r"\s*\(")
        else:
            rx = re.compile(r"(^|[;&|(\s])" + re.escape(name) + r"(\s|$|;|&|\|)")
        for i, raw in enumerate(lines, 1):
            if i == defs[name]:
                continue
            line = strip_comment(raw)
            if rx.search(line):
                call_sites[name].append(i)
    mult = {"<top>": 1}
    for name in defs:
        mult[name] = 0
    for _ in range(12):                       # small fixpoint; call graphs here are shallow
        changed = False
        for name in defs:
            tot = 0
            for i in call_sites[name]:
                caller = scope[i]
                tot += mult.get(caller, 0) * (LOOP_FACTOR if inloop[i] else 1)
            tot = min(tot, 999)   # capped: only ">=2 or not" is ever read, and an uncapped
            if tot != mult[name]:  # product of loop factors printed 2,657,200 on one file
                mult[name] = tot
                changed = True
        if not changed:
            break
    return mult, call_sites


def site_mult(i, scope, inloop, mult):
    return mult.get(scope[i], 0) * (LOOP_FACTOR if inloop[i] else 1)


def named_ref_reset(codelines):
    """`git reset --hard <REF>` also clears C. A BARE `reset --hard` does not: it resets to
    HEAD, and a commit has already moved HEAD."""
    for line in codelines:
        for sub, rest in git_invocations(line):
            if sub != "reset":
                continue
            for t in rest:
                if t.startswith("-"):
                    continue
                if t not in ("HEAD", "."):
                    return True
    return False


def strip_py_docstrings(lines):
    """Blank out triple-quoted blocks. A .py file whose DOCSTRING describes `git reset --hard`
    is describing a reset, not performing one -- and every instrument in this repo has a long
    one. Without this, a sweep of drives reads their own prose as their behaviour."""
    out = []
    delim = None
    for raw in lines:
        if delim is None:
            m = re.search(r'("""|\'\'\')', raw)
            if m:
                d = m.group(1)
                head = raw[:m.start()]
                rest = raw[m.end():]
                if d in rest:                     # opens and closes on one line
                    out.append(head + rest.split(d, 1)[1])
                else:
                    delim = d
                    out.append(head)
                continue
            out.append(raw)
        else:
            if delim in raw:
                out.append(raw.split(delim, 1)[1])
                delim = None
            else:
                out.append("")
    return out


def classify(path, text):
    is_py = path.endswith(".py") or text.startswith("#!/usr/bin/env python")
    lines = text.splitlines()
    scope, inloop, defs = scopes_and_loops(lines, is_py)
    mult, _ = multiplicities(lines, scope, inloop, defs, is_py)

    code = [strip_comment(r) for r in lines]
    if is_py:
        code = strip_py_docstrings(code)

    restores, mutations, fresh = {}, {}, []
    site_idioms = []          # (multiplicity, scope, idiom) per restore SITE
    restore_mult = 0
    fresh_mult = 0
    for i, line in enumerate(code, 1):
        if not line.strip():
            continue
        m = site_mult(i, scope, inloop, mult)
        for name in restore_idioms_on(line):
            restores.setdefault(name, []).append(i)
            site_idioms.append((m, scope[i], name))
            restore_mult = max(restore_mult, m)
        for c in mutation_classes_on(line):
            mutations.setdefault(c, []).append(i)
        if fresh_repo_on(line):
            fresh.append(i)
            fresh_mult = max(fresh_mult, m)

    # POPULATION MEMBERSHIP requires a GIT restore or a backup-restore. `rm -rf "$SCRATCH"` is
    # the teardown of a temp directory, not the restoration of a repo, and admitting it as a
    # population criterion took this sweep from 37 files to 382 in one edit -- 345 of them
    # scripts that delete their own scratch dir and never restore anything. It is kept ONLY as
    # a MITIGATOR: it can clear U for a file already in the population, never admit one.
    if not (set(restores) - {"rm_targeted"}):
        return None

    # THE LOAD-BEARING RESET IS NOT "EVERY RESTORE IDIOM IN THE FILE". A file may `git checkout
    # -- x` in a teardown trap and `git clean -fd` in a setup helper; unioning them credits the
    # inter-arm reset with a capability it does not have at the moment it runs. So `cleared` is
    # the union over the restore sites that are ACTUALLY THE INTER-ARM RESET -- the ones at the
    # highest multiplicity, in the scope where that maximum occurs. The file-wide union is kept
    # beside it as `cleared_anywhere` so the two can be compared rather than conflated.
    cleared_anywhere = set()
    for name in restores:
        cleared_anywhere |= RESTORE_CLEARS[name]
    lb_scopes = {sc for (mm, sc, _n) in site_idioms if mm == restore_mult}
    cleared = set()
    for (mm, sc, name) in site_idioms:
        if mm == restore_mult and sc in lb_scopes:
            cleared |= RESTORE_CLEARS[name]
    if "reset_hard" in restores and named_ref_reset(code):
        cleared.add("C")
        cleared_anywhere.add("C")
    dirtied = set(mutations)
    uncleared = sorted(dirtied - cleared)

    if fresh_mult >= 2:
        verdict = "ISOLATED"
    elif restore_mult < 2:
        verdict = "TEARDOWN"
    elif uncleared:
        verdict = "DECORATIVE"
    elif "rm_targeted" in restores and "U" in dirtied and not (
            {"clean_plain", "clean_x"} & set(restores)):
        # the ONLY thing clearing U is a removal of NAMED paths. Sufficient iff that list is
        # complete, which the text cannot say. Driven, not read.
        verdict = "SUFFICIENT-TARGETED"
    else:
        verdict = "SUFFICIENT"

    return {
        "path": path,
        "verdict": verdict,
        "restore_idioms": {k: v[:8] for k, v in sorted(restores.items())},
        "restore_multiplicity": restore_mult,
        "fresh_repo_multiplicity": fresh_mult,
        "mutation_classes": sorted(dirtied),
        "cleared_classes": sorted(cleared),
        "cleared_anywhere": sorted(cleared_anywhere),
        "uncleared_classes": uncleared,
    }


def calibrate(rows):
    seen = {r["path"]: r for r in rows}
    errs = []
    n = seen.get(CALIB_NEG_ISOLATED)
    if n is None:
        errs.append("NEG-ISOLATED absent from the population: " + CALIB_NEG_ISOLATED)
    elif n["verdict"] != "ISOLATED":
        errs.append("NEG-ISOLATED classified %s, expected ISOLATED: %s"
                    % (n["verdict"], CALIB_NEG_ISOLATED))
    f = seen.get(CALIB_NEG_FIXED)
    if f is None:
        errs.append("NEG-FIXED absent from the population: " + CALIB_NEG_FIXED)
    elif f["verdict"] == "DECORATIVE":
        errs.append("NEG-FIXED classified DECORATIVE though T316 FIXED it before shipping: "
                    + CALIB_NEG_FIXED)
    p = classify("<calibration>/prefix_reset.py", CALIB_POS_TEXT)
    if p is None:
        errs.append("POS-RECORDED produced no row at all -- the selector sees no restore site")
    elif p["verdict"] != "DECORATIVE" or "S" not in p["uncleared_classes"]:
        errs.append("POS-RECORDED classified %s uncleared=%s, expected DECORATIVE with S"
                    % (p["verdict"], p and p["uncleared_classes"]))
    return errs, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--verdict")
    args = ap.parse_args()

    root = repo_root()
    files = corpus(root)
    rows, unreadable = [], []
    for f in files:
        try:
            text = (root / f).read_text(errors="replace")
        except OSError as e:
            unreadable.append([f, str(e)])
            continue
        r = classify(f, text)
        if r:
            rows.append(r)

    errs, calpos = calibrate(rows)
    if errs:
        print("ERROR: CALIBRATION FAILED. The selector cannot reproduce a result already on the",
              file=sys.stderr)
        print("       record, so its count is evidence of nothing. NO PROBE LINE IS PRINTED.",
              file=sys.stderr)
        for e in errs:
            print("       - " + e, file=sys.stderr)
        raise SystemExit(2)

    by = {}
    for r in rows:
        by[r["verdict"]] = by.get(r["verdict"], 0) + 1

    print("SELECTOR, stated as a limit on the search:")
    print("  corpus      : git ls-files '.softhouse/' filtered to %s  ->  %d tracked files"
          % (" ".join(SUFFIXES), len(files)))
    print("  population  : corpus files with >=1 RESTORE SITE, line comments stripped first")
    print("  restore     : %s" % ", ".join(RESTORE_NAMES))
    print("  classes     : W worktree-edit  S staged-add  U untracked  I ignored  C commit  R ref")
    print("  multiplicity: textual call graph, mult(<top>)=1, loop factor %d;" % LOOP_FACTOR)
    print("                fresh-repo site mult>=2 => ISOLATED; restore site mult<2 => TEARDOWN")
    print("  blind to    : untracked files; other workers' live worktrees; drives in a language")
    print("                this selector does not read; a restore done by a helper it cannot name")
    print("  bias        : a file-write counts as dirtying BOTH W and U (static text cannot tell")
    print("                a tracked target from a new one) -- inflates DECORATIVE, never deflates")
    print("  calibration : NEG-ISOLATED %s" % CALIB_NEG_ISOLATED)
    print("                NEG-FIXED    %s" % CALIB_NEG_FIXED)
    print("                POS-RECORDED T316's pre-fix reset, in-memory -> %s uncleared=%s"
          % (calpos["verdict"], ",".join(calpos["uncleared_classes"])))
    print("                all three ENFORCED; failure aborts at exit 2 with NO probe line.")
    if unreadable:
        print("  unreadable  : %d (listed in --json)" % len(unreadable))
    print()

    order = {"DECORATIVE": 0, "SUFFICIENT-TARGETED": 1, "SUFFICIENT": 2,
             "ISOLATED": 3, "TEARDOWN": 4}
    for r in sorted(rows, key=lambda x: (order[x["verdict"]], x["path"])):
        if args.verdict and r["verdict"] != args.verdict:
            continue
        print("%-19s uncleared=%-8s mut=%-11s cleared=%-11s rMult=%-3d fMult=%-3d %s"
              % (r["verdict"], ",".join(r["uncleared_classes"]) or "-",
                 ",".join(r["mutation_classes"]) or "-",
                 ",".join(r["cleared_classes"]) or "-",
                 r["restore_multiplicity"], r["fresh_repo_multiplicity"], r["path"]))
    print()
    print("%s corpus=%d population=%d decorative=%d sufficientTargeted=%d sufficient=%d "
          "isolated=%d teardown=%d"
          % (PROBE, len(files), len(rows), by.get("DECORATIVE", 0),
             by.get("SUFFICIENT-TARGETED", 0), by.get("SUFFICIENT", 0),
             by.get("ISOLATED", 0), by.get("TEARDOWN", 0)))
    print("NOTE: DECORATIVE is a CANDIDATE, not a finding. Reading nominates; the drive convicts")
    print("      (P-95). See drive-reset-contamination-t321.py.")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"selector": {"suffixes": list(SUFFIXES), "corpus_size": len(files),
                          "loop_factor": LOOP_FACTOR},
             "counts": by, "rows": rows, "unreadable": unreadable}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
