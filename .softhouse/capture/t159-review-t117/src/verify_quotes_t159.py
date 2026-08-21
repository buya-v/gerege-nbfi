#!/usr/bin/env python3
"""T159 — P-46 QUOTATION AUDIT of T117's handoff against the artefacts it cites.

P-46 (recorded this fire): a fabricated capture excerpt survived into merged
evidence because "quotations get believed". This script re-derives, from T117's RAW
captures ONLY, every number and every quoted row value T117's handoff prints, and
prints CLAIM vs OBSERVED side by side so a mismatch cannot hide.

MONEY DISCIPLINE (P-25): integer minor units throughout, parsed by splitting the
oracle's BigDecimal.toPlainString() JSON string on '.'. Fraction for rate algebra.
No float is constructed anywhere in this file.
"""
import gzip
import json
import sys
from decimal import Decimal
from fractions import Fraction

DP = 2
OK, BAD = [], []


def minor(s, dp=DP):
    if not isinstance(s, str):
        raise TypeError("money must arrive as a JSON string, got %r" % (s,))
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    whole, _, frac = s.partition(".")
    frac = frac + "0" * (dp - len(frac))
    v = int(whole or "0") * (10 ** dp) + int(frac or "0")
    return -v if neg else v


def load(p):
    with gzip.open(p, "rt") as fh:
        return json.load(fh, parse_float=Decimal)


def check(label, claimed, observed):
    (OK if claimed == observed else BAD).append((label, claimed, observed))


