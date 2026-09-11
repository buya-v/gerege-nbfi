package conformance

import (
	"context"
	"fmt"
	"path/filepath"
	"sort"

	shared "github.com/gerege/nexus/internal/conformance"
)

// Outcome is the verdict of grading one vector.
type Outcome string

const (
	OutcomePass         Outcome = "PASS"
	OutcomeFail         Outcome = "FAIL"
	OutcomeInadmissible Outcome = "INADMISSIBLE"
	OutcomeRefused      Outcome = "REFUSED"
	OutcomeError        Outcome = "HARNESS-ERROR"
)

// Options configures a conformance run.
type Options struct {
	RepoRoot           string
	StoreRoot          string
	ContextFilter      string
	Implementation     LoanEvaluator
	ImplementationName string
	Pin                *Pin
	Registry           *CapabilityRegistry
	SelfTestMode       bool
}

// Summary is the aggregate outcome of a run. The type and its ExitCode live in
// nexus/internal/conformance; loan re-uses them unchanged.
type Summary = shared.Summary

// vectorResult is one vector's grading outcome.
type vectorResult struct {
	CaseID              string
	Outcome             Outcome
	Problems            []string
	Reasons             []string
	GradedCells         int
	MoneyCells          int
	InvariantViolations int
	Diffs               []string
}

// cellSink records every compared cell and which of them are money cells, so
// the report can distinguish a money kill from a structural difference.
type cellSink struct {
	graded int
	money  int
	diffs  []string
}

func (s *cellSink) cmpMoney(name, want, got string) {
	s.graded++
	s.money++
	if want != got {
		s.diffs = append(s.diffs, fmt.Sprintf("%s: MONEY want %q, got %q", name, want, got))
	}
}

// cmpText compares a non-money structural cell (a status code or enum label).
func (s *cellSink) cmpText(name, want, got string) {
	s.graded++
	if want != got {
		s.diffs = append(s.diffs, fmt.Sprintf("%s: want %q, got %q", name, want, got))
	}
}

// cmpStoredValue compares a persisted enum ordinal, transcribed as an integer.
func (s *cellSink) cmpStoredValue(name string, want, got int32) {
	s.graded++
	if want != got {
		s.diffs = append(s.diffs, fmt.Sprintf("%s: want %d, got %d", name, want, got))
	}
}

// diffWriteOffAllocation compares the four write-off portions and the
// write-off amount. Each portion is a money cell; a port that drops a bucket,
// writes off only principal (or principal + interest), or swaps fee and penalty
// moves at least one of them while leaving the others intact. The total is
// graded too, so a port that returns four buckets that do not reconcile to the
// observed amount is a visible money difference.
func diffWriteOffAllocation(s *cellSink, want AllocationMoney, wantTotal string, got *AllocationMoney, gotTotal string) {
	var g AllocationMoney
	if got != nil {
		g = *got
	}
	s.cmpMoney("write_off.principal", want.Principal, g.Principal)
	s.cmpMoney("write_off.interest", want.Interest, g.Interest)
	s.cmpMoney("write_off.fee", want.Fee, g.Fee)
	s.cmpMoney("write_off.penalty", want.Penalty, g.Penalty)
	s.cmpMoney("write_off.total", wantTotal, gotTotal)
}

// diffAllocation compares the four-bucket allocation and the leftover.
func diffAllocation(s *cellSink, want AllocationMoney, wantLeftover string, got AllocationMoney, gotLeftover string) {
	s.cmpMoney("allocation.penalty", want.Penalty, got.Penalty)
	s.cmpMoney("allocation.fee", want.Fee, got.Fee)
	s.cmpMoney("allocation.interest", want.Interest, got.Interest)
	s.cmpMoney("allocation.principal", want.Principal, got.Principal)
	s.cmpMoney("leftover", wantLeftover, gotLeftover)
}

