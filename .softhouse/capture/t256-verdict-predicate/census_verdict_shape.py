#!/usr/bin/env python3
"""T259 -- P-78 applied to T259's OWN fix, and P-40 applied to its scope.

T259's brief restricts what may be WRITTEN to `.softhouse/capture/t229-g8-site3/` and
`.softhouse/capture/t256-verdict-predicate/`. It does not restrict what may be MEASURED. This
census READS every JSON under `.softhouse/capture/` and reports, for each file that has the
classification shape at all:

    rows, predicate booleans, and DISAGREEMENTS -- rows carrying an affirmative verdict over a
    predicate they themselves recorded as false.

It writes nothing and fixes nothing. Its output is the backlog: a count of how many files carry
the T229 defect, so the size of the tail is a measured number rather than "probably just the one".

BOTH TERMS ARE COUNTED (P-67): files with the shape AND files without it; and files SKIPPED,
with the reason, are counted too (P-40).

NO FLOATING POINT: `parse_float=Decimal` on every read (T145). Nothing monetary is computed.

EXIT: 0 = census produced (a census REPORTS, it does not gate), 2 = error.
"""
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_verdict_predicate_agreement import (  # noqa: E402
    classify_verdict, is_verdict_key, key_class, walk_rows)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent  # .../repo
CAPTURE = ROOT / ".softhouse" / "capture"


def main() -> int:
    reg = json.loads((HERE / "boolean-key-register.json").read_text(), parse_float=Decimal)
    seen = shaped = unshaped = skipped_big = skipped_unparse = 0
    hits = []
    for p in sorted(CAPTURE.rglob("*.json")):
        seen += 1
        if p.stat().st_size > 8_000_000:
            skipped_big += 1
            continue
        try:
            doc = json.loads(p.read_text(), parse_float=Decimal)
        except (ValueError, UnicodeDecodeError, OSError) as exc:
            skipped_unparse += 1
            print(f"  SKIPPED (unparseable, counted): {p.relative_to(ROOT)}  "
                  f"{type(exc).__name__}")
            continue
        rows = list(walk_rows(doc))
        vrows = [(ck, i, r) for ck, i, r in rows
                 if any(is_verdict_key(k) and isinstance(v, str) for k, v in r.items())]
        if not vrows:
            unshaped += 1
            continue
        shaped += 1
        dis = 0
        for _ck, _i, r in vrows:
            affirm = any(classify_verdict(v) == "AFFIRMATIVE"
                         for k, v in r.items() if is_verdict_key(k) and isinstance(v, str))
            if not affirm:
                continue
            for k, v in r.items():
                if isinstance(v, bool) and v is False and key_class(reg, k)[0] == "PREDICATE":
                    dis += 1
        hits.append((str(p.relative_to(ROOT)), len(vrows), dis))

    print("T259 census -- classification-shaped JSON under .softhouse/capture/")
    print(f"  json files seen           : {seen}")
    print(f"  ... with the verdict shape: {shaped}")
    print(f"  ... without it            : {unshaped}")
    print(f"  ... SKIPPED, too large    : {skipped_big}")
    print(f"  ... SKIPPED, unparseable  : {skipped_unparse}")
    print()
    print("  files carrying the shape, and their disagreement count:")
    tot = 0
    for name, nrows, dis in sorted(hits, key=lambda h: -h[2]):
        tot += dis
        flag = "  <-- DISAGREEMENTS" if dis else ""
        print(f"    {dis:>3}  rows={nrows:<4} {name}{flag}")
    print(f"  TOTAL disagreements across the whole capture tree: {tot}")
    print()
    print("  NOTE: only `.softhouse/capture/t229-g8-site3/` and "
          "`.softhouse/capture/t256-verdict-predicate/`")
    print("  are in T259's write scope. Everything else above is REPORTED and left alone, and is")
    print("  recorded as backlog in the handoff. Counting it is the point (P-40).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
