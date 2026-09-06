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
// [VERIFIED: RepaymentPeriod.java:46-113 for the field list.]
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
// [VERIFIED: RepaymentPeriod.java:143-151]. emi is the level installment and
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
// [VERIFIED: RepaymentPeriod.java:200-202].
func (p *RepaymentPeriod) Previous() *RepaymentPeriod { return p.previous }

// Zero returns the currency- and rounding-correct zero money value.
func (p *RepaymentPeriod) Zero() Money { return moneyZero(p.currency, p.rounding) }

// Currency returns the monetary currency the period's amounts are denominated
// in.
func (p *RepaymentPeriod) Currency() Currency { return p.currency }

// InterestMethod returns the interest method the due-interest derivation reads.
func (p *RepaymentPeriod) InterestMethod() InterestMethod { return p.interestMethod }

// Emi returns the installment, zero when absent [VERIFIED: RepaymentPeriod.java:501-503].
func (p *RepaymentPeriod) Emi() Money { return p.emi }

// OriginalEmi returns the original installment before any re-adjustment, zero
// when absent [VERIFIED: RepaymentPeriod.java:505-507].
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

// FirstInterestPeriod returns the first segment [VERIFIED: RepaymentPeriod.java:433-435].
func (p *RepaymentPeriod) FirstInterestPeriod() *InterestPeriod {
	return p.InterestPeriods[0]
}

// LastInterestPeriod returns the last segment [VERIFIED: RepaymentPeriod.java:437-440].
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
// [VERIFIED: RepaymentPeriod.java:209-218 — the span covers both halves the
// oracle splits this across: the memoised accessor getRateFactorPlus1 at
// :209-214 and the computation calculateRateFactorPlus1 at :216-218, which is
// the reduce(BigDecimal.ONE, BigDecimal::add) this function reproduces].
func (p *RepaymentPeriod) RateFactorPlus1() *big.Rat {
	sum := big.NewRat(1, 1)
	for _, ip := range p.InterestPeriods {
		sum = new(big.Rat).Add(sum, ip.RateFactorValue())
	}
	return sum
}

// CalculatedDueInterest returns the calculated due interest plus credited
// interest, wrapped in Money [VERIFIED: RepaymentPeriod.java:226-233].
func (p *RepaymentPeriod) CalculatedDueInterest() Money {
	return p.CalculateCalculatedDueInterest()
}

// CalculateCalculatedDueInterest is calculateCalculatedDueInterest
// [VERIFIED: RepaymentPeriod.java:252-265]: the exact sum of the segments'
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
// [VERIFIED: RepaymentPeriod.java:235-250].
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
// whichever applies [VERIFIED: RepaymentPeriod.java:272-286].
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
// [VERIFIED: RepaymentPeriod.java:293-295].
func (p *RepaymentPeriod) EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest() Money {
	return p.Emi().plus(p.TotalCreditedAmount()).plus(p.FutureUnrecognizedInterest())
}

// CalculatedDuePrincipal is EMI plus credited amounts minus calculated due
// interest, floored at zero [VERIFIED: RepaymentPeriod.java:302-305].
func (p *RepaymentPeriod) CalculatedDuePrincipal() Money {
	return p.EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().
		minus(p.CalculatedDueInterest()).negToZero()
}

// CreditedPrincipal is the floored sum of credited principal over the segments
// [VERIFIED: RepaymentPeriod.java:312-316].
func (p *RepaymentPeriod) CreditedPrincipal() Money {
	res := p.Zero()
	for _, ip := range p.InterestPeriods {
		res = res.plus(ip.CreditedPrincipal())
	}
	return res.negToZero()
}

// CreditedInterest is the floored sum of credited interest over the segments
// [VERIFIED: RepaymentPeriod.java:323-327].
func (p *RepaymentPeriod) CreditedInterest() Money {
	res := p.Zero()
	for _, ip := range p.InterestPeriods {
		res = res.plus(ip.CreditedInterest())
	}
	return res.negToZero()
}

// CapitalizedIncomePrincipal is the floored sum of capitalized income principal
// over the segments [VERIFIED: RepaymentPeriod.java:334-338].
func (p *RepaymentPeriod) CapitalizedIncomePrincipal() Money {
	res := p.Zero()
	for _, ip := range p.InterestPeriods {
		res = res.plus(ip.CapitalizedIncomePrincipal())
	}
	return res.negToZero()
}

