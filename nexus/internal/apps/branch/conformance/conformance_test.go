package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its numbers are transcribed from
// the committed branch captures but it is never written to the store.

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

// allocateProbe builds a valid allocate vector.
func allocateProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-allocate",
		Title:   "probe allocate cash movement",
		Class:   ClassParity,
		Context: BranchContext,
		Note:    "probe: transcribed from summary-cashier2-final-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamCashierTxnAmount, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from summary-cashier2-final-raw.json",
			CaptureRef:    ".softhouse/capture/branch/out/summary-cashier2-final-raw.json",
			CaptureSHA256: "0000000000000000000000000000000000000000000000000000000000000000",
			CaptureCaseID: "7",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request:              Request{TxnType: 101, TxnAmount: "100000.50", CurrencyCode: "MNT"},
		Expect:               Expect{TxnTypeID: 101, TxnTypeValue: "Allocate Cash", TxnAmountMinor: "10000050"},
		CapabilitiesRequired: []string{"cashier-txn-amount"},
		GradedAgainst:        []string{"branch-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "branch-go",
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

func TestNoFloatInTheBranchTree(t *testing.T) {
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
	v := allocateProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}

	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrongImpl, ok := Lookup("branch-wrong-off-by-one")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("branch-wrong-off-by-one"); !bad {
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

// summaryPostProbe builds the cashier-summary POST-point vector as a probe (see
// BR-04): the row set summary-cashier2-post-raw.json listed, folded to the
// buckets that read-back published.
func summaryPostProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-summary-post",
		Title:   "probe cashier 2 summary after allocate/settle",
		Class:   ClassParity,
		Context: BranchContext,
		Note:    "probe: transcribed from summary-cashier2-post-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamCashierSummary, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from summary-cashier2-post-raw.json",
			CaptureRef:    ".softhouse/capture/branch/out/summary-cashier2-post-raw.json",
			CaptureSHA256: "0000000000000000000000000000000000000000000000000000000000000000",
			CaptureCaseID: "post",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request: Request{Summary: &SummaryRequest{Rows: []CashierSummaryRow{
			{ID: 2, TxnType: 101, TxnAmount: "100000.50"},
			{ID: 6, TxnType: 101, TxnAmount: "12345.67"},
			{ID: 7, TxnType: 101, TxnAmount: "100000.50"},
			{ID: 8, TxnType: 102, TxnAmount: "40000.25"},
		}}},
		Expect:               Expect{SumCashAllocation: "21234667", SumCashSettlement: "4000025", NetCash: "17234642"},
		CapabilitiesRequired: []string{"cashier-summary"},
		GradedAgainst:        []string{"branch-go"},
	}
}

// tellerStatusProbe builds the teller-status ACTIVE vector as a probe (see
// BR-05): the label the teller list read-back serialised for its two rows.
func tellerStatusProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-teller-active",
		Title:   "probe teller status ACTIVE stored integer",
		Class:   ClassParity,
		Context: BranchContext,
		Note:    "probe: transcribed from tellers-list-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamTellerStatus, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from tellers-list-raw.json",
			CaptureRef:    ".softhouse/capture/branch/out/tellers-list-raw.json",
			CaptureSHA256: "0000000000000000000000000000000000000000000000000000000000000000",
			CaptureCaseID: "teller id 2 (SEED-Teller-01)",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request:              Request{TellerStatus: &TellerStatusRequest{StatusLabel: "ACTIVE"}},
		Expect:               Expect{TellerStatusStored: 300},
		CapabilitiesRequired: []string{"teller-status"},
		GradedAgainst:        []string{"branch-go"},
	}
}

// gradeProbe admits and grades a probe against one implementation, failing the
// test if the probe is inadmissible.
func gradeProbe(t *testing.T, v *Vector, name string) vectorResult {
	t.Helper()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("%s probe should be admissible: %v", v.CaseID, p)
	}
	impl, ok := Lookup(name)
	if !ok {
		t.Fatalf("implementation %q not registered", name)
	}
	return gradeOne(v, Options{Implementation: impl})
}

