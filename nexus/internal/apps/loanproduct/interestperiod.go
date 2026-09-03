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
	RateFactor                  *big.Rat
	RateFactorTillPeriodDueDate *big.Rat

	creditedPrincipal  Money
	creditedInterest   Money
	disbursementAmount Money

	// balanceCorrectionAmount and outstandingLoanBalance are NOT LEDGER
	// BALANCES and never become a database column — see the package comment in
	// doc.go, "The two \"balance\"-named cells in this package are NOT ledger
	// balances", for the oracle evidence. In one line each:
	//
	// balanceCorrectionAmount is a SIGNED DELTA applied to the schedule's
	// principal projection; the oracle only ever adds a negated amount to it
	// [VERIFIED: ProgressiveEMICalculator.java:922, :952, :1129]. It is a
	// summand of the roll-forward below, exactly like disbursementAmount and
	// capitalizedIncomePrincipal.
	//
	// outstandingLoanBalance is the principal base of THIS SEGMENT's
	// declining-balance interest arithmetic and nothing else
	// [VERIFIED: InterestPeriod.java:151]. It is a SWEPT SNAPSHOT, refreshed
	// only by UpdateOutstandingLoanBalance below; between sweeps the oracle
	// deliberately leaves it stale, so it is not equivalent to an on-demand
	// derivation and must not be replaced by one.
	balanceCorrectionAmount    Money
	outstandingLoanBalance     Money
	capitalizedIncomePrincipal Money

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
//
// THE TWO ASSIGNMENTS BELOW ARE NOT LEDGER-BALANCE WRITES, and they are the
// reason the I-3 source guard refuses this package. They write a SWEPT SNAPSHOT
// of a schedule projection that never becomes a database column anywhere in the
// oracle — see doc.go for the full evidence. What matters here is why the cell
// cannot simply be derived on read instead:
//
// This function is the WHOLE refresh mechanism. The oracle calls it only from
// explicit sweeps [VERIFIED: ProgressiveEMICalculator.java:1254-1256, and the
// per-repayment-period sweeps at :1647, :1654 and :1667], and it deliberately
// leaves the cell unrefreshed in between — RepaymentPeriod.copyWithoutPaidAmounts
// zeroes each copied segment's balanceCorrectionAmount, which is a summand of
// the expression below, and does NOT re-run this function
// [VERIFIED: RepaymentPeriod.java:173-197]. So the value read between two sweeps
// is, by construction, not the value this expression would produce if evaluated
// at that moment. Turning the cell into an on-demand derivation would change the
// numbers at every such point, which is a parity break, not a repair.
//
// This is the opposite of RepaymentPeriod's derived cells: those carry an oracle
// Memo with an invalidation key, are observationally inert, and are therefore
// recomputed on every read by this port (see repaymentperiod.go). This cell has
// no invalidation key and is observationally live.
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
//
// balanceCorrectionAmount is a SIGNED DELTA, not a balance: every oracle caller
// adds a NEGATED principal amount to it
// [VERIFIED: ProgressiveEMICalculator.java:922, :952, :1129;
// RepaymentPeriod.java:192-194; ProgressiveLoanInterestScheduleModel.java:257,
// :290]. It is one summand of UpdateOutstandingLoanBalance's roll-forward above,
// structurally identical to disbursementAmount and capitalizedIncomePrincipal,
// whose Add* methods the I-3 guard does not flag. This one is flagged because
// its name contains the substring "balance" — see doc.go.
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

// IsPaused mirrors InterestPeriod.isPaused().
func (ip *InterestPeriod) IsPaused() bool { return ip.Paused }

// SetDueDate mutates the segment's due date [VERIFIED: InterestPeriod.java @Setter].
func (ip *InterestPeriod) SetDueDate(due time.Time) { ip.DueDate = due }

// SetPaused mutates the segment's paused flag [VERIFIED: InterestPeriod.java @Setter].
func (ip *InterestPeriod) SetPaused(paused bool) { ip.Paused = paused }

// SetRateFactor mutates the segment's own rate factor.
func (ip *InterestPeriod) SetRateFactor(f *big.Rat) { ip.RateFactor = f }

// SetRateFactorTillPeriodDueDate mutates the segment's rate factor measured to
// the enclosing repayment period's due date.
func (ip *InterestPeriod) SetRateFactorTillPeriodDueDate(f *big.Rat) {
	ip.RateFactorTillPeriodDueDate = f
}

// copy is InterestPeriod.copy(repaymentPeriod, interestPeriod) — a deep copy
// rebound to rp [VERIFIED: InterestPeriod.java:86-92].
func (ip *InterestPeriod) copy(rp *RepaymentPeriod) *InterestPeriod {
	c := &InterestPeriod{
		repaymentPeriod:             rp,
		FromDate:                    ip.FromDate,
		DueDate:                     ip.DueDate,
		RateFactor:                  ratCopy(ip.RateFactor),
		RateFactorTillPeriodDueDate: ratCopy(ip.RateFactorTillPeriodDueDate),
		creditedPrincipal:           ip.CreditedPrincipal(),
		creditedInterest:            ip.CreditedInterest(),
		disbursementAmount:          ip.DisbursementAmount(),
		balanceCorrectionAmount:     ip.BalanceCorrectionAmount(),
		outstandingLoanBalance:      ip.OutstandingLoanBalance(),
		capitalizedIncomePrincipal:  ip.CapitalizedIncomePrincipal(),
		rounding:                    ip.rounding,
		currency:                    ip.currency,
		Paused:                      ip.Paused,
	}
	return c
}

// withEmptyInterestPeriod is InterestPeriod.withEmptyAmounts(repaymentPeriod,
// fromDate, dueDate, isPaused): every amount is zero and the rate factors are
// BigDecimal.ZERO, matching the oracle's three- and four-argument factories
// [VERIFIED: InterestPeriod.java:94-109].
func withEmptyInterestPeriod(rp *RepaymentPeriod, from, due time.Time, paused bool) *InterestPeriod {
	zero := moneyZero(rp.currency, rp.rounding)
	return &InterestPeriod{
		repaymentPeriod:             rp,
		FromDate:                    from,
		DueDate:                     due,
		RateFactor:                  new(big.Rat),
		RateFactorTillPeriodDueDate: new(big.Rat),
		creditedPrincipal:           zero,
		creditedInterest:            zero,
		disbursementAmount:          zero,
		balanceCorrectionAmount:     zero,
		outstandingLoanBalance:      zero,
		capitalizedIncomePrincipal:  zero,
		rounding:                    rp.rounding,
		currency:                    rp.currency,
		Paused:                      paused,
	}
}

func ratCopy(r *big.Rat) *big.Rat {
	if r == nil {
		return nil
	}
	return new(big.Rat).Set(r)
}
