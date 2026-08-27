#!/usr/bin/env python3
"""Branch corpse sweep + case-shadow guard.  T312.

WHY THIS EXISTS -- the measurement, not a worry.
On 2026-08-27 the driver of fire `20260827-230001` asked "do these eight dispatched
branches hold surviving work?" and answered it with a hand-typed glob:

    git branch -a --list 'softhouse/t2*' --list 'softhouse/t3*'      # lowercase

The repo's convention is UPPERCASE (`softhouse/T297-...`), `git branch --list` globbing
is case-SENSITIVE, and the glob returned nothing for T297-T309. The driver recorded
"gone or empty" in RESUME.md and in a PUSHED commit message, and re-dispatched six tasks
as fresh attempts.  All eight had commits: T308 had 32, T309 eleven, T298 ten, T304
seven, T306 five, T302 four, and the "empty" T297 four -- one of them named "review
scaffold - first commit before analysis (SIGTERM insurance)", a worker doing exactly what
the commit-early rule asks.  A WORKER caught it, not the driver.
[VERIFIED: .softhouse/observations/20260827-branch-case-collision-shadows-committed-work.md]

THE SECOND MECHANISM, which is worse and which the wrong-case dispatch CREATES.
macOS's filesystem is case-insensitive, so `refs/heads/softhouse/T297-x` and
`.../t297-x` are ONE path -- but `.git/packed-refs` is a text file and is
case-SENSITIVE.  A loose ref of one case therefore shadows a packed ref of another, git
resolves loose before packed, and the packed value becomes UNREACHABLE BY NAME while
remaining a live object.  Measured in this very repo while writing this file:

    packed-refs:  c1a3888a refs/heads/softhouse/T297-review-t295
    loose file:   .git/refs/heads/softhouse/t297-review-t295 -> d189230b
    git rev-parse softhouse/T297-review-t295  ->  d189230b   (BOTH names, one answer)
    git merge-base --is-ancestor c1a3888a d189230b  ->  rc 1  (DIVERGED)

TWO RULES THIS FILE IMPLEMENTS.

  P-66 -- "'Not found' is a statement about the search, never about the world.  Before
  recording that a dependency, file, vector or citation does not exist, state where you
  looked."  Every report this program prints leads with its SELECTOR: which patterns,
  matched how, against which storages, from which directory, and what it could NOT read.
  A "no findings" line here is a measurement with its scope attached, not a default.

  P-45 -- "a guard that only works when someone remembers to run it enforces nothing."
  A sweep the driver retypes each fire is exactly such a guard, and it has now produced
  a false "all empty" once.  So the refusal does not live in this program's `main` alone:
  `install-hook` installs a git `reference-transaction` hook that refuses the ref
  CREATION itself.  A shadowing branch then cannot be created by any command -- `git
  branch`, `git worktree add -b`, `git push`, `git fetch`, `git update-ref` -- whether or
  not anyone remembered to run a check first.

WHAT IT REPORTS THAT `git branch --list` CANNOT.
  * case-INSENSITIVE matching, so a lowercase selector finds uppercase branches;
  * BOTH the loose value and the packed value for every candidate name, separately;
  * which stored value is UNREACHABLE BY NAME because another case shadows it;
  * whether the two lines have DIVERGED (neither is an ancestor of the other), which is
    the difference between "stale duplicate" and "committed work that is invisible".
  A sweep that reports only the winning ref reproduces the defect it is named after.

Commands
  sweep [--pattern GLOB]... [--counts|--no-counts] [--ensure-hook] [--quiet]
        [--base REF] [--repo D]
        Report every candidate ref, grouped by case-folded name.  `--quiet` prints only
        the flagged groups and says how many unflagged ones it inspected.
  check-dispatch NAME... [--repo D]
        The dispatch-time refusal.  Exit 3 if a case-variant of NAME already exists
        under a different spelling, or if NAME is not canonical-case.
  install-hook [--repo D]
        Install the reference-transaction ref guard.  Idempotent.
  hook STATE  (stdin: "<old> <new> <refname>" lines)
        The hook body.  PURE FILESYSTEM -- it never runs git, because it executes
        inside a live ref transaction holding ref locks.

Exit codes
  0   completed, nothing to report
  1   COULD NOT COMPLETE (git missing, refs unreadable).  Never read as "clean".
  3   FINDINGS: case-shadowing, an unreachable stored value, or a divergence.
      From `check-dispatch`: REFUSED.  From `hook`: the transaction is ABORTED.
  4   no ref findings, but the ref-guard hook is NOT installed -- enforcement is off.
  64  usage error
"""
import fnmatch
import os
import shutil
import subprocess
import sys