def main():
    p1, p2 = sys.argv[1], sys.argv[2]
    d1, d2 = load(p1), load(p2)
    c1 = {c["id"]: c for c in d1["captures"]}
    c2 = {c["id"]: c for c in d2["captures"]}
    allc = list(d1["captures"]) + list(d2["captures"])
    probe = [c for c in allc if not c["id"].startswith("P-CAL")]

    def residual(c):
        per = c["observed"]["periods"]
        d = sum(minor(p["principal"]) for p in per if p["type"] == "DISBURSEMENT")
        a = sum(minor(p["principal"]) for p in per if p["type"] == "REPAYMENT")
        return d, a, d - a

    famB = [c for c in probe if residual(c)[2] != 0]
    clean = [c for c in probe if residual(c)[2] == 0]

    # --- handoff section 2: skip accounting -------------------------------------
    check("s2 pass-1 cases asked", 200, len(d1["captures"]) - 2)
    check("s2 pass-2 cases asked", 87, len(d2["captures"]) - 2)
    check("s2 total probe cases", 287, len(probe))
    check("s2 errored cases", 0, sum(1 for c in allc if c.get("observed") is None or "error" in c))
    check("s2 pass-1 emitted rows", 93433, sum(len(c["observed"]["periods"]) for c in d1["captures"]))
    check("s2 pass-2 emitted rows", 25181, sum(len(c["observed"]["periods"]) for c in d2["captures"]))
    check("s2 pass-1 calibrations", 2, sum(1 for c in d1["captures"] if c["id"].startswith("P-CAL")))
    check("s2 pass-2 calibrations", 2, sum(1 for c in d2["captures"] if c["id"].startswith("P-CAL")))
    check("s2 gitDirty false (p1)", "false", d1["attestation"]["fineract"]["gitDirty"])
    check("s2 gitDirty false (p2)", "false", d2["attestation"]["fineract"]["gitDirty"])
    check("s2 pinned commit (p1)", "426a23544e8426a38ae43ae404670a0a7e85b9eb",
          d1["attestation"]["fineract"]["gitCommitId"])
    check("s2 pinned commit (p2)", "426a23544e8426a38ae43ae404670a0a7e85b9eb",
          d2["attestation"]["fineract"]["gitCommitId"])

    # --- handoff section 1(ii): the headline cell, quoted row by quoted row ------
    h = c2["T117P2-R600p0-N1000-B501"]
    reps = [p for p in h["observed"]["periods"] if p["type"] == "REPAYMENT"]
    d, a, r = residual(h)
    check("s1 headline disbursed (minor)", 501, d)
    check("s1 headline amortized (minor)", 0, a)
    check("s1 headline residual (minor)", 501, r)
    check("s1 headline: every REPAYMENT row principal '0.00'", 1000,
          sum(1 for p in reps if p["principal"] == "0.00"))
    check("s1 headline REPAYMENT row count", 1000, len(reps))
    check("s1 headline balance frozen at 5.01", ["5.01"], sorted({p["balance"] for p in reps}))
    check("s1 headline totalPrincipalAmount", "0.00", h["observed"]["totalPrincipalAmount"])
    check("s1 headline totalInterestAmount (MNT 2,505.01)", "2505.01",
          h["observed"]["totalInterestAmount"])
    check("s1 headline term: 83 years (last dueDate)", "2107-05-01", reps[-1]["dueDate"])
    check("s1 headline first dueDate", "2024-02-01", reps[0]["dueDate"])

    # --- handoff section 1(ii): 14 distinct principals, all odd -----------------
    prins = sorted({minor(c["inputs"]["disbursementAmount"]) for c in famB})
    check("s1 famB distinct principals",
          [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 51, 101, 501], prins)
    check("s1 famB distinct principal COUNT", 14, len(prins))
    check("s1 famB all odd", True, all(p % 2 == 1 for p in prins))

    # --- handoff section 1(ii) table: first failing term per principal ----------
    firsts = {}
    for c in famB:
        b = minor(c["inputs"]["disbursementAmount"])
        n = c["inputs"]["numberOfRepayments"]
        firsts[b] = min(firsts.get(b, 10 ** 9), n)
    for b, claimed in ((3, 108), (5, 108), (7, 108), (9, 108), (11, 108), (21, 108),
                       (51, 108), (13, 150), (15, 150), (17, 150), (19, 150),
                       (101, 250), (501, 1000)):
        check("s1 first failing term at B=%d" % b, claimed, firsts.get(b))
    for b in (1001, 10001, 100001, 1000001, 100000001, 120000001):
        check("s1 B=%d never family B" % b, None, firsts.get(b))

    # --- handoff section 1(i): band structure at B = 1 --------------------------
    b1 = sorted([c for c in probe if minor(c["inputs"]["disbursementAmount"]) == 1],
                key=lambda c: c["inputs"]["numberOfRepayments"])
    check("s1 B=1 cell count", 168, len(b1))
    check("s1 B=1 family-B count", 111, sum(1 for c in b1 if residual(c)[2] != 0))
    check("s1 B=1 clean count", 57, sum(1 for c in b1 if residual(c)[2] == 0))
    fam_terms = {c["inputs"]["numberOfRepayments"] for c in b1 if residual(c)[2] != 0}
    cln_terms = {c["inputs"]["numberOfRepayments"] for c in b1 if residual(c)[2] == 0}
    check("s1 band 300..361 all family B", True, all(n in fam_terms for n in range(300, 362)))
    check("s1 band 362..363 all clean", True, all(n in cln_terms for n in (362, 363)))
    check("s1 band 364..390 all family B", True, all(n in fam_terms for n in range(364, 391)))
    check("s1 band 391..400 all clean", True, all(n in cln_terms for n in range(391, 401)))
    check("s1 620,630,640,650 family B", True, all(n in fam_terms for n in (620, 630, 640, 650)))
    check("s1 860,870 family B", True, all(n in fam_terms for n in (860, 870)))
    check("s1 910..990 step 10 family B", True,
          all(n in fam_terms for n in range(910, 1000, 10)))
    check("s1 995..999 all family B", True, all(n in fam_terms for n in range(995, 1000)))
    check("s1 n=1000 family B", True, 1000 in fam_terms)
    check("s1 n=250 family B (CTRL re-ask)", True, 250 in fam_terms)
    check("s1 880,890,900 clean", True, all(n in cln_terms for n in (880, 890, 900)))

    # --- handoff section 4: PARTIAL amortization --------------------------------
    for n, ca, cr in ((108, 5, 6), (121, 4, 7), (150, 2, 9)):
        cc = c2["T117P2-R600p0-N%d-B11" % n]
        d, a, r = residual(cc)
        check("s4 B=11 n=%d disbursed" % n, 11, d)
        check("s4 B=11 n=%d amortized" % n, ca, a)
        check("s4 B=11 n=%d residual" % n, cr, r)
        check("s4 B=11 n=%d non-zero principal rows" % n, 1,
              len([p for p in cc["observed"]["periods"]
                   if p["type"] == "REPAYMENT" and minor(p["principal"]) != 0]))
    check("s4 famB cells summing to zero", 152, sum(1 for c in famB if residual(c)[1] == 0))
    check("s4 famB cells NOT summing to zero", 3, sum(1 for c in famB if residual(c)[1] != 0))
    check("s4 famB total", 155, len(famB))
    check("s4 residual == final balance on all 291 cases", 291,
          sum(1 for c in allc
              if residual(c)[2] == minor([p for p in c["observed"]["periods"]
                                          if p["type"] == "REPAYMENT"][-1]["balance"])))
    check("s4 total cases both passes", 291, len(allc))
    # last row interest varies with B
    for b, want in ((1, "0.01"), (3, "0.04"), (5, "0.07"), (501, "7.51")):
        cell = [c for c in famB if minor(c["inputs"]["disbursementAmount"]) == b]
        got = sorted({[p for p in c["observed"]["periods"]
                       if p["type"] == "REPAYMENT"][-1]["interest"] for c in cell})
        check("s4 last-row interest at B=%d" % b, True, want in got)

    # --- handoff section 5: the tie DESCRIPTION ---------------------------------
    half = 0
    integer = 0
    floor_ok = 0
    for c in famB:
        b = minor(c["inputs"]["disbursementAmount"])
        rr = Fraction(c["inputs"]["annualNominalInterestRate"]) / 100 / 12
        br = b * rr
        if (2 * br).denominator == 1 and int(2 * br) % 2 == 1:
            half += 1
        if br.denominator == 1:
            integer += 1
        inter = [p for p in c["observed"]["periods"] if p["type"] == "REPAYMENT"][:-1]
        if sorted({minor(p["total"]) for p in inter}) == [br.numerator // br.denominator]:
            floor_ok += 1
    check("s5 famB cells with B*r a half-integer", 155, half)
    check("s5 famB cells with B*r an integer", 0, integer)
    check("s5 famB intermediate total == floor(B*r)", 155, floor_ok)

    odd_clean_p1 = sum(1 for c in d1["captures"]
                       if not c["id"].startswith("P-CAL")
                       and residual(c)[2] == 0
                       and minor(c["inputs"]["disbursementAmount"]) % 2 == 1)
    odd_clean_p2 = sum(1 for c in d2["captures"]
                       if not c["id"].startswith("P-CAL")
                       and residual(c)[2] == 0
                       and minor(c["inputs"]["disbursementAmount"]) % 2 == 1)
    check("s5 odd-B non-family-B cells, pass 1", 62, odd_clean_p1)
    check("s5 odd-B non-family-B cells, pass 2", 38, odd_clean_p2)
    check("s5 odd-B non-family-B cells, total", 100, odd_clean_p1 + odd_clean_p2)
    # T117 says "100 of the 136 non-family-B cells".  Count the denominator BOTH ways.
    check("s5 DENOMINATOR: non-family-B PROBE cells (excl. 4 calibrations)", 136, len(clean))
    check("s5 DENOMINATOR: non-family-B cells INCLUDING calibrations", 136,
          len(allc) - len(famB))

    # --- handoff section 3: prediction scoring, re-derived ----------------------
    check("s3 pass-1 probe cells", 200, len(d1["captures"]) - 2)
    p1fam = [c for c in d1["captures"] if not c["id"].startswith("P-CAL") and residual(c)[2] != 0]
    check("s3 P1: B=1 n in [300,1000] family-B count", 110,
          sum(1 for c in p1fam if minor(c["inputs"]["disbursementAmount"]) == 1
              and 300 <= c["inputs"]["numberOfRepayments"] <= 1000))
    check("s3 P1: B=1 n in [300,1000] clean count", 56,
          sum(1 for c in d1["captures"] if not c["id"].startswith("P-CAL")
              and minor(c["inputs"]["disbursementAmount"]) == 1
              and 300 <= c["inputs"]["numberOfRepayments"] <= 1000
              and residual(c)[2] == 0))
    check("s3 P2: family-B cells at B in {2,3,4,5} (pass 1)", 11,
          sum(1 for c in p1fam if minor(c["inputs"]["disbursementAmount"]) in (2, 3, 4, 5)))
    check("s3 P3: pass-1 B>=2 cells", 32,
          sum(1 for c in d1["captures"] if not c["id"].startswith("P-CAL")
              and minor(c["inputs"]["disbursementAmount"]) >= 2))
    check("s3 P3: of those, family B", 11,
          sum(1 for c in p1fam if minor(c["inputs"]["disbursementAmount"]) >= 2))
    check("s3 P6: pass-1 largest failing principal (minor)", 5,
          max(minor(c["inputs"]["disbursementAmount"]) for c in p1fam))
    check("s3 Q3: even-B cells in pass 2, all clean", 16,
          sum(1 for c in d2["captures"] if not c["id"].startswith("P-CAL")
              and minor(c["inputs"]["disbursementAmount"]) % 2 == 0))
    check("s3 Q3: even-B family-B cells in pass 2", 0,
          sum(1 for c in d2["captures"] if not c["id"].startswith("P-CAL")
              and minor(c["inputs"]["disbursementAmount"]) % 2 == 0 and residual(c)[2] != 0))
    check("s3 Q4: B=13,15,17,19 family B at n=150", True,
          all(residual(c2["T117P2-R600p0-N150-B%d" % b])[2] != 0 for b in (13, 15, 17, 19)))
    check("s3 Q4: B=6,8,10,12,14,16,18,20 clean at n=150", True,
          all(residual(c2["T117P2-R600p0-N150-B%d" % b])[2] == 0
              for b in (6, 8, 10, 12, 14, 16, 18, 20)))

    # --- handoff section 2: the four reproduction re-asks ------------------------
    def canon(o):
        return json.dumps(o, sort_keys=True, separators=(",", ":"), default=str)

    def cmp_cells(a, b, allsrc):
        A = allsrc[a]
        B = allsrc[b]
        ind = [k for k in set(list(A["inputs"]) + list(B["inputs"]))
               if k not in ("tenantId", "tenantRoundingModeValue")
               and A["inputs"].get(k) != B["inputs"].get(k)]
        return canon(A["observed"]) == canon(B["observed"]), ind

    src = dict(c1)
    src.update(c2)
    # T84's and T100's cells are not in this directory; the two pass-1-vs-pass-2
    # re-asks ARE, and T159 checks those here.  The T84/T100 pair is checked
    # separately against those tasks' own committed captures.
    same, ind = cmp_cells("T117P2-R600p0-N104-B5", "T117-BS-R600p0-N104-B5", src)
    check("s2 RP re-ask N104-B5 byte-identical", True, same)
    check("s2 RP re-ask N104-B5 input diffs excl. tenant id", [], ind)
    same, ind = cmp_cells("T117P2-R600p0-N300-B3", "T117-BS-R600p0-N300-B3", src)
    check("s2 RP re-ask N300-B3 byte-identical", True, same)
    check("s2 RP re-ask N300-B3 input diffs excl. tenant id", [], ind)

    # --- report ------------------------------------------------------------------
    print(json.dumps({
        "checks_total": len(OK) + len(BAD),
        "checks_matching_T117": len(OK),
        "checks_MISMATCHING_T117": len(BAD),
        "MISMATCHES": [{"claim": l, "T117_says": c, "T159_observed": o} for l, c, o in BAD],
        "matched": [{"claim": l, "value": o} for l, c, o in OK],
    }, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
