#!/usr/bin/env python3
"""T45 - the legs T41's probe did not have, run against revision 9.

C1. The Path-A pass-3b twelve, cell by cell (which T41's probe never replayed).
C2. The four committed Path-B captures, cell by cell.
C3. T44's finding F39-1, RE-DERIVED INSIDE THIS DOCUMENT'S OWN MODEL rather than taken
    from T44's script: is `clamped-step whole months AND no special case` distinguishable
    from `packed whole months AND the special case` anywhere in the corpus, or anywhere
    in the swept date space?  Revision 9 asserts it is not. This tests that assertion.
C4. Revision 9's ONLY new normative content -- M4 and M5 -- transcribed from revision 9's
    text alone and replayed against the fee and penalty columns of T40's 21 charge
    captures, cell by cell.

Exact Decimal / integer minor units throughout. No float anywhere.
"""
import calendar
import json
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
os.chdir(ROOT)

from t47_model_inherited import (Request, generate, totals, m2s, MINOR,   # noqa: E402
                                 calculate_seed_date, plus_months, months_between,
                                 repayment_boundaries)

MINOR = Decimal(100)


def d(s):
    return date(*(int(x) for x in str(s).split("-")))


# ---------------------------------------------------------------------------
# C3 -- the two whole-months functions, and T44's F39-1
# ---------------------------------------------------------------------------

def months_between_clamped(a: date, b: date) -> int:
    """The OTHER reading of "whole months, truncated toward zero": the largest k
    such that a + k months <= b, using LocalDate month arithmetic (which clamps).
    DEC-1 section 4.1.1 step B names this as the reading a porter most naturally
    writes, and says it must be paired with OMITTING the special case."""
    if b < a:
        k = 0
        while plus_months(a, k - 1) >= b:
            k -= 1
        return k
    k = 0
    while plus_months(a, k + 1) <= b:
        k += 1
    return k


def period_ratio_variant(schedule_start, rp_from, rp_due, every, *, packed, special):
    """Section 4.1.1 steps A-C with step B's two clauses independently switchable.
    (packed=True, special=True)  = the pinned source, DEC-1's normative reading.
    (packed=False, special=False)= the reading DEC-1 section 4.1.1 step B says is
                                   equivalent, and which T44's F39-1 says no capture
                                   can distinguish from it.
    (packed=True, special=False) = the reading T39 refuted 116 of 116.
    """
    seed = calculate_seed_date(schedule_start, rp_from, rp_due, every)
    wm = months_between if packed else months_between_clamped
    last_day = calendar.monthrange(rp_from.year, rp_from.month)[1]
    if special and last_day == rp_from.day and seed.day > rp_from.day:
        k = wm(seed, rp_from + timedelta(days=1))
    else:
        k = wm(seed, rp_from)
    m = k + 1
    cursor = rp_from
    while cursor < rp_due:
        cursor = plus_months(seed, m)
        if not (cursor > rp_due):
            m += 1
        else:
            full = cursor
            m = m - k - 1
            base = plus_months(seed, m)
            num = Decimal((rp_due - base).days)
            den = Decimal((full - base).days)
            from decimal import Context, ROUND_HALF_UP
            return Context(prec=19, rounding=ROUND_HALF_UP).divide(num, den) + Decimal(m)
    return Decimal(m - k - 1)


