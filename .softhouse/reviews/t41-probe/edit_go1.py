#!/usr/bin/env python3
"""T41 — contract.go edits, batch 1: Rounding doc (multiplier, daysInMonth, MathContext)."""
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


# --- the "of the two argument differences" note -----------------------------
sub(
    """	// Both land in rateFactorByRepaymentPeriod's repaymentEvery parameter
	// (:1951) and are consumed once, at :1957. Of the two argument differences
	// only the MULTIPLIER is live inside the graded domain: daysInMonth is
	// daysInMonthType.isDaysInMonth_30() ? 30 : calculatedDaysInRepaymentPeriod
	// (:1508), so under DayCountFixed30Over360 both call sites pass exactly 30.
""",
    """	// Both land in rateFactorByRepaymentPeriod's repaymentEvery parameter
	// (:1951) and are consumed once, at :1957. Of the two argument differences
	// only the MULTIPLIER is live — and revision 8 states the UNCONDITIONAL
	// form of that, narrowing revision 7 (task T39's finding N-1). daysInMonth
	// is daysInMonthType.isDaysInMonth_30() ? 30 : calculatedDaysInRepaymentPeriod
	// (:1508) and it is consumed at exactly one place, :1537, which sits inside
	// the `case DAYS_30 ->` arm at :1536 — precisely the branch in which :1508
	// yields the literal 30, the same literal the interest call site passes at
	// :1413. On the other two DaysInMonthType values NEITHER call site is
	// reached with a days-in-month argument at all: ACTUAL takes :1534-1535 and
	// :1400-1402, INVALID throws at :1538 and :1415-1416. So there is no
	// configuration, inside the graded domain or outside it, in which the two
	// call sites pass different days-in-month arguments. A PORT MUST NOT
	// "correct" this second argument to differ between the call sites; only the
	// multiplier differs.
""",
)

# --- the blindness claim ----------------------------------------------------
sub(
    """	// A PORT THAT USES RepaymentEvery ON THE INTEREST CALL SITE RETURNS
	// DIFFERENT MONEY on 100% of drifted-boundary shapes — 480 of 480 swept,
	// worst total-interest gap MNT 398,967.73 — AND NO CAPTURE CAN DETECT IT:
	// 0 of the 21 committed production-setting captures and 0 of the 13
	// observations carry a non-unit periodRatio. Those counts are
	// RE-DERIVATIONS, not observations. The missing vector is DEC-1 section 8
	// item 3e, and the conformance/cutover binding is six vectors because of it.
""",
    """	// A PORT THAT USES RepaymentEvery ON THE INTEREST CALL SITE RETURNS
	// DIFFERENT MONEY on 100% of drifted-boundary shapes — 480 of 480 swept,
	// worst total-interest gap MNT 398,967.73 (that sweep is a RE-DERIVATION).
	//
	// REVISION 8: THIS IS NOW OBSERVED, NOT ONLY RE-DERIVED. Task T39 captured
	// 8 drift shapes from the pinned reference oracle; on the 415 cells where
	// the two readings disagree the oracle agrees with periodRatio 415 of 415
	// and with RepaymentEvery 0 of 415, and the periodRatio reading reproduces
	// all 1,239 cells of all 15 parity-setting captures with zero mismatches
	// (.softhouse/capture/periodratio/, analysis/discriminate-output.txt). The
	// worst gap is observed at exactly the re-derived MNT 398,967.73, and there
	// is no size threshold: MNT 100 still separates on 27 cells. The 21
	// pre-T39 captures still cannot see any of it, which is why the captures
	// had to be taken.
	//
	// A PORT MUST ALSO REPRODUCE THE MONTH-END SPECIAL CASE in the k step above
	// (:1426-1436, predicate at :1432, effect at :1433). Omitting those four
	// lines roughly DOUBLES periodRatio on alternate periods — an observed
	// MNT 83,959.76 overcharge on one six-month MNT 3,924,149 loan, refuted on
	// 116 of 116 discriminating cells (captures T39-ME-A..T39-ME-D). It cannot
	// share a vector with the multiplier question: over 51,729 same-month pairs
	// the special case fires on 210 and on 0 of those 210 does
	// ScheduleStartDate differ from Disbursement.Date, so the two questions are
	// DISJOINT in shape space.
	//
	// Both captures are attested raw observations, NOT admissible vectors. The
	// missing vectors are DEC-1 section 8 items 3e and 3f, and the
	// conformance/cutover binding is SEVEN vectors because of them.
""",
)

sub(
    """	// capture is an attested raw observation and not yet an admissible vector
	// (DEC-1 section 8 items 1 and 3d). The MULTIPLIER rule remains ungraded.
""",
    """	// capture is an attested raw observation and not yet an admissible vector
	// (DEC-1 section 8 items 1 and 3d). The MULTIPLIER rule is now OBSERVED
	// too (T39, above) and likewise NOT PROMOTED, so it remains UNGRADED: a
	// conformance PASS is not evidence that a port implements it.
""",
)

