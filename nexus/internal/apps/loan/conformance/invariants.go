package conformance

import (
	"fmt"
	"strconv"
)

// The property invariants this context can grade. The loan slice's gradeable
// invariants are structural money-integrity properties of the allocation and
// disbursement results, asserted on an implementation's RESULT rather than
// re-derived here. They are always asserted, so a pass means the implementation
// returned non-negative integer minor-unit money, never a float or a negative.

// InvariantStatus is the outcome of one invariant assertion.
type InvariantStatus string

const (
	InvariantHeld          InvariantStatus = "HOLD"
	InvariantViolated      InvariantStatus = "VIOLATED"
	InvariantNotApplicable InvariantStatus = "N/A"
)

// InvariantResult is one invariant's verdict on one vector.
type InvariantResult struct {
	Name       string
	Status     InvariantStatus
	Assertions int
	Detail     string
}

// AssertInvariants runs every gradeable loan invariant against the result an
// implementation returned. The seam decides the set.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	switch v.Oracle.Seam {
	case SeamLoanRepaymentAllocation:
		return []InvariantResult{assertAllocationNonNegative(got)}
	case SeamLoanScheduleInterest:
		return []InvariantResult{assertInterestNonNegative(got)}
	case SeamLoanSummaryOutstanding:
		return []InvariantResult{assertSummaryTotalNonNegative(got)}
	case SeamLoanStatus:
		return []InvariantResult{assertStatusIdentity(v, got)}
	case SeamLoanTransactionBalance:
		return []InvariantResult{assertTransactionBalances(v, got)}
	case SeamLoanJournalEntryBatchBalance:
		return []InvariantResult{assertJournalEntryBatchBalances(got)}
	case SeamLoanScheduleAmortization:
		return []InvariantResult{assertPrincipalAmortizesToZero(v, got)}
	case SeamLoanDelinquentDays:
		return []InvariantResult{assertDelinquentDaysConsistent(got)}
	default:
		return []InvariantResult{assertNetDisbursalNonNegative(got)}
	}
}

// assertAllocationNonNegative: every allocated bucket and the leftover are
// non-negative integer minor-unit amounts. A bucket or leftover that is
// negative, empty or fractional cannot be a transcription of a greedy
// allocation the oracle could have produced.
func assertAllocationNonNegative(got Expect) InvariantResult {
	r := InvariantResult{Name: "allocation_non_negative", Assertions: 5}
	if got.Allocation == nil {
		r.Status = InvariantViolated
		r.Detail = "allocation is nil"
		return r
	}
	for name, val := range map[string]string{
		"penalty":   got.Allocation.Penalty,
		"fee":       got.Allocation.Fee,
		"interest":  got.Allocation.Interest,
		"principal": got.Allocation.Principal,
		"leftover":  got.LeftoverMinor,
	} {
		if !isIntegerMinorString(val) {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("allocation %s %q is not a non-negative integer minor amount", name, val)
			return r
		}
	}
	r.Status = InvariantHeld
	r.Detail = "all five allocation cells are non-negative integer minor units"
	return r
}

