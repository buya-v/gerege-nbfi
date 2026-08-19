#!/usr/bin/env python3
"""T41 — contract.go edits, batch 2: M4, Period doc totalRepaymentExpected, ungraded list."""
import io
import sys

P = "nexus/internal/apps/loanschedule/contract/contract.go"
s = io.open(P, encoding="utf-8").read()
LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:260]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


sub(
    """// ## The THREE date-membership rules (normative; revision 7, P0-T37-1)
//
// The reference oracle uses THREE different membership conventions on the
// disbursement date, and they do not agree. A port that assumes one convention
// throughout is wrong somewhere.
//""",
    """// ## The FOUR date-membership rules (normative; revision 7, P0-T37-1; M4 added
// in revision 8 from task T40's charge observations)
//
// The reference oracle uses FOUR different membership conventions when it
// decides which repayment period a dated thing belongs to, and they do not all
// agree. A port that assumes one convention throughout is wrong somewhere.
//""",
)

sub(
    """//	M3  [FromDate, DueDate) — from-inclusive, DUE-EXCLUSIVE.
//	    (ProgressiveLoanScheduleGenerator.java:307-308, guard at :309)
//	    Decides: during which period's iteration processDisbursements runs, so
//	    in which period's iteration the disbursement is REGISTERED into the
//	    interest model (:351) and the disbursement row EMITTED (:318). It is
//	    also the ordering window key (see the Kind / ordering doc).
//""",
    """//	M3  [FromDate, DueDate) — from-inclusive, DUE-EXCLUSIVE.
//	    (ProgressiveLoanScheduleGenerator.java:307-308, guard at :309)
//	    Decides: during which period's iteration processDisbursements runs, so
//	    in which period's iteration the disbursement is REGISTERED into the
//	    interest model (:351) and the disbursement row EMITTED (:318). It is
//	    also the ordering window key (see the Kind / ordering doc).
//	M4  [FromDate, DueDate] for the FIRST repayment period and
//	    (FromDate, DueDate] for every later one — THE SAME PREDICATE FUNCTION
//	    AS M1 (LoanRepaymentScheduleProcessingWrapper.java:251-254), reached
//	    through LoanCharge.isDueInPeriod (LoanCharge.java:371-373,
//	    ProgressiveLoanScheduleGenerator.java:400-403).
//	    Decides: which repayment row a CHARGE lands on — the fee and penalty
//	    columns and totalDueForPeriod.
//	    NOT CARRIED BY THIS CONTRACT: GenerateRequest has no charge field and
//	    Period has no fee or penalty. M4 is stated so that a port which later
//	    admits charges does not reuse M1, M2 or M3 for them.
//
// M4 IS A DIFFERENT RULE FROM M1 EVEN THOUGH IT SHARES M1'S INTERVAL SHAPE,
// because the input that SELECTS the shape is different — and on one path it is
// STALE. M1 passes the repayment period's own structural property,
// period.isFirstRepaymentPeriod() (ProgressiveLoanInterestScheduleModel.java:243),
// which is `previous == null` (RepaymentPeriod.java:449-451) — true of the first
// period and nothing else, always. M4 passes LoanScheduleParams.isFirstPeriod(),
// which is `1 == instalmentNumber` (LoanScheduleParams.java:533-535) — a MUTABLE
// RUNNING COUNTER. Inside the main schedule loop it is correct, because
// applyChargesForCurrentPeriod runs at ProgressiveLoanScheduleGenerator.java:140
// and incrementInstalmentNumber() only at :143. On the SEPARATED charge path it
// is not: updatePeriodsWithCharges runs at :154, after the loop at :116-145 has
// incremented the counter once per period, so isFirstPeriod() is FALSE FOR EVERY
// PERIOD INCLUDING PERIOD 1 (:479, :483) and M4 degenerates to
// (FromDate, DueDate] everywhere. That staleness silently loses a charge dated
// on the first period's FromDate — OBSERVED, DEC-1 section 4.5.1 decision C-2b,
// capture FC-20 byte-identical to the zero-charge control while capture FC-11 (a
// FLAT charge, same date) pays 9,000.00.
//
// WHICH RULE GOVERNS WHICH FIELD: M1 the interest-period segmentation and the
// effective due date; M2 the related-period list and hence the level
// installment; M3 the disbursement row's emission, the interest model's
// registration and the ordering window key; M4 the fee and penalty columns.
// They are not interchangeable.
//""",
)

sub(
    """//	                        see "The THREE date-membership rules" above);""",
    """//	                        see "The FOUR date-membership rules" above);""",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
