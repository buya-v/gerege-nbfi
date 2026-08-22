#!/usr/bin/env python3
"""T262 independent re-derivation. INTEGER MINOR UNITS ONLY.

Every json.load carries parse_float=Decimal (T145); this file REPRODUCES nothing, so
T207's "sometimes parse_float is the wrong repair" ruling does not apply — the guard is added.
Reads the RAW gz capture, not only the derived classify JSON, so the algebra is checked against
the oracle's own emitted schedule rows rather than against T259's arithmetic.
"""
import gzip
import hashlib
import json
import sys
from decimal import Decimal

BASE = ".softhouse/capture/t229-g8-site3"
KEY = "P2_totalInterestEqualsNEplusB"


def m(s):
    d = Decimal(str(s)) * 100
    assert d == d.to_integral_value(), s
    return int(d)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


cls_p = BASE + "/out/classify-t229.json"
raw_p = BASE + "/out/capture-t229-raw.json.gz"
print("classify sha256", sha(cls_p))
print("raw      sha256", sha(raw_p))

cls = json.load(open(cls_p), parse_float=Decimal)
raw = json.load(gzip.open(raw_p, "rt"), parse_float=Decimal)
pred = {p["id"]: p for p in json.load(open(BASE + "/prediction.json"), parse_float=Decimal)}

rows = cls["cells"]
carriers = [r for r in rows if KEY in r]
lack = [r for r in rows if KEY not in r]
print()
print("PART 1 — the counts (P-67, both terms)")
print("  rows in file            :", len(rows))
print("  carriers of the key     :", len(carriers))
print("  lacking the key         :", len(lack))
print("  lacking, by predictedOutcome:", sorted({r["predictedOutcome"] for r in lack}))
print("  lacking ids             :", [r["id"] for r in lack])
f = [r for r in carriers if r[KEY] is False]
t = [r for r in carriers if r[KEY] is True]
print("  carriers false / true   :", len(f), "/", len(t), " (sums to", len(f) + len(t), ")")
print("  false & AFFIRMATIVE     :", [r["id"] for r in f if r["verdict"] == "AS PREDICTED"])
print("  false & NEGATIVE        :", [r["id"] for r in f if r["verdict"] != "AS PREDICTED"])

print()
print("PART 2 — is n*E+B the total REPAYMENT? checked against the raw emitted rows")
hdr = "  {:26} {:>9} {:>8} {:>8} {:>9} {:>10} {:>8} {:>9}".format(
    "id", "sumTotal", "sumPrin", "sumInt", "n*E+B", "tot==nE+B", "lastTot", "I==T-P")
print(hdr)
raw_by = {c["id"]: c for c in raw["captures"]}
for r in carriers:
    c = raw_by[r["id"]]
    reps = [x for x in c["observed"]["periods"] if x["type"] == "REPAYMENT"]
    st = sum(m(x["total"]) for x in reps)
    sp = sum(m(x["principal"]) for x in reps)
    si = sum(m(x["interest"]) for x in reps)
    hp = m(c["observed"]["totalPrincipalAmount"])
    hi = m(c["observed"]["totalInterestAmount"])
    assert (sp, si) == (hp, hi), ("header != row sum", r["id"], sp, hp, si, hi)
    assert st == sp + si, ("total != prin+int", r["id"])
    assert sp == r["observedPrincipalMinor"] and si == r["observedInterestMinor"]
    n = len(reps)
    assert n == r["n"] == r["observedRepaymentRows"]
    E = m(reps[0]["total"])
    assert E == r["observedRow1TotalMinor"]
    B = r["bMinor"]
    nEB = n * E + B
    print("  {:26} {:9d} {:8d} {:8d} {:9d} {:>10} {:8d} {:>9}".format(
        r["id"], st, sp, si, nEB, str(st == nEB), m(reps[-1]["total"]), str(si == st - sp)))

print()
print("PART 3 — agreement: registered vs corrected predicate, per row, integer only")
hdr = "  {:26} {:>5} {:>6} {:>6} {:>6} {:>8} {:>8} {:>8} {:>6} {:>6} {:>6} {:>7} {:>8}".format(
    "id", "n", "E_obs", "B", "P_rep", "nE+B", "nE+B-P", "int_obs", "REG", "CORR", "verd",
    "agrREG", "agrCORR")
print(hdr)
aR = aC = 0
aC_true = aC_false = 0
for r in carriers:
    n, E, B = r["n"], r["observedRow1TotalMinor"], r["bMinor"]
    P, I = r["observedPrincipalMinor"], r["observedInterestMinor"]
    for v in (n, E, B, P, I):
        assert type(v) is int, (r["id"], v, type(v))
    tot = n * E + B
    reg = (I == tot)
    corr = (I == tot - P)
    assert reg == r[KEY], ("recompute != recorded", r["id"], reg, r[KEY])
    vaff = (r["verdict"] == "AS PREDICTED")
    agrR, agrC = (reg == vaff), (corr == vaff)
    aR += agrR
    aC += agrC
    if agrC and vaff:
        aC_true += 1
    if agrC and not vaff:
        aC_false += 1
    print("  {:26} {:5d} {:6d} {:6d} {:6d} {:8d} {:8d} {:8d} {:>6} {:>6} {:>6} {:>7} {:>8}".format(
        r["id"], n, E, B, P, tot, tot - P, I, str(reg), str(corr), str(vaff), str(agrR), str(agrC)))
print()
print("  AGREEMENT under REGISTERED predicate : {} of {}".format(aR, len(carriers)))
print("  AGREEMENT under CORRECTED  predicate : {} of {}".format(aC, len(carriers)))
print("  corrected agreements, TRUE  direction:", aC_true)
print("  corrected agreements, FALSE direction:", aC_false)

print()
print("PART 4 — robustness: same test with E = predictedEmiMinor instead of observed row-1 total")
aC2 = 0
for r in carriers:
    n, B, P, I = r["n"], r["bMinor"], r["observedPrincipalMinor"], r["observedInterestMinor"]
    Ep = pred[r["id"]]["emiMinorPredicted"]
    assert type(Ep) is int
    corr = (I == n * Ep + B - P)
    aC2 += (corr == (r["verdict"] == "AS PREDICTED"))
print("  AGREEMENT under CORRECTED predicate, predicted E :", aC2, "of", len(carriers))

print()
print("PART 5 — the losing side: what ANDing P2 into verdict would print")
false_reported = 0
for r in carriers:
    if r["verdict"] == "AS PREDICTED" and r[KEY] is False:
        fam_hit = r["observedOutcome"] == r["predictedOutcome"]
        prin_hit = r["observedPrincipalMinor"] == r["predictedPrincipalMinor"]
        corr = (r["observedInterestMinor"] ==
                r["n"] * r["observedRow1TotalMinor"] + r["bMinor"] - r["observedPrincipalMinor"])
        print("  {:26} familyHit={} principalHit={} (obs={} pred={}) correctedPredicate={}".format(
            r["id"], fam_hit, prin_hit, r["observedPrincipalMinor"],
            r["predictedPrincipalMinor"], corr))
        if fam_hit and prin_hit:
            false_reported += 1
print("  cells that would flip to REFUTED despite hitting family AND principal exactly:",
      false_reported)
sys.exit(0)
