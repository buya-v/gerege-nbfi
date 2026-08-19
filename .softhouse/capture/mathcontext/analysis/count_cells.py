#!/usr/bin/env python3
"""How many cells did T42 actually compare?  Contacts no oracle."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"


def n(c):
    o = c.get("observed")
    return 0 if o is None else 4 + sum(len(p) for p in o["periods"])


d = json.load(open(OUT / "t42-mathcontext.json"))
caps = {c["id"]: c for c in d["captures"]}

tot = 0
threw = 0
per = {}
for base in sorted({k[: len("T42-MX-00")] for k in caps if k.startswith("T42-MX-")}):
    a = caps[base + "-A"]
    cells = n(a)
    per[a["shape"]] = cells
    for suf in ("-B", "-E", "-C", "-D"):
        if caps[base + suf].get("observed") is not None:
            tot += cells
        else:
            threw += 1
print("(a) MATRIX")
print("  cells per shape:", per)
print(f"  total cells compared: {tot}   (plus {threw} cases that THREW, which is the "
      f"absence-probe result rather than a comparison)")

tp1 = 0
for base in sorted({k[: len("T42-PREC-00")] for k in caps if k.startswith("T42-PREC-")}):
    tp1 += n(caps[base + "-p19"]) * 2  # 19-vs-12 and 19-vs-8
print("(b) PRECISION SWEEP, capture 1 (48 shapes x {19v12, 19v8}):", tp1, "cells")

d2 = json.load(open(OUT / "t42-mathcontext2.json"))
c2 = {c["id"]: c for c in d2["captures"]}
tp2 = 0
nshapes = 0
for base in sorted({k[: len("T42B-PREC-00")] for k in c2 if k.startswith("T42B-PREC-")}):
    tp2 += n(c2[base + "-p19"])
    nshapes += 1
print(f"(b) PRECISION SWEEP, capture 2 ({nshapes} shapes x 19v12):", tp2, "cells")

tw = 0
for base in sorted({k[: -len("ord4")] for k in c2 if k.startswith("T42B-P")
                    and "PREC" not in k}):
    for ordv in (1, 0, 6):
        tw += n(c2[base + f"ord{ordv}"])
print("(a) WIRING comparison, capture 2:", tw, "cells")
print()
print("TOTAL cells compared by T42:", tot + tp1 + tp2 + tw)
