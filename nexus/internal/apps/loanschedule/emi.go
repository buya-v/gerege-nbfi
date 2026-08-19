package loanschedule

import "math/big"

// The progressive-loan interest schedule model, and the EMI arithmetic over it.
//
// This is a port of the reference oracle's ProgressiveLoanInterestScheduleModel /
// RepaymentPeriod / InterestPeriod triple and of ProgressiveEMICalculator's
// declining-balance path, at pinned commit
// 426a23544e8426a38ae43ae404670a0a7e85b9eb.
//
// TWO STRUCTURAL DIFFERENCES FROM THE JAVA, BOTH DELIBERATE AND BOTH INERT:
//
//  1. The oracle memoises the derived quantities (RepaymentPeriod's four
//     Memo fields). Memo invalidates on the hash of its declared dependencies
//     [VERIFIED: Memo.java:56-72 recomputes whenever a dependency hash moves, and
//     InterestPeriod carries a generated equals/hashCode over its amounts,
//     InterestPeriod.java:40-43], so it is a pure cache. This port recomputes on
//     every read, which is the same function without the cache.
//  2. Every quantity the oracle carries as a Money is an int64 count of minor
//     units here. Money is a BigDecimal at the currency's scale plus a
//     MathContext [VERIFIED: Money.java:40-53], and at a fixed scale its add,
//     subtract, min, max and clamp are exact integer operations, so the two
//     representations agree cell for cell. Only the quantities the oracle carries
//     as a bare BigDecimal -- rate factors, growth factors, the EMI recurrence --
//     are rationals here, and each is rounded exactly where the oracle rounds it.

// interestPeriod is one segment of a repayment period.
// Port of InterestPeriod.
type interestPeriod struct {
	from, due civilDate

	// rateFactor is the segment's own rate factor, quantized to the request's
	// RateFactorScale [VERIFIED: ProgressiveEMICalculator.java:639-640 ->
	// :1486-1541]. The repayment period's growth factor sums these.
	rateFactor *big.Rat

	// rateFactorTillDue is the rate factor computed over
	// [segment FromDate, ENCLOSING REPAYMENT PERIOD DueDate]
	// [VERIFIED: ProgressiveEMICalculator.java:641-642 -> :1355-1418]. The
	// per-period interest reads this one, and it takes periodRatio as its
	// multiplier where the other takes RepaymentEvery.
	rateFactorTillDue *big.Rat

	// disbursedMinor is the principal registered ON this segment. It enters the
	// balance of the segment AFTER it, never this one
	// [VERIFIED: InterestPeriod.java:167-186].
	disbursedMinor int64

	// outstandingMinor is the balance carried INTO this segment.
	outstandingMinor int64
}

// repaymentPeriod is one installment window.
// Port of RepaymentPeriod.
type repaymentPeriod struct {
	from, due civilDate
	segments  []*interestPeriod
	emiMinor  int64

	// idx is this period's position in the model, cached so that the derived
	// quantities can walk the chain of previous periods without a linear search.
	idx int
}

// scheduleModel is the whole interest schedule under construction.
type scheduleModel struct {
	periods []*repaymentPeriod

	minorDigits int32
	precision   int32 // Rounding.SignificantDigits
	scale       int32 // Rounding.RateFactorScale

	// rate is the nominal annual rate as the reference oracle holds it after
	// dividing the input percentage by 100 under the MathContext
	// [VERIFIED: ProgressiveEMICalculator.java:1318-1320].
	rate *big.Rat

	repaymentEvery int64

	// daysInMonth and daysInYear are the day-count constants of
	// DayCountFixed30Over360: 30 and 360. daysInMonth is 30 on BOTH rate-factor
	// call sites and on every path either is reachable on -- the local at
	// :1508 is consumed only from the `case DAYS_30 ->` arm at :1536, which is
	// precisely where that ternary yields 30, and the interest call site passes
	// the literal 30 at :1413.
	daysInMonth *big.Rat
	daysInYear  *big.Rat
}

// newInterestPeriod builds a segment with the oracle's initial amounts: rate
// factors BigDecimal.ZERO and every Money zero
// [VERIFIED: InterestPeriod.java:96-105, withEmptyAmounts].
func newInterestPeriod(from, due civilDate) *interestPeriod {
	return &interestPeriod{from: from, due: due, rateFactor: new(big.Rat), rateFactorTillDue: new(big.Rat)}
}

// newRepaymentPeriod builds a window carrying exactly one segment spanning the
// whole of it [VERIFIED: RepaymentPeriod.java:143-151, create].
func newRepaymentPeriod(from, due civilDate) *repaymentPeriod {
	return &repaymentPeriod{from: from, due: due, segments: []*interestPeriod{newInterestPeriod(from, due)}}
}

