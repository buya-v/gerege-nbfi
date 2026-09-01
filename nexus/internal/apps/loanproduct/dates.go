package loanproduct

import "time"

// This file carries the proleptic-Gregorian calendar arithmetic the rate-factor
// recomputation needs. The schedule generator in nexus/internal/apps/loanschedule
// already owns an identical set of helpers on its own civilDate type; they are
// duplicated here (not imported) because the two packages use different date
// carriers and this package must not depend on the generator's private types.
// Every rule below matches java.time.LocalDate, not time.Time's wall-clock
// semantics, because the oracle's schedule arithmetic is date-only.

func isLeapYear(y int) bool { return y%4 == 0 && (y%100 != 0 || y%400 == 0) }

func daysInMonthOf(y int, mo time.Month) int {
	switch mo {
	case time.January, time.March, time.May, time.July, time.August, time.October, time.December:
		return 31
	case time.April, time.June, time.September, time.November:
		return 30
	case time.February:
		if isLeapYear(y) {
			return 29
		}
		return 28
	}
	return 0
}

// lengthOfYear matches LocalDate.lengthOfYear: 366 for a leap year, 365
// otherwise [VERIFIED: java.time.LocalDate.lengthOfYear].
func lengthOfYear(t time.Time) int {
	if isLeapYear(t.Year()) {
		return 366
	}
	return 365
}

// compareDates is the proleptic-Gregorian date ordering, matching LocalDate
// comparison (year, then month, then day).
func compareDates(a, b time.Time) int {
	a = dateOnly(a)
	b = dateOnly(b)
	switch {
	case a.Before(b):
		return -1
	case a.After(b):
		return 1
	default:
		return 0
	}
}

func plusDays(d time.Time, n int) time.Time {
	return dateOnly(d).AddDate(0, 0, n)
}

// plusMonths matches LocalDate.plusMonths: the day is CLAMPED into the target
// month, so 31 January plus one month is 28 or 29 February.
func plusMonths(d time.Time, n int) time.Time {
	d = dateOnly(d)
	months := d.Year()*12 + int(d.Month()) - 1 + n
	year := floorDivInt(months, 12)
	month := time.Month(floorModInt(months, 12) + 1)
	day := d.Day()
	if limit := daysInMonthOf(year, month); day > limit {
		day = limit
	}
	return time.Date(year, month, day, 0, 0, 0, 0, time.UTC)
}

// floorDivInt and floorModInt round toward negative infinity, as java.lang.Math
// does for its floorDiv/floorMod.
func floorDivInt(a, b int) int {
	q := a / b
	if (a%b != 0) && ((a < 0) != (b < 0)) {
		q--
	}
	return q
}

func floorModInt(a, b int) int { return a - floorDivInt(a, b)*b }

// monthsBetween is ChronoUnit.MONTHS.between (LocalDate.monthsUntil): each date
// is PACKED as (proleptic month)*32 + day-of-month and the difference is divided
// by 32, truncated toward zero. See nexus/internal/apps/loanschedule for the
// proof that this is not the same as "largest k with a + k months <= b".
func monthsBetween(a, b time.Time) int {
	a = dateOnly(a)
	b = dateOnly(b)
	packedA := (a.Year()*12+int(a.Month())-1)*32 + a.Day()
	packedB := (b.Year()*12+int(b.Month())-1)*32 + b.Day()
	return (packedB - packedA) / 32
}

// isAfterInclusive reproduces DateUtils.isAfterInclusive(first, second)
// [VERIFIED: DateUtils.java:304-306]: first is after second, or the two are
// equal. Both arguments are non-null civil dates on every reachable path.
func isAfterInclusive(a, b time.Time) bool {
	return compareDates(a, b) >= 0
}

// isDateInRangeInclusive reproduces DateUtils.isDateInRangeInclusive
// [VERIFIED: DateUtils.java:407-409]: target is not before from and not after
// to, i.e. from <= target <= to.
func isDateInRangeInclusive(target, from, to time.Time) bool {
	return compareDates(target, from) >= 0 && compareDates(target, to) <= 0
}

// isDateInRangeFromExclusiveToInclusive reproduces
// DateUtils.isDateInRangeFromExclusiveToInclusive
// [VERIFIED: DateUtils.java:415-417]: target is strictly after from and not
// after to, i.e. from < target <= to.
func isDateInRangeFromExclusiveToInclusive(target, from, to time.Time) bool {
	return compareDates(target, from) > 0 && compareDates(target, to) <= 0
}

// isInPeriod reproduces LoanRepaymentScheduleProcessingWrapper.isInPeriod
// [VERIFIED: LoanRepaymentScheduleProcessingWrapper.java:251-254]: the first
// repayment period is inclusive of its from-date; every later period opens
// exclusively on its from-date.
func isInPeriod(target, from, to time.Time, isFirstPeriod bool) bool {
	if isFirstPeriod {
		return isDateInRangeInclusive(target, from, to)
	}
	return isDateInRangeFromExclusiveToInclusive(target, from, to)
}

// exactDifferenceInDays is DateUtils.getExactDifferenceInDays(first, second)
// [VERIFIED: DateUtils.java:323-325]: the day count second - first, expressed
// through ChronoUnit.DAYS.between, which is exactly daysBetween below.
func exactDifferenceInDays(first, second time.Time) int64 {
	return daysBetween(first, second)
}

// exactDifference is DateUtils.getExactDifference(first, second, unit)
// [VERIFIED: DateUtils.java:315-317]. ChronoUnit.DAYS/WEEKS/MONTHS/YEARS are
// the only units the rate-factor recomputation reaches; each is expressed
// through the proleptic-Gregorian integer arithmetic already proven to match
// java.time in nexus/internal/apps/loanschedule.
func exactDifference(first, second time.Time, unit PeriodFrequencyType) int {
	switch unit {
	case PeriodDays:
		return int(exactDifferenceInDays(first, second))
	case PeriodWeeks:
		return int(exactDifferenceInDays(first, second)) / 7
	case PeriodMonths:
		return monthsBetween(first, second)
	case PeriodYears:
		return monthsBetween(first, second) / 12
	default:
		panic("loanproduct: unsupported exact-difference unit: " + unit.String())
	}
}
