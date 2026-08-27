"""
T38 pass 2 -- an EIGHTH candidate wrong reading, put to the same test.

Revision 7 states THREE date-membership rules (DEC-1 section 4.3.2) and says a
port that assumes one convention throughout "is wrong somewhere".  The probe
suite committed by pass 1 discriminates the reading that uses M1 where M3
belongs (the whole-principal pre-disbursement row).  It does NOT test the
opposite collapse: a port that uses M3 -- from-inclusive, DUE-EXCLUSIVE -- for
the INTEREST MODEL's balance-change attribution too, i.e. where revision 7 says
M1 applies.

That reading is what an implementer gets if they read only section 4.6's
ordering window key (which is M3, and is the ONLY place revisions 1-6 stated the
rule) and reuse it for section 4.3.2's segmentation.  It is exactly the mistake
revision 7's "M1 and M3 disagree on exactly one date" sentence exists to
prevent, so the document's claim deserves a measurement rather than an
assertion.

Method: the pass-1 from-text model, with ONE marked edit -- `segment()` and
`first_related()` select the affected repayment period with M3 instead of M1.
Compared cell by cell (from date, due date, principal, interest, outstanding
balance, row total, plus loan term and total interest) against:

  (1) the 21 committed captures at the production MathContext, and
  (2) a sweep of in-graded-domain shapes whose disbursement is dated ON a
      repayment period's DueDate -- the one date on which M1 and M3 disagree.

Exact Decimal at explicit contexts and integer minor units; no float anywhere on
a money path.  NO ORACLE WAS CONTACTED: every expectation is transcribed from a
capture file already committed on main.
"""
import json
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import t38_model as M
from t38_model import Request, MINOR, m2s

PATHA = ".softhouse/capture/out/capture-prod-raw.json"
BINDING = ".softhouse/capture/dec1-binding/out/t37-binding.json"


# ---------------------------------------------------------------- the edit ---
def segment_m3(req: Request):
    """Revision 7's segment(), with M1 replaced by M3 for the attribution of the
    balance change.  This is the WRONG reading under test; everything else is
    byte-identical to t38_model.segment()."""
    bounds = M.repayment_boundaries(req.start, req.disb, req.n, req.every)
    periods = [M.RepaymentPeriod(f, d) for f, d in bounds]
    for p in periods:
        p.interest_periods = [M.InterestPeriod(p.frm, p.due, p.frm, p.due)]

    D = req.disb
    target = None
    for idx in range(len(periods)):
        if M.membership_attachment(D, periods, idx):   # <-- M3, not M1
            target = idx
            break
    if target is None:
        raise ValueError("disbursement outside every half-open window")

    p = periods[target]
    if D == p.frm:
        p.interest_periods = [
            M.InterestPeriod(p.frm, p.frm, p.frm, p.due, disbursed_minor=req.principal_minor),
            M.InterestPeriod(p.frm, p.due, p.frm, p.due),
        ]
    elif D == p.due:
        p.interest_periods[0].disbursed_minor = req.principal_minor
    else:
        p.interest_periods = [
            M.InterestPeriod(p.frm, D, p.frm, p.due, disbursed_minor=req.principal_minor),
            M.InterestPeriod(D, p.due, p.frm, p.due),
        ]
    return periods, target


def cells(periods):
    out = {}
    for i, p in enumerate(periods, 1):
        out[f"R{i}.from"] = p.frm.isoformat()
        out[f"R{i}.due"] = p.due.isoformat()
        out[f"R{i}.principal"] = p.principal_minor
        out[f"R{i}.interest"] = p.interest_minor
        out[f"R{i}.balance"] = p.outstanding_minor
        out[f"R{i}.total"] = p.principal_minor + p.interest_minor
    out["totalInterest"] = sum(p.interest_minor for p in periods)
    return out


def run_normative(req):
    """t38_model's pipeline, inlined so the M3 variant differs in ONE line."""
    periods, target = M.segment(req)
    attach = M.attachment_index(req, periods)
    first_rel = M.first_related(req, periods, target)
    M.apply_rate_factors(req, periods)
    emi = M.level_installment(periods, first_rel, req.principal_minor)
    M.split_rows(req, periods, first_rel, attach, emi)
    M.apply_residual_and_recompute(req, periods, first_rel, attach)
    return periods