func (m *scheduleModel) deepCopy() *scheduleModel {
	out := &scheduleModel{
		minorDigits: m.minorDigits, precision: m.precision, scale: m.scale,
		rate: m.rate, repaymentEvery: m.repaymentEvery,
		daysInMonth: m.daysInMonth, daysInYear: m.daysInYear,
		periods: make([]*repaymentPeriod, 0, len(m.periods)),
	}
	for _, p := range m.periods {
		q := &repaymentPeriod{from: p.from, due: p.due, emiMinor: p.emiMinor, idx: p.idx,
			segments: make([]*interestPeriod, 0, len(p.segments))}
		for _, s := range p.segments {
			t := *s
			q.segments = append(q.segments, &t)
		}
		out.periods = append(out.periods, q)
	}
	return out
}

// previous returns the period before p, or nil for the first
// [VERIFIED: RepaymentPeriod.java:449-451, isFirstRepaymentPeriod is
// previous == null].
func (m *scheduleModel) previous(p *repaymentPeriod) *repaymentPeriod {
	if p.idx <= 0 {
		return nil
	}
	return m.periods[p.idx-1]
}

// startDate is the model's own start: the FIRST repayment period's from-date
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:208-210].
func (m *scheduleModel) startDate() civilDate { return m.periods[0].from }

// ---------------------------------------------------------------------------
// Membership conventions. Named M1..M3 after the contract's normative list; each
// decides a different thing and they are NOT interchangeable.
// ---------------------------------------------------------------------------

// inPeriodM1 is [FromDate, DueDate] for the FIRST repayment period and
// (FromDate, DueDate] for every later one
// [VERIFIED: LoanRepaymentScheduleProcessingWrapper.java:251-254, reached from
// ProgressiveLoanInterestScheduleModel.java:243-244].
//
// Decides: which repayment period a balance change is registered into, hence the
// interest-period segmentation and the effective due date.
func inPeriodM1(target, from, due civilDate, isFirst bool) bool {
	if isFirst {
		return compareDates(target, from) >= 0 && compareDates(target, due) <= 0
	}
	return compareDates(target, from) > 0 && compareDates(target, due) <= 0
}

// inPeriodM3 is [FromDate, DueDate) -- from-inclusive, DUE-EXCLUSIVE
// [VERIFIED: ProgressiveLoanScheduleGenerator.java:306-307,
// !disbursementDate.isBefore(periodFromDate) && disbursementDate.isBefore(periodDueDate)].
//
// Decides: during which period's ITERATION the disbursement row is emitted and
// the disbursement registered. M1 and M3 disagree on exactly one date -- a
// disbursement dated on a repayment period's due date, which M1 puts in period j
// and M3 in period j+1. That single date is the whole of the row-ordering trap.
func inPeriodM3(target, from, due civilDate) bool {
	return compareDates(target, from) >= 0 && compareDates(target, due) < 0
}

// findPeriodForBalanceChange applies M1
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:238-245].
func (m *scheduleModel) findPeriodForBalanceChange(d civilDate) *repaymentPeriod {
	for i, p := range m.periods {
		if inPeriodM1(d, p.from, p.due, i == 0) {
			return p
		}
	}
	return nil
}

// relatedPeriods are the periods whose DueDate is NOT BEFORE the effective due
// date [VERIFIED: ProgressiveLoanInterestScheduleModel.java:190-197]. They are
// the ONLY periods the level installment is computed over and written to, and
// their count is the n of the EMI re-adjust loop -- never NumberOfRepayments.
func (m *scheduleModel) relatedPeriods(effectiveDue civilDate) []*repaymentPeriod {
	var out []*repaymentPeriod
	for _, p := range m.periods {
		if compareDates(p.due, effectiveDue) >= 0 {
			out = append(out, p)
		}
	}
	return out
}

// ---------------------------------------------------------------------------
// Disbursement registration
// ---------------------------------------------------------------------------

// addDisbursement registers the advance and recomputes the schedule.
//
// Port of ProgressiveEMICalculator.addDisbursement
// [VERIFIED: :124-152]. The effectiveDueDate branch at :128-133 requires a
// non-null interestCalculationPeriodMethod, which the capture seam's assembler
// never populates [VERIFIED: LoanApplicationTerms.java:579-606 sets no
// interestCalculationPeriodMethod], so the disbursement date is used unchanged.
// The addFullTermTrancheDisbursement arm at :141-145 is gated on
// allowFullTermForTranche, pinned false by the contract.
func (m *scheduleModel) addDisbursement(d civilDate, amountMinor int64) {
	owner := m.findPeriodForBalanceChange(d)
	if owner == nil {
		return
	}
	m.registerBalanceChange(owner, d, amountMinor)
	m.recalculate(m.effectiveRepaymentDueDate(owner, d))
}

