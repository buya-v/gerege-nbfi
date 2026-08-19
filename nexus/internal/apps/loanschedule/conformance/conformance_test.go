package conformance

import (
	"bytes"
	"context"
	"fmt"
	"go/scanner"
	"go/token"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// repoRoot resolves the repository root once for every test in this file.
func repoRoot(t *testing.T) string {
	t.Helper()
	root, err := FindRepoRoot(".")
	if err != nil {
		t.Fatalf("FindRepoRoot: %v", err)
	}
	return root
}

func storeRoot(t *testing.T) string {
	t.Helper()
	return filepath.Join(repoRoot(t), ".softhouse", "vectors")
}

// TestStoreIsAdmissible is the table-driven conformance test: every file in the
// vector store is loaded, admitted and classified, and the test states what the
// corpus contains. It fails on an INADMISSIBLE file, because an inadmissible
// vector means the corpus cannot be trusted rather than merely that it is short.
func TestStoreIsAdmissible(t *testing.T) {
	root := repoRoot(t)
	store := storeRoot(t)

	pin, err := LoadPin(filepath.Join(store, "PIN.json"))
	if err != nil {
		t.Fatalf("LoadPin: %v", err)
	}
	if err := VerifyContractDigest(root, pin); err != nil {
		t.Fatalf("the frozen contract's digest does not match the store pin: %v", err)
	}
	registry, err := LoadCapabilityRegistry(filepath.Join(store, "capabilities.json"))
	if err != nil {
		t.Fatalf("LoadCapabilityRegistry: %v", err)
	}

	vectors, loadErrs, err := LoadStore(store, "")
	if err != nil {
		t.Fatalf("LoadStore: %v", err)
	}
	for _, le := range loadErrs {
		t.Errorf("%s could not be loaded as a vector: %v", le.Path, le.Err)
	}
	if len(vectors) == 0 {
		t.Fatal("the vector store is empty; even before promotion it must hold the self-test fixture")
	}

	counts := map[VectorClass]int{}
	for _, v := range vectors {
		v := v
		t.Run(v.CaseID, func(t *testing.T) {
			if problems := Admit(v, pin, root); len(problems) > 0 {
				for _, p := range problems {
					t.Errorf("INADMISSIBLE: %s", p)
				}
			}
			verdict := registry.Assess(v.Oracle.Seam, v.CapabilitiesRequired)
			if !verdict.Gradeable {
				t.Logf("REFUSED (%s): %s", verdict.Reason, strings.Join(verdict.Detail, "; "))
			}
			if v.Expect.Kind == "schedule" {
				if ok, why := GradedDomain(v); !ok {
					t.Logf("outside the graded domain: %s", strings.Join(why, "; "))
				}
			}
		})
		counts[v.Class]++
	}
	t.Logf("corpus: %d parity, %d contract-refusal, %d self-test",
		counts[ClassParity], counts[ClassContractRefusal], counts[ClassSelfTest])

	// The self-test fixture is not corpus. If this ever becomes the only thing
	// in the store AND the store starts reporting parity, something has gone
	// badly wrong upstream.
	if counts[ClassSelfTest] == 0 {
		t.Error("no self-test fixture found: the harness would have nothing to prove itself against")
	}
}

// TestHarnessGoesGreenAndRed is the mutation proof, in process.
//
// The shell harness proves the same four things end to end with real exit codes
// (.softhouse/conformance.sh --prove). This test proves them where a reviewer can
// step through them, and it runs under plain `go test ./...`.
func TestHarnessGoesGreenAndRed(t *testing.T) {
	root := repoRoot(t)
	pristine := storeRoot(t)

	t.Run("green_on_pristine_store", func(t *testing.T) {
		impl, n, err := NewReplayImplementation(pristine, "")
		if err != nil {
			t.Fatalf("NewReplayImplementation: %v", err)
		}
		if n == 0 {
			t.Fatal("the replay implementation learned no answers")
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: pristine,
			Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
		})
		if got := s.ExitCode(); got != 0 {
			t.Errorf("self-test over the pristine store: exit %d, want 0\n%s", got, render(s))
		}
		if s.SelfTestPass == 0 {
			t.Error("the self-test fixture did not pass")
		}
		// A PARITY PASS MUST BE EARNED.
		//
		// This assertion used to read "ParityPass must be 0, the store has no
		// promoted capture yet". That was a fact about the store on one day, not a
		// property of the harness, and it made `go test ./...` unmeetable the
		// moment a promotion succeeded (driver finding D-6). What it was actually
		// protecting is that the harness never reports a parity PASS it has not
		// earned, so that is what is asserted now — and it keeps holding as the
		// store fills up.
		vectors, _, lerr := LoadStore(pristine, "")
		if lerr != nil {
			t.Fatalf("LoadStore: %v", lerr)
		}
		byCase := map[string]*Vector{}
		for _, v := range vectors {
			byCase[v.CaseID] = v
		}
		if bad := parityPassViolations(s, byCase); len(bad) > 0 {
			t.Errorf("this run reports parity passes it did not earn:\n  %s", strings.Join(bad, "\n  "))
		}
		t.Logf("parity passes this run: %d (all earned)", s.ParityPass)

		// The other half of the property: with NO implementation registered there
		// is nothing to grade, so no parity pass is possible and the run is exit 2.
		none := mustRun(t, Options{RepoRoot: root, StoreRoot: pristine, SelfTestMode: true})
		if none.ParityPass != 0 {
			t.Errorf("with no implementation registered ParityPass must be 0, got %d", none.ParityPass)
		}
		if got := none.ExitCode(); got != 2 {
			t.Errorf("with no implementation registered the run must be exit 2, got %d", got)
		}

		// And a self-test run never claims conformance, however many vectors pass.
		out := render(s)
		for _, want := range []string{"SELF-TEST", "NOT a conformance PASS"} {
			if !strings.Contains(out, want) {
				t.Errorf("a self-test report must carry %q", want)
			}
		}
	})

	t.Run("the earned-parity check itself goes red", func(t *testing.T) {
		// RED PROOF for the replacement assertion: a summary claiming a parity
		// PASS for a case that is a hand-authored self-test fixture, and one
		// claiming a parity PASS with no implementation registered, must both be
		// reported as unearned. Without this, "all earned" could mean "the check
		// examines nothing".
		fixture := &Vector{
			CaseID: "PRETEND", Class: ClassSelfTest,
			Provenance: Provenance{Kind: ProvenanceHandAuthored},
		}
		s := &Summary{
			ImplementationName: "replay",
			ParityPass:         1,
			Results: []Result{{
				CaseID: "PRETEND", Class: ClassParity, Outcome: OutcomePass,
				Seam: "path_a_embeddable",
			}},
		}
		bad := parityPassViolations(s, map[string]*Vector{"PRETEND": fixture})
		if len(bad) == 0 {
			t.Fatal("a parity PASS for a hand-authored fixture must be reported as unearned")
		}
		s.ImplementationName = "(none)"
		if bad := parityPassViolations(s, map[string]*Vector{"PRETEND": fixture}); len(bad) == 0 {
			t.Fatal("a parity PASS with no implementation registered must be reported as unearned")
		}
	})

	t.Run("red_when_an_expected_value_is_perturbed", func(t *testing.T) {
		// A CONSISTENT one-minor-unit perturbation: both the integer and the
		// oracle's wire text move together, so the vector stays admissible and the
		// disagreement is between the vector and the implementation — which is
		// exactly what a conformance FAIL means. Exit 1.
		perturbed := copyStore(t, pristine)
		fixture := filepath.Join(perturbed, SelfTestDir, "SELFTEST-01-two-period-zero-rate.json")
		perturb(t, fixture, `"principal_minor": "50000",
        "interest_minor": "0",
        "outstanding_principal_minor": "50000",
        "principal_major_text": "500.00",`, `"principal_minor": "50001",
        "interest_minor": "0",
        "outstanding_principal_minor": "50000",
        "principal_major_text": "500.01",`)

		impl, _, err := NewReplayImplementation(pristine, "")
		if err != nil {
			t.Fatalf("NewReplayImplementation: %v", err)
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: perturbed,
			Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
		})
		if got := s.ExitCode(); got != 1 {
			t.Errorf("a one-minor-unit perturbation must be exit 1, got %d\n%s", got, render(s))
		}
		if s.SelfTestFail != 1 {
			t.Errorf("want exactly one failed vector, got SelfTestFail=%d", s.SelfTestFail)
		}
	})

	t.Run("inadmissible_when_only_the_integer_is_perturbed", func(t *testing.T) {
		// An INCONSISTENT perturbation: the integer moves and the oracle's own wire
		// text does not. That is not a conformance failure, it is a transcription
		// error, and the harness must say so — no other check in it could see one.
		// Exit 2, because a corpus that disagrees with itself grades nothing.
		perturbed := copyStore(t, pristine)
		perturb(t, filepath.Join(perturbed, SelfTestDir, "SELFTEST-01-two-period-zero-rate.json"),
			`"principal_minor": "50000"`, `"principal_minor": "50001"`)

		impl, _, err := NewReplayImplementation(pristine, "")
		if err != nil {
			t.Fatalf("NewReplayImplementation: %v", err)
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: perturbed,
			Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
		})
		if got := s.ExitCode(); got != 2 {
			t.Errorf("a transcription mismatch must be exit 2, got %d\n%s", got, render(s))
		}
		if s.Inadmissible != 1 {
			t.Errorf("want exactly one inadmissible vector, got %d", s.Inadmissible)
		}
	})

	t.Run("exit_2_when_the_store_is_empty", func(t *testing.T) {
		empty := t.TempDir()
		copyFile(t, filepath.Join(pristine, "PIN.json"), filepath.Join(empty, "PIN.json"))
		copyFile(t, filepath.Join(pristine, "capabilities.json"), filepath.Join(empty, "capabilities.json"))
		impl, _, err := NewReplayImplementation(pristine, "")
		if err != nil {
			t.Fatalf("NewReplayImplementation: %v", err)
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: empty,
			Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
		})
		if got := s.ExitCode(); got == 0 {
			t.Errorf("an empty store must never be exit 0, got %d\n%s", got, render(s))
		}
	})

	t.Run("exit_2_when_there_is_no_implementation", func(t *testing.T) {
		s := mustRun(t, Options{RepoRoot: root, StoreRoot: pristine, OracleProbe: "up"})
		if got := s.ExitCode(); got != 2 {
			t.Errorf("no implementation must be exit 2, got %d\n%s", got, render(s))
		}
		if !containsSubstring(s.FatalReasons, "NO IMPLEMENTATION REGISTERED") {
			t.Errorf("the report must say so in words, got %v", s.FatalReasons)
		}
	})

	t.Run("exit_2_when_the_oracle_is_unreachable", func(t *testing.T) {
		impl, _, err := NewReplayImplementation(pristine, "")
		if err != nil {
			t.Fatalf("NewReplayImplementation: %v", err)
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: pristine,
			Implementation: impl, ImplementationName: "replay", OracleProbe: "down",
		})
		if got := s.ExitCode(); got != 2 {
			t.Errorf("an unreachable oracle must be exit 2, got %d\n%s", got, render(s))
		}
	})

	t.Run("exit_2_when_the_caller_forgets_to_probe", func(t *testing.T) {
		impl, _, err := NewReplayImplementation(pristine, "")
		if err != nil {
			t.Fatalf("NewReplayImplementation: %v", err)
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: pristine,
			Implementation: impl, ImplementationName: "replay",
		})
		if got := s.ExitCode(); got != 2 {
			t.Errorf("an empty oracle-probe value must default to down and be exit 2, got %d", got)
		}
	})

	t.Run("self_test_fixture_never_counts_toward_parity", func(t *testing.T) {
		impl, _, err := NewReplayImplementation(pristine, SelfTestDir)
		if err != nil {
			t.Fatalf("NewReplayImplementation: %v", err)
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: pristine, ContextFilter: SelfTestDir,
			Implementation: impl, ImplementationName: "replay", OracleProbe: "up",
		})
		if s.SelfTestPass != 1 {
			t.Errorf("want the fixture to pass, got SelfTestPass=%d", s.SelfTestPass)
		}
		if s.ParityPass != 0 {
			t.Errorf("the fixture must not count toward parity, got ParityPass=%d", s.ParityPass)
		}
		if got := s.ExitCode(); got != 2 {
			t.Errorf("a run whose only passing vector is the hand-authored fixture must not be exit 0, got %d",
				got)
		}
		if !containsSubstring(s.FatalReasons, "NO PARITY VECTOR WAS GRADED") {
			t.Errorf("the report must say no parity vector was graded, got %v", s.FatalReasons)
		}
	})
}

