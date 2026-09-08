package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its stored value, code and name
// are transcribed from the committed loanproduct captures but it is never
// written to the store. It exists only so the harness machinery can be exercised
// without touching the store.

const probeCommit = "426a23544e8426a38ae43ae404670a0a7e85b9eb"

const probeTemplateSHA = "6168b177ec87a259015aa5a2cd8eb93a838de571765a0a3d16a66a6683c523fe"

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

// probeTenant is the gerege tenant context every loanproduct capture was taken under.
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

// configProbe builds a valid loanproduct-config vector for one (vocabulary,
// stored, code, name) decode, transcribed from the committed template capture.
func configProbe(vocab Vocabulary, stored int32, code, name, cap string) *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-" + strings.ReplaceAll(string(vocab), "_", "-") + "-" + strings.ReplaceAll(name, "_", "-"),
		Title:   "probe " + string(vocab) + " " + name,
		Class:   ClassParity,
		Context: LoanProductContext,
		Note:    "probe: transcribed from loanproducts-template-raw.json option list, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLoanProductConfig, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: transcribed from loanproducts-template-raw.json option list",
			CaptureRef:    ".softhouse/capture/loanproduct/out/loanproducts-template-raw.json",
			CaptureSHA256: probeTemplateSHA,
			CaptureCaseID: code,
			Citation:      "loanproducts-template-raw.json option list — stored id " + itoa(stored) + " -> code " + code,
		},
		TenantParams:         probeTenant(),
		Request:              Request{Vocabulary: string(vocab), Stored: stored},
		Expect:               Expect{Stored: stored, Code: code, Name: name},
		CapabilitiesRequired: []string{cap},
		GradedAgainst:        []string{"loanproduct-go"},
	}
}

func itoa(n int32) string {
	if n == 0 {
		return "0"
	}
	neg := n < 0
	if neg {
		n = -n
	}
	var b [12]byte
	i := len(b)
	for n > 0 {
		i--
		b[i] = byte('0' + n%10)
		n /= 10
	}
	if neg {
		i--
		b[i] = '-'
	}
	return string(b[i:])
}