// effectiveRepaymentDueDate: if the change lands exactly on the matched period's
// due date the calculation starts from the NEXT period's due date
// [VERIFIED: ProgressiveEMICalculator.java:249-262]. This is what takes the
// level installment off the periods that close before the money arrives.
func (m *scheduleModel) effectiveRepaymentDueDate(owner *repaymentPeriod, d civilDate) civilDate {
	if compareDates(owner.due, d) == 0 {
		if owner.idx+1 < len(m.periods) {
			return m.periods[owner.idx+1].due
		}
	}
	return owner.due
}

// registerBalanceChange puts the amount on the right segment, splitting one if
// the date falls strictly inside
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:245-296].
func (m *scheduleModel) registerBalanceChange(owner *repaymentPeriod, d civilDate, amountMinor int64) {
	isLast := owner.idx == len(m.periods)-1
	onMaturity := isLast && compareDates(d, owner.due) == 0

	if onMaturity {
		// A credit on the maturity date wants a zero-length segment, and reuses
		// one only if the last segment already is zero-length [:266-272].
		last := owner.segments[len(owner.segments)-1]
		if daysBetween(last.from, last.due) == 0 {
			last.disbursedMinor += amountMinor
			return
		}
	} else {
		// A segment that already ENDS exactly on the date takes the amount with
		// no split [:274-277].
		for _, s := range owner.segments {
			if compareDates(d, s.due) == 0 {
				s.disbursedMinor += amountMinor
				return
			}
		}
	}
	m.insertSegment(owner, d, amountMinor)
}

// insertSegment moves the containing segment's due date back to d, gives it the
// amount, and inserts a fresh segment [d, the original due date] after it
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:281-296].
func (m *scheduleModel) insertSegment(owner *repaymentPeriod, d civilDate, amountMinor int64) {
	idx := 0
	// findPreviousInterestPeriod: the LAST segment with from < d <= due, else the
	// first segment [VERIFIED: :327-330].
	found := false
	for i, s := range owner.segments {
		if compareDates(d, s.from) > 0 && compareDates(d, s.due) <= 0 {
			idx, found = i, true
		}
	}
	if !found {
		idx = 0
	}
	prev := owner.segments[idx]
	originalDue := prev.due
	// calculateNewDueDate clamps d into the segment's own window [:439-441].
	newDue := d
	if compareDates(d, prev.from) < 0 {
		newDue = prev.from
	} else if compareDates(d, prev.due) > 0 {
		newDue = prev.due
	}
	prev.due = newDue
	prev.disbursedMinor += amountMinor

	inserted := newInterestPeriod(newDue, originalDue)
	tail := append([]*interestPeriod{inserted}, owner.segments[idx+1:]...)
	owner.segments = append(owner.segments[:idx+1:idx+1], tail...)
}

// ---------------------------------------------------------------------------
// The declining-balance recalculation
// ---------------------------------------------------------------------------

// recalculate is calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod
// [VERIFIED: ProgressiveEMICalculator.java:729-752].
//
// onlyOnActualModelShouldApply is true here because the schedule model is empty
// at the initial disbursement of every loan (:731-734), which is the only
// operation the graded domain admits -- so both the actual-model EMI and the
// re-adjust loop run. The interest and principal moratorium arms are gated on a
// grace configuration the seam cannot express.
func (m *scheduleModel) recalculate(effectiveDue civilDate) {
	related := m.relatedPeriods(effectiveDue)
	for _, p := range related {
		m.calculateRateFactors(p)
	}
	m.updateOutstandingBalances()
	m.calculateLevelInstallment(related)
	m.updateOutstandingBalances()
	m.applyFinalPeriodResidual(0)
	m.adjustEMIIfNeeded(related)
}

// updateOutstandingBalances is calculateOutstandingBalance
// [VERIFIED: ProgressiveEMICalculator.java:1253-1255 ->
// InterestPeriod.updateOutstandingLoanBalance, InterestPeriod.java:166-186].
//
// The walk is strictly in order: a segment's opening balance is read off the one
// before it, and the FIRST segment of the FIRST repayment period is never
// assigned at all -- it keeps the zero it was constructed with, which is why a
// repayment row that closes before the disbursement reports zero rather than the
// principal awaiting advance.
func (m *scheduleModel) updateOutstandingBalances() {
	for i, p := range m.periods {
		for j, s := range p.segments {
			if j == 0 {
				if i == 0 {
					continue
				}
				prevPeriod := m.periods[i-1]
				prevSeg := prevPeriod.segments[len(prevPeriod.segments)-1]
				s.outstandingMinor = maxInt64(0,
					prevSeg.outstandingMinor+prevSeg.disbursedMinor-m.duePrincipalMinor(prevPeriod))
				continue
			}
			prevSeg := p.segments[j-1]
			s.outstandingMinor = maxInt64(0, prevSeg.outstandingMinor+prevSeg.disbursedMinor)
		}
	}
}

