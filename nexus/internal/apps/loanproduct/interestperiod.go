package loanproduct

import (
	"math/big"
	"time"
)

// daysBetween returns the calendar-day difference between two dates using the
// same LocalDate epoch-day arithmetic DateUtils.getDifferenceInDays uses
// [VERIFIED: DateUtils.java:319-321 — DAYS.between(first, second)]. The result
// is second - first, so a span that opens on first and closes on second has a
// positive length.
func daysBetween(first, second time.Time) int64 {
	return int64(dateOnly(second).Sub(dateOnly(first)) / (24 * time.Hour))
}

// dateOnly truncates a time.Time to its calendar date in UTC, matching the
// day-count convention used across the port (see nexus/internal/apps/loan).
func dateOnly(t time.Time) time.Time {
	y, m, d := t.Date()
	return time.Date(y, m, d, 0, 0, 0, 0, time.UTC)
}

// InterestPeriod is the Go port of Fineract's
// portfolio.loanproduct.calc.data.InterestPeriod: one segment of a repayment
// period over which a rate factor, an outstanding balance and the credited
// amounts are carried and recomputed after a transaction.
//
// [VERIFIED: InterestPeriod.java:48-60 for the field list.]
//
// It is the recomputation counterpart of the schedule GENERATOR's interest
// period: the generator in nexus/internal/apps/loanschedule builds a schedule
// from scratch, while this value object recomputes the due-interest, due-
// principal and outstanding-balance cells of an ALREADY-BUILT schedule after a
// repayment, disbursement, charge-back or interest-rate change.
type InterestPeriod struct {
	repaymentPeriod *RepaymentPeriod

	// FromDate and DueDate bound the segment.
	FromDate time.Time
	DueDate  time.Time

	// RateFactor and RateFactorTillPeriodDueDate are the segment's rate
	// factors, carried as exact rationals. A nil value is the oracle's null
	// BigDecimal and reads as zero.
	RateFactor                   *big.Rat
	RateFactorTillPeriodDueDate  *big.Rat

	creditedPrincipal            Money
	creditedInterest             Money
	disbursementAmount           Money
	balanceCorrectionAmount      Money
	outstandingLoanBalance       Money
	capitalizedIncomePrincipal   Money

	rounding Rounding
	currency Currency

	// Paused mirrors InterestPeriod.isPaused.
	Paused bool
}

func (ip *InterestPeriod) zero() Money { return moneyZero(ip.currency, ip.rounding) }

// CreditedPrincipal returns creditedPrincipal, zero when absent
// [VERIFIED: InterestPeriod.java:299-301].
func (ip *InterestPeriod) CreditedPrincipal() Money { return ip.creditedPrincipal }

// CreditedInterest returns creditedInterest, zero when absent
// [VERIFIED: InterestPeriod.java:303-305].
func (ip *InterestPeriod) CreditedInterest() Money { return ip.creditedInterest }

// DisbursementAmount returns disbursementAmount, zero when absent
// [VERIFIED: InterestPeriod.java:307-309].
func (ip *InterestPeriod) DisbursementAmount() Money { return ip.disbursementAmount }

// BalanceCorrectionAmount returns balanceCorrectionAmount, zero when absent
// [VERIFIED: InterestPeriod.java:311-313].
func (ip *InterestPeriod) BalanceCorrectionAmount() Money { return ip.balanceCorrectionAmount }

// OutstandingLoanBalance returns outstandingLoanBalance, zero when absent
// [VERIFIED: InterestPeriod.java:315-317].
func (ip *InterestPeriod) OutstandingLoanBalance() Money { return ip.outstandingLoanBalance }

// CapitalizedIncomePrincipal returns capitalizedIncomePrincipal, zero when absent
// [VERIFIED: InterestPeriod.java:319-321].
func (ip *InterestPeriod) CapitalizedIncomePrincipal() Money { return ip.capitalizedIncomePrincipal }

