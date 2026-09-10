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

// journalBatchProbe builds a valid journal-entry-batch-seam vector: the loan-10
// multi-pair batch observed in journalentries-all-raw.json — disbursement pair
// L17 (100000.00 each way) plus fee pair L18 (100.00 each way) — carrying the
// per-(transaction, account) side expectation the two totals cannot see.
func journalBatchProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-journal-entry-batch",
		Title:   "probe multi-pair journal-entry batch",
		Class:   ClassParity,
		Context: LoanContext,
		Note:    "probe: transcribed from journalentries-all-raw.json pageItems for entityId 10, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLoanJournalEntryBatchBalance, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: the four loan-10 legs and their sides",
			CaptureRef:    ".softhouse/capture/gl-accounting-surface/out/journalentries-all-raw.json",
			CaptureSHA256: "a400082a1b2974ccd6ec660789810b1ba1f8812a21024da230002ffee3a9913d",
			CaptureCaseID: "L17",
		},
		TenantParams: probeTenant(),
		Request: Request{JournalEntries: []JournalEntryLeg{
			{TransactionID: "L17", Account: "OHLGR-Loan-Portfolio", EntryType: "DEBIT", AmountMinor: "10000000"},
			{TransactionID: "L17", Account: "OHLGR-Fund-Source", EntryType: "CREDIT", AmountMinor: "10000000"},
			{TransactionID: "L18", Account: "OHLGR-Income-From-Fees", EntryType: "CREDIT", AmountMinor: "10000"},
			{TransactionID: "L18", Account: "OHLGR-Fund-Source", EntryType: "DEBIT", AmountMinor: "10000"},
		}},
		Expect: Expect{
			JournalEntryDebitsMinor:  "10010000",
			JournalEntryCreditsMinor: "10010000",
			JournalEntryAccountSides: []JournalEntryAccountSideCell{
				{TransactionID: "L17", Account: "OHLGR-Loan-Portfolio", EntryType: "DEBIT"},
				{TransactionID: "L17", Account: "OHLGR-Fund-Source", EntryType: "CREDIT"},
				{TransactionID: "L18", Account: "OHLGR-Income-From-Fees", EntryType: "CREDIT"},
				{TransactionID: "L18", Account: "OHLGR-Fund-Source", EntryType: "DEBIT"},
			},
		},
		CapabilitiesRequired: []string{"journal-entry-batch-balance"},
		GradedAgainst: []string{
			"loan-go",
			"loan-wrong-journal-entry-batch-first-pair-only",
			"loan-wrong-journal-entry-batch-drops-fee-pair",
			"loan-wrong-journal-entry-batch-nets-account",
			"loan-wrong-journal-entry-batch-swaps-first-pair-sides",
			"loan-wrong-journal-entry-batch-maps-fee-to-disbursement-accounts",
		},
	}
}