// diffTransactionBalance compares the per-row balance verdicts of the
// transaction-balance seam. Each row grades two cells: whether the read-back
// serialises an outstandingLoanBalance cell at all, and — when it does — the
// derived balance. A row the oracle leaves WITHOUT a balance cell (an accrual)
// grades only the serialisation cell: the ABSENCE is the observation, and an
// implementation that emits a zero balance where the oracle emits nothing
// fails on that cell alone.
func diffTransactionBalance(s *cellSink, wantRows, gotRows []TransactionBalanceRow) {
	s.cmpText("transaction_rows.count", fmt.Sprintf("%d", len(wantRows)), fmt.Sprintf("%d", len(gotRows)))
	for i := range wantRows {
		if i >= len(gotRows) {
			break
		}
		name := fmt.Sprintf("transactions[%d].serialized", i)
		s.cmpText(name, fmt.Sprintf("%t", wantRows[i].Serialized), fmt.Sprintf("%t", gotRows[i].Serialized))
		if wantRows[i].Serialized {
			s.cmpMoney(fmt.Sprintf("transactions[%d].balance", i), wantRows[i].BalanceMinor, gotRows[i].BalanceMinor)
		}
	}
}

// diffJournalEntryAccountSides compares WHICH account takes WHICH side in WHICH
// transaction — the property a swapped pair moves while leaving both totals
// equal. Both lists are sorted into a canonical (transaction_id, account,
// entry_type) order so the comparison grades the mapping, not the order the
// evaluator happened to emit it in. The counts are compared first, so a dropped
// or extra leg is a visible difference and not a silent truncation: the loop
// below stops at the shorter list, and only the count cell would otherwise
// carry that fact.
func diffJournalEntryAccountSides(s *cellSink, want, got []JournalEntryAccountSideCell) {
	s.cmpText("journal_entry_account_sides.count", fmt.Sprintf("%d", len(want)), fmt.Sprintf("%d", len(got)))
	w := canonicalJournalEntryAccountSides(want)
	g := canonicalJournalEntryAccountSides(got)
	for i := range w {
		if i >= len(g) {
			break
		}
		s.cmpText(fmt.Sprintf("journal_entry_account_sides[%d].transaction_id", i), w[i].TransactionID, g[i].TransactionID)
		s.cmpText(fmt.Sprintf("journal_entry_account_sides[%d].account", i), w[i].Account, g[i].Account)
		s.cmpText(fmt.Sprintf("journal_entry_account_sides[%d].entry_type", i), w[i].EntryType, g[i].EntryType)
	}
}

// diffReversalLegs compares the full after-read-back leg list of a
// loan-transaction reversal IN ORDER: the originals as they were, then the
// counter-legs. The count is compared first, so a port that drops or adds a leg
// is a visible difference rather than a silent truncation. Every leg grades six
// cells; the amount is the one money cell, and the side, transaction id,
// account, transaction date and reversed flag are structural. The side cells
// see a port that duplicates instead of reverses (both totals still balance);
// the date and reversed cells see a port that dates counters at the business
// date or flags the originals. The lists are compared positionally because the
// property is a fixed "originals, then mirrors" layout, not a set.
func diffReversalLegs(s *cellSink, want, got []ReversalLegCell) {
	s.cmpText("reversal_legs.count", fmt.Sprintf("%d", len(want)), fmt.Sprintf("%d", len(got)))
	n := len(want)
	if len(got) < n {
		n = len(got)
	}
	for i := 0; i < n; i++ {
		s.cmpText(fmt.Sprintf("reversal_legs[%d].transaction_id", i), want[i].TransactionID, got[i].TransactionID)
		s.cmpText(fmt.Sprintf("reversal_legs[%d].account", i), want[i].Account, got[i].Account)
		s.cmpText(fmt.Sprintf("reversal_legs[%d].entry_type", i), want[i].EntryType, got[i].EntryType)
		s.cmpMoney(fmt.Sprintf("reversal_legs[%d].amount", i), want[i].AmountMinor, got[i].AmountMinor)
		s.cmpText(fmt.Sprintf("reversal_legs[%d].transaction_date", i), want[i].TransactionDate, got[i].TransactionDate)
		s.cmpText(fmt.Sprintf("reversal_legs[%d].reversed", i), fmt.Sprintf("%t", want[i].Reversed), fmt.Sprintf("%t", got[i].Reversed))
	}
}