GIT = shutil.which("git")
HOOK_MARK = "softhouse-t312-ref-guard"
# `softhouse/rescued-agent-<hex>-<stamp>` is machine-generated and lowercase by design;
# it is the one exception to the canonical-case rule below.
CANONICAL_EXEMPT_PREFIXES = ("rescued-agent-",)


# ----------------------------------------------------------------- plumbing ---
def _run(args, cwd=None, timeout=20):
    """Returns (rc, stdout, stderr).  rc is None when the program could not be run."""
    if not GIT:
        return None, "", "git was not found on PATH"
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout)
    except Exception as exc:                                    # noqa: BLE001
        return None, "", "%s: %s" % (type(exc).__name__, exc)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def gitdir_of(repo):
    """(gitdir, note).  Filesystem-first so the hook never shells out to git."""
    dot = os.path.join(repo, ".git")
    if os.path.isdir(dot):
        return os.path.abspath(dot), "read .git/ directly"
    if os.path.isfile(dot):
        try:
            txt = open(dot).read().strip()
        except OSError as exc:
            return None, "could not read %s: %s" % (dot, exc)
        if txt.startswith("gitdir:"):
            p = txt.split(":", 1)[1].strip()
            if not os.path.isabs(p):
                p = os.path.join(repo, p)
            return os.path.abspath(p), "followed the .git file (linked worktree)"
        return None, "%s is a file but has no `gitdir:` line" % dot
    rc, out, err = _run([GIT, "-C", repo, "rev-parse", "--absolute-git-dir"])
    if rc == 0 and out:
        return out, "asked git rev-parse --absolute-git-dir"
    return None, "no .git at %s and git could not answer (%s)" % (dot, err or rc)


def common_dir_of(repo):
    """(common_dir, note).  The COMMON dir is where refs/heads and packed-refs live;
    a linked worktree's own gitdir has neither, and getting this wrong would make the
    sweep report an empty repo from inside a worktree."""
    gd, note = gitdir_of(repo)
    if gd is None:
        return None, note
    cdf = os.path.join(gd, "commondir")
    if os.path.isfile(cdf):
        try:
            p = open(cdf).read().strip()
        except OSError as exc:
            return None, "could not read %s: %s" % (cdf, exc)
        if not os.path.isabs(p):
            p = os.path.join(gd, p)
        return os.path.abspath(p), note + "; followed commondir to the main gitdir"
    return gd, note


# ------------------------------------------------------------- the ref index ---
class RefIndex(object):
    """Loose refs and packed refs read SEPARATELY, and never merged.

    `git for-each-ref` and `git branch` answer "what is the value of this ref", which is
    the loose value when a loose ref exists.  That single answer is what hid c1a3888a.
    So this index keeps two dicts and refuses to collapse them.

    THE ON-DISK NAME MATTERS.  Loose names come from os.walk (readdir), which returns the
    name as STORED.  Looking a name up by opening a constructed path would, on a
    case-insensitive filesystem, silently return the differently-cased file -- the exact
    confusion under investigation.
    """

    def __init__(self, common_dir):
        self.common_dir = common_dir
        self.loose = {}          # full refname -> value (sha, or "ref: ...")
        self.packed = {}         # full refname -> sha
        self.errors = []         # everything that could NOT be read
        self.notes = []
        self._read_loose()
        self._read_packed()

    def _read_loose(self):
        root = os.path.join(self.common_dir, "refs", "heads")
        if not os.path.isdir(root):
            self.notes.append("no loose heads directory at %s (all refs are packed, or "
                              "this is not a repo)" % root)
            return
        n = 0
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith(".lock") or fn == ".DS_Store":
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                try:
                    val = open(path).read().strip()
                except OSError as exc:
                    self.errors.append("loose ref %s unreadable: %s" % (rel, exc))
                    continue
                self.loose["refs/heads/" + rel] = val
                n += 1
        self.notes.append("walked %s -- %d loose head(s), names as stored on disk"
                          % (root, n))

    def _read_packed(self):
        path = os.path.join(self.common_dir, "packed-refs")
        if not os.path.isfile(path):
            self.notes.append("no packed-refs file at %s -- nothing is packed" % path)
            return
        try:
            lines = open(path).read().splitlines()
        except OSError as exc:
            self.errors.append("packed-refs unreadable (%s): %s -- refs that exist ONLY "
                               "as packed entries are INVISIBLE to this run"
                               % (path, exc))
            return
        n = 0
        for line in lines:
            if not line or line[0] in "#^":
                continue
            parts = line.split(" ", 1)
            if len(parts) != 2:
                self.errors.append("unparsed packed-refs line: %r" % line)
                continue
            sha, name = parts[0].strip(), parts[1].strip()
            if not name.startswith("refs/heads/"):
                continue
            self.packed[name] = sha
            n += 1
        self.notes.append("parsed %s -- %d packed head(s), matched CASE-SENSITIVELY as "
                          "git does" % (path, n))

    def names(self):
        return set(self.loose) | set(self.packed)

    def fold_index(self):
        """casefolded full refname -> sorted list of the exact spellings that exist."""
        idx = {}
        for name in self.names():
            idx.setdefault(name.casefold(), set()).add(name)
        return dict((k, sorted(v)) for k, v in idx.items())