// RateFactorValue returns the segment's own rate factor, zero when null
// [VERIFIED: InterestPeriod.java:323-325].
func (ip *InterestPeriod) RateFactorValue() *big.Rat {
	if ip.RateFactor == nil {
		return new(big.Rat)
	}
	return ip.RateFactor
}

// RateFactorTillPeriodDueDateValue returns the rate factor measured to the
// enclosing repayment period's due date, zero when null
// [VERIFIED: InterestPeriod.java:327-329].
func (ip *InterestPeriod) RateFactorTillPeriodDueDateValue() *big.Rat {
	if ip.RateFactorTillPeriodDueDate == nil {
		return new(big.Rat)
	}
	return ip.RateFactorTillPeriodDueDate
}

// Length returns the segment length in days [VERIFIED: InterestPeriod.java:229-231].
func (ip *InterestPeriod) Length() int64 {
	return daysBetween(ip.FromDate, ip.DueDate)
}

// LengthTillPeriodDueDate returns the day span from the segment's from-date to
// the ENCLOSING repayment period's due date [VERIFIED: InterestPeriod.java:233-235].
func (ip *InterestPeriod) LengthTillPeriodDueDate() int64 {
	return daysBetween(ip.FromDate, ip.repaymentPeriod.DueDate)
}

// IsFirstInterestPeriod reports whether this is the repayment period's first
// interest period [VERIFIED: InterestPeriod.java:252-254].
func (ip *InterestPeriod) IsFirstInterestPeriod() bool {
	return ip == ip.repaymentPeriod.FirstInterestPeriod()
}

// CalculatedDueInterest returns the raw due-interest for the segment before it
// is wrapped in Money, following the oracle's getCalculatedDueInterest
// [VERIFIED: InterestPeriod.java:193-201]. A paused or re-aged period returns
// its credited interest unchanged; otherwise the credited interest is added to
// the period's interest due at the repayment due date and floored at zero.
func (ip *InterestPeriod) CalculatedDueInterest() *big.Rat {
	if ip.Paused || ip.repaymentPeriod.ReAged {
		return ip.CreditedInterest().major()
	}
	lengthTill := ip.LengthTillPeriodDueDate()
	interestDueTillRepaymentDueDate := ip.CalculatedDueInterestFor(
		ip.repaymentPeriod.InterestMethod(), lengthTill)
	return ratNegativeToZero(roundSignificant(
		new(big.Rat).Add(ip.CreditedInterest().major(), interestDueTillRepaymentDueDate),
		ip.rounding.Precision, ip.rounding.Mode))
}

// CalculatedDueInterestFor is getCalculatedDueInterest(method, lengthTillPeriodDueDate)
// [VERIFIED: InterestPeriod.java:203-219]: the three separately
// MathContext-rounded operations that turn the base amount into interest.
//
//	baseAmount * rateFactorTillPeriodDueDate / lengthTill * length
//
// A zero lengthTill returns exactly zero before any operation runs. FLAT reads
// the disbursed-and-capitalized total; DECLINING_BALANCE reads the outstanding
// balance.
func (ip *InterestPeriod) CalculatedDueInterestFor(method InterestMethod, lengthTillPeriodDueDate int64) *big.Rat {
	if lengthTillPeriodDueDate == 0 {
		return new(big.Rat)
	}
	var baseAmount *big.Rat
	switch method {
	case InterestFlat:
		baseAmount = ip.repaymentPeriod.
			calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod(ip).major()
	case InterestDecliningBalance:
		baseAmount = ip.OutstandingLoanBalance().major()
	default:
		panic("loanproduct: method not implemented: " + method.String())
	}

	v := roundSignificant(new(big.Rat).Mul(baseAmount, ip.RateFactorTillPeriodDueDateValue()),
		ip.rounding.Precision, ip.rounding.Mode)
	v = roundSignificant(new(big.Rat).Quo(v, new(big.Rat).SetInt64(lengthTillPeriodDueDate)),
		ip.rounding.Precision, ip.rounding.Mode)
	return roundSignificant(new(big.Rat).Mul(v, new(big.Rat).SetInt64(ip.Length())),
		ip.rounding.Precision, ip.rounding.Mode)
}

