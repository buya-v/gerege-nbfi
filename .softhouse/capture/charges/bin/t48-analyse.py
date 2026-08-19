#!/usr/bin/env python3
"""
T48 -- analysis of the charge-gap pass.  Contacts no oracle; reads only committed bytes.

Two jobs:

1. EXACT-TEXT SIDECARS.  Following T44-X1 and T46's decision: Path B responses are
   float-shaped on the wire (Fineract serialises BigDecimal as a JSON *number*), so every
   T48 capture gets a `-exact.json` sidecar in which every JSON number is re-emitted as a
   JSON STRING carrying the literal characters that were on the wire.  No float is
   constructed anywhere: json.loads is given parse_float=str / parse_int=str, so the raw
   matched literal is what is stored.  The raw bytes are NEVER rewritten -- they are what
   the oracle said.

2. FULL-CELL COMPARISON.  Every period row, every column, plus the plan totals -- never the
   three headline scalars.  Discrimination is reported on DISAGREEING cells only, and a
   comparison that agrees everywhere is reported as proving nothing.
"""
import json
import os
import pathlib
import sys
from decimal import Decimal

O = pathlib.Path(__file__).resolve().parents[1] / "out" / "t48"
NUM = (int, float)
failures = []


# ------------------------------------------------------------------ exact-text sidecars
def to_text(node):
    if isinstance(node, dict):
        return dict((k, to_text(v)) for k, v in node.items())
    if isinstance(node, list):
        return [to_text(v) for v in node]
    return node  # already a str, bool or None -- numbers arrive as str via parse_*


def bare_numbers(node, path="", acc=None):
    if acc is None:
        acc = []
    if isinstance(node, dict):
        for k, v in node.items():
            bare_numbers(v, path + "." + k, acc)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            bare_numbers(v, "%s[%d]" % (path, i), acc)
    elif isinstance(node, NUM) and not isinstance(node, bool):
        acc.append((path, node))
    return acc


print("== exact-text sidecars ==")
made = 0
for f in sorted(O.glob("T48-CH-*-raw.json")):
    text = f.read_text()
    exact = json.loads(text, parse_float=str, parse_int=str)
    side = f.with_name(f.name.replace("-raw.json", "-exact.json"))
    side.write_text(json.dumps(to_text(exact), indent=1, ensure_ascii=False) + "\n")
    # identity: the sidecar must carry ZERO bare JSON numbers ...
    left = bare_numbers(json.loads(side.read_text()))
    if left:
        failures.append("%s: sidecar still carries %d bare JSON numbers" % (side.name, len(left)))
    # ... and must agree leaf for leaf, as text, with the raw bytes
    raw_leaves = bare_numbers(json.loads(text))
    ex = json.loads(side.read_text())

    def leaf(path, node):
        cur = node
        for part in path.strip(".").replace("]", "").split("."):
            if "[" in part:
                name, idx = part.split("[")
                if name:
                    cur = cur[name]
                cur = cur[int(idx)]
            elif part:
                cur = cur[part]
        return cur

    for path, val in raw_leaves:
        got = leaf(path, ex)
        if Decimal(got) != Decimal(str(val)):
            failures.append("%s: leaf %s is %r in the sidecar, %r on the wire" % (f.name, path, got, val))
    made += 1
print("  %d sidecars written; %d raw numeric leaves checked in the last file" % (made, len(raw_leaves)))


# --------------------------------------------------------------------- full-cell compare
def load_exact(stem):
    return json.loads((O / (stem + "-exact.json")).read_text())


def cells(doc):
    out = {}
    if "periods" not in doc:
        return {"__http_error__": doc.get("httpStatusCode"),
                "__msg__": "; ".join(e.get("developerMessage", "") for e in doc.get("errors", []))}
    for k, v in doc.items():
        if k in ("periods", "currency"):
            continue
        out[k] = v
    for i, p in enumerate(doc["periods"]):
        for k, v in p.items():
            out["row%d.%s" % (i, k)] = v
    return out


def compare(label, a, b, expect):
    A, B = cells(load_exact(a)), cells(load_exact(b))
    keys = sorted(set(A) | set(B))
    diffs = [(k, A.get(k), B.get(k)) for k in keys if A.get(k) != B.get(k)]
    print("\n== %s\n   %d of %d cells differ  (expected %s)" % (label, len(diffs), len(keys), expect))
    for k, x, y in diffs[:16]:
        print("     %-34s %-16s | %s" % (k, x, y))
    if len(diffs) > 16:
        print("     ... %d more" % (len(diffs) - 16))
    if expect == "identical" and diffs:
        failures.append("%s: expected IDENTICAL, %d cells differ" % (label, len(diffs)))
    if expect == "separate" and not diffs:
        failures.append("%s: every cell agrees -- THIS CAPTURE DISCRIMINATES NOTHING" % label)
    if expect == "observe" and not diffs:
        print("     -> EVERY CELL AGREES. This comparison DISCRIMINATES NOTHING: a port that "
              "conflated the two would pass it.")
    return diffs