// fiveLegBatchProbe builds a valid journal-entry-batch-seam vector for the
// SINGLE-transaction five-leg posting observed in
// journalentries-loan-12-after-raw.json for loan entityId 12, transactionId L53:
// four CREDIT legs, one per allocation bucket to a DISTINCT account, plus the
// single DEBIT equal to their sum. It is the shape LN-L09's admission rule has
// to admit without admitting a one-pair batch. The DEBIT is deliberately the
// LAST leg in request order: the port sees the request legs verbatim, so a port
// that walks legs two at a time drops that trailing debit, which is the
// odd-count defect this shape exists to discriminate.
func fiveLegBatchProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-five-leg-journal-entry-batch",
		Title:   "probe single-transaction five-leg repayment posting",
		Class:   ClassParity,
		Context: LoanContext,
		Note:    "probe: transcribed from journalentries-loan-12-after-raw.json pageItems for entityId 12 transactionId L53, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLoanJournalEntryBatchBalance, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: the five loan-12 L53 legs and their sides",
			CaptureRef:    ".softhouse/capture/loan12-four-bucket-allocation/out/journalentries-loan-12-after-raw.json",
			CaptureSHA256: "9024add5df2946c369719f7d83623d525ddc77df59ca3b457a586d0feed490c9",
			CaptureCaseID: "L53",
		},
		TenantParams: probeTenant(),
		Request: Request{JournalEntries: []JournalEntryLeg{
			{TransactionID: "L53", Account: "OHLGR-Loan-Portfolio", EntryType: "CREDIT", AmountMinor: "9120312"},
			{TransactionID: "L53", Account: "OHLGR-Interest-Receivable", EntryType: "CREDIT", AmountMinor: "661853"},
			{TransactionID: "L53", Account: "OHLGR-Fees-Receivable", EntryType: "CREDIT", AmountMinor: "10000"},
			{TransactionID: "L53", Account: "OHLGR-Penalties-Receivable", EntryType: "CREDIT", AmountMinor: "5700"},
			{TransactionID: "L53", Account: "OHLGR-Fund-Source", EntryType: "DEBIT", AmountMinor: "9797865"},
		}},
		Expect: Expect{
			JournalEntryDebitsMinor:  "9797865",
			JournalEntryCreditsMinor: "9797865",
			JournalEntryAccountSides: []JournalEntryAccountSideCell{
				{TransactionID: "L53", Account: "OHLGR-Loan-Portfolio", EntryType: "CREDIT"},
				{TransactionID: "L53", Account: "OHLGR-Interest-Receivable", EntryType: "CREDIT"},
				{TransactionID: "L53", Account: "OHLGR-Fees-Receivable", EntryType: "CREDIT"},
				{TransactionID: "L53", Account: "OHLGR-Penalties-Receivable", EntryType: "CREDIT"},
				{TransactionID: "L53", Account: "OHLGR-Fund-Source", EntryType: "DEBIT"},
			},
		},
		CapabilitiesRequired: []string{"journal-entry-batch-balance"},
		GradedAgainst: []string{
			"loan-go",
			"loan-wrong-journal-entry-batch-collapses-credits-to-one-account",
			"loan-wrong-journal-entry-batch-pairs-legs-two-at-a-time",
			"loan-wrong-journal-entry-batch-debit-from-first-two-credits",
		},
	}
}

// accrualBatchProbe builds a valid journal-entry-batch-seam vector for the
// SINGLE-transaction FOUR-leg accrual observed in
// journalentries-loan-12-after-raw.json for loan entityId 12, transactionId L25:
// the interest pair (DEBIT interest-receivable / CREDIT Interest-On-Loans, 921.15
// each way) plus the fee pair (DEBIT Fees-Receivable / CREDIT Income-From-Fees,
// 100.00 each way). It is the third batch shape — TWO BALANCED PAIRS in ONE
// transaction id, one pair per charge family — which neither the two-transaction
// disbursement probe nor the five-leg repayment probe has. It is admitted by the
// EXISTING multiLegDistinctCredits predicate (one transaction id, four legs, two
// distinct credit accounts); admission is not widened for it.
func accrualBatchProbe() *Vector {
	return &Vector{
		Schema:  SchemaV1,
		CaseID:  "probe-accrual-two-family-journal-entry-batch",
		Title:   "probe single-transaction two-family accrual posting",
		Class:   ClassParity,
		Context: LoanContext,
		Note:    "probe: transcribed from journalentries-loan-12-after-raw.json pageItems for entityId 12 transactionId L25, not an observation to promote",
		Oracle:  OracleStamp{Seam: SeamLoanJournalEntryBatchBalance, FineractCommit: probeCommit},
		Provenance: Provenance{
			Kind:          ProvenanceKindOracleCapture,
			Note:          "probe: the four loan-12 L25 legs and their sides",
			CaptureRef:    ".softhouse/capture/loan12-four-bucket-allocation/out/journalentries-loan-12-after-raw.json",
			CaptureSHA256: "9024add5df2946c369719f7d83623d525ddc77df59ca3b457a586d0feed490c9",
			CaptureCaseID: "L25",
		},
		TenantParams: probeTenant(),
		Request: Request{JournalEntries: []JournalEntryLeg{
			{TransactionID: "L25", Account: "OHLGR-Interest-Receivable", EntryType: "DEBIT", AmountMinor: "92115"},
			{TransactionID: "L25", Account: "OHLGR-Interest-On-Loans", EntryType: "CREDIT", AmountMinor: "92115"},
			{TransactionID: "L25", Account: "OHLGR-Income-From-Fees", EntryType: "CREDIT", AmountMinor: "10000"},
			{TransactionID: "L25", Account: "OHLGR-Fees-Receivable", EntryType: "DEBIT", AmountMinor: "10000"},
		}},
		Expect: Expect{
			JournalEntryDebitsMinor:  "102115",
			JournalEntryCreditsMinor: "102115",
			JournalEntryAccountSides: []JournalEntryAccountSideCell{
				{TransactionID: "L25", Account: "OHLGR-Interest-Receivable", EntryType: "DEBIT"},
				{TransactionID: "L25", Account: "OHLGR-Interest-On-Loans", EntryType: "CREDIT"},
				{TransactionID: "L25", Account: "OHLGR-Income-From-Fees", EntryType: "CREDIT"},
				{TransactionID: "L25", Account: "OHLGR-Fees-Receivable", EntryType: "DEBIT"},
			},
		},
		CapabilitiesRequired: []string{"journal-entry-batch-balance"},
		GradedAgainst: []string{
			"loan-go",
			"loan-wrong-journal-entry-batch-routes-accrual-income-to-one-account",
		},
	}
}

