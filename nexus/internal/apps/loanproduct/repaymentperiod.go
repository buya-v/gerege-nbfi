package loanproduct

import (
	"math/big"
	"time"
)

// RepaymentPeriod is the Go port of Fineract's
// portfolio.loanproduct.calc.data.RepaymentPeriod: one installment window of a
// progressive-loan schedule whose due-interest, due-principal and outstanding
// balance are DERIVED from the interest-period segments and the paid amounts.
//
// [VERIFIED: RepaymentPeriod.java:60-97 for the field list.]
//
// Unlike the schedule GENERATOR's private repayment period (in
// nexus/internal/apps/loanschedule), this value object is public and mutation
// oriented: repayments, disbursements, charge-backs and rate changes mutate its
// paid/credited/balance cells, and the derived quantities above recompute from
// those cells on every read. The oracle memoises those derived quantities; the
// memo is a pure cache and is observationally inert, so this port recomputes
// them directly and drops the cache.
type RepaymentPeriod struct {
	previous *RepaymentPeriod

	// FromDate and DueDate bound the installment window.
	FromDate time.Time
	DueDate  time.Time

	// InterestPeriods is the ordered list of segments inside the window.
	InterestPeriods []*InterestPeriod

	emi                        Money
	originalEmi                Money
	paidPrincipal              Money
	paidInterest               Money
	futureUnrecognizedInterest Money

	totalDisbursedAmount         Money
	totalCapitalizedIncomeAmount Money

	creditedPrincipalMovedDueReAge Money
	creditedInterestMovedDueReAge  Money
	fixedInterest                  Money

	rounding       Rounding
	currency       Currency
	interestMethod InterestMethod

	InterestMovedUpward        bool
	InterestPaymentGrace       bool
	InterestMovedDownward      bool
	ReAged                     bool
	ReAgedEarlyRepaymentHolder bool
}

// NewRepaymentPeriod builds a repayment period with one empty interest period
// spanning [from, due], mirroring RepaymentPeriod.create
// [VERIFIED: RepaymentPeriod.java:141-147]. emi is the level installment and
// becomes both emi and originalEmi; all paid and credited cells start at zero.
func NewRepaymentPeriod(previous *RepaymentPeriod, from, due time.Time, emi Money,
	rounding Rounding, currency Currency, method InterestMethod) *RepaymentPeriod {
	zero := moneyZero(currency, rounding)
	p := &RepaymentPeriod{
		previous:                       previous,
		FromDate:                       from,
		DueDate:                        due,
		emi:                            emi,
		originalEmi:                    emi,
		paidPrincipal:                  zero,
		paidInterest:                   zero,
		futureUnrecognizedInterest:     zero,
		totalDisbursedAmount:           zero,
		totalCapitalizedIncomeAmount:   zero,
		creditedPrincipalMovedDueReAge: zero,
		creditedInterestMovedDueReAge:  zero,
		fixedInterest:                  zero,
		rounding:                       rounding,
		currency:                       currency,
		interestMethod:                 method,
	}
	p.InterestPeriods = []*InterestPeriod{NewInterestPeriod(p, from, due)}
	return p
}

// NewInterestPeriod builds an empty interest-period segment bound to p, with
// every amount cell zeroed. The segment carries p's currency and rounding so
// that its money cells are never left as nil-backed zero values.
func NewInterestPeriod(p *RepaymentPeriod, from, due time.Time) *InterestPeriod {
	return &InterestPeriod{
		repaymentPeriod:            p,
		FromDate:                   from,
		DueDate:                    due,
		creditedPrincipal:          moneyZero(p.currency, p.rounding),
		creditedInterest:           moneyZero(p.currency, p.rounding),
		disbursementAmount:         moneyZero(p.currency, p.rounding),
		balanceCorrectionAmount:    moneyZero(p.currency, p.rounding),
		outstandingLoanBalance:     moneyZero(p.currency, p.rounding),
		capitalizedIncomePrincipal: moneyZero(p.currency, p.rounding),
		rounding:                   p.rounding,
		currency:                   p.currency,
	}
}

// Previous returns the preceding repayment period, or nil for the first period
// [VERIFIED: RepaymentPeriod.java:214-216].
func (p *RepaymentPeriod) Previous() *RepaymentPeriod { return p.previous }

// Zero returns the currency- and rounding-correct zero money value.
func (p *RepaymentPeriod) Zero() Money { return moneyZero(p.currency, p.rounding) }

