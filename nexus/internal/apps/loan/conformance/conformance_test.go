package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Every Vector built in this file is a PROBE: its numbers are transcribed from
// the committed loan captures but it is never written to the store. It exists
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

// repaymentProbe builds a valid repayment-seam vector: the SEED-L03 first
// instalment (interest 1000.00 + principal 7884.88) allocated against the
// 8884.88 repayment, transcribed from loan-3-schedule-raw.json periods[1] and
// loan-3-transactions-after-raw.json transaction 12.
func repaymentProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-repayment-allocation",
		Title:   "probe repayment allocation",
		Class:   ClassParity,
		Context: LoanContext,
		Note:    "probe: transcribed from loan-3-schedule-raw.json and loan-3-transactions-after-raw.json, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLoanRepaymentAllocation, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: interestPortion/principalPortion of the SEED-L03 repayment transaction",
			CaptureRef:    ".softhouse/capture/loan/out/loan-3-transactions-after-raw.json",
			CaptureSHA256: "d3d99d995ab050df37ec67bfd40bf96b11f86b1f0b503225883a5a6c1b3f7c0b",
			CaptureCaseID: "SEED-L03",
		},
		TenantParams: probeTenant(),
		Request: Request{Repayment: &RepaymentRequest{
			Outstanding: AllocationMoney{
				Penalty:   "0",
				Fee:       "0",
				Interest:  "100000",
				Principal: "788488",
			},
			AmountMinor: "888488",
		}},
		Expect: Expect{
			Allocation: &AllocationMoney{
				Penalty:   "0",
				Fee:       "0",
				Interest:  "100000",
				Principal: "788488",
			},
			LeftoverMinor: "0",
		},
		CapabilitiesRequired: []string{"repayment-allocation"},
		GradedAgainst:        []string{"loan-go"},
	}
}

// scheduleProbe builds a valid schedule-seam vector: the discriminating cell of
// the SEED-L06 loan, period-1 interest 1000.505 -> HALF_UP 1000.51.
func scheduleProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-schedule-interest",
		Title:   "probe schedule interest",
		Class:   ClassParity,
		Context: LoanContext,
		Note:    "probe: transcribed from loan-L06-schedule-raw.json periods[1].interestOriginalDue, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLoanScheduleInterest, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: period-1 interestOriginalDue of the discriminating loan SEED-L06",
			CaptureRef:    ".softhouse/capture/loan/out/loan-L06-schedule-raw.json",
			CaptureSHA256: "b64596033dacf3b74249633e07df6cc5a22368061b2ae899a078504317519281",
			CaptureCaseID: "SEED-L06",
		},
		TenantParams: probeTenant(),
		Request: Request{Schedule: &ScheduleRequest{
			PrincipalMinor:  "10005050",
			RatePerAnnumPct: 12,
			DaysInYear:      360,
			DaysInMonth:     30,
		}},
		Expect:               Expect{InterestMinor: "100051"},
		CapabilitiesRequired: []string{"schedule-interest-rounding"},
		GradedAgainst:        []string{"loan-go"},
	}
}

// disburseProbe builds a valid disbursement-seam vector: the SEED-L06 net
// disbursal (approved 100050.50, no charges, net 100050.50).
func disburseProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-disbursement",
		Title:   "probe disbursement",
		Class:   ClassParity,
		Context: LoanContext,
		Note:    "probe: transcribed from loan-L06-detail-raw.json netDisbursalAmount, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLoanDisbursement, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: netDisbursalAmount of the SEED-L06 disbursal",
			CaptureRef:    ".softhouse/capture/loan/out/loan-L06-detail-raw.json",
			CaptureSHA256: "096f2d90a922f51e498e546323b67edf4c910c0573f4a6083141cf81d7ef6b30",
			CaptureCaseID: "SEED-L06",
		},
		TenantParams: probeTenant(),
		Request: Request{Disburse: &DisburseRequest{
			ApprovedPrincipalMinor:        "10005050",
			ChargesDueAtDisbursementMinor: "0",
		}},
		Expect:               Expect{NetDisbursalMinor: "10005050"},
		CapabilitiesRequired: []string{"disbursement-net"},
		GradedAgainst:        []string{"loan-go"},
	}
}