// TestJournalEntryBatchSeamGrading grades the probe with the correct port and
// with each registered wrong drive. The totals drive and the side drive are
// asserted separately: the swap must FAIL on the side cells while its two money
// cells remain the observed 10010000/10010000, which is the whole point of the
// side expectation.
func TestJournalEntryBatchSeamGrading(t *testing.T) {
	v := journalBatchProbe()
	if p := Admit(v, Options{RepoRoot: repoRoot(t)}); len(p) > 0 {
		t.Fatalf("probe should be admissible: %v", p)
	}

	// The correct port grades: 2 money cells + count + 4 legs x 3 side cells.
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	if correct.GradedCells != 15 || correct.MoneyCells != 2 {
		t.Fatalf("graded cells = %d, money = %d; want 15/2", correct.GradedCells, correct.MoneyCells)
	}

	for _, name := range v.GradedAgainst[1:] {
		wrongImpl, ok := Lookup(name)
		if !ok {
			t.Fatalf("wrong implementation %q not registered", name)
		}
		if _, bad := IsRegisteredWrong(name); !bad {
			t.Fatalf("wrong implementation %q not marked wrong", name)
		}
		red := gradeOne(v, Options{Implementation: wrongImpl})
		if red.Outcome != OutcomeFail {
			t.Fatalf("%s outcome = %s, want FAIL; diffs=%v", name, red.Outcome, red.Diffs)
		}
		if len(red.Diffs) == 0 {
			t.Fatalf("%s produced no diffs", name)
		}
	}

	// The swap is invisible to the totals: prove it on the real reconstruction
	// path, not by assertion on the drive's diff. Swapping the L17 legs leaves
	// both money cells equal to the observed totals and moves only the side cell.
	wrongImpl, ok := Lookup("loan-wrong-journal-entry-batch-swaps-first-pair-sides")
	if !ok {
		t.Fatal("swap drive not registered")
	}
	swapped, err := wrongImpl.Evaluate(v.Request)
	if err != nil {
		t.Fatalf("swap Evaluate: %v", err)
	}
	if swapped.JournalEntryDebitsMinor != "10010000" || swapped.JournalEntryCreditsMinor != "10010000" {
		t.Fatalf("swap totals = %s/%s, want the observed 10010000/10010000",
			swapped.JournalEntryDebitsMinor, swapped.JournalEntryCreditsMinor)
	}
	if swapped.JournalEntryAccountSides[0].EntryType != "CREDIT" ||
		swapped.JournalEntryAccountSides[1].EntryType != "DEBIT" {
		t.Fatalf("swap sides = %s/%s, want the L17 pair reversed to CREDIT/DEBIT",
			swapped.JournalEntryAccountSides[0].EntryType, swapped.JournalEntryAccountSides[1].EntryType)
	}
}