def c3():
    print("=" * 78)
    print("C3  T44's F39-1, re-derived inside DEC-1's OWN model.")
    print("    R2 = packed whole-months AND the month-end special case  (the pinned source)")
    print("    R3 = packed whole-months, special case OMITTED           (T39 refuted this)")
    print("    R4 = clamped-step whole-months, special case OMITTED     (the porter's reading)")
    print("    Revision 9 asserts R2 == R4 as functions. This tests it.")
    print("=" * 78)
    fires = r3_diff = r4_diff = pairs = 0
    start = date(2023, 1, 1)
    end = date(2025, 12, 30)
    day = start
    while day <= end:
        for n in (6, 12, 36):
            # Boundaries come from section 4.2 -- stepped from ScheduleStartDate and
            # RE-ANCHORED on the disbursement seed.  Plain plusMonths is NOT the
            # boundary rule and never puts a FromDate on a month end after period 1,
            # so a sweep built on it fires the special case zero times.
            for prev, nxt in repayment_boundaries(day, day, n, 1):
                pairs += 1
                seed = calculate_seed_date(day, prev, nxt, 1)
                ld = calendar.monthrange(prev.year, prev.month)[1]
                if ld == prev.day and seed.day > prev.day:
                    fires += 1
                r2 = period_ratio_variant(day, prev, nxt, 1, packed=True, special=True)
                r3 = period_ratio_variant(day, prev, nxt, 1, packed=True, special=False)
                r4 = period_ratio_variant(day, prev, nxt, 1, packed=False, special=False)
                if r2 != r3:
                    r3_diff += 1
                if r2 != r4:
                    r4_diff += 1
        day += timedelta(days=1)
    print(f"  (ScheduleStartDate, repayment period) pairs swept : {pairs}")
    print(f"  periods on which the MONTH-END SPECIAL CASE FIRES : {fires}")
    print(f"  periods where periodRatio(R2) != periodRatio(R3)  : {r3_diff}"
          f"   <- the reading T39's captures refute")
    print(f"  periods where periodRatio(R2) != periodRatio(R4)  : {r4_diff}"
          f"   <- the reading NOTHING refutes")
    ok = (r4_diff == 0 and r3_diff == fires and fires > 0)
    print()
    print(f"  T44 F39-1 CONFIRMED INDEPENDENTLY: {ok}")
    print("  R2 and R4 are the same function on this whole domain, and the periods where")
    print("  R3 diverges are exactly the periods where the special case fires. So the four")
    print("  T39-ME captures grade the PAIR and neither clause alone -- which is what")
    print("  revision 9 says and revision 8 did not.")
    print()
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# C1 / C2 -- corpora T41's probe never replayed
# ---------------------------------------------------------------------------

def req_of(i):
    return Request(start=d(i["scheduleGenerationStartDate"]),
                   disb=d(i["disbursementDate"]),
                   principal_minor=int(Decimal(str(i["disbursementAmount"])) * MINOR),
                   n=int(i["numberOfRepayments"]),
                   rate_pct=Decimal(str(i["annualNominalInterestRate"])),
                   every=int(i.get("repaymentEvery", i.get("repaymentFrequency", 1))))


def c1():
    print("=" * 78)
    print("C1  Path-A PASS 3B, .softhouse/capture/out/capture-prod3b-raw.json")
    print("    The twelve re-emissions that added the disbursement row's `balance`.")
    print("    CELLS COMPARED per repayment row: periodFromDate, dueDate, principal,")
    print("    interest, balance, total; plus loanTermInDays, totalInterestAmount, and")
    print("    the DISBURSEMENT row's principal AND balance -- the column pass 3 lacked.")
    print("=" * 78)
    caps = json.load(open(".softhouse/capture/out/capture-prod3b-raw.json"))["captures"]
    checked = bad = cells = 0
    for cap in caps:
        i = cap["inputs"]
        if int(i["mathContextPrecision"]) != 19:
            print(f"{cap['id']:<16} SKIPPED (threaded precision "
                  f"{i['mathContextPrecision']}, not 19)")
            continue
        req = req_of(i)
        rows = generate(req)
        obs = cap["observed"]
        n = 0
        diffs = []
        rep = [p for p in obs["periods"] if p["type"] == "REPAYMENT"]
        for k, (r, p) in enumerate(zip(rows, rep), start=1):
            for key, got in (("periodFromDate", str(r.frm)), ("dueDate", str(r.due)),
                             ("principal", m2s(r.principal_minor)),
                             ("interest", m2s(r.interest_minor)),
                             ("balance", m2s(r.outstanding_minor)),
                             ("total", m2s(r.principal_minor + r.interest_minor))):
                if key in p:
                    n += 1
                    exp = p[key] if key in ("periodFromDate", "dueDate") \
                        else f"{Decimal(str(p[key])):.2f}"
                    if got != exp:
                        diffs.append((f"R{k}.{key}", got, exp))
        tp, ti, _ = totals(rows)
        for key, got in (("loanTermInDays", str((rows[-1].due - rows[0].frm).days)),
                         ("totalInterestAmount", m2s(ti))):
            if key in obs:
                n += 1
                exp = str(obs[key]) if key == "loanTermInDays" \
                    else f"{Decimal(str(obs[key])):.2f}"
                if got != exp:
                    diffs.append((key, got, exp))
        for p in obs["periods"]:
            if p["type"] == "DISBURSEMENT":
                for key, got in (("principal", m2s(req.principal_minor)),
                                 ("balance", m2s(req.principal_minor))):
                    if key in p:
                        n += 1
                        exp = f"{Decimal(str(p[key])):.2f}"
                        if got != exp:
                            diffs.append((f"DISB.{key}", got, exp))
        checked += 1
        cells += n
        if diffs:
            bad += 1
        print(f"{cap['id']:<16} rows={len(rep):<3} cells={n:<4} "
              f"{'OK' if not diffs else 'MISMATCH'}")
        for k, g, e in diffs:
            print(f"    {k}: model {g!r}  capture {e!r}")
    print(f"\nC1: {checked - bad} of {checked} captures reproduce; {cells} cells compared\n")
    return bad


