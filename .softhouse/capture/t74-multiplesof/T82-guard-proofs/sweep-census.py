#!/usr/bin/env python3
"""T82 — SHAPE-INDEPENDENT sweep for restatements of the parity-vector census.

    python3 sweep-census.py <repo-root> [--full]

WHY THIS EXISTS. T82's first sweep used two regexes, both written against the BANNER's phrasing:

    (1)  36 … (parity|promoted|golden) … vector
    (2)  `capture-prod3b-raw.json` (11)

A fourth copy of the same census survived both — in a file T82 had edited twice — because it renders
the census as a **markdown table** and says "36 parity + 4 refusal." with no following word
"vector". Same claim, different shape. T87 found it (F-3). That is P-12 landing inside the task
assigned to close P-12, and the fix is not a better sentence template: it is to stop searching for
sentences.

THE DESIGN PROBLEM, stated because it is the whole difficulty. A sweep has to be BROAD enough not to
miss a rendering nobody predicted, and NARROW enough that a human can classify every hit. A bare
`grep -n '\\b36\\b'` over these trees returns ~19,000 line-hits — complete, and useless, because
`36` is also a principal, a period count, a line number and a month. Those two pressures are
resolved by SPLITTING the search space rather than by weakening the pattern:

  TIER 1 — PROSE (.md, and the JSON/`.softhouse` files that carry human-written `note` /
           `description` strings). A census claim is a CLAIM, and a claim lives in prose. Here the
           net is the bare NUMERAL, with NO context word required and NO phrasing assumed: every
           line containing `36` or `42`. This is the tier that would have caught F-3, whose line
           reads "36 parity + 4 refusal." and matches no sentence template.

  TIER 2 — EVERYTHING ELSE (captures, transcripts, generated data, source). Here a bare numeral is
           unclassifiable, so two SHAPE-FREE structural nets are used instead:
             PASS B  a `capture-prod3*-raw.json` name near a small integer in ANY delimiter —
                     `(11)`, `| 11 |`, `: 11`, `= 11` — catching an enumeration with no total;
             PASS C  a corpus word (parity/promoted/vector/corpus/store/refusal) within 40 chars of
                     any integer 30-49, in EITHER order.

WHAT THIS SWEEP STRUCTURALLY CANNOT FIND — stated because an undocumented blind spot is how a fifth
copy survives, and this list is the deliverable as much as the hits are:

  1. A census that states NO number at all ("every vector in the store derives from pass 3b or
     later"). No numeric sweep can see it.
  2. A census whose numbers are SPELLED ("thirty-six parity vectors").
  3. A census in TIER 2 that uses neither a `capture-prod3*` artefact name nor a corpus word — e.g.
     a bare table of counts under a heading.
  4. A census in a TIER 2 line longer than the reported cap, in the two context passes only.
  5. A census outside the searched trees entirely (git history, commit messages, the `.claude/`
     skill definitions, anything untracked).
  6. A count that is CORRECT-BUT-STALE-IN-MEANING — e.g. "42" describing something else that
     happens to be 42 today. Classification, not the regex, is what catches that.
"""
import os
import re
import sys

TREES = [".softhouse/capture", ".softhouse/handoff", ".softhouse/reviews", ".softhouse/vectors",
         ".softhouse/patterns.md", ".softhouse/gates.md", ".softhouse/program.json",
         ".softhouse/tasks.json", ".softhouse/RESUME.md", "docs", "CLAUDE.md"]

SKIP_DIRS = {".git", "scratch", "__pycache__", "node_modules"}

# N-2 (T87). This sweep lives inside one of the trees it scans, so a re-run was scanning its OWN
# previous output — SWEEP.txt and the guard-proof TRANSCRIPT.txt — and reporting the hits it had
# just written as if they were findings. TIER 1 was unaffected (neither file is prose by the
# is_prose() rule) but the TIER 2 counts drifted upward on every run, which is exactly the kind of
# number that quietly stops meaning anything. Excluded by name, and the exclusion is REPORTED.
SELF_OUTPUTS = {"SWEEP.txt", "TRANSCRIPT.txt"}