# --- Mode doc: the two-context rule ----------------------------------------
sub(
    """	// The reference oracle takes every tie rule from one of two places — the
	// threaded MathContext where one is passed, and the tenant-global
	// MathContext where one is not (Money.java:52; Money.java:102-104;
	// Money.java:150-157; Money.java:159-161 and :163-170, whose return path
	// goes through the two-argument Money.of and therefore reads the
	// tenant-global context even though its own division used the threaded
	// one). Independently settable modes would admit combinations no deployment
	// can produce and would double the vector matrix.
""",
    """	// The reference oracle takes every tie rule from one of two places — the
	// threaded MathContext where one is passed, and the tenant-global
	// (AMBIENT) MathContext where one is not. WHICH OF THE TWO APPLIES IS
	// DECIDED BY ONE LINE, and revision 8 cites it rather than leaving
	// Money.java:52 to imply it: Money holds its own MathContext field
	// (Money.java:32), assigned in the constructor at :42 BEFORE the
	// currency-scale setScale at :52 runs, and getMc() is an INSTANCE method —
	// `return mc != null ? mc : MoneyHelper.getMathContext()`
	// (Money.java:494-496). So :52 reads the THREADED mode whenever one was
	// threaded, and the ambient mode ONLY where none was: the two-argument
	// Money.of (:102-104, :114-116), Money.zero(currency) (:118-120), the
	// static roundToMultiplesOf(BigDecimal, Integer) (:150-157),
	// roundToMultiplesOf(Money, Integer) (:159-161) and the three-argument
	// form's return path (:163-170, the two-argument Money.of at :169), and
	// multipliedBy(double) (:372-378, the two-argument Money.of at :377).
	// Every one of those sits on the installment-multiple or
	// multipliedBy(double) path, which the graded domain excludes.
	// Independently settable modes would admit combinations no deployment can
	// produce and would double the vector matrix.
	//
	// CONSEQUENCE, AND IT IS OBSERVED (revision 8; DEC-1 section 4.1.2, from
	// task T39's finding N-3). On the Path-A embeddable seam the arithmetic in
	// force is the THREADED MathContext; the AMBIENT MoneyHelper context is
	// inert inside the graded domain. Forcing the tenant rounding mode to DOWN
	// changed MoneyHelper.getMathContext() on the oracle's own testimony and
	// left ALL SIXTEEN observed capture blocks byte-identical; forcing the
	// THREADED mode to DOWN moved FIFTEEN OF SIXTEEN
	// (.softhouse/capture/periodratio/out/t39-neg5.json and out/t39-neg7.json
	// against out/t39-periodratio.json). On the Path-B running-server path the
	// converse holds — nothing threads a context, getMc() takes its null
	// branch, and the ambient mode IS the arithmetic, which is why the same
	// request on two tenants differing only in mode returns 20,925.05 under
	// HALF_UP and 20,925.04 under HALF_EVEN. A CAPTURE ATTESTATION MUST
	// RECORD THE TWO CONTEXTS AS TWO LABELLED FIELDS; "captured at
	// (19, HALF_UP)" does not say which, and on Path A only the threaded one
	// is evidence about the money.
""",
)

sub(
    """	// ADAPTER OBLIGATION, and it is wider than a single call site: the
	// Fineract-JVM adapter MUST initialise the tenant rounding mode to Mode
	// before EVERY call, because every path that constructs Money without an
	// explicit MathContext reads the tenant-global one, and outside an
	// initialised tenant those paths throw IllegalStateException
	// (MoneyHelper.java:74-82).
""",
    """	// ADAPTER OBLIGATION, and it is wider than a single call site: the
	// Fineract-JVM adapter MUST initialise the tenant rounding mode to Mode
	// before EVERY call, because every path that constructs Money without an
	// explicit MathContext reads the tenant-global one, and outside an
	// initialised tenant those paths throw IllegalStateException
	// (MoneyHelper.java:74-82, :91-93).
	//
	// REVISION 8 CORRECTS WHY. The obligation does NOT rest on the ambient mode
	// changing the answer inside the graded domain — observation says it does
	// not (T39: 0 of 16 blocks moved under an ambient-only change). It rests on
	// the THROW: an uninitialised tenant fails loudly instead of returning a
	// silently different number, and that is the stronger of the two reasons.
""",
)

sub(
	"""	// every Money is constructed through the three-argument Money.of(..., mc)
	// carrying the threaded context, and the Money constructor reads only the
	// ROUNDING MODE from getMc() (Money.java:52), never the precision. The call
	// sites that DO read the tenant-global precision (Money.java:103, :115,
	// :160, :169, :377) all sit on the installment-multiple and
	// multipliedBy(double) paths, and applyInstallmentAmountInMultiplesOf is
	// the identity inside the graded domain
	// (ProgressiveEMICalculator.java:1761-1766), so no reached call site
	// consults it.
""",
	"""	// every Money is constructed through the three-argument Money.of(..., mc)
	// carrying the threaded context, and the Money constructor reads only the
	// ROUNDING MODE from getMc() (Money.java:52), never the precision — and on
	// such a Money getMc() IS the threaded context (Money.java:494-496), so
	// that read is not a tenant-global read at all. The call sites that DO
	// reach the tenant-global context (Money.java:103, :115, :160, :169, :377)
	// all sit on the installment-multiple and multipliedBy(double) paths, and
	// applyInstallmentAmountInMultiplesOf is the identity inside the graded
	// domain (ProgressiveEMICalculator.java:1761-1766), so no reached call site
	// consults the tenant-global precision OR the tenant-global mode. That is
	// established from source and CONFIRMED BY A NEGATIVE TEST (T39, above).
""",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
