#!/usr/bin/env python3
"""T271 -- compare one top-level section of two classifier outputs, with NO FLOATING POINT.

Used by `prove_comment_only.sh`. Kept as a separate file rather than an inline heredoc so that
`lint_failopen_t259.py` scans it like every other instrument.

EXIT: 0 identical; 1 a REAL measured difference (and it is printed); 2 usage/IO/parse error.
Never conflated (P-80).
"""
import json
import sys
from decimal import Decimal
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print(f"usage: {Path(sys.argv[0]).name} <section> <fileA> <fileB>", file=sys.stderr)
        return 2
    section, pa, pb = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    try:
        a = json.loads(pa.read_text(), parse_float=Decimal)
        b = json.loads(pb.read_text(), parse_float=Decimal)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if section not in a or section not in b:
        print(f"ERROR: section {section!r} absent from one of the inputs", file=sys.stderr)
        return 2
    if a[section] == b[section]:
        print(f"    {section}: identical ({len(a[section])} entries)")
        return 0
    print(f"    {section}: DIFFER")
    print(f"      A ({pa.name}) : {json.dumps(a[section], default=str)[:400]}")
    print(f"      B ({pb.name}) : {json.dumps(b[section], default=str)[:400]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
