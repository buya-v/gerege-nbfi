package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/gerege/nexus/internal/apps/charges"
)

// Every Vector built in this file is a PROBE: its numbers are meaningless and it
// is never written to the store. It exists only so the harness machinery can be
// exercised without depending on the state of the vector store.

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

// percentFeeProbe is a percentage-of-amount fee whose exact fee carries a
// fraction that rounds HALF_UP: 1000000 * 1234567 / 10^8 = 12345.67 -> 12346.
func percentFeeProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-percent-fee",
		Title:   "probe percentage fee",
		Class:   ClassParity,
		Context: ChargesContext,
		Note:    "probe: meaningless numbers, not an observation",
		Oracle:  OracleStamp{Seam: SeamChargeEvaluate, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: meaningless numbers, not an observation",
			CaptureRef:    ".softhouse/capture/charges/out/fc/FC-00-probe.json",
			CaptureSHA256: "0000000000000000000000000000000000000000000000000000000000000000",
			CaptureCaseID: "probe-percent-fee",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request: ChargeRequest{
			Name:            "probe",
			CurrencyCode:    "MNT",
			AmountMinor:     "0",
			Percentage:      1234567,
			AppliesTo:       1,
			TimeType:        2,
			CalculationType: 2,
			PaymentMode:     0,
			BaseAmountMinor: "1000000",
		},
		Expect:        ChargeExpect{Kind: ExpectFee, FeeMinor: "12346"},
		GradedAgainst: []string{"charges-go"},
	}
}

