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
	Implementation     InvestorEvaluator
	ImplementationName string
	Pin                *Pin
	Registry           *CapabilityRegistry
	SelfTestMode       bool
}

// Summary is the aggregate outcome of a run. The type and its ExitCode live in
// nexus/internal/conformance; investor re-uses them unchanged.
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

	diffs := compareTransferExpect(v.Expect, got)
	r.GradedCells = 9 // transfer_id, owner_external_id, loan_external_id, transfer_external_id, purchase_price_ratio, status, settlement_date, effective_from, effective_to
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

// compareTransferExpect compares an expected transfer row against the evaluated
// one. Every field is a verbatim transcription; none is money in integer minor
// units, so the cells are plain string/integer comparisons.
func compareTransferExpect(want Expect, got Expect) []string {
	var diffs []string
	if want.TransferID != got.TransferID {
		diffs = append(diffs, fmt.Sprintf("transfer_id: want %d, got %d", want.TransferID, got.TransferID))
	}
	if want.OwnerExternalID != got.OwnerExternalID {
		diffs = append(diffs, fmt.Sprintf("owner_external_id: want %q, got %q", want.OwnerExternalID, got.OwnerExternalID))
	}
	if want.LoanExternalID != got.LoanExternalID {
		diffs = append(diffs, fmt.Sprintf("loan_external_id: want %q, got %q", want.LoanExternalID, got.LoanExternalID))
	}
	if want.TransferExternalID != got.TransferExternalID {
		diffs = append(diffs, fmt.Sprintf("transfer_external_id: want %q, got %q", want.TransferExternalID, got.TransferExternalID))
	}
	if want.PurchasePriceRatio != got.PurchasePriceRatio {
		diffs = append(diffs, fmt.Sprintf("purchase_price_ratio: want %q, got %q", want.PurchasePriceRatio, got.PurchasePriceRatio))
	}
	if want.Status != got.Status {
		diffs = append(diffs, fmt.Sprintf("status: want %q, got %q", want.Status, got.Status))
	}
	if want.SettlementDate != got.SettlementDate {
		diffs = append(diffs, fmt.Sprintf("settlement_date: want %q, got %q", want.SettlementDate, got.SettlementDate))
	}
	if want.EffectiveFrom != got.EffectiveFrom {
		diffs = append(diffs, fmt.Sprintf("effective_from: want %q, got %q", want.EffectiveFrom, got.EffectiveFrom))
	}
	if want.EffectiveTo != got.EffectiveTo {
		diffs = append(diffs, fmt.Sprintf("effective_to: want %q, got %q", want.EffectiveTo, got.EffectiveTo))
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
			"NO STORE PIN: the pin (PIN-investor.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}
	if opts.Registry == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO CAPABILITY REGISTRY: the registry (capabilities-investor.json) must be loaded to grade a non-empty corpus.")
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
