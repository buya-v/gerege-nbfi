#!/usr/bin/env python3
"""T22 audit probe: build reproduction product payloads that are byte-identical
to the committed Path B products except for `name` / `shortName`, which the
server enforces unique. Nothing else is touched."""
import collections
import json
import os

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(W, "t22-probe")

RENAME = {
    "product-1-baseline": ("T22 repro baseline", "T2A"),
    "product-2-multiplesof100": ("T22 repro mult100", "T2B"),
    "product-3-diycs-fullleapyear": ("T22 repro DIYCS FULL", "T2C"),
    "product-4-diycs-feb29only": ("T22 repro DIYCS FEB29", "T2D"),
}

for f, (name, short) in RENAME.items():
    src = os.path.join(W, "req", f + ".json")
    o = json.load(open(src), object_pairs_hook=collections.OrderedDict)
    o["name"] = name
    o["shortName"] = short
    with open(os.path.join(P, "req", f + "-repro.json"), "w") as fh:
        json.dump(o, fh, indent=1)
    print("wrote", f + "-repro.json")
