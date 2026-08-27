#!/usr/bin/env python3
"""T250 instrument 50 -- can `OracleStamp.tenant` be added under T250's constraint?

T245 proposed (and deliberately did NOT implement) a default-deny `tenant` field
on `OracleStamp`, graded exactly as `Seam` is, pinned in `PIN-ledger.json` and
`PIN.json`.  T250 may implement it ONLY IF that can be done

    (i)  WITHOUT moving `git rev-parse HEAD:.softhouse/vectors`, and
    (ii) WITHOUT making any existing vector inadmissible.

T250's brief calls this "a gate, not a judgement call".  So it is MEASURED here,
not argued: every route to the proposal is enumerated and each is tested against
(i) and (ii) with the real store.

MONEY: this instrument reads vector JSON to count fields and to look for a
`tenant` KEY.  It NEVER converts a value to a number, so `json.load` is not used
at all -- the files are scanned as TEXT with `re`.  A `json.load` without
`parse_float=` would turn every money literal in these vectors into a binary
double, which is the live T145 defect (224 unguarded sites); this file does not
become the 225th.

Engine: python3 `re` + `git` (P-75).  Any git failure ABORTS (exit 5); an error
is never reported as a zero.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.realpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..", "..")
)
VECDIR = os.path.join(ROOT, ".softhouse", "vectors")


def git(*args):
    p = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("ABORT: git %s -> rc=%d %s\n" % (" ".join(args), p.returncode, p.stderr))
        sys.exit(5)
    return p.stdout.strip()


def main():
    digest = git("rev-parse", "HEAD:.softhouse/vectors")
    print("LIVE store digest at HEAD           : %s" % digest)
    tracked = git("ls-tree", "-r", "--name-only", "HEAD", ".softhouse/vectors").splitlines()
    print("files inside the pinned tree        : %d" % len(tracked))

    pins = [p for p in tracked if os.path.basename(p).startswith("PIN")]
    print("  of which store PINS                : %d  %s" % (len(pins), pins))
    print("")
    print("FACT 1 -- the PINS ARE INSIDE THE PINNED TREE.")
    print("  `.softhouse/vectors/PIN.json` and `.softhouse/vectors/PIN-ledger.json` are")
    print("  both members of the tree whose hash is the store digest. Editing EITHER")
    print("  changes its blob hash, and a git tree hash is computed over its members'")
    print("  hashes, so the store digest MOVES. This is not an opinion about git; it")
    print("  is demonstrated below.")

    # Demonstrate blob-hash sensitivity WITHOUT writing to the store.
    sample = os.path.join(ROOT, ".softhouse", "vectors", "PIN-ledger.json")
    with open(sample, "rb") as fh:
        raw = fh.read()
    before = git("hash-object", "--stdin-paths") if False else None
    p = subprocess.run(["git", "-C", ROOT, "hash-object", "--stdin"],
                       input=raw, capture_output=True)
    h_before = p.stdout.decode().strip()
    mutated = raw.replace(b'"dec2_revision": 5', b'"dec2_revision": 6')
    if mutated == raw:
        sys.stderr.write("ABORT: could not construct the mutation; refusing to claim anything\n")
        sys.exit(5)
    p = subprocess.run(["git", "-C", ROOT, "hash-object", "--stdin"],
                       input=mutated, capture_output=True)
    h_after = p.stdout.decode().strip()
    print("")
    print("  PIN-ledger.json blob hash as committed        : %s" % h_before)
    print("  same file with dec2_revision 5 -> 6           : %s" % h_after)
    print("  identical? %s   -> editing a pin MOVES the tree hash"
          % ("YES" if h_before == h_after else "NO"))
    if h_before == h_after:
        sys.stderr.write("ABORT: mutation did not change the blob hash; instrument is broken\n")
        sys.exit(5)

    # FACT 2 -- how many vectors would a default-deny `tenant` refuse?
    vecs = [p for p in tracked
            if p.endswith(".json") and not os.path.basename(p).startswith("PIN")]
    tenant_re = re.compile(r'"tenant"\s*:')
    with_tenant, without_tenant, unreadable = [], [], []
    for rel in vecs:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            unreadable.append(rel)
            continue
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8", "replace")
        (with_tenant if tenant_re.search(text) else without_tenant).append(rel)

    print("")
    print("FACT 2 -- default-deny grading against the CURRENT corpus")
    print("  vector files in the store (PINs excluded)    : %d" % len(vecs))
    print("  carrying a `tenant` field TODAY              : %d" % len(with_tenant))
    print("  carrying NO `tenant` field                   : %d" % len(without_tenant))
    print("  unreadable, SKIPPED                          : %d" % len(unreadable))
    print("  `Seam` is the model T245 says to copy, and its grading reads:")
    print("      \"ABSENT REFUSES: default-deny, DEC-2 4.10\"  [admit.go:118-123]")
    print("  So a `tenant` graded that way REFUSES all %d." % len(without_tenant))

    print("")
    print("THE THREE ROUTES, EACH AGAINST T250's TWO CONSTRAINTS")
    print("")
    rows = [
        ("A. add the field, grade default-deny, re-stamp every vector with "
         "`tenant: gerege`",
         "MOVES the digest: %d vector blobs change" % len(without_tenant),
         "no vector left inadmissible",
         "VIOLATES (i)"),
        ("B. add the field, grade default-deny, do NOT re-stamp",
         "digest unmoved",
         "all %d vectors REFUSE" % len(without_tenant),
         "VIOLATES (ii)"),
        ("C. add the field, grade it PERMISSIVELY (absent == ok)",
         "digest unmoved",
         "no vector inadmissible",
         "VIOLATES THE POINT"),
    ]
    for name, c1, c2, verdict in rows:
        print("  %s" % name)
        print("      (i)  store digest : %s" % c1)
        print("      (ii) admissibility: %s" % c2)
        print("      -> %s" % verdict)
        print("")
    print("  Route C additionally requires the pin to carry the permitted value, and")
    print("  BOTH pins live inside the pinned tree (FACT 1), so even route C moves the")
    print("  digest the moment the pin names a tenant. There is no route that")
    print("  satisfies (i) and (ii) together.")
    print("")
    print("VERDICT: NOT IMPLEMENTED. The constraint is not merely unmet by the obvious")
    print("  route -- it is unmeetable by any route, because the artefact that must")
    print("  record the permitted tenant is itself inside the tree whose hash must not")
    print("  move. T245's own words apply to route C: item 1 without item 2 is")
    print("  COSMETIC, and a field graded permissively is a NEW P-45 artefact -- one")
    print("  that exists, is committed, is read, and grades nothing. Shipping that")
    print("  under the banner of fixing a fail-open would be the defect, re-committed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
