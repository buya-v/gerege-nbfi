#!/usr/bin/env python3
"""T41 edit batch 11 — leak closure: three->four membership rules, 4.5, 6.1, 8, 9."""
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


# --- 4.3.1's spec-check description -----------------------------------------
sub(
    "§4.3.1 and §4.3.2 *including the three membership rules and step 4b* — from the document "
    "text alone,",
    "§4.3.1 and §4.3.2 *including the membership rules and step 4b* — from the document text "
    "alone,",
)

# --- 4.3.2 provenance --------------------------------------------------------
sub(
    "the `periodRatio` multiplier, the three membership rules and step 4b added in revision 7 and "
    "re-derived by task T38 from the same checkout",
    "the `periodRatio` multiplier, membership rules M1–M3 and step 4b added in revision 7 and "
    "re-derived by task T38 from the same checkout; **M4 added in revision 8 and re-derived by "
    "task T41** [`LoanCharge.java:371-373`, "
    "`LoanRepaymentScheduleProcessingWrapper.java:251-254`, `LoanScheduleParams.java:533-535`, "
    "`ProgressiveLoanScheduleGenerator.java:140`, `:143`, `:154`, `:374`, `:377`, `:400-403`, "
    "`:479`, `:483`, `ProgressiveLoanInterestScheduleModel.java:243`, "
    "`RepaymentPeriod.java:449-451`]",
)

# --- section 9 date-membership obligation -----------------------------------
sub(
    "- **The date-membership obligation** (added in revision 7, P0-T37-1). The Go module must "
    "implement **all three** of §4.3.2's membership rules and must not collapse them into one:",
    "- **The date-membership obligation** (added in revision 7, P0-T37-1; **widened to four rules "
    "in revision 8** from task T40's charge observations). The Go module must implement **all "
    "four** of §4.3.2's membership rules and must not collapse them into one:",
)

sub(
    "and which §4.6 already uses as the ordering window key. M1 and M3 disagree on exactly one "
    "date — a disbursement on a repayment period's `DueDate` — and that disagreement is the whole "
    "of the next obligation.",

    "and which §4.6 already uses as the ordering window key; and **M4** — `[From, Due]` for the "
    "first repayment period and `(From, Due]` thereafter, the **same predicate function as M1** "
    "[`LoanRepaymentScheduleProcessingWrapper.java:251-254`] reached through "
    "`LoanCharge.isDueInPeriod` [`LoanCharge.java:371-373`, "
    "`ProgressiveLoanScheduleGenerator.java:400-403`] but with the \"is first\" flag supplied by "
    "the **mutable counter** `LoanScheduleParams.isFirstPeriod()` "
    "[`LoanScheduleParams.java:533-535`] rather than by the period's own "
    "`isFirstRepaymentPeriod()` [`ProgressiveLoanInterestScheduleModel.java:243`, "
    "`RepaymentPeriod.java:449-451`] — which decides **which row a CHARGE lands on**. M1 and M3 "
    "disagree on exactly one date — a disbursement on a repayment period's `DueDate` — and that "
    "disagreement is the whole of the next obligation. **M4 is not carried by this contract "
    "today** (there is no charge field), and it is stated so that a port which later admits "
    "charges does not reuse M1, M2 or M3 for them, and so that the **staleness** of M4's flag on "
    "the separated charge path (§4.5.1, decision C-2b) is a recorded oracle defect rather than a "
    "surprise.",
)

# --- section 9 rounding-policy bullet's closing sentence --------------------
sub(
    "**Revision 7 also names, in one place, the three date-membership rules the oracle uses on "
    "the disbursement date (§4.3.2), because two of them disagree and revisions 1–6 stated them "
    "in three different sections and never reconciled them.**",

    "**Revision 7 also names, in one place, the date-membership rules the oracle uses on the "
    "disbursement date (§4.3.2), because two of them disagree and revisions 1–6 stated them in "
    "three different sections and never reconciled them. Revision 8 adds a FOURTH to that same "
    "one place** — the rule that decides which row a **charge** lands on, which shares M1's "
    "interval shape but takes its \"is first\" input from a mutable counter and is therefore "
    "stale on one path (§4.3.2 M4, §4.5.1). **Revision 8 also makes the multiplier decision "
    "OBSERVED rather than only specified** (task T39: `periodRatio` 415 of 415 discriminating "
    "cells, `RepaymentEvery` 0 of 415), and adds §4.1.2, which says **which `MathContext` is in "
    "force** — the threaded one on Path A, the ambient one on Path B — so that an attestation is "
    "read as evidence of the thing it actually witnesses.",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
