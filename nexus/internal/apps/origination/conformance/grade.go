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
	Implementation     OriginationEvaluator
	ImplementationName string
	Pin                *Pin
	Registry           *CapabilityRegistry
	SelfTestMode       bool
}

// Summary is the aggregate outcome of a run. The type and its ExitCode live in
// nexus/internal/conformance; origination re-uses them unchanged.
type Summary = shared.Summary

// VerdictLine renders the one-word verdict for the summary.
func VerdictLine(s *Summary) string { return shared.VerdictLine(s) }

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

// compareStoredExpect compares the oracle's expected stored string with what the
// implementation produced. stored is the single string cell the seam grades.
func compareStoredExpect(want, got Expect) []string {
	var diffs []string
	if want.Stored != got.Stored {
		diffs = append(diffs, fmt.Sprintf("stored: want %q, got %q", want.Stored, got.Stored))
	}
	return diffs
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

	r.Diffs = compareStoredExpect(v.Expect, got)
	r.GradedCells = 1 // stored

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
			"NO STORE PIN: the pin (PIN-origination.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}
	if opts.Registry == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO CAPABILITY REGISTRY: the registry (capabilities-origination.json) must be loaded to grade a non-empty corpus.")
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
