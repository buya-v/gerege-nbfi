#!/usr/bin/env python3
"""T207 -- reconcile T185's published '193 -> 201' and the brief's '240 scripts' against the
LIVE tree, by enumerating the candidate populations rather than asserting one.

P-69: a measured claim can go stale inside one fire.  P-67: certify a figure only after
counting BOTH terms.  This script does not decide what T185 meant; it prints every plausible
reading side by side so the handoff can say which reproduces and which does not, and mark the
rest UNVERIFIED.

READ-ONLY.  No float.
"""
import ast
import os
import subprocess
import sys


def tracked(root, pat):
    out = subprocess.run(["git", "-C", root, "ls-files", "-z", pat],
                         capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.split("\0") if p)


def count(root, files, attrs, under=None):
    tot = no_pf = 0
    for rel in files:
        if under and not rel.startswith(under):
            continue
        try:
            tree = ast.parse(open(os.path.join(root, rel), "rb").read(), filename=rel)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr in attrs and isinstance(n.func.value, ast.Name)
                    and n.func.value.id == "json"):
                tot += 1
                if "parse_float" not in {k.arg for k in n.keywords if k.arg}:
                    no_pf += 1
    return tot, no_pf


def grepcount(root, files, needle, under=None):
    n = 0
    for rel in files:
        if under and not rel.startswith(under):
            continue
        with open(os.path.join(root, rel), "rb") as fh:
            for line in fh:
                if needle in line and b"parse_float" not in line:
                    n += 1
    return n


def main(argv):
    root = os.path.abspath(argv[0]) if argv else os.getcwd()
    py = tracked(root, "*.py")
    sh = tracked(root, "*.sh")
    print("T207 -- candidate populations for T185's '193 -> 201' and the brief's '240 scripts'")
    print("root   : %s" % root)
    print("commit : %s" % subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                                         capture_output=True, text=True).stdout.strip())
    print()
    print("SCRIPT-COUNT candidates (the '240 scripts' term):")
    print("  git-tracked *.py, whole repo                       : %d" % len(py))
    print("  git-tracked *.sh, whole repo                       : %d" % len(sh))
    print("  git-tracked *.py + *.sh, whole repo                : %d" % (len(py) + len(sh)))
    for pref in (".softhouse/capture/", ".softhouse/reviews/", ".softhouse/handoff/",
                 ".softhouse/bin/"):
        print("  git-tracked *.py under %-24s: %d"
              % (pref, len([p for p in py if p.startswith(pref)])))
    print("  git-tracked *.py that CONTAIN the text 'json.load' : %d"
          % len([p for p in py if b"json.load" in open(os.path.join(root, p), "rb").read()]))

    print()
    print("SITE-COUNT candidates (the '193 -> 201' term):")
    for label, attrs in (("json.load AND json.loads", ("load", "loads")),
                         ("json.load ONLY", ("load",)),
                         ("json.loads ONLY", ("loads",))):
        for scope_label, under in (("whole repo", None),
                                   (".softhouse/capture/ only", ".softhouse/capture/")):
            tot, no_pf = count(root, py, attrs, under)
            print("  AST  %-26s %-26s total %-4d  no parse_float %-4d"
                  % (label, scope_label, tot, no_pf))
    print("  GREP line-based 'json.load' with no parse_float on the SAME line, whole repo : %d"
          % grepcount(root, py, b"json.load"))
    print("  GREP line-based 'json.load(' with no parse_float on the SAME line, whole repo: %d"
          % grepcount(root, py, b"json.load("))
    print()
    print("NOTE: no reading is asserted to be T185's. The handoff records which of these")
    print("      reproduces 201 and which does not, and marks the rest UNVERIFIED.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
