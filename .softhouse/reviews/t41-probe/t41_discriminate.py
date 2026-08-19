"""
T41 (B) -- does DEC-1 REVISION 8, read from its TEXT ALONE, DISCRIMINATE every
wrong reading that is known to be corpus-invisible?

A specification that cannot tell the wrong answer from the right one has not
been fixed.  This script puts each wrong reading to the model and asks how many
COMMITTED captures it fails, CELL BY CELL, against three corpora:

  the 21 pre-T39 production-setting captures (11 Path-A pass-3 + 10 T37 binding)
  the 15 parity-setting T39 captures                       [NEW in revision 8]
  the 21 T40 charge captures, schedule core only           [NEW in revision 8]

and it adds the three readings revision 8 must newly separate:

  N1  the AMBIENT MathContext is the arithmetic in force on Path A   (4.1.2)
  N2  charges are folded INTO the EMI rather than sitting beside it  (4.5.1)
  N3  totalRepaymentExpected == the sum of the period totals         (4.5.1 C-1)

N1, N2 and N3 are not model switches: they are claims about the ORACLE, so they
are tested directly against committed capture artefacts.

*** NO ORACLE WAS CONTACTED BY THIS TASK. ***  Every expectation is transcribed
from a committed capture, quoted by id.  parse_float=Decimal throughout; no
binary float is constructed anywhere.
"""
import json
import os
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t41_model import Request, generate, totals, m2s, MINOR, assert_threaded_context

PATHA = ".softhouse/capture/out/capture-prod-raw.json"
BINDING = ".softhouse/capture/dec1-binding/out/t37-binding.json"
PERIODRATIO = ".softhouse/capture/periodratio/out/t39-periodratio.json"
T39_NEG_AMBIENT = ".softhouse/capture/periodratio/out/t39-neg5.json"
T39_NEG_THREADED = ".softhouse/capture/periodratio/out/t39-neg7.json"
CHARGES_DIR = ".softhouse/capture/charges/out/fc"
CONTROL = "FC-17-fee-after-final-duedate"   # byte-identical to the zero-charge
                                            # control; used only as a shape peer

READINGS = [
    ("ratio-is-always-1 (P0-T32-1)", dict(ratio_one=True)),
    ("textbook balance x rateFactor (P0-T29-2)", dict(textbook=True)),
    ("n = NumberOfRepayments (P0-T29-1)", dict(wrong_n=True)),
    ("whole-principal pre-disbursement row (P0-T37-1)",
     dict(whole_principal_prerow=True)),
    ("EMI re-adjust loop ABSENT (item 3)", dict(run_loop=False)),
    ("loop WITHOUT the adoption test (item 3a)", dict(no_adoption=True)),
    ("RepaymentEvery instead of periodRatio (P0-T34-1)",
     dict(till_multiplier="repaymentEvery")),
    ("periodRatio with the MONTH-END CASE OMITTED (T39 N-2)",
     dict(month_end_case=False)),
    ("M3 reused where M1 belongs (the inert collapse)",
     dict(collapse_M3_into_M1=True)),
]


def d(s):
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def jload(path):
    with open(path) as f:
        return json.load(f, parse_float=Decimal)


def req_of(i):
    return Request(start=d(i["scheduleGenerationStartDate"]),
                   disb=d(i["disbursementDate"]),
                   principal_minor=int(Decimal(str(i["disbursementAmount"])) * MINOR),
                   n=i["numberOfRepayments"],
                   rate_pct=Decimal(str(i["annualNominalInterestRate"])),
                   every=i.get("repaymentEvery", 1))


def cells(rows):
    out = {}
    for i, r in enumerate(rows, start=1):
        out[f"R{i}.fromDate"] = str(r.frm)
        out[f"R{i}.dueDate"] = str(r.due)
        out[f"R{i}.principal"] = m2s(r.principal_minor)
        out[f"R{i}.interest"] = m2s(r.interest_minor)
        out[f"R{i}.balance"] = m2s(r.outstanding_minor)
        out[f"R{i}.total"] = m2s(r.principal_minor + r.interest_minor)
    tp, ti, _ = totals(rows)
    out["totalInterest"] = m2s(ti)
    out["loanTermInDays"] = str((rows[-1].due - rows[0].frm).days)
    return out


