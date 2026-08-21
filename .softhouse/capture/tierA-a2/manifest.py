#!/usr/bin/env python3
"""Build MANIFEST.sha256 over every captured observation, and verify it.

  python3 manifest.py write     -> (re)write MANIFEST.sha256
  python3 manifest.py verify    -> exit 0 if every file matches, 1 if any differs

The manifest covers out/ (observations), req/ (the exact request bodies that
produced them) and sql/ (the queries). A capture whose request body has drifted
is not reproducible, which is why req/ is hashed too and not just out/.
"""
import hashlib, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(DIR, "MANIFEST.sha256")
DIRS = ("out", "req", "sql")


def digest(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def entries():
    for d in DIRS:
        base = os.path.join(DIR, d)
        if not os.path.isdir(base):
            continue
        for n in sorted(os.listdir(base)):
            p = os.path.join(base, n)
            if os.path.isfile(p):
                yield f"{d}/{n}", p


def write():
    lines = [f"{digest(p)}  {rel}\n" for rel, p in entries()]
    with open(MAN, "w") as f:
        f.writelines(lines)
    print(f"wrote {MAN} with {len(lines)} entries")


def verify():
    if not os.path.exists(MAN):
        print("MANIFEST.sha256 missing", file=sys.stderr)
        return 1
    want = {}
    for line in open(MAN):
        h, rel = line.rstrip("\n").split("  ", 1)
        want[rel] = h
    have = {rel: digest(p) for rel, p in entries()}
    bad = 0
    for rel, h in want.items():
        if rel not in have:
            print(f"MISSING   {rel}"); bad += 1
        elif have[rel] != h:
            print(f"CHANGED   {rel}\n  manifest {h}\n  actual   {have[rel]}"); bad += 1
    for rel in have:
        if rel not in want:
            print(f"UNTRACKED {rel}"); bad += 1
    if bad:
        print(f"\nFAIL: {bad} discrepancy/ies", file=sys.stderr)
        return 1
    print(f"OK: {len(want)} files match MANIFEST.sha256")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "write":
        write()
    else:
        sys.exit(verify())
