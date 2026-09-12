package conformance

import (
	"fmt"
	"strconv"

	"github.com/gerege/nexus/internal/apps/loan"
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
	case SeamLoanWriteOffFourBucket:
		return []InvariantResult{assertWriteOffFourBucketsSum(got)}
	case SeamLoanTransactionReversal:
		return []InvariantResult{assertReversalAppendOnly(v, got)}
	case SeamLoanWriteOffJournalEntries:
		return []InvariantResult{assertWriteOffJournalBalanced(got)}
	case SeamLoanChargeOffJournalEntries:
		return []InvariantResult{assertChargeOffJournalBalanced(got)}
	case SeamLoanChargedOffWriteOffJournalEntries:
		return []InvariantResult{assertChargedOffWriteOffJournalBalanced(got)}
	case SeamLoanRepaymentJournalEntries:
		return []InvariantResult{assertRepaymentJournalBalanced(got)}
	case SeamLoanGoodwillCreditJournalEntries:
		return []InvariantResult{assertGoodwillCreditJournalBalanced(got)}
	case SeamLoanDisbursementJournalEntries:
		return []InvariantResult{assertDisbursementJournalBalanced(got)}
	case SeamLoanChargeAdjustmentJournalEntries:
		return []InvariantResult{assertChargeAdjustmentJournalBalanced(got)}
	case SeamLoanChargedOffRepaymentJournalEntries:
		return []InvariantResult{assertChargedOffRepaymentJournalBalanced(got)}
	case SeamLoanChargedOffMerchantRefundJournalEntries:
		return []InvariantResult{assertChargedOffMerchantRefundJournalBalanced(got)}
	case SeamLoanAccrualJournalEntries:
		return []InvariantResult{assertAccrualJournalBalanced(got)}
	case SeamLoanChargebackJournalEntries:
		return []InvariantResult{assertChargebackJournalBalanced(got)}
	case SeamLoanBuyDownFeeJournalEntries:
		return []InvariantResult{assertBuyDownFeeJournalBalanced(got)}
	case SeamLoanCreditBalanceRefundJournalEntries:
		return []InvariantResult{assertCreditBalanceRefundJournalBalanced(got)}
	case SeamLoanInterestPaymentWaiverJournalEntries:
		return []InvariantResult{assertInterestPaymentWaiverJournalBalanced(got)}
	case SeamLoanCapitalizedIncomeAmortizationJournalEntries:
		return []InvariantResult{assertCapitalizedIncomeAmortizationJournalBalanced(got)}
	case SeamLoanChargeLifecycle:
		return []InvariantResult{assertChargeStatesConserved(v, got)}
	case SeamLoanStatusTransition:
		return []InvariantResult{assertStatusTransitionIdentity(v, got)}
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

// assertStatusTransitionIdentity: the status a lifecycle transition returns must
// be a legal decoded loan status whose i18n code matches the stored value it
// round-trips to. This is the persistence-identity property: a port that
// returns a right-looking code off a wrong m_loan.loan_status_id (or a code that
// does not belong to the status it stores) breaks the decode round-trip and is
// never a transcription of the oracle's read-back. The request's own `from`
// status is asserted legal too, so a vector cannot smuggle an out-of-band
// ordinal past admission. The assertion is on the implementation's RESULT, so an
// independently self-consistent port still fails here.
func assertStatusTransitionIdentity(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "status_transition_identity", Assertions: 3}
	req := v.Request.StatusTransition
	if req == nil {
		r.Status = InvariantViolated
		r.Detail = "loan-status-transition request is nil"
		return r
	}
	st, ok := loan.LoanStatusFromStoredValue(got.NextStatusStoredValue)
	if !ok {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("next status stored value %d is not a legal loan status", got.NextStatusStoredValue)
		return r
	}
	if got.NextStatusCode == "" {
		r.Status = InvariantViolated
		r.Detail = "next_status_code is empty"
		return r
	}
	if st.Code() != got.NextStatusCode {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("next status stored value %d decodes to %q, not the returned code %q",
			got.NextStatusStoredValue, st.Code(), got.NextStatusCode)
		return r
	}
	if _, ok := loan.LoanStatusFromStoredValue(req.FromStoredValue); !ok {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("request from_stored_value %d is not a legal loan status", req.FromStoredValue)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("next status %d decodes to %q and the from status %d is legal",
		got.NextStatusStoredValue, got.NextStatusCode, req.FromStoredValue)
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

// assertChargeStatesConserved: every state of a charge-lifecycle result carries
// non-negative integer minor-unit money, the state count matches the request's
// operations plus the created state, no state is flagged both fully paid and
// fully waived, and the charge's amount is CONSERVED across the three cells —
// amountPaid + amountWaived + amountOutstanding equals the requested amount
// EXACTLY, state by state. The assertions are on the implementation's RESULT: a
// port that derives outstanding from amount minus paid alone, or that records a
// waiver without reducing outstanding, breaks the conservation identity on the
// waived state even when each cell is still a plausible integer.
func assertChargeStatesConserved(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "charge_states_conserved", Assertions: 2}
	req := v.Request.ChargeLifecycle
	if req == nil {
		r.Status = InvariantViolated
		r.Detail = "charge-lifecycle request is nil"
		return r
	}
	wantStates := len(req.Operations) + 1
	if len(got.ChargeStates) != wantStates {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("result has %d states for %d operations (want %d)",
			len(got.ChargeStates), len(req.Operations), wantStates)
		return r
	}
	if !isIntegerMinorString(req.AmountMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("request amount %q is not a non-negative integer minor amount", req.AmountMinor)
		return r
	}
	amount, err := parseMinorText(req.AmountMinor)
	if err != nil {
		r.Status = InvariantViolated
		r.Detail = err.Error()
		return r
	}
	r.Assertions = wantStates
	for i, st := range got.ChargeStates {
		for name, val := range map[string]string{
			"paid":        st.PaidMinor,
			"waived":      st.WaivedMinor,
			"outstanding": st.OutstandingMinor,
		} {
			if !isIntegerMinorString(val) {
				r.Status = InvariantViolated
				r.Detail = fmt.Sprintf("state %d %s %q is not a non-negative integer minor amount", i, name, val)
				return r
			}
		}
		paid, _ := parseMinorText(st.PaidMinor)
		waived, _ := parseMinorText(st.WaivedMinor)
		outstanding, _ := parseMinorText(st.OutstandingMinor)
		if paid+waived+outstanding != amount {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("state %d does not conserve the charge amount: paid %s + waived %s + outstanding %s != amount %s",
				i, st.PaidMinor, st.WaivedMinor, st.OutstandingMinor, req.AmountMinor)
			return r
		}
		if st.Paid && st.Waived {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("state %d is flagged both fully paid and fully waived", i)
			return r
		}
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("all %d states are non-negative integer minor units conserving the charge amount", len(got.ChargeStates))
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

// assertWriteOffFourBucketsSum: a write-off result's four portions are
// non-negative integer minor-unit amounts and they sum EXACTLY to the write-off
// amount. This is the property the seam exists to grade: a discharge is not a
// transcription of the oracle's write-off transaction unless every one of the
// four buckets is present and the four reconcile to the amount the processor
// posted. The assertion is on the implementation's RESULT, so a port that
// returns four self-consistent buckets summing to the wrong total is VIOLATED.
func assertWriteOffFourBucketsSum(got Expect) InvariantResult {
	r := InvariantResult{Name: "writeoff_four_buckets_sum_to_amount", Assertions: 5}
	if got.WriteOffAllocation == nil {
		r.Status = InvariantViolated
		r.Detail = "write_off_allocation is nil"
		return r
	}
	if !isIntegerMinorString(got.WriteOffTotalMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("write-off total %q is not a non-negative integer minor amount", got.WriteOffTotalMinor)
		return r
	}
	a := got.WriteOffAllocation
	for name, val := range map[string]string{
		"principal": a.Principal,
		"interest":  a.Interest,
		"fee":       a.Fee,
		"penalty":   a.Penalty,
	} {
		if !isIntegerMinorString(val) {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("write-off %s portion %q is not a non-negative integer minor amount", name, val)
			return r
		}
	}
	sum, ok := sumMinorStrings(a.Principal, a.Interest, a.Fee, a.Penalty)
	if !ok || sum != got.WriteOffTotalMinor {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("write-off portions sum to %s, not the write-off amount %s", sum, got.WriteOffTotalMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("write-off portions sum to the amount %s exactly across all four buckets", got.WriteOffTotalMinor)
	return r
}

// assertReversalAppendOnly: a loan-transaction reversal ADDS exactly one
// counter-leg per original leg and changes no original. The assertion is on the
// implementation's RESULT: the first half must be the request's originals
// unchanged and in place (same transaction id, account, side and amount, and
// NOT flagged reversed), and the second half must be their mirrors (same
// transaction id, account and amount, the OPPOSITE side, the reversed
// transaction's date, and not flagged). This is the append-only property: a
// port that marks the originals reversed, dates a counter at the business date,
// duplicates instead of reversing, or drops/adds a leg is VIOLATED here even
// when every side and amount cell happens to line up.
func assertReversalAppendOnly(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "reversal_appends_mirrors_only", Assertions: 3}
	if v.Request.Reversal == nil {
		r.Status = InvariantNotApplicable
		r.Detail = "the vector carries no reversal request"
		return r
	}
	in := v.Request.Reversal.JournalEntries
	if len(got.ReversalLegs) != 2*len(in) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("result has %d legs, want 2x%d: a reversal ADDS exactly one counter-leg per original leg",
			len(got.ReversalLegs), len(in))
		return r
	}
	for i, leg := range in {
		o := got.ReversalLegs[i]
		if o.TransactionID != leg.TransactionID || o.Account != leg.Account ||
			o.EntryType != leg.EntryType || o.AmountMinor != leg.AmountMinor {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("original leg %d was rewritten: %+v", i, o)
			return r
		}
		if o.Reversed {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("original leg %d is flagged reversed: the loan reversal changes no original", i)
			return r
		}
	}
	for i := range in {
		leg := in[i]
		c := got.ReversalLegs[len(in)+i]
		opp, ok := oppositeEntryType(leg.EntryType)
		if !ok || c.EntryType != opp || c.TransactionID != leg.TransactionID ||
			c.Account != leg.Account || c.AmountMinor != leg.AmountMinor {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("appended leg %d is not the mirror of original leg %d: %+v", len(in)+i, i, c)
			return r
		}
		if c.Reversed {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("appended counter-leg %d is flagged reversed", len(in)+i)
			return r
		}
		if c.TransactionDate != v.Request.Reversal.TransactionDate {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("counter-leg %d date %q is not the reversed transaction date %q",
				len(in)+i, c.TransactionDate, v.Request.Reversal.TransactionDate)
			return r
		}
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("the %d originals are unchanged and unflagged, each mirrored by one counter-leg dated %s",
		len(in), v.Request.Reversal.TransactionDate)
	return r
}

// assertWriteOffJournalBalanced: the write-off result carries non-negative
// integer minor-unit amounts, exactly ONE debit leg, and the debits sum to the
// credits. It is asserted on the implementation's RESULT, so a port that posts
// a debit per portion (four debits, still balanced) fails the one-debit
// assertion, and a port that debits only the principal fails the balance
// assertion. The loan-portfolio-debit and fee/penalty-swap defects still
// balance here; those are caught by the account cells in
// diffWriteOffJournalLegs, not by this money shape.
func assertWriteOffJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "write_off_journal_one_debit_balances", Assertions: 3}
	if len(got.WriteOffJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	debitLegs := 0
	for i, leg := range got.WriteOffJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if debitLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d debit leg(s): the write-off debits the total exactly ONCE", debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the single debit is %d: a write-off batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("one debit of %d equals the %d credit portion(s)", debits, len(got.WriteOffJournalLegs)-1)
	return r
}

// assertChargedOffWriteOffJournalBalanced: the charged-off write-off result
// carries non-negative integer minor-unit amounts, exactly ONE debit leg, and
// the debit equals the sum of the credits. It is asserted on the
// implementation's RESULT, so a port that posts one fund-source debit per
// portion (more debits, still balanced) fails the one-debit assertion, and a
// port whose fund-source debits do not sum to the credits fails the balance
// assertion. The fraud-account defect still balances here; that is caught by the
// account cells in diffChargedOffWriteOffJournalLegs, not by this money shape.
func assertChargedOffWriteOffJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "charged_off_write_off_journal_one_debit_balances", Assertions: 3}
	if len(got.ChargedOffWriteOffJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	debitLegs := 0
	for i, leg := range got.ChargedOffWriteOffJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if debitLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d debit leg(s): a charged-off write-off debits the total exactly ONCE to losses-written-off", debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the single debit is %d: a charged-off write-off batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("one debit of %d equals the %d credit portion(s)", debits, len(got.ChargedOffWriteOffJournalLegs)-1)
	return r
}

// assertRepaymentJournalBalanced: the ordinary repayment result carries
// non-negative integer minor-unit amounts, exactly ONE debit leg, and the debit
// equals the sum of the credits. It is asserted on the implementation's RESULT,
// so a port that posts one fund-source debit per credited portion (more debits,
// still balanced) fails the one-debit assertion, and a port whose sum does not
// balance fails the balance assertion. The account cells in
// diffRepaymentJournalLegs catch a wrong slot account, not this money shape.
func assertRepaymentJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "repayment_journal_one_debit_balances", Assertions: 3}
	if len(got.RepaymentJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	debitLegs := 0
	for i, leg := range got.RepaymentJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if debitLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d debit leg(s): an ordinary repayment debits the total exactly ONCE to the resolved fund source", debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the single debit is %d: a repayment batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("one debit of %d equals the %d credit portion(s)", debits, len(got.RepaymentJournalLegs)-1)
	return r
}

// assertGoodwillCreditJournalBalanced: a goodwill credit's result carries
// non-negative integer minor-unit amounts, at least one credit and at least one
// debit leg, and the debits sum to the credits. Unlike an ordinary repayment the
// debit side is the goodwill table's, one leg per distinct debit account, so the
// debit count is not fixed at one: a principal+interest goodwill credit posts
// two debits. It is asserted on the implementation's RESULT, so a port that
// drops or unbalances a leg fails here; the account and count cells that
// separate the goodwill accounts from a fund source are the leg differ's job.
func assertGoodwillCreditJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "goodwill_credit_journal_balances", Assertions: 3}
	legs := got.GoodwillCreditJournalLegs
	if len(legs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range legs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if creditLegs == 0 || debitLegs == 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d credit and %d debit leg(s): a goodwill credit needs both sides", creditLegs, debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the %d debit leg(s) sum to %d: a goodwill credit must balance", credits, debitLegs, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("%d credit leg(s) sum to %d, matched by %d goodwill debit leg(s)", creditLegs, credits, debitLegs)
	return r
}