def short(name):
    return name[len("refs/heads/"):] if name.startswith("refs/heads/") else name


def full(name):
    return name if name.startswith("refs/") else "refs/heads/" + name


# ----------------------------------------------------------- canonical case ---
def canonical_case_problem(name):
    """None, or the reason `name` is not canonical-case for this repo.

    The convention, MEASURED not assumed: of 222 `softhouse/*` heads in the gerege-nbfi
    repo, the task-id prefix is UPPERCASE (`T297-`, `A2-7-`) everywhere except seven
    lowercase strays created by the very defect this file exists for, plus 21
    machine-generated `rescued-agent-*`.  So the rule is: the leading alphabetic run of
    the branch name must be uppercase.
    """
    s = short(name)
    if not s.startswith("softhouse/"):
        return None
    tail = s[len("softhouse/"):]
    for pre in CANONICAL_EXEMPT_PREFIXES:
        if tail.startswith(pre):
            return None
    lead = ""
    for ch in tail:
        if ch.isalpha():
            lead += ch
        else:
            break
    if lead and lead != lead.upper():
        return ("its task-id prefix %r is lowercase; this repo's convention is UPPERCASE "
                "(%r).  A lowercase dispatch is what created the T297/T305 shadows"
                % (lead, lead.upper()))
    return None


# ------------------------------------------------------------- the refusal ---
def shadow_conflicts(name, index):
    """Existing spellings that case-collide with `name` but are NOT `name`."""
    want = full(name)
    return [n for n in index.fold_index().get(want.casefold(), []) if n != want]


def check_dispatch(names, repo):
    """The dispatch-time guard.  Returns (exit_code, lines)."""
    out = []
    common, note = common_dir_of(repo)
    if common is None:
        return 1, ["REFUSING to answer: %s.  Whether a case-variant exists is UNVERIFIED "
                   "-- this is not a clean result." % note]
    index = RefIndex(common)
    out.append("SELECTOR: exact + case-folded lookup against loose refs under "
               "%s/refs/heads and every refs/heads entry in %s/packed-refs"
               % (common, common))
    for n in index.notes:
        out.append("          %s" % n)
    for e in index.errors:
        out.append("  UNREAD: %s" % e)
    worst = 0
    for raw in names:
        want = full(raw)
        conflicts = shadow_conflicts(want, index)
        exists = want in index.names()
        canon = canonical_case_problem(want)
        out.append("")
        out.append("  branch: %s" % short(want))
        if conflicts:
            worst = 3
            out.append("  VERDICT: REFUSED -- a case-variant already exists and "
                       "dispatching this name would SHADOW it.")
            for c in conflicts:
                out.append("    existing: %-56s loose=%s packed=%s"
                           % (short(c), (index.loose.get(c) or "-")[:9],
                              (index.packed.get(c) or "-")[:9]))
            out.append("    DO: reuse the existing spelling above VERBATIM (continue that "
                       "branch, as T308's worker did), or pick a name that differs by "
                       "more than case.  Do NOT delete or rewrite the existing branch.")
        elif exists:
            out.append("  VERDICT: OK -- this exact name already exists (loose=%s "
                       "packed=%s). Continue it; do not fork a variant."
                       % ((index.loose.get(want) or "-")[:9],
                          (index.packed.get(want) or "-")[:9]))
        elif canon:
            worst = max(worst, 3)
            out.append("  VERDICT: REFUSED -- non-canonical case: %s" % canon)
            out.append("    DO: dispatch the uppercase form instead.")
        else:
            out.append("  VERDICT: OK -- no ref, and no case-variant of one, exists under "
                       "that name.")
    return worst, out