// Currency returns the monetary currency the period's amounts are denominated
// in.
func (p *RepaymentPeriod) Currency() Currency { return p.currency }

// InterestMethod returns the interest method the due-interest derivation reads.
func (p *RepaymentPeriod) InterestMethod() InterestMethod { return p.interestMethod }

// Emi returns the installment, zero when absent [VERIFIED: RepaymentPeriod.java:417-419].
func (p *RepaymentPeriod) Emi() Money { return p.emi }

// OriginalEmi returns the original installment before any re-adjustment, zero
// when absent [VERIFIED: RepaymentPeriod.java:421-423].
func (p *RepaymentPeriod) OriginalEmi() Money { return p.originalEmi }

// PaidPrincipal returns paid principal, zero when absent.
func (p *RepaymentPeriod) PaidPrincipal() Money { return p.paidPrincipal }

// PaidInterest returns paid interest, zero when absent.
func (p *RepaymentPeriod) PaidInterest() Money { return p.paidInterest }

// FutureUnrecognizedInterest returns future unrecognized interest, zero when
// absent.
func (p *RepaymentPeriod) FutureUnrecognizedInterest() Money { return p.futureUnrecognizedInterest }

// TotalDisbursedAmount returns totalDisbursedAmount, zero when absent.
func (p *RepaymentPeriod) TotalDisbursedAmount() Money { return p.totalDisbursedAmount }

// TotalCapitalizedIncomeAmount returns totalCapitalizedIncomeAmount, zero when
// absent.
func (p *RepaymentPeriod) TotalCapitalizedIncomeAmount() Money { return p.totalCapitalizedIncomeAmount }

// FixedInterest returns fixedInterest, zero when absent.
func (p *RepaymentPeriod) FixedInterest() Money { return p.fixedInterest }

// CreditedPrincipalMovedDueReAge returns the principal moved to re-aging.
func (p *RepaymentPeriod) CreditedPrincipalMovedDueReAge() Money {
	return p.creditedPrincipalMovedDueReAge
}

// CreditedInterestMovedDueReAge returns the interest moved to re-aging.
func (p *RepaymentPeriod) CreditedInterestMovedDueReAge() Money {
	return p.creditedInterestMovedDueReAge
}

// FirstInterestPeriod returns the first segment [VERIFIED: RepaymentPeriod.java:292-294].
func (p *RepaymentPeriod) FirstInterestPeriod() *InterestPeriod {
	return p.InterestPeriods[0]
}

// LastInterestPeriod returns the last segment [VERIFIED: RepaymentPeriod.java:296-299].
func (p *RepaymentPeriod) LastInterestPeriod() *InterestPeriod {
	return p.InterestPeriods[len(p.InterestPeriods)-1]
}

// interestPeriodIndex returns the position of ip in the segment list, or -1.
func (p *RepaymentPeriod) interestPeriodIndex(ip *InterestPeriod) int {
	for i, candidate := range p.InterestPeriods {
		if candidate == ip {
			return i
		}
	}
	return -1
}

// RateFactorPlus1 is the sum of (rate factor + 1) over the segments
// [VERIFIED: RepaymentPeriod.java:218-229].
func (p *RepaymentPeriod) RateFactorPlus1() *big.Rat {
	sum := big.NewRat(1, 1)
	for _, ip := range p.InterestPeriods {
		sum = new(big.Rat).Add(sum, ip.RateFactorValue())
	}
	return sum
}

// CalculatedDueInterest returns the calculated due interest plus credited
// interest, wrapped in Money [VERIFIED: RepaymentPeriod.java:232-241].
func (p *RepaymentPeriod) CalculatedDueInterest() Money {
	return p.CalculateCalculatedDueInterest()
}

// CalculateCalculatedDueInterest is calculateCalculatedDueInterest
// [VERIFIED: RepaymentPeriod.java:262-272]: the exact sum of the segments'
// raw due interest, normalised to Money, plus fixed interest, future
// unrecognized interest and the previous period's unrecognized interest, all
// floored at zero.
func (p *RepaymentPeriod) CalculateCalculatedDueInterest() Money {
	calculated := p.Zero()
	if !p.InterestMovedUpward && !p.InterestMovedDownward {
		sum := new(big.Rat)
		for _, ip := range p.InterestPeriods {
			sum.Add(sum, ip.CalculatedDueInterest())
		}
		calculated = moneyOf(p.currency, p.rounding, sum)
	}
	calculated = calculated.plus(p.FixedInterest())
	calculated = calculated.plus(p.FutureUnrecognizedInterest())
	if p.previous != nil {
		calculated = calculated.plus(p.previous.UnrecognizedInterest())
	}
	return calculated.negToZero()
}

