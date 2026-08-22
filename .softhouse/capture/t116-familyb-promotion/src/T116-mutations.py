#!/usr/bin/env python3
"""T116 — the named wrong implementation the family-B cells are meant to kill.

Same contract as .softhouse/capture/t64-zeroprincipal/src/T64-mutations.py, which this file
deliberately does not edit or extend in place: each entry is (id, name, [(file, old, new), ...],
why); a patch is applied to a SCRATCH COPY of the port under /tmp, never to the committed tree, and
the anchor must appear EXACTLY ONCE or the run aborts.

THIS MUTATION IS NOT INVENTED BY T116. It is written down, by name, in the port's own source, as a
defect that the corpus cannot currently detect:

    nexus/internal/apps/loanschedule/emi.go:1832-1842, the doc comment on duePrincipalMinor --
    "THERE IS NO SPECIAL CASE THAT SETS THE FINAL ROW'S PRINCIPAL TO THE WHOLE REMAINING BALANCE.
     What makes the final row come out even is that the LAST UNPAID PERIOD'S INSTALLMENT absorbs
     the residual (see applyFinalPeriodResidual); the adjustment lands on the EMI and this
     expression is then applied to it unchanged. A PORT THAT SPECIAL-CASES THE PRINCIPAL INSTEAD
     REPRODUCES THE SAME NUMBERS ON THIS CORPUS AND IS WRONG IN SHAPE."

That last sentence is a standing admission of a blind spot. It is true precisely because every
promoted vector is a shape on which the final-period EMI adjustment SUCCEEDS in settling the
balance, so "the last row settles whatever is left" and "the last row's principal is emi - interest"
agree to the minor unit. Family B is the first observed shape where the adjustment does NOT settle
the balance, so it is the first shape on which the two readings can be told apart.

"The oracle" is the Fineract reference implementation. Oracle Database is a prohibited product in
this program and appears nowhere in this stack. Money is int64 minor units; there is no floating
point in this file.
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
EMI = os.path.join(ROOT, "nexus/internal/apps/loanschedule/emi.go")

MUTATIONS = [
    (
        "G8-FINAL-ROW-SETTLES-THE-BALANCE",
        "the final repayment row's principal is the whole remaining balance, instead of the "
        "balancing non-negative remainder of its own installment after interest",
        [(EMI,
          "func (m *scheduleModel) duePrincipalMinor(p *repaymentPeriod) int64 {\n"
          "\treturn maxInt64(0, p.emiMinor-m.dueInterestMinor(p))\n}",
          "func (m *scheduleModel) duePrincipalMinor(p *repaymentPeriod) int64 {\n"
          "\tif p.idx == len(m.periods)-1 {\n"
          "\t\tlast := p.segments[len(p.segments)-1]\n"
          "\t\treturn last.outstandingMinor + last.disbursedMinor\n"
          "\t}\n"
          "\treturn maxInt64(0, p.emiMinor-m.dueInterestMinor(p))\n}")],
        "getDuePrincipal is negativeToZero(emiPlusCreditedAmounts - getDueInterest()) on EVERY row "
        "including the last [RepaymentPeriod.java:339-344]; the final row comes out even because "
        "calculateLastUnpaidRepaymentPeriodEMI adjusts the INSTALLMENT "
        "[ProgressiveEMICalculator.java:1210-1214], not because the principal is special-cased. "
        "'The last row settles whatever is left' is the amortization-schedule folk rule, it is what "
        "every textbook writes, and it agrees with the oracle to the minor unit on every shape "
        "where the adjustment succeeds -- which is every one of the 43 vectors promoted before "
        "T116. The port's own doc comment names this reading as undetectable by the corpus.",
    ),
]

BY_ID = {m[0]: m for m in MUTATIONS}