// TestProbeCannotMasqueradeAsParity is the structural probe guard.
//
// Passes 1 and 2 of the capture corpus ran at precision 12 or 8, and production
// runs at (19, HALF_UP). Those captures are discrimination probes and may never
// be promoted as parity vectors. The guard is not a label: the harness reads the
// MathContext the numbers were produced at off the vector itself, so relabelling
// a probe cannot smuggle it in.
func TestProbeCannotMasqueradeAsParity(t *testing.T) {
	root := repoRoot(t)
	store := storeRoot(t)
	pin, err := LoadPin(filepath.Join(store, "PIN.json"))
	if err != nil {
		t.Fatalf("LoadPin: %v", err)
	}

	base := func() *Vector {
		return &Vector{
			Schema:               VectorSchemaV1,
			CaseID:               "FAKE-PROBE-AS-PARITY",
			Context:              "loanschedule",
			Class:                ClassParity,
			DEC1Revision:         pin.DEC1Revision,
			CapabilitiesRequired: []string{"schedule.core"},
			Provenance: Provenance{
				Kind:          ProvenanceOracleCapture,
				CaptureRef:    ".softhouse/capture/out/capture-raw.json",
				CaptureCaseID: "D-01",
			},
			Oracle: OracleStamp{
				FineractCommit:      pin.FineractCommit,
				Seam:                "path_a_embeddable",
				ThreadedMathContext: MathContext{Precision: 12, RoundingMode: "HALF_UP"},
				AmbientMathContext:  MathContext{Precision: 19, RoundingMode: "HALF_UP"},
			},
			Request: Request{
				TimeZone:                         "Asia/Ulaanbaatar",
				Currency:                         Currency{Code: "MNT", MinorUnitDigits: 2},
				Rounding:                         Rounding{SignificantDigits: 12, RateFactorScale: 12, Mode: "HALF_UP"},
				ScheduleStartDate:                Date{2024, 1, 1},
				Disbursements:                    []Disbursement{{Date: Date{2024, 1, 1}, AmountMinor: "10000"}},
				NumberOfRepayments:               6,
				RepaymentEvery:                   1,
				RepaymentFrequencyUnit:           "MONTHS",
				AnnualNominalInterestRate:        Rate{Numerator: 7, Denominator: 100},
				InterestMethod:                   "DECLINING_BALANCE",
				DayCount:                         "FIXED_30_360",
				DownPaymentPercentage:            Rate{Numerator: 0, Denominator: 1},
				InstallmentRoundingMultipleMinor: "0",
			},
			Expect: Expect{
				Kind: "schedule",
				Periods: []ExpectPeriod{{
					Kind: "REPAYMENT", InstallmentNumber: 1,
					FromDate: Date{2024, 1, 1}, DueDate: Date{2024, 2, 1},
					PrincipalMinor: "1643", InterestMinor: "58", OutstandingPrincipalMinor: "8357",
				}},
			},
			Path: filepath.Join("loanschedule", "FAKE-PROBE-AS-PARITY.json"),
		}
	}

	problems := Admit(base(), pin, root)
	if len(problems) == 0 {
		t.Fatal("a precision-12 capture was admitted as a parity vector; the probe guard is not working")
	}
	if !containsSubstring(problems, "DISCRIMINATION PROBE") {
		t.Errorf("the refusal must name the reason, got %v", problems)
	}
	if !containsSubstring(problems, "never-promotable") {
		t.Errorf("the never-promotable denylist must also catch capture case D-01, got %v", problems)
	}

	// The same vector at production settings, still hand-authored, is caught by
	// the capture reference instead: a parity vector must point at a real capture
	// artefact and name the case inside it.
	v := base()
	v.Oracle.ThreadedMathContext = MathContext{Precision: 19, RoundingMode: "HALF_UP"}
	v.Request.Rounding = Rounding{SignificantDigits: 19, RateFactorScale: 19, Mode: "HALF_UP"}
	v.Provenance.CaptureRef = ".softhouse/capture/does-not-exist.json"
	v.Provenance.CaptureCaseID = "MADE-UP"
	problems = Admit(v, pin, root)
	if !containsSubstring(problems, "does not resolve to a file") {
		t.Errorf("a parity vector citing a non-existent capture must be inadmissible, got %v", problems)
	}
}

