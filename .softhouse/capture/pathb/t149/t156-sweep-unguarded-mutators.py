#!/usr/bin/env python3
"""T156 / P-26 — sweep .softhouse for the CONCEPT behind prove-redgreen.sh's missing
EXIT trap, not for its wording.

THE CONCEPT: a rig that TEMPORARILY MUTATES something a later reader treats as ground
truth — the vector store, a committed capture set, a port source file, a committed
script — and restores it with a plain statement rather than a handler that runs on every
exit path.  Interrupt it in the window and the mutation survives the run that made it.
That is only half the defect; the other half is that whatever reads the mutated artefact
next does not know its own inputs changed, so it reports a green over a smaller world.

WHAT THIS SWEEP CAN AND CANNOT FIND (P-26 requires saying so).
  * It reads only `*.sh` and `*.py` under `.softhouse/`.  A mutator written in Go, in a
    Makefile, in a Java test, in a `.md` code block a human pastes, or in a shell
    one-liner typed into a handoff, is INVISIBLE to it.
  * It matches mutation VERBS lexically.  A mutation performed by a redirect (`> file`),
    by `sed -i`, by a Python `open(p,"w")`, or by a helper the file calls in another
    file, is only caught where those forms are listed below.
  * `trap` / `finally` / `atexit` in a file is evidence a guard EXISTS somewhere in that
    file, never that it covers THIS mutation.  Every guarded hit still needs reading.
  * It cannot see a mutator that is correct today and interruptible tomorrow.
  * Every file it could not read is COUNTED and NAMED (P-40).  A sweep with an invisible
    `except: continue` over a population it is measuring is the same defect as a guard
    that cannot fail.

Run:  python3 t156-sweep-unguarded-mutators.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ROOT = os.path.join(REPO, ".softhouse")

# Verbs that move, copy over, delete or rewrite an existing path in place.
MUTATE = [
    ("sh:mv", re.compile(r"(?m)^[^#\n]*(?<![\w./-])mv\s")),
    ("sh:cp", re.compile(r"(?m)^[^#\n]*(?<![\w./-])cp\s")),
    ("sh:sed-i", re.compile(r"(?m)^[^#\n]*sed\s+(-[a-zA-Z]*\s+)*-i")),
    ("sh:git-checkout", re.compile(r"(?m)^[^#\n]*git\s+checkout\s+--")),
    ("sh:git-restore", re.compile(r"(?m)^[^#\n]*git\s+(restore|stash)\b")),
    ("py:shutil", re.compile(r"(?m)^[^#\n]*shutil\.(move|copy|copy2|copyfile|copytree|rmtree)\s*\(")),
    ("py:os-rename", re.compile(r"(?m)^[^#\n]*os\.(replace|rename|remove|unlink)\s*\(")),
    ("py:write", re.compile(r"(?m)^[^#\n]*open\s*\([^)]*[\"'][rwa]?[+]?[bt]?w")),
    ("py:write_text", re.compile(r"(?m)^[^#\n]*\.write_(text|bytes)\s*\(")),
]

# A path a LATER reader treats as ground truth.
TARGETS = [
    ("STORE", re.compile(r"\.softhouse/vectors|STORE_ROOT|\$STORE\b|/vectors/")),
    ("PORT", re.compile(r"nexus/internal|\.go\b")),
    ("CAPTURE", re.compile(r"\.softhouse/capture|/out/|capture_dir|OUTDIR|\$O\b|\$OUT\b")),
    ("RIG", re.compile(r"attest\.py|conformance\.sh|contract\.go|PIN\.json|capabilities\.json")),
]

GUARD = re.compile(r"(?m)^[^#\n]*(\btrap\b|\bfinally\s*:|atexit\.register|__exit__|contextmanager)")

# A file that only ever writes into a throwaway directory is not this shape.
SANDBOXY = re.compile(r"mkdtemp|mktemp|TMPDIR|/tmp/|tempfile\.")


def main():
    files, unreadable = [], []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in sorted(filenames):
            if fn.endswith((".sh", ".py")):
                files.append(os.path.join(dirpath, fn))
    files.sort()

    # P-40: measure the population this sweep does NOT cover, and print the number.
    # A sweep whose misses are invisible reads as exhaustive.
    all_files, by_ext = 0, {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            all_files += 1
            by_ext[os.path.splitext(fn)[1] or "<none>"] = \
                by_ext.get(os.path.splitext(fn)[1] or "<none>", 0) + 1

    print("=== T156 / P-26 sweep — temporary mutation of an artefact a later reader trusts")
    print("root: %s" % ROOT)
    print("enumerated: %d files (*.sh, *.py)" % len(files))
    print("NOT ENUMERATED: %d of the %d files under this root — every other extension."
          % (all_files - len(files), all_files))
    print("  the largest uncovered groups: %s"
          % ", ".join("%s %d" % (e, n) for e, n in
                      sorted(((e, n) for e, n in by_ext.items() if e not in (".sh", ".py")),
                             key=lambda t: -t[1])[:6]))
    print("  a mutator written in Go, in a Makefile, or pasted out of a .md code block by a")
    print("  human is therefore INVISIBLE to this sweep. So is anything outside %s —" % ROOT)
    print("  nexus/ and docs/ were not swept at all.")
    print()

    hits = []
    for p in files:
        try:
            with open(p, "r", encoding="utf-8", errors="strict") as f:
                src = f.read()
        except (OSError, UnicodeDecodeError) as e:
            # NOT a silent skip: named and counted, and it changes the verdict below.
            unreadable.append((p, type(e).__name__))
            continue
        verbs = [n for n, rx in MUTATE if rx.search(src)]
        if not verbs:
            continue
        tgts = [n for n, rx in TARGETS if rx.search(src)]
        if not tgts:
            continue
        hits.append({
            "path": os.path.relpath(p, REPO),
            "verbs": verbs,
            "targets": tgts,
            "guard": bool(GUARD.search(src)),
            "sandboxy": bool(SANDBOXY.search(src)),
            "lines": [(i + 1, l.rstrip())
                      for i, l in enumerate(src.splitlines())
                      if any(rx.search(l) for _, rx in MUTATE)
                      and any(rx.search(l) for _, rx in TARGETS)],
        })

    unguarded = [h for h in hits if not h["guard"]]
    print("matched a mutation VERB *and* a trusted TARGET: %d" % len(hits))
    print("  of those, carrying no trap/finally/atexit anywhere in the file: %d" % len(unguarded))
    print("  of those, writing only into a throwaway dir (mktemp/tmp): %d"
          % len([h for h in unguarded if h["sandboxy"]]))
    print("could not be read (named, counted, NOT skipped silently): %d" % len(unreadable))
    for p, why in unreadable:
        print("    UNREADABLE %s (%s)" % (os.path.relpath(p, REPO), why))
    print()

    print("--- FILES THAT MUTATE THE VECTOR STORE AT ALL (the exact shape T156 fixed)")
    store = [h for h in hits if "STORE" in h["targets"]]
    if not store:
        print("    none — which would be surprising; treat as a sweep failure, not a clean bill")
    for h in store:
        print("  %-70s guard=%s  verbs=%s" % (h["path"], "yes" if h["guard"] else "**NO**",
                                              ",".join(h["verbs"])))
        for ln, text in h["lines"][:12]:
            print("      %5d | %s" % (ln, text.strip()[:130]))
    print()

    # The sharpest form of the concept: bytes from git written OVER a live path, or a
    # `git checkout --` used as the undo. Every such line is printed with its file's trap
    # count so a reader adjudicates rather than trusting a classifier.
    print("--- IN-PLACE RESTORE IDIOMS — `git show ... > path` and `git checkout -- path`")
    idiom = re.compile(r"(?m)^[^#\n]*(git\s+show\s+[^|]*>|git\s+checkout\s+--|git\s+restore\b)")
    found = 0
    for p_ in files:
        try:
            src = open(p_, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue          # already counted and named above; not a new silent skip
        ls = [(i + 1, l.rstrip()) for i, l in enumerate(src.splitlines()) if idiom.search(l)]
        if not ls:
            continue
        found += 1
        ntrap = len(re.findall(r"(?m)^\s*trap\s", src))
        print("  %-64s traps=%d" % (os.path.relpath(p_, REPO), ntrap))
        for ln, text in ls:
            print("      %5d | %s" % (ln, text.strip()[:130]))
    print("  files using an in-place restore idiom: %d" % found)
    print()

    print("--- EVERY OTHER UNGUARDED HIT, for reading by hand")
    for h in unguarded:
        if "STORE" in h["targets"]:
            continue
        print("  %-70s targets=%s verbs=%s sandbox-only=%s"
              % (h["path"], ",".join(h["targets"]), ",".join(h["verbs"]), h["sandboxy"]))
    print()
    print("counts: enumerated=%d  hits=%d  unguarded=%d  unreadable=%d"
          % (len(files), len(hits), len(unguarded), len(unreadable)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
