package loan

import (
	"reflect"
	"testing"
)

// alloc builds an Allocation from minor units in principal, interest, fee,
// penalty order (matching Fineract's allocationMap(double principal, double
// interest, double fee, double penalty, currency) helper).
func alloc(principal, interest, fee, penalty MinorUnits) Allocation {
	return Allocation{Principal: principal, Interest: interest, Fee: fee, Penalty: penalty}
}

func TestAllocationTypeString(t *testing.T) {
	cases := []struct {
		in   AllocationType
		want string
	}{
		{AllocationPenalty, "PENALTY"},
		{AllocationFee, "FEE"},
		{AllocationPrincipal, "PRINCIPAL"},
		{AllocationInterest, "INTEREST"},
	}
	for _, c := range cases {
		if got := c.in.String(); got != c.want {
			t.Errorf("%d String() = %q, want %q", int32(c.in), got, c.want)
		}
	}
}

func TestDueTypeString(t *testing.T) {
	cases := []struct {
		in   DueType
		want string
	}{
		{DuePastDue, "PAST_DUE"},
		{DueDue, "DUE"},
		{DueInAdvance, "IN_ADVANCE"},
	}
	for _, c := range cases {
		if got := c.in.String(); got != c.want {
			t.Errorf("%d String() = %q, want %q", int32(c.in), got, c.want)
		}
	}
}

func TestFutureInstallmentAllocationRuleString(t *testing.T) {
	cases := []struct {
		in   FutureInstallmentAllocationRule
		want string
	}{
		{FutureNextInstallment, "NEXT_INSTALLMENT"},
		{FutureLastInstallment, "LAST_INSTALLMENT"},
		{FutureNextLastInstallment, "NEXT_LAST_INSTALLMENT"},
		{FutureReamortization, "REAMORTIZATION"},
	}
	for _, c := range cases {
		if got := c.in.String(); got != c.want {
			t.Errorf("%d String() = %q, want %q", int32(c.in), got, c.want)
		}
	}
}

func TestPaymentAllocationTypeMapping(t *testing.T) {
	cases := []struct {
		in    PaymentAllocationType
		due   DueType
		alloc AllocationType
		name  string
	}{
		{PaymentPastDuePenalty, DuePastDue, AllocationPenalty, "PAST_DUE_PENALTY"},
		{PaymentPastDueFee, DuePastDue, AllocationFee, "PAST_DUE_FEE"},
		{PaymentPastDuePrincipal, DuePastDue, AllocationPrincipal, "PAST_DUE_PRINCIPAL"},
		{PaymentPastDueInterest, DuePastDue, AllocationInterest, "PAST_DUE_INTEREST"},
		{PaymentDuePenalty, DueDue, AllocationPenalty, "DUE_PENALTY"},
		{PaymentDueFee, DueDue, AllocationFee, "DUE_FEE"},
		{PaymentDuePrincipal, DueDue, AllocationPrincipal, "DUE_PRINCIPAL"},
		{PaymentDueInterest, DueDue, AllocationInterest, "DUE_INTEREST"},
		{PaymentInAdvancePenalty, DueInAdvance, AllocationPenalty, "IN_ADVANCE_PENALTY"},
		{PaymentInAdvanceFee, DueInAdvance, AllocationFee, "IN_ADVANCE_FEE"},
		{PaymentInAdvancePrincipal, DueInAdvance, AllocationPrincipal, "IN_ADVANCE_PRINCIPAL"},
		{PaymentInAdvanceInterest, DueInAdvance, AllocationInterest, "IN_ADVANCE_INTEREST"},
	}
	for _, c := range cases {
		if got := c.in.DueType(); got != c.due {
			t.Errorf("%s DueType() = %v, want %v", c.in, got, c.due)
		}
		if got := c.in.AllocationType(); got != c.alloc {
			t.Errorf("%s AllocationType() = %v, want %v", c.in, got, c.alloc)
		}
		if got := c.in.String(); got != c.name {
			t.Errorf("PaymentAllocationType(%d) String() = %q, want %q", int32(c.in), got, c.name)
		}
	}
}

// TestAllocateCreditFineractVectors ports, unchanged, the five captured
// expectations in Fineract's own calculateChargebackAllocationMap test
// [VERIFIED: AdvancedPaymentScheduleTransactionProcessorTest.java:640-678].
// The USD 2-decimal amounts are expressed in minor units.
func TestAllocateCreditFineractVectors(t *testing.T) {
	cases := []struct {
		name     string
		original Allocation
		amount   MinorUnits
		order    []AllocationType
		want     Allocation
	}{
		{
			name:     "exact principal, zero remainder",
			original: alloc(5000, 10000, 20000, 1200),
			amount:   5000,
			order:    []AllocationType{AllocationPrincipal, AllocationInterest, AllocationFee, AllocationPenalty},
			want:     alloc(5000, 0, 0, 0),
		},
		{
			name:     "spill to next bucket",
			original: alloc(4000, 10000, 20000, 1200),
			amount:   5000,
			order:    []AllocationType{AllocationPrincipal, AllocationInterest, AllocationFee, AllocationPenalty},
			want:     alloc(4000, 1000, 0, 0),
		},
		{
			name:     "order determines which bucket receives the spill",
			original: alloc(4000, 10000, 20000, 1200),
			amount:   5000,
			order:    []AllocationType{AllocationPrincipal, AllocationFee, AllocationPenalty, AllocationInterest},
			want:     alloc(4000, 0, 1000, 0),
		},
		{
			name:     "large payment partially fills final bucket",
			original: alloc(4000, 10000, 20000, 1200),
			amount:   34000,
			order:    []AllocationType{AllocationPrincipal, AllocationFee, AllocationPenalty, AllocationInterest},
			want:     alloc(4000, 8800, 20000, 1200),
		},
		{
			name:     "full coverage caps interest at outstanding",
			original: alloc(4000, 10000, 20000, 1200),
			amount:   35200,
			order:    []AllocationType{AllocationPrincipal, AllocationFee, AllocationPenalty, AllocationInterest},
			want:     alloc(4000, 10000, 20000, 1200),
		},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := AllocateCredit(c.original, c.amount, c.order); !reflect.DeepEqual(got, c.want) {
				t.Errorf("AllocateCredit() = %+v, want %+v", got, c.want)
			}
		})
	}
}

