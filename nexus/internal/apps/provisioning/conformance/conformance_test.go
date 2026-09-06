package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its numbers are transcribed from
// the committed CAT-00 capture but it is never written to the store. It exists
// only so the harness machinery can be exercised without touching the store.

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

// categoryProbe builds a valid STANDARD-category vector. Its expect fields are a
// transcription of the committed CAT-00 capture; with an empty RepoRoot the
// provenance file check is skipped, so the probe grades without the store.
func categoryProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-category-standard",
		Title:   "probe STANDARD category",
		Class:   ClassParity,
		Context: ProvisioningContext,
		Note:    "probe: transcribed from CAT-00, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamProvisioningCategoryRead, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from CAT-00",
			CaptureRef:    ".softhouse/capture/provisioning/out/CAT-00-categories-raw.json",
			CaptureSHA256: "b7c62862064d9b02e5506fb20b4d88e1449de20a62e54593fbdfcb6764eaf787",
			CaptureCaseID: "STANDARD",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request:              Request{CategoryID: 1},
		Expect:               Expect{ID: 1, Name: "STANDARD", Description: "Punctual Payment without any dues"},
		CapabilitiesRequired: []string{"category-aggregate"},
		GradedAgainst:        []string{"provisioning-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "provisioning-go",
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

func TestNoFloatInTheProvisioningTree(t *testing.T) {
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

func TestRejectFloatTokens(t *testing.T) {
	if err := RejectFloatTokens([]byte(`{"a": 1, "b": "2.5", "c": 3}`)); err != nil {
		t.Fatalf("integer document rejected: %v", err)
	}
	if err := RejectFloatTokens([]byte(`{"a": 1.5}`)); err == nil {
		t.Fatal("float document accepted")
	}
	if err := RejectFloatTokens([]byte(`{"a": 1e3}`)); err == nil {
		t.Fatal("exponent document accepted")
	}
}

func TestWrongImplementationRunsRed(t *testing.T) {
	v := categoryProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}

	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrongImpl, ok := Lookup("provisioning-wrong-blank-description")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("provisioning-wrong-blank-description"); !bad {
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

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"category-aggregate": {Name: "category-aggregate", InGradedDomain: true, Evidence: "CAT-00"},
			"reserve-amount":     {Name: "reserve-amount", InGradedDomain: false, Evidence: "no criteria captured"},
		},
		bySeam: map[string]Seam{
			SeamProvisioningCategoryRead: {Name: SeamProvisioningCategoryRead, Status: map[string]SeamStatus{
				"category-aggregate": StatusExercised,
				"reserve-amount":     StatusBlind,
			}},
		},
	}

	if v := r.Assess(SeamProvisioningCategoryRead, []string{"category-aggregate"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"category-aggregate"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamProvisioningCategoryRead, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamProvisioningCategoryRead, []string{"nope"}); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("unknown capability should refuse with reason %q, got %q", reasonUnknownCapability, v.Reason)
	}
	if v := r.Assess(SeamProvisioningCategoryRead, []string{"reserve-amount"}); v.Gradeable || v.Reason != reasonSeamBlind {
		t.Fatalf("blind capability should refuse with reason %q, got %q", reasonSeamBlind, v.Reason)
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := categoryProbe()

	badSchema := *base
	badSchema.Schema = "gerege.provisioning.vector/v2"
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

	zeroCategory := *base
	zeroCategory.Request.CategoryID = 0
	if p := Admit(&zeroCategory, Options{}); len(p) == 0 {
		t.Fatal("non-positive category_id admitted")
	}
}

func TestInvariants(t *testing.T) {
	held := AssertInvariants(nil, Expect{ID: 1, Name: "STANDARD", Description: "Punctual Payment without any dues"})
	for _, iv := range held {
		if iv.Status != InvariantHeld {
			t.Fatalf("invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
		if iv.Assertions != 1 {
			t.Fatalf("invariant %s assertions = %d, want 1", iv.Name, iv.Assertions)
		}
	}

	neg := AssertInvariants(nil, Expect{ID: 0, Name: "STANDARD"})
	if neg[0].Name != "category_id_positive" || neg[0].Status != InvariantViolated {
		t.Fatalf("category_id_positive = %s, want VIOLATED", neg[0].Status)
	}

	emptyName := AssertInvariants(nil, Expect{ID: 1, Name: ""})
	if emptyName[1].Name != "category_name_non_empty" || emptyName[1].Status != InvariantViolated {
		t.Fatalf("category_name_non_empty = %s, want VIOLATED", emptyName[1].Status)
	}
}
