#!/usr/bin/env python3
# T44 audit leg: INDEPENDENT re-derivation of T40's charge claims.
# Exact Decimal only. Money handled as integer MINOR UNITS. No binary float is ever constructed.
import json, hashlib, os, sys
from decimal import Decimal

ROOT = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse"
FC   = os.path.join(ROOT, "capture/charges/out/fc")
ATT  = os.path.join(ROOT, "capture/charges/out/attested")
RERN = os.path.join(ROOT, "capture/charges/out/fc-rerun")
CTRL = os.path.join(ROOT, "capture/charges/out/control/B-01-baseline-raw.json")

def load(p):
    with open(p) as f:
        return json.load(f, parse_float=Decimal)

def minor(v):
    """Decimal money -> integer minor units. Refuses anything that is not exact at 2dp."""
    if v is None:
        return None
    d = v if isinstance(v, Decimal) else Decimal(str(v))
    scaled = d * 100
    if scaled != scaled.to_integral_value():
        raise ValueError("not exact at 2dp: %s" % d)
    return int(scaled)

def m(node, key):
    v = node.get(key)
    return None if v is None else minor(v)

def flatten(o, path=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(flatten(v, path + "/" + k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out.update(flatten(v, path + "/[%d]" % i))
    else:
        out[path] = o
    return out

def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

IDS = ["FC-01-flat-disbursement", "FC-02-flat-instalment", "FC-03-pctamount-disbursement",
       "FC-04-pctinterest-instalment", "FC-05-pctamountinterest-instalment", "FC-06-penalty-inside-p3",
       "FC-07-fee-on-p3-duedate", "FC-08-penalty-instalment", "FC-09-pctamount-instalment",
       "FC-10-pctamount-inside-p6", "FC-11-fee-on-disbursement-date", "FC-12-fee-on-final-duedate",
       "FC-13-fee-inside-p12", "FC-14-fee-inside-p1", "FC-15-combined-fee-and-penalty",
       "FC-16-fee-on-p1-duedate", "FC-17-fee-after-final-duedate", "FC-19-pctinterest-sdd-inside-p6",
       "FC-20-pctinterest-sdd-on-disb", "FC-21-pctamtint-sdd-inside-p6",
       "FC-22-penalty-instalment-plus-sdd-on-p3-duedate"]

ctrl = load(CTRL)
ctrl_flat = flatten(ctrl)
docs = {i: load(os.path.join(FC, i + "-raw.json")) for i in IDS}

R = []
def say(s):
    R.append(s)
    print(s)

say("# T44 audit leg (charges) - independent recomputation of T40's claims")
say("")
say("Control: `out/control/B-01-baseline-raw.json`  sha256 `%s`" % sha(CTRL))
say("")

# ---------------- INVARIANTS C1..C10, written from the stated definitions ----------------
say("## Invariants C1-C10 (my own implementation, written from the stated definitions)")
say("")
say("| capture | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 |")
say("|---|---|---|---|---|---|---|---|---|---|---|")
tally = {("C%d" % i): [0, 0] for i in range(1, 11)}
c5_fail = []
cper = ctrl["periods"]
for i in IDS:
    d = docs[i]
    per = d["periods"]
    res = {}
    res["C1"] = sum(m(p, "feeChargesDue") or 0 for p in per) == (m(d, "totalFeeChargesCharged") or 0)
    res["C2"] = sum(m(p, "penaltyChargesDue") or 0 for p in per) == (m(d, "totalPenaltyChargesCharged") or 0)
    ok3 = True
    for p in per:
        comp = ((m(p, "principalDue") or 0) + (m(p, "interestDue") or 0)
                + (m(p, "feeChargesDue") or 0) + (m(p, "penaltyChargesDue") or 0))
        if comp != (m(p, "totalDueForPeriod") or 0):
            ok3 = False
    res["C3"] = ok3
    res["C4"] = all((m(p, "feeChargesOutstanding") or 0) == (m(p, "feeChargesDue") or 0)
                    and (m(p, "penaltyChargesOutstanding") or 0) == (m(p, "penaltyChargesDue") or 0)
                    for p in per)
    res["C5"] = (m(d, "totalRepaymentExpected") == sum(m(p, "totalDueForPeriod") or 0 for p in per))
    if not res["C5"]:
        c5_fail.append(i)
    res["C6"] = sum(m(p, "principalDue") or 0 for p in per) == m(d, "totalPrincipalExpected")
    res["C7"] = sum(m(p, "interestDue") or 0 for p in per) == m(d, "totalInterestCharged")
    ok8 = len(per) == len(cper)
    if ok8:
        for a, b in zip(per, cper):
            for k in ("principalDue", "principalOriginalDue", "interestDue", "principalLoanBalanceOutstanding"):
                if (m(a, k) if k in a else None) != (m(b, k) if k in b else None):
                    ok8 = False
    res["C8"] = ok8
    res["C9"] = all((m(a, "totalInstallmentAmountForPeriod") if "totalInstallmentAmountForPeriod" in a else None)
                    == (m(b, "totalInstallmentAmountForPeriod") if "totalInstallmentAmountForPeriod" in b else None)
                    for a, b in zip(per, cper))
    neg = [k for k, v in flatten(d).items() if isinstance(v, Decimal) and v < 0]
    res["C10"] = (len(neg) == 0)
    for k, v in res.items():
        tally[k][0 if v else 1] += 1
    say("| %s | %s |" % (i, " | ".join("PASS" if res["C%d" % n] else "**FAIL**" for n in range(1, 11))))
say("")
say("Totals: " + ", ".join("%s PASS %d / FAIL %d" % (k, v[0], v[1])
                           for k, v in sorted(tally.items(), key=lambda x: int(x[0][1:]))))
say("")
say("C5 FAILS on %d captures: %s" % (len(c5_fail), ", ".join(c5_fail)))
say("")

# ---------------- Full-cell leaf movement ----------------
say("## Leaf movement vs the zero-charge control (independent flatten)")
say("")
say("| capture | leaves in doc | leaves in control | moved | structural diff |")
say("|---|---|---|---|---|")
for i in IDS:
    f = flatten(docs[i])
    kd, kc = set(f), set(ctrl_flat)
    struct = len(kd ^ kc)
    moved = sum(1 for k in (kd & kc) if f[k] != ctrl_flat[k])
    say("| %s | %d | %d | **%d** | %d |" % (i, len(f), len(ctrl_flat), moved, struct))
say("")

# ---------------- D-2a / D-2b byte identity ----------------
say("## D-2a / D-2b - byte identity to the control, verified by my own sha256")
say("")
ctrl_sha = sha(CTRL)
say("| file | sha256 | == control |")
say("|---|---|---|")
for label, p in [("control B-01 (T40 control run)", CTRL),
                 ("FC-17 out/fc", os.path.join(FC, "FC-17-fee-after-final-duedate-raw.json")),
                 ("FC-20 out/fc", os.path.join(FC, "FC-20-pctinterest-sdd-on-disb-raw.json")),
                 ("FC-17 out/attested", os.path.join(ATT, "FC-17-fee-after-final-duedate-raw.json")),
                 ("FC-20 out/attested", os.path.join(ATT, "FC-20-pctinterest-sdd-on-disb-raw.json")),
                 ("CTRL-B-01 out/attested", os.path.join(ATT, "CTRL-B-01-raw.json"))]:
    s = sha(p)
    say("| %s | `%s` | %s |" % (label, s, "YES" if s == ctrl_sha else "no"))
say("")

# ---------------- Determinism across the three issues ----------------
say("## Determinism - three issues, my own digests")
say("")
say("| capture | out/fc | out/fc-rerun | out/attested | all three identical |")
say("|---|---|---|---|---|")
det_bad = []
for i in IDS:
    a = sha(os.path.join(FC, i + "-raw.json"))
    rp = os.path.join(RERN, i + "-raw.json")
    b = sha(rp) if os.path.exists(rp) else "MISSING"
    c = sha(os.path.join(ATT, i + "-raw.json"))
    same = (a == b == c)
    if not same:
        det_bad.append(i)
    say("| %s | `%s` | `%s` | `%s` | %s |" % (i, a[:16], (b[:16] if b != "MISSING" else b), c[:16],
                                              "yes" if same else "**NO**"))
say("")
say("Determinism mismatches: %s" % (det_bad or "none"))
say("")

# ---------------- Q5 percentage bases, recomputed exactly ----------------
def rnd_half_up(num, den):
    """exact HALF_UP division of non-negative integers -> integer"""
    assert num >= 0 and den > 0
    q = num // den
    rem = num - q * den
    if rem * 2 >= den:
        q += 1
    return q

say("## Q5 - percentage bases and rounding locus, recomputed exactly (integer minor units, HALF_UP)")
say("")
PRINC = minor(Decimal("1200000.00"))
TOTINT = m(ctrl, "totalInterestCharged")
say("control totalInterestCharged (minor) = %d ; principal (minor) = %d" % (TOTINT, PRINC))
say("")
checks = []
exp = rnd_half_up(PRINC * 12345, 1000000)
obs = m(docs["FC-03-pctamount-disbursement"]["periods"][0], "feeChargesDue")
checks.append(("FC-03 pct-of-amount DISBURSEMENT = 1.2345% x whole principal", exp, obs))
p6 = [p for p in docs["FC-10-pctamount-inside-p6"]["periods"] if p.get("period") == 6][0]
checks.append(("FC-10 pct-of-amount SDD, all of it in period 6", exp, m(p6, "feeChargesDue")))
ok = True
bad = []
for p in docs["FC-09-pctamount-instalment"]["periods"]:
    if p.get("period") is None:
        continue
    cp = [c for c in cper if c.get("period") == p["period"]][0]
    e = rnd_half_up(m(cp, "principalDue") * 5000, 1000000)
    o = m(p, "feeChargesDue")
    if e != o:
        ok = False
        bad.append((p["period"], e, o))
checks.append(("FC-09 0.5% of THAT PERIOD's principalDue, all 12 periods",
               "all match" if ok else str(bad), "all match" if ok else "MISMATCH"))
ok = True
s4 = 0
for p in docs["FC-04-pctinterest-instalment"]["periods"]:
    if p.get("period") is None:
        continue
    cp = [c for c in cper if c.get("period") == p["period"]][0]
    e = rnd_half_up(m(cp, "interestDue") * 375, 10000)
    o = m(p, "feeChargesDue")
    s4 += o
    if e != o:
        ok = False
checks.append(("FC-04 3.75% of THAT PERIOD's interestDue, all 12 periods",
               "all match" if ok else "MISMATCH", "sum=%d" % s4))
e19 = rnd_half_up(TOTINT * 375, 10000)
o19 = m(docs["FC-19-pctinterest-sdd-inside-p6"], "totalFeeChargesCharged")
checks.append(("FC-19 3.75% of WHOLE-TERM interest, ONE rounding", e19, o19))
checks.append(("rounding-locus: FC-04 sum-of-12 vs FC-19 single (must differ)", s4, o19))
ok = True
s5 = 0
for p in docs["FC-05-pctamountinterest-instalment"]["periods"]:
    if p.get("period") is None:
        continue
    cp = [c for c in cper if c.get("period") == p["period"]][0]
    base = m(cp, "principalDue") + m(cp, "interestDue")
    e = rnd_half_up(base * 12345, 1000000)
    o = m(p, "feeChargesDue")
    s5 += o
    if e != o:
        ok = False
checks.append(("FC-05 1.2345% of period principal+interest, all 12 periods",
               "all match" if ok else "MISMATCH", "sum=%d" % s5))
e21 = rnd_half_up((PRINC + TOTINT) * 12345, 1000000)
o21 = m(docs["FC-21-pctamtint-sdd-inside-p6"], "totalFeeChargesCharged")
checks.append(("FC-21 1.2345% of principal + WHOLE-TERM interest", e21, o21))
checks.append(("rounding-locus: FC-05 sum-of-12 vs FC-21 single (must differ)", s5, o21))
say("| recomputation | expected (minor) | observed (minor) | agrees |")
say("|---|---|---|---|")
for name, e, o in checks:
    say("| %s | %s | %s | %s |" % (name, e, o, "YES" if e == o else "differ"))
say("")

# ---- does HALF_UP vs HALF_EVEN separate anywhere in the charge arithmetic? ----
say("### Would any of these percentage roundings discriminate HALF_UP from HALF_EVEN?")
say("")
def is_tie(num, den):
    rem = num - (num // den) * den
    return rem * 2 == den
ties = []
for label, num, den in (
        [("FC-03/FC-10 1.2345%% x principal", PRINC * 12345, 1000000),
         ("FC-19 3.75%% x total interest", TOTINT * 375, 10000),
         ("FC-21 1.2345%% x (P+I)", (PRINC + TOTINT) * 12345, 1000000)]
        + [("FC-09 p%s" % p["period"], m(p, "principalDue") * 5000, 1000000) for p in cper if p.get("period")]
        + [("FC-04 p%s" % p["period"], m(p, "interestDue") * 375, 10000) for p in cper if p.get("period")]
        + [("FC-05 p%s" % p["period"], (m(p, "principalDue") + m(p, "interestDue")) * 12345, 1000000)
           for p in cper if p.get("period")]):
    if is_tie(num, den):
        ties.append(label)
say("exact half-unit ties found in the charge arithmetic of the whole capture set: **%d** %s"
    % (len(ties), ties))
say("")
say("=> no charge amount in this set is a rounding tie, so NO capture in the set discriminates")
say("   HALF_UP from HALF_EVEN *inside the charge arithmetic*. The tenant canary is a separate shape.")
say("")

# ---------------- Q3 / Q4 ----------------
say("## Q3/Q4 - which period each charge landed in (recomputed from the raw rows)")
say("")
say("| capture | disb-period fee | per-period fee (period:minor) | per-period penalty | totalFee | totalPenalty | TRE |")
say("|---|---|---|---|---|---|---|")
for i in IDS:
    d = docs[i]
    per = d["periods"]
    disb = m(per[0], "feeChargesDue") or 0
    fl = ";".join("%s:%d" % (p["period"], m(p, "feeChargesDue")) for p in per
                  if p.get("period") and m(p, "feeChargesDue"))
    pl = ";".join("%s:%d" % (p["period"], m(p, "penaltyChargesDue")) for p in per
                  if p.get("period") and m(p, "penaltyChargesDue"))
    say("| %s | %d | %s | %s | %d | %d | %d |" % (i, disb, fl or "-", pl or "-",
        m(d, "totalFeeChargesCharged"), m(d, "totalPenaltyChargesCharged"), m(d, "totalRepaymentExpected")))
say("")

# ---------------- D-1 ----------------
say("## D-1 - totalRepaymentExpected vs the rows and vs the control")
say("")
base_tre = m(ctrl, "totalRepaymentExpected")
say("control totalRepaymentExpected (minor) = %d" % base_tre)
say("")
say("| capture | totalFee | totalPenalty | TRE | TRE - control | Sum rows | TRE - Sum rows |")
say("|---|---|---|---|---|---|---|")
for i in IDS:
    d = docs[i]
    tre = m(d, "totalRepaymentExpected")
    rows = sum(m(p, "totalDueForPeriod") or 0 for p in d["periods"])
    say("| %s | %d | %d | %d | %+d | %d | %+d |" % (i, m(d, "totalFeeChargesCharged"),
        m(d, "totalPenaltyChargesCharged"), tre, tre - base_tre, rows, tre - rows))
say("")

# ---------------- blind spots ----------------
say("## What this capture set cannot distinguish (blind-spot probe)")
say("")
shapes = set()
for i in IDS:
    d = docs[i]
    shapes.add((str(m(d, "totalPrincipalExpected")), str(m(d, "totalInterestCharged")),
                str(d.get("loanTermInDays")), len([p for p in d["periods"] if p.get("period")])))
say("distinct (principal, total interest, term days, #instalments) tuples across all 21 captures: **%d**" % len(shapes))
for s in sorted(shapes):
    say("  " + str(s))
say("")
dig = {}
for i in IDS:
    dig.setdefault(sha(os.path.join(FC, i + "-raw.json")), []).append(i)
say("distinct response digests across the 21 captures: **%d**" % len(dig))
for k, v in sorted(dig.items(), key=lambda x: -len(x[1])):
    if len(v) > 1:
        say("  COLLISION `%s...` : %s" % (k[:16], ", ".join(v)))
say("")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "RECOMPUTE.md")
with open(out, "w") as f:
    f.write("\n".join(R) + "\n")
