package workingcapital

import (
	"errors"
	"strings"
	"testing"

	"github.com/gerege/nexus/internal/apps/loan"
)

func TestPaymentAllocationTypeNeverInterest(t *testing.T) {
	all := []WorkingCapitalPaymentAllocationType{
		WCPaymentDuePenalty, WCPaymentDueFee, WCPaymentDuePrincipal,
		WCPaymentInAdvancePenalty, WCPaymentInAdvanceFee, WCPaymentInAdvancePrincipal,
	}
	for _, p := range all {
		if p.AllocationType() == loan.AllocationInterest {
			t.Fatalf("%v mapped to interest, but working-capital loans have no interest bucket", p)
		}
	}
	if got := WCPaymentDuePenalty.String(); got != "DUE_PENALTY" {
		t.Fatalf("String() = %q, want DUE_PENALTY", got)
	}
	if WCPaymentDuePenalty.DueType() != loan.DueDue {
		t.Fatalf("DUE_PENALTY DueType = %v, want DUE", WCPaymentDuePenalty.DueType())
	}
	if WCPaymentInAdvancePrincipal.DueType() != loan.DueInAdvance {
		t.Fatalf("IN_ADVANCE_PRINCIPAL DueType = %v, want IN_ADVANCE", WCPaymentInAdvancePrincipal.DueType())
	}
	if WCPaymentDuePrincipal.AllocationType() != loan.AllocationPrincipal {
		t.Fatalf("DUE_PRINCIPAL AllocationType = %v, want PRINCIPAL", WCPaymentDuePrincipal.AllocationType())
	}
}

func TestBalanceOutstandingDerivations(t *testing.T) {
	b := WorkingCapitalLoanBalance{
		Principal:                     1_000_00,
		PrincipalPaid:                 400_00,
		PrincipalAdjustment:           50_00,
		Fee:                           100_00,
		FeePaid:                       25_00,
		Penalty:                       30_00,
		PenaltyPaid:                   30_00,
		TotalDiscountFee:              100_00,
		RealizedIncomeFromDiscountFee: 40_00,
	}
	if got, want := b.TotalPrincipalDue(), loan.MinorUnits(1_050_00); got != want {
		t.Fatalf("TotalPrincipalDue = %d, want %d", got, want)
	}
	if got, want := b.PrincipalOutstanding(), loan.MinorUnits(650_00); got != want {
		t.Fatalf("PrincipalOutstanding = %d, want %d", got, want)
	}
	if got, want := b.FeeOutstanding(), loan.MinorUnits(75_00); got != want {
		t.Fatalf("FeeOutstanding = %d, want %d", got, want)
	}
	if got := b.PenaltyOutstanding(); got != 0 {
		t.Fatalf("PenaltyOutstanding = %d, want 0 (never negative)", got)
	}
	if got, want := b.TotalOutstanding(), loan.MinorUnits(725_00); got != want {
		t.Fatalf("TotalOutstanding = %d, want %d", got, want)
	}
	if got, want := b.TotalExpectedRepayment(), loan.MinorUnits(1_180_00); got != want {
		t.Fatalf("TotalExpectedRepayment = %d, want %d", got, want)
	}
	if got, want := b.TotalRepayment(), loan.MinorUnits(455_00); got != want {
		t.Fatalf("TotalRepayment = %d, want %d", got, want)
	}
	if got, want := b.UnrealizedIncomeFromDiscountFee(), loan.MinorUnits(60_00); got != want {
		t.Fatalf("UnrealizedIncomeFromDiscountFee = %d, want %d", got, want)
	}
}

func TestApplyDisbursementAdmitsGradedDiscount(t *testing.T) {
	var b WorkingCapitalLoanBalance
	if err := b.ApplyDisbursement(1_000_00, 37_53); err != nil {
		t.Fatalf("ApplyDisbursement(graded discount 3753) = %v, want nil", err)
	}
	if b.Principal != 1_037_53 || b.TotalDiscountFee != 37_53 {
		t.Fatalf("discount disbursement = %+v, want principal 103753 and totalDiscountFee 3753", b)
	}
	if got, want := b.UnrealizedIncomeFromDiscountFee(), loan.MinorUnits(37_53); got != want {
		t.Fatalf("UnrealizedIncomeFromDiscountFee = %d, want %d", got, want)
	}
	// The relaxation is for TotalDiscountFee ONLY: a disbursement over a balance
	// that already carries a still-ungraded term is refused, and the refusal
	// leaves the balance untouched.
	dirty := WorkingCapitalLoanBalance{PrincipalPaid: 1}
	if err := dirty.ApplyDisbursement(1_000_00, 37_53); !errors.Is(err, ErrNoGradedCapture) {
		t.Fatalf("ApplyDisbursement over a non-zero ungraded term error = %v, want ErrNoGradedCapture", err)
	}
	if dirty != (WorkingCapitalLoanBalance{PrincipalPaid: 1}) {
		t.Fatalf("a refused disbursement mutated the balance: %+v", dirty)
	}
	if err := b.ApplyDisbursement(1_000_00, 0); err != nil {
		t.Fatalf("ApplyDisbursement(no discount) = %v, want nil", err)
	}
	if b.Principal != 1_000_00 || b.TotalDiscountFee != 0 {
		t.Fatalf("no-discount disbursement = %+v, want principal 100000 and no discount", b)
	}
}

