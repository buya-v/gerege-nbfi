package loan

// Allocation is the four-bucket money breakdown a repayment or credit decision
// reads from and writes to. It is the Go port of the oracle's
// Map<AllocationType, Money> that AdvancedPaymentScheduleTransactionProcessor
// threads through its allocation paths, and of the principal/interest/fee/
// penalty portions of a LoanTransactionToRepaymentScheduleMapping
// [VERIFIED: AdvancedPaymentScheduleTransactionProcessor.java:1348-1366,
// LoanTransactionToRepaymentScheduleMapping.java:getPrincipalPortion et al.].
//
// # G-12 derive-don't-store
//
// Allocation is a pure computation result. The four buckets are always
// recomputed from their inputs; nothing here is a persisted balance, and there
// is no write path. This is the arithmetic slice, not the schedule or ledger
// machinery that surrounds it.
type Allocation struct {
	Principal MinorUnits
	Interest  MinorUnits
	Fee       MinorUnits
	Penalty   MinorUnits
}

// Total returns the sum of the four buckets.
func (a Allocation) Total() MinorUnits {
	return a.Principal + a.Interest + a.Fee + a.Penalty
}

// For returns the bucket value for t.
func (a Allocation) For(t AllocationType) MinorUnits {
	switch t {
	case AllocationPenalty:
		return a.Penalty
	case AllocationFee:
		return a.Fee
	case AllocationPrincipal:
		return a.Principal
	case AllocationInterest:
		return a.Interest
	}
	return 0
}

// Set assigns the bucket value for t.
func (a *Allocation) Set(t AllocationType, v MinorUnits) {
	switch t {
	case AllocationPenalty:
		a.Penalty = v
	case AllocationFee:
		a.Fee = v
	case AllocationPrincipal:
		a.Principal = v
	case AllocationInterest:
		a.Interest = v
	}
}

// Add increments the bucket value for t by v.
func (a *Allocation) Add(t AllocationType, v MinorUnits) {
	a.Set(t, a.For(t)+v)
}

// AllocateInOrder greedily distributes amount across outstanding's buckets in
// order, never exceeding any bucket's outstanding amount. It returns the
// resulting allocation and the amount left unallocated.
//
// This is the shared arithmetic of Fineract's repayment and credit allocation.
// The oracle writes it twice:
//
//   - calculateChargebackAllocationMap, which loops over a List<AllocationType>
//     and moves min(remaining, outstanding) into each bucket in turn
//     [VERIFIED: AdvancedPaymentScheduleTransactionProcessor.java:1348-1366];
//   - processPaymentAllocation, which for each PaymentAllocationType pays the
//     matching component of a single instalment with
//     PaymentFunction.accept -> min(transactionAmountUnprocessed, outstanding)
//     [VERIFIED: AdvancedPaymentScheduleTransactionProcessor.java:2016-2042].
//
// Both reduce to the same greedy min(remaining, outstanding) rule; the only
// difference is the bucket key. A bucket whose outstanding is not positive is
// skipped, exactly as the oracle skips originalAmount.compareTo(ZERO) <= 0.
func AllocateInOrder(outstanding Allocation, amount MinorUnits, order []AllocationType) (Allocation, MinorUnits) {
	remaining := amount
	var result Allocation
	for _, t := range order {
		if remaining <= 0 {
			break
		}
		bucket := outstanding.For(t)
		if bucket <= 0 {
			continue
		}
		if remaining > bucket {
			result.Set(t, bucket)
			remaining -= bucket
		} else {
			result.Set(t, remaining)
			remaining = 0
		}
	}
	return result, remaining
}

// AllocateCredit is the exact port of calculateChargebackAllocationMap: it
// distributes amountToDistribute across the original allocation buckets in
// allocationTypes order, never exceeding a bucket's original amount, and drops
// any remainder (an over-allocation is not surfaced)
// [VERIFIED: AdvancedPaymentScheduleTransactionProcessor.java:1348-1366].
func AllocateCredit(original Allocation, amount MinorUnits, order []AllocationType) Allocation {
	alloc, _ := AllocateInOrder(original, amount, order)
	return alloc
}

// AllocatePayment distributes a repayment amount across a single instalment's
// outstanding buckets, following the product's payment-allocation order. It
// mirrors processPaymentAllocation: each PaymentAllocationType in turn fills
// its paired bucket up to min(remaining, outstanding). The returned remaining
// amount is the oracle's transactionAmountUnprocessed, which the repayment
// processor then routes to overpayment or a further instalment
// [VERIFIED: AdvancedPaymentScheduleTransactionProcessor.java:2016-2042].
//
// Because a single instalment carries one outstanding amount per bucket, the
// DueType on each PaymentAllocationType is irrelevant to the bucket arithmetic
// here — DueType drives instalment selection in the schedule processors, which
// is outside this arithmetic slice.
func AllocatePayment(outstanding Allocation, amount MinorUnits, order []PaymentAllocationType) (Allocation, MinorUnits) {
	types := make([]AllocationType, len(order))
	for i, p := range order {
		types[i] = p.AllocationType()
	}
	return AllocateInOrder(outstanding, amount, types)
}
