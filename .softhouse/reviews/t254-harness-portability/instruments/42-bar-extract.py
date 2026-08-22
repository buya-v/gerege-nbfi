#!/usr/bin/env python3
"""T254 reviewer instrument: extract the load-bearing BAR facts from a run.

P-83: the PROBE LINE'S PRESENCE is reported BEFORE its value. Exit 2 alone is
ambiguous -- several exit-2 paths run before the probe, one of them a failed
HARD guard -- so "was the probe line printed at all" is a separate, prior
question from "what did it say".

P-80: every number is read out of an enumerated line set. A missing key is
printed as MISSING (a measured absence over a known population), never as 0.
No shell grep is involved.

Usage: 42-bar-extract.py <stdout> <stderr> <label>
"""
import re
import sys

so_path, se_path, label = sys.argv[1], sys.argv[2], sys.argv[3]
so = open(so_path, encoding="utf-8", errors="replace").read()
se = open(se_path, encoding="utf-8", errors="replace").read()
both = so + "\n" + se

print("=" * 74)
print(f"BAR FACTS — {label}")
print("=" * 74)

# ---- 1. PROBE LINE: PRESENCE FIRST (P-83) ---------------------------------
probe_lines = [l for l in both.splitlines() if re.search(r"\bprobe\s*=", l)]
print(f"[1] PROBE LINE PRESENT? .......... {'YES' if probe_lines else 'NO — NOT PRINTED'}")
print(f"    (matched {len(probe_lines)} line(s) containing 'probe =')")
if probe_lines:
    for l in probe_lines:
        print(f"[2] PROBE LINE VALUE ............. {l.strip()}")
else:
    print("[2] PROBE LINE VALUE ............. N/A — the run died before the probe.")
print()

# ---- 2. VERDICT -----------------------------------------------------------
verdict = [l for l in both.splitlines() if "VERDICT" in l]
print(f"[3] VERDICT LINE(S) .............. {len(verdict)}")
for l in verdict:
    print(f"    {l.strip()}")
print()

# ---- 3. THE PINNED NUMBERS THE DRIVER GAVE AS BASELINE --------------------
def one(pat, what):
    m = re.search(pat, both)
    print(f"    {what:<44} {m.group(0).strip() if m else 'MISSING'}")

print("[4] BASELINE INVARIANTS (driver baseline @ c0e88c6: PASS, 46 parity /")
print("    7884 cells, frontier 11 == pinned 11, 9 exemption pins, 6/6 killed)")
one(r"\d+\s+parity vectors match[^\n]*", "parity vectors / cells")
one(r"front(?:ier)?[^\n]*\d+[^\n]*", "fail-open frontier line")
one(r"[^\n]*exemption[^\n]*", "exemption census line")
one(r"[^\n]*wrong[^\n]*implementation[^\n]*", "wrong-impl line")
print()

# ---- 4. FAIL-OPEN GUARD DETAIL --------------------------------------------
fo = [l for l in both.splitlines() if "fail-open" in l.lower()]
print(f"[5] FAIL-OPEN GUARD LINES ........ {len(fo)}")
for l in fo:
    print(f"    {l.strip()[:150]}")
print()

# ---- 5. TIER / t234 residue signal ----------------------------------------
tier = [l for l in both.splitlines() if re.search(r"TIER[123]", l)]
print(f"[6] LINES MENTIONING A TIER ...... {len(tier)}")
for l in tier[:25]:
    print(f"    {l.strip()[:150]}")
print()

# ---- 6. TOOLCHAIN PROVENANCE (T267) ---------------------------------------
tc_so = [l for l in so.splitlines() if "go-env" in l or "gerege go-env" in l]
tc_se = [l for l in se.splitlines() if "go-env" in l or "gerege go-env" in l]
print(f"[7] TOOLCHAIN NOTICE on STDOUT ... {len(tc_so)} line(s)")
print(f"    TOOLCHAIN NOTICE on STDERR ... {len(tc_se)} line(s)")
print()

# ---- 7. GUARD TALLY -------------------------------------------------------
gl = [l for l in both.splitlines() if re.match(r"\s*(guard|gate)[-_ ]", l, re.I)]
print(f"[8] GUARD/GATE-PREFIXED LINES .... {len(gl)}")
print()
print(f"[9] stdout lines={len(so.splitlines())}  stderr lines={len(se.splitlines())}")
print("=" * 74)
