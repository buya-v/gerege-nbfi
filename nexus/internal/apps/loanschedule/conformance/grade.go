package conformance

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// Outcome is one vector's verdict. Five values, not two, because the two
// interesting outcomes of this program are neither PASS nor FAIL: "the corpus
// cannot grade this" and "the corpus should never have contained this".
type Outcome string

const (
	// OutcomePass: graded, and the implementation matched.
	OutcomePass Outcome = "PASS"

	// OutcomeFail: graded, and the implementation disagreed. A defect.
	OutcomeFail Outcome = "FAIL"

	// OutcomeRefused: the harness refuses to grade this vector, because doing so
	// would be broken by construction — the capture seam is blind to something
	// the case needs, the capability is outside the graded domain, or the request
	// is outside it. Distinct from PASS and distinct from FAIL, reported in its
	// own column, and never silently treated as coverage.
	OutcomeRefused Outcome = "REFUSED"

	// OutcomeInadmissible: the file is not a valid vector of its declared class.
	// A probe wearing a parity label, a capture from another build, a float
	// token, a broken transcription. The run is untrustworthy, not merely short.
	OutcomeInadmissible Outcome = "INADMISSIBLE"

	// OutcomeError: the harness itself could not complete this vector.
	OutcomeError Outcome = "HARNESS-ERROR"
)

// Result is one vector's graded outcome.
type Result struct {
	CaseID  string
	Context string
	Class   VectorClass
	Path    string
	Seam    string
	Outcome Outcome
	Reason  RefusalReason
	Detail  []string

	// GradedCells and UngradedCells count the money and date cells actually
	// compared, and the cells the capture never recorded. Coverage is a number
	// here rather than an impression, because "13 of 13 observations reproduce"
	// once meant three scalars per shape and no due date at all.
	GradedCells   int
	UngradedCells int

	Invariants []InvariantResult
}

// Summary is the whole run.
type Summary struct {
	ImplementationName string
	OracleProbe        string
	SelfTestMode       bool
	StoreRoot          string
	ContextFilter      string

	Results []Result

	// LoadErrors are files that could not be read or decoded at all.
	LoadErrors []LoadError

	// FatalReasons are conditions that make the whole run unusable regardless of
	// any individual vector: no implementation, an unreachable oracle, a
	// contract digest mismatch, an empty store.
	FatalReasons []string

	ParityPass, ParityFail          int
	ContractPass, ContractFail      int
	SelfTestPass, SelfTestFail      int
	Refused, Inadmissible, Errored  int
	GradedCells, UngradedCells      int
	InvariantViolations             int
}

// ExitCode is the harness's verdict as a process exit status.
//
//	0 — every graded vector passed, at least one PARITY vector was graded, the
//	    oracle was confirmed reachable, and nothing was refused, inadmissible or
//	    errored. This is the only code that means anything like conformance, and
//	    it still does not mean "safe to cut over".
//	1 — at least one graded vector FAILED, or an invariant was violated. A
//	    definite, reproducible defect.
//	2 — the harness, the corpus or the oracle is unusable, so no verdict can be
//	    trusted: no implementation to grade, an unreachable oracle, zero parity
//	    vectors, an inadmissible vector, a refused vector, a load error.
//
// FAIL takes precedence over UNUSABLE, deliberately: a mismatch is a definite
// and actionable finding, whereas unusability is the absence of a finding, and
// the louder of the two should win. Both are non-zero, so neither can ever be
// mistaken for a pass — which is the only property that actually matters here.
func (s *Summary) ExitCode() int {
	if s.ParityFail+s.ContractFail+s.SelfTestFail > 0 || s.InvariantViolations > 0 {
		return 1
	}
	if len(s.FatalReasons) > 0 || len(s.LoadErrors) > 0 ||
		s.Refused > 0 || s.Inadmissible > 0 || s.Errored > 0 {
		return 2
	}
	if !s.SelfTestMode && s.ParityPass == 0 {
		// A run that graded no PARITY vector cannot support a parity claim, so it
		// is never exit 0 — self-test fixtures and contract-refusal vectors do not
		// substitute for an oracle observation. Self-test mode is exempt because it
		// grades the harness rather than a port, and every line of its report says
		// so; a green self-test run is a statement about this code, never about
		// parity with Fineract.
		return 2
	}
	return 0
}

