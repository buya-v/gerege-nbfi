#!/usr/bin/env python3
"""
T46 / M-5 — LEAF-BY-LEAF identity proof between the committed T42 capture 1 and the T46
re-emission that adds the object-echoed threaded-MathContext keys.

A published capture may be RE-EMITTED, never mutated.  The re-emission is admissible only if
EVERY value the committed payload publishes is byte-identical in the new one, and the only
differences anywhere are the keys that were deliberately ADDED.

Discipline: no float anywhere.  `json.load(..., parse_float=Decimal)`; every leaf compared as
the exact text the oracle emitted.

  exit 0 — identical on every previously published leaf
  exit 1 — at least one previously published leaf moved, or a case appeared/disappeared

Usage: python3 analysis/t46_m5_identity.py <committed.json> <re-emission.json>
"""
import json
import sys
from decimal import Decimal

ADDED_KEYS = {
    "threadedMathContext",
    "threadedMathContextPrecisionFromObject",
    "threadedMathContextRoundingModeFromObject",
    "wiring",
}
# Top-level keys allowed to differ, and why.
TOP_ALLOWED = {"harness"}


def leaves(node, prefix=""):
    out = {}
    if isinstance(node, dict):
        for k in node:
            out.update(leaves(node[k], prefix + "/" + k))
    elif isinstance(node, list):
        for i, x in enumerate(node):
            out.update(leaves(x, prefix + "[%d]" % i))
    else:
        if isinstance(node, float):
            raise SystemExit("FLOAT LEAF at %s -- parse_float=Decimal was bypassed" % prefix)
        out[prefix] = format(node, "f") if isinstance(node, Decimal) else str(node)
    return out


def main():
    a_path, b_path = sys.argv[1], sys.argv[2]
    a = json.load(open(a_path), parse_float=Decimal)
    b = json.load(open(b_path), parse_float=Decimal)

    print("=" * 96)
    print("T46 / M-5 identity proof")
    print("  committed   : %s" % a_path)
    print("  re-emission : %s" % b_path)
    print("=" * 96)

    bad = []

    # ---- 1. preamble ---------------------------------------------------------------------
    ka = {k for k in a if k != "captures"}
    kb = {k for k in b if k != "captures"}
    if ka != kb:
        bad.append("top-level keys differ: only in committed %s, only in re-emission %s"
                   % (sorted(ka - kb), sorted(kb - ka)))
    same_top = 0
    for k in sorted(ka & kb):
        if str(a[k]) != str(b[k]):
            if k in TOP_ALLOWED:
                print("  top-level %-30s DIFFERS (allowed): %r -> %r" % (k, a[k], b[k]))
            else:
                bad.append("top-level %s: %r -> %r" % (k, a[k], b[k]))
        else:
            same_top += 1
    print("  top-level keys identical: %d of %d" % (same_top, len(ka & kb)))

    # ---- 2. the case set -----------------------------------------------------------------
    ca = {c["id"]: c for c in a["captures"]}
    cb = {c["id"]: c for c in b["captures"]}
    if set(ca) != set(cb):
        bad.append("case ids differ: missing %s, extra %s"
                   % (sorted(set(ca) - set(cb))[:10], sorted(set(cb) - set(ca))[:10]))
    print("  cases: committed %d, re-emission %d, common %d"
          % (len(ca), len(cb), len(set(ca) & set(cb))))

    # ---- 3. every previously published leaf ----------------------------------------------
    total, moved, added = 0, 0, 0
    disagreements = []
    for cid in sorted(set(ca) & set(cb)):
        la = leaves(ca[cid])
        lb = leaves(cb[cid])
        for path, va in la.items():
            total += 1
            vb = lb.get(path, "<<ABSENT>>")
            if va != vb:
                moved += 1
                if len(bad) < 40:
                    bad.append("%s %s: %r -> %r" % (cid, path, va, vb))
        for path in lb:
            if path not in la:
                key = path.rsplit("/", 1)[-1]
                if key in ADDED_KEYS:
                    added += 1
                else:
                    bad.append("%s %s: UNEXPECTED new leaf %r" % (cid, path, lb[path]))

        # ---- 4. object echo must AGREE with the intent it supplements --------------------
        ia = cb[cid].get("inputs", {})
        if "threadedMathContextPrecisionFromObject" in ia:
            if str(ia["threadedMathContextPrecision"]) != str(ia["threadedMathContextPrecisionFromObject"]):
                disagreements.append("%s: precision intent %s vs object %s"
                                     % (cid, ia["threadedMathContextPrecision"],
                                        ia["threadedMathContextPrecisionFromObject"]))
            if str(ia["threadedMathContextRoundingMode"]) != str(ia["threadedMathContextRoundingModeFromObject"]):
                disagreements.append("%s: mode intent %s vs object %s"
                                     % (cid, ia["threadedMathContextRoundingMode"],
                                        ia["threadedMathContextRoundingModeFromObject"]))

    print()
    print("  previously published leaves compared : %d" % total)
    print("  leaves that MOVED                    : %d" % moved)
    print("  leaves ADDED by the re-emission      : %d  (%s)"
          % (added, ", ".join(sorted(ADDED_KEYS))))
    print()
    print("  M-5 substance: does the OBJECT echo agree with the INTENT the committed payload")
    print("  published under the object-named keys?")
    print("    cases with a disagreement: %d" % len(disagreements))
    for d in disagreements[:20]:
        print("      " + d)

    print()
    if bad:
        for x in bad:
            print("BREACH: " + x, file=sys.stderr)
        print("FAIL -- %d breach(es).  The re-emission is INADMISSIBLE." % len(bad))
        return 1
    if disagreements:
        print("FAIL -- the object echo DISAGREES with the intent on %d case(s).  Capture 1 would"
              " then be mis-attested in VALUE, not merely in wording." % len(disagreements))
        return 1
    print("PASS -- every one of the %d previously published leaves is byte-identical, %d keys "
          "added, and the object echo agrees with the intent on all %d cases."
          % (total, added, len(set(ca) & set(cb))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