// diffWriteOffJournalLegs compares the ordered leg list of a loan write-off's
// journal entry. The count is compared first, so a port that posts a debit per
// portion (more legs) or drops a leg is a visible difference rather than a
// silent truncation. Every leg grades four cells: the amount is the one money
// cell, and the transaction id, account and side are structural. The account
// cells see a port that debits loan portfolio instead of losses-written-off or
// swaps the fee and penalty receivables; the side cells see one debit per
// portion; the count cell sees a dropped portion. The list is positional
// because the property is a fixed "credits in slot order, then one debit"
// layout, not a set.
func diffWriteOffJournalLegs(s *cellSink, want, got []JournalEntryLeg) {
	diffJournalLegs(s, "write_off_journal_legs", want, got)
}

// diffChargeOffJournalLegs compares the ordered leg list of a loan charge-off's
// journal entry through the same per-leg differ the write-off-journal seam uses.
// Every leg grades four cells: the amount is the one money cell, and the
// transaction id, account and side are structural. The account cells see a port
// that ignores the fraud flag (the principal debit on the ordinary charge-off
// expense account instead of the fraud expense account); the count and side
// cells see a debit-per-portion port. The list is positional because the
// property is a fixed "credits in slot order, then debits in slot order"
// layout, not a set.
func diffChargeOffJournalLegs(s *cellSink, want, got []JournalEntryLeg) {
	diffJournalLegs(s, "charge_off_journal_legs", want, got)
}

// diffChargedOffWriteOffJournalLegs compares the ordered leg list of a
// charged-off loan write-off's journal entry through the same per-leg differ the
// write-off-journal seam uses. Every leg grades four cells: the amount is the
// one money cell, and the transaction id, account and side are structural. The
// account cells see a port that debits the per-portion fund-source accounts
// instead of the single LOSSES_WRITTEN_OFF account, or that credits the
// ordinary charge-off expense account instead of the fraud expense account; the
// count and side cells see a debit-per-portion port. The list is positional
// because the property is a fixed "credits in slot order, then one debit"
// layout, not a set.
func diffChargedOffWriteOffJournalLegs(s *cellSink, want, got []JournalEntryLeg) {
	diffJournalLegs(s, "charged_off_write_off_journal_legs", want, got)
}

// diffRepaymentJournalLegs compares the ordered leg list of an ordinary loan
// repayment's journal entry through the same per-leg differ the write-off-journal
// seam uses. Every leg grades four cells: the amount is the one money cell, and
// the transaction id, account and side are structural. The account cells see a
// port that credits the wrong receivable slot or debits a fund source other than
// the resolved one; the count and side cells see a debit-per-portion port. The
// list is positional because the property is a fixed "credits in slot order,
// then one debit" layout, not a set.
func diffRepaymentJournalLegs(s *cellSink, want, got []JournalEntryLeg) {
	diffJournalLegs(s, "repayment_journal_legs", want, got)
}

// diffChargebackJournalLegs compares the ordered leg list of a loan chargeback's
// journal entry through the same per-leg differ the write-off-journal seam uses.
// Every leg grades four cells: the amount is the one money cell, and the
// transaction id, account and side are structural. The account cells see a port
// that debits the overpayment portion to the loan-portfolio account; the count
// and order cells see a port that drops or reorders a leg. The list is
// positional because the property is a fixed "amount credit, then overpayment
// debit, then principal debit" layout, not a set.
func diffChargebackJournalLegs(s *cellSink, want, got []JournalEntryLeg) {
	diffJournalLegs(s, "chargeback_journal_legs", want, got)
}

// diffJournalLegs is the shared ordered-leg differ: the count is compared
// first, so a port that posts a leg per portion (more legs) or drops a leg is a
// visible difference rather than a silent truncation. Each label is prefixed
// with the seam's expect field name.
func diffJournalLegs(s *cellSink, prefix string, want, got []JournalEntryLeg) {
	s.cmpText(prefix+".count", fmt.Sprintf("%d", len(want)), fmt.Sprintf("%d", len(got)))
	n := len(want)
	if len(got) < n {
		n = len(got)
	}
	for i := 0; i < n; i++ {
		s.cmpText(fmt.Sprintf("%s[%d].transaction_id", prefix, i), want[i].TransactionID, got[i].TransactionID)
		s.cmpText(fmt.Sprintf("%s[%d].account", prefix, i), want[i].Account, got[i].Account)
		s.cmpText(fmt.Sprintf("%s[%d].entry_type", prefix, i), want[i].EntryType, got[i].EntryType)
		s.cmpMoney(fmt.Sprintf("%s[%d].amount", prefix, i), want[i].AmountMinor, got[i].AmountMinor)
	}
}

