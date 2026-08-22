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

	// PlaceholderCells counts the cells of the returned schedule the
	// implementation declared it could not compute (finding T58-N2). It is 0 for
	// every real implementation; only the self-test replay ever reports one, and
	// only for a cell the vector's own unrecorded_fields withdrew.
	PlaceholderCells int

	// RateFactorsRecorded counts the rate-factor observations this vector carries.
	// They are NEVER compared against anything (finding T17-F6: every one is a
	// 12-dp rounding of the engine's value), so they are counted apart from the
	// graded cells and never added to them.
	RateFactorsRecorded int

	// OverScaledCells counts money cells whose wire text carries more fraction
	// digits than the currency has minor units, and that the vector declared as
	// such (finding T17-F5). An UNDECLARED one is inadmissible, so this number
	// only ever counts values somebody wrote down deliberately.
	OverScaledCells int

	Invariants []InvariantResult
}

// Summary is the whole run.
type Summary struct {
	ImplementationName string
	OracleProbe        string
	SelfTestMode       bool
	StoreRoot          string
	ContextFilter      string

	// RepoRoot is the checkout that was graded and RepoRootRes is how it was
	// chosen. Both are printed in the header. "store" alone was not enough: a
	// store path says which CORPUS was read and says nothing about which tree
	// the no-float census walked, which contract.go was hashed, or which
	// checkout the capture_refs were resolved in — all four came from one root,
	// and before T165 that root was the caller's working directory.
	RepoRoot    string
	RepoRootRes RepoRootResolution

	Results []Result

	// LoadErrors are files that could not be read or decoded at all.
	LoadErrors []LoadError

	// FatalReasons are conditions that make the whole run unusable regardless of
	// any individual vector: no implementation, an unreachable oracle, a
	// contract digest mismatch, an empty store.
	FatalReasons []string

	ParityPass, ParityFail         int
	ContractPass, ContractFail     int
	SelfTestPass, SelfTestFail     int
	Refused, Inadmissible, Errored int
	GradedCells, UngradedCells     int
	InvariantViolations            int

	// InvariantAssertionsNotRun counts the individual invariant assertions that
	// could NOT be made because a cell they read was never observed (finding
	// T58-N2). It is reported next to the violation count and printed in full in
	// its own section, because a check that quietly stops checking is strictly
	// worse than a red one. 0 on the committed corpus.
	InvariantAssertionsNotRun int

	// CounterfactualsNamed is how many wrong implementations the GRADED vectors
	// between them claim to kill, and CounterfactualCoverage maps each graded
	// capability to the counterfactual ids covering it.
	CounterfactualsNamed   int
	CounterfactualCoverage map[string][]string

	// RefusedCounterfactualsNamed and RefusedCorroborationsClaimed are the claims
	// carried by REFUSED vectors. They are counted and PRINTED, and they are
	// credited to nothing (finding A2-19 F3).
	//
	// A refusal is "not a pass, not a failure": it says no discriminating vector
	// exists here, or the seam is blind to the behaviour. A vector that graded
	// nothing cannot back anything, so its named kills must not enter
	// CounterfactualsNamed and must not remove a capability from
	// UncoveredGradedCapabilities. Before A2-22 they did both, which meant a
	// refusal made the coverage report QUIETER — the one case with less evidence
	// going silent.
	//
	// They are counted rather than dropped because a number that vanishes is a
	// number nobody can audit: a reader must be able to see that 62 claims were
	// withheld and why, not merely that the total fell.
	RefusedCounterfactualsNamed  int
	RefusedCorroborationsClaimed int

	// ErroredCounterfactualsNamed and ErroredCorroborationsClaimed are the same
	// disclosure for HARNESS-ERROR vectors, and they close finding A2-22-F3 /
	// A2-24-F3 rather than merely noting it (A2-27).
	//
	// A HARNESS-ERROR vector is the STRONGEST case of "graded nothing": a refusal
	// at least decided that this vector cannot discriminate, whereas an error
	// means the harness could not complete the vector at all. It was nevertheless
	// entering the graded population, because the loop below skipped only
	// INADMISSIBLE and REFUSED. That is not merely latent. It is reachable through
	// the ordinary public API — Options.Implementation == nil, which is the
	// standing state of cmd/conformance/impl_hook.go until a port is registered —
	// and MEASURED on the committed store it read:
	//
	//	results 51 · errored 51 · CELLS COMPARED 0
	//	counterfactuals named by GRADED vectors: 113 (106 money, 7 structural)
	//	UNBACKED in_graded_domain claims: (none)
	//
	// A run that compared nothing claimed 113 kills and reported every capability
	// backed. That is exactly the A2-19 F3 shape the refused half of this struct
	// was written to stop — less evidence, quieter report — reached by the other
	// door. The run is exit 2 either way, so no exit code moves; what moves is the
	// sentence a reader takes away from a fatal run.
	ErroredCounterfactualsNamed  int
	ErroredCorroborationsClaimed int

	// MoneyKills and StructuralKills split CounterfactualsNamed by kind, and the
	// report prints them separately (driver finding D-4). Merging them would let a
	// store of nothing but structural kills read as though it graded amounts —
	// which is precisely the confusion the split exists to prevent.
	MoneyKills      int
	StructuralKills int

	// RateFactorsRecorded and OverScaledCells aggregate the per-vector counts.
	RateFactorsRecorded int
	OverScaledCells     int

	// CorroborationsClaimed is how many cross-check claims the GRADED vectors
	// make — the same population as CounterfactualsNamed, and FOR ITS OWN REASON,
	// not by symmetry with it. The two claims do not even have the same
	// truth-conditions: a counterfactual asserts DISCRIMINATION and its antecedent
	// is grading, so a refusal leaves it unrealised; a corroboration asserts
	// something about the RECORD ("a named second source printed these columns for
	// this row kind and agreed"), it is validated offline at admission
	// (admitCorroborations), and none of the five refusal reasons impugns it. A
	// refused vector's corroboration is still TRUE.
	//
	// It is nevertheless scoped to the graded population, because this report
	// scopes by POLARITY rather than by truth: hazard disclosures take the WIDEST
	// population (RateFactorsRecorded and OverScaledCells are accumulated in
	// gradeVector before any early return, so a refused vector still contributes
	// them), and SUPPORT counts take the NARROWEST. A corroboration exists only to
	// make the corpus look better attested — it can never make it look worse — so
	// it is support, and support is scoped to what the run actually compared.
	//
	// The case that settles it: on a store where one blinded seam refuses
	// everything, the wide rule prints "cells compared: 0" and a corroboration
	// count of the WHOLE CORPUS in the same report. A cross-check of columns that
	// were never compared to anything is the limiting case of the
	// confidence-nobody-measured that finding T17-F2 exists to prevent.
	//
	// The claims shed by REFUSED vectors are in RefusedCorroborationsClaimed and
	// by ERRORED vectors in ErroredCorroborationsClaimed; both are printed whether
	// or not they are zero, so nothing is hidden and the store-quality reader can
	// still recover the corpus total by adding them. Every claim is scoped to the
	// columns its source actually prints. (A2-22 narrowed it; A2-24 adjudicated
	// and approved it; A2-27 corrected this comment, which still said "admissible"
	// and was the tell that the corroboration half had ridden along without its
	// own reasoning.)
	CorroborationsClaimed int

	// UncoveredGradedCapabilities are capabilities marked in_graded_domain for
	// which no parity vector kills a named wrong implementation. An unbacked
	// claim, and a fatal reason.
	UncoveredGradedCapabilities []string

	// NoFloatCensus is what the no-float guard INSPECTED on this run — files,
	// tokens, and the count of each violation class. It is reported whether or
	// not anything was found, because a guard that only speaks when it fails is
	// indistinguishable from a guard that never ran (P-35).
	NoFloatCensus FloatingPointCensus
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

	// RepoRootRes is HOW RepoRoot was decided, and it is printed on every run.
	// cmd/conformance fills it from ResolveRepoRoot; a programmatic caller (the
	// Go tests) may leave it zero, and the report then says so in as many words
	// rather than implying the root was anchored when nothing recorded that it
	// was. Before T165 there was nothing to record: the root came from the
	// caller's working directory and no line of the report mentioned it.
	RepoRootRes RepoRootResolution

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
		RepoRoot:           opts.RepoRoot,
		RepoRootRes:        opts.RepoRootRes,
	}
	if s.ImplementationName == "" {
		s.ImplementationName = "(none)"
	}
	if s.OracleProbe == "" {
		s.OracleProbe = "down"
	}

	// The harness's own standing declarations are checked before anything else.
	// A weakened declaration — a narrowed claim that lost the observation that
	// narrowed it, a coverage gap marked closed with no capture behind it, a
	// rate-factor parity claim with nothing to point at — makes this run UNUSABLE
	// rather than quietly permissive.
	for _, defect := range HarnessDeclarationDefects() {
		s.FatalReasons = append(s.FatalReasons,
			"HARNESS DECLARATION DEFECT (structural.go): "+defect)
	}

	// THE NO-FLOAT CENSUS GATES THE VERDICT, not merely the test suite.
	//
	// conformance.sh does not run `go test`; it builds and runs this binary. So
	// before T154 a floating-point LITERAL on a money path could take the whole
	// conformance run to exit 0 (T143/M-3). The census runs here, its counts are
	// printed in the report whether or not anything is wrong, and any violation
	// is fatal. Zero files scanned is an error returned by the census itself.
	//
	// T166 WIDENED THE ROOT FROM ONE SUBTREE TO THE MODULE. Until T166 this call
	// passed LoanScheduleTreeRel, so a float anywhere outside
	// nexus/internal/apps/loanschedule — a whole new package, or any
	// SUBDIRECTORY of one — reached VERDICT: PASS untouched. Measured, not
	// theorised: three planted floats under nexus/internal/apps/ledger/ produced
	// a run log byte-identical to the clean baseline. GuardedGoTreeRel is now the
	// module root and the walk recurses, so a new package is covered by default.
	if census, cerr := ScanGoTreeForFloatingPoint(filepath.Join(opts.RepoRoot, GuardedGoTreeRel)); cerr != nil {
		s.FatalReasons = append(s.FatalReasons, "THE NO-FLOAT GUARD COULD NOT RUN: "+cerr.Error())
	} else {
		s.NoFloatCensus = census
		for _, v := range census.Violations() {
			s.FatalReasons = append(s.FatalReasons, "FLOATING POINT ON A MONEY PATH: "+v)
		}
	}

	// D-1 (T155): the census's own zero-files check lives INSIDE
	// ScanGoTreeForFloatingPoint, so it only fires when the census actually RUNS.
	// Delete the call site above and nothing runs, NoFloatCensus stays zero-valued,
	// and the report prints "0 Go files / 0 tokens" beside VERDICT: PASS on a tree
	// containing 0.036 — while report.go's own comment says 0 files means exit 2.
	// `go test` catches that deletion; `conformance.sh` does not run `go test`
	// (P-45), which is the exact shape T154 was dispatched to close. So the
	// assertion lives HERE, as a SEPARATE statement, precisely so that a minimal
	// deletion of the block above leaves it standing and it fires.
	if s.NoFloatCensus.FilesScanned == 0 {
		s.FatalReasons = append(s.FatalReasons,
			"THE NO-FLOAT CENSUS INSPECTED ZERO GO FILES: a guard that inspects nothing passes everything, "+
				"so this is an ERROR and not a pass")
	}
	// T166: the SAME assertion on the PACKAGE count, and for the same reason it
	// is a separate statement rather than an `||` on the line above. A file count
	// cannot distinguish "the module was walked" from "one directory was walked";
	// a package count of 1 on a multi-package module is the shape the pre-T166
	// root had, and a package count of 0 is a walk that opened nothing.
	if s.NoFloatCensus.PackagesScanned == 0 {
		s.FatalReasons = append(s.FatalReasons,
			"THE NO-FLOAT CENSUS INSPECTED ZERO GO PACKAGES: a guard that inspects nothing passes everything, "+
				"so this is an ERROR and not a pass")
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

	// s.LoadErrors is recorded BEFORE the error is examined, because LoadStore's
	// store-integrity refusals (a duplicate case_id) carry the load errors out
	// with them: a store that is both malformed and duplicated must report both,
	// not whichever the control flow happened to reach first.
	vectors, loadErrs, err := LoadStore(opts.StoreRoot, opts.ContextFilter)
	s.LoadErrors = loadErrs
	if err != nil {
		// The grading loop is BELOW this return. A duplicate case_id therefore
		// refuses the run before a single vector is graded, and no vector count
		// or cell count is ever computed that a reader could quote.
		s.FatalReasons = append(s.FatalReasons, err.Error())
		return s, nil
	}
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
		s.RateFactorsRecorded += r.RateFactorsRecorded
		s.OverScaledCells += r.OverScaledCells
		for _, iv := range r.Invariants {
			if iv.Status == InvariantViolated {
				s.InvariantViolations++
			}
			s.InvariantAssertionsNotRun += len(iv.NotAsserted)
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

	// Counterfactual coverage: is every capability we CALL graded actually backed
	// by a parity vector that kills a named wrong implementation for it?
	// THE POPULATION IS "GRADED", NOT "NOT INADMISSIBLE" (finding A2-19 F3).
	//
	// This list used to be every vector the run had not declared INADMISSIBLE, and
	// a REFUSED vector is not inadmissible — so the kills of vectors the harness
	// had just declined to grade were credited into the coverage report, the kill
	// count and the corroboration count alike. A refusal is "not a pass, not a
	// failure": it says no discriminating vector exists here, or the seam is blind
	// to the behaviour. A vector that graded nothing kills nothing.
	//
	// HARNESS-ERROR IS SHED FOR THE SAME REASON (finding A2-22-F3 / A2-24-F3,
	// closed by A2-27). This loop used to skip only INADMISSIBLE and REFUSED, so a
	// vector the harness could not complete AT ALL still credited its kills, its
	// corroborations and its capability coverage. If "a vector that graded nothing
	// kills nothing" is the rule, an errored vector is its strongest instance: a
	// refusal is at least a decision about the vector, an error is the absence of
	// one. Measured before the fix, with Options.Implementation nil: 51 errored
	// vectors, 0 cells compared, and the report still read "counterfactuals named
	// by GRADED vectors: 113" with no UNBACKED claim.
	//
	// The counts it sheds are RECORDED, in RefusedCounterfactualsNamed /
	// RefusedCorroborationsClaimed and ErroredCounterfactualsNamed /
	// ErroredCorroborationsClaimed, and printed by the report whether they are
	// zero or not. A number that silently disappears is a number nobody can audit,
	// and this fix must not be the thing that hides the next refusal.
	//
	// CounterfactualCoverage re-applies the same predicate for itself, so the two
	// cannot drift apart and no future caller can lose the rule by passing the
	// wrong list. Belt and braces on the exact defect that bit here.
	graded := make([]*Vector, 0, len(vectors))
	for i, v := range vectors {
		switch s.Results[i].Outcome {
		case OutcomeInadmissible:
			continue
		case OutcomeRefused:
			s.RefusedCounterfactualsNamed += len(v.GradedAgainst)
			s.RefusedCorroborationsClaimed += len(v.Provenance.CorroboratedBy)
			continue
		case OutcomeError:
			s.ErroredCounterfactualsNamed += len(v.GradedAgainst)
			s.ErroredCorroborationsClaimed += len(v.Provenance.CorroboratedBy)
			continue
		}
		graded = append(graded, v)
	}
	covered, uncovered := registry.CounterfactualCoverage(graded)
	s.CounterfactualCoverage = covered
	s.UncoveredGradedCapabilities = uncovered
	for _, v := range graded {
		s.CounterfactualsNamed += len(v.GradedAgainst)
		s.CorroborationsClaimed += len(v.Provenance.CorroboratedBy)
		for _, cf := range v.GradedAgainst {
			if cf.Kind == CounterfactualStructural {
				s.StructuralKills++
				continue
			}
			s.MoneyKills++
		}
	}
	if len(uncovered) > 0 && !opts.SelfTestMode {
		s.FatalReasons = append(s.FatalReasons, fmt.Sprintf(
			"THESE CAPABILITIES ARE MARKED in_graded_domain BUT NO PARITY VECTOR KILLS A NAMED WRONG "+
				"IMPLEMENTATION FOR THEM: %s. \"In the graded domain\" means a vector exists that can tell a "+
				"correct implementation from an incorrect one, and pair difference is NOT that test — "+
				"LB-DEC31 reports zero cells differing across the day-count setting and still kills a no-arm "+
				"port by 6,015 minor units (T55-N1). Either promote a vector with a graded_against entry, or "+
				"set in_graded_domain false in capabilities.json.",
			strings.Join(uncovered, ", ")))
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

	// Recorded-but-never-graded quantities, counted before anything else can
	// return: a rate factor is a 12-dp rounding (T17-F6) and a declared
	// over-scaled money text is an exact value the currency's scale did not
	// expect (T17-F5). Both are disclosures, and a disclosure nobody counts is a
	// disclosure nobody reads.
	for _, p := range v.Expect.Periods {
		if p.ObservedRateFactor != nil {
			r.RateFactorsRecorded++
		}
		r.OverScaledCells += len(p.OverScaledWireTextFields)
	}

	// A refusal vector goes STALE the moment its capability enters the graded
	// domain: "the implementation must refuse this" stops being the contract's
	// instruction. Detect it here and say "retire this vector", rather than let it
	// report FAIL and send a reader hunting for a defect in the port. This is also
	// why nothing in the harness hard-codes DayCountActualActual as refused —
	// flipping in_graded_domain retires the refusal by itself.
	if v.RetiresWhenCapabilityGraded != "" {
		graded, defined := registry.IsGraded(v.RetiresWhenCapabilityGraded)
		switch {
		case !defined:
			r.Outcome = OutcomeInadmissible
			r.Detail = []string{fmt.Sprintf(
				"retires_when_capability_graded names %q, which is not in the capability registry",
				v.RetiresWhenCapabilityGraded)}
			return r
		case graded:
			r.Outcome = OutcomeInadmissible
			r.Detail = []string{fmt.Sprintf(
				"STALE REFUSAL VECTOR: capability %q is now in_graded_domain, so refusing this request is no "+
					"longer what the contract requires. RETIRE THIS VECTOR and promote a parity vector in its "+
					"place — this is not a defect in any implementation.",
				v.RetiresWhenCapabilityGraded)}
			return r
		}
	}

	// THE REFUSAL PREDICATE LIVES IN ONE PLACE (A2-22). Capability gating comes
	// before the request's own graded-domain check, because a seam that cannot see
	// something is a stronger obstruction than a value nobody has promoted a
	// vector for — and that precedence is now stated once, inside RefusalFor, so
	// that the coverage report and this loop cannot disagree about which vectors
	// are refused. They used to: the coverage report never asked at all.
	if verdict := registry.RefusalFor(v); !verdict.Gradeable {
		r.Outcome = OutcomeRefused
		r.Reason = verdict.Reason
		r.Detail = verdict.Detail
		return r
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

	// FINDING T58-N2. The invariants read the schedule the implementation
	// RETURNED, so if the implementation could not compute a cell it must say
	// which, or the invariants grade a stand-in. A real port implements nothing
	// here and every invariant runs in full; only the self-test replay ever
	// declares a placeholder, and only for a cell the vector honestly withdrew.
	var placeholders PlaceholderCells
	if pr, ok := opts.Implementation.(PlaceholderReporter); ok {
		placeholders = pr.PlaceholderCells(req)
	}
	r.PlaceholderCells = placeholders.Count()
	r.Invariants = CheckInvariants(v, got, placeholders)
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