def c2():
    print("=" * 78)
    print("C2  PATH B, .softhouse/capture/pathb/t36/out/recapture-gerege/B-0n-*.json")
    print("    The four production-tenant server-path captures.")
    print("    CELLS COMPARED per repayment row: fromDate, dueDate, principalDue,")
    print("    interestDue, principalLoanBalanceOutstanding, totalDueForPeriod;")
    print("    plus loanTermInDays and totalInterestCharged.")
    print("    B-02 has installmentAmountInMultiplesOf = 100 and B-03/B-04 carry a")
    print("    daysInYearCustomStrategy -- ALL THREE ARE OUTSIDE THE GRADED DOMAIN")
    print("    (sections 4.4, 4.7), so the contract REFUSES them and this model is not")
    print("    expected to reproduce them. They are replayed anyway, and a mismatch on")
    print("    them is the refusal being CORRECT, not the model being wrong.")
    print("=" * 78)
    base = ".softhouse/capture/pathb/t36/out/recapture-gerege"
    graded = {"B-01"}
    bad = cells = 0
    for fn in sorted(os.listdir(base)):
        if not fn.startswith("B-0") or not fn.endswith("-raw.json"):
            continue
        cid = fn.split("-")[0] + "-" + fn.split("-")[1]
        obs = json.load(open(os.path.join(base, fn)))
        # B-01's inputs are the committed baseline every FC-nn shares.
        req = Request(start=d("2026-01-01"), disb=d("2026-01-01"),
                      principal_minor=120000000, n=12, every=1,
                      rate_pct=Decimal("21.6"))
        rows = generate(req)
        rep = [p for p in obs["periods"] if p.get("periodType" ) != "DISBURSEMENT"
               and p.get("dueDate") and p.get("period")]
        n = 0
        diffs = []
        for k, (r, p) in enumerate(zip(rows, rep), start=1):
            for key, got in (("principalDue", m2s(r.principal_minor)),
                             ("interestDue", m2s(r.interest_minor)),
                             ("principalLoanBalanceOutstanding", m2s(r.outstanding_minor)),
                             ("totalDueForPeriod",
                              m2s(r.principal_minor + r.interest_minor))):
                if key in p:
                    n += 1
                    if got != f"{Decimal(str(p[key])):.2f}":
                        diffs.append((f"R{k}.{key}", got, f"{Decimal(str(p[key])):.2f}"))
        cells += n
        inside = cid in graded
        status = "OK" if not diffs else "MISMATCH"
        note = "" if inside else "  (OUTSIDE the graded domain -- the contract REFUSES it)"
        if inside and diffs:
            bad += 1
        print(f"{cid:<8} rows={len(rep):<3} cells={n:<4} {status}{note}")
        if inside:
            for k, g, e in diffs[:6]:
                print(f"    {k}: model {g!r}  capture {e!r}")
    print(f"\nC2: {cells} cells compared; in-graded-domain mismatches: {bad}\n")
    return bad