// segmentCalculatedInterest is the interest of ONE segment, in major units.
//
// [VERIFIED: InterestPeriod.java:143-158.] The three operations are rounded
// SEPARATELY and IN THIS ORDER. Operations (2) and (3) cancel algebraically --
// inside the graded domain lengthTillDue equals length on every segment carrying
// a balance -- and DO NOT cancel numerically at 19 significant digits. Collapsing
// them into the textbook balance * rateFactor is a named counterfactual.
func (m *scheduleModel) segmentCalculatedInterest(p *repaymentPeriod, s *interestPeriod) *big.Rat {
	lengthTillDue := daysBetween(s.from, p.due)
	if lengthTillDue == 0 {
		return new(big.Rat)
	}
	base := majorFromMinor(s.outstandingMinor, m.minorDigits)
	t1 := roundSignificant(new(big.Rat).Mul(base, s.rateFactorTillDue), m.precision)
	t2 := roundSignificant(new(big.Rat).Quo(t1, ratInt64(lengthTillDue)), m.precision)
	t3 := roundSignificant(new(big.Rat).Mul(t2, ratInt64(daysBetween(s.from, s.due))), m.precision)
	return t3
}

// interestChainUpTo computes, in ONE forward pass, the calculated and due
// interest of every period up to and including index last, and returns that
// period's pair.
//
// The chain exists because a period's calculated interest carries the PREVIOUS
// period's UNRECOGNIZED interest -- interest that found no room in that
// period's installment [VERIFIED: RepaymentPeriod.java:255-257 adds
// getPrevious().get().getUnrecognizedInterest(), and :381-383 defines it as
// calculatedDueInterest minus dueInterest, clamped at zero]. The oracle
// expresses that as mutual recursion behind four memoised suppliers; without the
// memoisation the same recursion is exponential, so this port walks the chain
// forward instead. It is the same function, and only periods 0..last are needed
// because nothing later can influence an earlier period.
func (m *scheduleModel) interestChainUpTo(last int) (calculated, due int64) {
	var carriedUnrecognized int64
	for i := 0; i <= last; i++ {
		p := m.periods[i]
		// SUM THE SEGMENTS, THEN MAKE IT MONEY -- exactly once, and in that order:
		// rounding each segment to the minor unit and then adding is a different
		// function [VERIFIED: RepaymentPeriod.java:246-252, Money.of(currency, sum,
		// mc) whose constructor applies the currency scale at Money.java:52].
		sum := new(big.Rat)
		for _, s := range p.segments {
			sum.Add(sum, m.segmentCalculatedInterest(p, s))
		}
		calculated = maxInt64(0, minorFromMajor(sum, m.minorDigits)+carriedUnrecognized)
		// CAP AT THE INSTALLMENT [VERIFIED: RepaymentPeriod.java:266-280]. Nothing
		// is ever paid on a schedule this contract generates, so the paid-amount
		// arms of that expression collapse to the min.
		due = maxInt64(0, minInt64(calculated, p.emiMinor))
		carriedUnrecognized = maxInt64(0, calculated-due)
	}
	return calculated, due
}

func (m *scheduleModel) calculatedDueInterestMinor(p *repaymentPeriod) int64 {
	c, _ := m.interestChainUpTo(p.idx)
	return c
}

func (m *scheduleModel) dueInterestMinor(p *repaymentPeriod) int64 {
	_, d := m.interestChainUpTo(p.idx)
	return d
}

// duePrincipalMinor is the BALANCING non-negative remainder of the installment
// after interest -- ON EVERY ROW INCLUDING THE LAST
// [VERIFIED: RepaymentPeriod.java:339-344, getDuePrincipal is
// negativeToZero(emiPlusCreditedAmounts... minus getDueInterest())].
//
// THERE IS NO SPECIAL CASE THAT SETS THE FINAL ROW'S PRINCIPAL TO THE WHOLE
// REMAINING BALANCE. What makes the final row come out even is that the LAST
// UNPAID PERIOD'S INSTALLMENT absorbs the residual (see applyFinalPeriodResidual);
// the adjustment lands on the EMI and this expression is then applied to it
// unchanged. A port that special-cases the principal instead reproduces the same
// numbers on this corpus and is wrong in shape.
func (m *scheduleModel) duePrincipalMinor(p *repaymentPeriod) int64 {
	return maxInt64(0, p.emiMinor-m.dueInterestMinor(p))
}