// probeVectors returns one representative probe for each of the six vocabularies.
func probeVectors() []*Vector {
	return []*Vector{
		configProbe(VocabularyAmortizationMethod, 1, "amortizationType.equal.installments", "EQUAL_INSTALLMENTS", "amortization-method"),
		configProbe(VocabularyInterestMethod, 0, "interestType.declining.balance", "DECLINING_BALANCE", "interest-method"),
		configProbe(VocabularyInterestCalcPeriod, 1, "interestCalculationPeriodType.same.as.repayment.period", "SAME_AS_REPAYMENT_PERIOD", "interest-calc-period"),
		configProbe(VocabularyPeriodFrequency, 2, "periodFrequencyType.months", "MONTHS", "period-frequency"),
		configProbe(VocabularyDaysInMonth, 30, "DaysInMonthType.days360", "DAYS_30", "days-in-month"),
		configProbe(VocabularyDaysInYear, 360, "DaysInYearType.days360", "DAYS_360", "days-in-year"),
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "loanproduct-go",
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

func TestNoFloatInTheLoanProductTree(t *testing.T) {
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

func TestCorrectImplementationPassesAllVocabularies(t *testing.T) {
	for _, probe := range probeVectors() {
		if p := Admit(probe, Options{}); len(p) > 0 {
			t.Fatalf("%s probe should be admissible: %v", probe.CaseID, p)
		}
		if got := gradeOne(probe, Options{Implementation: NewGoEvaluator()}); got.Outcome != OutcomePass {
			t.Fatalf("%s correct impl outcome = %s, want PASS; diffs=%v", probe.CaseID, got.Outcome, got.Diffs)
		}
	}
}

func TestWrongImplementationRunsRed(t *testing.T) {
	v := configProbe(VocabularyDaysInYear, 360, "DaysInYearType.days360", "DAYS_360", "days-in-year")

	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrongImpl, ok := Lookup("loanproduct-wrong-swap-days360-365")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("loanproduct-wrong-swap-days360-365"); !bad {
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

// wrongRunsRedOn is the shared assertion for the additional red-drives: the
// probe must PASS under the correct implementation and FAIL under the named
// registered-wrong one, producing at least one diff.
func wrongRunsRedOn(t *testing.T, name string, probe *Vector) {
	t.Helper()
	wrongImpl, ok := Lookup(name)
	if !ok {
		t.Fatalf("%s not registered", name)
	}
	if _, bad := IsRegisteredWrong(name); !bad {
		t.Fatalf("%s not marked wrong", name)
	}
	correct := gradeOne(probe, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	red := gradeOne(probe, Options{Implementation: wrongImpl})
	if red.Outcome != OutcomeFail {
		t.Fatalf("%s outcome = %s, want FAIL", name, red.Outcome)
	}
	if len(red.Diffs) == 0 {
		t.Fatalf("%s produced no diffs", name)
	}
}

func TestIotaOrdinalWrongRunsRed(t *testing.T) {
	wrongRunsRedOn(t, "loanproduct-wrong-iota-ordinals",
		configProbe(VocabularyDaysInYear, 360, "DaysInYearType.days360", "DAYS_360", "days-in-year"))
}

func TestDimSiblingNameWrongRunsRed(t *testing.T) {
	wrongRunsRedOn(t, "loanproduct-wrong-dim-sibling-name",
		configProbe(VocabularyDaysInMonth, 30, "DaysInMonthType.days360", "DAYS_30", "days-in-month"))
}

func TestFreqFieldQualifiedCodeWrongRunsRed(t *testing.T) {
	wrongRunsRedOn(t, "loanproduct-wrong-freq-field-qualified-code",
		configProbe(VocabularyPeriodFrequency, 2, "periodFrequencyType.months", "MONTHS", "period-frequency"))
}

func TestUnknownStoredErrs(t *testing.T) {
	for _, v := range probeVectors() {
		v.Request.Stored = 9999
		got, err := NewGoEvaluator().Evaluate(v.Request)
		if err == nil {
			t.Fatalf("unknown stored value in %s should error, got %+v", v.Request.Vocabulary, got)
		}
	}
}

func TestUnknownVocabularyErrs(t *testing.T) {
	v := configProbe(VocabularyDaysInYear, 360, "DaysInYearType.days360", "DAYS_360", "days-in-year")
	v.Request.Vocabulary = "not-a-vocabulary"
	if _, err := NewGoEvaluator().Evaluate(v.Request); err == nil {
		t.Fatal("unknown vocabulary should error")
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"amortization-method":  {Name: "amortization-method", InGradedDomain: true, Evidence: "loanproducts-template-raw.json"},
			"interest-method":      {Name: "interest-method", InGradedDomain: true, Evidence: "loanproducts-template-raw.json"},
			"interest-calc-period": {Name: "interest-calc-period", InGradedDomain: true, Evidence: "loanproducts-template-raw.json"},
			"period-frequency":     {Name: "period-frequency", InGradedDomain: true, Evidence: "loanproducts-template-raw.json"},
			"days-in-month":        {Name: "days-in-month", InGradedDomain: true, Evidence: "loanproducts-template-raw.json"},
			"days-in-year":         {Name: "days-in-year", InGradedDomain: true, Evidence: "loanproducts-template-raw.json"},
		},
		bySeam: map[string]Seam{
			SeamLoanProductConfig: {Name: SeamLoanProductConfig, Status: map[string]SeamStatus{
				"amortization-method":  StatusExercised,
				"interest-method":      StatusExercised,
				"interest-calc-period": StatusExercised,
				"period-frequency":     StatusExercised,
				"days-in-month":        StatusExercised,
				"days-in-year":         StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamLoanProductConfig, []string{"days-in-year"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"days-in-year"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamLoanProductConfig, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
	// A capability not recorded on the seam refuses (default-deny).
	if v := r.Assess(SeamLoanProductConfig, []string{"not-a-capability"}); v.Gradeable {
		t.Fatalf("unknown capability should refuse, got gradeable")
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := configProbe(VocabularyDaysInYear, 360, "DaysInYearType.days360", "DAYS_360", "days-in-year")

	badSchema := *base
	badSchema.Schema = "gerege.loanproduct.vector/v2"
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

	negativeStored := *base
	negativeStored.Request.Stored = -1
	if p := Admit(&negativeStored, Options{}); len(p) == 0 {
		t.Fatal("negative stored admitted")
	}

	negativeExpect := *base
	negativeExpect.Expect.Stored = -1
	if p := Admit(&negativeExpect, Options{}); len(p) == 0 {
		t.Fatal("negative expect.stored admitted")
	}

	emptyCode := *base
	emptyCode.Expect.Code = ""
	if p := Admit(&emptyCode, Options{}); len(p) == 0 {
		t.Fatal("empty expect.code admitted")
	}

	emptyName := *base
	emptyName.Expect.Name = ""
	if p := Admit(&emptyName, Options{}); len(p) == 0 {
		t.Fatal("empty expect.name admitted")
	}

	// A corrupted expect is ADMITTED (admission checks structure, not the port's
	// decode) and graded red against the correct implementation: a divergence
	// between the oracle's expect and the port's output is a FAIL, not a refusal.
	badExpect := *base
	badExpect.Expect.Code = "DaysInYearType.days365"
	if p := Admit(&badExpect, Options{}); len(p) > 0 {
		t.Fatalf("corrupted expect should be admissible, got: %v", p)
	}
	if got := gradeOne(&badExpect, Options{Implementation: NewGoEvaluator()}); got.Outcome != OutcomeFail {
		t.Fatalf("corrupted expect outcome = %s, want FAIL", got.Outcome)
	}
}

func TestInvariants(t *testing.T) {
	v := configProbe(VocabularyDaysInYear, 360, "DaysInYearType.days360", "DAYS_360", "days-in-year")
	held := AssertInvariants(v, Expect{Stored: 360, Code: "DaysInYearType.days360", Name: "DAYS_360"})
	for _, iv := range held {
		if iv.Status != InvariantHeld {
			t.Fatalf("invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
		if iv.Assertions != 1 {
			t.Fatalf("invariant %s assertions = %d, want 1", iv.Name, iv.Assertions)
		}
	}

	if invs := AssertInvariants(v, Expect{Stored: 2, Code: "DaysInYearType.days360", Name: "DAYS_360"}); invs[0].Status != InvariantViolated {
		t.Fatalf("stored_in_vocabulary = %s, want VIOLATED", invs[0].Status)
	}
	if invs := AssertInvariants(v, Expect{Stored: 360, Code: "", Name: ""}); invs[1].Status != InvariantViolated {
		t.Fatalf("code_non_empty = %s, want VIOLATED", invs[1].Status)
	}
}
