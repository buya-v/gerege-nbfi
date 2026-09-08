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
		cellGraded, cellMoney, diffs = compareLoans(v.Expect, got)
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
// list seam grades total_elements and, per loan, id/external_id/status plus any
// OPTIONAL row-identity cell a vector pins (account_no, client_id). The list
// read serialises no money cell — the balance is read through the detail
// endpoint — so nothing on this seam is counted as money. A cell is graded only
// when the want side carries it. Returns the graded-cell and money-cell counts
// alongside the diffs.
func compareLoans(want Expect, got Expect) (int, int, []string) {
	graded, money := 0, 0
	var diffs []string

	if want.TotalElements != got.TotalElements {
		diffs = append(diffs, fmt.Sprintf("total_elements: want %d, got %d", want.TotalElements, got.TotalElements))
	}
	graded++
	if len(want.Loans) != len(got.Loans) {
		diffs = append(diffs, fmt.Sprintf("loans length: want %d, got %d", len(want.Loans), len(got.Loans)))
		return graded, money, diffs
	}
	for i := range want.Loans {
		wl, gl := want.Loans[i], got.Loans[i]
		// Mandatory row cells: id/external_id/status.
		for _, cell := range []struct {
			name string
			want string
			got  string
		}{
			{"id", wl.ID, gl.ID},
			{"external_id", wl.ExternalID, gl.ExternalID},
			{"status", wl.Status, gl.Status},
		} {
			graded++
			if cell.want != cell.got {
				diffs = append(diffs, fmt.Sprintf("loans[%d].%s: STRUCTURAL want %q, got %q",
					i, cell.name, cell.want, cell.got))
			}
		}
		// Optional row cells: a vector pins the cell it wants graded. The list
		// seam grades no money cell, so every optional cell is structural.
		for _, cell := range []struct {
			name string
			want string
			got  string
		}{
			{"account_no", wl.AccountNo, gl.AccountNo},
			{"client_id", wl.ClientID, gl.ClientID},
		} {
			if cell.want == "" {
				continue
			}
			graded++
			if cell.want == cell.got {
				continue
			}
			diffs = append(diffs, fmt.Sprintf("loans[%d].%s: STRUCTURAL want %q, got %q",
				i, cell.name, cell.want, cell.got))
		}
	}
	return graded, money, diffs
}

// compareDetail compares one working-capital loan's balance read-back. The
// detail seam grades the row id, its status code and the nine balance cells the
// port's stored-column + derive-don't-store contract reproduces, plus any
// OPTIONAL cell a vector pins (the stored status ordinal/active flag and the
// disbursement tranche the draw recorded). A cell is graded only when the want
// side carries it. Money cells are integer strings; a mismatch is reported as a
// MONEY diff.
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

	// Optional status cells: graded only when the vector pins them.
	cmpOpt := func(name string, wantVal, gotVal string) {
		if wantVal == "" {
			return
		}
		cmp(name, false, wantVal, gotVal)
	}
	cmpOpt("status_id", w.StatusOrdinal, g.StatusOrdinal)
	cmpOpt("status_active", w.StatusActive, g.StatusActive)

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

	// Optional disbursement-tranche block: when the vector pins a tranche, the
	// implementation must have recorded one (the seeded draw did) and the pinned
	// money cells must match.
	if w.Disbursement != nil {
		wd := w.Disbursement
		gd := g.Disbursement
		pinned := func(val string) bool { return val != "" }
		if gd == nil {
			for _, field := range []struct {
				name string
				val  string
			}{
				{"principal", wd.Principal},
				{"actual_amount", wd.ActualAmount},
			} {
				if !pinned(field.val) {
					continue
				}
				graded++
				money++
			}
			diffs = append(diffs, "detail.disbursement: MONEY want a recorded tranche, got none (the draw never wrote the tranche row)")
		} else {
			for _, cell := range []struct {
				name string
				want string
				got  string
			}{
				{"principal", wd.Principal, gd.Principal},
				{"actual_amount", wd.ActualAmount, gd.ActualAmount},
			} {
				if !pinned(cell.want) {
					continue
				}
				cmp("disbursement."+cell.name, true, cell.want, cell.got)
			}
		}
	}
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