// outstandingLoanBalanceMinor is the balance AFTER this row is applied, clamped
// at zero [VERIFIED: RepaymentPeriod.java:387-401].
func (m *scheduleModel) outstandingLoanBalanceMinor(p *repaymentPeriod) int64 {
	last := p.segments[len(p.segments)-1]
	return maxInt64(0, last.outstandingMinor+last.disbursedMinor-m.duePrincipalMinor(p))
}

// initialBalanceMinor is the balance the level installment is computed from: the
// previous period's closing balance plus everything disbursed inside this one
// [VERIFIED: RepaymentPeriod.java:418-432].
func (m *scheduleModel) initialBalanceMinor(p *repaymentPeriod) int64 {
	var initial int64
	if prev := m.previous(p); prev != nil {
		initial = m.outstandingLoanBalanceMinor(prev)
	}
	for _, s := range p.segments {
		initial += s.disbursedMinor
	}
	return initial
}

// growthFactor is 1 PLUS THE SUM OF the period's segments' rate factors, added
// with no MathContext at all -- the additions are EXACT and the quantized rate
// factors' full width propagates into the recurrence
// [VERIFIED: RepaymentPeriod.java:214-217].
func (m *scheduleModel) growthFactor(p *repaymentPeriod) *big.Rat {
	out := big.NewRat(1, 1)
	for _, s := range p.segments {
		out.Add(out, s.rateFactor)
	}
	return out
}

// ---------------------------------------------------------------------------
// Rate factors
// ---------------------------------------------------------------------------

// calculateRateFactors fills both rate factors of every segment of p
// [VERIFIED: ProgressiveEMICalculator.java:636-644].
func (m *scheduleModel) calculateRateFactors(p *repaymentPeriod) {
	for _, s := range p.segments {
		s.rateFactor = m.rateFactorForRecurrence(p, s)
		s.rateFactorTillDue = m.rateFactorForInterest(p, s)
	}
}

// rateFactorForRecurrence is calculateRateFactorPerPeriod's DAYS_30 arm
// [VERIFIED: ProgressiveEMICalculator.java:1486-1541, dispatch at :1536].
// Its multiplier is RepaymentEvery and its span is the segment's own window.
func (m *scheduleModel) rateFactorForRecurrence(p *repaymentPeriod, s *interestPeriod) *big.Rat {
	return m.rateFactorByRepaymentPeriod(
		ratInt64(m.repaymentEvery),
		daysBetween(s.from, s.due),
		daysBetween(p.from, p.due))
}

// rateFactorForInterest is calculateRateFactorPerPeriodForInterest's DAYS_30 arm
// [VERIFIED: ProgressiveEMICalculator.java:1355-1418, dispatch at :1404-1413].
//
// It differs from the recurrence's factor in TWO arguments and only one of them
// is live: the MULTIPLIER is periodRatio, not RepaymentEvery, and the span runs
// from the segment's from-date to the ENCLOSING REPAYMENT PERIOD's due date. The
// days-in-month argument is 30 at both call sites on every reachable path, so a
// port must NOT "correct" it to differ between them.
func (m *scheduleModel) rateFactorForInterest(p *repaymentPeriod, s *interestPeriod) *big.Rat {
	return m.rateFactorByRepaymentPeriod(
		m.periodRatio(p),
		daysBetween(s.from, p.due),
		daysBetween(p.from, p.due))
}

// rateFactorByRepaymentPeriod is the shared kernel
// [VERIFIED: ProgressiveEMICalculator.java:1947-1962].
//
//	if calculatedDaysInPeriod == 0 -> exactly ZERO, before any operation runs
//	fraction = daysInMonth * multiplier / daysInYear          (2 mc operations)
//	factor   = rate * fraction * actualDays / calculatedDays  (3 mc operations)
//	           then setScale(RateFactorScale, HALF_UP)
//
// The trailing setScale is a SCALE, not a precision: on a quantity of order
// 0.005 to 0.02 it is strictly lossier than the same count of significant
// digits, and the loss reaches a payable amount.
//
// The last two operations are a PRORATION whose denominator is the ENCLOSING
// REPAYMENT PERIOD's length and never the span's own. The ratio is 1 if and only
// if the span opens on that period's from-date; a disbursement dated strictly
// inside a period makes it strictly less than 1, and that term is the entire
// mechanism by which a mid-period advance is charged less than a full period.
func (m *scheduleModel) rateFactorByRepaymentPeriod(multiplier *big.Rat, actualDays, calculatedDays int64) *big.Rat {
	if calculatedDays == 0 {
		return new(big.Rat)
	}
	fraction := roundSignificant(new(big.Rat).Mul(m.daysInMonth, multiplier), m.precision)
	fraction = roundSignificant(new(big.Rat).Quo(fraction, m.daysInYear), m.precision)

	v := roundSignificant(new(big.Rat).Mul(m.rate, fraction), m.precision)
	v = roundSignificant(new(big.Rat).Mul(v, ratInt64(actualDays)), m.precision)
	v = roundSignificant(new(big.Rat).Quo(v, ratInt64(calculatedDays)), m.precision)
	return roundScale(v, m.scale)
}

