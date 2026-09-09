package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its name and stored string are
// transcribed from the committed origination captures but it is never written to
// the store. It exists only so the harness machinery can be exercised without
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

// statusProbe builds a valid origination status vector transcribed from the
// committed loan-originators-template-raw.json capture.
func statusProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-active",
		Title:   "probe ACTIVE originator stored string",
		Class:   ClassParity,
		Context: OriginationContext,
		Note:    "probe: transcribed from loan-originators-template-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLoanOriginatorStatus, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from loan-originators-template-raw.json statusOptions",
			CaptureRef:    ".softhouse/capture/origination/out/loan-originators-template-raw.json",
			CaptureSHA256: "59d4a563dff477cd04a47b93d6a0153f59d03e4aadb14ae1ea417dee77928f22",
			CaptureCaseID: "ACTIVE",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request:              Request{Name: "ACTIVE"},
		Expect:               Expect{Stored: "ACTIVE"},
		CapabilitiesRequired: []string{"loan-originator-status"},
		GradedAgainst:        []string{"origination-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "origination-go",
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

func TestNoFloatInTheOriginationTree(t *testing.T) {
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
	v := statusProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}

	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrongImpl, ok := Lookup("origination-wrong-swap-status")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("origination-wrong-swap-status"); !bad {
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

func TestWrongDefaultActiveRunsRed(t *testing.T) {
	// The default-ACTIVE drive is the second shape guarding the one graded
	// cell: a CONSTANT transcription rather than the swap's permutation. It
	// must be red on exactly the vectors that assert PENDING or INACTIVE and
	// green on ACTIVE — a drive that killed ACTIVE too would be a blanket
	// rejection and indistinguishable from a broken implementation.
	wrongImpl, ok := Lookup("origination-wrong-default-active")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("origination-wrong-default-active"); !bad {
		t.Fatal("wrong implementation not marked wrong")
	}

	active := statusProbe()
	green := gradeOne(active, Options{Implementation: wrongImpl})
	if green.Outcome != OutcomePass {
		t.Fatalf("default-active impl on ACTIVE = %s, want PASS (the default is ACTIVE); diffs=%v", green.Outcome, green.Diffs)
	}

	pending := statusProbe()
	pending.Request.Name = "PENDING"
	pending.Provenance.CaptureCaseID = "PENDING"
	pending.Expect.Stored = "PENDING"
	red := gradeOne(pending, Options{Implementation: wrongImpl})
	if red.Outcome != OutcomeFail {
		t.Fatalf("default-active impl on PENDING = %s, want FAIL", red.Outcome)
	}
	if len(red.Diffs) == 0 {
		t.Fatal("default-active impl produced no diffs on PENDING")
	}

	inactive := statusProbe()
	inactive.Request.Name = "INACTIVE"
	inactive.Provenance.CaptureCaseID = "INACTIVE"
	inactive.Expect.Stored = "INACTIVE"
	redInactive := gradeOne(inactive, Options{Implementation: wrongImpl})
	if redInactive.Outcome != OutcomeFail {
		t.Fatalf("default-active impl on INACTIVE = %s, want FAIL", redInactive.Outcome)
	}
}

func TestUnknownStatusErrs(t *testing.T) {
	v := statusProbe()
	v.Request.Name = "NOT_A_REAL_STATUS"
	got, err := NewGoEvaluator().Evaluate(v.Request)
	if err == nil {
		t.Fatalf("unknown status should error, got %+v", got)
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"loan-originator-status": {Name: "loan-originator-status", InGradedDomain: true, Evidence: "loan-originators-template-raw.json"},
		},
		bySeam: map[string]Seam{
			SeamLoanOriginatorStatus: {Name: SeamLoanOriginatorStatus, Status: map[string]SeamStatus{
				"loan-originator-status": StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamLoanOriginatorStatus, []string{"loan-originator-status"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"loan-originator-status"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamLoanOriginatorStatus, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := statusProbe()

	badSchema := *base
	badSchema.Schema = "gerege.origination.vector/v2"
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

	emptyStored := *base
	emptyStored.Expect.Stored = ""
	if p := Admit(&emptyStored, Options{}); len(p) == 0 {
		t.Fatal("empty stored admitted")
	}

	emptyName := *base
	emptyName.Request.Name = ""
	if p := Admit(&emptyName, Options{}); len(p) == 0 {
		t.Fatal("empty name admitted")
	}
}

func TestInvariants(t *testing.T) {
	v := &Vector{Oracle: OracleStamp{Seam: SeamLoanOriginatorStatus}}
	held := AssertInvariants(v, Expect{Stored: "ACTIVE"})
	for _, iv := range held {
		if iv.Status != InvariantHeld {
			t.Fatalf("invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
		if iv.Assertions != 1 {
			t.Fatalf("invariant %s assertions = %d, want 1", iv.Name, iv.Assertions)
		}
	}

	if invs := AssertInvariants(v, Expect{Stored: "SOMETHING_ELSE"}); invs[0].Status != InvariantViolated {
		t.Fatalf("stored_in_vocabulary = %s, want VIOLATED", invs[0].Status)
	}
}