// CalculateFixedInterestTillDate prorates the fixed interest over the window
// [VERIFIED: RepaymentPeriod.java:243-261].
func (p *RepaymentPeriod) CalculateFixedInterestTillDate() Money {
	calculated := p.Zero()
	if !p.FixedInterest().IsZero() {
		length := daysBetween(p.FromDate, p.DueDate)
		if length == 0 || len(p.InterestPeriods) == 0 {
			calculated = p.FixedInterest()
		} else {
			interestCalculationLength := daysBetween(
				p.FirstInterestPeriod().FromDate, p.LastInterestPeriod().DueDate)
			v := roundSignificant(
				new(big.Rat).Quo(new(big.Rat).SetInt64(interestCalculationLength),
					new(big.Rat).SetInt64(length)),
				p.rounding.Precision, p.rounding.Mode)
			v = roundSignificant(new(big.Rat).Mul(v, p.FixedInterest().major()),
				p.rounding.Precision, p.rounding.Mode)
			calculated = moneyOf(p.currency, p.rounding, v)
		}
	}
	return calculated
}

// DueInterest returns due interest plus credited interest or paid interest,
// whichever applies [VERIFIED: RepaymentPeriod.java:274-294].
func (p *RepaymentPeriod) DueInterest() Money {
	if p.InterestPaymentGrace {
		return p.PaidInterest()
	}
	var candidate Money
	if p.PaidPrincipal().isGreaterThan(p.CalculatedDuePrincipal()) {
		candidate = p.PaidInterest()
	} else {
		candidate = moneyMin(p.CalculatedDueInterest(), p.EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest())
	}
	return moneyMax(candidate, p.PaidInterest())
}

// EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest is the installment plus
// credited amounts and future unrecognized interest
// [VERIFIED: RepaymentPeriod.java:299-301].
func (p *RepaymentPeriod) EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest() Money {
	return p.Emi().plus(p.TotalCreditedAmount()).plus(p.FutureUnrecognizedInterest())
}

// CalculatedDuePrincipal is EMI plus credited amounts minus calculated due
// interest, floored at zero [VERIFIED: RepaymentPeriod.java:306-309].
func (p *RepaymentPeriod) CalculatedDuePrincipal() Money {
	return p.EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().
		minus(p.CalculatedDueInterest()).negToZero()
}

// CreditedPrincipal is the floored sum of credited principal over the segments
// [VERIFIED: RepaymentPeriod.java:314-317].
func (p *RepaymentPeriod) CreditedPrincipal() Money {
	res := p.Zero()
	for _, ip := range p.InterestPeriods {
		res = res.plus(ip.CreditedPrincipal())
	}
	return res.negToZero()
}

// CreditedInterest is the floored sum of credited interest over the segments
// [VERIFIED: RepaymentPeriod.java:322-325].
func (p *RepaymentPeriod) CreditedInterest() Money {
	res := p.Zero()
	for _, ip := range p.InterestPeriods {
		res = res.plus(ip.CreditedInterest())
	}
	return res.negToZero()
}

// CapitalizedIncomePrincipal is the floored sum of capitalized income principal
// over the segments [VERIFIED: RepaymentPeriod.java:330-333].
func (p *RepaymentPeriod) CapitalizedIncomePrincipal() Money {
	res := p.Zero()
	for _, ip := range p.InterestPeriods {
		res = res.plus(ip.CapitalizedIncomePrincipal())
	}
	return res.negToZero()
}

// DuePrincipal is EMI plus credited amounts minus due interest, floored at zero,
// or paid principal, whichever is greater [VERIFIED: RepaymentPeriod.java:338-343].
func (p *RepaymentPeriod) DuePrincipal() Money {
	return moneyMax(
		p.EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().minus(p.DueInterest()).negToZero(),
		p.PaidPrincipal())
}

// TotalCreditedAmount is credited principal plus credited interest, less the
// amounts moved to re-aging [VERIFIED: RepaymentPeriod.java:348-352].
func (p *RepaymentPeriod) TotalCreditedAmount() Money {
	return p.CreditedPrincipal().
		plus(p.CreditedInterest()).
		minus(p.CreditedInterestMovedDueReAge()).
		minus(p.CreditedPrincipalMovedDueReAge())
}

