#!/usr/bin/env python3
"""T296 review probe, step 2.

The first two-arm run showed the probe vector being refused by a DIFFERENT gate --
`graded_against is empty` -- which meant the capability gate was never the thing
deciding. This adds a placeholder kill claim so that gate is satisfied and the
CAPABILITY gate becomes the only remaining thing that could refuse the vector.
The claim itself is a placeholder and is never asserted as true of anything.
"""
import json
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "LDG-REFUSE-04-PROBE-future-dated-entry.json")

with open(P) as fh:
    v = json.load(fh)

v["graded_against"] = [{
    "impl": "ledger-wrong-openingbalance-posted-entries-ignored",
    "kind": "structural",
    "margin_minor": "0",
    "divergent_cells": ["refusal.code", "refusal.message"],
    "note": ("T296 PROBE ONLY -- a placeholder kill claim, present solely so the vector "
             "clears the non-empty graded_against gate and the CAPABILITY gate becomes "
             "the only thing left that could refuse it."),
}]

with open(P, "w") as fh:
    fh.write(json.dumps(v, indent=2) + "\n")
print("added graded_against to", P)
