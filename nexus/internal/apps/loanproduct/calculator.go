package loanproduct

import (
	"math/big"
	"time"
)

// This file ports the RATE-FACTOR RECOMPUTATION half of Fineract's
// ProgressiveEMICalculator: the arithmetic that rewrites the rateFactor and
// rateFactorTillPeriodDueDate cells of an ALREADY-BUILT schedule after a
// disbursement, balance correction, capitalized-income or interest-rate change.
//
// It is the recomputation counterpart of nexus/internal/apps/loanschedule, whose
// generator builds a schedule from scratch and is graded correct against the
// reference oracle under DEC-1. The two packages share one arithmetic kernel:
// every monetary quantity is an exact rational, every BigDecimal op qualified by
// MathContext(precision, mode) becomes roundSignificant, and every
// BigDecimal.setScale(precision, mode) becomes roundScale. The recomputation
// oracle sets both from the SAME MathContext precision, which is the
// graded-domain invariant (SignificantDigits == RateFactorScale) under which
// the two packages must agree.
//
// Line cites are against ProgressiveEMICalculator.java at the pinned commit.

func ratInt64(n int64) *big.Rat { return new(big.Rat).SetInt64(n) }
func ratOne() *big.Rat          { return big.NewRat(1, 1) }

// calcNominalInterestRatePercentage converts a percent rate into a fraction of
// one: nullToZero(rate).divide(100, mc) [VERIFIED:
// ProgressiveEMICalculator.java:1319].
func calcNominalInterestRatePercentage(rate *big.Rat, r Rounding) *big.Rat {
	return roundSignificant(new(big.Rat).Quo(rate, ratInt64(100)), r.Precision, r.Mode)
}

// CalculateRateFactorForPeriods recomputes the rate factors of every supplied
// repayment period [VERIFIED: ProgressiveEMICalculator.java:1325-1327].
func CalculateRateFactorForPeriods(periods []*RepaymentPeriod, m *ScheduleModel) {
	for _, rp := range periods {
		CalculateRateFactorForRepaymentPeriod(rp, m)
	}
}

// CalculateRateFactorForRepaymentPeriod rewrites both rate-factor cells of every
// interest-period segment in rp [VERIFIED: ProgressiveEMICalculator.java:636-644].
func CalculateRateFactorForRepaymentPeriod(rp *RepaymentPeriod, m *ScheduleModel) {
	for _, ip := range rp.InterestPeriods {
		ip.SetRateFactor(calculateRateFactorPerPeriod(m, rp, ip.FromDate, ip.DueDate))
		ip.SetRateFactorTillPeriodDueDate(calculateRateFactorPerPeriodForInterest(m, rp, ip.FromDate, rp.DueDate))
	}
}

// CalculateOutstandingBalance rolls the outstanding balance forward through
// every segment of every period [VERIFIED: ProgressiveEMICalculator.java:1254-1256].
func CalculateOutstandingBalance(m *ScheduleModel) {
	for _, rp := range m.RepaymentPeriods() {
		for _, ip := range rp.InterestPeriods {
			ip.UpdateOutstandingLoanBalance()
		}
	}
}

// daysInYearNumberOfDays reproduces DaysInYearType.getNumberOfDays
// [VERIFIED: DaysInYearType.java:95-100]: ACTUAL returns the reference date's
// year length; every fixed convention returns its literal stored day count.
func daysInYearNumberOfDays(d DaysInYearType, ref time.Time) int64 {
	if d == DaysInYearActual {
		return int64(lengthOfYear(ref))
	}
	return int64(d.StoredValue())
}

// isPeriodContainsFeb29 reports whether any 29 February of a leap year inside
// the span falls strictly after the from-date and on or before the due-date
// [VERIFIED: ProgressiveEMICalculator.java:1336-1345].
func isPeriodContainsFeb29(from, due time.Time) bool {
	for year := from.Year(); year <= due.Year(); year++ {
		if isLeapYear(year) {
			leapDay := time.Date(year, time.February, 29, 0, 0, 0, 0, time.UTC)
			if isDateInRangeFromExclusiveToInclusive(leapDay, from, due) {
				return true
			}
		}
	}
	return false
}