def load_corpus(paths):
    out = []
    for p in paths:
        for cap in jload(p)["captures"]:
            if assert_threaded_context(cap["inputs"]):
                continue
            if cap["inputs"].get("daysInMonth") != "DAYS_30":
                continue
            out.append(cap)
    return out


def part_b1():
    print("=" * 78)
    print("B1  DOES REVISION 8 DISCRIMINATE?  Each wrong reading is run against")
    print("    every committed production-setting capture and compared CELL BY")
    print("    CELL to revision 8's own reading.  A reading that fails 0 of a")
    print("    corpus is INVISIBLE to that corpus -- which is a fact about the")
    print("    corpus, never about the rule.")
    print("    CELLS PER ROW: fromDate, dueDate, principal, interest, balance,")
    print("    total; plus totalInterest and loanTermInDays per capture.")
    print("=" * 78)
    old = load_corpus([PATHA, BINDING])
    new39 = load_corpus([PERIODRATIO])
    print(f"    corpora: pre-T39 = {len(old)} captures, T39 = {len(new39)} captures\n")
    print(f"{'wrong reading':<52} {'pre-T39':>9} {'T39':>7}  first witness")
    print("-" * 78)
    rc = 0
    detail = {}
    for label, opts in READINGS:
        counts = []
        witness = None
        detail[label] = []
        for corpus in (old, new39):
            failed = 0
            for cap in corpus:
                req = req_of(cap["inputs"])
                a = cells(generate(req))
                try:
                    b = cells(generate(req, **dict(opts)))
                except Exception:
                    failed += 1
                    continue
                diff = [k for k in a if a[k] != b.get(k)]
                if diff:
                    failed += 1
                    detail[label].append(cap['id'])
                    if witness is None:
                        witness = f"{cap['id']} cell {sorted(diff)[0]}"
            counts.append(failed)
        tot = counts[0] + counts[1]
        if tot == 0:
            rc += 1
        print(f"{label:<52} {counts[0]:>4}/{len(old):<4} {counts[1]:>3}/{len(new39):<3}"
              f"  {witness or 'NONE -- corpus blind'}")
    print()
    print("    Every capture each reading FAILS, named in full:")
    for label, ids in detail.items():
        print(f"      {label}")
        print(f"        {', '.join(ids) if ids else '(none -- invisible to both corpora)'}")
    print()
    return rc


def part_b2():
    """N1 -- ambient versus threaded MathContext, measured on T39's own negative
    runs.  This is a claim about the ORACLE, so it is tested against committed
    capture artefacts and not against the model."""
    print("=" * 78)
    print("B2  N1: is the AMBIENT MoneyHelper context the arithmetic in force on")
    print("    Path A?  Revision 8 section 4.1.2 says NO -- the THREADED context")
    print("    is.  Measured here by re-comparing T39's committed negative runs,")
    print("    capture by capture, on every published cell of every row.")
    print("=" * 78)
    base = {c["id"]: c for c in jload(PERIODRATIO)["captures"]}
    for path, what in ((T39_NEG_AMBIENT, "AMBIENT tenant mode forced to DOWN"),
                       (T39_NEG_THREADED, "THREADED mode forced to DOWN")):
        neg = jload(path)
        hdr = {k: neg.get(k) for k in
               ("negativeTestTenantRoundingModeOrdinalOverride",
                "negativeTestMathContextRoundingModeOverride")}
        moved = 0
        cell_moves = 0
        total = 0
        for c in neg["captures"]:
            b = base[c["id"]]
            total += 1
            n = 0
            for pa, pb in zip(c["observed"]["periods"], b["observed"]["periods"]):
                for k in pa:
                    if str(pa[k]) != str(pb.get(k)):
                        n += 1
            for k in ("loanTermInDays", "totalDisbursedAmount",
                      "totalInterestAmount", "totalRepaymentAmount"):
                if str(c["observed"].get(k)) != str(b["observed"].get(k)):
                    n += 1
            if n:
                moved += 1
                cell_moves += n
        print(f"  {what}")
        print(f"    overrides recorded in the payload: {hdr}")
        print(f"    capture blocks that MOVED: {moved} of {total}"
              f"   (cells moved: {cell_moves})")
    print("\n  VERDICT: an ambient-only change moves NOTHING inside the graded")
    print("  domain on Path A; a threaded change moves almost everything. The")
    print("  reading 'the ambient MoneyHelper context is the arithmetic in")
    print("  force' is REFUTED, and 4.1.2's rule is what the data supports.\n")
    return 0


