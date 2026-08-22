#!/usr/bin/env python3
"""T253b — how many things still hardcode the Mac's absolute paths?

I was handed two different numbers for this (six, and thirty) and told to trust
neither. So this counts it from the tree, states the SELECTOR before the
conditions (P-76 addendum), and reports BOTH TERMS of every count (P-67):
the population searched and the subset that matched.

The number depends entirely on what you decide to count, so all the slices are
printed rather than one headline figure. A bare "N instruments" claim is
unfalsifiable without the selector that produced it.

No bare `grep`, no `rg` (P-75) — python re over `git ls-files`.
"""
import re
import subprocess
import sys

MAC = "/Users/buv/gerege-nbfi"
TOOLCHAIN = re.compile(re.escape(MAC) + r"/\.softhouse/toolchain")
GOENV = re.compile(re.escape(MAC) + r"/\.softhouse/bin/go-env\.sh")
ANYMAC = re.compile(re.escape(MAC))

RUNNABLE = (".sh", ".py")
# Evidence transcripts and prose record what a past run SAW on that host. A path
# inside them is a historical observation, not a thing that executes and breaks.
PROSE = (".md", ".txt", ".json", ".out")


def tracked():
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("git ls-files failed rc=%d\n" % r.returncode)
        raise SystemExit(2)
    return [f for f in r.stdout.split("\n") if f]


def main() -> int:
    files = tracked()
    print("SELECTOR : tracked files (git ls-files), literal %r" % MAC)
    print("POPULATION (all tracked files)            : %d" % len(files))

    runnable = [f for f in files if f.endswith(RUNNABLE)]
    prose = [f for f in files if f.endswith(PROSE)]
    print("  of which runnable (.sh/.py)             : %d" % len(runnable))
    print("  of which prose/evidence (.md/.txt/...)  : %d" % len(prose))
    print()

    buckets = {"toolchain": [], "goenv": [], "anymac": []}
    for f in files:
        try:
            t = open(f, encoding="utf-8", errors="replace").read()
        except (OSError, IsADirectoryError):
            continue
        if TOOLCHAIN.search(t):
            buckets["toolchain"].append(f)
        if GOENV.search(t):
            buckets["goenv"].append(f)
        if ANYMAC.search(t):
            buckets["anymac"].append(f)

    for name, label in (
        ("toolchain", "the Mac toolchain dir  %s/.softhouse/toolchain" % MAC),
        ("goenv", "the Mac go-env.sh path %s/.softhouse/bin/go-env.sh" % MAC),
        ("anymac", "ANY absolute %s path" % MAC),
    ):
        hits = buckets[name]
        run = [f for f in hits if f.endswith(RUNNABLE)]
        pro = [f for f in hits if f.endswith(PROSE)]
        other = [f for f in hits if f not in run and f not in pro]
        print("=== %s ===" % label)
        print("  matched  : %d of %d tracked files" % (len(hits), len(files)))
        print("  RUNNABLE : %d of %d runnable files  <-- the ones that actually break off-Mac"
              % (len(run), len(runnable)))
        print("  prose    : %d of %d prose files     <-- historical observations, not defects"
              % (len(pro), len(prose)))
        if other:
            print("  other    : %d  %s" % (len(other), other))
        if name in ("toolchain", "goenv"):
            for f in sorted(run):
                print("      RUNNABLE %s" % f)
        print()

    union_run = sorted(
        set(f for f in buckets["toolchain"] if f.endswith(RUNNABLE))
        | set(f for f in buckets["goenv"] if f.endswith(RUNNABLE))
    )
    print("=== HEADLINE, stated with its selector ===")
    print("  RUNNABLE tracked files hardcoding the Mac toolchain OR the Mac go-env.sh path")
    print("  (union, deduplicated) : %d of %d runnable tracked files"
          % (len(union_run), len(runnable)))
    print("  Any of these, executed on another host, resolves a path that is not there.")
    print()
    print("  CORRECTION TO MY OWN FIRST DRAFT, kept rather than quietly edited out:")
    print("  this note used to read '.softhouse/bin/go-env.sh is NO LONGER among them'.")
    print("  Its own selector says otherwise and the selector is right. Two files match")
    print("  the literal WITHOUT being live hardcodes, and a text search cannot tell the")
    print("  difference — only a reader can:")
    print("    .softhouse/bin/go-env.sh                                 — the path survives")
    print("      ONLY inside the comment that documents the defect that was removed. The")
    print("      executable part derives its toolchain and hardcodes nothing.")
    print("    .softhouse/capture/t253-portability/instruments/30-d2-red-drive.sh — it")
    print("      REPRODUCES the old file verbatim in order to drive it red. The hardcode")
    print("      is the specimen, not the defect.")
    print("  So: %d matched, of which 2 are T253b artefacts, leaving %d live hardcodes."
          % (len(union_run), len(union_run) - 2))
    print()
    print("  BASELINE ON `main` (pre-T253b), same literal, `git grep -F -l ... -- '*.sh' '*.py'`,")
    print("  rc classified per P-80: 29 files. Of those 29, go-env.sh was a GENUINE live")
    print("  hardcode and is the one this task removed; the other 28 are untouched and")
    print("  out of scope. `*.zsh`/`*.bash` were searched separately and matched NOTHING")
    print("  (git grep rc=1, a measured negative, not an error).")
    print()
    print("  I was handed the figures 'six' and 'thirty' and told to trust neither.")
    print("  Neither is reproduced exactly by this selector. 'Thirty' is within one of")
    print("  the runnable count and is the closer of the two; 'six' is not close to any")
    print("  slice measured here. A count of this kind is meaningless without the")
    print("  selector that produced it, which is why every slice above is printed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