// numberOfDaysFeb29PeriodOnly returns 366 when the period contains 29 February,
// else 365 [VERIFIED: ProgressiveEMICalculator.java:1347-1349].
func numberOfDaysFeb29PeriodOnly(from, due time.Time) int64 {
	if isPeriodContainsFeb29(from, due) {
		return 366
	}
	return 365
}

// getNumberOfDays resolves the days-in-year denominator, overriding a 366-day
// ACTUAL year with the FEB_29_PERIOD_ONLY convention when that strategy is set
// [VERIFIED: ProgressiveEMICalculator.java:1351-1357].
func getNumberOfDays(daysInYearType DaysInYearType, customStrategy DaysInYearCustomStrategy,
	interestFrom, rpFrom, rpDue time.Time) int64 {
	numberOfDays := daysInYearNumberOfDays(daysInYearType, interestFrom)
	if numberOfDays == 366 && customStrategy.IsFeb29PeriodOnly() {
		numberOfDays = numberOfDaysFeb29PeriodOnly(rpFrom, rpDue)
	}
	return numberOfDays
}

// calculateRateFactorPerPeriod is the recurrence rate factor of one segment
// [VERIFIED: ProgressiveEMICalculator.java:1471-1541].
func calculateRateFactorPerPeriod(m *ScheduleModel, rp *RepaymentPeriod, interestFrom, interestDue time.Time) *big.Rat {
	detail := m.detail
	r := m.rounding
	interestRate := calcNominalInterestRatePercentage(m.GetInterestRate(interestFrom), r)
	daysInYearType := detail.GetDaysInYearType()
	daysInMonthType := detail.DaysInMonthType
	repaymentFrequency := detail.RepaymentPeriodFrequencyType
	repaymentEvery := ratInt64(int64(detail.RepayEvery))
	daysInYearCustomStrategy := detail.DaysInYearCustomStrategy

	daysInYear := getNumberOfDays(daysInYearType, daysInYearCustomStrategy, interestFrom, rp.FromDate, rp.DueDate)
	actualDays := daysBetween(interestFrom, interestDue)
	calculatedDays := daysBetween(rp.FromDate, rp.DueDate)
	numberOfYearsDifference := interestDue.Year() - interestFrom.Year()
	partialPeriodNeeded := daysInYearType == DaysInYearActual && numberOfYearsDifference > 0 &&
		(!daysInYearCustomStrategy.IsFeb29PeriodOnly() || isPeriodContainsFeb29(rp.FromDate, rp.DueDate))

	if detail.InterestCalculationPeriodMethod.IsSameAsRepaymentPeriod() {
		if repaymentFrequency.IsMonthly() {
			return rateFactorByRepaymentPeriod(interestRate, ratOne(), repaymentEvery, 12, actualDays, calculatedDays, r)
		}
		if repaymentFrequency.IsWeekly() {
			return rateFactorByRepaymentPeriod(interestRate, ratOne(), repaymentEvery, 52, actualDays, calculatedDays, r)
		}
	}

	if partialPeriodNeeded {
		cumulatedPeriodFractions := calculatePeriodFractions(m, interestFrom, interestDue)
		return rateFactorByRepaymentPartialPeriod(interestRate, ratOne(), cumulatedPeriodFractions, ratOne(), ratOne(), r)
	}

	switch daysInMonthType {
	case DaysInMonthActual:
		return rateFactorByRepaymentPeriod(interestRate, ratInt64(actualDays), ratOne(), daysInYear, 1, 1, r)
	case DaysInMonth30:
		daysInMonth := ratInt64(30)
		if !daysInMonthType.IsDaysInMonth30() {
			daysInMonth = ratInt64(calculatedDays)
		}
		return calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate, repaymentFrequency, repaymentEvery,
			daysInMonth, daysInYear, actualDays, calculatedDays, r)
	default:
		panic("loanproduct: unsupported days-in-month type: " + daysInMonthType.String())
	}
}