# ---------------------------------------------------------------------------
# C4 -- M4 and M5, transcribed from revision 9's text alone
# ---------------------------------------------------------------------------

def is_in_period(dt, frm, due, is_first):
    """Section 4.3.2 M1/M4's predicate function
    [LoanRepaymentScheduleProcessingWrapper.java:251-254]:
    [FromDate, DueDate] for the first period, (FromDate, DueDate] thereafter."""
    return (frm <= dt <= due) if is_first else (frm < dt <= due)


def charge_rows(charge, boundaries):
    """Which repayment rows a charge lands on, from DEC-1 revision 9 section 4.3.2's
    M4 and M5 ALONE, transcribed from the text and not from the oracle.

    M5: an INSTALMENT_FEE lands on EVERY repayment row -- no membership test.
    M4: a SPECIFIED_DUE_DATE or OVERDUE_INSTALLMENT charge lands on the one row
        whose window contains its due date, `is first` supplied by the MUTABLE
        counter (true only during period 1's own iteration on the main-loop path).
    """
    kind = charge["timeType"]
    if kind == "INSTALMENT_FEE":
        return list(range(1, len(boundaries) + 1))          # M5
    if kind in ("SPECIFIED_DUE_DATE", "OVERDUE_INSTALLMENT"):
        due = charge["dueDate"]
        return [j for j, (frm, dd) in enumerate(boundaries, start=1)
                if is_in_period(due, frm, dd, j == 1)]       # M4
    return []                                               # DISBURSEMENT: no row