// assertInterestNonNegative: the single-period interest is a non-negative
// integer minor-unit amount.
func assertInterestNonNegative(got Expect) InvariantResult {
	r := InvariantResult{Name: "interest_non_negative", Assertions: 1}
	if !isIntegerMinorString(got.InterestMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("interest %q is not a non-negative integer minor amount", got.InterestMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("interest %q is a non-negative integer minor amount", got.InterestMinor)
	return r
}

// assertSummaryTotalNonNegative: the derived total outstanding is a
// non-negative integer minor-unit amount.
func assertSummaryTotalNonNegative(got Expect) InvariantResult {
	r := InvariantResult{Name: "summary_total_non_negative", Assertions: 1}
	if !isIntegerMinorString(got.SummaryTotalMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("summary total %q is not a non-negative integer minor amount", got.SummaryTotalMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("summary total %q is a non-negative integer minor amount", got.SummaryTotalMinor)
	return r
}

// assertStatusIdentity: a decoded loan status must round-trip to the stored
// value it was decoded from and carry a non-empty i18n code. A status that
// re-encodes to a different m_loan.loan_status_id (an iota-collapsed enum)
// breaks persistence identity and is never a transcription of the oracle's
// read-back.
func assertStatusIdentity(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "status_identity", Assertions: 2}
	if got.StatusStoredValue != v.Request.Status.StoredValue {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("decoded status round-trips to %d, not the requested stored value %d",
			got.StatusStoredValue, v.Request.Status.StoredValue)
		return r
	}
	if got.StatusCode == "" {
		r.Status = InvariantViolated
		r.Detail = "status_code is empty"
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("status %d round-trips and reads back as %q", got.StatusStoredValue, got.StatusCode)
	return r
}

// assertNetDisbursalNonNegative: the net disbursal amount is a non-negative
// integer minor-unit amount.
func assertNetDisbursalNonNegative(got Expect) InvariantResult {
	r := InvariantResult{Name: "net_disbursal_non_negative", Assertions: 1}
	if !isIntegerMinorString(got.NetDisbursalMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("net_disbursal %q is not a non-negative integer minor amount", got.NetDisbursalMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("net_disbursal %q is a non-negative integer minor amount", got.NetDisbursalMinor)
	return r
}

// assertTransactionBalances: every serialised balance row of a
// transaction-balance result is a non-negative integer minor-unit amount and
// the row count matches the request. A negative or fractional serialised
// balance cannot be a transcription of the oracle's principal-only running
// balance.
func assertTransactionBalances(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "transaction_balances_integer", Assertions: len(v.Request.Transactions)}
	if len(got.TransactionRows) != len(v.Request.Transactions) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("result has %d balance rows for a %d-transaction request",
			len(got.TransactionRows), len(v.Request.Transactions))
		return r
	}
	for i, row := range got.TransactionRows {
		if !row.Serialized {
			continue
		}
		if !isIntegerMinorString(row.BalanceMinor) {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("serialised row %d balance %q is not a non-negative integer minor amount", i, row.BalanceMinor)
			return r
		}
	}
	r.Status = InvariantHeld
	r.Detail = "all serialised balances are non-negative integer minor units; row count matches the request"
	return r
}

// assertJournalEntryBatchBalances: the two derived totals of a loan-produced
// journal-entry batch are non-negative integer minor-unit amounts and
// sum(debits) == sum(credits) EXACTLY. This is the property the seam exists to
// grade: a batch that pairs off within one transaction but not across the whole
// read-back cannot be a transcription of the oracle's double-entry postings.
func assertJournalEntryBatchBalances(got Expect) InvariantResult {
	r := InvariantResult{Name: "journal_entry_batch_balances", Assertions: 3}
	if !isIntegerMinorString(got.JournalEntryDebitsMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("debit total %q is not a non-negative integer minor amount", got.JournalEntryDebitsMinor)
		return r
	}
	if !isIntegerMinorString(got.JournalEntryCreditsMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("credit total %q is not a non-negative integer minor amount", got.JournalEntryCreditsMinor)
		return r
	}
	if got.JournalEntryDebitsMinor != got.JournalEntryCreditsMinor {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("batch does not balance: debits %s != credits %s",
			got.JournalEntryDebitsMinor, got.JournalEntryCreditsMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("batch balances exactly: debits == credits == %s", got.JournalEntryDebitsMinor)
	return r
}

// assertPrincipalAmortizesToZero: over a full repayment schedule the sum of the
// per-period principal components equals the disbursed principal EXACTLY and the
// final outstanding principal balance is EXACTLY zero, in integer minor units
// with no residue. This is the property the whole-schedule seam exists to grade;
// the assertions are on the implementation's RESULT, not re-derived from the
// request, so a port that returns a sum that does not reconcile or a non-zero
// final balance is VIOLATED even if its own arithmetic was self-consistent.
func assertPrincipalAmortizesToZero(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "principal_amortizes_to_zero", Assertions: 4}
	if !isIntegerMinorString(got.PrincipalSumMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("principal sum %q is not a non-negative integer minor amount", got.PrincipalSumMinor)
		return r
	}
	if !isIntegerMinorString(got.FinalPrincipalBalanceMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("final principal balance %q is not a non-negative integer minor amount", got.FinalPrincipalBalanceMinor)
		return r
	}
	if v.Request.ScheduleAmortization != nil {
		want := v.Request.ScheduleAmortization.PrincipalDisbursedMinor
		if got.PrincipalSumMinor != want {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("principal components sum to %s, not the disbursed principal %s", got.PrincipalSumMinor, want)
			return r
		}
	}
	if got.FinalPrincipalBalanceMinor != "0" {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("final outstanding principal balance is %s, not zero: principal does not amortize to zero", got.FinalPrincipalBalanceMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("principal components sum to the disbursed principal %s exactly and the final balance is zero", got.PrincipalSumMinor)
	return r
}

// assertDelinquentDaysConsistent: both day-count cells are non-negative integer
// day counts and the delinquent count never exceeds the overdue count. Fineract
// derives delinquentDays as overdueDays minus paused and grace days, floored at
// zero [delinquency.go:109], so delinquent <= overdue always holds; on every
// observed row pause and grace are zero, so the two are equal. The assertion is
// on the implementation's RESULT, not re-derived from the request, so a port
// whose independent arithmetic is self-consistent but violates the relation is
// still VIOLATED.
func assertDelinquentDaysConsistent(got Expect) InvariantResult {
	r := InvariantResult{Name: "delinquent_days_consistent", Assertions: 2}
	if !isIntegerMinorString(got.OverdueDays) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("overdue days %q is not a non-negative integer day count", got.OverdueDays)
		return r
	}
	if !isIntegerMinorString(got.DelinquentDays) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("delinquent days %q is not a non-negative integer day count", got.DelinquentDays)
		return r
	}
	overdue, _ := strconv.ParseInt(got.OverdueDays, 10, 64)
	delinquent, _ := strconv.ParseInt(got.DelinquentDays, 10, 64)
	if delinquent > overdue {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("delinquent days %d exceed overdue days %d", delinquent, overdue)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("overdue days %s and delinquent days %s are non-negative integer day counts with delinquent <= overdue", got.OverdueDays, got.DelinquentDays)
	return r
}