// diffChargeStates compares the ordered state sequence of the charge-lifecycle
// seam: the created state at index 0, then the state after each operation. Each
// state grades five cells — amountPaid, amountWaived and amountOutstanding as
// money cells, plus the paid and waived flags as structural cells. The count is
// compared first, so a dropped or extra operation is a visible difference
// rather than a silent truncation. A port that flips paid on a partial payment,
// leaves outstanding un-reduced after a waiver, routes a waiver into paid, or
// derives outstanding from amount minus paid alone moves at least one cell.
func diffChargeStates(s *cellSink, want, got []ChargeLifecycleState) {
	s.cmpText("charge_states.count", fmt.Sprintf("%d", len(want)), fmt.Sprintf("%d", len(got)))
	n := len(want)
	if len(got) < n {
		n = len(got)
	}
	for i := 0; i < n; i++ {
		s.cmpMoney(fmt.Sprintf("charge_states[%d].paid_minor", i), want[i].PaidMinor, got[i].PaidMinor)
		s.cmpMoney(fmt.Sprintf("charge_states[%d].waived_minor", i), want[i].WaivedMinor, got[i].WaivedMinor)
		s.cmpMoney(fmt.Sprintf("charge_states[%d].outstanding_minor", i), want[i].OutstandingMinor, got[i].OutstandingMinor)
		s.cmpText(fmt.Sprintf("charge_states[%d].paid", i), fmt.Sprintf("%t", want[i].Paid), fmt.Sprintf("%t", got[i].Paid))
		s.cmpText(fmt.Sprintf("charge_states[%d].waived", i), fmt.Sprintf("%t", want[i].Waived), fmt.Sprintf("%t", got[i].Waived))
	}
}

// diffStatusTransition compares the status the lifecycle state machine
// returned: the decoded read-back code and the stored value it round-trips to.
// Both are structural cells — the code is an i18n label, the stored value the
// persisted m_loan.loan_status_id — so a wrong closed-state distinction
// (written off vs obligations met) or an iota-collapsed ordinal moves a cell.
// No balance value is compared because none is returned: the machine answers
// with a status.
func diffStatusTransition(s *cellSink, want, got Expect) {
	s.cmpText("next_status_code", want.NextStatusCode, got.NextStatusCode)
	s.cmpStoredValue("next_status_stored_value", want.NextStatusStoredValue, got.NextStatusStoredValue)
}

// canonicalJournalEntryAccountSides returns a copy of in sorted by
// (transaction_id, account, entry_type) so the side comparison is
// order-insensitive.
func canonicalJournalEntryAccountSides(in []JournalEntryAccountSideCell) []JournalEntryAccountSideCell {
	out := append([]JournalEntryAccountSideCell(nil), in...)
	sort.Slice(out, func(i, j int) bool {
		if out[i].TransactionID != out[j].TransactionID {
			return out[i].TransactionID < out[j].TransactionID
		}
		if out[i].Account != out[j].Account {
			return out[i].Account < out[j].Account
		}
		return out[i].EntryType < out[j].EntryType
	})
	return out
}