// TestGradeabilityIsNotPairDifference covers the schema change forced by finding
// T55-N1.
//
// The intuitive test for whether a vector grades a behaviour — two captures
// differing only in that setting differ in some money cell — is FALSE. LB-DEC31
// reports ZERO cells differing across the day-count setting (22014.25 observed on
// products p3, p4 and p7 alike) and yet that value can only be produced by the
// ACT/ACT per-year arm: the 31-December boundary gives the 2024 segment zero days,
// so the ARM computes 0/366 + 31/365 = 22014.25 while the PLAIN branch computes
// 31/366 = 21954.10 — a margin of 6,015 minor units. A promotion rule that kept
// only non-zero-pair shapes would have discarded the three best graders in T55's
// set.
//
// So the store models gradeability as NAMED COUNTERFACTUALS with margins, and this
// test proves the rules around that field hold.
func TestGradeabilityIsNotPairDifference(t *testing.T) {
	root := repoRoot(t)
	store := storeRoot(t)
	pin, err := LoadPin(filepath.Join(store, "PIN.json"))
	if err != nil {
		t.Fatalf("LoadPin: %v", err)
	}
	registry, err := LoadCapabilityRegistry(filepath.Join(store, "capabilities.json"))
	if err != nil {
		t.Fatalf("LoadCapabilityRegistry: %v", err)
	}

	// A parity vector with no named counterfactual is a capture, not a grader.
	v := parityShell(pin)
	problems := Admit(v, pin, root)
	if !containsSubstring(problems, "at least one graded_against entry") {
		t.Errorf("a parity vector naming no counterfactual must be inadmissible, got %v", problems)
	}

	// A zero margin is not a kill.
	v = parityShell(pin)
	v.GradedAgainst = []Counterfactual{{
		ID: "ZERO-MARGIN", Capability: "schedule.core",
		Description: "d", Evidence: "e", MarginMinor: "0",
	}}
	problems = Admit(v, pin, root)
	if !containsSubstring(problems, "does NOT kill") {
		t.Errorf("a zero-margin counterfactual must be inadmissible, got %v", problems)
	}

	// A counterfactual may not grade a capability the vector does not claim.
	v = parityShell(pin)
	v.GradedAgainst = []Counterfactual{{
		ID: "OFF-PISTE", Capability: "daycount.actual.actual",
		Description: "d", Evidence: "e", MarginMinor: "6015",
	}}
	problems = Admit(v, pin, root)
	if !containsSubstring(problems, "not in capabilities_required") {
		t.Errorf("a counterfactual outside capabilities_required must be inadmissible, got %v", problems)
	}

	// A well-formed one is accepted, and it covers its capability.
	v = parityShell(pin)
	v.GradedAgainst = []Counterfactual{{
		ID:         "TEXTBOOK-BALANCE-TIMES-RATEFACTOR",
		Capability: "schedule.core",
		Description: "computes interest as balance * rateFactor instead of the oracle's three separately " +
			"rounded operations",
		Evidence:    "contract.go Period.InterestMinor; DEC-1 section 8 item 3b",
		MarginMinor: "1",
	}}
	if problems := Admit(v, pin, root); len(problems) > 0 {
		t.Errorf("a well-formed counterfactual must be admissible, got %v", problems)
	}
	covered, _ := registry.CounterfactualCoverage([]*Vector{v})
	if len(covered["schedule.core"]) != 1 {
		t.Errorf("schedule.core should be covered by one counterfactual, got %v", covered["schedule.core"])
	}

	// THE PROPERTY, NOT THE STORE'S STATE ON ONE DAY.
	//
	// This used to assert "the real store has no parity vector, so every graded
	// capability must be reported unbacked" — true when written, false the moment
	// a promotion lands, and the same defect class as D-6. What it protects is
	// that a capability is reported UNBACKED exactly when no admissible parity
	// vector names a counterfactual for it, so that is what is asserted, and it
	// keeps holding as the store fills up.
	vectors, _, err := LoadStore(store, "")
	if err != nil {
		t.Fatalf("LoadStore: %v", err)
	}
	covered, uncovered := registry.CounterfactualCoverage(vectors)
	unbacked := map[string]bool{}
	for _, name := range uncovered {
		unbacked[name] = true
	}
	for _, name := range registry.GradedCapabilities() {
		switch {
		case len(covered[name]) == 0 && !unbacked[name]:
			t.Errorf("capability %q is in_graded_domain, no parity vector names a counterfactual for it, "+
				"and yet it is not reported unbacked — that is a graded claim with nothing behind it", name)
		case len(covered[name]) > 0 && unbacked[name]:
			t.Errorf("capability %q is killed by %v and is still reported unbacked", name, covered[name])
		}
	}
	t.Logf("graded capabilities backed by %d counterfactual claims; unbacked: %v", len(covered), uncovered)

	// And the unbacked path must actually be able to fire: over an empty vector
	// set, every graded capability is unbacked. Without this, "nothing unbacked"
	// could mean "the check examines nothing".
	_, allUnbacked := registry.CounterfactualCoverage(nil)
	if len(allUnbacked) != len(registry.GradedCapabilities()) {
		t.Errorf("over an empty vector set every graded capability must be unbacked: got %v, want all of %v",
			allUnbacked, registry.GradedCapabilities())
	}
}