// TestFeeMappingDriveIsInvisibleToTotalsAndSides proves the mapping defect is a
// FOURTH, distinct shape rather than a restatement of the swap. Routing every
// L18 fee leg through the L17 disbursement accounts keeps BOTH totals AND ALL
// FOUR sides at the observed values and moves only the GL account a fee leg
// names: a fee posted to the loan portfolio instead of to income, still exactly
// balanced. That is the hole the totals, the side swap and the existing
// truncation drives all miss.
func TestFeeMappingDriveIsInvisibleToTotalsAndSides(t *testing.T) {
	impl, ok := Lookup("loan-wrong-journal-entry-batch-maps-fee-to-disbursement-accounts")
	if !ok {
		t.Fatal("mapping drive not registered")
	}
	got, err := impl.Evaluate(journalBatchProbe().Request)
	if err != nil {
		t.Fatalf("mapping Evaluate: %v", err)
	}
	if got.JournalEntryDebitsMinor != "10010000" || got.JournalEntryCreditsMinor != "10010000" {
		t.Fatalf("mapping totals = %s/%s, want the observed 10010000/10010000",
			got.JournalEntryDebitsMinor, got.JournalEntryCreditsMinor)
	}
	// The sides are exactly the observed sides; only the two L18 accounts move,
	// from the fee's own pair to the disbursement's pair.
	wantSides := []string{"DEBIT", "CREDIT", "CREDIT", "DEBIT"}
	wantAccounts := []string{
		"OHLGR-Loan-Portfolio",
		"OHLGR-Fund-Source",
		"OHLGR-Fund-Source",
		"OHLGR-Loan-Portfolio",
	}
	if len(got.JournalEntryAccountSides) != len(wantSides) {
		t.Fatalf("mapping sides has %d entries, want %d", len(got.JournalEntryAccountSides), len(wantSides))
	}
	for i, s := range got.JournalEntryAccountSides {
		if s.EntryType != wantSides[i] {
			t.Fatalf("mapping sides[%d] = %s, want %s (the defect must not move a side)",
				i, s.EntryType, wantSides[i])
		}
		if s.Account != wantAccounts[i] {
			t.Fatalf("mapping accounts[%d] = %s, want %s", i, s.Account, wantAccounts[i])
		}
	}
	// The fee pair no longer names either of its own accounts.
	if got.JournalEntryAccountSides[2].Account == "OHLGR-Income-From-Fees" ||
		got.JournalEntryAccountSides[3].Account == "OHLGR-Fund-Source" {
		t.Fatal("the fee pair must no longer name its own Income-From-Fees/Fund-Source pair")
	}

	// Through the grader, the reclassification must leave BOTH money cells at
	// the observed totals and fail only on the per-(transaction, account) side
	// list. Note the side list is compared in a canonical (transaction, account)
	// order, so the remapped L18 legs collide positionally with expected L18
	// legs and the diff can surface as an entry_type term at a collided index as
	// well as an account term. What matters, and what no total cell can see, is
	// that the reclassification never moves money: both totals stay observed and
	// the failure is confined to the side list.
	red := gradeOne(journalBatchProbe(), Options{Implementation: impl})
	if red.Outcome != OutcomeFail {
		t.Fatalf("mapping drive outcome = %s, want FAIL", red.Outcome)
	}
	if len(red.Diffs) == 0 {
		t.Fatal("mapping drive produced no diffs")
	}
	for _, d := range red.Diffs {
		if !strings.Contains(d, "journal_entry_account_sides[") {
			t.Fatalf("mapping drive escaped the side list: %s", d)
		}
	}
}

