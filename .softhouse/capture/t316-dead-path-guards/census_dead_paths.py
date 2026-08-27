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
    resolution : the literal is joined to the repo root and tested with os.path.exists(), which
                 follows symlinks and accepts directories -- AND, if that fails, tested again
                 with trailing sentence punctuation `)}],;:.` and `…` stripped.

FOUR BUCKETS, and the last three are why this instrument is not a wolf-crier:

    RESOLVES       the literal names something that is on disk, verbatim or after trailing
                   sentence punctuation is stripped.
    DEAD           the literal is a concrete path, contains no placeholder, glob, ellipsis or
                   whitespace, and nothing is there under either form.
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


def resolves(root: Path, path: str) -> bool:
    """A literal RESOLVES if it names something on disk EITHER verbatim OR after trailing
    sentence punctuation is stripped. The second arm is not laxity: `".softhouse/vectors)"` is a
    reference to a directory that EXISTS, wearing a closing paren from the sentence around it.
    Reporting it dead is a false positive, and false positives are how a census gets pinned away.
    The stripped form is only ever used to say YES; it can never turn a live path into a dead one.
    """
    if (root / path).exists():
        return True
    stripped = path.rstrip(TRAILING_PUNCT)
    return bool(stripped) and stripped != path and (root / stripped).exists()


def scan(root: Path, rel: str):
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
        elif resolves(root, path):
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

    per_file = {}
    for rel in files:
        r, d, i, pr = scan(root, rel)
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
    print("  resolution : os.path.exists(repo_root / literal)")
    print("  EXCLUDED   : templates (placeholder %s/{}/$VAR/<x>) and globs -> INDETERMINATE;")
    print("               literals containing WHITESPACE -> PROSE (a message that quotes a path).")
    print("               Both counted separately, NEVER added to the DEAD figure.")
    print("  BLIND TO   : untracked files; paths assembled from variables at runtime")
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