// TotalPaidAmount is paid principal plus paid interest
// [VERIFIED: RepaymentPeriod.java:357-359].
func (p *RepaymentPeriod) TotalPaidAmount() Money {
	return p.PaidPrincipal().plus(p.PaidInterest())
}

// IsFullyPaid reports whether the installment plus credited amounts equals the
// total paid [VERIFIED: RepaymentPeriod.java:361-363].
func (p *RepaymentPeriod) IsFullyPaid() bool {
	return p.EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().isEqualTo(p.TotalPaidAmount())
}

// UnrecognizedInterest is the calculated due interest that had no room in the
// installment, floored at zero [VERIFIED: RepaymentPeriod.java:369-371].
func (p *RepaymentPeriod) UnrecognizedInterest() Money {
	return p.CalculatedDueInterest().minus(p.DueInterest()).negToZero()
}

// CreditedAmounts is the sum of the segments' principal-like credited amounts
// [VERIFIED: RepaymentPeriod.java:373-375].
func (p *RepaymentPeriod) CreditedAmounts() Money {
	res := p.Zero()
	for _, ip := range p.InterestPeriods {
		res = res.plus(ip.CreditedAmounts())
	}
	return res
}

// OutstandingLoanBalance rolls the last segment's balance forward by the
// balance correction, capitalized income, disbursement and paid principal and
// back by the due principal, floored at zero [VERIFIED: RepaymentPeriod.java:377-389].
func (p *RepaymentPeriod) OutstandingLoanBalance() Money {
	last := p.LastInterestPeriod()
	return last.OutstandingLoanBalance().
		plus(last.BalanceCorrectionAmount()).
		plus(last.CapitalizedIncomePrincipal()).
		plus(last.DisbursementAmount()).
		plus(p.PaidPrincipal()).
		minus(p.DuePrincipal()).negToZero()
}

// AddPaidPrincipalAmount accumulates paid principal
// [VERIFIED: RepaymentPeriod.java:391-393].
func (p *RepaymentPeriod) AddPaidPrincipalAmount(paid Money) {
	p.paidPrincipal = p.PaidPrincipal().plus(paid)
}

// AddPaidInterestAmount accumulates paid interest
// [VERIFIED: RepaymentPeriod.java:395-397].
func (p *RepaymentPeriod) AddPaidInterestAmount(paid Money) {
	p.paidInterest = p.PaidInterest().plus(paid)
}

// InitialBalanceForEmiRecalculation is the previous period's outstanding
// balance (or zero) plus this period's disbursed and capitalized amounts
// [VERIFIED: RepaymentPeriod.java:399-415].
func (p *RepaymentPeriod) InitialBalanceForEmiRecalculation() Money {
	var initial Money
	if p.previous != nil {
		initial = p.previous.OutstandingLoanBalance()
	} else {
		initial = p.Zero()
	}
	var totalDisbursed Money = p.Zero()
	var totalCapitalized Money = p.Zero()
	for _, ip := range p.InterestPeriods {
		totalDisbursed = totalDisbursed.plus(ip.DisbursementAmount())
		totalCapitalized = totalCapitalized.plus(ip.CapitalizedIncomePrincipal())
	}
	return initial.plus(totalDisbursed).plus(totalCapitalized)
}

// OutstandingInterest is due interest minus paid interest, floored at zero
// [VERIFIED: RepaymentPeriod.java:420-422].
func (p *RepaymentPeriod) OutstandingInterest() Money {
	return p.DueInterest().minus(p.PaidInterest()).negToZero()
}

// OutstandingPrincipal is due principal minus paid principal, floored at zero
// [VERIFIED: RepaymentPeriod.java:424-426].
func (p *RepaymentPeriod) OutstandingPrincipal() Money {
	return p.DuePrincipal().minus(p.PaidPrincipal()).negToZero()
}

// ResetDerivedComponents zeroes the paid amounts, leaving the schedule cells
// intact [VERIFIED: RepaymentPeriod.java:428-431].
func (p *RepaymentPeriod) ResetDerivedComponents() {
	p.paidInterest = moneyZero(p.currency, p.rounding)
	p.paidPrincipal = moneyZero(p.currency, p.rounding)
}

// calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod is the total
// disbursed and capitalized amount through the given segment, inclusive of the
// period's carried totals and of every segment BEFORE the given one whose due
// date differs from the period's from-date [VERIFIED: RepaymentPeriod.java:436-449].
func (p *RepaymentPeriod) calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod(till *InterestPeriod) Money {
	res := p.TotalDisbursedAmount().plus(p.TotalCapitalizedIncomeAmount())
	for _, ip := range p.InterestPeriods {
		if ip == till {
			break
		}
		if !ip.DueDate.Equal(p.FromDate) {
			res = res.plus(ip.DisbursementAmount())
			res = res.plus(ip.CapitalizedIncomePrincipal())
		}
	}
	return res
}

// MoveOutstandingDueToReAging records the current credited amounts as moved to
// re-aging [VERIFIED: RepaymentPeriod.java:450-453].
func (p *RepaymentPeriod) MoveOutstandingDueToReAging() {
	p.creditedPrincipalMovedDueReAge = p.CreditedPrincipal()
	p.creditedInterestMovedDueReAge = p.CreditedInterest()
}

// IsFirstRepaymentPeriod reports whether this period has no predecessor
// [VERIFIED: RepaymentPeriod.java:206-208].
func (p *RepaymentPeriod) IsFirstRepaymentPeriod() bool { return p.previous == nil }

// FindInterestPeriod returns the segment whose [from, due] window contains
// transactionDate, inclusive on both ends [VERIFIED: RepaymentPeriod.java:436-443].
func (p *RepaymentPeriod) FindInterestPeriod(transactionDate time.Time) (*InterestPeriod, bool) {
	for _, ip := range p.InterestPeriods {
		if !transactionDate.Before(ip.FromDate) && !transactionDate.After(ip.DueDate) {
			return ip, true
		}
	}
	return nil, false
}

// SetEmi mutates the installment [VERIFIED: RepaymentPeriod.java @Setter].
func (p *RepaymentPeriod) SetEmi(emi Money) { p.emi = emi }

// SetOriginalEmi mutates the original installment [VERIFIED: RepaymentPeriod.java @Setter].
func (p *RepaymentPeriod) SetOriginalEmi(originalEmi Money) { p.originalEmi = originalEmi }

// SetFutureUnrecognizedInterest mutates future unrecognized interest.
func (p *RepaymentPeriod) SetFutureUnrecognizedInterest(m Money) { p.futureUnrecognizedInterest = m }

// SetFixedInterest mutates fixed interest.
func (p *RepaymentPeriod) SetFixedInterest(m Money) { p.fixedInterest = m }

// SetTotalDisbursedAmount mutates totalDisbursedAmount.
func (p *RepaymentPeriod) SetTotalDisbursedAmount(m Money) { p.totalDisbursedAmount = m }

// SetTotalCapitalizedIncomeAmount mutates totalCapitalizedIncomeAmount.
func (p *RepaymentPeriod) SetTotalCapitalizedIncomeAmount(m Money) {
	p.totalCapitalizedIncomeAmount = m
}

// SetCreditedPrincipalMovedDueReAge mutates creditedPrincipalMovedDueReAge.
func (p *RepaymentPeriod) SetCreditedPrincipalMovedDueReAge(m Money) {
	p.creditedPrincipalMovedDueReAge = m
}

// SetCreditedInterestMovedDueReAge mutates creditedInterestMovedDueReAge.
func (p *RepaymentPeriod) SetCreditedInterestMovedDueReAge(m Money) {
	p.creditedInterestMovedDueReAge = m
}

// SetInterestMovedUpward mutates the interest-moved-upward flag.
func (p *RepaymentPeriod) SetInterestMovedUpward(v bool) { p.InterestMovedUpward = v }

// SetInterestMovedDownward mutates the interest-moved-downward flag.
func (p *RepaymentPeriod) SetInterestMovedDownward(v bool) { p.InterestMovedDownward = v }

// SetInterestPaymentGrace mutates the interest payment grace flag.
func (p *RepaymentPeriod) SetInterestPaymentGrace(v bool) { p.InterestPaymentGrace = v }

// SetReAged mutates the re-aged flag.
func (p *RepaymentPeriod) SetReAged(v bool) { p.ReAged = v }

// SetReAgedEarlyRepaymentHolder mutates the re-aged early repayment holder flag.
func (p *RepaymentPeriod) SetReAgedEarlyRepaymentHolder(v bool) { p.ReAgedEarlyRepaymentHolder = v }

