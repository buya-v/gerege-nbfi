#!/usr/bin/env python3
"""T259 battery helper: write a SCRATCH acknowledgement file that pins the ORIGINAL sha256 to a
scratch copy's path. The point of the leg is that the copy's bytes differ, so the block must be
reported VOID and its rows must go back to UNACKNOWLEDGED.

usage: make_scratch_ack.py <out.json> <targetPath> <sha256ToPin>
"""
import json
import sys

out, target, sha = sys.argv[1], sys.argv[2], sys.argv[3]
rows = [{"id": i, "predicate": "P2_totalInterestEqualsNEplusB",
         "disposition": "SCRATCH -- battery fixture, not a real acknowledgement",
         "reason": "SCRATCH -- battery fixture"}
        for i in ("T229-R600p0-N200-B201", "T229-R600p0-N200-B251", "T229-R600p0-N200-B299")]
blk = {"file": target, "sha256": sha,
       "gradedProposition": "SCRATCH -- battery fixture", "rows": rows}
with open(out, "w") as fh:
    json.dump({"acknowledgements": [blk]}, fh, indent=1)
