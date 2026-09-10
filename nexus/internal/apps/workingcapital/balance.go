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
// Principal is the ONE stored money term the pinned capture observes at a
// non-zero value (100051 minor, wc-loan-detail-raw.json); it is therefore not
// checked. Every other stored term is zero in every balance the captures
// serialise (WC-02/WC-03/WC-04), so a port that drops the term, or returns a
// constant zero for it, passes every vector that mentions it. The derived folds
// are pure over a state this method has admitted; it is the seam that admits
// the state, in the spirit of loanschedule's validateGradedDomain, and it is
// called once before the getters run.
//
// The clamp in UnrealizedIncomeFromDiscountFee is the sharpest case. It is
// observable only when TotalDiscountFee - TotalDiscountFeeAdjustment -
// RealizedIncomeFromDiscountFee goes NEGATIVE, which requires non-zero
// operands. No capture has one, so no vector exercises the clamp at all;
// refusing each operand here is the only thing between the clamp and a
// silently wrong answer. See
// .softhouse/findings/F-2026-09-10-workingcapital-ungraded-terms.md for the
// capture each term would need in order to be graded.
func (b WorkingCapitalLoanBalance) ValidateGradedDomain() error {
	for _, t := range []ungradedTerm{
		{"PrincipalPaid", b.PrincipalPaid, "the capture records principalPaid 0 (no working-capital repayment has ever been captured), so no vector grades a non-zero principal paid"},
		{"PrincipalAdjustment", b.PrincipalAdjustment, "the capture records principalAdjustment 0, so no vector grades a write-up or write-down"},
		{"Fee", b.Fee, "the captured product carries no charges and the capture records fee 0, so no vector grades a non-zero fee"},
		{"FeePaid", b.FeePaid, "the capture records feePaid 0, so no vector grades a non-zero fee paid"},
		{"Penalty", b.Penalty, "the captured product carries no charges and the capture records penalty 0, so no vector grades a non-zero penalty"},
		{"PenaltyPaid", b.PenaltyPaid, "the capture records penaltyPaid 0, so no vector grades a non-zero penalty paid"},
		{"RealizedIncomeFromDiscountFee", b.RealizedIncomeFromDiscountFee, "the capture records realizedIncomeFromDiscountFee 0; it is an operand of the UnrealizedIncomeFromDiscountFee clamp, which no vector exercises"},
		{"OverpaymentAmount", b.OverpaymentAmount, "the capture records overpaymentAmount 0, so no vector grades an overpayment"},
		{"TotalDisbursement", b.TotalDisbursement, "the capture records totalDisbursement 0 and the reference working-capital module has no call site that ever sets it (setTotalDisbursement has no caller under its src/main), so no capture can produce a non-zero value to grade"},
		{"TotalDiscountFee", b.TotalDiscountFee, "the capture was disbursed with no discount and records totalDiscountFee 0; the discount is the first operand of the UnrealizedIncomeFromDiscountFee clamp, which no vector exercises"},
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
// A discount is REFUSED rather than applied when no committed capture has
// graded the resulting state: a non-zero totalDiscountFee is an operand of the
// UnrealizedIncomeFromDiscountFee clamp, and no vector has ever driven that
// clamp. The would-be state is validated before the receiver is touched, so a
// refused call leaves the balance exactly as it was. The graded seed
// (100051, 0) is admitted.
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