// Options configures a run.
type Options struct {
	// RepoRoot is the repository root. Capture references and the frozen contract
	// path are resolved against it.
	RepoRoot string

	// StoreRoot is the vector store, normally <RepoRoot>/.softhouse/vectors.
	StoreRoot string

	// ContextFilter, when non-empty, grades only that context directory.
	ContextFilter string

	// Implementation is the generator under test. A nil implementation is NOT an
	// empty pass: it is a fatal reason and exit 2.
	Implementation contract.ScheduleGenerator

	// ImplementationName is printed in the report so a reader always knows what
	// was graded.
	ImplementationName string

	// OracleProbe is "up", "down" or "skipped". It is supplied by the caller
	// (conformance.sh probes with curl) and DEFAULTS TO DOWN when empty, so a
	// caller that forgets to probe cannot obtain exit 0.
	OracleProbe string

	// SelfTestMode grades the harness rather than an implementation. In self-test
	// mode the parity-vector requirement and the oracle probe are not applied,
	// and every line of the report says SELF-TEST so that no reader can mistake
	// the result for a conformance PASS.
	SelfTestMode bool
}

// Run loads the store, grades every vector and returns the summary.
func Run(ctx context.Context, opts Options) (*Summary, error) {
	s := &Summary{
		ImplementationName: opts.ImplementationName,
		OracleProbe:        opts.OracleProbe,
		SelfTestMode:       opts.SelfTestMode,
		StoreRoot:          opts.StoreRoot,
		ContextFilter:      opts.ContextFilter,
	}
	if s.ImplementationName == "" {
		s.ImplementationName = "(none)"
	}
	if s.OracleProbe == "" {
		s.OracleProbe = "down"
	}

	pin, err := LoadPin(filepath.Join(opts.StoreRoot, "PIN.json"))
	if err != nil {
		s.FatalReasons = append(s.FatalReasons, err.Error())
		return s, nil
	}
	if err := VerifyContractDigest(opts.RepoRoot, pin); err != nil {
		s.FatalReasons = append(s.FatalReasons, err.Error())
	}
	registry, err := LoadCapabilityRegistry(filepath.Join(opts.StoreRoot, "capabilities.json"))
	if err != nil {
		s.FatalReasons = append(s.FatalReasons, err.Error())
		return s, nil
	}

	if !opts.SelfTestMode {
		switch s.OracleProbe {
		case "up":
		case "skipped":
			s.FatalReasons = append(s.FatalReasons,
				"the reference oracle was not probed: a conformance PASS is a claim about parity with a live "+
					"pinned oracle build, so an unprobed run is exit 2 by construction "+
					"(.softhouse/patterns.md: \"if it is down, conformance reports exit 2, not a false PASS\")")
		default:
			s.FatalReasons = append(s.FatalReasons,
				"the reference oracle is UNREACHABLE: conformance is exit 2, which is not a PASS and never "+
					"becomes one (.softhouse/reference-oracle.md)")
		}
	}
	if opts.Implementation == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO IMPLEMENTATION REGISTERED: there is nothing to grade. This is exit 2, not a pass over zero "+
				"work. Register the Go port in cmd/conformance/impl_hook.go once it exists.")
	}

	vectors, loadErrs, err := LoadStore(opts.StoreRoot, opts.ContextFilter)
	if err != nil {
		s.FatalReasons = append(s.FatalReasons, err.Error())
		return s, nil
	}
	s.LoadErrors = loadErrs
	if len(vectors) == 0 {
		where := opts.StoreRoot
		if opts.ContextFilter != "" {
			where = filepath.Join(opts.StoreRoot, opts.ContextFilter)
		}
		s.FatalReasons = append(s.FatalReasons, fmt.Sprintf(
			"ZERO VECTORS FOUND under %s: an empty vector set is exit 2. A harness that reported PASS over "+
				"zero vectors would be the single worst outcome available to it.", where))
	}

	for _, v := range vectors {
		r := gradeVector(ctx, v, pin, registry, opts)
		s.Results = append(s.Results, r)
		s.GradedCells += r.GradedCells
		s.UngradedCells += r.UngradedCells
		for _, iv := range r.Invariants {
			if iv.Status == InvariantViolated {
				s.InvariantViolations++
			}
		}
		switch r.Outcome {
		case OutcomePass:
			switch v.Class {
			case ClassParity:
				s.ParityPass++
			case ClassContractRefusal:
				s.ContractPass++
			case ClassSelfTest:
				s.SelfTestPass++
			}
		case OutcomeFail:
			switch v.Class {
			case ClassParity:
				s.ParityFail++
			case ClassContractRefusal:
				s.ContractFail++
			case ClassSelfTest:
				s.SelfTestFail++
			}
		case OutcomeRefused:
			s.Refused++
		case OutcomeInadmissible:
			s.Inadmissible++
		case OutcomeError:
			s.Errored++
		}
	}

	if !opts.SelfTestMode && s.ParityPass == 0 && len(vectors) > 0 {
		s.FatalReasons = append(s.FatalReasons,
			"NO PARITY VECTOR WAS GRADED. Self-test fixtures and contract-refusal vectors do not make a "+
				"parity claim: the first is hand-authored, the second is derived from the ratified contract "+
				"rather than observed from the oracle. Until a capture is promoted, this harness cannot say "+
				"the port matches Fineract, and it will not pretend to.")
	}
	return s, nil
}

