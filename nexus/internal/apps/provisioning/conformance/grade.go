package conformance

import (
	"context"
	"fmt"
	"path/filepath"
	"sort"
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
	Implementation     ProvisioningEvaluator
	ImplementationName string
	Pin                *Pin
	Registry           *CapabilityRegistry
	SelfTestMode       bool
}

// Summary is the aggregate outcome of a run. Every count is explicit so that a
// zero is visible rather than assumed.
type Summary struct {
	SelfTestMode        bool
	ParityPass          int
	ParityFail          int
	Refused             int
	Inadmissible        int
	Errored             int
	InvariantViolations int
	GradedCells         int
	VectorsLoaded       int
	FatalReasons        []string
	LoadErrors          []LoadError
	NoFloatCensus       FloatingPointCensus
}

// ExitCode maps the run to a process exit code.
//
// 0  every graded vector passed and at least one PARITY vector was graded
// 1  a mismatch or an invariant violation (an actionable finding)
// 2  the harness or corpus is unusable — including ZERO vectors graded
func (s *Summary) ExitCode() int {
	if s.ParityFail > 0 || s.InvariantViolations > 0 {
		return 1
	}
	if len(s.FatalReasons) > 0 || len(s.LoadErrors) > 0 ||
		s.Refused > 0 || s.Inadmissible > 0 || s.Errored > 0 {
		return 2
	}
	if !s.SelfTestMode && s.ParityPass == 0 {
		return 2
	}
	return 0
}

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
	case SeamProvisioningEntryReserve:
		diffs = compareReserveExpect(v.Expect, got)
		r.GradedCells = 3 // reserved_amount_minor, category_id, overdue_in_days
	default:
		diffs = compareExpect(v.Expect, got)
		r.GradedCells = 3 // id, name, description
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

// compareExpect compares an expected category against an evaluated one, returning
// the cells that differ, as printable strings.
func compareExpect(want Expect, got Expect) []string {
	var diffs []string
	if want.ID != got.ID {
		diffs = append(diffs, fmt.Sprintf("id: want %d, got %d", want.ID, got.ID))
	}
	if want.Name != got.Name {
		diffs = append(diffs, fmt.Sprintf("name: want %q, got %q", want.Name, got.Name))
	}
	if want.Description != got.Description {
		diffs = append(diffs, fmt.Sprintf("description: want %q, got %q", want.Description, got.Description))
	}
	return diffs
}

// compareReserveExpect compares an expected aggregated reserve entry against the
// evaluated one. reserved_amount_minor is the reserve-amount money cell;
// category_id and overdue_in_days are the identity cells that pin which band the
// amount belongs to.
func compareReserveExpect(want Expect, got Expect) []string {
	var diffs []string
	if want.ReservedAmountMinor != got.ReservedAmountMinor {
		diffs = append(diffs, fmt.Sprintf("reserved_amount_minor: want %q, got %q", want.ReservedAmountMinor, got.ReservedAmountMinor))
	}
	if want.CategoryID != got.CategoryID {
		diffs = append(diffs, fmt.Sprintf("category_id: want %d, got %d", want.CategoryID, got.CategoryID))
	}
	if want.OverdueInDays != got.OverdueInDays {
		diffs = append(diffs, fmt.Sprintf("overdue_in_days: want %d, got %d", want.OverdueInDays, got.OverdueInDays))
	}
	return diffs
}

// Run loads the store, runs the no-float census and grades every vector.
//
// IT NEVER RETURNS A PASS OVER ZERO VECTORS AND IT NEVER MAKES ONE UP. An empty
// store is recorded as a FatalReason ("ZERO VECTORS FOUND"), which forces exit
// code 2; a harness that reported PASS over an empty corpus would be the exact
// fail-open this program has been bitten by.
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
			"NO STORE PIN: the pin (PIN-provisioning.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}
	if opts.Registry == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO CAPABILITY REGISTRY: the registry (capabilities-provisioning.json) must be loaded to grade a non-empty corpus.")
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
