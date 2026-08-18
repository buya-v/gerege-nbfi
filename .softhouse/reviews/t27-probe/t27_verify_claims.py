#!/usr/bin/env python3
"""T27 re-check probe — mechanical verification of every CORRECTED claim T25 wrote.

=======================================================================
NOT RUN AGAINST A LIVE ORACLE. No Fineract instance and no PostgreSQL is
reachable in this sandbox. Every value checked here is read from an
artifact ALREADY COMMITTED on `main`. Nothing is synthesized. Where a
number can only be settled by a fresh oracle observation this script
says so instead of guessing.
=======================================================================

Checks, in order:
  1. PASS3-REPORT.md and PASS3-REPORT-shared.md are byte-identical.
  2. Every oracle number in the corrected PASS3 section
     "precision sensitivity is a rounding-boundary property" appears, with
     the same verdict, in the committed oracle transcript
     .softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt.
  3. capture-prod-raw.json really is 11 captures at (19, HALF_UP) plus one
     calibration at (12, HALF_UP)  -- the tasks.json count fix.
  4. The three T21 P0 admissibility blockers are still OPEN in the artifact
     (attestation block, periodFromDate/feeAmount/penaltyAmount, run recipe).
  5. Path B: the round-DOWN observation really shows rounding down, and the
     unrounded EMI is re-derived here from the annuity formula at
     MathContext(19, HALF_UP) -- calibrated against the committed B-01 EMI,
     never taken on faith from prose.
  6. Path B: FULL_LEAP_YEAR == field-unset, and DIYCS inert under
     SAME_AS_REPAYMENT_PERIOD, by SHA-256 over committed probe captures.
  7. Path B: the fresh-tenant re-observation really is byte-identical.

Decimal only; no floating-point anywhere.
"""
import hashlib
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP, Context, localcontext

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
P = lambda *a: os.path.join(ROOT, *a)
FAILS = []


