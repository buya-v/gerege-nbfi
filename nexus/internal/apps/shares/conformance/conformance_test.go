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
			TotalPendingShares:  0,
			PurchasedShares:     100,
			PurchasedPrice:      "100.00",
			PurchasedAmount:     "10000.00",
			PurchasedStatusID:   300,
		},
		Expect: Expect{
			Kind:                  KindAccount,
			AccountStatusStored:   300,
			TotalApprovedShares:   100,
			TotalPendingShares:    0,
			PurchasedShares:       100,
			PurchasedPriceMinor:   "10000",
			PurchasedAmountMinor:  "1000000",
			PurchasedStatusStored: 300,
		},
		CapabilitiesRequired: []string{"share-account"},
		GradedAgainst:        []string{"shares-go"},
	}
}

// nonroundAccountProbe builds a valid share-account vector from the NON-ROUND
// capture (account id 5): 137 shares at 137.50 = 18837.50, so the purchase price
// and the share count both differ from the seed 100.00 / 100 corpus.
func nonroundAccountProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-account-nonround",
		Title:   "probe non-round share account purchase readback",
		Class:   ClassParity,
		Context: SharesContext,
		Note:    "probe: transcribed from shares-nonround-money out/share-account-detail-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamShareAccount, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from shares-nonround-money out/share-account-detail-raw.json (account 5)",
			CaptureRef:    ".softhouse/capture/shares-nonround-money/out/share-account-detail-raw.json",
			CaptureSHA256: "3d1af6c9640dfa776856c7189e9eb051b24c76eac0dcaf76abe8596824c69c7b",
			CaptureCaseID: "5",
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
			TotalApprovedShares: 137,
			TotalPendingShares:  0,
			PurchasedShares:     137,
			PurchasedPrice:      "137.50",
			PurchasedAmount:     "18837.50",
			PurchasedStatusID:   300,
		},
		Expect: Expect{
			Kind:                  KindAccount,
			AccountStatusStored:   300,
			TotalApprovedShares:   137,
			TotalPendingShares:    0,
			PurchasedShares:       137,
			PurchasedPriceMinor:   "13750",
			PurchasedAmountMinor:  "1883750",
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

// dividendStatusProbe builds a valid share-dividend vector that also pins the
// dividend row's stored status integer (the account aggregate's dividends list
// read the same row SH-02 grades by amount back with status id 100).
func dividendStatusProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-dividend-status",
		Title:   "probe share-account dividend row status readback",
		Class:   ClassParity,
		Context: SharesContext,
		Note:    "probe: transcribed from share-account-detail-raw.json dividends[0], not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamShareDividend, FineractCommit: probeCommit},
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
			Kind:             KindDividend,
			CurrencyCode:     "MNT",
			DividendAmount:   "0.01",
			DividendStatusID: 100,
		},
		Expect: Expect{
			Kind:                 KindDividend,
			DividendAmountMinor:  "1",
			DividendStatusStored: 100,
		},
		CapabilitiesRequired: []string{"share-dividend"},
		GradedAgainst:        []string{"shares-go"},
	}
}

// productDetailProbe builds a valid share-product vector (product id 3,
// unit 100.00, capital 100000.00, no rounding surface).
func productDetailProbe() *Vector {
	return productProbe("100.00", "100000.00", "10000", "10000000")
}

// productListProbe builds a share-product list-row vector whose unit price and
// share capital differ (product id 2, unit 100.00, capital 1.00), so a
// transposed-money-column defect discriminates.
func productListProbe() *Vector {
	return productProbe("100.00", "1.00", "10000", "100")
}

// productZeroProbe builds the share-product list row with a PRESENT-but-ZERO
// share capital (product id 1, unit 100.00, capital 0.00): a port that drops a
// zero money cell goes red here.
func productZeroProbe() *Vector {
	return productProbe("100.00", "0.00", "10000", "0")
}

func productProbe(unitPrice, capital, unitMinor, capitalMinor string) *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-product",
		Title:   "probe share-product readback",
		Class:   ClassParity,
		Context: SharesContext,
		Note:    "probe: transcribed from share-product captures, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamShareProduct, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from share-product-detail-raw.json",
			CaptureRef:    ".softhouse/capture/shares/out/share-product-detail-raw.json",
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
			Kind:         KindProduct,
			CurrencyCode: "MNT",
			UnitPrice:    unitPrice,
			ShareCapital: capital,
			TotalShares:  1000,
		},
		Expect: Expect{
			Kind:              KindProduct,
			UnitPriceMinor:    unitMinor,
			ShareCapitalMinor: capitalMinor,
			TotalShares:       1000,
		},
		CapabilitiesRequired: []string{"share-product"},
		GradedAgainst:        []string{"shares-go"},
	}
}