// assertDisbursementJournalBalanced: a disbursement's result carries
// non-negative integer minor-unit amounts, EXACTLY ONE credit leg (the resolved
// fund source for the whole amount) and at least one debit leg, and the debits
// sum to the credit. Unlike a goodwill credit the debit side is the loan
// portfolio (plus overpayment when a portion is present), so the credit count is
// fixed at one: a port that posts one fund-source credit per debit fails here.
// It is asserted on the implementation's RESULT, so a port that takes
// the portfolio debit from the read-back principalPortion (0 on every
// observation) drops the debit and fails both the one-or-more-debit and the
// balance assertions. The account cells are the leg differ's job.
func assertDisbursementJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "disbursement_journal_balances", Assertions: 3}
	legs := got.DisbursementJournalLegs
	if len(legs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range legs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if creditLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d credit leg(s): a disbursement credits the resolved fund source exactly ONCE for the whole amount", creditLegs)
		return r
	}
	if debitLegs == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no debit leg: a disbursement debits the loan portfolio (and any overpayment) before the credit"
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credit is %d but the %d debit leg(s) sum to %d: a disbursement must balance", credits, debitLegs, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("one credit of %d is matched by %d disbursement debit leg(s)", credits, debitLegs)
	return r
}

// assertChargeAdjustmentJournalBalanced: a charge adjustment's result carries
// non-negative integer minor-unit amounts, at least one credit leg, EXACTLY ONE
// debit leg and the debit sums to the credits. Unlike a goodwill credit the
// debit side is a single income debit of the total (INCOME_FROM_FEES, or
// INCOME_FROM_PENALTIES when the adjusted charge is a penalty), so the count is
// fixed at one: a port that emits one debit per credit fails here. It is
// asserted on the implementation's RESULT, so a port that drops or unbalances a
// leg fails too; the account cells that separate the not-charged-off credits
// from the charge-off income table are the leg differ's job.
func assertChargeAdjustmentJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "charge_adjustment_journal_balances", Assertions: 4}
	legs := got.ChargeAdjustmentJournalLegs
	if len(legs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range legs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if creditLegs == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no credit leg: a charge adjustment credits each non-zero portion"
		return r
	}
	if debitLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d debit leg(s): a charge adjustment posts exactly ONE debit of the total", debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the %d credit leg(s) sum to %d but the single debit is %d: a charge adjustment must balance", creditLegs, credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("%d credit leg(s) sum to %d, matched by the one income debit", creditLegs, credits)
	return r
}