// TestStaleRefusalVectorIsDetected proves that admitting a capability retires the
// refusal vector that asserted it was ungraded — automatically, from registry data,
// with no capability hard-coded anywhere in the harness.
func TestStaleRefusalVectorIsDetected(t *testing.T) {
	root := repoRoot(t)
	store := storeRoot(t)

	// Copy the store and flip daycount.actual.actual into the graded domain, as a
	// later promotion task legitimately will.
	widened := copyStore(t, store)
	perturb(t, filepath.Join(widened, "capabilities.json"),
		`"name": "daycount.actual.actual",
      "description": "The ACT/ACT arm: real calendar year lengths, and the per-calendar-year fraction accumulation used where an interest sub-period crosses a year boundary.",
      "in_graded_domain": false`,
		`"name": "daycount.actual.actual",
      "description": "The ACT/ACT arm: real calendar year lengths, and the per-calendar-year fraction accumulation used where an interest sub-period crosses a year boundary.",
      "in_graded_domain": true`)

	impl, _, err := NewReplayImplementation(store, "")
	if err != nil {
		t.Fatalf("NewReplayImplementation: %v", err)
	}
	s := mustRun(t, Options{
		RepoRoot: root, StoreRoot: widened,
		Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
	})
	var found bool
	for _, r := range s.Results {
		if r.CaseID != "REFUSE-01-actual-actual-ungraded" {
			continue
		}
		found = true
		if r.Outcome != OutcomeInadmissible {
			t.Errorf("REFUSE-01 outcome %s, want %s once its capability is graded", r.Outcome, OutcomeInadmissible)
		}
		if !containsSubstring(r.Detail, "STALE REFUSAL VECTOR") {
			t.Errorf("the report must say the vector is stale and must be retired, got %v", r.Detail)
		}
		if !containsSubstring(r.Detail, "not a defect in any implementation") {
			t.Errorf("the report must say this is not an implementation defect, got %v", r.Detail)
		}
	}
	if !found {
		t.Fatal("REFUSE-01 was not graded at all")
	}
	if got := s.ExitCode(); got == 0 {
		t.Errorf("a stale refusal vector must not be exit 0, got %d", got)
	}
}

