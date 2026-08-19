#!/usr/bin/env python3
"""T46 -- the RE-EMISSION IDENTITY PROOF required by .softhouse/patterns.md.

  "Re-emit a capture input-for-input before you add cases to it.  T35 added columns to the
   pass-3 capture and proved 1560/1560 published values identical before trusting the new
   ones -- then deliberately declined to add new *cases* in the same pass, because that
   would have destroyed the identity check that makes the re-emission meaningful."

This compares T39's committed payload (`out/t39-periodratio.json`) against T46's re-emission
(`out/t46-periodratio-reemit.json`) LEAF BY LEAF.  Every leaf present in T39 must be present
in T46 with a byte-identical value.  T46 is allowed to carry EXTRA leaves (the
`threadedMathContext*` object echo and the `wiring` field that F39-3 required) and extra
top-level metadata; it is not allowed to change or drop one existing leaf.

Nothing here parses a money value as a number.  Every leaf is compared as TEXT
(`json.load(..., parse_float=str, parse_int=str)` would coerce; instead the raw text of each
leaf is taken from a decimal-exact reload).  No float is constructed anywhere in this file.

Exit 0 = identical.  Exit 1 = a value moved, which voids the re-emission.
"""
import json
import pathlib
import sys
from decimal import Decimal

HERE = pathlib.Path(__file__).resolve().parent.parent
OLD = HERE / "out" / "t39-periodratio.json"
NEW = HERE / "out" / "t46-periodratio-reemit.json"

# Keys T46 adds.  Their PRESENCE is checked; they are exempt from the "must exist in T39" rule.
ADDED_INPUT_KEYS = {
    "threadedMathContext",
    "threadedMathContextPrecision",
    "threadedMathContextRoundingMode",
    "wiring",
}
# Top-level metadata that legitimately differs (it names the task and the harness, not an
# observation).  Everything else at top level must match.
TOPLEVEL_EXEMPT = {"task", "harness", "question", "set"}


def load(path):
    # parse_float=Decimal, parse_int=int: no binary float is ever constructed.
    return json.loads(path.read_text(), parse_float=Decimal)


def leaves(obj, prefix=""):
    """Yield (path, value) for every scalar leaf."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def main():
    old = load(OLD)
    new = load(NEW)

    old_caps = {c["id"]: c for c in old["captures"]}
    new_caps = {c["id"]: c for c in new["captures"]}

    problems = []

    missing = sorted(set(old_caps) - set(new_caps))
    extra = sorted(set(new_caps) - set(old_caps))
    if missing:
        problems.append(f"re-emission DROPPED capture ids: {missing}")
    if extra:
        problems.append(f"re-emission ADDED capture ids in the identity pass: {extra} "
                        "-- new cases belong in a new pass with new ids")

    compared = 0
    for cid in sorted(set(old_caps) & set(new_caps)):
        o = dict(leaves(old_caps[cid]))
        n = dict(leaves(new_caps[cid]))
        for path, ov in o.items():
            compared += 1
            if path not in n:
                problems.append(f"{cid}: leaf {path} DISAPPEARED (was {ov!r})")
            elif n[path] != ov:
                problems.append(f"{cid}: leaf {path} MOVED  {ov!r} -> {n[path]!r}")
        for path in n:
            if path not in o:
                key = path.split(".")[-1]
                if key not in ADDED_INPUT_KEYS:
                    problems.append(f"{cid}: unexpected NEW leaf {path} = {n[path]!r}")
        # the added echo must actually be present on every case
        for k in ADDED_INPUT_KEYS:
            if f"inputs.{k}" not in n:
                problems.append(f"{cid}: required new leaf inputs.{k} is MISSING")

    # top-level metadata
    for k, v in old.items():
        if k in ("captures",) or k in TOPLEVEL_EXEMPT:
            continue
        compared += 1
        if new.get(k) != v:
            problems.append(f"top-level {k}: {v!r} -> {new.get(k)!r}")

    # money-shaped leaves must still be exact text, never a JSON number
    float_leaves = [p for p, v in leaves(new) if isinstance(v, Decimal)]
    if float_leaves:
        problems.append(f"re-emission carries {len(float_leaves)} BARE JSON NUMBER leaves "
                        f"(first: {float_leaves[0]}) -- Path A must emit exact text")

    print("T46 re-emission identity proof")
    print(f"  old payload : {OLD}")
    print(f"  new payload : {NEW}")
    print(f"  captures compared            : {len(set(old_caps) & set(new_caps))}")
    print(f"  leaves + top-level compared  : {compared}")
    print(f"  new leaves added per capture : {sorted(ADDED_INPUT_KEYS)}")
    if problems:
        print(f"  RESULT: {len(problems)} PROBLEM(S) -- re-emission is NOT identity-clean")
        for p in problems:
            print("    ! " + p)
        return 1
    print(f"  RESULT: {compared} of {compared} published values IDENTICAL. "
          "Re-emission is identity-clean; the added columns may be trusted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