func TestEmptyStoreRefuses(t *testing.T) {
	store := t.TempDir()
	s, err := Run(context.Background(), Options{
		RepoRoot:           repoRoot(t),
		StoreRoot:          store,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "loan-go",
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

func TestNoFloatInTheLoanTree(t *testing.T) {
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

func TestRepaymentSeamGrading(t *testing.T) {
	v := repaymentProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	if correct.GradedCells != 5 || correct.MoneyCells != 5 {
		t.Fatalf("repayment graded cells = %d, money = %d; want 5/5", correct.GradedCells, correct.MoneyCells)
	}
}

func TestScheduleSeamGrading(t *testing.T) {
	v := scheduleProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}

	wrongImpl, ok := Lookup("loan-wrong-half-even-schedule-interest")
	if !ok {
		t.Fatal("wrong implementation not registered")
	}
	if _, bad := IsRegisteredWrong("loan-wrong-half-even-schedule-interest"); !bad {
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

func TestDisburseSeamGrading(t *testing.T) {
	v := disburseProbe()
	if p := Admit(v, Options{}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
}

// seedL01Transactions is the SEED-L01 posting stream observed in
// loan-1-transactions-after-raw.json, reduced to the balance-derivation cells
// (disbursement 100000.00; accrual 6618.53; waive-interest 1000.00, balance
// unmoved at 100000.00 because the waiver recognises no principal).
var seedL01Transactions = []TransactionRow{
	{Type: "disbursement", AmountMinor: "10000000"},
	{Type: "accrual", AmountMinor: "661853"},
	{Type: "waiver", AmountMinor: "100000"},
}

// seedL03Transactions is the SEED-L03 posting stream observed in
// loan-3-transactions-after-raw.json (disbursement 100000.00; accrual 6618.53;
// repayment 8884.88 recognising principal 7884.88, balance 92115.12).
var seedL03Transactions = []TransactionRow{
	{Type: "disbursement", AmountMinor: "10000000"},
	{Type: "accrual", AmountMinor: "661853"},
	{Type: "repayment", AmountMinor: "888488", PrincipalMinor: "788488"},
}

func transactionBalanceVector(caseID string, rows []TransactionRow, want []TransactionBalanceRow, captureRef, captureSha, caseLabel, citation string) *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  caseID,
		Title:   "probe: derived outstandingLoanBalance column",
		Class:   ClassParity,
		Context: "loan",
		Note:    "probe: transcribed from " + captureRef + ", not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLoanTransactionBalance, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          "oracle-capture",
			Note:          "probe: rows and balances transcribed from " + captureRef,
			CaptureRef:    captureRef,
			CaptureSHA256: captureSha,
			CaptureCaseID: caseLabel,
			Citation:      citation,
		},
		TenantParams:         probeTenant(),
		Request:              Request{Transactions: rows},
		Expect:               Expect{TransactionRows: want},
		CapabilitiesRequired: []string{"transaction-balance"},
		GradedAgainst:        []string{"loan-go"},
	}
}

func TestTransactionBalanceSeamGrading(t *testing.T) {
	// SEED-L01: disbursement, accrual, waiver. The accrual row serialises NO
	// balance cell and the waiver leaves the balance unmoved at 100000.00.
	l01 := transactionBalanceVector(
		"probe-transaction-balance-l01",
		seedL01Transactions,
		[]TransactionBalanceRow{
			{Serialized: true, BalanceMinor: "10000000"},
			{Serialized: false},
			{Serialized: true, BalanceMinor: "10000000"},
		},
		".softhouse/capture/loan/out/loan-1-transactions-after-raw.json",
		"4a74f23eba3f56e9c3b52699097d9c5330bb950a41e2cc196694d13116ecb47f",
		"SEED-L01",
		`loan-1-transactions-after-raw.json {"id":13,"type":{"code":"loanTransactionType.waiver"},"amount":1000.0,"principalPortion":null,"interestPortion":1000.0,"outstandingLoanBalance":100000.0}`,
	)
	// SEED-L03: disbursement, accrual, repayment. Same absent accrual balance;
	// the repayment moves the running balance by its 7884.88 principal portion.
	l03 := transactionBalanceVector(
		"probe-transaction-balance-l03",
		seedL03Transactions,
		[]TransactionBalanceRow{
			{Serialized: true, BalanceMinor: "10000000"},
			{Serialized: false},
			{Serialized: true, BalanceMinor: "9211512"},
		},
		".softhouse/capture/loan/out/loan-3-transactions-after-raw.json",
		"054b73bb9f2cc2e513d76a181aecae96226a2aaa1adde89390176abda45f5f46",
		"SEED-L03",
		`loan-3-transactions-after-raw.json {"id":12,"type":{"code":"loanTransactionType.repayment"},"amount":8884.88,"principalPortion":7884.88,"interestPortion":1000.0,"outstandingLoanBalance":92115.12}`,
	)

	for _, v := range []*Vector{l01, l03} {
		if p := Admit(v, Options{}); len(p) > 0 {
			t.Fatalf("probe %s should be admissible: %v", v.CaseID, p)
		}
		correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
		if correct.Outcome != OutcomePass {
			t.Fatalf("correct impl on %s = %s, want PASS; diffs=%v", v.CaseID, correct.Outcome, correct.Diffs)
		}
		// Three rows: one count cell, three serialization cells, and two money
		// cells (the two serialized balances).
		if correct.GradedCells != 6 || correct.MoneyCells != 2 {
			t.Fatalf("%s graded cells = %d, money = %d; want 6/2", v.CaseID, correct.GradedCells, correct.MoneyCells)
		}
	}

	wrongWaiver, _ := Lookup("loan-wrong-transaction-balance-waiver-moves-principal")
	wrongAccrual, _ := Lookup("loan-wrong-transaction-balance-accrual-zero")
	wrongRepayment, _ := Lookup("loan-wrong-transaction-balance-folds-repayment-interest")

	red := gradeOne(l01, Options{Implementation: wrongWaiver})
	if red.Outcome != OutcomeFail || len(red.Diffs) == 0 {
		t.Fatalf("waiver drive on l01 = %s (diffs %v), want FAIL", red.Outcome, red.Diffs)
	}
	// The waiver drive observes no waiver on the SEED-L03 stream: it must stay green there.
	if pass := gradeOne(l03, Options{Implementation: wrongWaiver}); pass.Outcome != OutcomePass {
		t.Fatalf("waiver drive on l03 = %s, want PASS (isolated to the waiver-bearing vector)", pass.Outcome)
	}
	for _, v := range []*Vector{l01, l03} {
		red := gradeOne(v, Options{Implementation: wrongAccrual})
		if red.Outcome != OutcomeFail || len(red.Diffs) == 0 {
			t.Fatalf("accrual-zero drive on %s = %s (diffs %v), want FAIL", v.CaseID, red.Outcome, red.Diffs)
		}
	}
	red = gradeOne(l03, Options{Implementation: wrongRepayment})
	if red.Outcome != OutcomeFail || len(red.Diffs) == 0 {
		t.Fatalf("folds-interest drive on l03 = %s (diffs %v), want FAIL", red.Outcome, red.Diffs)
	}
	if pass := gradeOne(l01, Options{Implementation: wrongRepayment}); pass.Outcome != OutcomePass {
		t.Fatalf("folds-interest drive on l01 = %s, want PASS (isolated to the repayment-bearing vector)", pass.Outcome)
	}
}

func TestCapabilityRegistryDefaultDeny(t *testing.T) {
	r := &CapabilityRegistry{
		byName: map[string]Capability{
			"repayment-allocation":       {Name: "repayment-allocation", InGradedDomain: true, Evidence: "loan-3-transactions-after-raw.json"},
			"schedule-interest-rounding": {Name: "schedule-interest-rounding", InGradedDomain: true, Evidence: "loan-L06-schedule-raw.json"},
			"disbursement-net":           {Name: "disbursement-net", InGradedDomain: true, Evidence: "loan-L06-detail-raw.json"},
			"interest-waiver":            {Name: "interest-waiver", InGradedDomain: false, Evidence: "no loan-slice interest-waiver arithmetic"},
		},
		bySeam: map[string]Seam{
			SeamLoanRepaymentAllocation: {Name: SeamLoanRepaymentAllocation, Status: map[string]SeamStatus{
				"repayment-allocation": StatusExercised,
			}},
			SeamLoanScheduleInterest: {Name: SeamLoanScheduleInterest, Status: map[string]SeamStatus{
				"schedule-interest-rounding": StatusExercised,
			}},
			SeamLoanDisbursement: {Name: SeamLoanDisbursement, Status: map[string]SeamStatus{
				"disbursement-net": StatusExercised,
			}},
		},
	}

	if v := r.Assess(SeamLoanScheduleInterest, []string{"schedule-interest-rounding"}); !v.Gradeable {
		t.Fatalf("exercised+graded should be gradeable: %v", v.Detail)
	}
	if v := r.Assess("unknown-seam", []string{"repayment-allocation"}); v.Gradeable || v.Reason != reasonUnknownSeam {
		t.Fatalf("unknown seam should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownSeam, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamLoanScheduleInterest, nil); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("empty required should refuse with reason %q, got gradeable=%v reason=%q", reasonUnknownCapability, v.Gradeable, v.Reason)
	}
	if v := r.Assess(SeamLoanScheduleInterest, []string{"nope"}); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("unknown capability should refuse with reason %q, got %q", reasonUnknownCapability, v.Reason)
	}
	if v := r.Assess(SeamLoanRepaymentAllocation, []string{"interest-waiver"}); v.Gradeable || v.Reason != reasonUnknownCapability {
		t.Fatalf("out-of-domain capability should refuse with reason %q, got %q", reasonUnknownCapability, v.Reason)
	}
}

func TestAdmitDefaultDeny(t *testing.T) {
	base := scheduleProbe()

	badSchema := *base
	badSchema.Schema = "gerege.loan.vector/v2"
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

	// A schedule vector that also carries a repayment sub-request is refused.
	both := *base
	both.Request = Request{
		Schedule:  base.Request.Schedule,
		Repayment: &RepaymentRequest{Outstanding: AllocationMoney{Penalty: "0", Fee: "0", Interest: "0", Principal: "0"}, AmountMinor: "0"},
	}
	if p := Admit(&both, Options{}); len(p) == 0 {
		t.Fatal("schedule seam with repayment sub-request admitted")
	}

	// A fractional money string is refused on the raw pass and the typed pass.
	frac := *base
	frac.Request.Schedule.PrincipalMinor = "100050.50"
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
	rep := &Vector{Oracle: OracleStamp{Seam: SeamLoanRepaymentAllocation}}
	held := AssertInvariants(rep, Expect{
		Allocation:    &AllocationMoney{Penalty: "0", Fee: "0", Interest: "100000", Principal: "788488"},
		LeftoverMinor: "0",
	})
	if held[0].Status != InvariantHeld {
		t.Fatalf("allocation_non_negative = %s, want HOLD", held[0].Status)
	}

	viol := AssertInvariants(rep, Expect{
		Allocation:    &AllocationMoney{Penalty: "0", Fee: "0", Interest: "-5", Principal: "788488"},
		LeftoverMinor: "0",
	})
	if viol[0].Status != InvariantViolated {
		t.Fatalf("allocation_non_negative = %s, want VIOLATED", viol[0].Status)
	}

	sched := &Vector{Oracle: OracleStamp{Seam: SeamLoanScheduleInterest}}
	if invs := AssertInvariants(sched, Expect{InterestMinor: "-1"}); invs[0].Status != InvariantViolated {
		t.Fatalf("interest_non_negative = %s, want VIOLATED", invs[0].Status)
	}
	if invs := AssertInvariants(sched, Expect{InterestMinor: "100051"}); invs[0].Status != InvariantHeld {
		t.Fatalf("interest_non_negative = %s, want HOLD", invs[0].Status)
	}
}