// periodRatio is the interest call site's multiplier
// [VERIFIED: ProgressiveEMICalculator.java:1419-1459, seed at :1461-1481].
//
// It equals RepaymentEvery if and only if the period's window sits on the
// lattice ScheduleStartDate + j months. It leaves that lattice whenever the
// month-end re-anchor has moved a boundary, because the re-anchor is seeded on
// the DISBURSEMENT date while the seed here is the SCHEDULE START -- and that
// asymmetry between two seeds is the whole mechanism.
//
// Only the MONTHS arm is implemented: every other repayment unit is refused
// before any of this runs, and the YEARS arm of the enclosing dispatch throws in
// the oracle itself.
func (m *scheduleModel) periodRatio(p *repaymentPeriod) *big.Rat {
	seed := m.periodRatioSeed(p)

	// The whole-month count, by java.time's PACKED rule
	// (monthsUntil: (year*12 + month-1)*32 + day, difference divided by 32 and
	// truncated toward zero) [VERIFIED: DateUtils.java:308-317 ->
	// ChronoUnit.MONTHS.between].
	//
	// THE MONTH-END SPECIAL CASE at :1426-1436 is part of the rule, not an
	// optimisation: when the target is the last day of its month AND the seed's
	// day is later, the count is measured to the day AFTER the target. Keeping
	// the packed rule and dropping these four lines roughly DOUBLES periodRatio
	// on alternate periods.
	var months int64
	seedDay := seed.Day
	targetDay := p.from.Day
	if daysInMonth(p.from.Year, p.from.Month) == targetDay && seedDay > targetDay {
		months = monthsBetween(seed, plusDays(p.from, 1))
	} else {
		months = monthsBetween(seed, p.from)
	}

	multiplicator := months + 1
	cursor := p.from
	for compareDates(cursor, p.due) < 0 {
		cursor = plusMonths(seed, multiplicator)
		if compareDates(cursor, p.due) <= 0 {
			multiplicator++
			continue
		}
		fullPeriodDate := cursor
		multiplicator = multiplicator - months - 1
		cursor = plusMonths(seed, multiplicator)
		partial := daysBetween(cursor, p.due)
		whole := daysBetween(cursor, fullPeriodDate)
		// The division is the ONLY MathContext-rounded step; the addition of the
		// whole-period count is EXACT [:1451-1454].
		ratio := roundSignificant(new(big.Rat).Quo(ratInt64(partial), ratInt64(whole)), m.precision)
		return ratio.Add(ratio, ratInt64(multiplicator))
	}
	return ratInt64(multiplicator - months - 1)
}

// periodRatioSeed is calculateSeedDate [VERIFIED:
// ProgressiveEMICalculator.java:1461-1481]: the SCHEDULE START if the period's
// window lies exactly on the schedule-start lattice, otherwise the period's own
// from-date. BOTH conjuncts are required.
func (m *scheduleModel) periodRatioSeed(p *repaymentPeriod) civilDate {
	seed := m.startDate()
	multiplicator := int64(1)
	var calculated civilDate
	for {
		calculated = plusMonths(seed, multiplicator)
		multiplicator++
		if compareDates(calculated, p.due) >= 0 {
			break
		}
	}
	if compareDates(calculated, p.due) == 0 &&
		compareDates(plusMonths(calculated, -m.repaymentEvery), p.from) == 0 {
		return seed
	}
	return p.from
}

// ---------------------------------------------------------------------------
// The level installment
// ---------------------------------------------------------------------------

