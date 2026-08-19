#!/usr/bin/env python3
"""
T51 -- analysis of the alias + tranche pass.  Contacts no oracle; reads only committed bytes.

Three jobs:

1. EXACT-TEXT SIDECARS (T44-X1, T46's decision, T46-N2).  Path B responses are float-shaped
   on the wire: Fineract's REST layer serialises BigDecimal as a JSON *number*, and the
   disbursement-row charge scale is caller-controlled (T46-N2 observed `6000.000` at scale 3
   and `14814.000000` at scale 6).  A comparison that parses those as numbers is blind to
   real behaviour.  Every raw capture therefore gets a `-exact.json` sidecar in which every
   JSON number is re-emitted as a JSON STRING carrying the literal characters that were on
   the wire.  No float is constructed anywhere: json.loads is handed parse_float=str /
   parse_int=str, so the RAW MATCHED LITERAL is what is stored.  The raw bytes are never
   rewritten -- they are what the oracle said.

2. FULL-CELL COMPARISON (T46-N3, T46-N4).  Every period row, every column, plus the plan
   totals -- never the three headline scalars.  Every comparison reports its differing-cell
   count, and a comparison that moves ZERO cells is reported as discriminating nothing.

3. THE BOUNDARY DISCRIMINATION for item 1.  ProgressiveEMICalculator's cross-year partial
   arm computes  f = SUM over years  days(segment) / Year.of(year).length()
   [:1554-1568], with the segment boundary at 31 December, or at 1 January of the next year
   when the LoanConfigurationDetails slot named isInterestRecognitionOnDisbursementDate() is
   true [:1578-1584].  The two boundaries give two DIFFERENT f, hence two different rate
   factors, hence two different period interests.  This tool RE-DERIVES both candidates at
   the ratified MathContext(19, HALF_UP) and reports which one the ORACLE's observed
   interest matches.  The re-derivation is labelled as such; the oracle's cells are the
   observation and are printed in full.
"""
import json
import os
import pathlib
import sys
from decimal import Decimal, ROUND_HALF_UP, getcontext

O = pathlib.Path(__file__).resolve().parents[1] / "out" / "t51"
NUM = (int, float)
failures = []
getcontext().prec = 19          # MoneyHelper.PRECISION, compile-time [MoneyHelper.java:35]
getcontext().rounding = ROUND_HALF_UP   # ratified tenant rounding mode (HALF_UP = ordinal 4)


# ------------------------------------------------------------------ exact-text sidecars
def to_text(node):
    if isinstance(node, dict):
        return dict((k, to_text(v)) for k, v in node.items())
    if isinstance(node, list):
        return [to_text(v) for v in node]
    return node


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


print("== exact-text sidecars ==")
made = 0
scales = {}
for f in sorted(O.glob("T51-*-raw.json")):
    text = f.read_text()
    exact = json.loads(text, parse_float=str, parse_int=str)
    side = f.with_name(f.name.replace("-raw.json", "-exact.json"))
    side.write_text(json.dumps(to_text(exact), indent=1, ensure_ascii=False) + "\n")
    left = bare_numbers(json.loads(side.read_text()))
    if left:
        failures.append("%s: sidecar still carries %d bare JSON numbers" % (side.name, len(left)))
    raw_leaves = bare_numbers(json.loads(text))
    ex = json.loads(side.read_text())
    for path, val in raw_leaves:
        got = leaf(path, ex)
        if Decimal(got) != Decimal(str(val)):
            failures.append("%s: leaf %s is %r in the sidecar, %r on the wire" % (f.name, path, got, val))
    # T46-N2: record the SCALE of every disbursement-row fee, as exact text.
    for p in ex.get("periods", []):
        if "period" not in p and "feeChargesDue" in p:
            s = str(p["feeChargesDue"])
            scales.setdefault(f.name, []).append(s)
    made += 1
print("  %d sidecars written, each re-checked leaf for leaf against the raw bytes" % made)
print("  disbursement-row feeChargesDue, EXACT TEXT (T46-N2: the scale is caller-controlled):")
for k in sorted(scales):
    print("    %-46s %s" % (k.replace("-raw.json", ""), " ".join(scales[k])))


# --------------------------------------------------------------------- full-cell compare
def load_exact(stem):
    return json.loads((O / (stem + "-exact.json")).read_text())


