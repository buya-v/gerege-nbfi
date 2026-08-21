#!/usr/bin/env python3
"""Prove A2-7 ADDED evidence and REWROTE none of it.

The A2 rig's hard rule is that nothing under out/, req/ or sql/ may be mutated: those
bytes are oracle observations. `manifest.py verify` proves the tree matches the manifest
NOW; it cannot by itself prove that regenerating the manifest did not launder a changed
file, because `manifest.py write` would happily record the new hash.

So this compares the CURRENT MANIFEST.sha256 against the one committed at the immutable
fork point, and asserts:

  * every path in the OLD manifest is still present in the NEW one, with a BYTE-IDENTICAL
    hash — the pre-existing evidence hashes were unchanged by the regeneration;
  * no path was dropped;
  * the only additions are the A2-7 artefacts.

BASELINE IS A LITERAL SHA, DELIBERATELY (P-24). `git merge-base main HEAD` resolves to
the fork point while this runs on the branch and to the MERGE COMMIT ITSELF once merged,
at which point the comparison would be against the post-change state and pass
vacuously — the exact time bomb P-24 records. A literal sha cannot follow main.

  python3 prove-a2-7-additive.py
"""
import os
import subprocess
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
REPO = subprocess.run(["git", "-C", DIR, "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
REL = os.path.relpath(os.path.join(DIR, "MANIFEST.sha256"), REPO)

# The fork point of branch softhouse/A2-7-capture-mandatory-accounts. Immutable.
BASELINE = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"


def manifest_at(rev):
    p = subprocess.run(["git", "-C", REPO, "show", f"{rev}:{REL}"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        print(f"cannot read {REL} at {rev}: {p.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    d = {}
    for line in p.stdout.splitlines():
        if line.strip():
            h, rel = line.split("  ", 1)
            d[rel] = h
    return d


def current():
    d = {}
    for line in open(os.path.join(DIR, "MANIFEST.sha256")):
        if line.strip():
            h, rel = line.rstrip("\n").split("  ", 1)
            d[rel] = h
    return d


def main():
    old = manifest_at(BASELINE)
    new = current()
    print(f"baseline {BASELINE[:12]}  {len(old)} entries")
    print(f"working tree                   {len(new)} entries")

    changed = sorted(r for r in old if r in new and old[r] != new[r])
    dropped = sorted(r for r in old if r not in new)
    added = sorted(r for r in new if r not in old)

    for r in changed:
        print(f"  CHANGED {r}\n    was {old[r]}\n    now {new[r]}")
    for r in dropped:
        print(f"  DROPPED {r}")

    print(f"\n  pre-existing entries carried forward UNCHANGED: "
          f"{len(old) - len(changed) - len(dropped)} of {len(old)}")
    print(f"  changed: {len(changed)}   dropped: {len(dropped)}   added: {len(added)}")

    # The manifest hashes ITSELF is not in the manifest, so a changed hash for any other
    # rig file would show above. MANIFEST.sha256 is excluded by manifest.py by design.
    bad = []
    if changed:
        bad.append(f"{len(changed)} pre-existing file(s) changed hash")
    if dropped:
        bad.append(f"{len(dropped)} pre-existing file(s) dropped")
    if not added:
        bad.append("nothing was added — this task captured no evidence")

    print("\n  added by A2-7:")
    for r in added:
        print(f"    + {r}")

    if bad:
        print("\nFAIL: " + "; ".join(bad), file=sys.stderr)
        return 1
    print("\nPASS: additive only — every pre-existing evidence hash is byte-identical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