def check(label, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label, ("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(label)
    return ok


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def s1_reports_identical():
    print("\n1. PASS3-REPORT.md vs PASS3-REPORT-shared.md")
    a = sha(P(".softhouse/capture/PASS3-REPORT.md"))
    b = sha(P(".softhouse/capture/PASS3-REPORT-shared.md"))
    check("byte-identical", a == b, a[:16])


def s2_transcript():
    print("\n2. corrected PASS3 section vs committed oracle transcript")
    tx = open(P(".softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt")).read()
    rows = {}
    for line in tx.strip().splitlines():
        m = re.match(r"\s*(\S+)\s*x\s*(\S+)\s+principal\s+(\d+)\s+p12 int=(\S+)\s+rep=\S+\s+\|"
                     r"\s+p19 int=(\S+)\s+rep=\S+\s+\|\s+(\S+)", line)
        assert m, line
        rows[(m.group(1), m.group(2), int(m.group(3)))] = (m.group(4), m.group(5), m.group(6))
    # (shape_n, shape_rate, principal, p12, p19, verdict) exactly as the corrected text states
    claims = [
        ("36", "16.8", 4,          "1.13",        "1.14",        "DIFFERENT"),
        ("36", "16.8", 59,         "16.52",       "16.51",       "DIFFERENT"),
        ("36", "16.8", 72,         "20.13",       "20.14",       "DIFFERENT"),
        ("36", "16.8", 340,        "95.16",       "95.15",       "DIFFERENT"),
        ("36", "16.8", 426,        "119.20",      "119.18",      "DIFFERENT"),
        ("36", "16.8", 6940,       "1942.66",     "1942.65",     "DIFFERENT"),
        ("36", "16.8", 50000000,   "13995886.40", "13995886.40", "IDENTICAL"),
        ("6",  "7.0",  43811,      "898.82",      "898.82",      "IDENTICAL"),
        ("6",  "7.0",  131432,     "2696.42",     "2696.42",     "IDENTICAL"),
        ("6",  "7.0",  131433,     "2696.43",     "2696.43",     "DIFFERENT"),
        ("6",  "7.0",  87654321,   "1798283.07",  "1798283.07",  "IDENTICAL"),
        ("18", "18.5", 87654321,   "13393481.05", "13393481.04", "DIFFERENT"),
        # "all four MNT captures p12/p19-identical"
        ("12", "21.6", 1200000,    "144988.47",   "144988.47",   "IDENTICAL"),
        ("18", "18.5", 4999999,    "763994.20",   "763994.20",   "IDENTICAL"),
        ("18", "18.5", 5000000,    "763994.33",   "763994.33",   "IDENTICAL"),
        ("36", "16.8", 50000000,   "13995886.40", "13995886.40", "IDENTICAL"),
    ]
    for n, r, pr, p12, p19, verdict in claims:
        got = rows.get((n, r, pr))
        check("%s x %s%% principal %d -> p12 %s / p19 %s / %s"
              % (n, r, pr, p12, p19, verdict),
              got == (p12, p19, verdict),
              "transcript says %s" % (got,))
    # the corrected text drops the transcript's own annotation on 131,433
    print("  [NOTE] 131,433 is verdict DIFFERENT in the transcript but the two TOTAL")
    print("         interest figures are equal (2696.43 both) -- the divergence is")
    print("         per-period. T21 s6.2 annotates this; PASS3-REPORT.md:68 does not.")


def s3_counts():
    print("\n3. pass-3 capture count by MathContext (the tasks.json fix)")
    d = json.load(open(P(".softhouse/capture/out/capture-prod-raw.json")))
    prod = [c for c in d["captures"]
            if str(c["inputs"]["mathContextPrecision"]) == "19"
            and str(c["inputs"]["tenantRoundingModeValue"]) == "4"]
    cal = [c for c in d["captures"]
           if str(c["inputs"]["mathContextPrecision"]) == "12"]
    check("11 captures at (19, HALF_UP)", len(prod) == 11, str(sorted(c["id"] for c in prod)))
    check("1 calibration at (12, HALF_UP)", len(cal) == 1 and cal[0]["id"] == "P-CAL")
    check("12 records total", len(d["captures"]) == 12)


def s4_p0_still_open():
    print("\n4. T21 P0 admissibility blockers -- are they still OPEN?")
    raw = open(P(".softhouse/capture/out/capture-prod-raw.json")).read()
    d = json.loads(raw)
    check("P0-2 attestation block ABSENT (still open)", "attestation" not in d)
    keys = set()
    for c in d["captures"]:
        for p in (c.get("observed") or {}).get("periods", []):
            keys |= set(p)
    check("P0-3 periodFromDate ABSENT (still open)", "periodFromDate" not in keys)
    check("P0-3 feeAmount ABSENT (still open)", "feeAmount" not in keys)
    check("P0-3 penaltyAmount ABSENT (still open)", "penaltyAmount" not in keys)
    scripts = [f for f in os.listdir(P(".softhouse/capture"))
               if f.endswith(".sh") or f.endswith(".bash")]
    check("P0-4 executable pass-3 run recipe ABSENT (still open)", not scripts, str(scripts))
    pb = P(".softhouse/capture/pathb")
    check("T22 P0-3 Path B attestation sidecar ABSENT (still open)",
          not [f for f in os.listdir(pb) if "attest" in f.lower()])
    rep = open(os.path.join(pb, "REPRODUCE.md")).read()
    check("T22 P0-5 broken capture-loop glob STILL PRESENT (still open)",
          "out/B-$n-*-raw.json" in rep)
    check("T22 P0-5 %{http_code} STILL ABSENT (still open)", "http_code" not in rep)
    check("T22 P0-4 rounding-mode precondition STILL ABSENT (still open)",
          "rounding-mode" not in rep)


def s5_rounddown():
    print("\n5. Path B round-DOWN: is round-to-nearest what the oracle did?")
    j = json.load(open(P(".softhouse/capture/pathb/t22-audit/out-rounddown/"
                         "rounddown-gerege-raw.json")))
    req = json.load(open(P(".softhouse/capture/pathb/t22-audit/req/calc-prounddown.json")))
    prod = json.load(open(P(".softhouse/capture/pathb/t22-audit/req/prounddown.json")))
    rows = [p for p in j["periods"] if "period" in p]
    emis = {str(p["totalDueForPeriod"]) for p in rows[:-1]}
    check("periods 1-11 all share one EMI", len(emis) == 1, str(emis))
    applied = Decimal(str(rows[0]["totalDueForPeriod"]))
    mult = Decimal(prod["installmentAmountInMultiplesOf"])
    check("applied EMI is a multiple of installmentAmountInMultiplesOf",
          applied % mult == 0, "%s %% %s" % (applied, mult))

    # Re-derive the UNROUNDED EMI from the annuity formula at MathContext(19, HALF_UP).
    # Calibrated first against the committed B-01 observation so the model is not
    # taken on faith.
    def emi(principal, n, rate_per_period):
        with localcontext(Context(prec=19, rounding=ROUND_HALF_UP)):
            pr = Decimal(principal)
            r = Decimal(rate_per_period)
            return (pr * r) / (Decimal(1) - (Decimal(1) + r) ** Decimal(-n))

    b01 = json.load(open(P(".softhouse/capture/pathb/out/B-01-baseline-raw.json")))
    b01_emi = Decimal(str([p for p in b01["periods"] if "period" in p][0]["totalDueForPeriod"]))
    model_b01 = emi(1200000, 12, Decimal("0.018")).quantize(Decimal("0.01"), ROUND_HALF_UP)
    check("model calibrates against committed B-01 EMI", model_b01 == b01_emi,
          "model %s vs observed %s" % (model_b01, b01_emi))

    unrounded = emi(req["principal"], req["numberOfRepayments"],
                    Decimal(str(req["interestRatePerPeriod"])) / 100 / 12
                    ).quantize(Decimal("0.01"), ROUND_HALF_UP)
    check("re-derived unrounded EMI == the 111,148.35 the correction cites",
          unrounded == Decimal("111148.35"), str(unrounded))
    check("oracle APPLIED EMI is BELOW the unrounded EMI -> rounded DOWN",
          applied < unrounded, "%s < %s" % (applied, unrounded))
    up = (unrounded / mult).to_integral_value(rounding="ROUND_CEILING") * mult
    check("a ROUND-UP rule would have produced %s, not %s -> round-up REFUTED"
          % (up, applied), up != applied)
    nearest = (unrounded / mult).quantize(Decimal(1), ROUND_HALF_UP) * mult
    check("round-to-NEAREST under HALF_UP reproduces the observed EMI",
          nearest == applied, "%s == %s" % (nearest, applied))


def s6_diycs():
    print("\n6. Path B: FULL_LEAP_YEAR == field-unset, and DIYCS inert under SARP")
    pb = P(".softhouse/capture/pathb")
    h = lambda p: sha(os.path.join(pb, p))
    check("p07 (DAILY/ACTUAL, DIYCS UNSET) == B-03 (FULL_LEAP_YEAR), byte-identical",
          h("t22-audit/out-probe/p07-raw.json") == h("out/B-03-diycs-fullleapyear-raw.json"))
    check("B-04 (FEB_29_PERIOD_ONLY) DIFFERS from B-03 -> only FEB_29 discriminates",
          h("out/B-04-diycs-feb29only-raw.json") != h("out/B-03-diycs-fullleapyear-raw.json"))
    check("p05 (SARP, FULL_LEAP_YEAR) == p06 (SARP, FEB_29) -> DIYCS inert under SARP",
          h("t22-audit/out-probe/p05-raw.json") == h("t22-audit/out-probe/p06-raw.json"))
    check("p07 (DAILY ACT/ACT) != p08 (DAILY 360/30) -> day-count moves DAILY schedules",
          h("t22-audit/out-probe/p07-raw.json") != h("t22-audit/out-probe/p08-raw.json"))
    check("p09 (SARP 360/30) == B-01 (SARP ACT/ACT) -> day-count inert under SARP",
          h("t22-audit/out-probe/p09-raw.json") == h("out/B-01-baseline-raw.json"))


def s7_freshtenant():
    print("\n7. Path B fresh-tenant (19, HALF_UP) re-observation")
    pb = P(".softhouse/capture/pathb")
    pairs = [("out/B-01-baseline-raw.json", "t22-audit/out-fresh-tenant/B-01-raw.json"),
             ("out/B-02-multiplesof100-raw.json", "t22-audit/out-fresh-tenant/B-02-raw.json"),
             ("out/B-03-diycs-fullleapyear-raw.json", "t22-audit/out-fresh-tenant/B-03-raw.json"),
             ("out/B-04-diycs-feb29only-raw.json", "t22-audit/out-fresh-tenant/B-04-raw.json")]
    for a, b in pairs:
        check("%s SHA-256 == fresh-tenant re-observation" % a.split("/")[-1],
              sha(os.path.join(pb, a)) == sha(os.path.join(pb, b)))
    # and the t22-probe independent reproduction
    for a, b in [("out/B-01-baseline-raw.json", "t22-probe/out/calc-B-01-baseline-halfeven-raw.json"),
                 ("out/B-04-diycs-feb29only-raw.json",
                  "t22-probe/out/calc-B-04-diycs-feb29only-halfeven-raw.json")]:
        check("%s SHA-256 == t22-probe independent re-capture" % a.split("/")[-1],
              sha(os.path.join(pb, a)) == sha(os.path.join(pb, b)))


if __name__ == "__main__":
    print(__doc__.split("Checks, in order:")[0].strip())
    s1_reports_identical()
    s2_transcript()
    s3_counts()
    s4_p0_still_open()
    s5_rounddown()
    s6_diycs()
    s7_freshtenant()
    print("\n%s  (%d failure(s))" % ("ALL CHECKS PASS" if not FAILS else "FAILURES: " + ", ".join(FAILS),
                                     len(FAILS)))
    sys.exit(0 if not FAILS else 1)