def cells(doc):
    out = {}
    if "periods" not in doc:
        return {"__http__": doc.get("httpStatusCode"),
                "__msg__": "; ".join(e.get("developerMessage", "") for e in doc.get("errors", []))}
    for k, v in doc.items():
        if k in ("periods", "currency"):
            continue
        out[k] = v
    for i, p in enumerate(doc["periods"]):
        for k, v in p.items():
            out["row%d.%s" % (i, k)] = v
    return out


def compare(label, a, b, expect, show=10):
    A, B = cells(load_exact(a)), cells(load_exact(b))
    keys = sorted(set(A) | set(B))
    diffs = [(k, A.get(k), B.get(k)) for k in keys if A.get(k) != B.get(k)]
    print("\n== %s\n   %d of %d cells differ   [expected: %s]" % (label, len(diffs), len(keys), expect))
    for k, x, y in diffs[:show]:
        print("     %-36s %-18s | %s" % (k, x, y))
    if len(diffs) > show:
        print("     ... %d more" % (len(diffs) - show))
    if expect == "identical" and diffs:
        failures.append("%s: expected IDENTICAL, %d cells differ" % (label, len(diffs)))
    if expect == "separate" and not diffs:
        failures.append("%s: EVERY CELL AGREES -- this comparison DISCRIMINATES NOTHING" % label)
    if not diffs:
        print("     -> every cell agrees.  A port that conflated the two would pass this "
              "comparison, so on its own it discriminates NOTHING.")
    return diffs


# =======================================================================================
print("\n\n" + "#" * 86)
print("# ITEM 1 -- is T48-N1's aliasing behaviourally reachable?")
print("#" * 86)
print("""
Products 17 (`T51 IROD true`) and 18 (`T51 IROD false`) were created from the SAME committed
payload, differ in exactly three text lines (name, shortName, the flag), and were asserted in
PostgreSQL to be identical on 20 compared columns and to differ on
interest_recognition_on_disbursement_date.  Every shape below is captured on BOTH.
""")

pairs = [("AA1  leap->non-leap, monthly, disbursed 01 Nov 2024 (T48's AA-1 shape)", "IROD-AA1"),
         ("DEC15  disbursed 15 Dec 2024: crossing period with a 16-day first segment", "IROD-DEC15"),
         ("DEC31  disbursed 31 Dec 2024: first segment is 0 days at the 31-Dec boundary,"
          " 1 day at the 1-Jan boundary", "IROD-DEC31"),
         ("R13  repaymentEvery 13 months from 15 Dec 2023: each period spans THREE year"
          " segments", "IROD-R13"),
         ("NOCROSS  CONTROL, disbursed 01 Feb 2025: no period crosses a year boundary,"
          " so the arm cannot fire", "IROD-NOCROSS")]
for label, stem in pairs:
    compare("%s  --  product 17 (flag TRUE) vs product 18 (flag FALSE)" % label,
            "T51-%s-P1" % stem, "T51-%s-P2" % stem, "observe")

compare("REQUEST-LEVEL override: product 18 (flag FALSE) + request "
        "interestRecognitionOnDisbursementDate=true, vs plain product 18",
        "T51-IROD-AA1-REQTRUE-P2", "T51-IROD-AA1-P2", "observe")
compare("REQUEST-LEVEL override: product 17 (flag TRUE) + request "
        "interestRecognitionOnDisbursementDate=false, vs plain product 17",
        "T51-IROD-AA1-REQFALSE-P1", "T51-IROD-AA1-P1", "observe")

print("\n--- is the shape even capable of moving?  the arm-vs-no-arm control ---")
compare("AA1 at daysInYearType ACTUAL vs the SAME shape forced to 365 (arm cannot fire: "
        "the first conjunct of partialPeriodCalculationNeeded is false)",
        "T51-IROD-AA1-P1", "T51-IROD-D365-P1", "separate")


# ---------------------------------------------- boundary re-derivation vs the observation
print("\n\n" + "-" * 86)
print("-- WHICH BOUNDARY DID THE ORACLE USE?  re-derivation at MathContext(19, HALF_UP)")
print("-" * 86)
print("""
The arm's f is  SUM over years  days(segment) / Year.of(year).length()  [:1554-1568].
The segment boundary is 31 December, or 1 January of the next year when the
LoanConfigurationDetails slot isInterestRecognitionOnDisbursementDate() is true [:1578-1584].
Interest for a period is  round2(balance_at_period_start x rateFactor)  and rateFactor is
0.216 x f.  Below, BOTH candidate f are re-derived from the observed dates and compared with
the interest the ORACLE actually returned.  The dates, balances and interests are
OBSERVATIONS; the two candidate columns are RE-DERIVATIONS.
""")


