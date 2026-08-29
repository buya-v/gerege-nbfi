#!/usr/bin/env python3
"""T421 / F-T406-1 -- sweep EVERY json under .softhouse/vectors for a captured_at
that is a ROUND HOUR (mm:ss == 00:00) or that lies in the FUTURE relative to the
instant this script runs.

"Not found" is a statement about the SEARCH, so the search states its own extent:
every .json file under .softhouse/vectors is opened, every key whose name contains
"captur" is inspected wherever it sits in the tree (not just oracle.captured_at),
and files carrying NO such key are listed by name rather than passed over silently.

Decoded with parse_float=str / parse_int=str: this file must not turn a value into
a float in the act of checking the store.
"""
import json, os, sys, datetime

ROOT = ".softhouse/vectors"
now = datetime.datetime.now(datetime.timezone.utc)
print("SWEEP RUN AT UTC:", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
print("ROOT:", ROOT)

def walkkeys(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walkkeys(v, path + "." + k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walkkeys(v, path + "[%d]" % i)
    else:
        yield path, node

files = sorted(
    os.path.join(dp, fn)
    for dp, _, fns in os.walk(ROOT)
    for fn in fns if fn.endswith(".json")
)
print("FILES SCANNED:", len(files))

withts, without, roundhour, future = [], [], [], []
for f in files:
    with open(f) as fh:
        doc = json.load(fh, parse_float=str, parse_int=str)
    hits = [(p, v) for p, v in walkkeys(doc)
            if "captur" in p.lower() and isinstance(v, str)
            and len(v) >= 19 and v[4] == "-" and v[10] == "T"]
    if not hits:
        without.append(f)
        continue
    for p, v in hits:
        withts.append((f, p, v))
        # ROUND HOUR: minutes and seconds both zero. String comparison only.
        if v[14:19] == "00:00":
            roundhour.append((f, p, v))
        # FUTURE: lexicographic compare of two Z-suffixed ISO-8601 strings is a
        # chronological compare. No parsing, no arithmetic.
        if v[:19] > now.strftime("%Y-%m-%dT%H:%M:%S"):
            future.append((f, p, v))

print("FILES WITH >=1 capture timestamp:", len({f for f, _, _ in withts}),
      " timestamps found:", len(withts))
print("FILES WITH NONE (listed, not skipped):", len(without))
for f in without:
    print("   none:", f)
print()
print("ROUND-HOUR (mm:ss == 00:00):", len(roundhour))
for f, p, v in roundhour:
    print("   ROUND ", v, p, f)
print("FUTURE (> run instant):", len(future))
for f, p, v in future:
    print("   FUTURE", v, p, f)
print()
print("VERDICT:", "CLEAN" if not roundhour and not future else "OFFENDERS PRESENT")
sys.exit(0)