func TestAllocateInOrderEdgeCases(t *testing.T) {
	t.Run("zero amount allocates nothing", func(t *testing.T) {
		got, remaining := AllocateInOrder(alloc(100, 200, 300, 400), 0,
			[]AllocationType{AllocationPenalty, AllocationFee, AllocationPrincipal, AllocationInterest})
		if got != (Allocation{}) {
			t.Errorf("AllocateInOrder() = %+v, want zero Allocation", got)
		}
		if remaining != 0 {
			t.Errorf("remaining = %d, want 0", remaining)
		}
	})

	t.Run("zero and negative buckets are skipped", func(t *testing.T) {
		// Fee and Penalty are <= 0 and must never absorb payment, even though
		// they precede Principal in the order.
		got, remaining := AllocateInOrder(alloc(1000, 0, 0, -50), 500,
			[]AllocationType{AllocationPenalty, AllocationFee, AllocationPrincipal, AllocationInterest})
		want := alloc(500, 0, 0, 0)
		if !reflect.DeepEqual(got, want) {
			t.Errorf("AllocateInOrder() = %+v, want %+v", got, want)
		}
		if remaining != 0 {
			t.Errorf("remaining = %d, want 0", remaining)
		}
	})

	t.Run("over-payment leaves the remainder unallocated", func(t *testing.T) {
		got, remaining := AllocateInOrder(alloc(1000, 500, 300, 200), 2500,
			[]AllocationType{AllocationPenalty, AllocationFee, AllocationInterest, AllocationPrincipal})
		want := alloc(1000, 500, 300, 200)
		if !reflect.DeepEqual(got, want) {
			t.Errorf("AllocateInOrder() = %+v, want %+v", got, want)
		}
		if remaining != 500 {
			t.Errorf("remaining = %d, want 500", remaining)
		}
	})

	t.Run("order not covering all buckets only fills listed buckets", func(t *testing.T) {
		got, remaining := AllocateInOrder(alloc(1000, 500, 300, 200), 1500,
			[]AllocationType{AllocationPrincipal, AllocationInterest})
		want := alloc(1000, 500, 0, 0)
		if !reflect.DeepEqual(got, want) {
			t.Errorf("AllocateInOrder() = %+v, want %+v", got, want)
		}
		if remaining != 0 {
			t.Errorf("remaining = %d, want 0", remaining)
		}
	})
}

// TestAllocatePayment exercises the repayment-side entry point. The mifos
// standard strategy ("penalties, fees, interest, principal") is the order used
// by Fineract's FineractStyleLoanRepaymentScheduleTransactionProcessor
// [VERIFIED: FineractStyleLoanRepaymentScheduleTransactionProcessor.java].
func TestAllocatePayment(t *testing.T) {
	mifosOrder := []PaymentAllocationType{
		PaymentDuePenalty, PaymentDueFee, PaymentDueInterest, PaymentDuePrincipal,
	}

	t.Run("penalty fee interest principal order", func(t *testing.T) {
		got, remaining := AllocatePayment(alloc(10000, 5000, 3000, 2000), 15000, mifosOrder)
		want := alloc(5000, 5000, 3000, 2000)
		if !reflect.DeepEqual(got, want) {
			t.Errorf("AllocatePayment() = %+v, want %+v", got, want)
		}
		if remaining != 0 {
			t.Errorf("remaining = %d, want 0", remaining)
		}
	})

	t.Run("principal first order", func(t *testing.T) {
		order := []PaymentAllocationType{
			PaymentDuePrincipal, PaymentDueInterest, PaymentDueFee, PaymentDuePenalty,
		}
		got, remaining := AllocatePayment(alloc(10000, 5000, 3000, 2000), 15000, order)
		want := alloc(10000, 5000, 0, 0)
		if !reflect.DeepEqual(got, want) {
			t.Errorf("AllocatePayment() = %+v, want %+v", got, want)
		}
		if remaining != 0 {
			t.Errorf("remaining = %d, want 0", remaining)
		}
	})

	t.Run("partial payment leaves principal untouched", func(t *testing.T) {
		got, remaining := AllocatePayment(alloc(10000, 5000, 3000, 2000), 6000, mifosOrder)
		want := alloc(0, 1000, 3000, 2000)
		if !reflect.DeepEqual(got, want) {
			t.Errorf("AllocatePayment() = %+v, want %+v", got, want)
		}
		if remaining != 0 {
			t.Errorf("remaining = %d, want 0", remaining)
		}
	})

	t.Run("over-payment returns unprocessed amount", func(t *testing.T) {
		got, remaining := AllocatePayment(alloc(10000, 5000, 3000, 2000), 25000, mifosOrder)
		want := alloc(10000, 5000, 3000, 2000)
		if !reflect.DeepEqual(got, want) {
			t.Errorf("AllocatePayment() = %+v, want %+v", got, want)
		}
		if remaining != 5000 {
			t.Errorf("remaining = %d, want 5000", remaining)
		}
	})
}
