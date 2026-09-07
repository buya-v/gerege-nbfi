package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its numbers are transcribed from
// the committed savings captures but it is never written to the store. It exists
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

// dailyInterestProbe builds a valid daily-interest-seam vector: the
// discriminating cell of the SEED-Savings-Product-Daily account, one-day raw
// interest 0.005 -> HALF_UP 0.01.
func dailyInterestProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-daily-interest",
		Title:   "probe daily interest",
		Class:   ClassParity,
		Context: SavingsContext,
		Note:    "probe: transcribed from savings-account-daily-raw.json transaction id 5, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamSavingsDailyInterest, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: amount of the daily interest posting of the discriminating savings account",
			CaptureRef:    ".softhouse/capture/savings/out/savings-account-daily-raw.json",
			CaptureSHA256: "15999be438f6d8db15d13b4eb351c6749260db7f6790cb42ce4b2af8843eddf8",
			CaptureCaseID: "SEED-Savings-Product-Daily",
		},
		TenantParams: probeTenant(),
		Request: Request{DailyInterest: &DailyInterestRequest{
			BalanceMinor:         "100000",
			RatePerAnnumMicroPct: 182500,
			DaysInYear:           365,
			Days:                 1,
		}},
		Expect:               Expect{InterestMinor: "1"},
		CapabilitiesRequired: []string{"daily-balance-interest-rounding"},
		GradedAgainst:        []string{"savings-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "savings-go",
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

func TestNoFloatInTheSavingsTree(t *testing.T) {
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

func TestDailyInterestSeamGrading(t *testing.T) {
	v := dailyInterestProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	if correct.GradedCells != 1 || correct.MoneyCells != 1 {
		t.Fatalf("daily-interest graded cells = %d, money = %d; want 1/1", correct.GradedCells, correct.MoneyCells)
	}

	wrongImpl, ok := Lookup("savings-wrong-half-even-daily-interest")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("savings-wrong-half-even-daily-interest"); !bad {
		t.Fatal("wrong implementation not marked wrong")
	}
	red := gradeOne(v, Options{Implementation: wrongImpl})
	if red.Outcome != OutcomeFail {
		t.Fatalf("wrong impl outcome = %s, want FAIL; diffs=%v", red.Outcome, red.Diffs)
	}
	if len(red.Diffs) == 0 {
		t.Fatal("wrong impl produced no diffs")
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"daily-balance-interest-rounding": {Name: "daily-balance-interest-rounding", InGradedDomain: true, Evidence: "savings-account-daily-raw.json"},
			"monthly-posting":                 {Name: "monthly-posting", InGradedDomain: false, Evidence: "no transcribed day counts for the monthly postings"},
		},
		bySeam: map[string]Seam{
			SeamSavingsDailyInterest: {Name: SeamSavingsDailyInterest, Status: map[string]SeamStatus{
				"daily-balance-interest-rounding": StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamSavingsDailyInterest, []string{"daily-balance-interest-rounding"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"daily-balance-interest-rounding"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamSavingsDailyInterest, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamSavingsDailyInterest, []string{"nope"}); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("unknown capability should refuse with reason %q, got %q", reasonUnknownCapability, v.Reason)
	}
	if v := r.Assess(SeamSavingsDailyInterest, []string{"monthly-posting"}); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("out-of-domain capability should refuse with reason %q, got %q", reasonUnknownCapability, v.Reason)
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := dailyInterestProbe()

	badSchema := *base
	badSchema.Schema = "gerege.savings.vector/v2"
	if p := Admit(&badSchema, Options{}); len(p) == 0 {
		t.Fatal("wrong schema admitted")
	}

	badContext := *base
	badContext.Context = "loan"
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

	frac := *base
	frac.Request.DailyInterest.BalanceMinor = "1000.00"
	if p := Admit(&frac, Options{}); len(p) == 0 {
		t.Fatal("fractional money string admitted")
	}

	negExpect := *base
	negExpect.Expect.InterestMinor = "-1"
	if p := Admit(&negExpect, Options{}); len(p) == 0 {
		t.Fatal("negative expect money admitted")
	}
}

func TestInvariants(t *testing.T) {
	d := &Vector{Oracle: OracleStamp{Seam: SeamSavingsDailyInterest}}
	if invs := AssertInvariants(d, Expect{InterestMinor: "-1"}); invs[0].Status != InvariantViolated {
		t.Fatalf("interest_non_negative = %s, want VIOLATED", invs[0].Status)
	}
	if invs := AssertInvariants(d, Expect{InterestMinor: "1"}); invs[0].Status != InvariantHeld {
		t.Fatalf("interest_non_negative = %s, want HOLD", invs[0].Status)
	}
}
