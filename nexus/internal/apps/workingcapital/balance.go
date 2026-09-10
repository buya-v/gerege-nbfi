package workingcapital

import (
	"errors"
	"fmt"

	"github.com/gerege/nexus/internal/apps/loan"
)

// WorkingCapitalLoanBalance stores the money balances of one working-capital
// loan (one row per loan in m_wc_loan_balance). It is the Go port of Fineract's
// WorkingCapitalLoanBalance [VERIFIED: WorkingCapitalLoanBalance.java:45-156].
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

// ErrNoGradedCapture is returned when a balance carries a non-zero value in a
// money term no committed capture has ever observed as non-zero. It is the
// working-capital spelling of a discipline other contexts state through their
// own refusal idioms (loanschedule at its request seam, loan through an error
// sentinel): the port REFUSES to answer a question no vector has ever asked
// rather than silently computing a value no capture can grade.
//
// The spelling is deliberately a sentinel error rather than a formatted string:
// the seam here admits a balance value, not a request, so callers can tell a
// refusal from a decode failure with errors.Is.
var ErrNoGradedCapture = errors.New("workingcapital: money term not graded by any committed capture")

// ungradedTerm is one stored money term and the reason no committed capture can
// grade a non-zero value for it.
type ungradedTerm struct {
	name  string
	value loan.MinorUnits
	why   string
}

// ValidateGradedDomain refuses a balance that carries a non-zero value in any
// money term the committed working-capital captures cannot discriminate.
//
// TWO stored money terms are now observed at a non-zero value and are therefore
// not checked:
//
//   - Principal, 100051 minor in wc-loan-detail-raw.json (the no-discount seed);
//   - TotalDiscountFee, 3753 minor in the discount-nonzero capture
//     (wc-loan-discount-detail-raw.json, facility 2), promoted by OH-WCGRADE-Q.
//
// Every OTHER stored term is zero in every balance the captures serialise, so a
// port that drops the term, or returns a constant zero for it, passes every
// vector that mentions it. The derived folds are pure over a state this method
// has admitted; it is the seam that admits the state, in the spirit of
// loanschedule's validateGradedDomain, and it is called once before the getters
// run.
//
// The clamp in UnrealizedIncomeFromDiscountFee is STILL not exercised, and this
// method still refuses its remaining operands. The first operand,
// TotalDiscountFee, is now non-zero (3753), but TotalDiscountFeeAdjustment and
// RealizedIncomeFromDiscountFee are both still 0, so the un-clamped expression
// TotalDiscountFee - adjustment - realized stays POSITIVE (max(3753, 0)); the
// max(..., 0) floor itself is ungraded (a port omitting it computes the same
// answer). Refusing TotalDiscountFeeAdjustment and
// RealizedIncomeFromDiscountFee is what keeps the clamp from being answerable
// while it cannot be graded. See
// .softhouse/findings/F-2026-09-10-workingcapital-discount-fee-graded.md (and
// its predecessor F-2026-09-10-workingcapital-ungraded-terms.md) for what a
// capture would need to drive each remaining term.
func (b WorkingCapitalLoanBalance) ValidateGradedDomain() error {
	for _, t := range []ungradedTerm{
		{"PrincipalPaid", b.PrincipalPaid, "the capture records principalPaid 0 (no working-capital repayment has ever been captured), so no vector grades a non-zero principal paid"},
		{"PrincipalAdjustment", b.PrincipalAdjustment, "the capture records principalAdjustment 0, so no vector grades a write-up or write-down"},
		{"Fee", b.Fee, "the captured product carries no charges and the capture records fee 0, so no vector grades a non-zero fee"},
		{"FeePaid", b.FeePaid, "the capture records feePaid 0, so no vector grades a non-zero fee paid"},
		{"Penalty", b.Penalty, "the captured product carries no charges and the capture records penalty 0, so no vector grades a non-zero penalty"},
		{"PenaltyPaid", b.PenaltyPaid, "the capture records penaltyPaid 0, so no vector grades a non-zero penalty paid"},
		{"RealizedIncomeFromDiscountFee", b.RealizedIncomeFromDiscountFee, "the capture records realizedIncomeFromDiscountFee 0; it is an operand of the UnrealizedIncomeFromDiscountFee clamp, which no vector exercises (the other operand, totalDiscountFee, is now graded but this one is not)"},
		{"OverpaymentAmount", b.OverpaymentAmount, "the capture records overpaymentAmount 0, so no vector grades an overpayment"},
		{"TotalDisbursement", b.TotalDisbursement, "the capture records totalDisbursement 0 and the reference working-capital module has no call site that ever sets it (setTotalDisbursement has no caller under its src/main), so no capture can produce a non-zero value to grade"},
		{"TotalDiscountFeeAdjustment", b.TotalDiscountFeeAdjustment, "the capture records totalDiscountFeeAdjustment 0; it is an operand of the UnrealizedIncomeFromDiscountFee clamp, and nothing grades the clamp"},
		{"BreachPastDueAmount", b.BreachPastDueAmount, "the capture records breachPastDueAmount 0, so no vector grades a breach amount"},
	} {
		if t.value != 0 {
			return fmt.Errorf("%w: working-capital balance %s is %d; %s", ErrNoGradedCapture, t.name, t.value, t.why)
		}
	}
	return nil
}

