package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its numbers are transcribed from
// the committed shares captures but it is never written to the store.

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

// accountProbe builds a valid share-account vector (account id 3, purchase
// 100 shares at 100.00 = 10000.00, no rounding surface).
func accountProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-account",
		Title:   "probe share account purchase readback",
		Class:   ClassParity,
		Context: SharesContext,
		Note:    "probe: transcribed from share-account-detail-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamShareAccount, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from share-account-detail-raw.json",
			CaptureRef:    ".softhouse/capture/shares/out/share-account-detail-raw.json",
			CaptureSHA256: "0000000000000000000000000000000000000000000000000000000000000000",
			CaptureCaseID: "3",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request: Request{
			Kind:                KindAccount,
			CurrencyCode:        "MNT",
			AccountStatusID:     300,
			TotalApprovedShares: 100,
			PurchasedShares:     100,
			PurchasedPrice:      "100.00",
			PurchasedAmount:     "10000.00",
			PurchasedStatusID:   300,
		},
		Expect: Expect{
			Kind:                  KindAccount,
			AccountStatusStored:   300,
			TotalApprovedShares:   100,
			PurchasedShares:       100,
			PurchasedPriceMinor:   "10000",
			PurchasedAmountMinor:  "1000000",
			PurchasedStatusStored: 300,
		},
		CapabilitiesRequired: []string{"share-account"},
		GradedAgainst:        []string{"shares-go"},
	}
}

// dividendProbe builds a valid share-dividend vector (dividend id 3, the
// HALF_UP read-back 0.010000 stored, normalised to one minor unit).
func dividendProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-dividend",
		Title:   "probe share-product dividend amount readback",
		Class:   ClassParity,
		Context: SharesContext,
		Note:    "probe: transcribed from shares-product-dividends-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamShareDividend, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from shares-product-dividends-raw.json",
			CaptureRef:    ".softhouse/capture/shares/out/shares-product-dividends-raw.json",
			CaptureSHA256: "0000000000000000000000000000000000000000000000000000000000000000",
			CaptureCaseID: "3",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request: Request{
			Kind:           KindDividend,
			CurrencyCode:   "MNT",
			DividendAmount: "0.010000",
		},
		Expect: Expect{
			Kind:                KindDividend,
			DividendAmountMinor: "1",
		},
		CapabilitiesRequired: []string{"share-dividend"},
		GradedAgainst:        []string{"shares-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "shares-go",
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

func TestNoFloatInTheSharesTree(t *testing.T) {
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
	for _, v := range []*Vector{accountProbe(), dividendProbe()} {
		if p := Admit(v, Options{}); len(p) > 0 {
			t.Fatalf("%s should be admissible: %v", v.CaseID, p)
		}

		correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
		if correct.Outcome != OutcomePass {
			t.Fatalf("%s correct impl outcome = %s, want PASS; diffs=%v", v.CaseID, correct.Outcome, correct.Diffs)
		}

		wrongImpl, ok := Lookup("shares-wrong-off-by-one")
		if !ok {
			t.Fatal("wrong implementation not registered")
		}
		if _, bad := IsRegisteredWrong("shares-wrong-off-by-one"); !bad {
			t.Fatal("wrong implementation not marked wrong")
		}

		red := gradeOne(v, Options{Implementation: wrongImpl})
		if red.Outcome != OutcomeFail {
			t.Fatalf("%s wrong impl outcome = %s, want FAIL", v.CaseID, red.Outcome)
		}
		if len(red.Diffs) == 0 {
			t.Fatalf("%s wrong impl produced no diffs", v.CaseID)
		}
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"share-account":  {Name: "share-account", InGradedDomain: true, Evidence: "share-account-detail"},
			"share-dividend": {Name: "share-dividend", InGradedDomain: true, Evidence: "shares-product-dividends"},
		},
		bySeam: map[string]Seam{
			SeamShareAccount: {Name: SeamShareAccount, Status: map[string]SeamStatus{
				"share-account": StatusExercised,
			}},
			SeamShareDividend: {Name: SeamShareDividend, Status: map[string]SeamStatus{
				"share-dividend": StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamShareAccount, []string{"share-account"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess(SeamShareDividend, []string{"share-dividend"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"share-account"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamShareAccount, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamShareAccount, []string{"nope"}); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("unknown capability should refuse with reason %q, got %q", reasonUnknownCapability, v.Reason)
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := accountProbe()

	badSchema := *base
	badSchema.Schema = "gerege.shares.vector/v2"
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

	unknownStatus := *base
	unknownStatus.Request.AccountStatusID = 0
	if p := Admit(&unknownStatus, Options{}); len(p) == 0 {
		t.Fatal("unknown account_status_id admitted")
	}

	fractional := *base
	fractional.Request.PurchasedAmount = "10000.005"
	if p := Admit(&fractional, Options{}); len(p) == 0 {
		t.Fatal("sub-minor-unit residue purchased_amount admitted")
	}

	kindMismatch := *base
	kindMismatch.Expect.Kind = KindDividend
	if p := Admit(&kindMismatch, Options{}); len(p) == 0 {
		t.Fatal("expect.kind / request.kind mismatch admitted")
	}
}

func TestInvariants(t *testing.T) {
	held := AssertInvariants(nil, Expect{
		Kind:                 KindAccount,
		PurchasedPriceMinor:  "10000",
		PurchasedAmountMinor: "1000000",
	})
	for _, iv := range held {
		if iv.Status != InvariantHeld {
			t.Fatalf("invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
		if iv.Assertions != 1 {
			t.Fatalf("invariant %s assertions = %d, want 1", iv.Name, iv.Assertions)
		}
	}

	heldDiv := AssertInvariants(nil, Expect{Kind: KindDividend, DividendAmountMinor: "1"})
	if len(heldDiv) != 1 || heldDiv[0].Status != InvariantHeld {
		t.Fatalf("dividend invariant = %+v, want one HOLD", heldDiv)
	}

	neg := AssertInvariants(nil, Expect{
		Kind:                 KindAccount,
		PurchasedPriceMinor:  "10000",
		PurchasedAmountMinor: "-1",
	})
	found := false
	for _, iv := range neg {
		if iv.Name == "purchased_amount_minor_non_negative" && iv.Status == InvariantViolated {
			found = true
		}
	}
	if !found {
		t.Fatalf("purchased_amount_minor_non_negative = %+v, want VIOLATED", neg)
	}
}
