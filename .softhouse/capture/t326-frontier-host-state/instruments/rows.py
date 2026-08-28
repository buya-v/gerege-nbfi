#!/usr/bin/env python3
"""T326 helper -- print the frontier ROWS from a census JSON, one per line, sorted.

Byte-for-byte the same derivation `.softhouse/guards/check-dead-path-frontier.sh` performs, so
that "the drive compared the rows" and "the guard compares the rows" are the same sentence.

EXIT: 0 rows printed (at least one); 2 unreadable input, or ZERO rows -- zero is a failed read,
never an empty frontier, and a drive that silently compared two empty files would report the
defect fixed no matter what.
"""
import json
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: rows.py <census.json>", file=sys.stderr)
        return 2
    try:
        doc = json.load(open(sys.argv[1]))
    except (OSError, ValueError) as exc:
        print("ERROR: %s: %s" % (sys.argv[1], exc), file=sys.stderr)
        return 2
    rows = sorted({"%s | %s" % (f, d)
                   for f in doc.get("deadFiles", [])
                   for d in doc.get("perFile", {}).get(f, {}).get("dead", [])})
    if not rows:
        print("ERROR: zero rows derived from %s. A comparison of two empty sets is not a"
              % sys.argv[1], file=sys.stderr)
        print("ERROR: measurement. REFUSING (exit 2).", file=sys.stderr)
        return 2
    for r in rows:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
