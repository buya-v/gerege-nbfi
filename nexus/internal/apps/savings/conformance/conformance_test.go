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

// accountStatusProbe builds a valid account-status-seam vector for the
// observed lifecycle step: the status stored value the oracle's command
// acknowledgement wrote back (approve -> 200, activate -> 300).
func accountStatusProbe(step string, statusID int32) *Vector {
	ref := ".softhouse/capture/savings/out/savings-daily-" + step + "-raw.json"
	sum := "f3144125d99583776564d32522532fc6f1fb42e3a5241953488b96405972eb81"
	caseID := "savingsAccountStatusType.approved"
	if step == "activate" {
		sum = "43ff3b0fd2508177170e0f19eba857fe9be640895e972ad78daf469548709b95"
		caseID = "savingsAccountStatusType.active"
	}
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-account-status-" + step,
		Title:   "probe account status after " + step,
		Class:   ClassParity,
		Context: SavingsContext,
		Note:    "probe: transcribed from savings-daily-" + step + "-raw.json changes.status.id, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamSavingsAccountStatus, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: status stored value of the " + step + " ack",
			CaptureRef:    ref,
			CaptureSHA256: sum,
			CaptureCaseID: caseID,
		},
		TenantParams:         probeTenant(),
		Request:              Request{AccountStatus: &AccountStatusRequest{Step: step}},
		Expect:               Expect{StatusID: statusID},
		CapabilitiesRequired: []string{"account-status-stored-value"},
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

func TestAccountStatusSeamGrading(t *testing.T) {
	cases := []struct {
		step string
		id   int32
	}{
		{"approve", 200},
		{"activate", 300},
	}
	for _, c := range cases {
		v := accountStatusProbe(c.step, c.id)
		if p := Admit(v, Options{}); len(p) > 0 {
			t.Fatalf("%s probe should be admissible: %v", c.step, p)
		}
		correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
		if correct.Outcome != OutcomePass {
			t.Fatalf("%s correct impl outcome = %s, want PASS; diffs=%v", c.step, correct.Outcome, correct.Diffs)
		}
		// The status cell is a graded enum ordinal, never a money cell.
		if correct.GradedCells != 1 || correct.MoneyCells != 0 {
			t.Fatalf("%s graded cells = %d, money = %d; want 1/0", c.step, correct.GradedCells, correct.MoneyCells)
		}

		wrongImpl, ok := Lookup("savings-wrong-iota-status-ordinal")
		if !ok {
			t.Fatal("iota-status wrong implementation not registered")
		}
		if _, bad := IsRegisteredWrong("savings-wrong-iota-status-ordinal"); !bad {
			t.Fatal("iota-status wrong implementation not marked wrong")
		}
		red := gradeOne(v, Options{Implementation: wrongImpl})
		if red.Outcome != OutcomeFail {
			t.Fatalf("%s wrong impl outcome = %s, want FAIL; diffs=%v", c.step, red.Outcome, red.Diffs)
		}
		if len(red.Diffs) == 0 {
			t.Fatalf("%s wrong impl produced no diffs", c.step)
		}
	}
}

func TestAccountStatusAdmissionDefaultDeny(t *testing.T) {
	base := accountStatusProbe("approve", 200)

	badStep := *base
	badStep.Request.AccountStatus = &AccountStatusRequest{Step: "submit"}
	if p := Admit(&badStep, Options{}); len(p) == 0 {
		t.Fatal("unobserved lifecycle step admitted")
	}

	badExpect := *base
	badExpect.Expect.StatusID = 0
	if p := Admit(&badExpect, Options{}); len(p) == 0 {
		t.Fatal("non-positive status_id admitted")
	}

	twoSubRequests := *base
	twoSubRequests.Request.DailyInterest = &DailyInterestRequest{
		BalanceMinor: "100000", RatePerAnnumMicroPct: 182500, DaysInYear: 365, Days: 1,
	}
	if p := Admit(&twoSubRequests, Options{}); len(p) == 0 {
		t.Fatal("account-status vector carrying daily_interest too admitted")
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

// streamProbe builds a valid deposit- or transactions-seam vector whose rows
// and running balances are transcribed from a committed account read-back
// capture, in the running-balance chain order the read-back records.
func streamProbe(caseID, title, seam string, ref, sha256, caseIDInCapture string, rows []TransactionRow, balances []string, caps []string) *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  caseID,
		Title:   title,
		Class:   ClassParity,
		Context: SavingsContext,
		Note:    "probe: transcribed from an account read-back capture, not an observation to promote",
		Oracle:  OracleStamp{Seam: seam, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: running-balance cells of the captured account stream",
			CaptureRef:    ref,
			CaptureSHA256: sha256,
			CaptureCaseID: caseIDInCapture,
		},
		TenantParams:         probeTenant(),
		Request:              Request{Stream: &TransactionStreamRequest{Transactions: rows}},
		Expect:               Expect{RunningBalances: balances},
		CapabilitiesRequired: caps,
		GradedAgainst:        []string{"savings-go"},
	}
}