func gradeVector(ctx context.Context, v *Vector, pin *Pin, registry *CapabilityRegistry,
	opts Options) Result {

	r := Result{
		CaseID:  v.CaseID,
		Context: v.Context,
		Class:   v.Class,
		Path:    v.Path,
		Seam:    v.Oracle.Seam,
	}
	if problems := Admit(v, pin, opts.RepoRoot); len(problems) > 0 {
		r.Outcome = OutcomeInadmissible
		r.Detail = problems
		return r
	}

	// Capability gating comes before the request's own graded-domain check,
	// because a seam that cannot see something is a stronger obstruction than a
	// value nobody has promoted a vector for.
	verdict := registry.Assess(v.Oracle.Seam, v.CapabilitiesRequired)
	if !verdict.Gradeable {
		r.Outcome = OutcomeRefused
		r.Reason = verdict.Reason
		r.Detail = verdict.Detail
		return r
	}

	if v.Expect.Kind == "schedule" {
		if ok, why := GradedDomain(v); !ok {
			r.Outcome = OutcomeRefused
			r.Reason = ReasonUngradedRequest
			r.Detail = why
			return r
		}
	}

	if opts.Implementation == nil {
		r.Outcome = OutcomeError
		r.Detail = []string{"no implementation to grade"}
		return r
	}

	req, err := v.Request.ContractRequest()
	if err != nil {
		r.Outcome = OutcomeInadmissible
		r.Detail = []string{fmt.Sprintf("request does not map onto the frozen contract: %v", err)}
		return r
	}

	got, genErr := opts.Implementation.Generate(ctx, req)

	if v.Expect.Kind == "refusal" {
		ok, why := matchesSentinel(genErr, v.Expect.Sentinel)
		if !ok {
			r.Outcome = OutcomeFail
			r.Detail = []string{why}
			return r
		}
		r.Outcome = OutcomePass
		r.GradedCells = 1
		r.Detail = []string{fmt.Sprintf("refused with %s, as the contract requires", v.Expect.Sentinel)}
		return r
	}

	if genErr != nil {
		r.Outcome = OutcomeFail
		r.Detail = []string{fmt.Sprintf("expected a schedule of %d rows, got error: %v",
			len(v.Expect.Periods), genErr)}
		return r
	}

	diffs, graded, ungraded := diffSchedule(v, got)
	r.GradedCells, r.UngradedCells = graded, ungraded
	r.Invariants = CheckInvariants(v, got)
	if len(diffs) > 0 {
		r.Outcome = OutcomeFail
		r.Detail = diffs
		return r
	}
	for _, iv := range r.Invariants {
		if iv.Status == InvariantViolated {
			r.Outcome = OutcomeFail
			r.Detail = append(r.Detail, fmt.Sprintf("invariant %s VIOLATED: %s", iv.Name, iv.Detail))
		}
	}
	if r.Outcome == "" {
		r.Outcome = OutcomePass
	}
	return r
}