// parityShell builds a minimal admissible parity vector pointing at a real capture
// artefact, for tests that vary one thing about it.
func parityShell(pin *Pin) *Vector {
	return &Vector{
		Schema:               VectorSchemaV1,
		CaseID:               "SHELL",
		Context:              "loanschedule",
		Class:                ClassParity,
		DEC1Revision:         pin.DEC1Revision,
		CapabilitiesRequired: []string{"schedule.core"},
		Provenance: Provenance{
			Kind:          ProvenanceOracleCapture,
			CaptureRef:    ".softhouse/capture/out/capture-prod3b-attestation.json",
			CaptureCaseID: "P-01",
		},
		Oracle: OracleStamp{
			FineractCommit:      pin.FineractCommit,
			Seam:                "path_a_embeddable",
			ThreadedMathContext: MathContext{Precision: 19, RoundingMode: "HALF_UP"},
			AmbientMathContext:  MathContext{Precision: 19, RoundingMode: "HALF_UP"},
		},
		Request: Request{
			TimeZone:                         "Asia/Ulaanbaatar",
			Currency:                         Currency{Code: "MNT", MinorUnitDigits: 2},
			Rounding:                         Rounding{SignificantDigits: 19, RateFactorScale: 19, Mode: "HALF_UP"},
			ScheduleStartDate:                Date{2024, 1, 1},
			Disbursements:                    []Disbursement{{Date: Date{2024, 1, 1}, AmountMinor: "10000"}},
			NumberOfRepayments:               1,
			RepaymentEvery:                   1,
			RepaymentFrequencyUnit:           "MONTHS",
			AnnualNominalInterestRate:        Rate{Numerator: 7, Denominator: 100},
			InterestMethod:                   "DECLINING_BALANCE",
			DayCount:                         "FIXED_30_360",
			DownPaymentPercentage:            Rate{Numerator: 0, Denominator: 1},
			InstallmentRoundingMultipleMinor: "0",
		},
		Expect: Expect{
			Kind: "schedule",
			Periods: []ExpectPeriod{{
				Kind: "REPAYMENT", InstallmentNumber: 1,
				FromDate: Date{2024, 1, 1}, DueDate: Date{2024, 2, 1},
				PrincipalMinor: "10000", InterestMinor: "58", OutstandingPrincipalMinor: "0",
			}},
		},
		Path: filepath.Join("loanschedule", "SHELL.json"),
	}
}

