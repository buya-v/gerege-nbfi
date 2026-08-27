import json

W = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-af5b53dea6ccaf635/.softhouse/capture/out"
p1 = {c["id"]: c for c in json.load(open(W + "/capture-raw.json"))["captures"]}
p2 = {c["id"]: c for c in json.load(open(W + "/capture-tenant-raw.json"))["captures"]}
p3 = {c["id"]: c for c in json.load(open(W + "/capture-prod-raw.json"))["captures"]}

pairs = [("P-CAL", p3, "C-00", p1), ("P-01", p3, "D-01-p19", p1), ("P-00", p3, "P-CAL", p3),
         ("P-04f", p3, "P-04t", p3), ("P-00", p3, "P-04f", p3), ("P-01", p3, "D-01", p1),
         ("P-MNT-5M", p3, "T-MNT5M", p2)]
for a, sa, b, sb in pairs:
    if a not in sa or b not in sb:
        print(f"{a} vs {b}: MISSING")
        continue
    oa, ob = sa[a]["observed"], sb[b]["observed"]
    print(f"{a} vs {b}: observed-block {'IDENTICAL' if oa == ob else 'DIFFERENT'}")
    if oa != ob:
        for k in ("loanTermInDays", "totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"):
            if oa[k] != ob[k]:
                print(f"    {k}: {oa[k]}  vs  {ob[k]}")
        for i, (x, y) in enumerate(zip(oa["periods"], ob["periods"])):
            if x != y:
                print(f"    period idx {i}:\n      A {x}\n      B {y}")

print()
print("pass1 ids:", sorted(p1))
print("pass2 ids:", sorted(p2))
print("pass3 ids:", sorted(p3))
for a, sa, b, sb in (("P-CAL", p3, "C-00", p1), ("P-01", p3, "D-01-p19", p1)):
    print(f"\ninput-block deltas {a} vs {b}:")
    ia, ib = sa[a]["inputs"], sb[b]["inputs"]
    for k in sorted(set(ia) | set(ib)):
        if ia.get(k, "<absent>") != ib.get(k, "<absent>"):
            print("   ", k, "=", ia.get(k, "<absent>"), "|", ib.get(k, "<absent>"))