// calculateLevelInstallment is
// calculateEMIOnActualModelWithDecliningBalanceInterestMethod
// [VERIFIED: ProgressiveEMICalculator.java:1722-1741].
//
//	rateFactorN = product over the RELATED periods of their growth factors
//	fn          = fold over the related periods AFTER THE FIRST of
//	              fn' = 1 + fn * growth
//	EMI         = rateFactorN * openingBalance / fn
//
// Every one of those multiplications, divisions and additions is
// MathContext-qualified, INCLUDING the first product against BigDecimal.ONE: a
// growth factor is 1 plus a quantity of 19 decimal places, so it carries 20
// significant digits and the very first rounding is not a no-op.
//
// The installment is written onto the RELATED periods only. Rows before the
// first related period keep a ZERO installment and produce an all-zero row.
func (m *scheduleModel) calculateLevelInstallment(related []*repaymentPeriod) {
	if len(related) == 0 {
		return
	}
	rateFactorN := big.NewRat(1, 1)
	for _, p := range related {
		rateFactorN = roundSignificant(new(big.Rat).Mul(rateFactorN, m.growthFactor(p)), m.precision)
	}
	fn := big.NewRat(1, 1)
	for i, p := range related {
		if i == 0 {
			continue
		}
		product := roundSignificant(new(big.Rat).Mul(fn, m.growthFactor(p)), m.precision)
		fn = roundSignificant(product.Add(product, big.NewRat(1, 1)), m.precision)
	}
	balance := majorFromMinor(m.initialBalanceMinor(related[0]), m.minorDigits)
	numerator := roundSignificant(new(big.Rat).Mul(rateFactorN, balance), m.precision)
	installment := roundSignificant(new(big.Rat).Quo(numerator, fn), m.precision)
	emi := minorFromMajor(installment, m.minorDigits)
	for _, p := range related {
		if emi >= 0 {
			p.emiMinor = emi
		}
	}
}

// applyFinalPeriodResidual is calculateLastUnpaidRepaymentPeriodEMI
// [VERIFIED: ProgressiveEMICalculator.java:1160-1219].
//
// THE FINAL ROW'S INSTALLMENT IS NOT THE LEVEL INSTALLMENT. It absorbs the whole
// residual, so its principal is the WHOLE REMAINING BALANCE rather than
// installment minus interest, and the schedule amortizes to exactly zero.
func (m *scheduleModel) applyFinalPeriodResidual(depth int) {
	if depth > len(m.periods)+2 {
		return
	}

	// The oracle's guard at :1163-1174. totalDuePrincipal is the sum of the
	// periods' CREDITED AMOUNTS -- every disbursement, not the due principal
	// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:347-348 ->
	// RepaymentPeriod.getCreditedAmounts, :375-377]. Ported rather than dropped:
	// it is provably inert on an unpaid schedule and dropping a step because it
	// looks inert is how the two money defects of this program's first run
	// survived review.
	var totalDuePaidDiff int64
	for _, p := range m.periods {
		for _, s := range p.segments {
			totalDuePaidDiff += s.disbursedMinor
		}
	}
	for _, p := range m.periods {
		outstanding := m.duePrincipalMinor(p)
		if outstanding > totalDuePaidDiff {
			p.emiMinor -= outstanding - totalDuePaidDiff
			if p.emiMinor < 0 {
				p.emiMinor = 0
			}
		}
	}

	idx := m.findLastUnpaidPeriod()
	if idx < 0 {
		return
	}

	var totalDueInterest, totalEMI, totalDisbursed int64
	for _, p := range m.periods {
		totalDueInterest += m.dueInterestMinor(p)
		totalEMI += p.emiMinor
		for _, s := range p.segments {
			totalDisbursed += s.disbursedMinor
		}
	}
	m.periods[idx].emiMinor += totalDisbursed + totalDueInterest - totalEMI
	if m.periods[idx].emiMinor < 0 {
		m.periods[idx].emiMinor = 0
		m.applyFinalPeriodResidual(depth + 1)
	}
}

// findLastUnpaidPeriod: the last period that is not fully paid, which on an
// untouched schedule means the last with a non-zero installment
// [VERIFIED: ProgressiveEMICalculator.java:1176-1181; isFullyPaid compares the
// installment against the total paid, RepaymentPeriod.java:361-363]. The fallback
// at :1178-1180 applies when every installment is zero.
func (m *scheduleModel) findLastUnpaidPeriod() int {
	for i := len(m.periods) - 1; i >= 0; i-- {
		if m.periods[i].emiMinor != 0 {
			return i
		}
	}
	for i := len(m.periods) - 1; i >= 0; i-- {
		if len(m.periods[i].segments) > 0 && m.outstandingLoanBalanceMinor(m.periods[i]) > 0 {
			return i
		}
	}
	return -1
}

// ---------------------------------------------------------------------------
// The EMI re-adjust smoothing loop
// ---------------------------------------------------------------------------