// assertChargedOffRepaymentJournalBalanced: a charged-off loan's repayment
// result carries non-negative integer minor-unit amounts, exactly ONE debit leg,
// and the debit equals the sum of the credits. It is asserted on the
// implementation's RESULT, so a port that posts one fund-source debit per
// credited portion (more debits, still balanced) fails the one-debit assertion,
// and a port whose sum does not balance fails the balance assertion. A port that
// posts the repayment like an ordinary one keeps this shape and is caught by the
// leg differ's account and count cells, not here.
func assertChargedOffRepaymentJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "chargedoff_repayment_journal_one_debit_balances", Assertions: 3}
	if len(got.ChargedOffRepaymentJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	debitLegs := 0
	for i, leg := range got.ChargedOffRepaymentJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if debitLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d debit leg(s): a charged-off loan's repayment debits the total exactly ONCE to the resolved fund source", debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the single debit is %d: a charged-off repayment batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("one debit of %d equals the %d credit portion(s)", debits, len(got.ChargedOffRepaymentJournalLegs)-1)
	return r
}

// assertChargedOffMerchantRefundJournalBalanced: a merchant-issued refund on a
// charged-off loan carries non-negative integer minor-unit amounts, exactly ONE
// debit leg, and the debit equals the sum of the credits. It is asserted on the
// implementation's RESULT, so a port that emits one fund-source debit per
// credited portion fails the one-debit assertion, and a port whose sum does not
// balance fails the balance assertion. A port that posts the refund like a
// charged-off repayment keeps this shape (it is still a balanced posting) and is
// caught by the leg differ's account and count cells, not here.
func assertChargedOffMerchantRefundJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "chargedoff_merchant_refund_journal_one_debit_balances", Assertions: 3}
	if len(got.ChargedOffMerchantRefundJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	debitLegs := 0
	for i, leg := range got.ChargedOffMerchantRefundJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if debitLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d debit leg(s): a charged-off merchant-issued refund debits the total exactly ONCE to the resolved fund source", debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the single debit is %d: a charged-off merchant refund batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("one debit of %d equals the %d credit portion(s)", debits, len(got.ChargedOffMerchantRefundJournalLegs)-1)
	return r
}

