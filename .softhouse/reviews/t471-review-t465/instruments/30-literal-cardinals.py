#!/usr/bin/env python3
"""T471 -- re-measure CLAIM 3's two cardinals against the TREES, not against a transcript.

    "17 rows = 43 quoted literals; 43 removed, 0 remain."

A ROW is a (file, literal) pair. An OCCURRENCE is one match of the quoted-literal selector. The
two cardinals are different things and this program has had both rot inside 24 h, so both are
counted here from `git show`n bytes.

SELECTOR, printed with every figure (P-66/P-70):
  corpus   : `git ls-files '<S>/*.py' '<S>/*.sh'` at the rev -- exactly the census's own corpus.
  literals : the census's own LITERAL_RE, imported by VALUE from the census file at the rev so
             this instrument cannot drift from the thing it is grading.
  subject  : a literal whose interior contains the assembled lock path.

NO REAL REPO PATH IS SPELT AS A LITERAL HERE (P-103): the dot-directory and the lock file name
are assembled from parts at run time, which is the same remedy the work under review applied.

EXIT 0 measured; 2 refusal. Probe line: T471-LITERALS:
"""
import argparse
import re
import subprocess
import sys

PROBE = "T471-LITERALS:"

DOT = "." + "softhouse"                 # assembled, never spelt
LOCKNAME = "LOCK"
LOCKPATH = DOT + "/" + LOCKNAME


def git(args, cwd):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if p.returncode != 0:
        print("ERROR: git %s -> %d: %s" % (" ".join(args), p.returncode, p.stderr.strip()),
              file=sys.stderr)
        raise SystemExit(2)
    return p.stdout


def load_literal_re(repo, rev):
    """Import the census's selector BY VALUE from the rev under test."""
    src = git(["show", "%s:%s/capture/t316-dead-path-guards/census_dead_paths.py" % (rev, DOT)],
              repo)
    m = re.search(r"^LITERAL_RE = re\.compile\((.*?)\)\n", src, re.S | re.M)
    if not m:
        print("ERROR: could not read LITERAL_RE out of the census at %s. REFUSING." % rev,
              file=sys.stderr)
        raise SystemExit(2)
    ns = {"re": re}
    exec("LITERAL_RE = re.compile(%s)" % m.group(1), ns)
    return ns["LITERAL_RE"], m.group(1).strip()


def measure(repo, rev):
    lit_re, lit_src = load_literal_re(repo, rev)
    # `git ls-files` reads the INDEX, which is the caller's checkout, not the rev. Reading the
    # corpus out of the REV's own tree is what makes this a measurement of the commit. The
    # pathspecs are byte-identical to the census's.
    # `git ls-tree` takes a literal prefix; the two suffixes are applied here, which is exactly
    # what the census's two pathspecs mean (git pathspec `*` crosses `/`).
    files = [f for f in git(["ls-tree", "-r", "--name-only", rev, "--", DOT + "/"],
                            repo).splitlines()
             if f.strip() and (f.endswith(".py") or f.endswith(".sh"))]
    if not files:
        print("ERROR: empty corpus at %s -- a selector failure, not a clean tree." % rev,
              file=sys.stderr)
        raise SystemExit(2)
    per_file = {}
    total_occ = 0
    for f in files:
        blob = git(["show", "%s:%s" % (rev, f)], repo)
        occ = [m.group(2) for m in lit_re.finditer(blob) if LOCKPATH in m.group(2)]
        if occ:
            per_file[f] = occ
            total_occ += len(occ)
    rows = set()
    for f, occ in per_file.items():
        for o in occ:
            rows.add((f, o))
    return files, per_file, total_occ, rows, lit_src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    a = ap.parse_args()

    bfiles, bper, bocc, brows, lit_src = measure(a.repo, a.base)
    hfiles, hper, hocc, hrows, _ = measure(a.repo, a.head)

    print("selector corpus  : git ls-files '%s/*.py' '%s/*.sh'" % (DOT, DOT))
    print("selector literals: %s" % lit_src)
    print("subject          : literal interior contains the assembled lock path")
    print()
    print("BASE %s  corpusFiles=%d  filesWithLockLiteral=%d  occurrences=%d  distinctRows=%d"
          % (a.base, len(bfiles), len(bper), bocc, len(brows)))
    for f in sorted(bper):
        vals = sorted(set(bper[f]))
        print("    %-72s occ=%d distinct=%d" % (f, len(bper[f]), len(vals)))
        for v in vals:
            print("        literal: %r" % v)
    print()
    print("HEAD %s  corpusFiles=%d  filesWithLockLiteral=%d  occurrences=%d  distinctRows=%d"
          % (a.head, len(hfiles), len(hper), hocc, len(hrows)))
    for f in sorted(hper):
        print("    %-72s occ=%d" % (f, len(hper[f])))
    print()
    removed = bocc - hocc
    print("%s baseFiles=%d baseOccurrences=%d baseDistinctRows=%d "
          "headFiles=%d headOccurrences=%d removed=%d remain=%d"
          % (PROBE, len(bper), bocc, len(brows), len(hper), hocc, removed, hocc))


if __name__ == "__main__":
    main()
