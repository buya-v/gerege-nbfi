package workingcapital

import "github.com/gerege/nexus/internal/apps/loan"

// WorkingCapitalLoanBalance stores the money balances of one working-capital
// loan (one row per loan in m_wc_loan_balance). It is the Go port of Fineract's
// WorkingCapitalLoanBalance [VERIFIED: WorkingCapitalLoanBalance.java:24-140].
//
// # derive-don't-store
//
// The outstanding figures are always DERIVED: a balance row stores the raw
// charged/paid/disbursed totals, and every "outstanding" or "due" figure is a
// pure fold over those stored totals. No outstanding column exists. The zero
// value is the correct empty balance (the oracle initialises every field to
// BigDecimal.ZERO).
type WorkingCapitalLoanBalance struct {
	Principal           loan.MinorUnits // principal charged (disbursed + discount)
	PrincipalPaid       loan.MinorUnits // principal repaid
	PrincipalAdjustment loan.MinorUnits // principal written up/down
	Fee                 loan.MinorUnits // fee charged
	FeePaid             loan.MinorUnits // fee repaid
	Penalty             loan.MinorUnits // penalty charged
	PenaltyPaid         loan.MinorUnits // penalty repaid

	RealizedIncomeFromDiscountFee loan.MinorUnits
	OverpaymentAmount             loan.MinorUnits
	TotalDisbursement             loan.MinorUnits
	TotalDiscountFee              loan.MinorUnits
	TotalDiscountFeeAdjustment    loan.MinorUnits
	BreachPastDueAmount           loan.MinorUnits
}

// ApplyDisbursement ports WorkingCapitalLoanBalance.applyDisbursement
// [VERIFIED: WorkingCapitalLoanBalance.java:84-90]: principal becomes
// disbursed + discount, totalDiscountFee becomes discount, and any overpayment
// is reset.
func (b *WorkingCapitalLoanBalance) ApplyDisbursement(disbursed, discount loan.MinorUnits) {
	b.TotalDiscountFee = discount
	b.Principal = disbursed + discount
	b.OverpaymentAmount = 0
}

// TotalPrincipalDue ports getTotalPrincipalDue: principal + principalAdjustment
// [VERIFIED: WorkingCapitalLoanBalance.java:92-94].
func (b WorkingCapitalLoanBalance) TotalPrincipalDue() loan.MinorUnits {
	return b.Principal + b.PrincipalAdjustment
}

// PrincipalOutstanding ports getPrincipalOutstanding:
// max(totalPrincipalDue - principalPaid, 0)
// [VERIFIED: WorkingCapitalLoanBalance.java:96-98].
func (b WorkingCapitalLoanBalance) PrincipalOutstanding() loan.MinorUnits {
	return maxUnits(b.TotalPrincipalDue()-b.PrincipalPaid, 0)
}

// FeeOutstanding ports getFeeOutstanding: max(fee - feePaid, 0)
// [VERIFIED: WorkingCapitalLoanBalance.java:100-102].
func (b WorkingCapitalLoanBalance) FeeOutstanding() loan.MinorUnits {
	return maxUnits(b.Fee-b.FeePaid, 0)
}

// PenaltyOutstanding ports getPenaltyOutstanding: max(penalty - penaltyPaid, 0)
// [VERIFIED: WorkingCapitalLoanBalance.java:104-106].
func (b WorkingCapitalLoanBalance) PenaltyOutstanding() loan.MinorUnits {
	return maxUnits(b.Penalty-b.PenaltyPaid, 0)
}

// TotalOutstanding ports getTotalOutstanding: principal + fee + penalty
// outstanding [VERIFIED: WorkingCapitalLoanBalance.java:108-110].
func (b WorkingCapitalLoanBalance) TotalOutstanding() loan.MinorUnits {
	return b.PrincipalOutstanding() + b.FeeOutstanding() + b.PenaltyOutstanding()
}

// TotalExpectedRepayment ports getTotalExpectedRepayment:
// principal + principalAdjustment + penalty + fee
// [VERIFIED: WorkingCapitalLoanBalance.java:112-114].
func (b WorkingCapitalLoanBalance) TotalExpectedRepayment() loan.MinorUnits {
	return b.Principal + b.PrincipalAdjustment + b.Penalty + b.Fee
}

// TotalRepayment ports getTotalRepayment: principalPaid + feePaid + penaltyPaid
// [VERIFIED: WorkingCapitalLoanBalance.java:116-118].
func (b WorkingCapitalLoanBalance) TotalRepayment() loan.MinorUnits {
	return b.PrincipalPaid + b.FeePaid + b.PenaltyPaid
}

// UnrealizedIncomeFromDiscountFee ports getUnrealizedIncomeFromDiscountFee:
// max(totalDiscountFee - totalDiscountFeeAdjustment - realizedIncomeFromDiscountFee, 0)
// [VERIFIED: WorkingCapitalLoanBalance.java:120-125].
func (b WorkingCapitalLoanBalance) UnrealizedIncomeFromDiscountFee() loan.MinorUnits {
	return maxUnits(b.TotalDiscountFee-b.TotalDiscountFeeAdjustment-b.RealizedIncomeFromDiscountFee, 0)
}

func maxUnits(a, b loan.MinorUnits) loan.MinorUnits {
	if a > b {
		return a
	}
	return b
}