// penaltyAtDisbursementProbe is a flat PENALTY due at disbursement: the charge
// definition's own Validate() refuses it with one code and assigns no fee. Its
// shape mirrors OHCAPj-penalty-at-disbursement-refused (750000 minor, penalty
// true, time 1), which is the only corpus vector whose output reads `penalty`.
func penaltyAtDisbursementProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-penalty-at-disbursement",
		Title:   "probe penalty due at disbursement refused",
		Class:   ClassParity,
		Context: ChargesContext,
		Note:    "probe: meaningless numbers, not an observation",
		Oracle:  OracleStamp{Seam: SeamChargeEvaluate, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: meaningless numbers, not an observation",
			CaptureRef:    ".softhouse/capture/charges/out/fc/FC-00-probe.json",
			CaptureSHA256: "0000000000000000000000000000000000000000000000000000000000000000",
			CaptureCaseID: "probe-penalty-at-disbursement",
		},
		TenantParams: &TenantParams{
			RoundingMode:    "HALF_UP",
			RoundingOrdinal: 4,
			Precision:       19,
			Currency:        "MNT",
			MinorUnits:      2,
			Timezone:        "Asia/Ulaanbaatar",
		},
		Request: ChargeRequest{
			Name:            "probe",
			CurrencyCode:    "MNT",
			AmountMinor:     "750000",
			Percentage:      0,
			AppliesTo:       1,
			TimeType:        1,
			CalculationType: 1,
			PaymentMode:     0,
			Penalty:         true,
			BaseAmountMinor: "",
		},
		Expect: ChargeExpect{
			Kind:            ExpectValidation,
			ValidationCodes: []string{"charge.due.at.disbursement.cannot.be.penalty"},
			FeeMinor:        "",
		},
		GradedAgainst: []string{"charges-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "charges-go",
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

func TestNoFloatInTheChargesTree(t *testing.T) {
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

func TestCellFieldsComputedAndNonEmpty(t *testing.T) {
	fields := CellFields()
	want := map[string]bool{
		"validation_code_count": true,
		"validation_codes[]":    true,
		"fee_minor":             true,
		"fee_present":           true,
	}
	for _, f := range fields {
		if !want[f] {
			t.Fatalf("unexpected cell field %q in %v", f, fields)
		}
		if !IsCellField(f) {
			t.Fatalf("IsCellField(%q) = false", f)
		}
	}
	for name := range want {
		if !IsCellField(name) {
			t.Fatalf("cell field %q missing from %v", name, fields)
		}
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

func TestParseMinorText(t *testing.T) {
	cases := []struct {
		in  string
		out charges.MinorUnits
		ok  bool
	}{
		{"12345", 12345, true},
		{"0", 0, true},
		{"-1", -1, true},
		{" 12 ", 12, true},
		{"1.5", 0, false},
		{"1e3", 0, false},
		{"", 0, false},
		{"12a", 0, false},
	}
	for _, c := range cases {
		got, err := parseMinorText(c.in)
		if c.ok && err != nil {
			t.Fatalf("parseMinorText(%q) error: %v", c.in, err)
		}
		if !c.ok && err == nil {
			t.Fatalf("parseMinorText(%q) accepted, want error", c.in)
		}
		if c.ok && got != c.out {
			t.Fatalf("parseMinorText(%q) = %d, want %d", c.in, got, c.out)
		}
	}
}

func TestWrongImplementationRunsRed(t *testing.T) {
	v := percentFeeProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}

	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrongImpl, ok := Lookup("charges-wrong-percent-truncating")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("charges-wrong-percent-truncating"); !bad {
		t.Fatal("wrong implementation not marked wrong")
	}

	red := gradeOne(v, Options{Implementation: wrongImpl})
	if red.Outcome != OutcomeFail {
		t.Fatalf("wrong impl outcome = %s, want FAIL", red.Outcome)
	}
	if red.MoneyCells != 1 {
		t.Fatalf("wrong impl money cells = %d, want 1 (the kill must be a MONEY kill)", red.MoneyCells)
	}
	if len(red.Diffs) == 0 {
		t.Fatal("wrong impl produced no diffs")
	}
}

// wrongRunsRedOn is the shared assertion for a registered-wrong driver whose
// defect the probe can see: the probe must PASS under the correct implementation
// and FAIL under the named one, producing at least one diff.
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

func TestOneScaleShortWrongRunsRed(t *testing.T) {
	wrongRunsRedOn(t, "charges-wrong-percent-one-scale-short", percentFeeProbe())
}

// TestCalculationTypeAlwaysFlatWrongRunsRed pins the shape of the
// ignore-calculation_type drive: on a percentage probe the correct port answers
// the percentage fee (12346) while a port that prices everything as FLAT answers
// the stored amount (0). The kill is a MONEY kill, which is the point of grading
// this field before any of the lower-impact ones.
func TestCalculationTypeAlwaysFlatWrongRunsRed(t *testing.T) {
	probe := percentFeeProbe()

	correct := gradeOne(probe, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrong, ok := Lookup("charges-wrong-calculation-type-always-flat")
	if !ok {
		t.Fatal("charges-wrong-calculation-type-always-flat not registered")
	}
	if _, bad := IsRegisteredWrong("charges-wrong-calculation-type-always-flat"); !bad {
		t.Fatal("charges-wrong-calculation-type-always-flat not marked wrong")
	}

	red := gradeOne(probe, Options{Implementation: wrong})
	if red.Outcome != OutcomeFail {
		t.Fatalf("calculation-type-always-flat outcome = %s, want FAIL", red.Outcome)
	}
	if red.MoneyCells != 1 {
		t.Fatalf("calculation-type-always-flat money cells = %d, want 1 (the kill must be a MONEY kill)", red.MoneyCells)
	}
}

// TestPenaltyIgnoredWrongRunsRed pins the shape of the ignore-penalty drive: the
// correct port refuses a penalty due at disbursement with one validation code,
// while a port that leaves the flag at its zero value treats it as a fee and
// returns 750000. The refusal is the only corpus output that reads `penalty`,
// which is why the kill count is 1 and not more.
func TestPenaltyIgnoredWrongRunsRed(t *testing.T) {
	probe := penaltyAtDisbursementProbe()

	correct := gradeOne(probe, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrong, ok := Lookup("charges-wrong-penalty-ignored")
	if !ok {
		t.Fatal("charges-wrong-penalty-ignored not registered")
	}
	if _, bad := IsRegisteredWrong("charges-wrong-penalty-ignored"); !bad {
		t.Fatal("charges-wrong-penalty-ignored not marked wrong")
	}

	red := gradeOne(probe, Options{Implementation: wrong})
	if red.Outcome != OutcomeFail {
		t.Fatalf("penalty-ignored outcome = %s, want FAIL", red.Outcome)
	}
	var sawValidation bool
	for _, d := range red.Diffs {
		if strings.HasPrefix(d, "validation") {
			sawValidation = true
		}
	}
	if !sawValidation {
		t.Fatalf("penalty-ignored diffs = %v, want at least one validation diff", red.Diffs)
	}
}

// TestBaseAmountIgnoredWrongRunsRed pins the shape of the ignore-base drive: a
// percentage fee computed against a zero base answers 0 where the probe's
// recorded fee is 12346, a money kill.
func TestBaseAmountIgnoredWrongRunsRed(t *testing.T) {
	wrongRunsRedOn(t, "charges-wrong-base-amount-ignored", percentFeeProbe())
}

// TestTimeTypeIgnoredWrongRunsRed pins the shape of the ignore-time-type drive:
// the probe's time 2 (SPECIFIED_DUE_DATE) decodes to INVALID(0), which is not a
// loan-legal charge time, so the fee probe is answered with a validation code
// and no fee.
func TestTimeTypeIgnoredWrongRunsRed(t *testing.T) {
	wrongRunsRedOn(t, "charges-wrong-time-type-ignored", percentFeeProbe())
}

// TestHalfEvenDiffersOnlyOnAnExactHalf pins the shape of the half-even red
// drive: the two rounding modes agree on every product whose truncated value is
// ODD (so the drive is indistinguishable from the correct port on the
// non-tie probe, whose fraction is .67) and differ only when the exact fee
// lands on a half-minor tie whose truncated value is EVEN — 1162502.5 rounds to
// 1162503 under HALF_UP but 1162502 under HALF_EVEN, which is exactly the kill
// the stored vector OHCAPj-pctamount-disbursement-halfup-tie reports. The
// probe is an exact half: 100 minor units x 0.5% = 0.5, whose truncated 0 is
// even, so HALF_UP rounds to 1 and HALF_EVEN rounds to 0.
func TestHalfEvenDiffersOnlyOnAnExactHalf(t *testing.T) {
	tie := percentFeeProbe()
	tie.CaseID = "probe-half-even-tie"
	tie.Request.TimeType = 1
	tie.Request.BaseAmountMinor = "100"
	tie.Request.Percentage = 500000
	tie.Expect.FeeMinor = "1"

	// HALF_UP answers 1 and PASSES.
	correct := gradeOne(tie, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	halfEven, ok := Lookup("charges-wrong-rounding-half-even")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("charges-wrong-rounding-half-even"); !bad {
		t.Fatal("wrong implementation not marked wrong")
	}

	// On the corpus-shaped probe (fraction .67, no tie) it is indistinguishable
	// from the correct port — that is why the stored corpus grades it green.
	corpusLike := gradeOne(percentFeeProbe(), Options{Implementation: halfEven})
	if corpusLike.Outcome != OutcomePass {
		t.Fatalf("half-even on a non-tie probe = %s, want PASS (indistinguishable); diffs=%v",
			corpusLike.Outcome, corpusLike.Diffs)
	}

	// On the tie it rounds to even, answering 0 where the oracle answers 1.
	red := gradeOne(tie, Options{Implementation: halfEven})
	if red.Outcome != OutcomeFail {
		t.Fatalf("half-even on the exact-half probe = %s, want FAIL", red.Outcome)
	}
	if red.MoneyCells != 1 {
		t.Fatalf("half-even money cells = %d, want 1 (the tie kill is a MONEY kill)", red.MoneyCells)
	}
}

// TestValidationSkippedChargesARequestTheOracleRefuses pins the shape of the
// validation-skipped red drive: a loan PENALTY due at disbursement is
// construction-invalid — Charge.java refuses it with
// charge.due.at.disbursement.cannot.be.penalty and no fee is assigned — so the
// correct port answers codes and no fee. A port that computes the fee without
// ever running Validate() answers a fee for that same request. The corpus
// carries only construction-valid charges, so no stored vector can see the
// difference; the probe can.
func TestValidationSkippedChargesARequestTheOracleRefuses(t *testing.T) {
	refused := percentFeeProbe()
	refused.CaseID = "probe-penalty-at-disbursement"
	refused.Request.CalculationType = 1 // FLAT
	refused.Request.TimeType = 1        // disbursement
	refused.Request.Penalty = true
	refused.Request.AmountMinor = "750000"
	refused.Request.Percentage = 0
	refused.Request.BaseAmountMinor = ""
	refused.Expect = ChargeExpect{
		Kind:            ExpectValidation,
		ValidationCodes: []string{"charge.due.at.disbursement.cannot.be.penalty"},
	}

	if p := Admit(refused, Options{}); len(p) > 0 {
		t.Fatalf("refused probe should be admissible: %v", p)
	}
	correct := gradeOne(refused, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	skip, ok := Lookup("charges-wrong-validation-skipped")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("charges-wrong-validation-skipped"); !bad {
		t.Fatal("wrong implementation not marked wrong")
	}

	red := gradeOne(refused, Options{Implementation: skip})
	if red.Outcome != OutcomeFail {
		t.Fatalf("validation-skipped outcome = %s, want FAIL: it charges a request the oracle refuses", red.Outcome)
	}
	if len(red.Diffs) == 0 {
		t.Fatalf("validation-skipped produced no diffs")
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"percent-fee":  {Name: "percent-fee", InGradedDomain: true, Evidence: "LoanCharge.percentageOf"},
			"flat-fee":     {Name: "flat-fee", InGradedDomain: true, Evidence: "flat amount"},
			"interest-fee": {Name: "interest-fee", InGradedDomain: false, Evidence: "needs loan interest"},
			"cap-blind":    {Name: "cap-blind", InGradedDomain: true, Evidence: "min/max cap"},
		},
		bySeam: map[string]Seam{
			SeamChargeEvaluate: {Name: SeamChargeEvaluate, Status: map[string]SeamStatus{
				"percent-fee":  StatusExercised,
				"flat-fee":     StatusExercised,
				"interest-fee": StatusExercised,
				"cap-blind":    StatusBlind,
			}},
		},
	}

	if v := r.Assess(SeamChargeEvaluate, []string{"percent-fee"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"percent-fee"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamChargeEvaluate, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamChargeEvaluate, []string{"nope"}); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("unknown capability should refuse with reason %q, got %q", reasonUnknownCapability, v.Reason)
	}
	if v := r.Assess(SeamChargeEvaluate, []string{"cap-blind"}); v.Gradeable || v.Reason != reasonSeamBlind {
		t.Fatalf("blind capability should refuse with reason %q, got %q", reasonSeamBlind, v.Reason)
	}
	if v := r.Assess(SeamChargeEvaluate, []string{"interest-fee"}); v.Gradeable || v.Reason != reasonUngraded {
		t.Fatalf("ungraded capability should refuse with reason %q, got %q", reasonUngraded, v.Reason)
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := percentFeeProbe()

	badSchema := *base
	badSchema.Schema = "gerege.charges.vector/v2"
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

	// A fee vector for an interest-based charge is not computable here.
	interestFee := *base
	interestFee.Request.CalculationType = 3 // percent of amount and interest
	interestFee.Expect = ChargeExpect{Kind: ExpectFee, FeeMinor: "1"}
	if p := Admit(&interestFee, Options{}); len(p) == 0 {
		t.Fatal("interest-based fee vector admitted")
	}

	// A validation vector with no codes grades nothing.
	emptyVal := *base
	emptyVal.Expect = ChargeExpect{Kind: ExpectValidation}
	if p := Admit(&emptyVal, Options{}); len(p) == 0 {
		t.Fatal("validation vector with empty codes admitted")
	}
}

func TestInvariants(t *testing.T) {
	held := AssertInvariants(nil, ChargeResult{FeePresent: true, FeeMinor: 12346})
	for _, iv := range held {
		if iv.Status != InvariantHeld {
			t.Fatalf("invariant %s = %s, want HOLD", iv.Name, iv.Status)
		}
		if iv.Assertions != 1 {
			t.Fatalf("invariant %s assertions = %d, want 1", iv.Name, iv.Assertions)
		}
	}

	both := AssertInvariants(nil, ChargeResult{FeePresent: true, FeeMinor: 5, ValidationCodes: []string{"x"}})
	if both[0].Name != "fee_requires_valid" || both[0].Status != InvariantViolated {
		t.Fatalf("fee_requires_valid = %s, want VIOLATED", both[0].Status)
	}

	neg := AssertInvariants(nil, ChargeResult{FeePresent: true, FeeMinor: -1})
	if neg[1].Name != "fee_non_negative" || neg[1].Status != InvariantViolated {
		t.Fatalf("fee_non_negative = %s, want VIOLATED", neg[1].Status)
	}

	na := AssertInvariants(nil, ChargeResult{})
	for _, iv := range na {
		if iv.Status != InvariantNotApplicable {
			t.Fatalf("invariant %s = %s, want N/A", iv.Name, iv.Status)
		}
	}
}
