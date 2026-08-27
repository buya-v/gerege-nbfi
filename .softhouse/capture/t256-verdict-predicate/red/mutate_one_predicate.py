#!/usr/bin/env python3
"""T259 battery helper: copy a classification file, flipping exactly ONE named predicate from
true to false on exactly ONE named row. Aborts if the fixture assumption is not met, so the leg
can never silently degrade into "mutated nothing and still went red for another reason".

The SOURCE file is only ever READ. T114/T176: committed evidence is never written to.

NO FLOATING POINT: parse_float=Decimal on the read. (The re-serialisation would raise on a
Decimal, which is itself an assertion that this corpus contains no float literal -- measured
independently at 0 float-shaped tokens of 160.)

usage: mutate_one_predicate.py <src.json> <dst.json> <rowId> <predicateKey>
"""
import json
import sys
from decimal import Decimal

src, dst, row_id, key = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
doc = json.loads(open(src).read(), parse_float=Decimal)

n = 0
for container in doc.values():
    if not isinstance(container, list):
        continue
    for row in container:
        if isinstance(row, dict) and row.get("id") == row_id:
            if row.get(key) is not True:
                raise SystemExit(
                    f"FIXTURE ASSUMPTION BROKEN: {row_id}.{key} is {row.get(key)!r}, expected True")
            row[key] = False
            n += 1
if n != 1:
    raise SystemExit(f"FIXTURE ASSUMPTION BROKEN: mutated {n} rows, expected exactly 1")

with open(dst, "w") as fh:
    json.dump(doc, fh, indent=1)
print(f"mutated {row_id}.{key} True -> False; wrote {dst}")
