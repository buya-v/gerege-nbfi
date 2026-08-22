#!/usr/bin/env python3
"""T203 - measure the exposure of the TWO vector-store rewriters that T196 and
T198 did not name: `T57-promote-emi-vectors.py` and `T8-promote-vectors.py`.

Both compute their output directory as
    OUT = os.path.join(ROOT, ".softhouse", "vectors", "loanschedule")
with ROOT derived at runtime, so T179's classifier resolves the target to
UNKNOWN rather than TRUSTED - and UNKNOWN does not trip `--enforce`.  That is
the residual fail-open in the same family T196 closed for function parameters.

READ-ONLY.  Modules are imported (so `main()` stays dormant) purely to read
their `PROMOTE`/`SLUG` tables and their `OUT` constant.  Nothing is executed
that writes.
"""
import importlib.util
import os
import sys

STORE = ".softhouse/vectors/loanschedule"
TARGETS = [
    ("T57", ".softhouse/handoff/T57-promote-emi-vectors.py"),
    ("T8", ".softhouse/handoff/T8-promote-vectors.py"),
]


def load(root, rel, tag):
    spec = importlib.util.spec_from_file_location("t203probe_%s" % tag,
                                                  os.path.join(root, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(root):
    root = os.path.realpath(root)
    os.chdir(root)
    live_store = os.path.realpath(os.path.join(root, STORE))
    total = 0
    for tag, rel in TARGETS:
        mod = load(root, rel, tag)
        out = os.path.realpath(getattr(mod, "OUT"))
        names = [mod.SLUG[c] + ".json" for c in mod.PROMOTE]
        live = [n for n in names if os.path.isfile(os.path.join(live_store, n))]
        print("%s  %s" % (tag, rel))
        print("    OUT resolves to      : %s" % out)
        print("    OUT IS THE LIVE STORE: %s" % (out == live_store))
        print("    targets              : %d ; LIVE in store: %d"
              % (len(names), len(live)))
        for n in live:
            print("        LIVE  %s" % n)
        for n in names:
            if n not in live:
                print("        (not in store) %s" % n)
        total += len(live)
        print("")
    print("LIVE parity vectors reachable by T57 + T8: %d" % total)
    if total == 0:
        sys.stderr.write("P-35: inspected ZERO live targets - ERROR\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