// TestJournalEntryBatchDrivesAreIsolated pins that each journal-entry-batch
// drive delegates on every other seam, so a drive reddens only the batch vector
// and the kill counts measure the drive, not collateral damage.
func TestJournalEntryBatchDrivesAreIsolated(t *testing.T) {
	other := repaymentProbe()
	for _, name := range journalBatchProbe().GradedAgainst[1:] {
		impl, ok := Lookup(name)
		if !ok {
			t.Fatalf("wrong implementation %q not registered", name)
		}
		res := gradeOne(other, Options{Implementation: impl})
		if res.Outcome != OutcomePass {
			t.Fatalf("%s reddened a repayment vector (isolation broken): %v", name, res.Diffs)
		}
	}
}

func problemsContain(problems []string, sub string) bool {
	for _, p := range problems {
		if strings.Contains(p, sub) {
			return true
		}
	}
	return false
}

// TestFiveLegJournalEntryBatchSeamGrading grades the five-leg probe with the
// correct port and each new drive. This is an ODD leg count (5) over ONE
// transaction id, so the correct grading is 2 money cells + 1 leg-count cell +
// 5 legs x 3 side cells = 18 cells.
func TestFiveLegJournalEntryBatchSeamGrading(t *testing.T) {
	v := fiveLegBatchProbe()
	if p := Admit(v, Options{RepoRoot: repoRoot(t)}); len(p) > 0 {
		t.Fatalf("five-leg probe should be admissible: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	if correct.GradedCells != 18 || correct.MoneyCells != 2 {
		t.Fatalf("graded cells = %d, money = %d; want 18/2", correct.GradedCells, correct.MoneyCells)
	}
	for _, name := range v.GradedAgainst[1:] {
		impl, ok := Lookup(name)
		if !ok {
			t.Fatalf("wrong implementation %q not registered", name)
		}
		if _, bad := IsRegisteredWrong(name); !bad {
			t.Fatalf("wrong implementation %q not marked wrong", name)
		}
		red := gradeOne(v, Options{Implementation: impl})
		if red.Outcome != OutcomeFail {
			t.Fatalf("%s outcome = %s, want FAIL; diffs=%v", name, red.Outcome, red.Diffs)
		}
		if len(red.Diffs) == 0 && red.InvariantViolations == 0 {
			t.Fatalf("%s produced no diffs and no invariant violation", name)
		}
	}
}

// TestFiveLegBatchDrivesAreDistinct pins that the three new drives are three
// DIFFERENT defects, not restatements of each other, by asserting on the real
// reconstruction path what each one moves:
//
//   - collapse: both totals stay the observed 9797865/9797865 (it still
//     balances) and the four bucket credits become ONE credit;
//   - pairs: the trailing leg (the single DEBIT, last in request order) is
//     dropped, so the debit total reads 0 while all four credits still sum to
//     9797865;
//   - partial debit: every leg is still posted and the credit total is observed
//     but the debit is only the first two credits, 9120312+661853 = 9782165.
func TestFiveLegBatchDrivesAreDistinct(t *testing.T) {
	req := fiveLegBatchProbe().Request

	collapse, ok := Lookup("loan-wrong-journal-entry-batch-collapses-credits-to-one-account")
	if !ok {
		t.Fatal("collapse drive not registered")
	}
	got, err := collapse.Evaluate(req)
	if err != nil {
		t.Fatalf("collapse Evaluate: %v", err)
	}
	if got.JournalEntryDebitsMinor != "9797865" || got.JournalEntryCreditsMinor != "9797865" {
		t.Fatalf("collapse totals = %s/%s, want the observed 9797865/9797865 (the collapse still balances)",
			got.JournalEntryDebitsMinor, got.JournalEntryCreditsMinor)
	}
	credits := 0
	for _, s := range got.JournalEntryAccountSides {
		if s.EntryType == "CREDIT" {
			credits++
		}
	}
	if credits != 1 {
		t.Fatalf("collapse left %d credit leg(s), want the four bucket credits merged into ONE", credits)
	}

	pairs, ok := Lookup("loan-wrong-journal-entry-batch-pairs-legs-two-at-a-time")
	if !ok {
		t.Fatal("pairs drive not registered")
	}
	got, err = pairs.Evaluate(req)
	if err != nil {
		t.Fatalf("pairs Evaluate: %v", err)
	}
	if got.JournalEntryDebitsMinor != "0" || got.JournalEntryCreditsMinor != "9797865" {
		t.Fatalf("pairs totals = %s/%s, want the dropped-debit 0/9797865",
			got.JournalEntryDebitsMinor, got.JournalEntryCreditsMinor)
	}
	if len(got.JournalEntryAccountSides) != 4 {
		t.Fatalf("pairs posted %d legs, want 4 (one of the odd five dropped)", len(got.JournalEntryAccountSides))
	}

	partial, ok := Lookup("loan-wrong-journal-entry-batch-debit-from-first-two-credits")
	if !ok {
		t.Fatal("partial-debit drive not registered")
	}
	got, err = partial.Evaluate(req)
	if err != nil {
		t.Fatalf("partial-debit Evaluate: %v", err)
	}
	if got.JournalEntryDebitsMinor != "9782165" || got.JournalEntryCreditsMinor != "9797865" {
		t.Fatalf("partial-debit totals = %s/%s, want 9782165/9797865",
			got.JournalEntryDebitsMinor, got.JournalEntryCreditsMinor)
	}
	if len(got.JournalEntryAccountSides) != 5 {
		t.Fatalf("partial-debit posted %d legs, want all 5 (only the debit total is short)",
			len(got.JournalEntryAccountSides))
	}
}

// TestFiveLegDrivesAreInvisibleToTwoPairBatch is the kill-count isolation for
// the new property: each new drive must leave the two-pair LN-L09 batch PASSING,
// so the drive reddens only the five-leg posting and its measured kill count is
// the five-leg vector alone. The collapse is a no-op where a transaction has one
// credit; the pairing is a no-op where every transaction has exactly two legs;
// and the partial debit happens to equal the full debit where there are exactly
// two credits and their sum is the single debit.
func TestFiveLegDrivesAreInvisibleToTwoPairBatch(t *testing.T) {
	for _, name := range fiveLegBatchProbe().GradedAgainst[1:] {
		impl, ok := Lookup(name)
		if !ok {
			t.Fatalf("wrong implementation %q not registered", name)
		}
		res := gradeOne(journalBatchProbe(), Options{Implementation: impl})
		if res.Outcome != OutcomePass {
			t.Fatalf("%s reddened the two-pair LN-L09 batch (kill count would exceed 1): %v", name, res.Diffs)
		}
	}
}

// TestAccrualBatchSeamGrading grades the accrual probe with the correct port and
// with the new drive. The correct grading is 2 money cells + 1 leg-count cell +
// 4 legs x 3 side cells = 15 cells, the same cell count as the two-pair probe:
// what changes is that all four legs share ONE transaction id and carry TWO
// distinct income credits.
func TestAccrualBatchSeamGrading(t *testing.T) {
	v := accrualBatchProbe()
	if p := Admit(v, Options{RepoRoot: repoRoot(t)}); len(p) > 0 {
		t.Fatalf("accrual probe should be admissible by the EXISTING predicate: %v", p)
	}
	correct := gradeOne(v, Options{Implementation: NewGoEvaluator()})
	if correct.Outcome != OutcomePass {
		t.Fatalf("correct impl outcome = %s, want PASS; diffs=%v", correct.Outcome, correct.Diffs)
	}
	if correct.GradedCells != 15 || correct.MoneyCells != 2 {
		t.Fatalf("graded cells = %d, money = %d; want 15/2", correct.GradedCells, correct.MoneyCells)
	}
	for _, name := range v.GradedAgainst[1:] {
		impl, ok := Lookup(name)
		if !ok {
			t.Fatalf("wrong implementation %q not registered", name)
		}
		if _, bad := IsRegisteredWrong(name); !bad {
			t.Fatalf("wrong implementation %q not marked wrong", name)
		}
		red := gradeOne(v, Options{Implementation: impl})
		if red.Outcome != OutcomeFail {
			t.Fatalf("%s outcome = %s, want FAIL; diffs=%v", name, red.Outcome, red.Diffs)
		}
		if len(red.Diffs) == 0 {
			t.Fatalf("%s produced no diffs", name)
		}
	}
}

// TestAccrualIncomeDriveIsInvisibleToTotalsAndSides proves the accrual-income
// defect is distinct from every total-based and side-based drive by asserting on
// the real reconstruction path what it moves: routing every credit of the single
// L25 transaction to its FIRST income account (Interest-On-Loans) leaves BOTH
// totals at the observed 102115/102115 and EVERY side in place, moving only the
// account the fee family's credit names. Through the grader, the failure is
// confined to the per-(transaction, account) side list — a fee family's income
// posted to the interest family's income account, still exactly balanced.
func TestAccrualIncomeDriveIsInvisibleToTotalsAndSides(t *testing.T) {
	impl, ok := Lookup("loan-wrong-journal-entry-batch-routes-accrual-income-to-one-account")
	if !ok {
		t.Fatal("accrual-income drive not registered")
	}
	got, err := impl.Evaluate(accrualBatchProbe().Request)
	if err != nil {
		t.Fatalf("accrual-income Evaluate: %v", err)
	}
	if got.JournalEntryDebitsMinor != "102115" || got.JournalEntryCreditsMinor != "102115" {
		t.Fatalf("accrual-income totals = %s/%s, want the observed 102115/102115",
			got.JournalEntryDebitsMinor, got.JournalEntryCreditsMinor)
	}
	wantSides := []string{"DEBIT", "CREDIT", "CREDIT", "DEBIT"}
	wantAccounts := []string{
		"OHLGR-Interest-Receivable",
		"OHLGR-Interest-On-Loans",
		"OHLGR-Interest-On-Loans",
		"OHLGR-Fees-Receivable",
	}
	if len(got.JournalEntryAccountSides) != len(wantSides) {
		t.Fatalf("accrual-income sides has %d entries, want %d", len(got.JournalEntryAccountSides), len(wantSides))
	}
	for i, s := range got.JournalEntryAccountSides {
		if s.EntryType != wantSides[i] {
			t.Fatalf("accrual-income sides[%d] = %s, want %s (the defect must not move a side)",
				i, s.EntryType, wantSides[i])
		}
		if s.Account != wantAccounts[i] {
			t.Fatalf("accrual-income accounts[%d] = %s, want %s", i, s.Account, wantAccounts[i])
		}
	}
	// The fee family's credit no longer names its own income account.
	if got.JournalEntryAccountSides[2].Account == "OHLGR-Income-From-Fees" {
		t.Fatal("the fee family's credit must no longer name OHLGR-Income-From-Fees")
	}

	red := gradeOne(accrualBatchProbe(), Options{Implementation: impl})
	if red.Outcome != OutcomeFail {
		t.Fatalf("accrual-income drive outcome = %s, want FAIL", red.Outcome)
	}
	if len(red.Diffs) == 0 {
		t.Fatal("accrual-income drive produced no diffs")
	}
	for _, d := range red.Diffs {
		if !strings.Contains(d, "journal_entry_account_sides[") {
			t.Fatalf("accrual-income drive escaped the side list: %s", d)
		}
	}
}

// TestAccrualDriveIsInvisibleToDisbursementAndRepayment is the kill-count
// isolation for the new property: the accrual-income drive keys on a transaction
// with MORE THAN ONE PAIR, so it must leave the two-transaction disbursement
// batch (each transaction a one-debit/one-credit pair) and the five-leg L53
// repayment (one debit, four credits) PASSING. Its measured kill count is then
// the accrual shapes alone, and the transaction-boundary mapping drive — which
// it is the intra-transaction analogue of — remains the only drive the
// two-transaction batch can measure.
func TestAccrualDriveIsInvisibleToDisbursementAndRepayment(t *testing.T) {
	const name = "loan-wrong-journal-entry-batch-routes-accrual-income-to-one-account"
	impl, ok := Lookup(name)
	if !ok {
		t.Fatal("accrual-income drive not registered")
	}
	for _, probe := range []*Vector{journalBatchProbe(), fiveLegBatchProbe()} {
		res := gradeOne(probe, Options{Implementation: impl})
		if res.Outcome != OutcomePass {
			t.Fatalf("%s reddened %s (kill count would exceed the accrual shapes): %v",
				name, probe.CaseID, res.Diffs)
		}
	}
}

// TestJournalEntryBatchAdmissionAdmitsFiveLegButRefusesSinglePair pins the
// admission boundary itself: the five-leg single-transaction posting is admitted,
// while a one-pair batch and a three-leg batch whose credits all land on ONE
// account are still refused as unable to discriminate.
func TestJournalEntryBatchAdmissionAdmitsFiveLegButRefusesSinglePair(t *testing.T) {
	base := fiveLegBatchProbe()
	if p := Admit(base, Options{RepoRoot: repoRoot(t)}); len(p) != 0 {
		t.Fatalf("five-leg single-transaction batch must be admitted: %v", p)
	}

	pair := *base
	pair.Request = Request{JournalEntries: []JournalEntryLeg{
		{TransactionID: "L53", Account: "OHLGR-Fund-Source", EntryType: "DEBIT", AmountMinor: "100"},
		{TransactionID: "L53", Account: "OHLGR-Loan-Portfolio", EntryType: "CREDIT", AmountMinor: "100"},
	}}
	pair.Expect = Expect{
		JournalEntryDebitsMinor:  "100",
		JournalEntryCreditsMinor: "100",
		JournalEntryAccountSides: []JournalEntryAccountSideCell{
			{TransactionID: "L53", Account: "OHLGR-Fund-Source", EntryType: "DEBIT"},
			{TransactionID: "L53", Account: "OHLGR-Loan-Portfolio", EntryType: "CREDIT"},
		},
	}
	if p := Admit(&pair, Options{RepoRoot: repoRoot(t)}); !problemsContain(p, "a discriminating batch carries") {
		t.Fatalf("one-pair batch must be refused as non-discriminating; problems=%v", p)
	}

	sameAcct := *base
	sameAcct.Request = Request{JournalEntries: []JournalEntryLeg{
		{TransactionID: "L53", Account: "OHLGR-Loan-Portfolio", EntryType: "CREDIT", AmountMinor: "60"},
		{TransactionID: "L53", Account: "OHLGR-Loan-Portfolio", EntryType: "CREDIT", AmountMinor: "40"},
		{TransactionID: "L53", Account: "OHLGR-Fund-Source", EntryType: "DEBIT", AmountMinor: "100"},
	}}
	sameAcct.Expect = Expect{
		JournalEntryDebitsMinor:  "100",
		JournalEntryCreditsMinor: "100",
		JournalEntryAccountSides: []JournalEntryAccountSideCell{
			{TransactionID: "L53", Account: "OHLGR-Loan-Portfolio", EntryType: "CREDIT"},
			{TransactionID: "L53", Account: "OHLGR-Loan-Portfolio", EntryType: "CREDIT"},
			{TransactionID: "L53", Account: "OHLGR-Fund-Source", EntryType: "DEBIT"},
		},
	}
	if p := Admit(&sameAcct, Options{RepoRoot: repoRoot(t)}); !problemsContain(p, "a discriminating batch carries") {
		t.Fatalf("three legs over ONE credit account must be refused as non-discriminating; problems=%v", p)
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