// TestSeamBlindnessRefuses proves the load-bearing property of the schema: a case
// that needs a capability its capture seam cannot see is REFUSED, not passed.
func TestSeamBlindnessRefuses(t *testing.T) {
	store := storeRoot(t)
	registry, err := LoadCapabilityRegistry(filepath.Join(store, "capabilities.json"))
	if err != nil {
		t.Fatalf("LoadCapabilityRegistry: %v", err)
	}

	cases := []struct {
		name     string
		seam     string
		required []string
		want     RefusalReason
	}{
		{"charges on path A is seam-blind", "path_a_embeddable", []string{"schedule.core", "charges"}, ReasonSeamBlind},
		{"holidays on path A is seam-blind", "path_a_embeddable", []string{"holiday.adjustment"}, ReasonSeamBlind},
		{"working days on path A is seam-blind", "path_a_embeddable", []string{"workingday.adjustment"}, ReasonSeamBlind},
		{"installment multiple on path A is seam-blind", "path_a_embeddable",
			[]string{"installment.rounding.multiple"}, ReasonSeamBlind},
		{"holidays on path B are only partial", "path_b_server", []string{"holiday.adjustment"}, ReasonSeamBlind},
		{"charges on path B are exercised but ungraded", "path_b_server",
			[]string{"charges"}, ReasonUngradedCapability},
		{"ACT/ACT is exercised by path A but ungraded", "path_a_embeddable",
			[]string{"daycount.actual.actual"}, ReasonUngradedCapability},
		{"an unaudited capability on path A2 defaults to deny", "path_a2_reflective",
			[]string{"monthend.reanchor"}, ReasonUnknownCapability},
		{"an unknown seam refuses", "path_z_imaginary", []string{"schedule.core"}, ReasonUnknownSeam},
		{"an unknown capability refuses", "path_a_embeddable", []string{"telepathy"}, ReasonUnknownCapability},
		{"no declared capability refuses", "path_a_embeddable", nil, ReasonUnknownCapability},
		{"core on path A grades", "path_a_embeddable", []string{"schedule.core", "monthend.reanchor"}, ReasonNone},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := registry.Assess(c.seam, c.required)
			if got.Reason != c.want {
				t.Errorf("Assess(%q, %v) reason %q, want %q (detail: %v)",
					c.seam, c.required, got.Reason, c.want, got.Detail)
			}
			if (c.want == ReasonNone) != got.Gradeable {
				t.Errorf("Gradeable=%v with reason %q", got.Gradeable, got.Reason)
			}
		})
	}
}