print("\n\n######## GAP 1 + GAP 3 -- m_charge.amount vs the request's amount ########")
for stem, tt in (("T48-CH-01-defamount-omitted-tt2", "SPECIFIED_DUE_DATE (2)"),
                 ("T48-CH-03-defamount-omitted-tt8", "INSTALMENT_FEE (8)"),
                 ("T48-CH-05-defamount-omitted-tt1", "DISBURSEMENT (1)"),
                 ("T48-CH-07-defamount-omitted-pct", "DISBURSEMENT (1), PERCENT_OF_AMOUNT"),
                 ("T48-CH-13-calc5-omitted", "TRANCHE_DISBURSEMENT (12), calc type 5")):
    d = load_exact(stem)
    code = d.get("httpStatusCode")
    msg = "; ".join(e.get("developerMessage", "") for e in d.get("errors", []))
    print("  %-36s chargeTimeType %-38s HTTP %s  %s" % (stem[8:], tt, code, msg))
    if code != "400":
        failures.append("%s: expected the omitted-amount leg to be rejected, got HTTP %s" % (stem, code))

print("\n  the DISAGREEING legs (request amount != m_charge.amount):")
for stem, defamt, reqamt in (("T48-CH-02-defamount-disagree-tt2", "9000.000000", "4444"),
                             ("T48-CH-04-defamount-disagree-tt8", "2500.000000", "3333"),
                             ("T48-CH-06-defamount-disagree-tt1", "15000.000000", "5555"),
                             ("T48-CH-08-defamount-disagree-pct", "1.234500", "2.5")):
    d = load_exact(stem)
    print("     %-34s m_charge.amount %-12s request %-6s -> totalFeeChargesCharged %s"
          % (stem[8:], defamt, reqamt, d["totalFeeChargesCharged"]))

print("\n\n######## GAP 2 -- chargeCalculationType 5 and 9 ########")
for f in sorted(O.glob("create-c*.json")) + sorted(O.glob("create-tt*.json")):
    d = json.loads(f.read_text())
    if "resourceId" in d:
        print("  %-24s HTTP 200  created charge id %s" % (f.stem, d["resourceId"]))
    else:
        msgs = [e.get("developerMessage", "") for e in d.get("errors", [])
                if "chargeCalculationType" in e.get("parameterName", "")
                or "chargeTimeType" in e.get("parameterName", "")]
        print("  %-24s HTTP %s  %s" % (f.stem, d.get("httpStatusCode"),
                                       " | ".join(msgs) or d.get("defaultUserMessage")))

compare("calc type 5 (id 13, TRANCHE) vs calc type 2 (id 3) at the same 1.2345 % -- "
        "T48-CH-10 vs T48-CH-14",
        "T48-CH-10-calc5-disbursement", "T48-CH-14-calc2-disbursement-comparator", "observe")
compare("calc type 5 WITH a dueDate vs WITHOUT -- T48-CH-11 vs T48-CH-10",
        "T48-CH-11-calc5-specifieddue", "T48-CH-10-calc5-disbursement", "observe")
compare("calc type 5 landed at all? T48-CH-10 vs the zero-charge control",
        "T48-CH-10-calc5-disbursement", "T48-CH-00-zerocharge-control", "separate")

print("\n\n######## GAP 4 -- RepaymentEvery > 3 ########")
for stem in ("T48-CH-20-repayevery4", "T48-CH-21-repayevery6", "T48-CH-22-repayevery12",
             "T48-CH-24-repayevery3-comparator", "T48-CH-23-repayevery4-instalmentfee"):
    d = load_exact(stem)
    n = len([p for p in d["periods"] if "period" in p])
    print("  %-34s periods %2d  loanTermInDays %-4s totalInterest %-12s totalFee %-10s totalRepayment %s"
          % (stem[8:], n, d["loanTermInDays"], d["totalInterestCharged"],
             d["totalFeeChargesCharged"], d["totalRepaymentExpected"]))
    for p in d["periods"]:
        if "period" not in p:
            continue
        print("      p%-2s %s -> %s  days %-4s principal %-14s interest %-12s fee %-10s total %s"
              % (p["period"], p.get("fromDate"), p.get("dueDate"), p.get("daysInPeriod"),
                 p.get("principalDue"), p.get("interestDue"), p.get("feeChargesDue"),
                 p.get("totalDueForPeriod")))

compare("repaymentEvery 4 vs 3 -- T48-CH-20 vs T48-CH-24",
        "T48-CH-20-repayevery4", "T48-CH-24-repayevery3-comparator", "separate")
compare("repaymentEvery 4 with an instalment fee vs without -- T48-CH-23 vs T48-CH-20",
        "T48-CH-23-repayevery4-instalmentfee", "T48-CH-20-repayevery4", "separate")

# --- the invariant this program already knows is violated, re-checked at repayEvery > 3 --
print("\n  INVARIANT RE-CHECK -- does totalRepaymentExpected equal the sum of "
      "totalDueForPeriod?  (T40 finding 1)")
for stem in ("T48-CH-24-repayevery3-comparator", "T48-CH-20-repayevery4",
             "T48-CH-23-repayevery4-instalmentfee", "T48-CH-02-defamount-disagree-tt2",
             "T48-CH-04-defamount-disagree-tt8", "T48-CH-06-defamount-disagree-tt1",
             "T48-CH-10-calc5-disbursement"):
    d = load_exact(stem)
    s = sum(Decimal(p["totalDueForPeriod"]) for p in d["periods"])
    tre = Decimal(d["totalRepaymentExpected"])
    print("     %-34s sum(totalDueForPeriod) %-14s totalRepaymentExpected %-14s %s"
          % (stem[8:], s, tre, "AGREE" if s == tre else "DISAGREE by %s" % (s - tre)))

print("")
if failures:
    for f in failures:
        print("BREACH: " + f, file=sys.stderr)
    sys.exit(1)
print("== T48 charge analysis PASS")
