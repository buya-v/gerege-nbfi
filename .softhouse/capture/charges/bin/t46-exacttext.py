#!/usr/bin/env python3
"""T46 -- exact-text serialisation for Path B raw captures.  Closes T44 finding T44-X1.

T44-X1: "every charges response carries 207-214 bare (unquoted) non-integer JSON numbers --
9,122 occurrences, 245 distinct literals, max scale 6 -- because Fineract's REST layer
serialises BigDecimal as a JSON *number*.  The Path A payloads carry 0.  Today 0 of 245
literals change VALUE on a float round-trip, but 41 of 245 change TEXT, and the rule is
integer minor units, EXACT TEXT."

THE DECISION, and why
---------------------
1. **The raw response bytes remain the canonical artefact and are NOT rewritten.**  They are
   what the oracle said.  A JSON number literal on the wire is already exact text; the hazard
   is entirely in the CONSUMER, which is where `encoding/json` into `interface{}` yields a
   `float64` and Python's default decoder yields a `float`.  Mutating a committed capture to
   fix a consumer bug would destroy the only thing that makes it evidence.
   `patterns.md`: re-emit, never mutate.

2. **Every Path B capture gets an EXACT-TEXT SIDECAR**, `<capture>-exact.json`, in which every
   JSON number is re-emitted as a JSON **string** carrying the literal characters that were on
   the wire, byte for byte -- `1200000.00` becomes `"1200000.00"`, `0` becomes `"0"`,
   `14814.000000` keeps all six decimals.  The sidecar is a pure function of the committed
   bytes and can be regenerated at any time.

3. **No float is constructed anywhere in producing it.**  Python's `json` hands the RAW
   MATCHED LITERAL to `parse_float` / `parse_int`, so `json.loads(text, parse_float=str,
   parse_int=str)` yields the original characters and never touches a binary double.

4. **Identity is proved, not asserted.**  For every capture this tool re-reads the sidecar and
   the raw bytes and requires that the two agree leaf for leaf as TEXT, and that the sidecar
   contains ZERO bare JSON numbers.  A mismatch is exit 1.

5. **Admissibility rule that must travel with the promoted vectors:** a Path B vector is
   compared as EXACT DECIMAL TEXT, never through a JSON number.  Consumers read the sidecar,
   or read the raw bytes with an exact-decimal parser; nothing may parse a Path B capture into
   a binary float.

`--negative` corrupts one sidecar leaf IN MEMORY and shows the identity check failing.
"""
import json
import os
import pathlib
import re
import sys

CH = pathlib.Path(os.environ.get("T40_WORKTREE",
                                 str(pathlib.Path(__file__).resolve().parents[4]))) \
    / ".softhouse" / "capture" / "charges"
CAP = CH.parent  # .softhouse/capture

# Path B capture directories this tool serialises.
PATHB_DIRS = [CH / "out" / "fc", CH / "out" / "t46", CH / "out" / "control",
              CH / "out" / "attested"]
# Path A payloads, read only as a CONTROL: they must already carry zero bare numbers.
PATHA_FILES = [CAP / "periodratio" / "out" / "t39-periodratio.json",
               CAP / "periodratio" / "out" / "t46-periodratio-reemit.json",
               CAP / "periodratio" / "out" / "t46-periodratio-arms.json",
               CAP / "mathcontext" / "out" / "t42-mathcontext.json",
               CAP / "mathcontext" / "out" / "t42-mathcontext2.json"]

NUMBER_RE = re.compile(r'(?<![\w"])-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w"])')


def load_exact(text):
    """Decode with every number kept as its RAW LITERAL TEXT.  No float is constructed."""
    return json.loads(text, parse_float=str, parse_int=str)


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def bare_numbers(text):
    """Count unquoted JSON number tokens by stripping every string literal first."""
    stripped = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
    return NUMBER_RE.findall(stripped)