// TestFloatTokensAreRejected proves the float guard rejects a decimal number
// anywhere in a vector document, including in a field a typed decode would drop.
func TestFloatTokensAreRejected(t *testing.T) {
	cases := []struct {
		name string
		doc  string
		want bool
	}{
		{"integers pass", `{"a":1,"b":-20,"c":[3,4],"d":{"e":0}}`, false},
		{"a decimal anywhere fails", `{"a":1,"b":21.6}`, true},
		{"exponent notation fails", `{"a":1e3}`, true},
		{"negative decimal fails", `{"periods":[{"interest":-0.01}]}`, true},
		{"a decimal in an unmodelled field still fails", `{"nonsense":{"deep":[{"x":1.5}]}}`, true},
		{"a decimal inside a string is fine", `{"principal_major_text":"112082.37"}`, false},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			err := RejectFloatTokens([]byte(c.doc))
			if (err != nil) != c.want {
				t.Fatalf("RejectFloatTokens(%s) error = %v, want error = %v", c.doc, err, c.want)
			}
		})
	}
}

// TestMinorTextIsExact covers the money parsing and the transcription cross-check.
func TestMinorTextIsExact(t *testing.T) {
	t.Run("canonical integer strings", func(t *testing.T) {
		cases := []struct {
			in   MinorText
			want int64
			ok   bool
		}{
			{"0", 0, true},
			{"100000", 100000, true},
			{"-1", -1, true},
			{"8765432100", 8765432100, true},
			{"", 0, false},
			{"007", 0, false},
			{"+7", 0, false},
			{"1.0", 0, false},
			{"1e3", 0, false},
			{"1 000", 0, false},
		}
		for _, c := range cases {
			got, err := c.in.Int64()
			if (err == nil) != c.ok {
				t.Errorf("MinorText(%q).Int64() error = %v, want ok = %v", c.in, err, c.ok)
				continue
			}
			if c.ok && got != c.want {
				t.Errorf("MinorText(%q).Int64() = %d, want %d", c.in, got, c.want)
			}
		}
	})

	t.Run("major wire text converts exactly", func(t *testing.T) {
		cases := []struct {
			text   string
			digits int32
			want   int64
			ok     bool
		}{
			{"112082.37", 2, 11208237, true},
			{"1200000.00", 2, 120000000, true},
			{"0.00", 2, 0, true},
			{"0", 2, 0, true},
			{"100.5", 2, 10050, true},
			{"14814.000000", 2, 1481400, true}, // scale 6 with only zeros beyond scale 2
			{"1200000.000000", 2, 120000000, true},
			{"112082.375", 2, 0, false}, // a significant digit beyond the currency scale
			{".50", 2, 0, false},
			{"1,200.00", 2, 0, false},
			{"", 2, 0, false},
		}
		for _, c := range cases {
			got, err := MinorFromMajorText(c.text, c.digits)
			if (err == nil) != c.ok {
				t.Errorf("MinorFromMajorText(%q, %d) error = %v, want ok = %v", c.text, c.digits, err, c.ok)
				continue
			}
			if c.ok && got != c.want {
				t.Errorf("MinorFromMajorText(%q, %d) = %d, want %d", c.text, c.digits, got, c.want)
			}
		}
	})
}

// TestNoFloatInTheLoanScheduleTree is the no-float guard, run as a test so it
// cannot be forgotten.
//
// It scans the Go TOKEN STREAM and inspects only identifiers, deliberately, rather
// than grepping the file's bytes. A byte grep reports the frozen contract.go on
// every run, because its doc comments NAME the forbidden types in order to forbid
// them — "There is no float32, float64, big.Float, decimal string or float-backed
// decimal type in this package". A guard that fires on the sentence prohibiting
// the thing is a guard somebody will switch off, and switching this one off would
// remove the check that matters most in the whole repository.
//
// Identifiers only also means this test file's own assembled token strings are
// string literals rather than identifiers, so there is no exemption list to rot.
// And it proves the ABSENCE of known-bad patterns and nothing more: .softhouse/
// patterns.md is explicit that a grep-based HARD check never proves correctness.
func TestNoFloatInTheLoanScheduleTree(t *testing.T) {
	root := filepath.Join(repoRoot(t), "nexus", "internal", "apps", "loanschedule")
	forbidden := map[string]bool{
		"float" + "32": true, "float" + "64": true,
		"complex" + "64": true, "complex" + "128": true,
		"Float": true, "Float" + "32": true, "Float" + "64": true,
		"Parse" + "Float": true, "Format" + "Float": true, "Append" + "Float": true,
		"Decimal": true,
	}
	scanned := 0
	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.IsDir() || !strings.HasSuffix(path, ".go") {
			return nil
		}
		raw, rerr := os.ReadFile(path)
		if rerr != nil {
			return rerr
		}
		scanned++
		fset := token.NewFileSet()
		file := fset.AddFile(path, -1, len(raw))
		var sc scanner.Scanner
		sc.Init(file, raw, func(pos token.Position, msg string) {
			t.Errorf("%s: scan error: %s", pos, msg)
		}, 0) // mode 0: comments are skipped entirely
		for {
			pos, tok, lit := sc.Scan()
			if tok == token.EOF {
				break
			}
			if tok != token.IDENT || !forbidden[lit] {
				continue
			}
			t.Errorf("%s: identifier %q: no floating-point type may appear on a money path, "+
				"including for intermediate calculation", fset.Position(pos), lit)
		}
		return nil
	})
	if err != nil {
		t.Fatalf("walking %s: %v", root, err)
	}
	if scanned == 0 {
		t.Fatalf("scanned no Go files under %s: a guard that inspects nothing passes everything", root)
	}
	t.Logf("scanned %d Go files under %s for floating-point identifiers", scanned, root)
}

