#!/usr/bin/env python3
"""A2-34: the reviewer's OWN non-vacuity census of the promoted ledger set.
Both terms of every ratio are counted here in the live artefact (P-67)."""
import glob, json, os

R = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac008956278f2d6ea"
VD = os.path.join(R, ".softhouse/vectors/ledger")

files = sorted(glob.glob(os.path.join(VD, "*.json")))
print(f"POPULATION: {len(files)} .json files under {VD}")
tot_legs = 0
tot_money = 0
tot_money_nonzero = 0
legdist = {}
print()
print(f"{'case_id':48s} {'class':15s} {'legs':>5} {'DR':>3} {'CR':>3} {'money cells':>12} {'non-zero minor':>15}")
for f in files:
    d = json.load(open(f))
    legs = d["expect"].get("legs", [])
    dr = sum(1 for l in legs if l["entry_side"] == "DEBIT")
    cr = sum(1 for l in legs if l["entry_side"] == "CREDIT")
    # money cells = per-leg amount_minor + the two totals when present
    mc = [l["amount_minor"] for l in legs]
    for k in ("total_debits_minor", "total_credits_minor"):
        v = d["expect"].get(k, "")
        if v:
            mc.append(v)
    nz = sum(1 for m in mc if int(m) % 100 != 0)
    tot_legs += len(legs)
    tot_money += len(mc)
    tot_money_nonzero += nz
    if legs:
        legdist[len(legs)] = legdist.get(len(legs), 0) + 1
    print(f"{d['case_id']:48s} {d['class']:15s} {len(legs):5d} {dr:3d} {cr:3d} {len(mc):12d} {nz:15d}")

print()
print(f"TOTAL legs across the promoted set                   : {tot_legs}")
print(f"TOTAL promoted MONEY cells (legs + present totals)    : {tot_money}")
print(f"  of which carry NON-ZERO minor units (minor%100 != 0): {tot_money_nonzero}")
print(f"  of which are a WHOLE TUGRIK (minor%100 == 0)        : {tot_money - tot_money_nonzero}")
print(f"LEG-COUNT DISTRIBUTION of the promoted entry-asserting vectors: "
      + ", ".join(f"{n}-leg x{c}" for n, c in sorted(legdist.items())))

print()
print("VACUITY TEST A2-26 FIXED: before A2-26 every entry was 2-leg and every amount a whole tugrik.")
print(f"  promoted vectors with MORE THAN 2 legs : {sum(c for n,c in legdist.items() if n>2)} of {sum(legdist.values())} entry-asserting vectors")
print(f"  promoted money cells with minor units  : {tot_money_nonzero} of {tot_money}")

print()
print("PRODUCT IDs cited by the promoted set (PIN-ledger inadmissible = [22,23,24,27,28]):")
pin = json.load(open(os.path.join(R, ".softhouse/vectors/PIN-ledger.json")))
inad = set(pin["inadmissible_product_ids"])
for f in files:
    d = json.load(open(f))
    pid = d["request"]["product_id"]
    verdict = "INADMISSIBLE PRODUCT" if pid in inad else ("manual entry, no product" if pid == 0 else "admissible")
    print(f"  {d['case_id']:48s} product_id={pid:3d}  {verdict}")

print()
print("dec2_revision declared per vector (PIN-ledger says %d):" % pin["dec2_revision"])
for f in files:
    d = json.load(open(f))
    print(f"  {d['case_id']:48s} dec2_revision={d.get('dec2_revision')}  dec1_revision={d.get('dec1_revision','<absent>')}")

print()
print("excluded_fields per leg (must be exactly ['gl_account_type']):")
for f in files:
    d = json.load(open(f))
    ex = [l.get("excluded_fields") for l in d["expect"].get("legs", [])]
    print(f"  {d['case_id']:48s} {ex}")

print()
print("NOTE-CONTENT CHECK — does each vector's OWN _note carry the required sentences?")
needles = {
    "glAccountType instability": "glAccountType",
    "A2-088/A2-320 observation": "A2-088",
    "G-12 named":               "G-12",
    "running balance named":    "running_balance",
    "no balance graded":        "NO BALANCE IS GRADED",
    "fetchRunningBalance 500":  "fetchRunningBalance=true is HTTP 500",
}
for f in files:
    d = json.load(open(f))
    note = d.get("_note", "")
    row = []
    for label, n in needles.items():
        row.append(f"{label}={'Y' if n in note else 'N'}")
    print(f"  {d['case_id']:48s} " + "  ".join(row))
