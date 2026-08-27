#!/usr/bin/env python3
"""T305 -- replace the opening-balance capability row's gap paragraph with the closing one.

EDITS THE ENCODED STRING INSIDE THE RAW FILE, not a re-serialised document, so no other row is
reformatted and the diff is exactly one paragraph wide. The first version of this rig did the same
thing for the same reason.
"""
import json
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
CAP = os.path.join(REPO, ".softhouse/vectors/capabilities-ledger.json")
TAIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capability-tail.txt")

MARKER = "***** T305-ACCEPTING-SIDE-GAP -- OPEN, DECLARED, AND NOT CLOSEABLE ON THIS RIG. *****"

raw = open(CAP).read()
doc = json.load(open(CAP))
row = [c for c in doc["capabilities"] if c["name"] == "ledger.opening.balance.and.closure"]
if len(row) != 1:
    raise SystemExit("REFUSED: expected exactly one opening-balance capability row, found %d" % len(row))
old_evidence = row[0]["evidence"]
if MARKER not in old_evidence:
    raise SystemExit("REFUSED: the gap paragraph is not where this script expects it; refusing to guess")

head = old_evidence[: old_evidence.index(MARKER)]
new_evidence = head + open(TAIL).read().strip()

old_encoded = json.dumps(old_evidence)[1:-1]
new_encoded = json.dumps(new_evidence)[1:-1]
if raw.count(old_encoded) != 1:
    raise SystemExit("REFUSED: the encoded evidence string does not occur exactly once in the raw file")
open(CAP, "w").write(raw.replace(old_encoded, new_encoded))

check = json.load(open(CAP))
if len(check["capabilities"]) != len(doc["capabilities"]):
    raise SystemExit("REFUSED: capability count changed")
if "T305-ACCEPTING-SIDE-GAP" in open(CAP).read():
    raise SystemExit("REFUSED: the token is still present; conformance.sh would fail the bar")
print("capability row updated; %d capabilities intact; token removed" % len(check["capabilities"]))