// ratNegativeToZero is MathUtil.negativeToZero over a bare BigDecimal: a value
// that is not greater than zero becomes ZERO [VERIFIED: MathUtil.java:175-178].
func ratNegativeToZero(x *big.Rat) *big.Rat {
	if x.Sign() <= 0 {
		return new(big.Rat)
	}
	return x
}

// UpdateOutstandingLoanBalance rolls the previous segment's (or previous
// repayment period's) balance forward into this segment
// [VERIFIED: InterestPeriod.java:237-250].
//
// The first segment of a period seeds its balance from the previous period's
// last segment, subtracting the previous period's due principal and adding back
// its paid principal; a later segment seeds from the immediately preceding
// segment in the same period.
func (ip *InterestPeriod) UpdateOutstandingLoanBalance() {
	if ip.IsFirstInterestPeriod() {
		previous := ip.repaymentPeriod.Previous()
		if previous != nil {
			previousInterestPeriod := previous.LastInterestPeriod()
			ip.outstandingLoanBalance = previousInterestPeriod.OutstandingLoanBalance().
				plus(previousInterestPeriod.DisbursementAmount()).
				plus(previousInterestPeriod.CapitalizedIncomePrincipal()).
				plus(previousInterestPeriod.BalanceCorrectionAmount()).
				minus(previous.DuePrincipal()).
				plus(previous.PaidPrincipal()).negToZero()
		}
		return
	}
	index := ip.repaymentPeriod.interestPeriodIndex(ip)
	previousInterestPeriod := ip.repaymentPeriod.InterestPeriods[index-1]
	ip.outstandingLoanBalance = previousInterestPeriod.OutstandingLoanBalance().
		plus(previousInterestPeriod.BalanceCorrectionAmount()).
		plus(previousInterestPeriod.CapitalizedIncomePrincipal()).
		plus(previousInterestPeriod.DisbursementAmount()).negToZero()
}

// CreditedAmounts is the principal-like total: disbursement + credited
// principal + capitalized income principal [VERIFIED: InterestPeriod.java:256-259].
func (ip *InterestPeriod) CreditedAmounts() Money {
	return ip.DisbursementAmount().
		plus(ip.CreditedPrincipal()).
		plus(ip.CapitalizedIncomePrincipal())
}

// AddBalanceCorrectionAmount mutates balanceCorrectionAmount by adding the
// supplied amount [VERIFIED: InterestPeriod.java:165-167].
func (ip *InterestPeriod) AddBalanceCorrectionAmount(additional Money) {
	ip.balanceCorrectionAmount = ip.BalanceCorrectionAmount().plus(additional)
}

// AddDisbursementAmount mutates disbursementAmount by adding the supplied amount
// [VERIFIED: InterestPeriod.java:169-171].
func (ip *InterestPeriod) AddDisbursementAmount(additional Money) {
	ip.disbursementAmount = ip.DisbursementAmount().plus(additional)
}

// AddCreditedPrincipalAmount mutates creditedPrincipal by adding the supplied
// amount [VERIFIED: InterestPeriod.java:173-175].
func (ip *InterestPeriod) AddCreditedPrincipalAmount(additional Money) {
	ip.creditedPrincipal = ip.CreditedPrincipal().plus(additional)
}

// AddCreditedInterestAmount mutates creditedInterest by adding the supplied
// amount [VERIFIED: InterestPeriod.java:177-179].
func (ip *InterestPeriod) AddCreditedInterestAmount(additional Money) {
	ip.creditedInterest = ip.CreditedInterest().plus(additional)
}

// AddCapitalizedIncomePrincipalAmount mutates capitalizedIncomePrincipal by
// adding the supplied amount [VERIFIED: InterestPeriod.java:181-183].
func (ip *InterestPeriod) AddCapitalizedIncomePrincipalAmount(additional Money) {
	ip.capitalizedIncomePrincipal = ip.CapitalizedIncomePrincipal().plus(additional)
}
