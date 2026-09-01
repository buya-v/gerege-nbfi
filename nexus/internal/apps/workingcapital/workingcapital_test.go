package workingcapital

import (
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

func TestApplyDisbursement(t *testing.T) {
	var b WorkingCapitalLoanBalance
	b.ApplyDisbursement(1_000_00, 50_00)
	if b.TotalDiscountFee != 50_00 {
		t.Fatalf("TotalDiscountFee = %d, want 5000", b.TotalDiscountFee)
	}
	if b.Principal != 1_050_00 {
		t.Fatalf("Principal = %d, want 105000", b.Principal)
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
