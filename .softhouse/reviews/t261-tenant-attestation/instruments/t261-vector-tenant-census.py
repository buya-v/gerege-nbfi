#!/usr/bin/env python3
"""T261 -- independent census of the vector store for T250 s.4 FACT 2.

Question: how many vector files are there, and how many carry a `tenant` field
(at any depth, and specifically inside an `oracle`/`stamp` object)?

MONEY (CLAUDE.md non-negotiable): every JSON here is parsed with
`parse_float=str` so that no monetary literal is ever turned into a binary float,
even transiently, by this instrument.  Nothing here decides anything from a
number, but the rule is about the code path, not the intent.

Engine: python3 stdlib.  No grep / rg / git grep.  A git failure ABORTS (exit 5).

usage: t261-vector-tenant-census.py <tree-ish> <root-dir>
"""
import json
import os
import subprocess
import sys

TREE, ROOT = sys.argv[1], sys.argv[2]


def keys_anywhere(obj, name, path="$"):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() == name:
                hits.append("%s.%s" % (path, k))
            hits.extend(keys_anywhere(v, name, "%s.%s" % (path, k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(keys_anywhere(v, name, "%s[%d]" % (path, i)))
    return hits


def main():
    p = subprocess.run(["git", "ls-tree", "-r", "--name-only", TREE, ".softhouse/vectors"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("ABORT: git ls-tree rc=%d %s\n" % (p.returncode, p.stderr))
        sys.exit(5)
    files = [x for x in p.stdout.splitlines() if x.strip()]
    pins = [f for f in files if os.path.basename(f).startswith("PIN")]
    vectors = [f for f in files if f.endswith(".json") and f not in pins]
    other = [f for f in files if not f.endswith(".json")]

    # calibration: the census must SEE a tenant field when one is present,
    # and must NOT see one when it is absent.  Otherwise "0" means nothing.
    pos = {"oracle": {"tenant": "gerege"}, "amount": "1250000"}
    neg = {"oracle": {"commit": "426a2354"}, "amount": "1250000"}
    if len(keys_anywhere(pos, "tenant")) != 1 or len(keys_anywhere(neg, "tenant")) != 0:
        sys.stderr.write("CALIBRATION FAILED -- ABORT\n")
        sys.exit(4)
    print("CALIBRATION: positive fixture 1 hit, negative fixture 0 hits -- discriminates\n")

    with_tenant, unparseable = [], []
    for rel in vectors:
        path = os.path.join(ROOT, rel)
        try:
            with open(path, "rb") as fh:
                doc = json.loads(fh.read().decode("utf-8"), parse_float=str)
        except Exception as exc:
            unparseable.append((rel, str(exc)))
            continue
        h = keys_anywhere(doc, "tenant")
        if h:
            with_tenant.append((rel, h))

    print("SCOPE  tree=%s path=.softhouse/vectors" % TREE)
    print("  files in the pinned tree          : %d" % len(files))
    print("  of which PIN files                : %d  %s" % (len(pins), pins))
    print("  of which non-json                 : %d  %s" % (len(other), other))
    print("  VECTOR files (json, non-PIN)      : %d" % len(vectors))
    print("  unparseable                       : %d" % len(unparseable))
    for r, e in unparseable:
        print("      %s  %s" % (r, e))
    print("")
    print("  vectors carrying a `tenant` field : %d" % len(with_tenant))
    for r, h in with_tenant:
        print("      %s  %s" % (r, h))
    print("")
    # and the pins themselves
    for pin in pins:
        with open(os.path.join(ROOT, pin), "rb") as fh:
            doc = json.loads(fh.read().decode("utf-8"), parse_float=str)
        print("  %s tenant field(s): %s" % (pin, keys_anywhere(doc, "tenant") or "NONE"))


main()