const (
	dailyCaptureSum   = "15999be438f6d8db15d13b4eb351c6749260db7f6790cb42ce4b2af8843eddf8"
	monthlyCaptureSum = "9fbafd509cda6f462a16f4e1f7f46127c12d94b19648981f65a85fea7788ad50"
	dailyCaptureRef   = ".softhouse/capture/savings/out/savings-account-daily-raw.json"
	monthlyCaptureRef = ".softhouse/capture/savings/out/savings-account-monthly-raw.json"
)

// depositProbe is the opening DEPOSIT row of the daily account (id 2): amount
// 1000.00 against the zero opening balance, recorded running balance 1000.00.
func depositProbe() *Vector {
	return streamProbe(
		"probe-deposit-credits-100000",
		"probe deposit credits 100000 minor",
		SeamSavingsDeposit,
		dailyCaptureRef, dailyCaptureSum, "000000002",
		[]TransactionRow{{TypeStoredValue: 1, AmountMinor: "100000"}},
		[]string{"100000"},
		[]string{"deposit-credit-balance"},
	)
}

// transactionsDailyProbe is the daily account's full stream: deposit 1000.00
// (transaction id 4) then interest posting 0.01 (transaction id 5), recorded
// running balances 1000.00 then 1000.01.
func transactionsDailyProbe() *Vector {
	return streamProbe(
		"probe-daily-stream-100000-100001",
		"probe daily deposit-then-posting stream",
		SeamSavingsTransactions,
		dailyCaptureRef, dailyCaptureSum, "000000002",
		[]TransactionRow{{TypeStoredValue: 1, AmountMinor: "100000"}, {TypeStoredValue: 3, AmountMinor: "1"}},
		[]string{"100000", "100001"},
		[]string{"deposit-credit-balance", "interest-posting-credit-balance"},
	)
}

// transactionsMonthlyProbe is the monthly account's full stream: deposit 1000.00
// (transaction id 1) then interest postings 0.15 (transaction id 3, 2026-08-01)
// and 0.16 (transaction id 2, 2026-09-01), in the recorded running-balance chain
// order; recorded running balances 1000.00, 1000.15, 1000.31.
func transactionsMonthlyProbe() *Vector {
	return streamProbe(
		"probe-monthly-stream-100000-100015-100031",
		"probe monthly deposit-plus-two-postings stream",
		SeamSavingsTransactions,
		monthlyCaptureRef, monthlyCaptureSum, "000000001",
		[]TransactionRow{
			{TypeStoredValue: 1, AmountMinor: "100000"},
			{TypeStoredValue: 3, AmountMinor: "15"},
			{TypeStoredValue: 3, AmountMinor: "16"},
		},
		[]string{"100000", "100015", "100031"},
		[]string{"deposit-credit-balance", "interest-posting-credit-balance"},
	)
}

