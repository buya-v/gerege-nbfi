package conformance

import (
	"context"
	"fmt"
	"path/filepath"

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
	Implementation     WorkingCapitalEvaluator
	ImplementationName string
	Pin                *Pin
	Registry           *CapabilityRegistry
	SelfTestMode       bool
}

// Summary is the aggregate outcome of a run. The type and its ExitCode live in
// nexus/internal/conformance; workingcapital re-uses them unchanged.
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

	var cellGraded, cellMoney int
	var diffs []string
	switch v.Oracle.Seam {
	case SeamWorkingCapitalLoansList:
		diffs = compareLoans(v.Expect, got)
		cellGraded = 1 + len(got.Loans)*3 // total_elements + (id, external_id, status) per loan
	case SeamWorkingCapitalLoansDetail:
		cellGraded, cellMoney, diffs = compareDetail(v.Expect, got)
	}
	r.GradedCells = cellGraded
	r.MoneyCells = cellMoney
	r.Diffs = diffs

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

// compareLoans compares the expected loan list against the evaluated one. The
// list seam grades total_elements and, per loan, id/external_id/status; it has
// no money cell (the list read does not serialise balance money).
func compareLoans(want Expect, got Expect) []string {
	var diffs []string
	if want.TotalElements != got.TotalElements {
		diffs = append(diffs, fmt.Sprintf("total_elements: want %d, got %d", want.TotalElements, got.TotalElements))
	}
	if len(want.Loans) != len(got.Loans) {
		diffs = append(diffs, fmt.Sprintf("loans length: want %d, got %d", len(want.Loans), len(got.Loans)))
		return diffs
	}
	for i := range want.Loans {
		if want.Loans[i].ID != got.Loans[i].ID {
			diffs = append(diffs, fmt.Sprintf("loans[%d].id: want %q, got %q", i, want.Loans[i].ID, got.Loans[i].ID))
		}
		if want.Loans[i].ExternalID != got.Loans[i].ExternalID {
			diffs = append(diffs, fmt.Sprintf("loans[%d].external_id: want %q, got %q", i, want.Loans[i].ExternalID, got.Loans[i].ExternalID))
		}
		if want.Loans[i].Status != got.Loans[i].Status {
			diffs = append(diffs, fmt.Sprintf("loans[%d].status: want %q, got %q", i, want.Loans[i].Status, got.Loans[i].Status))
		}
	}
	return diffs
}

// compareDetail compares one working-capital loan's balance read-back. The
// detail seam grades the row id, its status code, and the nine balance cells the
// port's stored-column + derive-don't-store contract reproduces. Money cells are
// integer strings; a mismatch is reported as a MONEY diff.
func compareDetail(want Expect, got Expect) (int, int, []string) {
	graded, money := 0, 0
	var diffs []string

	cmp := func(name string, isMoney bool, wantVal, gotVal string) {
		graded++
		if isMoney {
			money++
		}
		if wantVal == gotVal {
			return
		}
		kind := "STRUCTURAL"
		if isMoney {
			kind = "MONEY"
		}
		diffs = append(diffs, fmt.Sprintf("detail.%s: %s want %q, got %q", name, kind, wantVal, gotVal))
	}

	w := want.Detail
	if w == nil {
		diffs = append(diffs, "detail: want.Detail is nil (list seam reached the detail comparator)")
		return graded, money, diffs
	}
	g := got.Detail
	if g == nil {
		diffs = append(diffs, "detail: want a balance read-back, got nil")
		g = &DetailExpect{}
	}
	cmp("id", false, w.ID, g.ID)
	cmp("status", false, w.Status, g.Status)

	wb, gb := w.Balance, g.Balance
	cmp("balance.principal", true, wb.Principal, gb.Principal)
	cmp("balance.principal_paid", true, wb.PrincipalPaid, gb.PrincipalPaid)
	cmp("balance.total_disbursement", true, wb.TotalDisbursement, gb.TotalDisbursement)
	cmp("balance.total_discount_fee", true, wb.TotalDiscountFee, gb.TotalDiscountFee)
	cmp("balance.principal_outstanding", true, wb.PrincipalOutstanding, gb.PrincipalOutstanding)
	cmp("balance.total_expected_repayment", true, wb.TotalExpectedRepayment, gb.TotalExpectedRepayment)
	cmp("balance.total_repayment", true, wb.TotalRepayment, gb.TotalRepayment)
	cmp("balance.total_outstanding", true, wb.TotalOutstanding, gb.TotalOutstanding)
	cmp("balance.unrealized_income_from_discount_fee", true, wb.UnrealizedIncomeFromDiscountFee, gb.UnrealizedIncomeFromDiscountFee)
	return graded, money, diffs
}

// Run loads the store, runs the no-float census and grades every vector.
//
// IT NEVER RETURNS A PASS OVER ZERO VECTORS AND IT NEVER MAKES ONE UP.
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
			"NO STORE PIN: the pin (PIN-workingcapital.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}
	if opts.Registry == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO CAPABILITY REGISTRY: the registry (capabilities-workingcapital.json) must be loaded to grade a non-empty corpus.")
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