// diffSchedule compares the returned schedule against the vector, cell by cell.
//
// EVERY cell, not the headline scalars. The first observed defect in DEC-1 lived
// in exactly the cells a three-scalar check never looked at, so a row's kind,
// installment number, both dates and all three money columns are each compared
// separately and each reported separately. A cell the capture never recorded is
// counted as ungraded rather than compared against a fabricated expectation.
func diffSchedule(v *Vector, got contract.Schedule) (diffs []string, graded, ungraded int) {
	if len(got.Periods) != len(v.Expect.Periods) {
		diffs = append(diffs, fmt.Sprintf("row count: expected %d, got %d",
			len(v.Expect.Periods), len(got.Periods)))
		if len(got.Periods) < len(v.Expect.Periods) {
			return diffs, 0, 0
		}
	}
	n := len(v.Expect.Periods)
	if len(got.Periods) < n {
		n = len(got.Periods)
	}
	for i := 0; i < n; i++ {
		want, have := v.Expect.Periods[i], got.Periods[i]
		unrecorded := map[string]bool{}
		for _, f := range want.UnrecordedFields {
			unrecorded[f] = true
		}
		cmp := func(field, wantStr, haveStr string) {
			if unrecorded[field] {
				ungraded++
				return
			}
			graded++
			if wantStr != haveStr {
				diffs = append(diffs, fmt.Sprintf("row %d %s: expected %s, got %s", i, field, wantStr, haveStr))
			}
		}
		cmp("kind", want.Kind, periodKindName(have.Kind))
		cmp("installment_number", fmt.Sprint(want.InstallmentNumber), fmt.Sprint(have.InstallmentNumber))
		cmp("from_date", want.FromDate.String(), civil(have.FromDate))
		cmp("due_date", want.DueDate.String(), civil(have.DueDate))
		money := []struct {
			field string
			want  MinorText
			have  int64
		}{
			{"principal_minor", want.PrincipalMinor, have.PrincipalMinor},
			{"interest_minor", want.InterestMinor, have.InterestMinor},
			{"outstanding_principal_minor", want.OutstandingPrincipalMinor, have.OutstandingPrincipalMinor},
		}
		for _, m := range money {
			if unrecorded[m.field] {
				ungraded++
				continue
			}
			wv, err := m.want.Int64()
			if err != nil {
				diffs = append(diffs, fmt.Sprintf("row %d %s: %v", i, m.field, err))
				continue
			}
			graded++
			if wv != m.have {
				diffs = append(diffs, fmt.Sprintf("row %d %s: expected %s minor units, got %s (delta %s)",
					i, m.field, FormatMinor(wv), FormatMinor(m.have), FormatMinor(m.have-wv)))
			}
		}
	}
	return diffs, graded, ungraded
}

// FormatRefusalHint returns the operator-facing sentence for a refusal reason:
// what has to happen for the refusal to retire. They retire differently, and
// conflating them is how a blind capture gets re-graded instead of re-captured.
func FormatRefusalHint(reason RefusalReason) string {
	switch reason {
	case ReasonSeamBlind:
		return "retire by RE-CAPTURING on a seam that exercises the capability; promoting anything from this " +
			"seam cannot help, because the capture has zero discriminating power here"
	case ReasonUngradedCapability:
		return "retire by PROMOTING a discriminating vector for the capability, then setting " +
			"in_graded_domain on it in capabilities.json"
	case ReasonUngradedRequest:
		return "retire by WIDENING the graded domain (behaviour, not shape — no amendment) once a " +
			"discriminating vector for that value exists"
	case ReasonUnknownCapability:
		return "retire by DEFINING the capability and its per-seam status in capabilities.json; " +
			"default-deny means an unaudited input is assumed invisible"
	case ReasonUnknownSeam:
		return "retire by DECLARING the seam and its capability statuses in capabilities.json"
	}
	return ""
}

// ContextsIn lists the context directories present in a store, for a caller that
// wants to report an unmatched filter usefully.
func ContextsIn(vectors []*Vector) string {
	seen := map[string]bool{}
	var out []string
	for _, v := range vectors {
		if !seen[v.Context] {
			seen[v.Context] = true
			out = append(out, v.Context)
		}
	}
	return strings.Join(out, ", ")
}
