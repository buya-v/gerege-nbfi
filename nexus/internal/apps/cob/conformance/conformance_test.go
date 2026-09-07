package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its step name and order are
// transcribed from the committed cob captures but it is never written to the
// store. It exists only so the harness machinery can be exercised without
// touching the store.

const probeCommit = "426a23544e8426a38ae43ae404670a0a7e85b9eb"

// moduleRoot walks up from the test package to the go.mod directory (nexus/).
func moduleRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("could not locate go.mod")
		}
		dir = parent
	}
}

// repoRoot is the directory that contains the nexus/ module.
func repoRoot(t *testing.T) string {
	return filepath.Dir(moduleRoot(t))
}

// stepProbe builds a valid cob step-order vector transcribed from the committed
// jobs-LOAN_CLOSE_OF_BUSINESS-steps-raw.json capture.
func stepProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-apply-charge",
		Title:   "probe apply charge to overdue loans order",
		Class:   ClassParity,
		Context: COBContext,
		Note:    "probe: transcribed from jobs-LOAN_CLOSE_OF_BUSINESS-steps-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamCOBBusinessStepOrder, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from jobs-LOAN_CLOSE_OF_BUSINESS-steps-raw.json",
			CaptureRef:    ".softhouse/capture/cob/out/jobs-LOAN_CLOSE_OF_BUSINESS-steps-raw.json",
			CaptureSHA256: "3ee2a9f85c63b936f3bfdcdcae0087c035455fb697623a4f29416a3f02ad3d8b",
			CaptureCaseID: "APPLY_CHARGE_TO_OVERDUE_LOANS",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request:              Request{StepName: "APPLY_CHARGE_TO_OVERDUE_LOANS"},
		Expect:               Expect{StepOrder: 1},
		CapabilitiesRequired: []string{"business-step-order"},
		GradedAgainst:        []string{"cob-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "cob-go",
	})
	if err != nil {
		t.Fatalf("Run: %v", err)
	}
	joined := strings.Join(s.FatalReasons, "\n")
	if !strings.Contains(joined, "ZERO VECTORS FOUND") {
		t.Fatalf("empty store should refuse with ZERO VECTORS FOUND, got: %s", joined)
	}
	if s.ParityPass != 0 {
		t.Fatalf("empty store parity pass = %d, want 0", s.ParityPass)
	}
	if got := s.ExitCode(); got != 2 {
		t.Fatalf("empty store exit code = %d, want 2", got)
	}
}

func TestNoFloatInTheCobTree(t *testing.T) {
	census, err := ScanGoTreeForFloatingPoint(moduleRoot(t))
	if err != nil {
		t.Fatalf("no-float census: %v", err)
	}
	if len(census.Violations()) > 0 {
		t.Fatalf("floating point found in the guarded tree: %v", census.Violations())
	}
	if census.PackagesScanned == 0 || census.FilesScanned == 0 {
		t.Fatalf("no-float census scanned nothing (packages=%d files=%d): a guard that inspects nothing is an error",
			census.PackagesScanned, census.FilesScanned)
	}
}

func TestWrongImplementationRunsRed(t *testing.T) {
	v := stepProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}

	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrongImpl, ok := Lookup("cob-wrong-shift-order")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("cob-wrong-shift-order"); !bad {
		t.Fatal("wrong implementation not marked wrong")
	}

	red := gradeOne(v, Options{Implementation: wrongImpl})
	if red.Outcome != OutcomeFail {
		t.Fatalf("wrong impl outcome = %s, want FAIL", red.Outcome)
	}
	if len(red.Diffs) == 0 {
		t.Fatal("wrong impl produced no diffs")
	}
}

func TestUnknownStepErrs(t *testing.T) {
	v := stepProbe()
	v.Request.StepName = "NOT_A_REAL_STEP"
	got, err := NewGoEvaluator().Evaluate(v.Request)
	if err == nil {
		t.Fatalf("unknown step should error, got %+v", got)
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"business-step-order": {Name: "business-step-order", InGradedDomain: true, Evidence: "jobs-LOAN_CLOSE_OF_BUSINESS-steps-raw.json"},
		},
		bySeam: map[string]Seam{
			SeamCOBBusinessStepOrder: {Name: SeamCOBBusinessStepOrder, Status: map[string]SeamStatus{
				"business-step-order": StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamCOBBusinessStepOrder, []string{"business-step-order"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"business-step-order"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamCOBBusinessStepOrder, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := stepProbe()

	badSchema := *base
	badSchema.Schema = "gerege.cob.vector/v2"
	if p := Admit(&badSchema, Options{}); len(p) == 0 {
		t.Fatal("wrong schema admitted")
	}

	badContext := *base
	badContext.Context = "ledger"
	if p := Admit(&badContext, Options{}); len(p) == 0 {
		t.Fatal("wrong context admitted")
	}

	noNote := *base
	noNote.Note = ""
	if p := Admit(&noNote, Options{}); len(p) == 0 {
		t.Fatal("missing _note admitted")
	}

	noGraded := *base
	noGraded.GradedAgainst = nil
	if p := Admit(&noGraded, Options{}); len(p) == 0 {
		t.Fatal("empty graded_against admitted")
	}

	unknownGraded := *base
	unknownGraded.GradedAgainst = []string{"not-registered"}
	if p := Admit(&unknownGraded, Options{}); len(p) == 0 {
		t.Fatal("unknown graded_against admitted")
	}

	badKind := *base
	badKind.Provenance.Kind = "computed"
	if p := Admit(&badKind, Options{}); len(p) == 0 {
		t.Fatal("non-oracle-capture provenance.kind admitted")
	}

	noTenant := *base
	noTenant.TenantParams = nil
	if p := Admit(&noTenant, Options{}); len(p) == 0 {
		t.Fatal("missing tenant_params admitted")
	}

	zeroOrder := *base
	zeroOrder.Expect.StepOrder = 0
	if p := Admit(&zeroOrder, Options{}); len(p) == 0 {
		t.Fatal("non-positive step_order admitted")
	}

	emptyStep := *base
	emptyStep.Request.StepName = ""
	if p := Admit(&emptyStep, Options{}); len(p) == 0 {
		t.Fatal("empty step_name admitted")
	}
}

func TestInvariants(t *testing.T) {
	v := &Vector{Oracle: OracleStamp{Seam: SeamCOBBusinessStepOrder}}
	held := AssertInvariants(v, Expect{StepOrder: 1})
	for _, iv := range held {
		if iv.Status != InvariantHeld {
			t.Fatalf("invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
		if iv.Assertions != 1 {
			t.Fatalf("invariant %s assertions = %d, want 1", iv.Name, iv.Assertions)
		}
	}

	if invs := AssertInvariants(v, Expect{StepOrder: 0}); invs[0].Status != InvariantViolated {
		t.Fatalf("step_order_positive = %s, want VIOLATED", invs[0].Status)
	}
}
