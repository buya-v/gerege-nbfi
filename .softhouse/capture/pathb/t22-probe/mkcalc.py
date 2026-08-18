#!/usr/bin/env python3
"""T22 audit probe: build reproduction calc payloads identical to the committed
Path B ones except `productId`, which is offset by +4 because re-running
REPRODUCE.md on the same tenant allocates new product ids (5-8 instead of 1-4).
Clients are NOT re-created: fixture clients 1 and 2 already carry the required
activation dates, so `clientId` is unchanged."""
import collections
import json
import os

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(W, "t22-probe")
OFFSET = 4

for f in ("calc-B-01-baseline", "calc-B-02-multiplesof100",
          "calc-B-03-diycs-fullleapyear", "calc-B-04-diycs-feb29only"):
    o = json.load(open(os.path.join(W, "req", f + ".json")),
                  object_pairs_hook=collections.OrderedDict)
    o["productId"] = o["productId"] + OFFSET
    with open(os.path.join(P, "req", f + "-repro.json"), "w") as fh:
        json.dump(o, fh, indent=1)
    print("wrote", f + "-repro.json", "productId ->", o["productId"])