func TestCashierSummarySeamWrongImplsRunRed(t *testing.T) {
	v := summaryPostProbe()

	if r := gradeProbe(t, v, "branch-go"); r.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", r.Outcome, r.Diffs)
	}
	for _, w := range []string{
		"branch-wrong-summary-drops-last-row",
		"branch-wrong-summary-settle-as-allocate",
		"branch-wrong-summary-net-adds-settlement",
		"branch-wrong-off-by-one",
	} {
		if _, bad := IsRegisteredWrong(w); !bad {
			t.Fatalf("wrong implementation %q not marked wrong", w)
		}
		r := gradeProbe(t, v, w)
		if r.Outcome != OutcomeFail {
			t.Fatalf("wrong impl %s outcome = %s, want FAIL", w, r.Outcome)
		}
		if len(r.Diffs) == 0 {
			t.Fatalf("wrong impl %s produced no diffs", w)
		}
	}
}

func TestTellerStatusSeamWrongImplsRunRed(t *testing.T) {
	v := tellerStatusProbe()

	if r := gradeProbe(t, v, "branch-go"); r.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", r.Outcome, r.Diffs)
	}
	for _, w := range []string{
		"branch-wrong-teller-status-ordinal",
		"branch-wrong-off-by-one",
	} {
		if _, bad := IsRegisteredWrong(w); !bad {
			t.Fatalf("wrong implementation %q not marked wrong", w)
		}
		r := gradeProbe(t, v, w)
		if r.Outcome != OutcomeFail {
			t.Fatalf("wrong impl %s outcome = %s, want FAIL", w, r.Outcome)
		}
		if len(r.Diffs) == 0 {
			t.Fatalf("wrong impl %s produced no diffs", w)
		}
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"cashier-txn-amount": {Name: "cashier-txn-amount", InGradedDomain: true, Evidence: "summary-cashier2-final"},
		},
		bySeam: map[string]Seam{
			SeamCashierTxnAmount: {Name: SeamCashierTxnAmount, Status: map[string]SeamStatus{
				"cashier-txn-amount": StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamCashierTxnAmount, []string{"cashier-txn-amount"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"cashier-txn-amount"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamCashierTxnAmount, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamCashierTxnAmount, []string{"nope"}); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("unknown capability should refuse with reason %q, got %q", reasonUnknownCapability, v.Reason)
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := allocateProbe()

	badSchema := *base
	badSchema.Schema = "gerege.branch.vector/v2"
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

	unknownTxn := *base
	unknownTxn.Request.TxnType = 0
	if p := Admit(&unknownTxn, Options{}); len(p) == 0 {
		t.Fatal("unknown txn_type admitted")
	}

	fractional := *base
	fractional.Request.TxnAmount = "100000.505"
	if p := Admit(&fractional, Options{}); len(p) == 0 {
		t.Fatal("sub-minor-unit residue txn_amount admitted")
	}
}

func TestInvariants(t *testing.T) {
	held := AssertInvariants(nil, Expect{TxnTypeID: 101, TxnTypeValue: "Allocate Cash", TxnAmountMinor: "10000050"})
	for _, iv := range held {
		if iv.Status != InvariantHeld {
			t.Fatalf("invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
		if iv.Assertions != 1 {
			t.Fatalf("invariant %s assertions = %d, want 1", iv.Name, iv.Assertions)
		}
	}

	neg := AssertInvariants(nil, Expect{TxnTypeID: 101, TxnTypeValue: "Allocate Cash", TxnAmountMinor: "-1"})
	if neg[0].Name != "txn_amount_non_negative" || neg[0].Status != InvariantViolated {
		t.Fatalf("txn_amount_non_negative = %s, want VIOLATED", neg[0].Status)
	}
}
