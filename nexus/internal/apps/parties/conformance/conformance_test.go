package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its name and ordinal are
// transcribed from the committed parties captures but it is never written to the
// store. It exists only so the harness machinery can be exercised without
// touching the store.

const probeCommit = "426a23544e8426a38ae43ae404670a0a7e85b9eb"

const (
	probeClientStatusSHA   = "0ee9cdc5e038111173b64ad4583afb8040b10307393366cd33f3f3a70cee1a05"
	probeLegalFormSHA      = "9baf39c809179c3298d87a41237273329cc642d18b30c7304cf4713c6b3639ce"
	probeGroupingStatusSHA = "7a9e78dd84be0301b19406f0c159084f765f74eb29257202904008301b4235be"
	probeClientReadbackSHA = "d4d2877ffbcbbbca2d8d4cdb88b655a15fd98e0486a2933bf8df7fb01a68b2b4"
)

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

// probeTenant is the gerege tenant context every parties capture was taken under.
func probeTenant() *TenantParams {
	return &TenantParams{
		RoundingMode:    "HALF_UP",
		RoundingOrdinal: 4,
		Precision:       19,
		Currency:        "MNT",
		MinorUnits:      2,
		Timezone:        "Asia/Ulaanbaatar",
	}
}

// clientStatusProbe builds a valid client-status ACTIVE vector transcribed from
// the committed m-client-readback-raw.json capture.
func clientStatusProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-client-active",
		Title:   "probe client ACTIVE ordinal",
		Class:   ClassParity,
		Context: PartiesContext,
		Note:    "probe: transcribed from m-client-readback-raw.json status_enum, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamClientStatus, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from m-client-readback-raw.json row id=1 status_enum",
			CaptureRef:    ".softhouse/capture/parties/out/m-client-readback-raw.json",
			CaptureSHA256: probeClientReadbackSHA,
			CaptureCaseID: `"status_enum":300`,
			Citation:      "ClientStatus.java:28-35 — ACTIVE(300, \"clientStatusType.active\")",
		},
		TenantParams:        probeTenant(),
		Request:             Request{Vocabulary: string(VocabularyClientStatus), Name: "ACTIVE"},
		Expect:              Expect{Ordinal: 300},
		CapabilitiesRequired: []string{"client-status"},
		GradedAgainst:       []string{"parties-go"},
	}
}

func legalFormProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-legalform-person",
		Title:   "probe legal-form PERSON ordinal",
		Class:   ClassParity,
		Context: PartiesContext,
		Note:    "probe: transcribed from clients-template-raw.json clientLegalFormOptions id 1, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLegalForm, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from clients-template-raw.json clientLegalFormOptions id 1",
			CaptureRef:    ".softhouse/capture/parties/out/clients-template-raw.json",
			CaptureSHA256: probeLegalFormSHA,
			CaptureCaseID: "legalFormType.person",
			Citation:      "LegalForm.java:29-30 — PERSON(1, \"legalFormType.person\", \"Person\")",
		},
		TenantParams:        probeTenant(),
		Request:             Request{Vocabulary: string(VocabularyLegalForm), Name: "PERSON"},
		Expect:              Expect{Ordinal: 1},
		CapabilitiesRequired: []string{"legal-form"},
		GradedAgainst:       []string{"parties-go"},
	}
}

func groupingStatusProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-grouping-active",
		Title:   "probe grouping ACTIVE ordinal",
		Class:   ClassParity,
		Context: PartiesContext,
		Note:    "probe: transcribed from grouping-status-source.txt GroupingTypeStatus.java, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamGroupingStatus, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from grouping-status-source.txt (Java-source-only; m_group is empty)",
			CaptureRef:    ".softhouse/capture/parties/out/grouping-status-source.txt",
			CaptureSHA256: probeGroupingStatusSHA,
			CaptureCaseID: "ACTIVE",
			Citation:      "GroupingTypeStatus.java:26-31 — ACTIVE(300, \"groupingStatusType.active\")",
		},
		TenantParams:        probeTenant(),
		Request:             Request{Vocabulary: string(VocabularyGroupingStatus), Name: "ACTIVE"},
		Expect:              Expect{Ordinal: 300},
		CapabilitiesRequired: []string{"grouping-status"},
		GradedAgainst:       []string{"parties-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "parties-go",
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

func TestNoFloatInThePartiesTree(t *testing.T) {
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

func TestCorrectImplementationPassesAllThreeVocabularies(t *testing.T) {
	for _, probe := range []*Vector{clientStatusProbe(), legalFormProbe(), groupingStatusProbe()} {
		if p := Admit(probe, Options{}); len(p) > 0 {
			t.Fatalf("%s probe should be admissible: %v", probe.CaseID, p)
		}
		if got := gradeOne(probe, Options{Implementation: NewGoEvaluator()}); got.Outcome != OutcomePass {
			t.Fatalf("%s correct impl outcome = %s, want PASS; diffs=%v", probe.CaseID, got.Outcome, got.Diffs)
		}
	}
}

func TestWrongImplementationRunsRed(t *testing.T) {
	v := clientStatusProbe()

	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrongImpl, ok := Lookup("parties-wrong-swap-active-pending")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("parties-wrong-swap-active-pending"); !bad {
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

func TestUnknownNameErrs(t *testing.T) {
	for _, v := range []*Vector{clientStatusProbe(), legalFormProbe(), groupingStatusProbe()} {
		v.Request.Name = "NOT_A_REAL_MEMBER"
		got, err := NewGoEvaluator().Evaluate(v.Request)
		if err == nil {
			t.Fatalf("unknown name in %s should error, got %+v", v.Request.Vocabulary, got)
		}
	}
}

func TestUnknownVocabularyErrs(t *testing.T) {
	v := clientStatusProbe()
	v.Request.Vocabulary = "not-a-vocabulary"
	if _, err := NewGoEvaluator().Evaluate(v.Request); err == nil {
		t.Fatal("unknown vocabulary should error")
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"client-status":   {Name: "client-status", InGradedDomain: true, Evidence: "m-client-readback-raw.json"},
			"legal-form":      {Name: "legal-form", InGradedDomain: true, Evidence: "clients-template-raw.json"},
			"grouping-status": {Name: "grouping-status", InGradedDomain: true, Evidence: "grouping-status-source.txt"},
		},
		bySeam: map[string]Seam{
			SeamClientStatus: {Name: SeamClientStatus, Status: map[string]SeamStatus{
				"client-status": StatusExercised,
			}},
			SeamLegalForm: {Name: SeamLegalForm, Status: map[string]SeamStatus{
				"legal-form": StatusExercised,
			}},
			SeamGroupingStatus: {Name: SeamGroupingStatus, Status: map[string]SeamStatus{
				"grouping-status": StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamClientStatus, []string{"client-status"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"client-status"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamClientStatus, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
	// A capability not recorded on the seam refuses (default-deny).
	if v := r.Assess(SeamLegalForm, []string{"client-status"}); v.Gradeable {
		t.Fatalf("client-status on legal-form seam should refuse, got gradeable")
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := clientStatusProbe()

	badSchema := *base
	badSchema.Schema = "gerege.parties.vector/v2"
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

	badSeam := *base
	badSeam.Oracle.Seam = "cob-business-step-order"
	if p := Admit(&badSeam, Options{}); len(p) == 0 {
		t.Fatal("unknown seam admitted")
	}

	badVocab := *base
	badVocab.Request.Vocabulary = "not-a-vocabulary"
	if p := Admit(&badVocab, Options{}); len(p) == 0 {
		t.Fatal("unknown vocabulary admitted")
	}

	seamVocabMismatch := *base
	seamVocabMismatch.Oracle.Seam = SeamLegalForm
	if p := Admit(&seamVocabMismatch, Options{}); len(p) == 0 {
		t.Fatal("vocabulary/seam mismatch admitted")
	}

	emptyName := *base
	emptyName.Request.Name = ""
	if p := Admit(&emptyName, Options{}); len(p) == 0 {
		t.Fatal("empty name admitted")
	}

	negativeOrdinal := *base
	negativeOrdinal.Expect.Ordinal = -5
	if p := Admit(&negativeOrdinal, Options{}); len(p) == 0 {
		t.Fatal("negative ordinal admitted")
	}
}

func TestInvariants(t *testing.T) {
	v := clientStatusProbe()
	held := AssertInvariants(v, Expect{Ordinal: 300})
	for _, iv := range held {
		if iv.Status != InvariantHeld {
			t.Fatalf("invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
		if iv.Assertions != 1 {
			t.Fatalf("invariant %s assertions = %d, want 1", iv.Name, iv.Assertions)
		}
	}

	if invs := AssertInvariants(v, Expect{Ordinal: 299}); invs[0].Status != InvariantViolated {
		t.Fatalf("ordinal_in_vocabulary = %s, want VIOLATED", invs[0].Status)
	}
}
