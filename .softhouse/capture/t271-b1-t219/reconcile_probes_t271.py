#!/usr/bin/env python3
"""T271 -- reconcile the two independent re-derivations of the 6-of-7 BY RUNNING THEM.

P-83: *two independent movements of one pinned number reconcile by RUNNING, never by arithmetic.*
The 6-of-7 has now been moved three times -- T262's review, the killed 20260822-140002 worker's
`rederive_t219_carriers.py`, and T271's `independent_recheck_t271.py`, which was written without
reusing the second one's derivations. This file is the mechanical form of that rule: it EXECUTES
both surviving instruments in this repository, parses each one's probe line, and refuses if any
shared figure differs by one.

It also refuses if either probe line is ABSENT, because an exit code alone cannot tell a refusal
from a crash before the measurement (P-84 -- read the probe line's PRESENCE before its VALUE).

WHAT IT DOES NOT ESTABLISH: that either instrument is right. Two instruments can agree and both be
wrong. It establishes only that the number this task reports is not one instrument's opinion.

EXIT: 0 both ran and every shared figure agrees; 1 a REAL measured disagreement or a missing probe
line; 2 usage/IO error. Never conflated (P-80).
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T271-RECONCILE:"

# (script, probe prefix, {sharedName: fieldNameInThatProbe})
INSTRUMENTS = [
    (HERE / "rederive_t219_carriers.py", "T271-REDERIVE:",
     {"carriers": "carriers", "agreeREG": "agreeREG", "agreeCORR": "agreeCORR",
      "agreeUNCOND": "agreeUNCOND", "structureHolds": "structureHolds"}),
    (HERE / "independent_recheck_t271.py", "T271-INDEP:",
     {"carriers": "carriers", "agreeREG": "agreeREG", "agreeCORR": "agreeCORR",
      "agreeUNCOND": "agreeUNCOND", "structureHolds": "structureHolds"}),
]

# The figures this task's handoff and acknowledgement register state. Pinned here so that a
# future edit to either instrument that changes the answer goes RED instead of quietly restating
# a different number. This is a PIN ON A MEASUREMENT, not a substitute for taking it.
EXPECTED = {"carriers": "7", "agreeREG": "4", "agreeCORR": "6", "agreeUNCOND": "7",
            "structureHolds": "6"}


def fields(out: str, prefix: str):
    line = next((l for l in out.splitlines() if l.startswith(prefix)), None)
    if line is None:
        return None
    d = {"state": line[len(prefix):].split()[0]}
    for tok in line.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            d[k] = v
    return d


def main() -> int:
    print("T271 -- reconcile the two independent re-derivations BY RUNNING THEM (P-83)")
    print("=" * 96)
    problems = []
    measured = {}
    for path, prefix, mapping in INSTRUMENTS:
        if not path.exists():
            print(f"ERROR: instrument absent: {path}", file=sys.stderr)
            return 2
        p = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
        out = p.stdout + p.stderr
        f = fields(out, prefix)
        print(f"  {path.name:<32} exit {p.returncode}   probe {'PRESENT' if f else 'ABSENT'}")
        if f is None:
            problems.append(f"{path.name}: NO probe line {prefix!r} -- it died before it measured, "
                            "and an exit code alone cannot tell that from a refusal (P-84)")
            continue
        if p.returncode != 0 or f.get("state") != "GREEN":
            problems.append(f"{path.name}: state={f.get('state')!r} exit={p.returncode}, "
                            "wanted GREEN/0")
        measured[path.name] = {k: f.get(src) for k, src in mapping.items()}
        print(f"      {measured[path.name]}")

    print()
    if len(measured) == len(INSTRUMENTS):
        names = list(measured)
        a, b = measured[names[0]], measured[names[1]]
        for k in sorted(set(a) | set(b)):
            same = a.get(k) == b.get(k)
            pin = EXPECTED.get(k)
            pin_ok = (a.get(k) == pin)
            flag = "OK " if (same and pin_ok) else "!! "
            print(f"  {flag}{k:<16} {names[0]}={a.get(k)!r}  {names[1]}={b.get(k)!r}  "
                  f"pinned={pin!r}")
            if not same:
                problems.append(f"{k}: {names[0]} says {a.get(k)!r}, {names[1]} says {b.get(k)!r}")
            elif not pin_ok:
                problems.append(f"{k}: both instruments say {a.get(k)!r}, this task's handoff and "
                                f"acknowledgement register say {pin!r}")
    else:
        problems.append("fewer than two instruments produced a probe line; nothing was reconciled")

    print()
    print("  THIS DOES NOT ESTABLISH that either instrument is right -- two instruments can agree")
    print("  and both be wrong. Only that the 6-of-7 this task reports is not one file's opinion.")
    if problems:
        print()
        for p_ in problems:
            print(f"    !! {p_}")
    state = "REFUSED" if problems else "GREEN"
    print(f"{PROBE} {state} instruments={len(INSTRUMENTS)} reconciled={len(measured)} "
          f"disagreements={len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