func TestValidateGradedDomain(t *testing.T) {
	var graded WorkingCapitalLoanBalance
	if err := graded.ApplyDisbursement(100051, 0); err != nil {
		t.Fatalf("the pinned capture's balance must be admitted: %v", err)
	}
	if err := graded.ValidateGradedDomain(); err != nil {
		t.Fatalf("the pinned capture's balance must be admitted: %v", err)
	}

	// The discount-nonzero capture is now graded: a balance carrying it (and the
	// principal that includes it) is admitted, while its remaining clamp operand
	// stays refused.
	var discounted WorkingCapitalLoanBalance
	if err := discounted.ApplyDisbursement(100000, 3753); err != nil {
		t.Fatalf("the discount-nonzero capture's balance must be admitted: %v", err)
	}
	if err := discounted.ValidateGradedDomain(); err != nil {
		t.Fatalf("the discount-nonzero capture's balance must be admitted: %v", err)
	}
	if discounted.Principal != 103753 || discounted.TotalDiscountFee != 3753 {
		t.Fatalf("discount-nonzero balance = %+v, want principal 103753 and totalDiscountFee 3753", discounted)
	}

	cases := []struct {
		name string
		set  func(*WorkingCapitalLoanBalance)
	}{
		{"PrincipalPaid", func(b *WorkingCapitalLoanBalance) { b.PrincipalPaid = 1 }},
		{"PrincipalAdjustment", func(b *WorkingCapitalLoanBalance) { b.PrincipalAdjustment = 1 }},
		{"Fee", func(b *WorkingCapitalLoanBalance) { b.Fee = 1 }},
		{"FeePaid", func(b *WorkingCapitalLoanBalance) { b.FeePaid = 1 }},
		{"Penalty", func(b *WorkingCapitalLoanBalance) { b.Penalty = 1 }},
		{"PenaltyPaid", func(b *WorkingCapitalLoanBalance) { b.PenaltyPaid = 1 }},
		{"RealizedIncomeFromDiscountFee", func(b *WorkingCapitalLoanBalance) { b.RealizedIncomeFromDiscountFee = 1 }},
		{"OverpaymentAmount", func(b *WorkingCapitalLoanBalance) { b.OverpaymentAmount = 1 }},
		{"TotalDisbursement", func(b *WorkingCapitalLoanBalance) { b.TotalDisbursement = 1 }},
		{"TotalDiscountFeeAdjustment", func(b *WorkingCapitalLoanBalance) { b.TotalDiscountFeeAdjustment = 1 }},
		{"BreachPastDueAmount", func(b *WorkingCapitalLoanBalance) { b.BreachPastDueAmount = 1 }},
	}
	for _, tc := range cases {
		var b WorkingCapitalLoanBalance
		tc.set(&b)
		err := b.ValidateGradedDomain()
		if !errors.Is(err, ErrNoGradedCapture) {
			t.Fatalf("%s: error = %v, want ErrNoGradedCapture", tc.name, err)
		}
		if !strings.Contains(err.Error(), tc.name) {
			t.Fatalf("%s: refusal %q does not name the term", tc.name, err)
		}
	}
}

func TestTransactionAllocationTotal(t *testing.T) {
	a := ForPortions(500_00, 20_00, 5_00, 0)
	if got := a.Total(); got != 525_00 {
		t.Fatalf("Total = %d, want 52500", got)
	}
	if p := ForChargeAccrual(15_00, true); p.PenaltyChargesPortion != 15_00 || p.FeeChargesPortion != 0 {
		t.Fatalf("penalty accrual = %+v, want penalty only", p)
	}
	if f := ForChargeAccrual(15_00, false); f.FeeChargesPortion != 15_00 || f.PenaltyChargesPortion != 0 {
		t.Fatalf("fee accrual = %+v, want fee only", f)
	}
	if r := ForCreditBalanceRefund(10_00, 30_00); r.PrincipalPortion != 10_00 || r.OverpaymentPortion != 30_00 {
		t.Fatalf("credit balance refund = %+v, want principal 1000 overpayment 3000", r)
	}
}

func TestAllocationTypeListRoundTrip(t *testing.T) {
	types := []WorkingCapitalPaymentAllocationType{
		WCPaymentDuePenalty, WCPaymentDueFee, WCPaymentDuePrincipal,
		WCPaymentInAdvancePenalty, WCPaymentInAdvanceFee, WCPaymentInAdvancePrincipal,
	}
	joined := JoinAllocationTypes(types)
	if joined != "DUE_PENALTY,DUE_FEE,DUE_PRINCIPAL,IN_ADVANCE_PENALTY,IN_ADVANCE_FEE,IN_ADVANCE_PRINCIPAL" {
		t.Fatalf("JoinAllocationTypes = %q", joined)
	}
	back, err := SplitAllocationTypes(joined)
	if err != nil {
		t.Fatalf("SplitAllocationTypes: %v", err)
	}
	if len(back) != len(types) {
		t.Fatalf("round-trip length = %d, want %d", len(back), len(types))
	}
	for i := range types {
		if back[i] != types[i] {
			t.Fatalf("round-trip[%d] = %v, want %v", i, back[i], types[i])
		}
	}
}

func TestAllocationTypeListDeduplicates(t *testing.T) {
	if got := JoinAllocationTypes([]WorkingCapitalPaymentAllocationType{
		WCPaymentDuePenalty, WCPaymentDuePenalty, WCPaymentDueFee,
	}); got != "DUE_PENALTY,DUE_FEE" {
		t.Fatalf("JoinAllocationTypes dedup = %q, want DUE_PENALTY,DUE_FEE", got)
	}
	if got, _ := SplitAllocationTypes("DUE_FEE,DUE_FEE,DUE_PRINCIPAL"); len(got) != 2 {
		t.Fatalf("SplitAllocationTypes dedup len = %d, want 2", len(got))
	}
	if _, err := SplitAllocationTypes("DUE_INTEREST"); err == nil {
		t.Fatal("SplitAllocationTypes accepted an interest value that does not exist")
	}
}
