#!/usr/bin/env python3
"""T64 — the named wrong implementations this capture is meant to kill.

Each entry is (id, name, [(file, old, new), ...], why). A patch is applied to a
SCRATCH COPY of the port under /tmp, never to the committed tree, and the anchor
must appear EXACTLY ONCE or the run aborts: a mutation that silently failed to
apply would report "survives the corpus" about code that was never changed.

Every mutation below is a reading a competent porter could actually arrive at
from the Java, not a random corruption. Two of them are readings that were
ACTUALLY MADE during this task, by the author, before the source was re-opened.

"The oracle" is the Fineract reference implementation. Oracle Database is a
prohibited product in this program and appears nowhere in this stack. Money is
int64 minor units; there is no floating point in this file.
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
EMI = os.path.join(ROOT, "nexus/internal/apps/loanschedule/emi.go")

MUTATIONS = [
    (
        "ZP-GUARD-SCALES-THE-INSTALLMENT",
        "EMI smoothing guard multiplies the installment by floor(n/2) instead of comparing "
        "against floor(n/2) whole currency units",
        [(EMI,
          "\tthreshold := new(big.Int).Mul(big.NewInt(lowerHalf), pow10(minorDigits))",
          "\tthreshold := new(big.Int).Mul(big.NewInt(lowerHalf), big.NewInt(absInt64(original)))")],
        "EmiAdjustment.shouldBeAdjusted compares |emiDifference| * 100 against "
        "originalEmi.copy(lowerHalfOfRelatedPeriods) [EmiAdjustment.java:31-36]. Money.copy(double) "
        "REPLACES the amount rather than scaling it [Money.java:216-222], so the right-hand side is "
        "floor(n/2) whole currency units FLAT and carries no dependence on the installment at all. "
        "Reading `originalEmi.copy(k)` as `originalEmi * k` is the obvious misreading -- the method "
        "is called on the EMI and takes a count -- and it is the reading THE AUTHOR OF THIS TASK "
        "made from the same lines before re-opening Money.java. It changes when the loop fires.",
    ),
    (
        "ZP-GUARD-NONSTRICT",
        "EMI smoothing guard fires on equality (>=) where the oracle requires strict inequality (>)",
        [(EMI,
          "\treturn left.Cmp(threshold) > 0",
          "\treturn left.Cmp(threshold) >= 0")],
        "isGreaterThan is strict [EmiAdjustment.java:33-35]. On a rounding-floor shape the two "
        "sides are EXACTLY EQUAL -- |emiDifference| * 100 = floor(n/2) to the minor unit -- so "
        "strict-vs-non-strict decides whether the whole smoothing loop runs, and the two schedules "
        "that result are not close to each other. Off-by-one on a comparison operator is the "
        "cheapest defect in this file to introduce and the hardest to see in review.",
    ),
    (
        "ZP-RESIDUAL-NO-RECURSION",
        "the final-period residual clamps a negative installment to zero but does not re-apply "
        "itself, so the residual it could not place is silently dropped",
        [(EMI,
          "\tif m.periods[idx].emiMinor < 0 {\n\t\tm.periods[idx].emiMinor = 0\n\t\tm.applyFinalPeriodResidual(depth + 1)\n\t}",
          "\tif m.periods[idx].emiMinor < 0 {\n\t\tm.periods[idx].emiMinor = 0\n\t}")],
        "calculateLastUnpaidRepaymentPeriodEMI re-enters itself when the adjusted installment falls "
        "below what is already paid [ProgressiveEMICalculator.java:1211-1214]. This is the exact "
        "recursion T59 profiled at 34.9% cumulative on near-interest-only shapes and correctly "
        "declined to touch BECAUSE NO VECTOR GRADED IT. A port that drops the recursion as "
        "'dead on an unpaid schedule' is making the same judgement T59 refused to make.",
    ),
    (
        "ZP-PRINCIPAL-NOT-CLAMPED",
        "a repayment row's principal is installment minus interest without the negative clamp",
        [(EMI,
          "\treturn maxInt64(0, p.emiMinor-m.dueInterestMinor(p))",
          "\treturn p.emiMinor - m.dueInterestMinor(p)")],
        "getDuePrincipal wraps the subtraction in MathUtil.negativeToZero "
        "[RepaymentPeriod.java:345-350]. On every promoted vector the installment strictly exceeds "
        "the interest, so the clamp is a provable no-op and a porter who drops it as redundant "
        "passes the whole corpus. It is only at the rounding floor that installment and interest "
        "meet.",
    ),
    (
        "ZP-ADOPTION-TEST-NONSTRICT",
        "the smoothing loop adopts a trial whose EMI difference merely TIES the previous one",
        [(EMI,
          "\t\tif !(absInt64(newDifference) < absInt64(difference)) {",
          "\t\tif !(absInt64(newDifference) <= absInt64(difference)) {")],
        "hasLessEmiDifference is strict [EmiAdjustment.java:45-47] and its failure DISCARDS the "
        "trial, leaving the live schedule at its pre-trial values "
        "[ProgressiveEMICalculator.java:1288-1290]. Equality is not adoption.",
    ),
    (
        "ZP-SMOOTHING-DIVISOR-IS-LOWER-HALF",
        "the smoothing loop spreads the gap over floor(n/2) periods instead of n",
        [(EMI,
          "\t\tdivisor := maxInt64(1, int64(len(related)))",
          "\t\tdivisor := maxInt64(1, int64(len(related)/2))")],
        "adjustment() divides by max(1, numberOfRelatedPeriods() - uncountablePeriods) "
        "[EmiAdjustment.java:37-39], and uncountablePeriods is identically zero at origination "
        "[ProgressiveEMICalculator.java:2027-2031]. floor(n/2) appears one method above in the same "
        "record and is the natural thing to carry down by accident.",
    ),
]

BY_ID = {m[0]: m for m in MUTATIONS}