// assertAccrualJournalBalanced checks the harness-independent invariant of any
// accrual or accrual-adjustment posting: a non-empty leg list whose amounts are
// non-negative integer minor units, whose sides are DEBIT/CREDIT, and whose
// credit total equals its debit total. It does NOT assert a leg count or side
// order, so it cannot be satisfied by a wrong port that merely reorders or
// merges the groups; the graded leg cells do that. Every accrual group posts
// both a debit and a credit of the same amount, so a balanced batch is exactly
// one credit per debit across the group(s).
func assertAccrualJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "accrual_journal_balanced", Assertions: 3}
	if len(got.AccrualJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range got.AccrualJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the debits sum to %d: an accrual batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("%d debit leg(s) and %d credit leg(s) balance at %d", debitLegs, creditLegs, debits)
	return r
}

// assertChargeOffJournalBalanced: the charge-off result carries non-negative
// integer minor-unit amounts and the debits sum to the credits. Unlike the
// write-off, which has exactly one debit of the total, a charge-off posts one
// debit per distinct debit account (portions that MERGE to one account share a
// leg), so the debit-leg count is not fixed; the side-consistency and the
// credit/debit balance are the money shape the account cells in
// diffChargeOffJournalLegs do not already cover.
func assertChargeOffJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "charge_off_journal_balances", Assertions: 3}
	if len(got.ChargeOffJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range got.ChargeOffJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if creditLegs == 0 || debitLegs == 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d credit leg(s) and %d debit leg(s): a charge-off posts both sides", creditLegs, debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the debits sum to %d: a charge-off batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("%d debit(s) of %d equal the %d credit portion(s)", debitLegs, debits, creditLegs)
	return r
}

