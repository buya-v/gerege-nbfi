#!/usr/bin/env python3
"""T175 helper for drive-red.sh -- count files a glob set requests, and how many of them
`json.load` refuses.  Read-only; constructs no float; writes nothing."""
import glob
import json
import sys


def paths(pats):
    out = []
    for pat in pats:
        out.extend(sorted(glob.glob(pat, recursive=True)))
    return out


def main(argv):
    mode, pats = argv[0], argv[1:]
    ps = paths(pats)
    if mode == "--count-requested":
        print(len(ps))
        return 0
    if mode == "--count-unparseable":
        n = 0
        for p in ps:
            try:
                json.load(open(p))
            except Exception:
                # Counted here on purpose: this helper's ONLY job is to produce that count,
                # and it is printed. Nothing is swallowed -- the number IS the record.
                n += 1
        print(n)
        return 0
    if mode == "--name-unparseable":
        for p in ps:
            try:
                json.load(open(p))
            except Exception as exc:
                print("%s\t%s\t%s" % (p, type(exc).__name__, exc))
        return 0
    sys.stderr.write("unknown mode %r\n" % mode)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