// gradeOne admits, checks capabilities, evaluates and compares one vector.
func gradeOne(v *Vector, opts Options) vectorResult {
	r := vectorResult{CaseID: v.CaseID}

	if problems := Admit(v, opts); len(problems) > 0 {
		r.Outcome = OutcomeInadmissible
		r.Problems = problems
		return r
	}

	if opts.Registry != nil {
		if verdict := opts.Registry.Assess(v.Oracle.Seam, v.CapabilitiesRequired); !verdict.Gradeable {
			r.Outcome = OutcomeRefused
			r.Reasons = verdict.Detail
			return r
		}
	}

	got, err := opts.Implementation.Evaluate(v.Request)
	if err != nil {
		r.Outcome = OutcomeError
		r.Reasons = []string{err.Error()}
		return r
	}

	var s cellSink
	switch v.Oracle.Seam {
	case SeamLoanRepaymentAllocation:
		diffAllocation(&s, *v.Expect.Allocation, v.Expect.LeftoverMinor, *got.Allocation, got.LeftoverMinor)
	case SeamLoanScheduleInterest:
		s.cmpMoney("interest", v.Expect.InterestMinor, got.InterestMinor)
	case SeamLoanDisbursement:
		s.cmpMoney("net_disbursal", v.Expect.NetDisbursalMinor, got.NetDisbursalMinor)
	case SeamLoanSummaryOutstanding:
		s.cmpMoney("summary_total", v.Expect.SummaryTotalMinor, got.SummaryTotalMinor)
	case SeamLoanStatus:
		s.cmpText("status_code", v.Expect.StatusCode, got.StatusCode)
		s.cmpStoredValue("status_stored_value", v.Expect.StatusStoredValue, got.StatusStoredValue)
	case SeamLoanTransactionBalance:
		diffTransactionBalance(&s, v.Expect.TransactionRows, got.TransactionRows)
	case SeamLoanJournalEntryBatchBalance:
		s.cmpMoney("journal_entry_debits", v.Expect.JournalEntryDebitsMinor, got.JournalEntryDebitsMinor)
		s.cmpMoney("journal_entry_credits", v.Expect.JournalEntryCreditsMinor, got.JournalEntryCreditsMinor)
		diffJournalEntryAccountSides(&s, v.Expect.JournalEntryAccountSides, got.JournalEntryAccountSides)
	case SeamLoanScheduleAmortization:
		s.cmpMoney("principal_sum", v.Expect.PrincipalSumMinor, got.PrincipalSumMinor)
		s.cmpMoney("final_principal_balance", v.Expect.FinalPrincipalBalanceMinor, got.FinalPrincipalBalanceMinor)
	case SeamLoanDelinquentDays:
		// Day counts are integer calendar-day differences, not money: they are
		// compared as text so they never enter the money-cell count.
		s.cmpText("overdue_days", v.Expect.OverdueDays, got.OverdueDays)
		s.cmpText("delinquent_days", v.Expect.DelinquentDays, got.DelinquentDays)
	case SeamLoanWriteOffFourBucket:
		diffWriteOffAllocation(&s, *v.Expect.WriteOffAllocation, v.Expect.WriteOffTotalMinor, got.WriteOffAllocation, got.WriteOffTotalMinor)
	case SeamLoanTransactionReversal:
		diffReversalLegs(&s, v.Expect.ReversalLegs, got.ReversalLegs)
	case SeamLoanWriteOffJournalEntries:
		diffWriteOffJournalLegs(&s, v.Expect.WriteOffJournalLegs, got.WriteOffJournalLegs)
	case SeamLoanChargeOffJournalEntries:
		diffChargeOffJournalLegs(&s, v.Expect.ChargeOffJournalLegs, got.ChargeOffJournalLegs)
	case SeamLoanChargedOffWriteOffJournalEntries:
		diffChargedOffWriteOffJournalLegs(&s, v.Expect.ChargedOffWriteOffJournalLegs, got.ChargedOffWriteOffJournalLegs)
	case SeamLoanRepaymentJournalEntries:
		diffRepaymentJournalLegs(&s, v.Expect.RepaymentJournalLegs, got.RepaymentJournalLegs)
	case SeamLoanChargedOffRepaymentJournalEntries:
		// Reuse the repayment-journal per-leg differ: the property is the same
		// fixed "credits in slot order, then one debit" layout, and the account
		// and count cells are what separate the merged recovery credit from a
		// per-slot ordinary posting.
		diffRepaymentJournalLegs(&s, v.Expect.ChargedOffRepaymentJournalLegs, got.ChargedOffRepaymentJournalLegs)
	case SeamLoanAccrualJournalEntries:
		// Reuse the repayment-journal per-leg differ: the property is the same
		// fixed ordered leg list, and the interest pair's side (swapped by an
		// adjustment) is what separates an adjustment from an accrual.
		diffRepaymentJournalLegs(&s, v.Expect.AccrualJournalLegs, got.AccrualJournalLegs)
	case SeamLoanChargebackJournalEntries:
		diffChargebackJournalLegs(&s, v.Expect.ChargebackJournalLegs, got.ChargebackJournalLegs)
	case SeamLoanChargeLifecycle:
		diffChargeStates(&s, v.Expect.ChargeStates, got.ChargeStates)
	case SeamLoanStatusTransition:
		diffStatusTransition(&s, v.Expect, got)
	}
	r.GradedCells = s.graded
	r.MoneyCells = s.money
	r.Diffs = s.diffs

	invs := AssertInvariants(v, got)
	for _, iv := range invs {
		if iv.Status == InvariantViolated {
			r.InvariantViolations++
			r.Diffs = append(r.Diffs, fmt.Sprintf("invariant %s: %s", iv.Name, iv.Detail))
		}
	}

	if len(r.Diffs) > 0 || r.InvariantViolations > 0 {
		r.Outcome = OutcomeFail
	} else {
		r.Outcome = OutcomePass
	}
	return r
}