// assertInterestPaymentWaiverJournalBalanced: the interest-payment-waiver
// result carries non-negative integer minor-unit amounts, one or more merged
// CREDIT legs, EXACTLY ONE DEBIT leg (the total) and the debit equals the credit
// sum. The merged-account cells are checked by the leg diff; this is the money
// shape that a debit-per-portion or dropped-debit port cannot satisfy.
func assertInterestPaymentWaiverJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "interest_payment_waiver_journal_balances", Assertions: 4}
	if len(got.InterestPaymentWaiverJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range got.InterestPaymentWaiverJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if creditLegs == 0 || debitLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d credit leg(s) and %d debit leg(s): a waiver posts its merged credits and then one total debit", creditLegs, debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the debits sum to %d: a waiver batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("one debit of %d equals the %d credit portion(s)", debits, creditLegs)
	return r
}

// assertCapitalizedIncomeAmortizationJournalBalanced: the amortization result
// carries non-negative integer minor-unit amounts, EXACTLY ONE CREDIT leg (the
// interest and fee portions merge onto a single income account) and EXACTLY ONE
// DEBIT leg (the same total to DEFERRED_INCOME_LIABILITY), and the debit equals
// the credit. The account cells are checked by the leg diff; this is the money
// shape that a dropped-merge or dropped-debit port cannot satisfy.
func assertCapitalizedIncomeAmortizationJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "capitalized_income_amortization_journal_balances", Assertions: 4}
	if len(got.CapitalizedIncomeAmortizationJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range got.CapitalizedIncomeAmortizationJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if creditLegs != 1 || debitLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d credit leg(s) and %d debit leg(s): an amortization merges both portions into one income credit and then one total deferred-income-liability debit", creditLegs, debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credit sums to %d but the debit sums to %d: an amortization batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("one credit of %d equals the one debit", credits)
	return r
}