func TestDepositSeamGrading(t *testing.T) {
	v := depositProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("deposit probe should be admissible: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	if correct.GradedCells != 1 || correct.MoneyCells != 1 {
		t.Fatalf("deposit graded cells = %d, money = %d; want 1/1", correct.GradedCells, correct.MoneyCells)
	}

	for _, wrong := range []string{
		"savings-wrong-deposit-not-credited",
		"savings-wrong-running-balance-before",
	} {
		impl, ok := Lookup(wrong)
		if !ok {
			t.Fatalf("%s not registered", wrong)
		}
		if _, bad := IsRegisteredWrong(wrong); !bad {
			t.Fatalf("%s not marked wrong", wrong)
		}
		red := gradeOne(v, Options{Implementation: impl})
		if red.Outcome != OutcomeFail {
			t.Fatalf("%s outcome = %s, want FAIL; diffs=%v", wrong, red.Outcome, red.Diffs)
		}
		if len(red.Diffs) == 0 {
			t.Fatalf("%s produced no diffs", wrong)
		}
	}

	// An interest-posting-debits defect cannot show on a deposit-only stream:
	// the vector carries no posting row, so the wrong side never engages. The
	// stream vectors below catch it instead.
	if impl, ok := Lookup("savings-wrong-interest-posting-debits"); ok {
		if green := gradeOne(v, Options{Implementation: impl}); green.Outcome != OutcomePass {
			t.Fatalf("interest-posting-debits impl outcome = %s on a deposit-only stream, want PASS; diffs=%v",
				green.Outcome, green.Diffs)
		}
	}
}

func TestTransactionsSeamGrading(t *testing.T) {
	cases := []struct {
		name string
		v    *Vector
		rows int
	}{
		{"daily", transactionsDailyProbe(), 2},
		{"monthly", transactionsMonthlyProbe(), 3},
	}
	wrongImpls := []string{
		"savings-wrong-deposit-not-credited",
		"savings-wrong-interest-posting-debits",
		"savings-wrong-running-balance-before",
	}
	for _, c := range cases {
		if p := Admit(c.v, Options{}); len(p) > 0 {
			t.Fatalf("%s probe should be admissible: %v", c.name, p)
		}
		correct := gradeOne(c.v, Options{Implementation: NewGoEvaluator()})
		if correct.Outcome != OutcomePass {
			t.Fatalf("%s correct impl outcome = %s, want PASS; diffs=%v", c.name, correct.Outcome, correct.Diffs)
		}
		if correct.GradedCells != c.rows || correct.MoneyCells != c.rows {
			t.Fatalf("%s graded cells = %d, money = %d; want %d/%d",
				c.name, correct.GradedCells, correct.MoneyCells, c.rows, c.rows)
		}
		for _, wrong := range wrongImpls {
			impl, ok := Lookup(wrong)
			if !ok {
				t.Fatalf("%s not registered", wrong)
			}
			red := gradeOne(c.v, Options{Implementation: impl})
			if red.Outcome != OutcomeFail {
				t.Fatalf("%s: %s outcome = %s, want FAIL; diffs=%v", c.name, wrong, red.Outcome, red.Diffs)
			}
			if len(red.Diffs) == 0 {
				t.Fatalf("%s: %s produced no diffs", c.name, wrong)
			}
		}
	}
}

func TestStreamSeamAdmissionDefaultDeny(t *testing.T) {
	base := transactionsDailyProbe()

	depositSubRequest := *base
	depositSubRequest.Request.DailyInterest = &DailyInterestRequest{
		BalanceMinor: "100000", RatePerAnnumMicroPct: 182500, DaysInYear: 365, Days: 1,
	}
	if p := Admit(&depositSubRequest, Options{}); len(p) == 0 {
		t.Fatal("transactions vector carrying daily_interest too admitted")
	}

	depositSeamMultiRow := *depositProbe()
	depositSeamMultiRow.Request.Stream.Transactions = append(depositSeamMultiRow.Request.Stream.Transactions,
		TransactionRow{TypeStoredValue: 3, AmountMinor: "1"})
	depositSeamMultiRow.Expect.RunningBalances = []string{"100000", "100001"}
	if p := Admit(&depositSeamMultiRow, Options{}); len(p) == 0 {
		t.Fatal("deposit seam vector carrying more than the opening deposit row admitted")
	}

	badType := *base
	badType.Request.Stream.Transactions = []TransactionRow{{TypeStoredValue: 2, AmountMinor: "100000"}}
	if p := Admit(&badType, Options{}); len(p) == 0 {
		t.Fatal("unobserved transaction type admitted")
	}

	emptyStream := *base
	emptyStream.Request.Stream.Transactions = nil
	if p := Admit(&emptyStream, Options{}); len(p) == 0 {
		t.Fatal("empty transaction stream admitted")
	}

	balanceCountMismatch := *base
	balanceCountMismatch.Expect.RunningBalances = []string{"100000"}
	if p := Admit(&balanceCountMismatch, Options{}); len(p) == 0 {
		t.Fatal("running-balance cell count not matching the row count admitted")
	}
}