// SetCurrency mutates the period's monetary currency.
func (p *RepaymentPeriod) SetCurrency(c Currency) { p.currency = c }

// copy is RepaymentPeriod.copy(previous, repaymentPeriod): a full deep copy with
// the supplied predecessor and a fresh interest-period list [VERIFIED:
// RepaymentPeriod.java:149-166].
func (p *RepaymentPeriod) copy(previous *RepaymentPeriod) *RepaymentPeriod {
	c := &RepaymentPeriod{
		previous:                       previous,
		FromDate:                       p.FromDate,
		DueDate:                        p.DueDate,
		emi:                            p.Emi(),
		originalEmi:                    p.OriginalEmi(),
		paidPrincipal:                  p.PaidPrincipal(),
		paidInterest:                   p.PaidInterest(),
		futureUnrecognizedInterest:     p.FutureUnrecognizedInterest(),
		totalDisbursedAmount:           p.TotalDisbursedAmount(),
		totalCapitalizedIncomeAmount:   p.TotalCapitalizedIncomeAmount(),
		creditedPrincipalMovedDueReAge: p.CreditedPrincipalMovedDueReAge(),
		creditedInterestMovedDueReAge:  p.CreditedInterestMovedDueReAge(),
		fixedInterest:                  p.FixedInterest(),
		rounding:                       p.rounding,
		currency:                       p.currency,
		interestMethod:                 p.interestMethod,
		InterestMovedUpward:            p.InterestMovedUpward,
		InterestPaymentGrace:           p.InterestPaymentGrace,
		InterestMovedDownward:          p.InterestMovedDownward,
		ReAged:                         p.ReAged,
		ReAgedEarlyRepaymentHolder:     p.ReAgedEarlyRepaymentHolder,
	}
	c.InterestPeriods = make([]*InterestPeriod, 0, len(p.InterestPeriods))
	for _, ip := range p.InterestPeriods {
		c.InterestPeriods = append(c.InterestPeriods, ip.copy(c))
	}
	return c
}

// copyWithoutPaidAmounts is RepaymentPeriod.copyWithoutPaidAmounts(previous,
// repaymentPeriod): the same as copy but with paid principal, paid interest and
// future unrecognized interest zeroed, and — when interest has moved downward —
// the paid interest promoted to fixed interest [VERIFIED: RepaymentPeriod.java:168-194].
func (p *RepaymentPeriod) copyWithoutPaidAmounts(previous *RepaymentPeriod) *RepaymentPeriod {
	c := p.copy(previous)
	c.paidPrincipal = moneyZero(c.currency, c.rounding)
	c.paidInterest = moneyZero(c.currency, c.rounding)
	c.futureUnrecognizedInterest = moneyZero(c.currency, c.rounding)
	if p.InterestMovedDownward {
		c.fixedInterest = p.PaidInterest()
	}
	for _, ip := range c.InterestPeriods {
		if !ip.BalanceCorrectionAmount().IsZero() {
			// addBalanceCorrectionAmount(negated) nets the cell to exactly zero,
			// so writing zero directly is the same result without the extra add
			// [VERIFIED: RepaymentPeriod.java:192-194].
			//
			// NOT A LEDGER-BALANCE WRITE, and left RED deliberately, on the two
			// legs in doc.go, "THE TEST THAT DECIDES IT: TWO LEGS". LEG 1,
			// PARITY: the segment balance this summand feeds is a swept
			// snapshot the oracle reads stale, so I-3's remedy "derive by
			// summation" changes the numbers — this very function is where it
			// does, as the paragraph below records. LEG 2, REACHABILITY:
			// balanceCorrectionAmount reaches no journal entry, no GL posting
			// and no column any aggregate reads as an account balance.
			//
			// Neither "it is never a column" nor "there is no posting stream"
			// is the argument; both were tried here and both are retired with
			// their counterexamples in doc.go.
			//
			// Note also what the oracle does NOT do here: it clears this
			// summand and leaves the segment's outstandingLoanBalance, which
			// the summand feeds, untouched until the next explicit sweep. That
			// is the staleness UpdateOutstandingLoanBalance's comment describes,
			// and it is why neither cell may be replaced by an on-demand
			// derivation.
			ip.balanceCorrectionAmount = ip.zero()
		}
	}
	return c
}