// DuePrincipal is EMI plus credited amounts minus due interest, floored at zero,
// or paid principal, whichever is greater [VERIFIED: RepaymentPeriod.java:345-350].
func (p *RepaymentPeriod) DuePrincipal() Money {
	return moneyMax(
		p.EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().minus(p.DueInterest()).negToZero(),
		p.PaidPrincipal())
}

// TotalCreditedAmount is credited principal plus credited interest, less the
// amounts moved to re-aging [VERIFIED: RepaymentPeriod.java:357-360].
func (p *RepaymentPeriod) TotalCreditedAmount() Money {
	return p.CreditedPrincipal().
		plus(p.CreditedInterest()).
		minus(p.CreditedInterestMovedDueReAge()).
		minus(p.CreditedPrincipalMovedDueReAge())
}

// TotalPaidAmount is paid principal plus paid interest
// [VERIFIED: RepaymentPeriod.java:367-369].
func (p *RepaymentPeriod) TotalPaidAmount() Money {
	return p.PaidPrincipal().plus(p.PaidInterest())
}

// IsFullyPaid reports whether the installment plus credited amounts equals the
// total paid [VERIFIED: RepaymentPeriod.java:371-373].
func (p *RepaymentPeriod) IsFullyPaid() bool {
	return p.EmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().isEqualTo(p.TotalPaidAmount())
}

// UnrecognizedInterest is the calculated due interest that had no room in the
// installment, floored at zero [VERIFIED: RepaymentPeriod.java:381-383].
func (p *RepaymentPeriod) UnrecognizedInterest() Money {
	return p.CalculatedDueInterest().minus(p.DueInterest()).negToZero()
}

// CreditedAmounts is the sum of the segments' principal-like credited amounts
// [VERIFIED: RepaymentPeriod.java:385-387].
func (p *RepaymentPeriod) CreditedAmounts() Money {
	res := p.Zero()
	for _, ip := range p.InterestPeriods {
		res = res.plus(ip.CreditedAmounts())
	}
	return res
}

// OutstandingLoanBalance rolls the last segment's balance forward by the
// balance correction, capitalized income, disbursement and paid principal and
// back by the due principal, floored at zero [VERIFIED: RepaymentPeriod.java:389-403].
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
// [VERIFIED: RepaymentPeriod.java:405-407].
func (p *RepaymentPeriod) AddPaidPrincipalAmount(paid Money) {
	p.paidPrincipal = p.PaidPrincipal().plus(paid)
}

// AddPaidInterestAmount accumulates paid interest
// [VERIFIED: RepaymentPeriod.java:409-411].
func (p *RepaymentPeriod) AddPaidInterestAmount(paid Money) {
	p.paidInterest = p.PaidInterest().plus(paid)
}

// InitialBalanceForEmiRecalculation is the previous period's outstanding
// balance (or zero) plus this period's disbursed and capitalized amounts
// [VERIFIED: RepaymentPeriod.java:413-427].
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
// [VERIFIED: RepaymentPeriod.java:458-460].
func (p *RepaymentPeriod) OutstandingInterest() Money {
	return p.DueInterest().minus(p.PaidInterest()).negToZero()
}

// OutstandingPrincipal is due principal minus paid principal, floored at zero
// [VERIFIED: RepaymentPeriod.java:462-464].
func (p *RepaymentPeriod) OutstandingPrincipal() Money {
	return p.DuePrincipal().minus(p.PaidPrincipal()).negToZero()
}

// ResetDerivedComponents zeroes the paid amounts, leaving the schedule cells
// intact [VERIFIED: RepaymentPeriod.java:466-469].
func (p *RepaymentPeriod) ResetDerivedComponents() {
	p.paidInterest = moneyZero(p.currency, p.rounding)
	p.paidPrincipal = moneyZero(p.currency, p.rounding)
}

// calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod is the total
// disbursed and capitalized amount through the given segment, inclusive of the
// period's carried totals and of every segment BEFORE the given one whose due
// date differs from the period's from-date [VERIFIED: RepaymentPeriod.java:476-492].
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
// re-aging [VERIFIED: RepaymentPeriod.java:533-536].
func (p *RepaymentPeriod) MoveOutstandingDueToReAging() {
	p.creditedPrincipalMovedDueReAge = p.CreditedPrincipal()
	p.creditedInterestMovedDueReAge = p.CreditedInterest()
}

// IsFirstRepaymentPeriod reports whether this period has no predecessor
// [VERIFIED: RepaymentPeriod.java:449-451].
func (p *RepaymentPeriod) IsFirstRepaymentPeriod() bool { return p.previous == nil }

