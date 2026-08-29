#!/usr/bin/env python3
"""
T466 -- WORKING-TREE READ CENSUS, RE-DERIVED.  Answers C-T459-4.

THE CLAIM UNDER TEST is the sentence shipped in the harness: "T454's census counted 27
executable sites in this file that touch this host's filesystem at a $REPO_ROOT path, and 26
of them name a path containing a character this volume folds".  T459 measured 67 and called
T454's direction confirmed but understated.  This probe re-derives it and, more usefully,
PRINTS ITS SELECTOR AND ITS MEMBER SET, because a bare cardinal is exactly what rotted here.

THREE NESTED SELECTORS ARE REPORTED, widest last, so a reader can see which one produces which
number instead of guessing which one an earlier author meant:

  S1  DIRECT   -- a non-comment line that spells the root variable itself.
  S2  +ANCHOR  -- S1, plus a non-comment line that spells a repository-relative path anchored
                  at the program directory (whether or not the root variable is on that line);
                  these are the strings later joined to the root, and they read the same tree.
  S3  +VARS    -- S2, plus a non-comment line that uses a local variable which was, somewhere
                  in this file, assigned from the root variable.  This is the population that
                  ACTUALLY touches this host's filesystem through a $REPO_ROOT path, and it is
                  the honest answer to the sentence's own words.

FOLDABILITY is then measured over each set: a site is FOLDABLE when the path text on that line
contains any image confirmed by the fold census beside this file.  Every path under the
program's own directory contains the 's' of its name, so the expected answer is "nearly all",
and that is checked rather than asserted.

The file to read arrives as argv[1]; the fold images arrive on stdin, one per line, from the
fold census -- neither is spelled here.  (guard_dead_path_frontier.)
"""
import re
import sys


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: read-census.py <harness-file>  (fold images on stdin)\n")
        return 3
    images = [ln.rstrip("\n") for ln in sys.stdin if ln.strip()]
    if not images:
        sys.stderr.write("REFUSED: no fold images on stdin. Foldability would then measure "
                         "zero for every site, which is a fact about this pipe.\n")
        return 3
    with open(sys.argv[1], "r", encoding="utf-8", errors="surrogateescape") as fh:
        raw = fh.read().split("\n")
    if len(raw) < 100:
        sys.stderr.write("REFUSED: harness file has %d lines. Not the file this is about.\n"
                         % len(raw))
        return 3

    code = [(i + 1, ln) for i, ln in enumerate(raw)
            if ln.strip() and not ln.lstrip().startswith("#")]
    print("SELECTOR CORPUS: %d lines in the file, %d of them NON-COMMENT and non-blank."
          % (len(raw), len(code)))

    ROOT = "REPO_" + "ROOT"
    PROG = "." + "soft" + "house" + "/"

    # CALIBRATION (P-72). The root variable must be findable at all, or every count below is
    # a statement about this regex and not about the file.
    if not [1 for _, ln in code if ROOT in ln]:
        sys.stderr.write("REFUSED: CALIBRATION FAILED -- the root variable appears on NO "
                         "non-comment line. The reader is broken, not the file.\n")
        return 3

    s1 = [(n, ln) for n, ln in code if ROOT in ln]

    # Locals assigned from the root variable anywhere in the file, e.g.  local x="$REPO_ROOT/..."
    assign = re.compile(r"""(?:^|\s|\()(?:local\s+|declare\s+)?([A-Za-z_][A-Za-z_0-9]*)=""")
    derived = set()
    for n, ln in s1:
        ref = "$" + ROOT
        if ref not in ln:
            continue
        m = assign.search(ln)
        if m and m.end() <= ln.index(ref):
            derived.add(m.group(1))
    derived.discard(ROOT)
    print("LOCALS ASSIGNED FROM THE ROOT VARIABLE: %d -- %s"
          % (len(derived), ", ".join(sorted(derived)) or "<none>"))

    s2 = list(s1)
    seen = set(n for n, _ in s1)
    for n, ln in code:
        if n not in seen and PROG in ln:
            s2.append((n, ln))
            seen.add(n)

    s3 = list(s2)
    varuse = [re.compile(r"\$\{?" + re.escape(v) + r"\b") for v in sorted(derived)]
    for n, ln in code:
        if n in seen:
            continue
        if any(p.search(ln) for p in varuse):
            s3.append((n, ln))
            seen.add(n)

    def foldable(sites):
        return [(n, ln) for n, ln in sites if any(im in ln for im in images)]

    # S0 is NARROWER than S1 and is the reading closest to the shipped sentence's own words --
    # "executable sites that TOUCH this host's filesystem". A line that merely NAMES a path
    # inside a `warn` string is in S1 and is not a filesystem touch, so S1 over-reads; S0
    # requires the path to be the operand of something that opens, enters, or searches it.
    TOUCH = re.compile(
        r"(?:\bcd\s|\bpushd\s|\bsource\s|^\s*\.\s|\bfind\s|\bgrep\b|\bsed\s|\bawk\s|\bcat\s"
        r"|\bstat\s|\bchmod\s|\bmkdir\s|\brm\s|\bcp\s|\bmv\s|\btee\s|\bls\s|\bwc\s|\bcmp\s"
        r"|\bpython3\s|\bbash\s|\bgo\s|\bgit\s|\bhash-object\b|\bls-files\b|\bdiff-index\b"
        r"|\[\s*-[a-z]\s|\btest\s+-[a-z]\s|<\s*\"|>\s*\"|>>\s*\")")
    s0 = [(n, ln) for n, ln in s1 if TOUCH.search(ln)]

    for name, sites in (("S0 TOUCH  ", s0), ("S1 DIRECT ", s1),
                        ("S2 +ANCHOR", s2), ("S3 +VARS  ", s3)):
        f = foldable(sites)
        print("%s : %3d sites, %3d of them FOLDABLE (path text carries a confirmed fold "
              "image), %3d not." % (name, len(sites), len(f), len(sites) - len(f)))

    print("")
    print("S3 MEMBER SET (line numbers, and they are a fact about THIS tree only -- the "
          "standing remedy in this program is to cite by name, never by line):")
    for n, ln in sorted(s3):
        mark = "FOLDABLE" if any(im in ln for im in images) else "plain   "
        print("  %5d %s  %s" % (n, mark, ln.strip()[:104]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