# --------------------------------------------------------------- the sweep ---
def _ancestor(a, b, repo):
    rc, _o, _e = _run([GIT, "-C", repo, "merge-base", "--is-ancestor", a, b])
    if rc == 0:
        return True
    if rc == 1:
        return False
    return None


def sweep(repo, patterns, want_counts=None, base="main", quiet=False):
    """Returns (exit_code, lines)."""
    out = []
    common, note = common_dir_of(repo)
    if common is None:
        return 1, ["COULD NOT COMPLETE: %s.  Nothing below is a clean result." % note]
    index = RefIndex(common)

    out.append("BRANCH SWEEP -- T312 instrument (%s)" % os.path.abspath(__file__))
    out.append("SELECTOR, stated because 'not found' is a statement about the search:")
    out.append("  repo          %s  (%s)" % (os.path.abspath(repo), note))
    out.append("  patterns      %s" % " ".join(repr(p) for p in patterns))
    out.append("  matching      fnmatch on the CASE-FOLDED short name -- 'softhouse/t3*' "
               "and 'softhouse/T3*' select identically here.  `git branch --list` does "
               "NOT; that is the defect this replaces.")
    for n in index.notes:
        out.append("  storage       %s" % n)
    if index.errors:
        for e in index.errors:
            out.append("  UNREAD        %s" % e)
        out.append("  ^ the sweep is INCOMPLETE by exactly that much; do not read the "
                   "findings below as exhaustive.")

    fold = index.fold_index()
    selected = {}
    for key, spellings in fold.items():
        if any(fnmatch.fnmatch(short(s).casefold(), p.casefold())
               or fnmatch.fnmatch(s.casefold(), p.casefold())
               for s in spellings for p in patterns):
            selected[key] = spellings
    out.append("  matched       %d ref name(s) in %d case-folded group(s), out of %d "
               "head(s) present" % (sum(len(v) for v in selected.values()),
                                    len(selected), len(index.names())))

    if want_counts is None:
        want_counts = len(selected) <= 40
        if not want_counts:
            out.append("  counts        SKIPPED: %d groups is over the 40-group budget "
                       "for one `git rev-list` per name.  Re-run with --counts to force. "
                       "Nothing below claims a branch is empty." % len(selected))
    findings = {"shadow": [], "unreachable": [], "diverged": [], "split": []}
    flagged = 0

    out.append("")
    for key in sorted(selected):
        spellings = selected[key]
        group_lines = []
        resolved = {}
        stored = {}
        for name in spellings:
            lo = index.loose.get(name)
            pk = index.packed.get(name)
            rv = None
            if GIT:
                rc, o, _e = _run([GIT, "-C", repo, "rev-parse", "--verify", "--quiet",
                                  name + "^{commit}"])
                rv = o if rc == 0 and o else None
            resolved[name] = rv
            for src, val in (("loose", lo), ("packed", pk)):
                if val and not val.startswith("ref:"):
                    stored.setdefault(val, []).append("%s(%s)" % (short(name), src))
            cnt = ""
            if want_counts and rv:
                rc2, o2, _e2 = _run([GIT, "-C", repo, "rev-list", "--count",
                                     "%s..%s" % (base, name)])
                cnt = ("  ahead-of-%s=%s" % (base, o2)) if rc2 == 0 and o2.isdigit() \
                    else ("  ahead-of-%s=UNVERIFIED(rc=%s)" % (base, rc2))
            group_lines.append("    %-52s loose=%-9s packed=%-9s resolves-to=%-9s%s"
                               % (short(name), (lo or "-")[:9], (pk or "-")[:9],
                                  (rv or "UNRESOLVED")[:9], cnt))
            if lo and pk and not lo.startswith("ref:") and lo != pk:
                findings["split"].append((name, lo, pk))
        reachable = set(v for v in resolved.values() if v)
        # A value that no spelling resolves to is only a LOSS if it is not already
        # contained in one that does.  The ordinary case -- a loose ref updated while a
        # stale packed-refs entry for the SAME name survives until the next repack -- is
        # an ancestor of the resolved value, carries nothing the winner lacks, and
        # flagging it would drown the two real shadows in 500 lines of noise.
        lost, stale = [], []
        for sha, srcs in sorted(stored.items()):
            if sha in reachable:
                continue
            contained = any(_ancestor(sha, r, repo) for r in sorted(reachable))
            (stale if contained else lost).append((sha, srcs))
        flag = []
        if len(spellings) > 1:
            flag.append("CASE-SHADOW")
            findings["shadow"].append(spellings)
        if lost:
            flag.append("UNREACHABLE-VALUE")
            findings["unreachable"].append((key, lost))
        if len(stored) > 1 and GIT:
            shas = sorted(stored)
            for i in range(len(shas)):
                for j in range(i + 1, len(shas)):
                    a, b = shas[i], shas[j]
                    if _ancestor(a, b, repo) is False and _ancestor(b, a, repo) is False:
                        flag.append("DIVERGED")
                        findings["diverged"].append((key, a, b))
        if flag:
            flagged += 1
        if quiet and not flag:
            # `--quiet` prints only flagged groups.  The count of what it suppressed is
            # printed in the summary, so this is a shorter report, not a narrower one.
            continue
        out.append("  %-22s %s" % ("[" + ",".join(sorted(set(flag))) + "]" if flag
                                   else "[ok]", short(key)))
        out.extend(group_lines)
        for sha, srcs in lost:
            # The count on the HIDDEN value, not on the winning name.  "Is this branch
            # empty?" was answered about the wrong object once already; this line answers
            # it about the object that was actually hidden.
            held = ""
            if GIT:
                rc3, o3, _e3 = _run([GIT, "-C", repo, "rev-list", "--count",
                                     "%s..%s" % (base, sha)])
                held = ("  It holds %s commit(s) ahead of %s." % (o3, base)) \
                    if rc3 == 0 and o3.isdigit() else \
                    ("  Its commit count vs %s is UNVERIFIED (rc=%s) -- NOT zero."
                     % (base, rc3))
            out.append("    !! %s is STORED (%s) but NO spelling in this group resolves "
                       "to it, AND it is not an ancestor of anything that resolves -- a "
                       "live object holding work no name reaches.  It is NOT empty and it "
                       "is NOT gone.%s" % (sha[:9], ", ".join(srcs), held))
        for sha, srcs in stale:
            out.append("    -- %s (%s) is shadowed but is an ANCESTOR of the resolved "
                       "value: an ordinary stale packed entry, no work is hidden by it."
                       % (sha[:9], ", ".join(srcs)))
        for _k, a, b in [f for f in findings["diverged"] if f[0] == key]:
            out.append("    !! %s and %s have DIVERGED (neither is an ancestor of the "
                       "other) -- these are two different lines of work, not a stale "
                       "duplicate." % (a[:9], b[:9]))

    out.append("")
    hard = (findings["shadow"] or findings["unreachable"] or findings["diverged"])
    if quiet:
        out.append("  (--quiet: %d unflagged group(s) inspected and not printed; they "
                   "were LOOKED AT, not skipped)" % (len(selected) - flagged))
    out.append("FINDINGS: case-shadow groups=%d  unreachable values=%d  diverged pairs=%d"
               % (len(findings["shadow"]), len(findings["unreachable"]),
                  len(findings["diverged"])))
    out.append("  (informational, NOT a finding: %d name(s) hold different loose and "
               "packed values under the same spelling -- the ordinary stale packed entry)"
               % len(findings["split"]))
    if not hard:
        out.append("  none -- and that is a measurement over the selector printed above, "
                   "not a default.")
    else:
        out.append("  DO NOT repair these by deleting or rewriting a branch: that "
                   "destroys the evidence.  Pin each distinct value under "
                   "refs/rescue/<fire>/ first.")

    hook_ok, hook_note = hook_status(repo)
    out.append("")
    out.append("REF GUARD: %s -- %s" % ("INSTALLED" if hook_ok else "NOT INSTALLED",
                                        hook_note))
    if not hook_ok:
        out.append("  Without it, nothing PREVENTS the next shadow; this sweep only finds "
                   "shadows after the fact.  Install: python3 %s install-hook"
                   % os.path.abspath(__file__))

    if hard:
        return 3, out
    if not hook_ok:
        return 4, out
    return 0, out