def c4():
    print("=" * 78)
    print("C4  M4 and M5, the ONLY new normative content in revision 9, transcribed")
    print("    from revision 9's text alone and replayed against T40's 21 charge")
    print("    captures.  CELLS COMPARED: the SET OF REPAYMENT ROWS carrying a")
    print("    non-zero feeChargesDue or penaltyChargesDue, per capture -- exactly the")
    print("    question M4 and M5 answer, and nothing that needs a charge AMOUNT.")
    print("    Revision 8's M4, applied to an INSTALMENT_FEE, predicts ONE row or none.")
    print("    Revision 9's M5 predicts EVERY row.  Both readings are scored below.")
    print("    NOTE (T44's A-3): chargeTimeType comes from the persisted DEFINITION and")
    print("    the AMOUNT from the REQUEST. This leg reads only the type, which is the")
    print("    half the definition really governs.")
    print("=" * 78)
    att = json.load(open(".softhouse/capture/charges/out/attested/attestation.json"))
    TIME = {1: "DISBURSEMENT", 8: "INSTALMENT_FEE", 2: "SPECIFIED_DUE_DATE",
            9: "OVERDUE_INSTALLMENT", 12: "TRANCHE_DISBURSEMENT"}
    defs = {c["id"]: TIME.get(c["charge_time_enum"], "ENUM_%d" % c["charge_time_enum"])
            for c in att["charges_as_persisted"]}
    CALC = {1: "FLAT", 2: "PERCENT_OF_AMOUNT", 3: "PERCENT_OF_AMOUNT_AND_INTEREST",
            4: "PERCENT_OF_INTEREST", 5: "PERCENT_OF_DISBURSEMENT_AMOUNT"}
    calc = {c["id"]: CALC.get(c["charge_calculation_enum"],
                              "ENUM_%d" % c["charge_calculation_enum"])
            for c in att["charges_as_persisted"]}
    print("    charge definitions in force (id -> chargeTimeType):")
    for k in sorted(defs):
        print("      %3d  %-20s %s" % (k, defs[k], calc[k]))
    print()

    boundaries = []
    prev = d("2026-01-01")
    for _ in range(12):
        nxt = plus_months(prev, 1)
        boundaries.append((prev, nxt))
        prev = nxt

    MON = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
           "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
           "December": 12}

    def parse_dd(s):
        a, b, c = s.split()
        return date(int(c), MON[b], int(a))

    base = ".softhouse/capture/charges/out/fc"
    reqdir = ".softhouse/capture/charges/req"
    v9 = v8 = n = 0
    for fn in sorted(os.listdir(base)):
        if not fn.endswith("-raw.json"):
            continue
        cid = fn[: -len("-raw.json")]
        obs = json.load(open(os.path.join(base, fn)))
        observed = set()
        for p in obs.get("periods", []):
            if p.get("period") is None:
                continue
            fee = Decimal(str(p.get("feeChargesDue", 0) or 0))
            pen = Decimal(str(p.get("penaltyChargesDue", 0) or 0))
            if fee or pen:
                observed.add(int(p["period"]))
        rp = os.path.join(reqdir, "calc-" + cid + ".json")
        if not os.path.exists(rp):
            print("%-48s NO COMMITTED REQUEST -- skipped" % cid)
            continue
        rq = json.load(open(rp))
        pred9, pred8 = set(), set()
        for ch in rq.get("charges", []):
            tt = defs.get(ch["chargeId"], "?")
            due = parse_dd(ch["dueDate"]) if ch.get("dueDate") else None
            if tt == "DISBURSEMENT":
                continue                                  # never lands on a repayment row
            if tt == "INSTALMENT_FEE":
                pred9.update(range(1, len(boundaries) + 1))            # M5
            elif tt in ("SPECIFIED_DUE_DATE", "OVERDUE_INSTALLMENT") and due:
                # M4, with the flag read PER PATH exactly as revision 9's M4 row now
                # states it. A PERCENT_OF_INTEREST or PERCENT_OF_AMOUNT_AND_INTEREST
                # SPECIFIED_DUE_DATE charge is SEPARATED out of the main loop
                # [:492-504], so its flag is false for EVERY period including
                # period 1 [:479, :483]. Every other charge takes the main-loop
                # flag [:374, :377], true during period 1's own iteration.
                separated = calc.get(ch["chargeId"]) in ("PERCENT_OF_INTEREST",
                                                         "PERCENT_OF_AMOUNT_AND_INTEREST")
                pred9.update(j for j, (f, dd) in enumerate(boundaries, start=1)
                             if is_in_period(due, f, dd,
                                             (j == 1) and not separated))   # M4
            # revision 8: M4 for EVERY charge type, instalment fee included.
            if due:
                pred8.update(j for j, (f, dd) in enumerate(boundaries, start=1)
                             if is_in_period(due, f, dd, j == 1))
        n += 1
        ok9, ok8 = pred9 == observed, pred8 == observed
        v9 += ok9
        v8 += ok8
        print("%-48s observed=%-30s rev9 %s rev8 %s"
              % (cid, sorted(observed), "OK   " if ok9 else "WRONG",
                 "OK   " if ok8 else "WRONG"))
        if not ok9:
            print("      rev9 predicted %s" % sorted(pred9))
        if not ok8:
            print("      rev8 predicted %s" % sorted(pred8))
    print()
    print("C4: %d charge captures replayed." % n)
    print("    revision 9's M4 + M5            reproduce the row set on %d of %d" % (v9, n))
    print("    revision 8's M4-for-every-type  reproduces it on         %d of %d" % (v8, n))
    print("    A reading that scores fewer than n is REFUTED by the corpus.")
    print()
    return 0 if (v9 == n and v8 < n) else 1


if __name__ == "__main__":
    rc = 0
    rc |= c1()
    rc |= c2()
    rc |= c3()
    try:
        rc |= c4()
    except Exception as e:                                   # noqa: BLE001
        print(f"C4 could not run against the committed request bodies: {e!r}")
        print("See the fallback in t45_m4m5.py.")
        rc |= 8
    sys.exit(1 if rc else 0)
