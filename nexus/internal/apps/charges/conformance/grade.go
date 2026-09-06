package conformance

import (
	"context"
	"fmt"
	"path/filepath"
	"sort"
	"strings"

	"github.com/gerege/nexus/internal/apps/charges"
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

// cellSink is the ONLY route by which the comparator can record a compared
// cell. CellFields() returns what a comparison run over a probe actually
// emitted, so there is no hand-written list of cells to drift from the code.
type cellSink struct {
	names  []string
	diffs  []string
	graded int
	money  int
}

// cmpStr compares one non-money cell and records that it was compared.
func (s *cellSink) cmpStr(name, want, got string) {
	s.names = append(s.names, name)
	s.graded++
	if want != got {
		s.diffs = append(s.diffs, fmt.Sprintf("%s: want %q, got %q", name, want, got))
	}
}

// cmpInt compares one non-money integer cell.
func (s *cellSink) cmpInt(name string, want, got int64) {
	s.names = append(s.names, name)
	s.graded++
	if want != got {
		s.diffs = append(s.diffs, fmt.Sprintf("%s: want %d, got %d", name, want, got))
	}
}

// cmpMoney compares one MONEY cell in int64 minor units and returns the signed
// margin. It is a separate method from cmpInt so the report can distinguish a
// money kill from a structural cell difference.
func (s *cellSink) cmpMoney(name string, want, got charges.MinorUnits) charges.MinorUnits {
	s.names = append(s.names, name)
	s.graded++
	s.money++
	if want != got {
		s.diffs = append(s.diffs, fmt.Sprintf(
			"%s: MONEY want %d, got %d (margin %d minor units)", name, want, got, got-want))
		return got - want
	}
	return 0
}

// diffCharge compares an expected charge result with the one an implementation
// produced. Every comparison goes through the sink.
func diffCharge(s *cellSink, v *Vector, got ChargeResult) {
	s.cmpInt("validation_code_count", int64(len(v.Expect.ValidationCodes)), int64(len(got.ValidationCodes)))
	n := len(v.Expect.ValidationCodes)
	if len(got.ValidationCodes) < n {
		n = len(got.ValidationCodes)
	}
	for i := 0; i < n; i++ {
		s.cmpStr(fmt.Sprintf("validation_codes[%d]", i), v.Expect.ValidationCodes[i], got.ValidationCodes[i])
	}
	if v.Expect.Kind == ExpectFee {
		want, _ := parseMinorText(v.Expect.FeeMinor) // Admit guarantees parseability
		s.cmpMoney("fee_minor", want, got.FeeMinor)
		s.cmpInt("fee_present", 1, boolToInt(got.FeePresent))
	}
}

func boolToInt(b bool) int64 {
	if b {
		return 1
	}
	return 0
}

// CellFields returns the complete set of cell names this comparator can compare.
//
// It is COMPUTED by running the comparator over probe pairs that exercise every
// branch, not transcribed. The probes are deliberately tiny and their numbers
// are meaningless: nothing here is an observation and nothing is graded.
func CellFields() []string {
	var s cellSink

	// The fee probe exercises the fee_minor and fee_present cells.
	feeProbe := &Vector{
		Class: ClassParity,
		Request: ChargeRequest{
			Name: "probe", CurrencyCode: "MNT", AmountMinor: "0",
			AppliesTo: 1, TimeType: 1, CalculationType: 1, PaymentMode: 0,
			BaseAmountMinor: "100",
		},
		Expect: ChargeExpect{Kind: ExpectFee, FeeMinor: "1"},
	}
	got, _ := (goEvaluator{}).Evaluate(feeProbe.Request)
	diffCharge(&s, feeProbe, got)

	// The validation probe carries a code, so the validation_codes[] branch is
	// exercised; a probe with an empty list would silently drop it from the
	// vocabulary and every divergent_cells entry naming it would be INADMISSIBLE.
	valProbe := &Vector{
		Class: ClassParity,
		Request: ChargeRequest{
			Name: "probe", AmountMinor: "0",
			AppliesTo: 2, TimeType: 1, CalculationType: 1, PaymentMode: 0,
		},
		Expect: ChargeExpect{Kind: ExpectValidation, ValidationCodes: []string{"c"}},
	}
	got2, _ := (goEvaluator{}).Evaluate(valProbe.Request)
	diffCharge(&s, valProbe, got2)

	seen := map[string]bool{}
	var out []string
	for _, n := range s.names {
		n = stripIndex(n)
		if !seen[n] {
			seen[n] = true
			out = append(out, n)
		}
	}
	sort.Strings(out)
	return out
}

// stripIndex turns "validation_codes[0]" into "validation_codes[]".
func stripIndex(n string) string {
	i := strings.Index(n, "[")
	j := strings.Index(n, "]")
	if i < 0 || j < i {
		return n
	}
	return n[:i+1] + n[j:]
}

// IsCellField reports whether name is a cell this comparator compares.
func IsCellField(name string) bool {
	for _, c := range CellFields() {
		if c == name {
			return true
		}
	}
	return false
}

// Options configures a conformance run.
type Options struct {
	RepoRoot           string
	StoreRoot          string
	ContextFilter      string
	Implementation     ChargeEvaluator
	ImplementationName string
	Pin                *Pin
	Registry           *CapabilityRegistry
	SelfTestMode       bool
}

// Summary is the aggregate outcome of a run. The type and its ExitCode live in
// nexus/internal/conformance; charges re-uses them unchanged.
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

	var s cellSink
	diffCharge(&s, v, got)
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

	// The no-float census runs FIRST and on EVERY run, with or without vectors.
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

	// With vectors present, the implementation, pin and capability registry are
	// all required; each missing one refuses the whole run rather than grading
	// with a silent gap.
	if opts.Implementation == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO IMPLEMENTATION REGISTERED: there is nothing to grade. This is exit 2, not a pass over zero work.")
		return s, nil
	}
	if opts.Pin == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO STORE PIN: the pin (PIN-charges.json) must be loaded to grade a non-empty corpus.")
		return s, nil
	}
	if opts.Registry == nil {
		s.FatalReasons = append(s.FatalReasons,
			"NO CAPABILITY REGISTRY: the registry (capabilities-charges.json) must be loaded to grade a non-empty corpus.")
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
