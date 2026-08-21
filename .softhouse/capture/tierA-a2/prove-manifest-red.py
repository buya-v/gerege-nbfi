#!/usr/bin/env python3
"""Drive manifest.py verify RED, three ways, and restore the tree afterwards.

The pipeline rule is: ship no guard you have not driven red. A hash manifest that
cannot fail is worse than none, because it launders unverified files as verified.
This proves the guard detects (1) a mutated observation, (2) a deleted
observation, (3) an added-but-unrecorded observation — and that it returns exit 0
again once the tree is restored.

Run:  python3 prove-manifest-red.py
Exits 0 only if ALL THREE mutations were caught AND the restored tree verifies.
"""
import os, shutil, subprocess, sys, tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
VICTIM = os.path.join(DIR, "out", "A2-084-disburse-loan1-paymenttype1.json")
EXTRA = os.path.join(DIR, "out", "ZZ-not-an-observation.json")


def verify():
    r = subprocess.run([sys.executable, os.path.join(DIR, "manifest.py"), "verify"],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def main():
    if not os.path.exists(VICTIM):
        print("cannot run: victim file absent", file=sys.stderr)
        return 2

    rc, out = verify()
    if rc != 0:
        print("BASELINE IS ALREADY RED — cannot prove anything:\n" + out, file=sys.stderr)
        return 2
    print("baseline: GREEN (exit 0)")

    original = open(VICTIM, "rb").read()
    results = []

    # (1) mutate a captured observation by ONE byte
    try:
        open(VICTIM, "wb").write(original.replace(b'"loanId":1', b'"loanId":9', 1))
        rc, out = verify()
        ok = rc != 0 and "CHANGED" in out
        results.append(("mutated observation", ok, rc))
        print(f"  mutate  -> exit {rc} {'CAUGHT' if ok else 'MISSED'}")
    finally:
        open(VICTIM, "wb").write(original)

    # (2) delete a captured observation
    try:
        os.remove(VICTIM)
        rc, out = verify()
        ok = rc != 0 and "MISSING" in out
        results.append(("deleted observation", ok, rc))
        print(f"  delete  -> exit {rc} {'CAUGHT' if ok else 'MISSED'}")
    finally:
        open(VICTIM, "wb").write(original)

    # (3) add a file that no recorded recipe produced
    try:
        open(EXTRA, "w").write('{"fabricated":true}\n')
        rc, out = verify()
        ok = rc != 0 and "UNTRACKED" in out
        results.append(("untracked file", ok, rc))
        print(f"  add     -> exit {rc} {'CAUGHT' if ok else 'MISSED'}")
    finally:
        os.remove(EXTRA)

    rc, out = verify()
    restored = rc == 0
    print(f"restored: {'GREEN (exit 0)' if restored else 'STILL RED — TREE DAMAGED'}")

    allok = all(ok for _, ok, _ in results) and restored
    print("\nRESULT:", "guard is demonstrably failable" if allok else "GUARD DID NOT FAIL — DO NOT SHIP IT")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