// calculateRateFactorPerPeriodForInterest is the interest rate factor of one
// segment, measured from the segment's from-date to the ENCLOSING repayment
// period's due date [VERIFIED: ProgressiveEMICalculator.java:1360-1418].
func calculateRateFactorPerPeriodForInterest(m *ScheduleModel, rp *RepaymentPeriod, interestFrom, interestDue time.Time) *big.Rat {
	detail := m.detail
	r := m.rounding
	interestRate := calcNominalInterestRatePercentage(m.GetInterestRate(interestFrom), r)
	daysInYearType := detail.GetDaysInYearType()
	daysInMonthType := detail.DaysInMonthType
	repaymentFrequency := detail.RepaymentPeriodFrequencyType
	repaymentEvery := ratInt64(int64(detail.RepayEvery))
	daysInYearCustomStrategy := detail.DaysInYearCustomStrategy

	daysInYear := getNumberOfDays(daysInYearType, daysInYearCustomStrategy, interestFrom, rp.FromDate, rp.DueDate)
	actualDays := daysBetween(interestFrom, interestDue)
	calculatedDays := daysBetween(rp.FromDate, rp.DueDate)
	numberOfYearsDifference := interestDue.Year() - interestFrom.Year()
	partialPeriodNeeded := daysInYearType == DaysInYearActual && numberOfYearsDifference > 0 &&
		(!daysInYearCustomStrategy.IsFeb29PeriodOnly() || isPeriodContainsFeb29(rp.FromDate, rp.DueDate))

	if detail.InterestCalculationPeriodMethod.IsSameAsRepaymentPeriod() {
		if repaymentFrequency.IsMonthly() {
			return rateFactorByRepaymentPeriod(interestRate, ratOne(), repaymentEvery, 12, actualDays, calculatedDays, r)
		}
		if repaymentFrequency.IsWeekly() {
			return rateFactorByRepaymentPeriod(interestRate, ratOne(), repaymentEvery, 52, actualDays, calculatedDays, r)
		}
	}

	if partialPeriodNeeded {
		cumulatedPeriodFractions := calculatePeriodFractions(m, interestFrom, interestDue)
		return rateFactorByRepaymentPartialPeriod(interestRate, ratOne(), cumulatedPeriodFractions, ratOne(), ratOne(), r)
	}

	switch daysInMonthType {
	case DaysInMonthActual:
		return rateFactorByRepaymentPeriod(interestRate, ratInt64(actualDays), ratOne(), daysInYear, 1, 1, r)
	case DaysInMonth30:
		periodRatio := calculatePeriodRatio(m, rp, repaymentFrequency, r)
		return calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate, repaymentFrequency, periodRatio,
			ratInt64(30), daysInYear, actualDays, calculatedDays, r)
	default:
		panic("loanproduct: unsupported days-in-month type: " + daysInMonthType.String())
	}
}

// calculateRateFactorPerPeriodBasedOnRepaymentFrequency dispatches the
// DAYS_30 recurrence arm by repayment frequency
// [VERIFIED: ProgressiveEMICalculator.java:1600-1610].
func calculateRateFactorPerPeriodBasedOnRepaymentFrequency(rate *big.Rat, repaymentFrequency PeriodFrequencyType,
	repaymentEvery, daysInMonth *big.Rat, daysInYear int64, actualDays, calculatedDays int64, r Rounding) *big.Rat {
	switch repaymentFrequency {
	case PeriodDays:
		return rateFactorByRepaymentEveryDay(rate, repaymentEvery, daysInYear, actualDays, calculatedDays, r)
	case PeriodWeeks:
		return rateFactorByRepaymentEveryWeek(rate, repaymentEvery, daysInYear, actualDays, calculatedDays, r)
	case PeriodMonths:
		return rateFactorByRepaymentEveryMonth(rate, repaymentEvery, daysInMonth, daysInYear, actualDays, calculatedDays, r)
	default:
		panic("loanproduct: invalid repayment frequency: " + repaymentFrequency.String())
	}
}

func rateFactorByRepaymentEveryDay(rate, repaymentEvery *big.Rat, daysInYear int64, actualDays, calculatedDays int64,
	r Rounding) *big.Rat {
	return rateFactorByRepaymentPeriod(rate, ratOne(), repaymentEvery, daysInYear, actualDays, calculatedDays, r)
}

func rateFactorByRepaymentEveryWeek(rate, repaymentEvery *big.Rat, daysInYear int64, actualDays, calculatedDays int64,
	r Rounding) *big.Rat {
	return rateFactorByRepaymentPeriod(rate, ratInt64(7), repaymentEvery, daysInYear, actualDays, calculatedDays, r)
}