# TIER 1 = files where a human-written CLAIM can live.
PROSE_SUFFIX = (".md",)
PROSE_EXTRA = ("program.json", "tasks.json", "PIN.json", "capabilities.json", "RESUME.md")

LONG_LINE = 4000

NUMERAL = re.compile(r"(?<![0-9.])(36|42)(?![0-9.])")
PASS_B = re.compile(r"capture-prod3[a-z]?-raw\.json[^0-9\n]{0,12}([0-9]{1,2})\b")
CONCEPT = ("parity", "promoted", "vector", "corpus", "store", "refusal")
PASS_C = re.compile(r"(?:parity|promoted|vector|corpus|store|refusal)[^0-9\n]{0,40}(3[0-9]|4[0-9])\b"
                    r"|\b(3[0-9]|4[0-9])[^0-9\n]{0,40}(?:parity|promoted|vector|corpus|store|refusal)",
                    re.I)


def files(root):
    for t in TREES:
        p = os.path.join(root, t)
        if os.path.isfile(p):
            yield p
            continue
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for f in filenames:
                if f in SELF_OUTPUTS and "T82-guard-proofs" in dirpath:
                    continue
                yield os.path.join(dirpath, f)


def is_prose(rel):
    return rel.endswith(PROSE_SUFFIX) or os.path.basename(rel) in PROSE_EXTRA


def main(root, full=False):
    root = os.path.abspath(root)
    t1, b, c = [], [], []
    prose_files = other_files = skipped_long = 0

    for path in files(root):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except (OSError, IsADirectoryError):
            continue
        rel = os.path.relpath(path, root)
        prose = is_prose(rel)
        prose_files += prose
        other_files += not prose
        for n, line in enumerate(lines, 1):
            s = line.strip()
            if prose and ("36" in line or "42" in line) and NUMERAL.search(line):
                t1.append((rel, n, s))
            if len(line) > LONG_LINE:
                skipped_long += 1
                continue
            if "capture-prod3" in line and PASS_B.search(line):
                b.append((rel, n, s))
            if any(w in line.lower() for w in CONCEPT) and PASS_C.search(line):
                c.append((rel, n, s))

    print("=== T82 shape-independent census sweep ===")
    print("prose files (TIER 1, bare-numeral net): %d" % prose_files)
    print("other files (TIER 2, structural nets):  %d" % other_files)
    print("lines over %d chars skipped by TIER 2 only: %d" % (LONG_LINE, skipped_long))
    print()
    print("TIER 1 — every prose line containing 36 or 42, no phrasing assumed: %d" % len(t1))
    print("TIER 2 — PASS B (artefact name near an integer, any delimiter):     %d" % len(b))
    print("TIER 2 — PASS C (corpus word within 40 chars of 30-49, either order): %d" % len(c))
    print()
    print("--- TIER 1 hits, grouped by file (classify every one) ---")
    per = {}
    for rel, n, s in t1:
        per.setdefault(rel, []).append((n, s))
    for rel in sorted(per):
        print("\n%s  (%d)" % (rel, len(per[rel])))
        for n, s in sorted(per[rel]):
            print("  %5d  %s" % (n, s[:145]))
    # N-3 (T87). PASS C is the widest net here and its hits were COUNTED but never printed, even
    # under --full — a number with no classifiable population behind it, which is close to the
    # defect class this whole task removed. Both TIER 2 passes now print in full under --full, and
    # PASS C's per-file distribution prints ALWAYS so the count is never bare.
    print()
    print("--- TIER 2 PASS C, per file (the count is never printed without its population) ---")
    perc = {}
    for rel, n, s in c:
        perc.setdefault(rel, []).append(n)
    for rel in sorted(perc, key=lambda r: (-len(perc[r]), r)):
        print("  %-70s %d" % (rel, len(perc[rel])))

    if full:
        print("\n--- TIER 2 PASS B hits (%d) ---" % len(b))
        for rel, n, s in sorted(b):
            print("  %s:%d  %s" % (rel, n, s[:145]))
        print("\n--- TIER 2 PASS C hits (%d) ---" % len(c))
        for rel, n, s in sorted(c):
            print("  %s:%d  %s" % (rel, n, s[:145]))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(a[0] if a else ".", "--full" in sys.argv)