def main():
    negative = "--negative" in sys.argv
    written = 0
    problems = []
    all_literals = set()
    total_occurrences = 0

    print("## Path B -- exact-text sidecars")
    print()
    print("| capture | bare JSON numbers | distinct literals | max scale | sidecar leaves | identity |")
    print("|---|---:|---:|---:|---:|---|")

    for d in PATHB_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json") or f.endswith("-exact.json"):
                continue
            raw_path = d / f
            text = raw_path.read_text()
            try:
                doc = load_exact(text)
            except json.JSONDecodeError:
                continue

            nums = bare_numbers(text)
            total_occurrences += len(nums)
            all_literals.update(nums)
            scales = [len(n.split(".")[1]) for n in nums if "." in n]

            sidecar = raw_path.with_name(raw_path.stem + "-exact.json")
            sidecar.write_text(json.dumps(doc, indent=1, ensure_ascii=False,
                                          sort_keys=False) + "\n")
            written += 1

            # ---- IDENTITY PROOF -------------------------------------------------------
            back = json.loads(sidecar.read_text())        # plain load: everything is a string
            if negative and written == 1:
                first_key = next(iter(back))
                back[first_key] = "CORRUPTED"
                print(f"| (negative run: {f} leaf `{first_key}` corrupted in memory) | | | | | |")
            lhs = dict(leaves(doc))
            rhs = dict(leaves(back))
            ident = "OK"
            if lhs.keys() != rhs.keys():
                problems.append(f"{f}: sidecar leaf SET differs from the raw capture")
                ident = "**LEAF SET DIFFERS**"
            else:
                moved = [k for k in lhs if lhs[k] != rhs[k]]
                if moved:
                    problems.append(f"{f}: {len(moved)} leaf(s) MOVED, first {moved[0]}: "
                                    f"{lhs[moved[0]]!r} -> {rhs[moved[0]]!r}")
                    ident = f"**{len(moved)} MOVED**"
            side_nums = bare_numbers(sidecar.read_text())
            if side_nums:
                problems.append(f"{sidecar.name}: still carries {len(side_nums)} bare JSON numbers")
                ident = "**NOT EXACT TEXT**"

            print(f"| {f} | {len(nums)} | {len(set(nums))} | {max(scales) if scales else 0} "
                  f"| {len(lhs)} | {ident} |")

    print()
    print(f"Path B: {written} sidecars written; {total_occurrences} bare JSON number occurrences "
          f"across {len(all_literals)} distinct literals in the raw captures.")
    changes_text = sorted(l for l in all_literals
                          if "." in l and (l.rstrip("0").rstrip(".") or "0") != l)
    print(f"Distinct literals whose TEXT a float round-trip would change (trailing zeros or "
          f"redundant scale): {len(changes_text)}")
    print()

    print("## Path A control -- must already be zero")
    print()
    print("| payload | bare JSON numbers outside metadata |")
    print("|---|---:|")
    for p in PATHA_FILES:
        if not p.exists():
            continue
        doc = load_exact(p.read_text())
        # Path A money leaves are JSON strings; the only bare numbers are structural metadata
        # (precision, ordinals, counts) -- count the MONEY-SHAPED ones, i.e. any bare number
        # with a decimal point.
        decimals = [n for n in bare_numbers(p.read_text()) if "." in n]
        print(f"| {p.parent.parent.name}/{p.name} | {len(decimals)} |")
        if decimals:
            problems.append(f"{p.name}: Path A payload carries {len(decimals)} bare decimal "
                            "numbers -- money must be exact text there")

    print()
    if problems:
        print(f"RESULT: {len(problems)} PROBLEM(S)")
        for p in problems:
            print("  ! " + p)
        return 1
    print("RESULT: every sidecar reproduces its raw capture leaf for leaf as TEXT, and no "
          "sidecar carries a bare JSON number.")
    print()
    print("ADMISSIBILITY RULE: a Path B vector is compared as EXACT DECIMAL TEXT, never through")
    print("a JSON number.  Nothing downstream may parse a Path B capture into a binary float.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
