package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its numbers are transcribed from
// the committed collateral captures but it is never written to the store. It
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

// productProbe builds a valid product-seam vector. Its expect fields are a
// transcription of the committed collateral-product-readback-raw.json capture;
// with an empty RepoRoot the provenance file check is skipped.
func productProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-product-read",
		Title:   "probe product read",
		Class:   ClassParity,
		Context: CollateralContext,
		Note:    "probe: transcribed from collateral-product-readback-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamCollateralProductRead, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from collateral-product-readback-raw.json",
			CaptureRef:    ".softhouse/capture/collateral/out/collateral-product-readback-raw.json",
			CaptureSHA256: "812f55f434cbfa740e7f0f4aadbfadcfb4c5e5af6e3e07622023dd326ee541a0",
			CaptureCaseID: "SEED-Collateral-Product",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request: Request{ProductID: 2},
		Expect: Expect{
			ID:        2,
			Name:      "SEED-Collateral-Product",
			Quality:   "Good",
			UnitType:  "1",
			Currency:  "MNT",
			BasePrice: "10000000000",
			PctToBase: "5000000",
		},
		CapabilitiesRequired: []string{"product-aggregate-read"},
		GradedAgainst:        []string{"collateral-go"},
	}
}

// linkProbe builds a valid link-seam vector transcribed from the committed
// loan-collateral-readback-raw.json capture.
func linkProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-link-read",
		Title:   "probe link read",
		Class:   ClassParity,
		Context: CollateralContext,
		Note:    "probe: transcribed from loan-collateral-readback-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamCollateralLinkRead, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from loan-collateral-readback-raw.json",
			CaptureRef:    ".softhouse/capture/collateral/out/loan-collateral-readback-raw.json",
			CaptureSHA256: "d974b632789119080aab869792b4e2a16b60b5df37bd4dba88ed2c25b8b45f4f",
			CaptureCaseID: "SEED Collateral Type",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request:              Request{LinkID: 2},
		Expect:               Expect{ID: 2, TypeID: 24},
		CapabilitiesRequired: []string{"collateral-type-link"},
		GradedAgainst:        []string{"collateral-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "collateral-go",
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

func TestNoFloatInTheCollateralTree(t *testing.T) {
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
	v := productProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}

	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrongImpl, ok := Lookup("collateral-wrong-blank-quality")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("collateral-wrong-blank-quality"); !bad {
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

func TestLinkSeamGrading(t *testing.T) {
	v := linkProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("link probe should be admissible: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl link outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	wrongImpl, _ := Lookup("collateral-wrong-blank-quality")
	if red := gradeOne(v, Options{Implementation: wrongImpl}); red.Outcome != OutcomeFail {
		t.Fatalf("wrong impl link outcome = %s, want FAIL", red.Outcome)
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"product-aggregate-read": {Name: "product-aggregate-read", InGradedDomain: true, Evidence: "collateral-product-readback-raw.json"},
			"collateral-type-link":   {Name: "collateral-type-link", InGradedDomain: true, Evidence: "loan-collateral-readback-raw.json"},
			"collateral-valuation":   {Name: "collateral-valuation", InGradedDomain: false, Evidence: "no API read-back computes basePrice*pctToBase*quantity"},
		},
		bySeam: map[string]Seam{
			SeamCollateralProductRead: {Name: SeamCollateralProductRead, Status: map[string]SeamStatus{
				"product-aggregate-read": StatusExercised,
				"collateral-valuation":   StatusBlind,
			}},
			SeamCollateralLinkRead: {Name: SeamCollateralLinkRead, Status: map[string]SeamStatus{
				"collateral-type-link": StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamCollateralProductRead, []string{"product-aggregate-read"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"product-aggregate-read"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamCollateralProductRead, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamCollateralProductRead, []string{"nope"}); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("unknown capability should refuse with reason %q, got %q", reasonUnknownCapability, v.Reason)
	}
	if v := r.Assess(SeamCollateralProductRead, []string{"collateral-valuation"}); v.Gradeable || v.Reason != reasonSeamBlind {
		t.Fatalf("blind capability should refuse with reason %q, got %q", reasonSeamBlind, v.Reason)
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := productProbe()

	badSchema := *base
	badSchema.Schema = "gerege.collateral.vector/v2"
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

	zeroProduct := *base
	zeroProduct.Request.ProductID = 0
	if p := Admit(&zeroProduct, Options{}); len(p) == 0 {
		t.Fatal("non-positive product_id admitted")
	}

	productWithLink := *base
	productWithLink.Request.LinkID = 1
	if p := Admit(&productWithLink, Options{}); len(p) == 0 {
		t.Fatal("product seam with link_id admitted")
	}

	// The link seam is refused when the request is malformed in the mirror way.
	zeroLink := linkProbe()
	zeroLink.Request.LinkID = 0
	if p := Admit(zeroLink, Options{}); len(p) == 0 {
		t.Fatal("non-positive link_id admitted")
	}
}

func TestInvariants(t *testing.T) {
	product := &Vector{Oracle: OracleStamp{Seam: SeamCollateralProductRead}}
	held := AssertInvariants(product, Expect{ID: 2, Name: "SEED-Collateral-Product"})
	for _, iv := range held {
		if iv.Status != InvariantHeld {
			t.Fatalf("invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
		if iv.Assertions != 1 {
			t.Fatalf("invariant %s assertions = %d, want 1", iv.Name, iv.Assertions)
		}
	}

	if invs := AssertInvariants(product, Expect{ID: 0, Name: "SEED-Collateral-Product"}); invs[0].Status != InvariantViolated {
		t.Fatalf("product_id_positive = %s, want VIOLATED", invs[0].Status)
	}
	if invs := AssertInvariants(product, Expect{ID: 2, Name: ""}); invs[1].Status != InvariantViolated {
		t.Fatalf("product_name_non_empty = %s, want VIOLATED", invs[1].Status)
	}

	link := &Vector{Oracle: OracleStamp{Seam: SeamCollateralLinkRead}}
	if invs := AssertInvariants(link, Expect{ID: 0, TypeID: 24}); invs[0].Status != InvariantViolated {
		t.Fatalf("link_id_positive = %s, want VIOLATED", invs[0].Status)
	}
	if invs := AssertInvariants(link, Expect{ID: 2, TypeID: 0}); invs[1].Status != InvariantViolated {
		t.Fatalf("link_type_id_positive = %s, want VIOLATED", invs[1].Status)
	}
}
