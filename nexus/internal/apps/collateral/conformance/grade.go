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

// Cell is one compared field of one vector.
type Cell struct {
	VectorCaseID string
	Field        string
	Got          string
	Want         string
}

// Options configures a conformance run.
type Options struct {
	RepoRoot           string
	StoreRoot          string
	ContextFilter      string
	Implementation     CollateralEvaluator
	ImplementationName string
	Pin                *Pin
	Registry           *CapabilityRegistry
	SelfTestMode       bool
}

// Summary is the aggregate outcome of a run. The type and its ExitCode live in
// nexus/internal/conformance; collateral re-uses them unchanged.
type Summary = shared.Summary

// vectorResult is one vector's grading outcome.
type vectorResult struct {
	CaseID              string
	Outcome             Outcome
	Problems            []string
	Reasons             []string
	GradedCells         int
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

	var diffs []string
	switch v.Oracle.Seam {
	case SeamCollateralLinkRead:
		diffs = compareLinkExpect(v.Expect, got)
		r.GradedCells = 2 // id, type_id
	case SeamClientCollateralRead:
		diffs = compareClientExpect(v.Expect, got)
		r.GradedCells = 1 // page_presence (empty client-collateral page)
	case SeamClientCollateralValuationRead:
		diffs = compareValuationExpect(v.Expect, got)
		r.GradedCells = 4 // id, quantity, total, total_collateral
	default:
		diffs = compareProductExpect(v.Expect, got)
		r.GradedCells = 7 // id, name, quality, unit_type, currency, base_price, pct_to_base
	}
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

// compareProductExpect compares an expected product row against the evaluated
// one. base_price and pct_to_base are scale-5 integer strings.
func compareProductExpect(want Expect, got Expect) []string {
	var diffs []string
	if want.ID != got.ID {
		diffs = append(diffs, fmt.Sprintf("id: want %d, got %d", want.ID, got.ID))
	}
	if want.Name != got.Name {
		diffs = append(diffs, fmt.Sprintf("name: want %q, got %q", want.Name, got.Name))
	}
	if want.Quality != got.Quality {
		diffs = append(diffs, fmt.Sprintf("quality: want %q, got %q", want.Quality, got.Quality))
	}
	if want.UnitType != got.UnitType {
		diffs = append(diffs, fmt.Sprintf("unit_type: want %q, got %q", want.UnitType, got.UnitType))
	}
	if want.Currency != got.Currency {
		diffs = append(diffs, fmt.Sprintf("currency: want %q, got %q", want.Currency, got.Currency))
	}
	if want.BasePrice != got.BasePrice {
		diffs = append(diffs, fmt.Sprintf("base_price: want %q, got %q", want.BasePrice, got.BasePrice))
	}
	if want.PctToBase != got.PctToBase {
		diffs = append(diffs, fmt.Sprintf("pct_to_base: want %q, got %q", want.PctToBase, got.PctToBase))
	}
	return diffs
}

// compareClientExpect compares the expected client-collateral read-back against
// the evaluated one. The oracle returned an EMPTY content page for client 5
// (client-collateral-readback-raw.json: content []), while the seed's own write
// path stored holding id 2 under m_client_collateral_management — the write and
// read paths target different models in this build. Page presence is the
// discriminating cell: a conformant port reproduces the read-back the oracle
// exposed, so a read that answers the client from the table the write populated
// fabricates a holding row the oracle never returned.
func compareClientExpect(want Expect, got Expect) []string {
	if want.Empty != got.Empty {
		if want.Empty {
			return []string{fmt.Sprintf(
				"page: expected an EMPTY client-collateral read (the oracle returned content [] for this client); implementation returned a holding row (holding id %d)", got.ID)}
		}
		return []string{"page: expected a client-collateral holding row; implementation returned an EMPTY page"}
	}
	return nil
}

// compareValuationExpect compares an expected single-row client-collateral
// read-back against the evaluated one. quantity, total and total_collateral are
// scale-5 integer strings transcribed from the oracle's decimal displays in
// client-collateral-single-raw.json. The discriminating cells are the two
// COMPUTED valuation fields: the oracle derives total = base_price * quantity
// and total_collateral = total * pct_to_base/100 on the read path
// (ClientCollateralManagementReadServiceImpl.java), so an implementation whose
// valuation arithmetic differs from the oracle's fails these cells even when the
// stored quantity matches.
func compareValuationExpect(want Expect, got Expect) []string {
	var diffs []string
	if want.ID != got.ID {
		diffs = append(diffs, fmt.Sprintf("id: want %d, got %d", want.ID, got.ID))
	}
	if want.Quantity != got.Quantity {
		diffs = append(diffs, fmt.Sprintf("quantity: want %q, got %q", want.Quantity, got.Quantity))
	}
	if want.Total != got.Total {
		diffs = append(diffs, fmt.Sprintf("total: want %q, got %q", want.Total, got.Total))
	}
	if want.TotalCollateral != got.TotalCollateral {
		diffs = append(diffs, fmt.Sprintf("total_collateral: want %q, got %q", want.TotalCollateral, got.TotalCollateral))
	}
	return diffs
}

// compareLinkExpect compares an expected loan-collateral row against the
// evaluated one: id and type_cv_id (the LoanCollateral code value). The value,
// description and currency members of the capture are API joins/absences the
// port's LoanCollateral model does not carry, so they are not graded.
func compareLinkExpect(want Expect, got Expect) []string {
	var diffs []string
	if want.ID != got.ID {
		diffs = append(diffs, fmt.Sprintf("id: want %d, got %d", want.ID, got.ID))
	}
	if want.TypeID != got.TypeID {
		diffs = append(diffs, fmt.Sprintf("type_id: want %d, got %d", want.TypeID, got.TypeID))
	}
	return diffs
}

// Run loads the store, runs the no-float census and grades every vector.
//
// IT NEVER RETURNS A PASS OVER ZERO VECTORS AND IT NEVER MAKES ONE UP.
func Run(ctx context.Context, opts Options) (*Summary, error) {
	_ = ctx
	s := &Summary{SelfTestMode: opts.SelfTestMode}

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
			"NO STORE PIN: the pin (PIN-collateral.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}
	if opts.Registry == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO CAPABILITY REGISTRY: the registry (capabilities-collateral.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}

	for _, v := range vectors {
		r := gradeOne(v, opts)
		s.GradedCells += r.GradedCells
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
