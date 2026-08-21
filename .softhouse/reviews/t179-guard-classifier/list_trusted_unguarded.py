#!/usr/bin/env python3
"""T179 — one line per UNGUARDED mutation of a TRUSTED artefact, at a pinned ref.

The population table gives counts; this gives the list a human has to read (P-48
rule 3: report the population, then hand-read the exceptions — an unexamined
allowlist is where this class of defect lives).  Shell files are absent because they
are REFUSED, not because they are clean.

Usage: python3 list_trusted_unguarded.py [--ref main]
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import guard_classify as gc                                     # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="main")
    args = ap.parse_args()
    sha = subprocess.run(["git", "-C", REPO, "rev-parse", args.ref],
                         capture_output=True, text=True).stdout.strip()
    paths = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only",
                            args.ref, "--", ".softhouse"],
                           capture_output=True, text=True).stdout.split()
    py = [p for p in paths if p.endswith(".py")]
    print("T179 — UNGUARDED mutations of a TRUSTED artefact, python only")
    print("ref: %s (%s)   python files read: %d" % (args.ref, sha, len(py)))
    print("shell files are REFUSED and therefore ABSENT from this list — absence "
          "here is not evidence of a guard")
    print()
    n, files = 0, set()
    for rel in py:
        src = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (args.ref, rel)],
                             capture_output=True).stdout.decode("utf-8", "replace")
        r = gc.classify_python(rel, src)
        if r.get("refused"):
            continue
        for s in r["sites"]:
            if s["scope"] == gc.TRUSTED and s["verdict"] == gc.UNGUARDED:
                n += 1
                files.add(rel)
                print("%-60s :%-5d %-20s tags=%-9s target=%s"
                      % (rel, s["line"], s["verb"], ",".join(s["target_tags"]),
                         s["target"][:70]))
    print()
    print("sites: %d   files: %d" % (n, len(files)))
    if n == 0:
        print("ZERO sites is only meaningful if files were read: %d python files "
              "were parsed above (P-35)." % len(py))
    return 0


if __name__ == "__main__":
    sys.exit(main())
