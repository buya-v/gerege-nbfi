"""
T38 (B) -- P1-T34-2: exactly which committed harnesses record the DISBURSEMENT
row's outstanding balance, and what they record.

Revision 6 claimed "Every committed capture contains a disbursement row, so this
IS graded".  T34 found that false against pass 3.  T35 then landed pass 3b on
main, which DOES emit `balance` on disbursement rows.  This script reads the
committed artefacts and states the coverage PER HARNESS rather than
unqualified, which is what revision 7 must say.

It also records T35's `totalOutstandingAmount` finding as observed in the file.

NOTHING HERE IS A NEW OBSERVATION -- every value is read out of a capture file
already committed on main.
"""
import json
import os
from decimal import Decimal

FILES = [
    (".softhouse/capture/out/capture-prod-raw.json", "Path A pass 3  (Capture3.java)"),
    (".softhouse/capture/out/capture-prod3b-raw.json", "Path A pass 3b (Capture3b.java)"),
    (".softhouse/capture/dec1-binding/out/t37-binding.json", "Path A T37 binding (T37 harness)"),
]

PATHB = [
    ".softhouse/capture/pathb/out/B-01-baseline-raw.json",
    ".softhouse/capture/pathb/out/B-02-multiplesof100-raw.json",
    ".softhouse/capture/pathb/out/B-03-diycs-fullleapyear-raw.json",
    ".softhouse/capture/pathb/out/B-04-diycs-feb29only-raw.json",
]


def main():
    print("=" * 78)
    print("B  Which committed harness records the DISBURSEMENT row's outstanding")
    print("   balance?  (P1-T34-2)")
    print("=" * 78)
    for path, label in FILES:
        if not os.path.exists(path):
            print(f"{label:<36} FILE ABSENT: {path}")
            continue
        data = json.load(open(path), parse_float=Decimal, parse_int=int)
        caps = data["captures"]
        with_bal, without_bal, mismatch = 0, 0, []
        keysets = set()
        for cap in caps:
            for p in cap["observed"]["periods"]:
                if p["type"] != "DISBURSEMENT":
                    continue
                keysets.add(tuple(sorted(p.keys())))
                if "balance" in p:
                    with_bal += 1
                    if p["balance"] != p["principal"]:
                        mismatch.append((cap["id"], p["principal"], p["balance"]))
                else:
                    without_bal += 1
        print(f"\n{label}")
        print(f"    captures                        : {len(caps)}")
        print(f"    DISBURSEMENT rows WITH balance  : {with_bal}")
        print(f"    DISBURSEMENT rows WITHOUT it    : {without_bal}")
        for ks in sorted(keysets):
            print(f"    emitted keys                    : {list(ks)}")
        if with_bal:
            print(f"    balance == principal on all?    : "
                  f"{'YES' if not mismatch else 'NO ' + str(mismatch)}")

    print("\n" + "=" * 78)
    print("   Path B server-path captures (DEC-1 5 calls these 'not yet admissible';")
    print("   T36 closed the four T22 admissibility P0s against the live oracle).")
    print("=" * 78)
    for path in PATHB:
        if not os.path.exists(path):
            print(f"  ABSENT {path}")
            continue
        data = json.load(open(path), parse_float=Decimal, parse_int=int)
        periods = data.get("periods", [])
        disb = [p for p in periods if p.get("period") is None or p.get("principalDisbursed")]
        for p in periods[:1]:
            print(f"  {os.path.basename(path):<32} first period keys: "
                  f"{sorted(k for k in p.keys())[:8]} ...")
            print(f"  {'':<32} principalDisbursed="
                  f"{p.get('principalDisbursed')} "
                  f"principalLoanBalanceOutstanding="
                  f"{p.get('principalLoanBalanceOutstanding')}")

    print("\n" + "=" * 78)
    print("C  T35's totalOutstandingAmount finding, read out of the committed file")
    print("=" * 78)
    p3b = ".softhouse/capture/out/capture-prod3b-raw.json"
    if os.path.exists(p3b):
        data = json.load(open(p3b), parse_float=Decimal, parse_int=int)
        vals = {}
        for cap in data["captures"]:
            v = cap["observed"].get("totalOutstandingAmount")
            vals.setdefault(repr(v), []).append(cap["id"])
        for v, ids in vals.items():
            print(f"    totalOutstandingAmount = {v}  on {len(ids)} captures: "
                  f"{', '.join(ids)}")
        # scale discipline of every other money string
        scales = {}
        for cap in data["captures"]:
            for k in ("totalDisbursedAmount", "totalPrincipalAmount",
                      "totalInterestAmount", "totalFeeAmount",
                      "totalPenaltyAmount", "totalRepaymentAmount"):
                s = cap["observed"].get(k)
                if s is not None:
                    ss = str(s)
                    scales.setdefault(k, set()).add(
                        len(ss.split(".")[1]) if "." in ss else 0)
        for k, v in scales.items():
            print(f"    {k:<24} decimal places observed: {sorted(v)}")
        fees = set()
        for cap in data["captures"]:
            for p in cap["observed"]["periods"]:
                for kk in ("fee", "feeAmount", "penalty", "penaltyAmount"):
                    if kk in p:
                        fees.add(p[kk])
        print(f"    every per-row fee/penalty value observed: {sorted(fees)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