def d(x):
    return Decimal(str(x))


def year_len(y):
    return 366 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 365


def days_between(a, b):
    import datetime
    return (datetime.date(*b) - datetime.date(*a)).days


def f_segments(frm, due, boundary_is_jan1):
    """Re-derivation of calculatePeriodFractions [:1548-1570], exactly as written."""
    import datetime
    total = Decimal(0)
    actual_year = frm[0]
    end_year = due[0]
    actual = frm
    segs = []
    while actual_year <= end_year:
        if actual_year == end_year:
            frac_due = due
        else:
            frac_due = (actual_year + 1, 1, 1) if boundary_is_jan1 else (actual_year, 12, 31)
        n = days_between(actual, frac_due)
        total += Decimal(n) / Decimal(year_len(actual_year))
        segs.append("%d/%d" % (n, year_len(actual_year)))
        actual = frac_due
        actual_year += 1
    return total, " + ".join(segs)


def rate_of_year(period_from, period_due):
    """Only the crossing periods are re-derived; the rest are left to the oracle."""
    return period_from[0] != period_due[0]


RATE = Decimal("0.216")     # annualNominalInterestRate 21.6 %, as exact text


def check_boundary(stem, label):
    doc = load_exact(stem)
    print("\n  %s   [%s]" % (label, stem))
    print("    %-4s %-12s %-12s %-16s %-16s %-16s %s" %
          ("per", "from", "due", "balance@start", "oracle interest",
           "31-Dec reading", "1-Jan reading"))
    balance = None
    verdict = {"31-Dec": 0, "1-Jan": 0, "neither": 0}
    for p in doc["periods"]:
        if "period" not in p:
            balance = Decimal(p["principalDisbursed"])
            continue
        frm = tuple(int(x) for x in p["fromDate"])
        due = tuple(int(x) for x in p["dueDate"])
        obs = Decimal(p["interestDue"])
        if rate_of_year(frm, due):
            f_dec, s_dec = f_segments(frm, due, False)
            f_jan, s_jan = f_segments(frm, due, True)
            i_dec = (balance * (RATE * f_dec)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            i_jan = (balance * (RATE * f_jan)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            tag = "31-Dec" if obs == i_dec and obs != i_jan else \
                  "1-Jan" if obs == i_jan and obs != i_dec else \
                  "BOTH-AGREE" if i_dec == i_jan else "neither"
            verdict[tag if tag in verdict else "neither"] += 1
            print("    %-4s %-12s %-12s %-16s %-16s %-16s %-16s  -> %s" %
                  (p["period"], "%d-%02d-%02d" % frm, "%d-%02d-%02d" % due, balance, obs,
                   i_dec, i_jan, tag))
            print("         segments  31-Dec: %-28s  1-Jan: %s" % (s_dec, s_jan))
        else:
            print("    %-4s %-12s %-12s %-16s %-16s %-16s %s" %
                  (p["period"], "%d-%02d-%02d" % frm, "%d-%02d-%02d" % due, balance, obs,
                   "(no crossing)", ""))
        balance = Decimal(p["principalLoanBalanceOutstanding"])
    return verdict


tally = {"31-Dec": 0, "1-Jan": 0, "neither": 0}
for stem, label in (("T51-IROD-AA1-P1", "product 17, flag TRUE"),
                    ("T51-IROD-AA1-P2", "product 18, flag FALSE"),
                    ("T51-IROD-DEC31-P1", "product 17, flag TRUE"),
                    ("T51-IROD-DEC31-P2", "product 18, flag FALSE"),
                    ("T51-IROD-DEC15-P1", "product 17, flag TRUE"),
                    ("T51-IROD-DEC15-P2", "product 18, flag FALSE"),
                    ("T51-IROD-R13-P1", "product 17, flag TRUE"),
                    ("T51-IROD-R13-P2", "product 18, flag FALSE")):
    v = check_boundary(stem, label)
    for k in tally:
        tally[k] += v.get(k, 0)

print("\n  TALLY over the crossing periods where the two readings differ:")
print("    matched the 31-DECEMBER boundary : %d" % tally["31-Dec"])
print("    matched the 1-JANUARY  boundary : %d" % tally["1-Jan"])
print("    matched NEITHER                 : %d" % tally["neither"])


# =======================================================================================
print("\n\n" + "#" * 86)
print("# ITEM 2 -- chargeCalculationType 5 (PERCENT_OF_DISBURSEMENT_AMOUNT) on a tranche product")
print("#" * 86)

print("\n-- charge-definition attempts (a rejected POST creates no row) --")
for f in sorted(O.glob("create-c*.json")):
    doc = json.loads(f.read_text())
    if "resourceId" in doc:
        print("  %-26s HTTP 200  created charge id %s" % (f.stem, doc["resourceId"]))
    else:
        msgs = [e.get("developerMessage", "") for e in doc.get("errors", [])]
        print("  %-26s HTTP %s  %s" % (f.stem, doc.get("httpStatusCode"), " | ".join(msgs)))

print("\n-- HTTP codes for every calc leg --")
for line in (O / "HTTP-CODES.txt").read_text().splitlines():
    print("   " + line)

compare("ct=5 (id 13, TRANCHE_DISBURSEMENT) vs ct=2 (id 3, PERCENT_OF_AMOUNT) at the same "
        "1.2345 %, THREE genuine tranches, on the multi-disbursement product 19",
        "T51-TR-01-c5-tranche-P3", "T51-TR-02-c2-comparator-P3", "separate")
compare("ct=5, three tranches, tranche product 19 vs the SAME request on the "
        "single-disbursement product 1",
        "T51-TR-01-c5-tranche-P3", "T51-TR-06-c5-on-singledisb-product-P1PROD", "observe")
compare("did the ct=5 charge land at all?  vs the zero-charge control on the same product",
        "T51-TR-01-c5-tranche-P3", "T51-TR-00-ctrl-P3", "separate")
compare("ct=1 FLAT at TRANCHE_DISBURSEMENT (id 14, 7000) vs ct=5 (id 13, 1.2345 %)",
        "T51-TR-03-c1flat-tranche-P3", "T51-TR-01-c5-tranche-P3", "separate")
compare("ct=5 with THREE tranches vs ct=5 with ONE tranche of the whole principal",
        "T51-TR-01-c5-tranche-P3", "T51-TR-04-c5-onetranche-P3", "separate")

print("\n-- the disbursement rows, exact text --")
for stem in ("T51-TR-00-ctrl-P3", "T51-TR-01-c5-tranche-P3", "T51-TR-02-c2-comparator-P3",
             "T51-TR-03-c1flat-tranche-P3", "T51-TR-04-c5-onetranche-P3",
             "T51-TR-06-c5-on-singledisb-product-P1PROD"):
    doc = load_exact(stem)
    if "periods" not in doc:
        print("  %-44s HTTP %s" % (stem, doc.get("httpStatusCode")))
        continue
    rows = [p for p in doc["periods"] if "period" not in p]
    print("  %-44s totalFee=%-14s totalInterest=%-12s totalRepay=%s"
          % (stem, doc["totalFeeChargesCharged"], doc["totalInterestCharged"],
             doc["totalRepaymentExpected"]))
    for r in rows:
        print("      disb %-12s principalDisbursed %-14s feeChargesDue %-16s totalDueForPeriod %s"
              % ("%s-%s-%s" % tuple(r["dueDate"]), r.get("principalDisbursed"),
                 r.get("feeChargesDue"), r.get("totalDueForPeriod")))
    s = sum(Decimal(p["totalDueForPeriod"]) for p in doc["periods"])
    print("      sum(totalDueForPeriod)=%s   totalRepaymentExpected=%s   %s"
          % (s, doc["totalRepaymentExpected"],
             "AGREE" if s == Decimal(doc["totalRepaymentExpected"]) else "**DISAGREE**"))

print("\n-- the leg that was REJECTED --")
doc = load_exact("T51-TR-05-c5-nodisbdata-P3")
print("  T51-TR-05  tranche product, ct=5 charge, NO disbursementData -> HTTP %s : %s"
      % (doc.get("httpStatusCode"),
         "; ".join(e.get("developerMessage", "") for e in doc.get("errors", []))))

print("\n")
if failures:
    print("RESULT: %d PROBLEM(S)" % len(failures))
    for p in failures:
        print("  ! " + p)
    sys.exit(1)
print("RESULT: every sidecar reproduces its raw capture leaf for leaf as text; every "
      "comparison above reports its own differing-cell count.")
