#!/usr/bin/env python3
"""T41 edit batch 9 — M4, the fourth date-membership rule (T40)."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()
LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:260]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


# --- heading + lead-in -------------------------------------------------------
sub(
    "##### The THREE date-membership rules, stated together (P0-T37-1, added in revision 7)\n\n"
    "The oracle uses **three different** date-membership conventions on the disbursement date, "
    "and they do not agree with one another. Revisions 1–6 stated two of them in §4.3.1 and the "
    "third in §4.6, in a different context and never reconciled with §4.3.2's roll-forward — "
    "which is exactly how §4.3.2 step 4 came to contradict this subsection's own segmentation "
    "table. **A port that assumes one convention throughout is wrong somewhere.** All three are "
    "normative:",

    "##### The FOUR date-membership rules, stated together (P0-T37-1, added in revision 7; **M4 "
    "added in revision 8** from task T40's charge observations)\n\n"
    "The oracle uses **four different** date-membership conventions when it decides which "
    "repayment period a dated thing belongs to, and they do not all agree with one another. "
    "Revisions 1–6 stated two of them in §4.3.1 and the third in §4.6, in a different context and "
    "never reconciled with §4.3.2's roll-forward — which is exactly how §4.3.2 step 4 came to "
    "contradict this subsection's own segmentation table. The fourth governs **charges** and was "
    "unobservable until task T40 captured the first non-zero fee in this program's history. "
    "**A port that assumes one convention throughout is wrong somewhere.** All four are "
    "normative, and this table is the one place they are reconciled:",
)

# --- the M4 row --------------------------------------------------------------
sub(
    "| **M3** | `[FromDate, DueDate)` — from-inclusive, **DUE-EXCLUSIVE** | "
    "`ProgressiveLoanScheduleGenerator.java:307-308`, guard at `:309` | during which repayment "
    "period's iteration `processDisbursements` runs — so **in which period's iteration the "
    "disbursement is registered into the interest model** [`:351`] and the disbursement row is "
    "emitted [`:318`], which §4.6 already uses as its ordering window key |",

    "| **M3** | `[FromDate, DueDate)` — from-inclusive, **DUE-EXCLUSIVE** | "
    "`ProgressiveLoanScheduleGenerator.java:307-308`, guard at `:309` | during which repayment "
    "period's iteration `processDisbursements` runs — so **in which period's iteration the "
    "disbursement is registered into the interest model** [`:351`] and the disbursement row is "
    "emitted [`:318`], which §4.6 already uses as its ordering window key |\n"
    "| **M4** | `[FromDate, DueDate]` for the **FIRST** repayment period and `(FromDate, DueDate]` "
    "for every later one — **the same predicate function as M1**, but reached with a **different "
    "source for the \"is first\" flag** | `LoanCharge.java:371-373` → "
    "`LoanRepaymentScheduleProcessingWrapper.java:251-254`, flag supplied by "
    "`LoanScheduleParams.isFirstPeriod()` [`LoanScheduleParams.java:533-535`] at "
    "`ProgressiveLoanScheduleGenerator.java:374`, `:377` (main loop) and `:479`, `:483` "
    "(separated path) | which repayment row a **CHARGE** lands on — the `feeChargesDue` / "
    "`penaltyChargesDue` columns and `totalDueForPeriod`. **Not carried by this contract** "
    "(§4.5, §4.5.1); stated because a port that later admits charges must not reuse M1, M2 or M3 "
    "for them |",
)

# --- the "M1 and M3 disagree" paragraph: extend to M4 -----------------------
sub(
    "**M1 and M3 disagree on exactly one date: a disbursement dated on a repayment period's "
    "`DueDate`.** M1 puts it in period *j*; M3 puts it in period *j+1*. Both are right about "
    "their own question, and the disagreement is the whole of P0-T37-1.",

    "**M1 and M3 disagree on exactly one date: a disbursement dated on a repayment period's "
    "`DueDate`.** M1 puts it in period *j*; M3 puts it in period *j+1*. Both are right about "
    "their own question, and the disagreement is the whole of P0-T37-1.\n\n"
    "**M4 shares M1's interval shape and is still a different rule, because the input that "
    "selects the shape is different — and on one path it is STALE** (revision 8, re-derived by "
    "this task from the pinned checkout and corroborated by observation). M1 passes the "
    "repayment period's **own structural property**, `period.isFirstRepaymentPeriod()` "
    "[`ProgressiveLoanInterestScheduleModel.java:243`], which is `previous == null` "
    "[`RepaymentPeriod.java:449-451`] — true of the first period and of nothing else, always. "
    "M4 passes `LoanScheduleParams.isFirstPeriod()`, which is `1 == instalmentNumber` "
    "[`LoanScheduleParams.java:533-535`] — a **mutable running counter**. Inside the main "
    "schedule loop the counter is correct, because `applyChargesForCurrentPeriod` runs at "
    "[`ProgressiveLoanScheduleGenerator.java:140`] and `incrementInstalmentNumber()` only at "
    "[`:143`], so during period 1's iteration the flag is `true` and M4 coincides with M1. "
    "On the **separated** path it is not: `updatePeriodsWithCharges` runs at [`:154`], **after** "
    "the `for` loop at [`:116-145`] has incremented the counter once per period, so "
    "`isFirstPeriod()` is **false for every period including period 1** [`:479`, `:483`] and M4 "
    "degenerates to `(FromDate, DueDate]` everywhere. **That staleness is a money-losing defect "
    "in the reference oracle and it is OBSERVED** — §4.5.1, capture `FC-20`. "
    "**Which rule governs which field:** M1 the interest-period segmentation and the effective "
    "due date; M2 the related-period list and hence the level installment; M3 the disbursement "
    "row's emission, the interest model's registration and §4.6's ordering window key; M4 the "
    "fee and penalty columns. **They are not interchangeable and this table is the only place "
    "they may be read from.**",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