// ApplyDisbursement ports WorkingCapitalLoanBalance.applyDisbursement
// [VERIFIED: WorkingCapitalLoanBalance.java:115-121]: principal becomes
// disbursed + discount, totalDiscountFee becomes discount, and any overpayment
// is reset.
//
// The discount the product carries is now GRADED: OH-WCGRADE-Q observed a
// facility disbursed with discount 3753 on a product whose discount is 37.53
// MNT, and TotalDiscountFee was removed from the refusal set, so the resulting
// state is admitted when no ungraded term is non-zero. The would-be state is
// still validated before the receiver is touched, so a call refused for some
// other ungraded term leaves the balance exactly as it was. The no-discount
// seed (100051, 0) and the discount-nonzero capture (100000, 3753) are both
// admitted; the latter yields principal 103753 and totalDiscountFee 3753.
func (b *WorkingCapitalLoanBalance) ApplyDisbursement(disbursed, discount loan.MinorUnits) error {
	next := *b
	next.TotalDiscountFee = discount
	next.Principal = disbursed + discount
	next.OverpaymentAmount = 0
	if err := next.ValidateGradedDomain(); err != nil {
		return err
	}
	*b = next
	return nil
}

// TotalPrincipalDue ports getTotalPrincipalDue: principal + principalAdjustment
// [VERIFIED: WorkingCapitalLoanBalance.java:123-125].
func (b WorkingCapitalLoanBalance) TotalPrincipalDue() loan.MinorUnits {
	return b.Principal + b.PrincipalAdjustment
}

// PrincipalOutstanding ports getPrincipalOutstanding:
// max(totalPrincipalDue - principalPaid, 0)
// [VERIFIED: WorkingCapitalLoanBalance.java:127-129].
func (b WorkingCapitalLoanBalance) PrincipalOutstanding() loan.MinorUnits {
	return maxUnits(b.TotalPrincipalDue()-b.PrincipalPaid, 0)
}

// FeeOutstanding ports getFeeOutstanding: max(fee - feePaid, 0)
// [VERIFIED: WorkingCapitalLoanBalance.java:131-133].
func (b WorkingCapitalLoanBalance) FeeOutstanding() loan.MinorUnits {
	return maxUnits(b.Fee-b.FeePaid, 0)
}

// PenaltyOutstanding ports getPenaltyOutstanding: max(penalty - penaltyPaid, 0)
// [VERIFIED: WorkingCapitalLoanBalance.java:135-137].
func (b WorkingCapitalLoanBalance) PenaltyOutstanding() loan.MinorUnits {
	return maxUnits(b.Penalty-b.PenaltyPaid, 0)
}

// TotalOutstanding ports getTotalOutstanding: principal + fee + penalty
// outstanding [VERIFIED: WorkingCapitalLoanBalance.java:139-141].
func (b WorkingCapitalLoanBalance) TotalOutstanding() loan.MinorUnits {
	return b.PrincipalOutstanding() + b.FeeOutstanding() + b.PenaltyOutstanding()
}

// TotalExpectedRepayment ports getTotalExpectedRepayment:
// principal + principalAdjustment + penalty + fee
// [VERIFIED: WorkingCapitalLoanBalance.java:143-145].
func (b WorkingCapitalLoanBalance) TotalExpectedRepayment() loan.MinorUnits {
	return b.Principal + b.PrincipalAdjustment + b.Penalty + b.Fee
}

// TotalRepayment ports getTotalRepayment: principalPaid + feePaid + penaltyPaid
// [VERIFIED: WorkingCapitalLoanBalance.java:147-149].
func (b WorkingCapitalLoanBalance) TotalRepayment() loan.MinorUnits {
	return b.PrincipalPaid + b.FeePaid + b.PenaltyPaid
}

// UnrealizedIncomeFromDiscountFee ports getUnrealizedIncomeFromDiscountFee:
// max(totalDiscountFee - totalDiscountFeeAdjustment - realizedIncomeFromDiscountFee, 0)
// [VERIFIED: WorkingCapitalLoanBalance.java:151-155].
func (b WorkingCapitalLoanBalance) UnrealizedIncomeFromDiscountFee() loan.MinorUnits {
	return maxUnits(b.TotalDiscountFee-b.TotalDiscountFeeAdjustment-b.RealizedIncomeFromDiscountFee, 0)
}

func maxUnits(a, b loan.MinorUnits) loan.MinorUnits {
	if a > b {
		return a
	}
	return b
}