// parityPassViolations returns one line per parity PASS the run has not earned.
//
// "Earned" is the whole content of a conformance claim, and it is four things at
// once: something was registered to grade; the case that passed is a vector of
// class PARITY; that vector's expectation was OBSERVED FROM THE ORACLE rather
// than hand-authored or derived from the contract; and it names the capture it
// came from. Anything else counted into ParityPass would be the harness awarding
// itself credit.
func parityPassViolations(s *Summary, byCase map[string]*Vector) []string {
	var out []string
	counted := 0
	for _, r := range s.Results {
		if r.Outcome != OutcomePass || r.Class != ClassParity {
			continue
		}
		counted++
		if s.ImplementationName == "" || s.ImplementationName == "(none)" {
			out = append(out, r.CaseID+": counted as a parity PASS with no implementation registered")
		}
		v, ok := byCase[r.CaseID]
		if !ok {
			out = append(out, r.CaseID+": counted as a parity PASS but no such vector is in the store")
			continue
		}
		if v.Class != ClassParity {
			out = append(out, r.CaseID+": counted as a parity PASS but the vector's class is "+string(v.Class))
		}
		if v.Provenance.Kind != ProvenanceOracleCapture {
			out = append(out, r.CaseID+": counted as a parity PASS but its provenance is "+
				string(v.Provenance.Kind)+", not an oracle capture")
		}
		if v.Provenance.CaptureRef == "" || v.Provenance.CaptureCaseID == "" {
			out = append(out, r.CaseID+": counted as a parity PASS but it names no capture artefact or case")
		}
		if v.Oracle.Seam == "" || v.Oracle.Seam == "none" {
			out = append(out, r.CaseID+": counted as a parity PASS but it names no capture seam")
		}
	}
	if counted != s.ParityPass {
		out = append(out, "ParityPass says "+fmt.Sprint(s.ParityPass)+
			" but the results carry "+fmt.Sprint(counted)+" passing parity vectors")
	}
	return out
}

func mustRun(t *testing.T, opts Options) *Summary {
	t.Helper()
	s, err := Run(context.Background(), opts)
	if err != nil {
		t.Fatalf("Run: %v", err)
	}
	return s
}

func render(s *Summary) string {
	var buf bytes.Buffer
	WriteReport(&buf, s)
	return buf.String()
}

func containsSubstring(haystack []string, needle string) bool {
	for _, h := range haystack {
		if strings.Contains(h, needle) {
			return true
		}
	}
	return false
}

func copyStore(t *testing.T, src string) string {
	t.Helper()
	dst := t.TempDir()
	entries, err := os.ReadDir(src)
	if err != nil {
		t.Fatalf("ReadDir %s: %v", src, err)
	}
	for _, e := range entries {
		from := filepath.Join(src, e.Name())
		to := filepath.Join(dst, e.Name())
		if !e.IsDir() {
			copyFile(t, from, to)
			continue
		}
		if err := os.MkdirAll(to, 0o755); err != nil {
			t.Fatalf("MkdirAll: %v", err)
		}
		sub, serr := os.ReadDir(from)
		if serr != nil {
			t.Fatalf("ReadDir %s: %v", from, serr)
		}
		for _, f := range sub {
			if f.IsDir() {
				continue
			}
			copyFile(t, filepath.Join(from, f.Name()), filepath.Join(to, f.Name()))
		}
	}
	return dst
}

func copyFile(t *testing.T, from, to string) {
	t.Helper()
	raw, err := os.ReadFile(from)
	if err != nil {
		t.Fatalf("ReadFile %s: %v", from, err)
	}
	if err := os.MkdirAll(filepath.Dir(to), 0o755); err != nil {
		t.Fatalf("MkdirAll: %v", err)
	}
	if err := os.WriteFile(to, raw, 0o644); err != nil {
		t.Fatalf("WriteFile %s: %v", to, err)
	}
}

func perturb(t *testing.T, path, from, to string) {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile %s: %v", path, err)
	}
	if !bytes.Contains(raw, []byte(from)) {
		t.Fatalf("%s does not contain %q, so the perturbation would be a no-op and the proof vacuous",
			path, from)
	}
	out := bytes.Replace(raw, []byte(from), []byte(to), 1)
	if err := os.WriteFile(path, out, 0o644); err != nil {
		t.Fatalf("WriteFile %s: %v", path, err)
	}
}