# ------------------------------------------------------------------- hook ---
HOOK_TEMPLATE = """#!/bin/sh
# %s -- installed by .softhouse/bin/branch_sweep.py (T312).
# Refuses to CREATE a refs/heads/softhouse/* ref that differs from an existing ref only
# by case.  That is the precondition for a loose ref shadowing a packed one on a
# case-insensitive filesystem, and it is the whole bug of fire 20260827-230001.
# Escape hatch, for deliberate rescue work only:  SOFTHOUSE_ALLOW_CASE_SHADOW=1
exec %s %s hook "$@"
"""


def hook_path(repo):
    common, note = common_dir_of(repo)
    if common is None:
        return None, note
    return os.path.join(common, "hooks", "reference-transaction"), note


def hook_status(repo):
    path, note = hook_path(repo)
    if path is None:
        return False, "could not locate the hooks directory: %s" % note
    if not os.path.exists(path):
        return False, "no hook at %s" % path
    try:
        body = open(path).read()
    except OSError as exc:
        return False, "hook at %s is unreadable (%s)" % (path, exc)
    if HOOK_MARK not in body:
        return False, ("a reference-transaction hook exists at %s but it is NOT this "
                       "guard -- refusing to claim enforcement that is not there" % path)
    if not os.access(path, os.X_OK):
        return False, "hook at %s is present but NOT executable, so git ignores it" % path
    return True, "hook at %s carries the %s marker and is executable" % (path, HOOK_MARK)