func rateFactorByRepaymentEveryMonth(rate, repaymentEvery, daysInMonth *big.Rat, daysInYear int64, actualDays, calculatedDays int64,
	r Rounding) *big.Rat {
	return rateFactorByRepaymentPeriod(rate, daysInMonth, repaymentEvery, daysInYear, actualDays, calculatedDays, r)
}

// rateFactorByRepaymentPeriod is the shared rate-factor kernel
// [VERIFIED: ProgressiveEMICalculator.java:1950-1962].
//
//	interestFractionPerPeriod = multiplierInDays * repaymentEvery / daysInYear
//	factor = rate * interestFractionPerPeriod * actualDays / calculatedDays
//	         then setScale(precision, mode)
//
// Every multiplication and division is MathContext-qualified (roundSignificant),
// and the trailing setScale is a scale (roundScale), matching the source.
func rateFactorByRepaymentPeriod(rate, multiplierInDays, repaymentEvery *big.Rat, daysInYear int64, actualDays, calculatedDays int64,
	r Rounding) *big.Rat {
	if calculatedDays == 0 {
		return new(big.Rat)
	}
	interestFraction := roundSignificant(new(big.Rat).Mul(multiplierInDays, repaymentEvery), r.Precision, r.Mode)
	interestFraction = roundSignificant(new(big.Rat).Quo(interestFraction, ratInt64(daysInYear)), r.Precision, r.Mode)

	v := roundSignificant(new(big.Rat).Mul(rate, interestFraction), r.Precision, r.Mode)
	v = roundSignificant(new(big.Rat).Mul(v, ratInt64(actualDays)), r.Precision, r.Mode)
	v = roundSignificant(new(big.Rat).Quo(v, ratInt64(calculatedDays)), r.Precision, r.Mode)
	return roundScale(v, r.Precision, r.Mode)
}

// rateFactorByRepaymentPartialPeriod computes a partial-period rate factor; the
// interest fraction is repaymentEvery * cumulatedPeriodRatio with NO
// MathContext (exact), then the same rate * fraction * actual / calculated chain
// as the exact-period kernel [VERIFIED: ProgressiveEMICalculator.java:1969-1979].
func rateFactorByRepaymentPartialPeriod(rate, repaymentEvery, cumulatedPeriodRatio, actualDays, calculatedDays *big.Rat,
	r Rounding) *big.Rat {
	if calculatedDays.Sign() == 0 {
		return new(big.Rat)
	}
	interestFraction := new(big.Rat).Mul(repaymentEvery, cumulatedPeriodRatio)

	v := roundSignificant(new(big.Rat).Mul(rate, interestFraction), r.Precision, r.Mode)
	v = roundSignificant(new(big.Rat).Mul(v, actualDays), r.Precision, r.Mode)
	v = roundSignificant(new(big.Rat).Quo(v, calculatedDays), r.Precision, r.Mode)
	return roundScale(v, r.Precision, r.Mode)
}

// calculatePeriodFractions sums each whole year's fraction of the period under
// the ACTUAL convention, splitting a multi-year span at the year boundary
// [VERIFIED: ProgressiveEMICalculator.java:1547-1565].
func calculatePeriodFractions(m *ScheduleModel, interestFrom, interestDue time.Time) *big.Rat {
	r := m.rounding
	cumulated := new(big.Rat)
	actualYear := interestFrom.Year()
	endYear := interestDue.Year()
	actualDate := interestFrom

	for actualYear <= endYear {
		fractionPeriodDueDate := interestDue
		if actualYear != endYear {
			fractionPeriodDueDate = getFractionPeriodDueDateForEndOfYear(m, actualYear)
		}
		numberOfDaysInYear := int64(lengthOfYear(time.Date(actualYear, time.January, 1, 0, 0, 0, 0, time.UTC)))
		calculatedDaysInActualYear := daysBetween(actualDate, fractionPeriodDueDate)
		fraction := roundSignificant(new(big.Rat).Quo(ratInt64(calculatedDaysInActualYear), ratInt64(numberOfDaysInYear)),
			r.Precision, r.Mode)
		cumulated = roundSignificant(new(big.Rat).Add(cumulated, fraction), r.Precision, r.Mode)
		actualDate = fractionPeriodDueDate
		actualYear++
	}
	return cumulated
}

