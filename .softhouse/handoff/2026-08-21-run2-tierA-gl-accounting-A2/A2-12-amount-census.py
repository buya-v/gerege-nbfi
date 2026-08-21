#!/usr/bin/env python3
"""A2-12 — the `amount`-field census cited by nexus/internal/apps/ledger/money.go.

Written to close A2-9's finding F-C: A2-8's money.go carried a [VERIFIED:]
count of "27 JSON `amount` fields", A2-9 measured 52 and could not reproduce 27,
and a number nobody can reproduce is worse than no number. This script IS the
measurement, so the claim in money.go is checkable rather than quotable.

NO FLOATING POINT ANYWHERE (P-25 — the no-float rule binds analysis scripts,
because a wrong number here becomes a wrong money claim in a comment a porter
reads). Every numeric literal in the captures is parsed as decimal.Decimal and
every count is an int.

Run from the repo root:

    python3 .softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/A2-12-amount-census.py

Optional argument: a capture directory (default .softhouse/capture/tierA-a2/out).
"""

import decimal
import json
import pathlib
import sys

TWO_DP = decimal.Decimal("1.00")


def census(root):
    files = sorted(root.glob("*.json"))
    hits = []
    unparseable = []

    def walk(node, path, fname):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "amount" and not isinstance(value, (dict, list)):
                    text = value if isinstance(value, str) else str(value)
                    hits.append((fname, path + "." + key, text))
                walk(value, path + "." + key, fname)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, path + "[%d]" % i, fname)

    for f in files:
        try:
            doc = json.loads(f.read_text(), parse_float=decimal.Decimal)
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed (P-40)
            unparseable.append((f.name, repr(exc)))
            continue
        walk(doc, "", f.name)

    return files, hits, unparseable


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".softhouse/capture/tierA-a2/out")
    if not root.is_dir():
        sys.exit("no such capture directory: %s" % root)

    files, hits, unparseable = census(root)

    sub_minor = [h for h in hits if decimal.Decimal(h[2]) != decimal.Decimal(h[2]).quantize(TWO_DP)]
    exact = [h for h in hits if h not in sub_minor]
    trailing_zeros = [h for h in exact if h[2].endswith(".000000")]
    distinct_pairs = sorted({(h[0], h[2]) for h in hits})

    print("root                                  %s" % root)
    print("json files                            %d  (unparseable %d)" % (len(files), len(unparseable)))
    for name, exc in unparseable:
        print("    UNPARSEABLE %s %s" % (name, exc))
    print("`amount` fields at any depth          %d" % len(hits))
    print("files carrying at least one           %d" % len({h[0] for h in hits}))
    print("NOT exact at two decimal places       %d" % len(sub_minor))
    for h in sub_minor:
        print("    %-40s %-32s %s" % h)
    print("exact at two decimal places           %d" % len(exact))
    print("    of those, reading ....000000      %d" % len(trailing_zeros))
    print("    of those, not                     %d" % (len(exact) - len(trailing_zeros)))
    for h in exact:
        if not h[2].endswith(".000000"):
            print("        %-36s %-32s %s" % h)
    print("distinct (file, amount text) pairs    %d   <- this is A2-8's '27'" % len(distinct_pairs))
    print("    of those, reading ....000000      %d"
          % len([p for p in distinct_pairs if p[1].endswith(".000000")]))

    # Every guard here is POSITIVE (P-35): it asserts what was inspected, and
    # an empty capture directory is an error rather than a silent pass.
    if not files:
        sys.exit("FAIL: inspected zero json files — an empty census is not a green one")
    if not hits:
        sys.exit("FAIL: inspected zero `amount` fields — an empty census is not a green one")


if __name__ == "__main__":
    main()