// assertChargebackJournalBalanced: the chargeback result carries non-negative
// integer minor-unit amounts and the debits sum to the credits. A chargeback
// posts ONE amount credit and up to two debits (overpayment, then principal), so
// the credit-leg count is one and the debit-leg count is not fixed; the
// side-consistency and the credit/debit balance are the money shape the account
// cells in diffChargebackJournalLegs do not already cover.
func assertChargebackJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "chargeback_journal_balances", Assertions: 3}
	if len(got.ChargebackJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range got.ChargebackJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if creditLegs == 0 || debitLegs == 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d credit leg(s) and %d debit leg(s): a chargeback posts both sides", creditLegs, debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the debits sum to %d: a chargeback batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("%d debit(s) of %d equal the %d credit(s)", debitLegs, debits, creditLegs)
	return r
}

// assertBuyDownFeeJournalBalanced: the buy-down-fee result carries non-negative
// integer minor-unit amounts and the debits sum to the credits. A buy-down fee
// posts exactly TWO legs, one debit and one credit of the same amount, so the
// both-sides and one-each counts are the fixed shape the account cells in
// diffBuyDownFeeJournalLegs do not already cover.
func assertBuyDownFeeJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "buy_down_fee_journal_balances", Assertions: 3}
	if len(got.BuyDownFeeJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range got.BuyDownFeeJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if creditLegs != 1 || debitLegs != 1 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d debit leg(s) and %d credit leg(s): a buy-down fee posts exactly one of each", debitLegs, creditLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credit of %d does not equal the debit of %d: a buy-down-fee batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("one debit of %d equals one credit of %d", debits, credits)
	return r
}

// assertCreditBalanceRefundJournalBalanced: the credit-balance-refund result
// carries non-negative integer minor-unit amounts and the debits sum to the
// credits. A refund posts ONE total credit and up to two debits (the principal
// portion first, then the overpayment portion), so the credit-leg count is one
// and the debit-leg count is not fixed; the side-consistency and the
// credit/debit balance are the money shape the account cells in
// diffCreditBalanceRefundJournalLegs do not already cover.
func assertCreditBalanceRefundJournalBalanced(got Expect) InvariantResult {
	r := InvariantResult{Name: "credit_balance_refund_journal_balances", Assertions: 3}
	if len(got.CreditBalanceRefundJournalLegs) == 0 {
		r.Status = InvariantViolated
		r.Detail = "the result carries no legs"
		return r
	}
	var credits, debits int64
	creditLegs, debitLegs := 0, 0
	for i, leg := range got.CreditBalanceRefundJournalLegs {
		n, err := strconv.ParseInt(leg.AmountMinor, 10, 64)
		if err != nil || n < 0 {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d amount %q is not a non-negative integer minor amount", i, leg.AmountMinor)
			return r
		}
		switch leg.EntryType {
		case "CREDIT":
			creditLegs++
			credits += n
		case "DEBIT":
			debitLegs++
			debits += n
		default:
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("leg %d side %q is not DEBIT or CREDIT", i, leg.EntryType)
			return r
		}
	}
	if creditLegs == 0 || debitLegs == 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the result carries %d credit leg(s) and %d debit leg(s): a credit balance refund posts both sides", creditLegs, debitLegs)
		return r
	}
	if credits != debits {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the credits sum to %d but the debits sum to %d: a credit balance refund batch must balance", credits, debits)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("%d debit(s) of %d equal the %d credit(s)", debitLegs, debits, creditLegs)
	return r
}