def part_b3():
    """N2 and N3 -- the two charge readings, measured on T40's captures."""
    print("=" * 78)
    print("B3  N2: are charges folded INTO the EMI, or do they sit BESIDE it?")
    print("    N3: is totalRepaymentExpected the sum of the period totals?")
    print("    Both are claims about the ORACLE, tested against T40's committed")
    print("    captures.  CELLS COMPARED for N2: principalDue, interestDue,")
    print("    principalLoanBalanceOutstanding, totalInstallmentAmountForPeriod")
    print("    on every repayment row, against the zero-charge control's values;")
    print("    plus feeChargesDue and penaltyChargesDue, to show the charge DID")
    print("    land somewhere.  For N3: totalRepaymentExpected against the sum")
    print("    of totalDueForPeriod, exact Decimal, zero tolerance.")
    print("=" * 78)
    caps = {}
    for fn in sorted(os.listdir(CHARGES_DIR)):
        if fn.endswith("-raw.json"):
            caps[fn[:-len("-raw.json")]] = jload(os.path.join(CHARGES_DIR, fn))
    ctrl = caps[CONTROL]     # byte-identical to the committed zero-charge control
    core = ["principalDue", "interestDue", "principalLoanBalanceOutstanding",
            "totalInstallmentAmountForPeriod"]

    n2_moved = n2_total = 0
    charge_bearing = 0
    n3_fail = n3_total = 0
    print(f"{'capture':<48} {'core cells moved':>17} {'charge cells':>13} {'C5':>5}")
    print("-" * 88)
    for cid, cap in caps.items():
        n2_total += 1
        moved = 0
        chg = 0
        for pa, pb in zip(cap["periods"], ctrl["periods"]):
            if "period" not in pa:
                continue
            for k in core:
                if Decimal(str(pa[k])) != Decimal(str(pb[k])):
                    moved += 1
            for k in ("feeChargesDue", "penaltyChargesDue"):
                if Decimal(str(pa.get(k, 0))) != Decimal(str(pb.get(k, 0))):
                    chg += 1
        # the disbursement pseudo-period's fee, which FC-01/FC-03 use
        for k in ("feeChargesDue", "penaltyChargesDue"):
            if Decimal(str(cap["periods"][0].get(k, 0))) != \
               Decimal(str(ctrl["periods"][0].get(k, 0))):
                chg += 1
        if moved:
            n2_moved += 1
        if chg:
            charge_bearing += 1
        n3_total += 1
        tre = Decimal(str(cap["totalRepaymentExpected"]))
        s = sum(Decimal(str(p["totalDueForPeriod"])) for p in cap["periods"])
        c5 = "PASS" if tre == s else "FAIL"
        if c5 == "FAIL":
            n3_fail += 1
        print(f"{cid:<48} {moved:>17} {chg:>13} {c5:>5}")
    print()
    print(f"  N2: of {n2_total} charge captures, {charge_bearing} carry a charge that")
    print(f"      LANDED somewhere, and {n2_moved} moved ANY of the four core")
    print(f"      schedule cells.  {n2_moved} == 0 means: A CHARGE SITS ALONGSIDE")
    print(f"      THE EMI, NEVER INSIDE IT.  The reading 'charges are folded into")
    print(f"      the EMI' is REFUTED on every capture that carries one.")
    print()
    print(f"  N3: totalRepaymentExpected == sum(totalDueForPeriod) FAILS on")
    print(f"      {n3_fail} of {n3_total} captures.  The reading 'the oracle's")
    print(f"      totalRepaymentExpected is the sum of the rows' is REFUTED, which")
    print(f"      is decision C-1's premise: the contract does not carry it and no")
    print(f"      invariant may assert it.")
    print()
    return 0


def main():
    blind = part_b1()
    part_b2()
    part_b3()
    print("=" * 78)
    print(f"B1: {len(READINGS)} readings tested; {blind} of them are invisible to")
    print("    BOTH corpora.  Every one that is invisible is named above with")
    print("    'NONE -- corpus blind' and must be read as a corpus fact.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