def install_hook(repo):
    path, note = hook_path(repo)
    if path is None:
        return 1, ["COULD NOT INSTALL: %s" % note]
    ok, why = hook_status(repo)
    if ok:
        return 0, ["ref guard already installed: %s" % why]
    if os.path.exists(path):
        try:
            body = open(path).read()
        except OSError as exc:
            body = "(unreadable: %s)" % exc
        if HOOK_MARK not in body:
            return 1, ["REFUSING to overwrite the existing reference-transaction hook at "
                       "%s -- it is somebody else's and clobbering it silently is the "
                       "class of error this task exists to remove.  Merge it by hand, or "
                       "move it aside and re-run." % path,
                       "  its first line: %r" % ((body.splitlines() or [""])[0])]
    target = os.path.join(repo, ".softhouse", "bin", "branch_sweep.py")
    if not os.path.isfile(target):
        target = os.path.abspath(__file__)
    py = sys.executable or "/usr/bin/python3"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(HOOK_TEMPLATE % (HOOK_MARK, py, os.path.abspath(target)))
        os.chmod(path, 0o755)
    except OSError as exc:
        return 1, ["COULD NOT INSTALL the ref guard at %s: %s" % (path, exc)]
    return 0, ["ref guard INSTALLED at %s -> %s %s hook" % (path, py, target),
               "  it now refuses any ref CREATION under refs/heads/softhouse/ whose name "
               "differs from an existing ref only by case, for every git command."]


