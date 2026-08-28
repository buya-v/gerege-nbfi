#!/usr/bin/env python3
"""T316 -- how many instruments under `.softhouse/` name a repo path that DOES NOT RESOLVE?

WHY THIS EXISTS. T299's follow-up FU-T299-2 reported "two" such instruments, from an incidental
observation made while doing something else, and explicitly flagged it as not a measured total.
Two is a lower bound on a population nobody had counted. This counts it.

THE SELECTOR, PRINTED BESIDE EVERY FIGURE, because a census that hides its selector is asking to
be believed rather than checked (P-66/P-70: `not found` is a statement about the SEARCH):

    corpus     : `git ls-files '.softhouse/*.py' '.softhouse/*.sh'` -- TRACKED files only.
                 Untracked files and other workers' worktrees are OUT, and that is a limit of the
                 census, not a fact about the world.
    literals   : single- or double-quoted string literals containing the substring `.softhouse/`,
                 taken verbatim. A path assembled at runtime from variables is NOT seen.
    resolution : **TRACKED CONTENT ONLY [T326]**. The literal is looked up in `git ls-files -z`
                 and in the set of directory prefixes of those paths -- AND, if that fails,
                 looked up again with trailing sentence punctuation `)}],;:.` and `…` stripped.
                 `.` and `..` segments are collapsed LEXICALLY. **THE DISK IS NEVER CONSULTED.**
                 T316 used `os.path.exists()` here, and that made the frontier -- and, once the
                 guard was wired HARD, the colour of the entire conformance bar -- a function of
                 what happened to be on the running machine's disk. See `tracked_universe()` for
                 the measurement that retired it and the two-host figures.

FOUR BUCKETS, and the last three are why this instrument is not a wolf-crier:

    RESOLVES       the literal names a TRACKED file, or a directory containing at least one
                   tracked file, verbatim or after trailing sentence punctuation is stripped.
    DEAD           the literal is a concrete path, contains no placeholder, glob, ellipsis or
                   whitespace, and is not in the tracked universe under either form. **An
                   untracked path is DEAD whether or not it exists on this machine** -- see the
                   argument recorded at `.softhouse/guards/dead-path-frontier.pin`.
    INDETERMINATE  the literal carries a format placeholder (%s, {}, $VAR, <x>), a glob
                   metacharacter, or an ellipsis. It is a TEMPLATE or a truncation, not a path.
    PROSE          the literal contains whitespace: an English sentence that quotes a path.

WHY THE PUNCTUATION ARM EXISTS, and it is a measurement rather than a preference. The first
version of this census resolved literals VERBATIM only. It reported 154 dead rows. **56 of those
154 -- 36% -- were `.softhouse/vectors)`, `.softhouse/conformance.sh}`,
`.softhouse/capture/t256-verdict-predicate/OWNER-IS-T259-NOT-T256.md.` and friends: references to
paths that EXIST, wearing a closing paren, brace or full stop glued on by the surrounding text.**
A census with a 36% false-positive rate is a census that gets pinned away in one fire, and it
would have slandered nine other tasks' committed evidence on the way. Recorded in
`evidence/50-selector-artefacts.txt`. The stripped form is only ever consulted to say YES, so it
can never turn a live reference into a dead one.

CALIBRATION IS ENFORCED, and the run ABORTS if it fails. The two references T299 named are known
positives; if the selector cannot see them it is broken, and a broken selector reporting `0 dead`
is the exact failure this whole task is about. A census that cannot find the thing that provoked
it must refuse, not report zero.

EXIT: 0 census completed; 2 calibration or corpus failure. Never conflated (P-80).
NOTE: exit 0 is NOT a verdict that the tree is clean -- this instrument COUNTS, it does not judge.
The probe line is `T316-DEADPATH-CENSUS:` and it is printed on every path that reaches a count.
Exit 2 prints NO probe line, so a refusal can never be read as a census of zero (P-84).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROBE = "T316-DEADPATH-CENSUS:"

# A quoted literal containing `.softhouse/`. Captures the literal's interior.
LITERAL_RE = re.compile(r"""(['"])((?:[^'"\\\n]|\\.)*?\.softhouse/(?:[^'"\\\n]|\\.)*?)\1""")

PLACEHOLDER_RE = re.compile(r"%[sdrf]|\{[^}]*\}|\$\{?\w+|<[a-zA-Z_]+>")
GLOB_RE = re.compile(r"[*?\[\]]")
# A truncation mark is a statement that the author elided the rest of the path. It is not a path.
ELLIPSIS_RE = re.compile(r"\.\.\.|…")

# Sentence punctuation that can trail a path inside prose or inside an f-string/format brace.
# `".softhouse/vectors)"`, `"...conformance.sh}"`, `"...OWNER-IS-T259-NOT-T256.md."` are all
# REFERENCES TO PATHS THAT EXIST, with a closing paren, brace or full stop glued on by the
# surrounding text. Calling them dead is a FALSE POSITIVE, and it was 56 of this census's first
# 154 rows -- 36% -- which would have made the whole figure worthless. Measured, not guessed:
# `evidence/50-selector-artefacts.txt`.
TRAILING_PUNCT = ")}],;:.…"

# A TRAILING LINE-RANGE CITATION: `:36`, `:36-44`. ANCHORED AT THE END and digits only, so
# `PIN.json:dec1_revision` (a path plus a JSON key) is NOT matched and stays dead. Consulted
# only to say YES, and only after the verbatim and punctuation forms have both failed --
# see `resolves()` for the argument and the measurement that provoked it [T326].
CITATION_RE = re.compile(r":\d+(?:-\d+)?$")

# The two references FU-T299-2 names. The selector must see both, or the census aborts.
CALIBRATION = [
    (".softhouse/capture/t290-review-t271/guard_rvpa_floor_t290.py",
     ".softhouse/capture/t256-verdict-predicate/run_rvpa_over_targets.py"),
    (".softhouse/capture/t290-review-t271/red/drive-red-t290.py",
     ".softhouse/capture/t256-verdict-predicate/run_rvpa_over_targets.py"),
]


def repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: no .git ancestor", file=sys.stderr)
    raise SystemExit(2)


def corpus(root: Path):
    proc = subprocess.run(
        ["git", "ls-files", ".softhouse/*.py", ".softhouse/*.sh"],
        cwd=str(root), capture_output=True, text=True)
    # git ls-files exits 0 on no-match too; a non-zero status is a real error (P-81).
    if proc.returncode != 0:
        print("ERROR: git ls-files exited %d: %s" % (proc.returncode, proc.stderr.strip()),
              file=sys.stderr)
        raise SystemExit(2)
    files = [f for f in proc.stdout.splitlines() if f.strip()]
    if not files:
        print("ERROR: the corpus is EMPTY. That is a selector failure, not a clean tree.",
              file=sys.stderr)
        raise SystemExit(2)
    return files


def classify(literal: str):
    # A literal carrying whitespace is an English sentence that happens to quote a path, not a
    # path. `".softhouse/RESUME.md was not rewritten by this fire"` is a message string. Counting
    # it as a dead path would manufacture 100+ findings out of the program's own prose, and a
    # census that cries wolf on its first run is a census that gets pinned away (T299).
    if re.search(r"\s", literal):
        return "PROSE"
    if ELLIPSIS_RE.search(literal):
        return "INDETERMINATE"
    if PLACEHOLDER_RE.search(literal) or GLOB_RE.search(literal):
        return "INDETERMINATE"
    return "CONCRETE"


def tracked_universe(root: Path):
    """T326 -- THE RESOLUTION UNIVERSE IS `git ls-files`, NEVER THE DISK.

    Returns `(files, dirs)`: the set of tracked repo-relative paths, and the set of every
    directory prefix of a tracked path. A literal resolves iff it is in one of those two sets.

    WHY THIS REPLACED `os.path.exists`. The first version of this census resolved literals with
    `os.path.exists(root / literal)`. That makes the census -- and therefore T316's frontier pin,
    and therefore the colour of the whole conformance bar once the guard is wired HARD -- a
    function of WHAT HAPPENS TO BE ON SOMEBODY'S DISK. Measured, not argued, on ONE commit:

        `.softhouse/toolchain`   exists in Buyan's main checkout, is `.gitignore`d
                                 (`.gitignore:6`), has ZERO tracked files, and does not exist in
                                 a fresh worktree.  23 pin rows name it.
        `.softhouse/capture/t74-multiplesof/T82-guard-proofs/scratch`
                                 is untracked RUN RESIDUE left on the main checkout by an earlier
                                 run.  1 more pin row names it.

        => the SAME COMMIT yields frontier rows=102 in a fresh worktree and rows=78 in the main
           checkout.  [VERIFIED: .softhouse/capture/t326-frontier-host-state/evidence/]

    That is fatal here and not merely untidy, because this program is driven by TWO fires -- a
    launchd fire on Buyan's Mac and a cloud fire that never runs on that host -- and the failure
    presents as `exit 2, no probe line`, which a driver is trained by P-84 to read as a MONEY
    NON-NEGOTIABLE VIOLATION. A host-state defect wearing the costume of a float violation is the
    worst available failure mode. T256/T298 already spent themselves on this class and the repo
    carries `guard_no_host_state_in_lint_corpus` for it.

    THE RULE THIS ENCODES: if regenerating a pin in a worktree, on a fresh clone, or on another
    host yields a different set, IT IS NOT A PIN -- it is a snapshot of somebody's disk.

    WHY THE INDEX (`git ls-files`) AND NOT `git ls-tree -r HEAD`. The index is what a commit is
    about to be. On any clean checkout, clone or worktree the two are identical, so the
    host-independence property is unaffected; but a worker who adds a new instrument AND the file
    it references in one change should be green before committing, not after. Using HEAD would
    grade the previous commit. Either way, and this is the load-bearing half, NEITHER reads
    untracked or ignored paths.

    WHAT THIS DELIBERATELY GIVES UP. A tracked directory whose files are all deleted from the
    working tree still resolves, and a legitimately generated-at-runtime output never resolves.
    Both are accepted: see the DEAD bucket's documented meaning -- a row is a SMELL to be
    inspected once and then repaired or pinned WITH ITS REASON, never an accusation.
    """
    proc = subprocess.run(["git", "ls-files", "-z"],
                          cwd=str(root), capture_output=True, text=True)
    if proc.returncode != 0:
        print("ERROR: git ls-files -z exited %d: %s" % (proc.returncode, proc.stderr.strip()),
              file=sys.stderr)
        raise SystemExit(2)
    files = {f for f in proc.stdout.split("\0") if f}
    if not files:
        # An empty tracked universe is a failed READ, never a repository with no files. Refusing
        # here matters more than anywhere else in this instrument: an empty universe would make
        # EVERY literal dead and the census would report a spectacular, entirely false finding.
        print("ERROR: the tracked universe is EMPTY. That is a selector failure, not a repo with",
              file=sys.stderr)
        print("ERROR: no tracked files. REFUSING (exit 2) rather than calling every path dead.",
              file=sys.stderr)
        raise SystemExit(2)
    dirs = set()
    for f in files:
        p = f
        while "/" in p:
            p = p.rsplit("/", 1)[0]
            dirs.add(p)
    return files, dirs


def _lexical_norm(path: str) -> str:
    """Collapse `.`/`..`/`//` LEXICALLY -- os.path.normpath touches no filesystem. A literal such
    as `.softhouse/capture/t274-attestation-failopen/instruments/../evidence/wrap` is a real
    reference to `.softhouse/capture/t274-attestation-failopen/evidence/wrap`; without this it
    would be reported dead purely because the tracked universe is a set of strings while
    `os.path.exists` walked directories. Returns "" if the path escapes the repo root, which
    makes it unresolvable -- correct, since the universe only contains paths inside the root.
    """
    n = os.path.normpath(path)
    if n == "." or n.startswith("..") or n.startswith("/"):
        return ""
    return n


def resolves(files, dirs, path: str) -> bool:
    """A literal RESOLVES if it names a TRACKED file, or a directory containing at least one
    tracked file: verbatim, or after trailing sentence punctuation is stripped, or after a
    trailing LINE-RANGE CITATION is stripped.

    The punctuation arm is unchanged from T316 and is not laxity: `".softhouse/vectors)"` is a
    reference to a directory that exists, wearing a closing paren from the sentence around it.
    Reporting it dead is a false positive, and false positives are how a census gets pinned away
    (it was 56 of the first 154 rows). The stripped form is only ever consulted to say YES, so it
    can never turn a live reference into a dead one.

    THE CITATION ARM [T326] IS THE SAME ARGUMENT, MEASURED THE SAME WAY. T272's merge landed
    `"...t254-harness-portability/REVIEW.md:36-44)"` inside a prose `echo`, and the frontier
    guard reported it as a NEW DEAD PATH. The file it names IS TRACKED [VERIFIED:
    `git ls-files .softhouse/reviews/t254-harness-portability/` lists `REVIEW.md`]; what the
    census could not see past was a `:36-44` LINE-RANGE CITATION -- the exact shape T326 spent
    its day repairing under P-86. The guard's own printed rule is "a '+' row is a NEW site:
    REPAIR it rather than pinning it", and pinning a false positive is how a census decays into
    the wolf-crier its own header warns about, so this is repaired in the SELECTOR rather than
    excused in the pin.

    WHY THIS CANNOT WEAKEN THE CENSUS, stated as a property and not as a hope. Every arm here is
    consulted ONLY AFTER the previous one has failed, and every arm can only answer YES. A
    literal is still DEAD unless some form of it names something in the TRACKED universe -- the
    disk is not consulted in any arm -- so no genuinely dead path can be made to resolve by
    stripping a suffix: the remaining prefix must itself be a tracked file or a tracked
    directory. The suffix pattern is anchored and deliberately narrow: `:N` or `:N-M` at the very
    END, digits only. The frontier's existing `PIN.json` row -- a path plus a JSON KEY rather
    than a line number -- does NOT match and stays dead, which is the control that shows the arm
    is not a blanket "strip anything after a colon". That row is named in the pin; it is not
    quoted here, because this census counts quoted literals and quoting it in its own source
    would ADD A ROW TO THE FRONTIER FROM THIS FILE -- which is precisely what happened on the
    first attempt at this comment, and the guard caught it on the next run. Repaired rather than
    pinned, per the rule the guard prints.
    """
    n = _lexical_norm(path)
    if n and (n in files or n in dirs):
        return True
    stripped = path.rstrip(TRAILING_PUNCT)
    if stripped and stripped != path:
        s = _lexical_norm(stripped)
        if s and (s in files or s in dirs):
            return True
    # THE CITATION ARM. Applied to the punctuation-stripped form, because a citation in prose
    # arrives wearing both: `REVIEW.md:36-44)`.
    base = stripped if stripped else path
    m = CITATION_RE.search(base)
    if not m:
        return False
    c = _lexical_norm(base[: m.start()])
    return bool(c) and (c in files or c in dirs)


def scan(root: Path, rel: str, files, dirs):
    """Return (resolves, dead, indeterminate) lists of literals named by this file."""
    try:
        text = (root / rel).read_text(errors="replace")
    except OSError as exc:
        print("ERROR: unreadable corpus member %s: %s" % (rel, exc), file=sys.stderr)
        raise SystemExit(2)
    resolves_, dead, indet, prose = [], [], [], []
    for m in LITERAL_RE.finditer(text):
        lit = m.group(2)
        # Trim to the `.softhouse/`-rooted tail: a literal may carry a prefix like `$REPO_ROOT/`.
        idx = lit.find(".softhouse/")
        path = lit[idx:]
        kind = classify(path)
        if kind == "PROSE":
            prose.append(path)
        elif kind == "INDETERMINATE":
            indet.append(path)
        elif resolves(files, dirs, path):
            resolves_.append(path)
        else:
            dead.append(path)
    return resolves_, dead, indet, prose


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="census of dead `.softhouse/` path references")
    ap.add_argument("--json", default=None,
                    help="write the machine-readable census here. OMIT IT AND NOTHING IS "
                         "WRITTEN -- the bare run is read-only by construction.")
    args = ap.parse_args(argv)

    root = repo_root()
    files = corpus(root)
    # T326: the resolution universe. TRACKED CONTENT ONLY -- see tracked_universe.__doc__.
    tracked_files, tracked_dirs = tracked_universe(root)

    per_file = {}
    for rel in files:
        r, d, i, pr = scan(root, rel, tracked_files, tracked_dirs)
        if r or d or i or pr:
            per_file[rel] = {"resolves": sorted(set(r)),
                             "dead": sorted(set(d)),
                             "indeterminate": sorted(set(i)),
                             "prose": sorted(set(pr))}

    # ---- CALIBRATION, enforced -------------------------------------------------------------
    missed = []
    for holder, needle in CALIBRATION:
        got = per_file.get(holder, {}).get("dead", [])
        if needle not in got:
            missed.append((holder, needle, got))
    if missed:
        print("ABORT(2): the selector did not see its own known positives. It is BROKEN, and a")
        print("broken selector reporting `0 dead` is the defect this task exists to find.")
        for holder, needle, got in missed:
            print("  missed: %s" % needle)
            print("      in: %s" % holder)
            print("    dead literals actually seen there: %s" % (got or "(none)"))
        print("NO PROBE LINE IS PRINTED. This is a refusal, not a census of zero (P-84).",
              file=sys.stderr)
        return 2

    dead_files = sorted(f for f, v in per_file.items() if v["dead"])
    dead_occ = sum(len(per_file[f]["dead"]) for f in dead_files)
    indet_files = sorted(f for f, v in per_file.items() if v["indeterminate"])
    resolving_occ = sum(len(v["resolves"]) for v in per_file.values())
    indet_occ = sum(len(v["indeterminate"]) for v in per_file.values())
    prose_occ = sum(len(v["prose"]) for v in per_file.values())

    print("T316 -- dead repo-path references among tracked `.softhouse/` instruments")
    print("=" * 88)
    print("SELECTOR (P-66: `not found` is a statement about the search)")
    print("  corpus     : git ls-files '.softhouse/*.py' '.softhouse/*.sh'   -> %d tracked file(s)"
          % len(files))
    print("  literals   : quoted strings containing `.softhouse/`, trimmed to that root")
    print("  regex      : %s" % LITERAL_RE.pattern.replace("\n", ""))
    print("  resolution : TRACKED CONTENT ONLY [T326] -- membership in `git ls-files -z`")
    print("               (%d path(s)) or in the set of their directory prefixes (%d)."
          % (len(tracked_files), len(tracked_dirs)))
    print("               NOT os.path.exists. THE DISK IS NEVER CONSULTED, so this census is a")
    print("               property of the COMMIT and not of the machine, the checkout, or what a")
    print("               previous run left lying about. `.` / `..` are collapsed LEXICALLY.")
    print("  EXCLUDED   : templates (placeholder %s/{}/$VAR/<x>) and globs -> INDETERMINATE;")
    print("               literals containing WHITESPACE -> PROSE (a message that quotes a path).")
    print("               Both counted separately, NEVER added to the DEAD figure.")
    print("  BLIND TO   : untracked files as CORPUS; paths assembled from variables at runtime.")
    print("  DELIBERATE : an UNTRACKED path -- `.gitignore`d build output, a runtime-materialised")
    print("               toolchain, another run's scratch -- is DEAD, present on disk or not.")
    print("               Same answer on every host: that is the whole point [T326].")
    print()
    print("CALIBRATION: both FU-T299-2 known positives were seen as DEAD by this selector.")
    print()
    print("COUNTS (both terms printed -- P-67)")
    print("  files naming any `.softhouse/` literal : %d" % len(per_file))
    print("  occurrences that RESOLVE               : %d" % resolving_occ)
    print("  occurrences that are INDETERMINATE     : %d  (in %d file(s))"
          % (indet_occ, len(indet_files)))
    print("  occurrences that are PROSE             : %d" % prose_occ)
    print("  occurrences that are DEAD              : %d  (in %d file(s))"
          % (dead_occ, len(dead_files)))
    print()
    print("THE %d FILE(S) NAMING A DEAD CONCRETE PATH" % len(dead_files))
    print("-" * 88)
    for f in dead_files:
        print("  %s" % f)
        for d in per_file[f]["dead"]:
            print("      -> %s" % d)

    # THE BARE RUN WRITES NOTHING. T299 fixed exactly this defect in the T238 linter -- an
    # instrument whose DEFAULT destination is a tracked file dirties the tree of anyone who runs
    # it to debug it, and the person who runs it bare is precisely the person debugging it. So the
    # JSON is OPT-IN: no `--json`, no write, and a caller (the guard) passes a scratch path.
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(
            {"corpusFiles": len(files), "deadFiles": dead_files,
             "deadOccurrences": dead_occ, "resolvingOccurrences": resolving_occ,
             "indeterminateOccurrences": indet_occ, "proseOccurrences": prose_occ,
             "perFile": {f: per_file[f] for f in dead_files}}, indent=2, sort_keys=True) + "\n")
        print()
        print("  JSON written to %s" % out)

    print()
    print("%s corpus=%d deadFiles=%d deadOccurrences=%d resolving=%d indeterminate=%d prose=%d"
          % (PROBE, len(files), len(dead_files), dead_occ, resolving_occ, indet_occ, prose_occ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
