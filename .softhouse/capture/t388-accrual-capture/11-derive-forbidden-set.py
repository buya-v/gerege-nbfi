#!/usr/bin/env python3
"""T388 -- DERIVE the set of GL accounts that a PROMOTED vector reads.

WHY THIS FILE EXISTS. The task that raised T388 handed over a list ("gl 16 / 17 / 21")
and then told me not to trust it, and it is right: the same numbers in
`.softhouse/vectors/capabilities-ledger.json` have already gone stale twice (gl 16
restated 16 -> 20 -> 21, gl 21 8 -> 12 -> 13). A list of accounts typed into prose is
exactly the artefact this program keeps being bitten by. So the set is DERIVED here,
from the vector JSON on disk, on every run.

WHAT IT READS, and therefore what its answer is a statement about:

  * every file under .softhouse/vectors/<context>/*.json -- the PROMOTED corpus. A
    file not in the store is not promoted and is not consulted;
  * every STORE-LEVEL json at .softhouse/vectors/*.json -- `capabilities-ledger.json`
    in particular, whose `unposted_slots` rows name gl 18 / 22 / 16 and are PRINTED BY
    THE HARNESS on every run. Those accounts are named by the store even though no
    vector carries a leg on 22, so they belong in the forbidden set;
  * every JSON key anywhere in either whose name ends in `gl_account_id` (this catches
    `gl_account_id` and `contra_gl_account_id`, and would catch a new one);
  * `provenance.capture_ref`, to decide WHICH INSTANCE each vector's accounts live on.

THE INSTANCE SPLIT IS THE POINT, AND IT IS NOT COSMETIC. LDG-05/06/07 were captured on
THROWAWAY Fineract instances stood up and torn down by
`.softhouse/capture/t305-.../throwaway/run-all.sh` and `t327-.../throwaway/run-all.sh`.
Their `gl_account_id: 1..4` name accounts in a database that no longer exists; on the
STANDING oracle, id 1 is `10000 Assets` and id 4 is `10201 Loan Portfolio`. Merging the
two id spaces would produce a forbidden set that is both too large and wrong about why.

OUTPUT: the forbidden set per instance, the per-vector attribution, and -- if
`--check` is given a list of account ids -- a PASS/FAIL disjointness verdict with a
non-zero exit on overlap. It reads only files; it cannot move the oracle.

NO FLOAT: no monetary value is parsed, compared or printed. Account ids are integers.
"""
import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
VECTORS = os.path.join(REPO, ".softhouse", "vectors")

# A capture_ref under one of these prefixes was taken on a THROWAWAY instance, not on the
# standing reference oracle. Derived from the rigs' own README/run-all.sh, which stand an
# instance up and tear it down; stated as a prefix list so a reader can check each one.
THROWAWAY_PREFIXES = (
    ".softhouse/capture/t305-openingbalance-accepting-side/throwaway/",
    ".softhouse/capture/t327-closure-accepting-side/throwaway/",
)

ACCOUNT_KEY = re.compile(r"gl_account_id$")


def walk_accounts(node, out):
    """Collect every integer under a key ending in gl_account_id, at any depth."""
    if isinstance(node, dict):
        for k, v in node.items():
            if ACCOUNT_KEY.search(k) and isinstance(v, int):
                out.add(v)
            else:
                walk_accounts(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_accounts(v, out)


def main(argv):
    check = None
    if "--check" in argv:
        i = argv.index("--check")
        check = sorted({int(x) for x in argv[i + 1].split(",") if x.strip()})

    if not os.path.isdir(VECTORS):
        print("REFUSING: no vector store at %s -- nothing to derive from." % VECTORS)
        return 2

    contexts = sorted(
        d for d in os.listdir(VECTORS)
        if os.path.isdir(os.path.join(VECTORS, d)) and not d.startswith("_")
    )

    rows = []
    for ctx in contexts:
        for fn in sorted(os.listdir(os.path.join(VECTORS, ctx))):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(VECTORS, ctx, fn)
            with open(path) as fh:
                doc = json.load(fh)
            accounts = set()
            walk_accounts(doc, accounts)
            ref = (doc.get("provenance") or {}).get("capture_ref", "")
            instance = "throwaway" if ref.startswith(THROWAWAY_PREFIXES) else "standing-oracle"
            rows.append((ctx, fn, doc.get("class", "?"), instance, sorted(accounts), ref))

    # Store-level files. They have no provenance and no instance of their own; every
    # account they name is a STANDING-ORACLE account, because that is the instance the
    # capability registry describes.
    for fn in sorted(os.listdir(VECTORS)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(VECTORS, fn)) as fh:
            doc = json.load(fh)
        accounts = set()
        walk_accounts(doc, accounts)
        rows.append(("<store>", fn, "store", "standing-oracle", sorted(accounts), ""))

    print("T388 -- GL ACCOUNTS READ BY THE PROMOTED VECTOR STORE, DERIVED")
    print("vector store: %s" % VECTORS)
    print("contexts    : %s" % ", ".join(contexts))
    print("vectors read: %d" % len(rows))
    print()
    print("%-14s %-64s %-8s %-15s %s" % ("context", "vector", "class", "instance", "gl_account_ids"))
    print("-" * 150)
    for ctx, fn, cls, inst, accs, _ref in rows:
        print("%-14s %-64s %-8s %-15s %s" % (ctx, fn, cls, inst, accs if accs else "-"))
    print()

    standing = set()
    throwaway = set()
    for _ctx, _fn, _cls, inst, accs, _ref in rows:
        (standing if inst == "standing-oracle" else throwaway).update(accs)

    print("FORBIDDEN SET on the STANDING REFERENCE ORACLE (the instance T388 writes to):")
    print("  %s" % sorted(standing))
    print("FORBIDDEN SET on the THROWAWAY instances (a DIFFERENT id space; listed, not merged):")
    print("  %s" % sorted(throwaway))
    print()
    print("Provenance of every vector counted as THROWAWAY:")
    for _ctx, fn, _cls, inst, _accs, ref in rows:
        if inst == "throwaway":
            print("  %-64s %s" % (fn, ref))
    print()

    if check is None:
        print("no --check given; set derived only.")
        return 0

    overlap = sorted(set(check) & standing)
    print("DISJOINTNESS CHECK")
    print("  accounts T388 created : %s" % check)
    print("  forbidden (standing)  : %s" % sorted(standing))
    print("  intersection          : %s" % (overlap if overlap else "EMPTY"))
    if overlap:
        print("  VERDICT: FAIL -- T388 would move a GL account a promoted vector reads.")
        return 1
    print("  VERDICT: PASS -- T388's accounts are disjoint from the promoted corpus.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
