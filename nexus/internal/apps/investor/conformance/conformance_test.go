package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its numbers are transcribed from
// the committed investor captures but it is never written to the store. It
// exists only so the harness machinery can be exercised without touching the
// store.

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

func tenantParams() *TenantParams {
	return &TenantParams{
		RoundingMode:    "HALF_UP",
		RoundingOrdinal: 4,
		Precision:       19,
		Currency:        "MNT",
		MinorUnits:      2,
		Timezone:        "Asia/Ulaanbaatar",
	}
}

// rowProbe builds a valid row-seam vector transcribed from the committed
// transfer-read-loan-6-raw.json capture; with an empty RepoRoot the provenance
// file check is skipped.
func rowProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-transfer-read",
		Title:   "probe transfer read (loan 6)",
		Class:   ClassParity,
		Context: InvestorContext,
		Note:    "probe: transcribed from transfer-read-loan-6-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamExternalAssetOwnerTransferRead, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from transfer-read-loan-6-raw.json",
			CaptureRef:    ".softhouse/capture/investor/out/transfer-read-loan-6-raw.json",
			CaptureSHA256: "33c360bda77742b018a5bf35b278e28796f13a356ac948a99ffad1f2f90e4e8c",
			CaptureCaseID: "SEED-Tr-01",
		},
		TenantParams: tenantParams(),
		Request:      Request{LoanID: 6},
		Expect: Expect{
			TransferID:         1,
			OwnerExternalID:    "SEED-Inv-01",
			LoanExternalID:     "SEED-L06",
			TransferExternalID: "SEED-Tr-01",
			PurchasePriceRatio: "97.25",
			Status:             "PENDING",
			SettlementDate:     "2026-09-01",
			EffectiveFrom:      "2026-09-01",
			EffectiveTo:        "9999-12-31",
		},
		CapabilitiesRequired: []string{"transfer-read"},
		GradedAgainst:        []string{"investor-go"},
	}
}

// emptyProbe builds the mirror image: a vector whose expectation is the EMPTY
// page the oracle returned for loan 1 (transfer-read-loan-1-raw.json).
func emptyProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-transfer-read-empty",
		Title:   "probe transfer read (loan 1 - no transfer)",
		Class:   ClassParity,
		Context: InvestorContext,
		Note:    "probe: transcribed from transfer-read-loan-1-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamExternalAssetOwnerTransferRead, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from transfer-read-loan-1-raw.json",
			CaptureRef:    ".softhouse/capture/investor/out/transfer-read-loan-1-raw.json",
			CaptureSHA256: "11525a84bc4a9934f600e1b2d3579069539f6dd890dea99cf246d469b8b742ca",
			CaptureCaseID: "\"totalElements\":0",
		},
		TenantParams:         tenantParams(),
		Request:              Request{LoanID: 1},
		Expect:               Expect{Empty: true},
		CapabilitiesRequired: []string{"transfer-read"},
		GradedAgainst:        []string{"investor-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "investor-go",
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

func TestNoFloatInTheInvestorTree(t *testing.T) {
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

func TestRowVectorGradesGreenOnCorrectImpl(t *testing.T) {
	v := rowProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("row probe should be admissible: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl row outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	if correct.GradedCells != 9 {
		t.Fatalf("row vector graded cells = %d, want 9", correct.GradedCells)
	}
}

func TestEmptyVectorGradesGreenOnCorrectImpl(t *testing.T) {
	v := emptyProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("empty probe should be admissible: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl empty outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	if correct.GradedCells != 1 {
		t.Fatalf("empty vector graded cells = %d, want 1", correct.GradedCells)
	}
}

func TestFabricatingWrongImplFailsOnlyTheEmptyVector(t *testing.T) {
	wrongImpl, ok := Lookup("investor-wrong-fabricates-transfer")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("investor-wrong-fabricates-transfer"); !bad {
		t.Fatal("wrong implementation not marked wrong")
	}
	// Loan 6 still grades green: the fabrication returns the very row the oracle
	// returned for loan 6.
	if red := gradeOne(rowProbe(), Options{Implementation: wrongImpl}); red.Outcome != OutcomePass {
		t.Fatalf("fabricating impl row outcome = %s, want PASS (fabrication is invisible on loan 6); diffs=%v", red.Outcome, red.Diffs)
	}
	// Loan 1 goes red: the fabrication answers the empty page with a transfer.
	red := gradeOne(emptyProbe(), Options{Implementation: wrongImpl})
	if red.Outcome != OutcomeFail {
		t.Fatalf("fabricating impl empty outcome = %s, want FAIL; diffs=%v", red.Outcome, red.Diffs)
	}
	if len(red.Diffs) == 0 {
		t.Fatal("fabricating impl produced no diffs")
	}
}

func TestBlankStatusWrongImplFailsOnlyTheRowVector(t *testing.T) {
	wrongImpl, _ := Lookup("investor-wrong-blank-status")
	if red := gradeOne(rowProbe(), Options{Implementation: wrongImpl}); red.Outcome != OutcomeFail {
		t.Fatalf("blank-status impl row outcome = %s, want FAIL", red.Outcome)
	}
	// An empty page has no status to blank: the wrong impl must not invent one.
	if red := gradeOne(emptyProbe(), Options{Implementation: wrongImpl}); red.Outcome != OutcomePass {
		t.Fatalf("blank-status impl empty outcome = %s, want PASS (no row to blank); diffs=%v", red.Outcome, red.Diffs)
	}
}

func TestInvariantsOnEmptyPageAreNotApplicable(t *testing.T) {
	inv := AssertInvariants(&Vector{}, Expect{Empty: true})
	if len(inv) != 4 {
		t.Fatalf("empty page invariants = %d, want 4", len(inv))
	}
	for _, iv := range inv {
		if iv.Status != InvariantNotApplicable {
			t.Fatalf("invariant %s on an empty page = %s, want N/A", iv.Name, iv.Status)
		}
		if iv.Assertions != 0 {
			t.Fatalf("invariant %s on an empty page assertions = %d, want 0", iv.Name, iv.Assertions)
		}
	}
}