// emiAdjustment is getEmiAdjustment
// [VERIFIED: ProgressiveEMICalculator.java:1778-1789]: it scans from the END for
// the last ADJACENT pair in which NEITHER period is fully paid, and the scan
// requires idx > 0, so a single-element list falls to the degenerate branch whose
// difference is zero.
func emiAdjustment(list []*repaymentPeriod) (original, difference int64) {
	for idx := len(list) - 1; idx > 0; idx-- {
		last, penultimate := list[idx], list[idx-1]
		if last.emiMinor != 0 && penultimate.emiMinor != 0 {
			return penultimate.emiMinor, last.emiMinor - penultimate.emiMinor
		}
	}
	if len(list) == 0 {
		return 0, 0
	}
	return list[0].emiMinor, 0
}

// shouldBeAdjusted is EmiAdjustment.shouldBeAdjusted
// [VERIFIED: EmiAdjustment.java:31-36]. ALL THREE conjuncts are required.
//
// Money.copy(double) REPLACES the amount rather than scaling it
// [VERIFIED: Money.java:219-222], so the threshold is floor(n/2) whole currency
// units flat and the guard has no dependence on installment rounding. In minor
// units the comparison is |difference| * 100 against floor(n/2) * 10^minorDigits,
// and both sides are exact integers -- the doubles in the Java are an artefact of
// the reference implementation and are NOT reproduced.
func shouldBeAdjusted(n int, original, difference int64, minorDigits int32) bool {
	lowerHalf := int64(n / 2)
	if lowerHalf <= 0 || difference == 0 {
		return false
	}
	threshold := new(big.Int).Mul(big.NewInt(lowerHalf), pow10(minorDigits))
	left := new(big.Int).Mul(big.NewInt(absInt64(difference)), big.NewInt(100))
	return left.Cmp(threshold) > 0
}

// adjustEMIIfNeeded is checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods
// [VERIFIED: ProgressiveEMICalculator.java:1258-1308].
//
// It runs on EVERY ordinary generation, not only when installment rounding is
// configured, and it moves money on ordinary loans. Five things it is easy to get
// wrong, each of which changes the schedule returned:
//
//   - THE DIVISOR IS n, the RELATED-period count, so the gap is spread across the
//     related periods rather than absorbed whole.
//   - THE TRIAL IS A REBUILD on a copy, not a patch: balances are recomputed and
//     the final-period residual re-applied before the trial is judged.
//   - THE ADOPTION TEST IS STRICT and its failure DISCARDS the trial, leaving the
//     live schedule at its pre-trial values. Equality is not adoption.
//   - break MEANS STOP. All four exits terminate the loop.
//   - THE COUNTER ADVANCES ONLY ON ADOPTION, and bounds the loop at three.
func (m *scheduleModel) adjustEMIIfNeeded(related []*repaymentPeriod) {
	if len(related) == 0 {
		return
	}
	adjustCounter := 1
	for {
		original, difference := emiAdjustment(related)
		if !shouldBeAdjusted(len(related), original, difference, m.minorDigits) {
			return
		}
		// uncountablePeriods counts periods whose total paid exceeds the original
		// installment [VERIFIED: :2027-2031]; it is identically zero on a schedule
		// this contract generates, and the divisor is therefore n.
		divisor := maxInt64(1, int64(len(related)))
		adjusted := original + divideMinorHalfUp(difference, divisor)
		// applyInstallmentAmountInMultiplesOf is the identity inside the graded
		// domain, where InstallmentRoundingMultipleMinor is 0 [:1270 -> :1761-1766].
		if adjusted == original {
			return
		}

		trial := m.deepCopy()
		firstFrom, firstDue := related[0].from, related[0].due
		for _, p := range trial.periods {
			if compareDates(p.from, firstFrom) >= 0 && compareDates(p.due, firstDue) >= 0 && adjusted >= 0 {
				p.emiMinor = adjusted
			}
		}
		trial.updateOutstandingBalances()
		trial.applyFinalPeriodResidual(0)

		// The adoption test re-measures over the trial's FULL period list, not the
		// related sublist [:1289]; only the magnitude of the difference is read, so
		// the differing list does not matter.
		_, newDifference := emiAdjustment(trial.periods)
		if !(absInt64(newDifference) < absInt64(difference)) {
			return
		}

		var trialRelated []*repaymentPeriod
		for _, p := range trial.periods {
			if compareDates(p.from, firstFrom) >= 0 && compareDates(p.due, firstDue) >= 0 {
				trialRelated = append(trialRelated, p)
			}
		}
		for i, p := range related {
			if i >= len(trialRelated) {
				break
			}
			p.emiMinor = trialRelated[i].emiMinor
		}
		m.updateOutstandingBalances()

		adjustCounter++
		if adjustCounter > 3 {
			return
		}
	}
}
