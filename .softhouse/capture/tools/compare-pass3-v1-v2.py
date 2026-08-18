#!/usr/bin/env python3
"""
T25 — prove the pass-3 RE-RUN changed only what is RECORDED, never a number.

The T21 audit required `periodFromDate`, `feeAmount` and `penaltyAmount` to be emitted and the
pass-3 captures re-run (P0-3). A re-run is only safe to accept if every value the OLD emitter
printed is still printed, byte for byte, by the new one. This script asserts exactly that:

  * same capture ids, same order;
  * every `inputs` key present in v1 has an IDENTICAL value in v2;
  * every `observed` scalar present in v1 has an IDENTICAL value in v2;
  * every period present in v1 has an IDENTICAL value for every key v1 emitted;
  * and it REPORTS (does not fail on) the keys v2 adds.

Comparison is on the raw emitted strings — no float is constructed anywhere, and money is
additionally re-checked in integer minor units.

    python3 compare-pass3-v1-v2.py out/capture-prod-raw.json out/capture-prod-v2-raw.json

Exit 0 = no previously-recorded value moved. Exit 1 = something moved, and the OBSERVATION wins:
the re-run must then be investigated before anything is promoted.
"""
import json
import sys
from decimal import Decimal

# v1 emitted `principal` for a DISBURSEMENT row and nothing else; v2 adds periodFromDate/balance.
# We compare only the keys v1 actually had.


def minor(s, dp):
    return int((Decimal(s) * (10 ** dp)).to_integral_value())


def main():
    v1 = json.load(open(sys.argv[1]))
    v2 = json.load(open(sys.argv[2]))
    rc = 0
    added_keys = set()

    ids1 = [c["id"] for c in v1["captures"]]
    ids2 = [c["id"] for c in v2["captures"]]
    if ids1 != ids2:
        print(f"FAIL capture ids differ:\n  v1 {ids1}\n  v2 {ids2}")
        return 1
    print(f"{'capture':<14} {'inputs':>8} {'totals':>8} {'periods':>8}   verdict")

    for c1, c2 in zip(v1["captures"], v2["captures"]):
        bad = []
        for k, want in c1["inputs"].items():
            got = c2["inputs"].get(k, "<<MISSING>>")
            if str(got) != str(want):
                bad.append(f"inputs.{k}: v1={want!r} v2={got!r}")
        o1, o2 = c1["observed"], c2["observed"]
        for k, want in o1.items():
            if k == "periods":
                continue
            got = o2.get(k, "<<MISSING>>")
            if str(got) != str(want):
                bad.append(f"observed.{k}: v1={want!r} v2={got!r}")
        p1, p2 = o1["periods"], o2["periods"]
        if len(p1) != len(p2):
            bad.append(f"period count v1={len(p1)} v2={len(p2)}")
        else:
            for i, (r1, r2) in enumerate(zip(p1, p2)):
                for k, want in r1.items():
                    got = r2.get(k, "<<MISSING>>")
                    if str(got) != str(want):
                        bad.append(f"period[{i}].{k}: v1={want!r} v2={got!r}")
                added_keys |= set(r2) - set(r1)
        added_keys |= set(o2) - set(o1)
        # money re-checked in integer minor units, independently of the string compare
        dp = int(c1["inputs"]["currencyDecimalPlaces"])
        for i, (r1, r2) in enumerate(zip(p1, p2)):
            for k in ("principal", "interest", "total", "balance", "totalOutstandingBalance"):
                if k in r1 and k in r2 and minor(r1[k], dp) != minor(r2[k], dp):
                    bad.append(f"period[{i}].{k} minor units differ")
        verdict = "IDENTICAL" if not bad else "CHANGED"
        if bad:
            rc = 1
        print(f"{c1['id']:<14} {len(c1['inputs']):>8} {len(o1) - 1:>8} {len(p1):>8}   {verdict}")
        for b in bad:
            print(f"    !! {b}")

    print()
    print("keys ADDED by the re-run (recorded, not a change to any value):",
          ", ".join(sorted(added_keys)) or "(none)")
    print("top-level keys added:", ", ".join(sorted(set(v2) - set(v1))) or "(none)")
    print("VERDICT:", "no previously-recorded value moved" if rc == 0 else "A VALUE MOVED — investigate")
    return rc


if __name__ == "__main__":
    sys.exit(main())