// getFractionPeriodDueDateForEndOfYear returns the year boundary used to split a
// partial ACTUAL period [VERIFIED: ProgressiveEMICalculator.java:1575-1584].
func getFractionPeriodDueDateForEndOfYear(m *ScheduleModel, year int) time.Time {
	if m.detail.InterestRecognitionOnDisbursementDate {
		return time.Date(year+1, time.January, 1, 0, 0, 0, 0, time.UTC)
	}
	return time.Date(year, time.December, 31, 0, 0, 0, 0, time.UTC)
}

// calculateSeedDate picks the anchor date the period-ratio walk counts from
// [VERIFIED: ProgressiveEMICalculator.java:1446-1469].
func calculateSeedDate(m *ScheduleModel, rp *RepaymentPeriod) time.Time {
	seedDate := m.StartDate()
	unit := m.detail.RepaymentPeriodFrequencyType
	multiplicator := 1
	var calculated time.Time
	for {
		calculated = plusPeriods(seedDate, multiplicator, unit)
		multiplicator++
		if compareDates(calculated, rp.DueDate) >= 0 {
			break
		}
	}
	if compareDates(calculated, rp.DueDate) == 0 &&
		compareDates(plusPeriods(calculated, -m.detail.RepayEvery, unit), rp.FromDate) == 0 {
		return seedDate
	}
	return rp.FromDate
}

// calculatePeriodRatio measures the number of whole repayment periods between
// the seed date and the period's from-date, plus any fractional trailing period
// [VERIFIED: ProgressiveEMICalculator.java:1420-1444].
func calculatePeriodRatio(m *ScheduleModel, rp *RepaymentPeriod, unit PeriodFrequencyType, r Rounding) *big.Rat {
	seedDate := calculateSeedDate(m, rp)
	var numberOfPeriods int
	switch unit {
	case PeriodDays, PeriodWeeks, PeriodYears:
		numberOfPeriods = exactDifference(seedDate, rp.FromDate, unit)
	case PeriodMonths:
		seedDay := seedDate.Day()
		targetDay := rp.FromDate.Day()
		targetLastDay := daysInMonthOf(rp.FromDate.Year(), rp.FromDate.Month())
		if targetLastDay == targetDay && seedDay > targetDay {
			numberOfPeriods = exactDifference(seedDate, plusDays(rp.FromDate, 1), unit)
		} else {
			numberOfPeriods = exactDifference(seedDate, rp.FromDate, unit)
		}
	default:
		panic("loanproduct: unsupported period-ratio unit: " + unit.String())
	}

	multiplicator := numberOfPeriods + 1
	fromDate := rp.FromDate
	for compareDates(fromDate, rp.DueDate) < 0 {
		fromDate = plusPeriods(seedDate, multiplicator, unit)
		if compareDates(fromDate, rp.DueDate) <= 0 {
			multiplicator++
		} else {
			fullPeriodDate := fromDate
			multiplicator = multiplicator - numberOfPeriods - 1
			fromDate = plusPeriods(seedDate, multiplicator, unit)
			differenceInDays := daysBetween(fromDate, rp.DueDate)
			fullPeriodDifferenceInDays := daysBetween(fromDate, fullPeriodDate)
			fraction := roundSignificant(new(big.Rat).Quo(ratInt64(differenceInDays), ratInt64(fullPeriodDifferenceInDays)),
				r.Precision, r.Mode)
			return new(big.Rat).Add(fraction, ratInt64(int64(multiplicator)))
		}
	}
	multiplicator = multiplicator - numberOfPeriods - 1
	return ratInt64(int64(multiplicator))
}

// plusPeriods shifts a civil date by n periods of the given unit, matching
// LocalDate.plus(n, ChronoUnit) for YEARS/MONTHS/WEEKS/DAYS.
func plusPeriods(d time.Time, n int, unit PeriodFrequencyType) time.Time {
	switch unit {
	case PeriodYears:
		return plusMonths(d, n*12)
	case PeriodMonths:
		return plusMonths(d, n)
	case PeriodWeeks:
		return plusDays(d, n*7)
	case PeriodDays:
		return plusDays(d, n)
	default:
		panic("loanproduct: unsupported period unit: " + unit.String())
	}
}
