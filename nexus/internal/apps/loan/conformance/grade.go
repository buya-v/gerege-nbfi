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