// FindInterestPeriod returns the FIRST segment whose [from, due] window
// contains transactionDate, inclusive on both ends.
//
// DIVERGENCE FROM THE ORACLE — DO NOT CITE THIS AS PARITY. The oracle's
// findInterestPeriod [VERIFIED: RepaymentPeriod.java:442-447] differs on two
// axes, and this port matches it on neither:
//
//  1. BOUNDARY. The oracle filters with isInPeriod(transactionDate, from, due,
//     isFirstRepaymentPeriod() && interestPeriod.isFirstInterestPeriod()), and
//     that fourth argument selects the boundary rule —
//     isFirstPeriod ? DateUtils.isDateInRangeInclusive
//     : DateUtils.isDateInRangeFromExclusiveToInclusive
//     [VERIFIED: LoanRepaymentScheduleProcessingWrapper.java:251-254] — whose
//     from-exclusive branch is isAfter(target, from) && !isAfter(target, due)
//     [VERIFIED: DateUtils.java:415-417]. So the oracle's window is [from, due]
//     for the FIRST segment of the FIRST repayment period and (from, due] —
//     FROM-EXCLUSIVE, due-inclusive — for every other segment. This function is
//     unconditionally inclusive on both ends.
//  2. WHICH MATCH. The oracle terminates with .reduce((one, two) -> two),
//     which returns the LAST match, not the first. The loop below returns the
//     first.
//
// WORKED EXAMPLE — THE INPUT THAT ACTUALLY DIVERGES. Take a NON-first repayment
// period (previous != nil) carrying the contiguous segments [F, D0] and
// [D0, D1], and let transactionDate == F, the period's own FromDate:
//
//   - Oracle: no segment here is the first segment of the first repayment
//     period, so every segment is from-exclusive. Segment 1 needs F after F —
//     false. Segment 2 needs F after D0 — false. Nothing matches and
//     findInterestPeriod returns Optional.empty().
//   - This port: !F.Before(F) && !F.After(D0) is true, so it returns segment 1.
//
// Empty versus a segment: that is the divergence, and it is the case a vector
// must capture. The control that proves it is about the BOUNDARY and not about
// the date is the same transactionDate on the FIRST repayment period, where
// segment 1 IS first-of-first, the inclusive branch applies, and both sides
// return segment 1.
//
// THE INPUT THAT DOES *NOT* DIVERGE — DO NOT BUILD A VECTOR ON IT. An earlier
// revision of this block named "a transaction dated exactly on a later
// segment's from-date" as the divergent case. It is not: there the two agree.
// On the INSERTION path a later segment's from-date IS the preceding segment's
// due-date — insertInterestPeriod truncates the predecessor to newDueDate and
// inserts the successor at previousIndex+1 with FromDate == that same
// newDueDate [VERIFIED: ProgressiveLoanInterestScheduleModel.java:280-296],
// and calculateNewDueDate clamps newDueDate into [previous.from, previous.due]
// [VERIFIED: ProgressiveLoanInterestScheduleModel.java:439-442], so the split
// can neither escape nor invert the parent range. With transactionDate == D0 in
// the same non-first period the oracle matches [F, D0] (D0 is after F and not
// after D0) and does NOT match [D0, D1] (D0 is not after D0), so its last-match
// reduction yields [F, D0]; the port's first match is [F, D0] too. Identical
// answers. A vector built on that input COMES BACK GREEN and would be filed as
// parity while the real defect stayed live — which is why the worked example
// matters more here than the two facts above it do.
//
// CONTIGUITY HOLDS ON THE INSERTION PATH; IT IS NOT AN INVARIANT OF THE LIST.
// Do not port it as one. Both date fields carry a public Lombok @Setter
// [VERIFIED: InterestPeriod.java:47-52], getInterestPeriods() hands out the
// live ArrayList [VERIFIED: RepaymentPeriod.java:54-56], nothing validates or
// re-sorts it, and Gson rebuilds the whole list out of
// m_loan_progressive_model.json_model with no ordering check whatsoever
// [VERIFIED: InterestScheduleModelRepositoryWrapperImpl.java:95-100;
// ProgressiveLoanInterestScheduleModelParserServiceGsonImpl.java:66, :87] —
// a list written by a different code version is restored unchecked, and
// getSavedModel then re-processes transactions onto it
// [VERIFIED: InterestScheduleModelRepositoryWrapperImpl.java:110-128]. Strict
// contiguity is in fact BROKEN at ProgressiveEMICalculator.java:1791-1794,
// which shrinks an INTERIOR segment's dueDate to targetDate and — unlike :665,
// which clears the whole tail at :677-678 — truncates nothing. A port that
// treats DueDate == next.FromDate as an invariant (binary search over the
// segments, an assertion, or deriving one boundary from its neighbour) is
// wrong on that path, and that path is inside interest recalculation.
//
// THE DIRECTION OF THAT BREAK IS A GAP, NOT AN OVERLAP, and that is why the
// conclusion below survives its premise. findInterestPeriod only ever returns a
// segment whose window already contains targetDate, so targetDate <= due_i
// [VERIFIED: RepaymentPeriod.java:442-447]; setDueDate(targetDate) therefore
// only SHRINKS due_i while from_(i+1) keeps the old value, leaving
// from_(i+1) >= due_i. An overlap would need due_i to GROW past from_(i+1),
// which would require targetDate > due_i — exactly what the filter forbids.
//
// Axis 2 is LATENT, and this weaker property is what carries it: no reachable
// path leaves two segments i < j with from_j < due_i. Every date mutation
// outside insertInterestPeriod touches only the FIRST segment's fromDate
// [ProgressiveEMICalculator.java:857], only the LAST segment's dueDate
// [:838, :859, :1066, :1153, :2036], or a segment whose successors are cleared
// in the same block [:665 with :677-678, :687 with :689]; every deletion
// [:654, :678, :689, :692, AdvancedPaymentScheduleTransactionProcessor.java:3592]
// only drops elements, which cannot create a pair; both copy constructors
// preserve dates and order [VERIFIED: RepaymentPeriod.java:153-171, :173-198];
// and insertInterestPeriod splits in place under the clamp above. Two segments
// therefore never match at once: a match on i needs transactionDate <= due_i,
// while a match on a later j needs transactionDate > from_j >= due_i. The one
// corner where even that weaker property bends is insertInterestPeriod's
// indexOf at ProgressiveLoanInterestScheduleModel.java:294, which is a VALUE
// lookup (@EqualsAndHashCode excludes only repaymentPeriod, and only
// repaymentPeriod — InterestPeriod.java:41) and so can place the successor after
// an earlier value-equal duplicate; that bend requires the intervening segment
// to be inverted, whose match window is empty, so it still yields at most one
// match. The site-by-site derivation is in
// .softhouse/handoff/T539-t538-conditions.md.
//
// First-versus-last is therefore observable ONLY on (i) two segments i < j in
// STRICT overlap, from_j < due_i, or (ii) two segments carrying IDENTICAL
// non-empty [from, due] ranges — case (ii) being the from_j == from_i <
// due_i == due_j instance of case (i). A SHARED boundary (from_j == due_i) does
// NOT produce a second match: that IS contiguity, it is verbatim the retired
// example above, and it comes back green. Neither do zero-length segments (the
// from-exclusive window (d, d] is empty, and the one inclusive window [d, d] is
// the first segment of the first repayment period, which no later segment can
// also match because from_j >= d), nor gaps, nor inverted segments (due < from,
// empty window). Pin axis 2 with its own case built on from_j < due_i, not as a
// by-product of the boundary case.
//
// Both helpers this needs already exist and are graded: isInPeriod and
// isDateInRangeFromExclusiveToInclusive in dates.go, and IsFirstInterestPeriod
// in interestperiod.go. The repair was NOT made here because T530 is a
// citation-integrity task and this is a behavioural change to a
// transaction-to-segment assignment rule — it needs its own golden vector
// against the oracle before the numbers move. It is latent rather than live:
// this function has no caller anywhere in the module at the time of writing
// (grep FindInterestPeriod). Recorded in
// .softhouse/handoff/T530-t529-conditions.md as substantive finding 1; the
// worked example above was corrected by T534 after T531 rated the original one
// MAJOR, and the vector spec that must capture it is T533.
func (p *RepaymentPeriod) FindInterestPeriod(transactionDate time.Time) (*InterestPeriod, bool) {
	for _, ip := range p.InterestPeriods {
		if !transactionDate.Before(ip.FromDate) && !transactionDate.After(ip.DueDate) {
			return ip, true
		}
	}
	return nil, false
}

// SetEmi mutates the installment [VERIFIED: RepaymentPeriod.java:57-58 @Setter].
func (p *RepaymentPeriod) SetEmi(emi Money) { p.emi = emi }

// SetOriginalEmi mutates the original installment [VERIFIED: RepaymentPeriod.java:59-60 @Setter].
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
// RepaymentPeriod.java:153-171].
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
// the paid interest promoted to fixed interest [VERIFIED: RepaymentPeriod.java:173-198].
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