// Run loads the store, runs the no-float census and grades every vector.
//
// IT NEVER RETURNS A PASS OVER ZERO VECTORS AND IT NEVER MAKES ONE UP. An empty
// store is recorded as a FatalReason ("ZERO VECTORS FOUND"), which forces exit
// code 2; a harness that reported PASS over an empty corpus would be the exact
// fail-open this program has been bitten by.
func Run(ctx context.Context, opts Options) (*Summary, error) {
	_ = ctx
	s := &Summary{SelfTestMode: opts.SelfTestMode, ReportMoneyCells: true}

	census, err := ScanGoTreeForFloatingPoint(filepath.Join(opts.RepoRoot, GuardedGoTreeRel))
	if err != nil {
		s.FatalReasons = append(s.FatalReasons, fmt.Sprintf("no-float census: %v", err))
	} else {
		s.NoFloatCensus = census
		for _, viol := range census.Violations() {
			s.FatalReasons = append(s.FatalReasons, viol)
		}
	}

	vectors, loadErrs, err := LoadStore(opts.StoreRoot, opts.ContextFilter)
	s.LoadErrors = loadErrs
	if err != nil {
		s.FatalReasons = append(s.FatalReasons, err.Error())
		return s, nil
	}
	s.VectorsLoaded = len(vectors)

	if len(vectors) == 0 {
		where := opts.StoreRoot
		if opts.ContextFilter != "" {
			where = filepath.Join(opts.StoreRoot, opts.ContextFilter)
		}
		s.FatalReasons = append(s.FatalReasons, fmt.Sprintf(
			"ZERO VECTORS FOUND under %s: an empty vector set is exit 2. A harness that reported PASS over "+
				"zero vectors would be the single worst outcome available to it.", where))
		return s, nil
	}

	if opts.Implementation == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO IMPLEMENTATION REGISTERED: there is nothing to grade. This is exit 2, not a pass over zero work.")
		return s, nil
	}
	if opts.Pin == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO STORE PIN: the pin (PIN-loan.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}
	if opts.Registry == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO CAPABILITY REGISTRY: the registry (capabilities-loan.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}

	for _, v := range vectors {
		r := gradeOne(v, opts)
		s.GradedCells += r.GradedCells
		s.MoneyCells += r.MoneyCells
		s.InvariantViolations += r.InvariantViolations
		switch r.Outcome {
		case OutcomePass:
			s.ParityPass++
		case OutcomeFail:
			s.ParityFail++
		case OutcomeRefused:
			s.Refused++
		case OutcomeInadmissible:
			s.Inadmissible++
		case OutcomeError:
			s.Errored++
		}
	}
	return s, nil
}

// sortedStrings returns a sorted copy (helpers keep report ordering deterministic).
func sortedStrings(in []string) []string {
	out := append([]string(nil), in...)
	sort.Strings(out)
	return out
}