def run_m3(req):
    """The same, with M1 replaced by M3 in the interest model's attribution."""
    periods, target = segment_m3(req)
    attach = M.attachment_index(req, periods)
    if periods[target].due == req.disb:
        eff = periods[target + 1].due if target + 1 < len(periods) else periods[target].due
    else:
        eff = periods[target].due
    first_rel = next(i for i, p in enumerate(periods) if not (p.due < eff))
    M.apply_rate_factors(req, periods)
    emi = M.level_installment(periods, first_rel, req.principal_minor)
    M.split_rows(req, periods, first_rel, attach, emi)
    M.apply_residual_and_recompute(req, periods, first_rel, attach)
    return periods


def req_from_capture(cap):
    i = cap["inputs"]
    if i["mathContextPrecision"] != 19:
        return None
    if i["daysInMonth"] != "DAYS_30" or i["daysInYear"] != "DAYS_360":
        return None
    return Request(start=date.fromisoformat(i["scheduleGenerationStartDate"]),
                   disb=date.fromisoformat(i["disbursementDate"]),
                   principal_minor=int(Decimal(i["disbursementAmount"]) * MINOR),
                   n=i["numberOfRepayments"],
                   rate_pct=Decimal(i["annualNominalInterestRate"]),
                   every=i.get("repaymentEvery", i.get("repaymentFrequency", 1)))


def main() -> int:
    print("=" * 78)
    print("T38 pass 2 -- does collapsing M1 into M3 move money?")
    print("  normative : M1 for the interest model's balance-change attribution")
    print("  wrong     : M3 (from-inclusive, DUE-EXCLUSIVE) used there too")
    print("  NO ORACLE CONTACTED.  Every shape is either a committed capture's")
    print("  input or a synthetic in-graded-domain request; no expectation is new.")
    print("=" * 78)

    print("")
    print("-- (1) the committed captures at (19, HALF_UP) --------------------")
    same = diverged = skipped = 0
    for path in (PATHA, BINDING):
        for cap in json.load(open(path))["captures"]:
            req = req_from_capture(cap)
            if req is None:
                skipped += 1
                continue
            a = cells(run_normative(req))
            b = cells(run_m3(req))
            bad = [k for k in a if a[k] != b[k]]
            if bad:
                diverged += 1
                print(f"  {cap['id']:<14} DIVERGES on {len(bad)} cells: {bad[:4]}")
            else:
                same += 1
    print("")
    print(f"  identical on {same} captures, diverges on {diverged}, skipped {skipped}")

    print("")
    print("-- (2) sweep: disbursement dated ON a repayment period's DueDate ---")
    print("     (the ONE date on which M1 and M3 disagree)")
    n_div = n_tot = 0
    worst = None
    for principal in (100_00, 1_200_000_00, 10_548_069_00, 50_000_000_00):
        for n in (6, 12, 36):
            for rate in ("7.0", "16.8", "21.6"):
                for j in (1, 2, 3):
                    if j >= n:
                        continue
                    start = date(2024, 1, 1)
                    bounds = M.repayment_boundaries(start, start, n, 1)
                    disb = bounds[j - 1][1]
                    req = Request(start=start, disb=disb, principal_minor=principal,
                                  n=n, rate_pct=Decimal(rate), every=1)
                    a = cells(run_normative(req))
                    b = cells(run_m3(req))
                    n_tot += 1
                    bad = [k for k in a if a[k] != b[k]]
                    if bad:
                        n_div += 1
                        gap = abs(a["totalInterest"] - b["totalInterest"])
                        if worst is None or gap > worst[0]:
                            worst = (gap, principal, n, rate, disb, len(bad))
    print(f"  {n_div} of {n_tot} due-date-disbursement shapes return different money")
    if worst:
        gap, principal, n, rate, disb, ncells = worst
        print(f"  worst total-interest gap: MNT {m2s(gap)} "
              f"({m2s(principal)} / {n} x {rate}%, disbursement {disb}, {ncells} cells)")

    print("")
    print("=" * 78)
    if n_div == 0 and diverged == 0:
        print("RESULT: the M1->M3 collapse is INERT on every shape tested. Revision 7's")
        print("        M1/M3 distinction is correct AND, on the SEGMENTATION question,")
        print("        unobservable here; the money consequence of confusing the two")
        print("        lives in the EMITTED balance (step 4b), which the pass-1 probe")
        print("        already discriminates on 3 of 21 captures.")
    else:
        print("RESULT: the M1->M3 collapse MOVES MONEY -- see the counts above.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