// nonroundProductProbe builds the share-product read-back whose unit price and
// share capital are NOT the seed 100.00 / 100000.00 (product id 4, unit 137.50,
// capital 188787.50, 1373 issued shares): the only product probe a hardcoded
// unit_price = 10000 defect can see.
func nonroundProductProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-product-nonround",
		Title:   "probe non-round share-product readback",
		Class:   ClassParity,
		Context: SharesContext,
		Note:    "probe: transcribed from shares-nonround-money out/share-product-detail-raw.json (product 4), not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamShareProduct, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from shares-nonround-money out/share-product-detail-raw.json (product 4)",
			CaptureRef:    ".softhouse/capture/shares-nonround-money/out/share-product-detail-raw.json",
			CaptureSHA256: "40c2bcc65b16c5ee579dcbfe9a99e9f57d4e1d3b61a1b4c3125fb4f48dc1b7b1",
			CaptureCaseID: "4",
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
			Kind:         KindProduct,
			CurrencyCode: "MNT",
			UnitPrice:    "137.50",
			ShareCapital: "188787.50",
			TotalShares:  1373,
		},
		Expect: Expect{
			Kind:              KindProduct,
			UnitPriceMinor:    "13750",
			ShareCapitalMinor: "18878750",
			TotalShares:       1373,
		},
		CapabilitiesRequired: []string{"share-product"},
		GradedAgainst:        []string{"shares-go"},
	}
}

// accountListProbe builds a valid share-account LIST-ROW vector (account id 3,
// no purchase group, no money): it grades the stored status and summary counts
// only.
func accountListProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-account-list",
		Title:   "probe share-account list row readback",
		Class:   ClassParity,
		Context: SharesContext,
		Note:    "probe: transcribed from shares-accounts-list-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamShareAccount, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from shares-accounts-list-raw.json",
			CaptureRef:    ".softhouse/capture/shares/out/shares-accounts-list-raw.json",
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
			TotalPendingShares:  0,
		},
		Expect: Expect{
			Kind:                KindAccount,
			AccountStatusStored: 300,
			TotalApprovedShares: 100,
			TotalPendingShares:  0,
		},
		CapabilitiesRequired: []string{"share-account"},
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

// allProbes returns every probe the red-drive exercises. A probe is never
// written to the store: it exists to prove, in-test, that the correct
// implementation PASSes and each registered wrong implementation FAILs with a
// non-zero diff on the vectors its defect can see.
func allProbes() []*Vector {
	return []*Vector{
		accountProbe(), nonroundAccountProbe(), dividendProbe(), dividendStatusProbe(),
		productDetailProbe(), productListProbe(), productZeroProbe(), nonroundProductProbe(),
		accountListProbe(),
	}
}

// wrongImplRed is one registered wrong implementation and the probes its defect
// MUST turn red (its "drive set"). A wrong implementation may PASS a probe its
// defect cannot see: off-by-one cannot move a share-account list row that has
// no money cell, and a status-ordinal defect cannot touch an amount-only
// dividend vector.
var wrongImplRed = map[string][]*Vector{
	"shares-wrong-off-by-one": {
		accountProbe(), nonroundAccountProbe(), dividendProbe(), dividendStatusProbe(),
		productDetailProbe(), productListProbe(), productZeroProbe(), nonroundProductProbe(),
	},
	"shares-wrong-status-iota-ordinal": {
		accountProbe(), nonroundAccountProbe(), dividendStatusProbe(), accountListProbe(),
	},
	"shares-wrong-summary-approved-as-pending": {
		accountProbe(), nonroundAccountProbe(), accountListProbe(),
	},
	"shares-wrong-product-price-transposed": {
		productDetailProbe(), productListProbe(), productZeroProbe(), nonroundProductProbe(),
	},
	"shares-wrong-zero-money-dropped": {
		productZeroProbe(),
	},
	"shares-wrong-unit-price-hardcoded": {
		nonroundAccountProbe(), nonroundProductProbe(),
	},
}

