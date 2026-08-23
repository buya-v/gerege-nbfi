#!/usr/bin/env python3
"""T304 — derive the PROTECTED ROOT set for the evidence-destruction guard from the
census, rather than from a hand-written list.

A root is protected iff some destructive operation in the tracked tree resolves to a
path at or under it AND that path contains tracked files. The root is the resolved
directory (or the file's parent), with any root that is a prefix of another dropped so
the set is an antichain.

Output: `evidence_roots.json` -- the guard's pin. It carries, per root, the tracked file
count MEASURED at derivation time. That count is a FLOOR, not an equality: the guard
ratchets on DECREASE only. F-T283-7 measured the opposite shape going red on sanctioned
work -- `attest_population_pin.json` pinned 231 legacy sidecars, `main` had moved to 253
through the sanctioned `cap*.sh` chain, and the ratchet failed on captures the program
had asked for. A decrease-only ratchet cannot have that failure mode.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def tracked(path):
    r = subprocess.run(["git", "ls-files", "-z", "--", path], cwd=ROOT, capture_output=True)
    return [x for x in r.stdout.decode("utf-8", "replace").split("\0") if x]


def main():
    adj = json.load(open(os.path.join(HERE, "adjudication.json")))
    cand = {}
    for s in adj["sites"]:
        # ONLY adjudicated defects contribute a protected root. Deriving the set from the
        # raw census instead produced exactly one root -- `.softhouse`, 6777 tracked files
        # -- because site C1 (fire-program.sh's atomic RESUME.md replace, correct by
        # design) contributes the parent `.softhouse`, which is a prefix of every other
        # root. A guard over that root blocks every future fire. The adjudication is what
        # keeps the guard narrow; a census alone cannot.
        if s["verdict"] not in ("DEFECT", "UNDECLARED"):
            continue
        t = s.get("target")
        if not t:
            continue
        # A6's operand is `rm -rf "$EV/red" "$EV/green"` -- TWO roots in one site.
        for part in t.split(" + "):
            part = part.strip().replace("/*.json", "").replace("/*", "")
            if not part:
                continue
            if not os.path.isdir(os.path.join(ROOT, part)):
                part = os.path.dirname(part)
            cand.setdefault(part, []).append(s["id"])
    # The parity vector store carries no adjudicated DEFECT, and is protected anyway:
    # B3/B4 mutate real ledger vectors in place with NO `trap`, so a kill between plant
    # and restore leaves a poisoned vector in the working tree. Stated, not assumed.
    cand.setdefault(".softhouse/vectors", []).append("B3/B4 residual kill window")
    cand = {c: v for c, v in cand.items() if c and c != "." and tracked(c)}
    # antichain: drop any root that lives under another root
    roots = sorted(c for c in cand
                   if not any(c != d and c.startswith(d.rstrip("/") + "/") for d in cand))
    assert ".softhouse" not in roots, "the root set collapsed to the whole tree"

    pin = {
        "_what": "T304 -- roots holding COMMITTED EVIDENCE that a tracked instrument is "
                 "measured to destroy. Graded by 30-evidence-guard.sh.",
        "_direction": "DECREASE-ONLY RATCHET. `min_tracked_files` is a FLOOR. Adding "
                      "evidence is always allowed and never requires moving the pin; "
                      "removing it is a failure. This is the shape F-T283-7 asked for: "
                      "the ratchet it measured pinned an EQUALITY and went red on 22 "
                      "sanctioned tierA-a2 captures.",
        "_derivation": "25-derive-protected-roots.py, from evidence/20-resolved.json, "
                       "which comes from 10-census.py over `git ls-files`.",
        "roots": [{"path": p, "min_tracked_files": len(tracked(p)), "why": cand[p]}
                  for p in roots],
    }
    out = os.path.join(HERE, "evidence_roots.json")
    with open(out, "w") as fh:
        json.dump(pin, fh, indent=2)
    print("derived %d protected root(s):" % len(roots))
    for r in pin["roots"]:
        print("  %-70s %5d tracked" % (r["path"], r["min_tracked_files"]))
    print("wrote %s" % out)


if __name__ == "__main__":
    sys.exit(main())