def run_hook(argv):
    """PURE FILESYSTEM.  Runs inside a live ref transaction; calling git here would
    re-enter the ref machinery while it holds locks."""
    state = argv[0] if argv else ""
    try:
        data = sys.stdin.read()
    except Exception:                                           # noqa: BLE001
        data = ""
    if state != "prepared":
        return 0
    if os.environ.get("SOFTHOUSE_ALLOW_CASE_SHADOW") == "1":
        return 0
    gd = os.environ.get("GIT_DIR")
    common = None
    if gd:
        gd = os.path.abspath(gd)
        cdf = os.path.join(gd, "commondir")
        if os.path.isfile(cdf):
            try:
                p = open(cdf).read().strip()
                common = os.path.abspath(p if os.path.isabs(p)
                                         else os.path.join(gd, p))
            except OSError:
                common = None
        else:
            common = gd
    if common is None:
        common, _n = common_dir_of(os.getcwd())
    if common is None:
        sys.stderr.write("softhouse ref guard: could not locate the git common dir; "
                         "REFUSING the transaction rather than passing it unchecked (a "
                         "guard that cannot look must not say 'clean').\n")
        return 1
    index = RefIndex(common)
    fold = index.fold_index()
    bad = []
    for line in data.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        old, new, ref = parts[0], parts[1], parts[2]
        if set(old) != {"0"}:
            continue                       # an update or a delete, not a creation
        # MEASURED, not assumed: the hook also fires for the packed-refs backend's own
        # transaction, and there a deletion arrives as `0000... 0000... <ref>`.  Attempt
        # 1 of this guard read that as a creation and REFUSED `git update-ref -d`
        # [.softhouse/capture/t312-branch-case-collision/red-drive.txt, step 3g].  A
        # creation has a non-zero NEW value; a zero-to-zero line is not one.
        if set(new) == {"0"}:
            continue
        if not ref.startswith("refs/heads/softhouse/"):
            continue
        # If this EXACT spelling already exists, the transaction is re-recording a ref
        # that is already there -- `git pack-refs`/`git gc` moving a loose ref into
        # packed-refs presents it as a creation.  Refusing that would break repacking in
        # a repo that already carries a shadow, and would prevent nothing: the shadow
        # predates this transaction.  This guard exists to stop a NEW precondition being
        # created, not to punish an old one.
        if ref in index.names():
            continue
        for other in fold.get(ref.casefold(), []):
            if other != ref:
                bad.append((ref, other, index.loose.get(other), index.packed.get(other)))
    if not bad:
        return 0
    w = sys.stderr.write
    w("\n*** softhouse ref guard (T312): TRANSACTION REFUSED ***\n")
    for ref, other, lo, pk in bad:
        w("  creating   %s\n" % ref)
        w("  would SHADOW an existing ref that differs only by case:\n")
        w("             %s  loose=%s packed=%s\n"
          % (other, (lo or "-")[:9], (pk or "-")[:9]))
    w("\n  On a case-insensitive filesystem the loose ref hides the packed one, git\n"
      "  resolves loose first, and the packed value becomes unreachable by name while\n"
      "  staying a live object.  That silently hid 4 commits on T297 and 8 on T305.\n"
      "  Use the EXISTING spelling verbatim, or a name differing by more than case.\n"
      "  Deliberate rescue work only: SOFTHOUSE_ALLOW_CASE_SHADOW=1\n\n")
    return 1


# ------------------------------------------------------------------- main ---
def main(argv):
    if not argv:
        argv = ["sweep"]
    cmd, rest = argv[0], argv[1:]
    if cmd == "hook":
        return run_hook(rest)
    repo = os.getcwd()
    base = "main"
    patterns, counts, ensure, names, quiet = [], None, False, [], False
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--repo" and i + 1 < len(rest):
            repo = rest[i + 1]
            i += 2
            continue
        if a == "--pattern" and i + 1 < len(rest):
            patterns.append(rest[i + 1])
            i += 2
            continue
        if a == "--base" and i + 1 < len(rest):
            base = rest[i + 1]
            i += 2
            continue
        if a == "--counts":
            counts = True
            i += 1
            continue
        if a == "--no-counts":
            counts = False
            i += 1
            continue
        if a == "--ensure-hook":
            ensure = True
            i += 1
            continue
        if a == "--quiet":
            quiet = True
            i += 1
            continue
        if a.startswith("--"):
            sys.stderr.write("unknown option %s\n" % a)
            return 64
        names.append(a)
        i += 1
    if cmd == "install-hook":
        rc, lines = install_hook(repo)
        print("\n".join(lines))
        return rc
    if cmd == "check-dispatch":
        if not names:
            sys.stderr.write("usage: branch_sweep.py check-dispatch <branch>...\n")
            return 64
        rc, lines = check_dispatch(names, repo)
        print("\n".join(lines))
        return rc
    if cmd == "sweep":
        if ensure:
            _irc, ilines = install_hook(repo)
            print("\n".join(ilines))
            print("")
        if not patterns:
            patterns = names or ["softhouse/*"]
        rc, lines = sweep(repo, patterns, counts, base, quiet)
        print("\n".join(lines))
        return rc
    sys.stderr.write(__doc__)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