func TestWrongImplementationRunsRed(t *testing.T) {
	// The correct implementation must PASS every probe.
	for _, v := range allProbes() {
		if p := Admit(v, Options{}); len(p) > 0 {
			t.Fatalf("%s should be admissible: %v", v.CaseID, p)
		}
		correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
		if correct.Outcome != OutcomePass {
			t.Fatalf("%s correct impl outcome = %s, want PASS; diffs=%v", v.CaseID, correct.Outcome, correct.Diffs)
		}
	}

	for name, drive := range wrongImplRed {
		wrongImpl, ok := Lookup(name)
		if !ok {
			t.Fatalf("wrong implementation %q not registered", name)
		}
		if _, bad := IsRegisteredWrong(name); !bad {
			t.Fatalf("wrong implementation %q not marked wrong", name)
		}

		// Every probe in its drive set must go red with a non-zero diff.
		for _, v := range drive {
			red := gradeOne(v, Options{Implementation: wrongImpl})
			if red.Outcome != OutcomeFail {
				t.Fatalf("%s wrong impl %q outcome = %s, want FAIL", v.CaseID, name, red.Outcome)
			}
			if len(red.Diffs) == 0 {
				t.Fatalf("%s wrong impl %q produced no diffs", v.CaseID, name)
			}
		}

		// And a probe the defect cannot see must still PASS: a wrong
		// implementation that is red on everything proves nothing about its
		// specificity.
		for _, v := range allProbes() {
			skip := false
			for _, dv := range drive {
				if dv.CaseID == v.CaseID {
					skip = true
					break
				}
			}
			if skip {
				continue
			}
			if red := gradeOne(v, Options{Implementation: wrongImpl}); red.Outcome != OutcomePass {
				t.Fatalf("%s wrong impl %q should PASS (defect cannot see it): outcome = %s, diffs=%v",
					v.CaseID, name, red.Outcome, red.Diffs)
			}
		}
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"share-account":  {Name: "share-account", InGradedDomain: true, Evidence: "share-account-detail"},
			"share-dividend": {Name: "share-dividend", InGradedDomain: true, Evidence: "shares-product-dividends"},
			"share-product":  {Name: "share-product", InGradedDomain: true, Evidence: "share-product-detail"},
		},
		bySeam: map[string]Seam{
			SeamShareAccount: {Name: SeamShareAccount, Status: map[string]SeamStatus{
				"share-account": StatusExercised,
			}},
			SeamShareDividend: {Name: SeamShareDividend, Status: map[string]SeamStatus{
				"share-dividend": StatusExercised,
			}},
			SeamShareProduct: {Name: SeamShareProduct, Status: map[string]SeamStatus{
				"share-product": StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamShareAccount, []string{"share-account"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess(SeamShareDividend, []string{"share-dividend"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess(SeamShareProduct, []string{"share-product"}); !v.Gradeable {
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
	acct := &Vector{Request: Request{PurchasedShares: 100}}
	held := AssertInvariants(acct, Expect{
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

	// A share-account LIST row carries no purchase group, so its money
	// invariants must not be asserted (an absent group is not a violation).
	if got := AssertInvariants(&Vector{}, Expect{Kind: KindAccount}); len(got) != 0 {
		t.Fatalf("account list row produced invariants %+v, want none", got)
	}

	heldDiv := AssertInvariants(&Vector{}, Expect{Kind: KindDividend, DividendAmountMinor: "1"})
	if len(heldDiv) != 1 || heldDiv[0].Status != InvariantHeld {
		t.Fatalf("dividend invariant = %+v, want one HOLD", heldDiv)
	}

	heldProd := AssertInvariants(&Vector{}, Expect{
		Kind:              KindProduct,
		UnitPriceMinor:    "10000",
		ShareCapitalMinor: "0",
	})
	if len(heldProd) != 2 {
		t.Fatalf("product invariants = %+v, want two HOLDs", heldProd)
	}
	for _, iv := range heldProd {
		if iv.Status != InvariantHeld {
			t.Fatalf("product invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
	}

	neg := AssertInvariants(acct, Expect{
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

	negProd := AssertInvariants(&Vector{}, Expect{
		Kind:              KindProduct,
		UnitPriceMinor:    "10000",
		ShareCapitalMinor: "1.5",
	})
	found = false
	for _, iv := range negProd {
		if iv.Name == "share_capital_minor_non_negative" && iv.Status == InvariantViolated {
			found = true
		}
	}
	if !found {
		t.Fatalf("share_capital_minor_non_negative = %+v, want VIOLATED", negProd)
	}
}
