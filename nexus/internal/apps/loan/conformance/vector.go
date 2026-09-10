package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.loan.vector/v1"

// LoanContext is the ONE bounded context this schema's machinery can say anything
// about, and it is the directory name that context's vectors live in.
const LoanContext = "loan"

// SeamLoanRepaymentAllocation is the capture seam this schema grades: the
// four-bucket greedy allocation of a repayment across penalty/fee/interest/
// principal, observed on the SEED-L03 repayment.
const SeamLoanRepaymentAllocation = "loan-repayment-allocation"

// SeamLoanScheduleInterest is the discriminating capture seam: the single-period
// interest of the discriminating loan SEED-L06, whose period-1 interest ties
// HALF_UP against HALF_EVEN.
const SeamLoanScheduleInterest = "loan-schedule-interest"

// SeamLoanDisbursement is the capture seam this schema grades: the net disbursal
// amount of the SEED-L06 disbursal.
const SeamLoanDisbursement = "loan-disbursement"

// SeamLoanStatus is the capture seam this schema grades: the persisted
// loan-status ordinal as the oracle's read-back serialises it. Fineract stores
// loan status in m_loan.loan_status_id with a NON-contiguous value table — the
// active band sits at 300 with transfer sub-states at 303/304 and the closed
// band carries three 6xx values — so a port that encodes the enum as an iota
// silently collapses states. Each vector decodes one observed stored value and
// pins the status_code the read-back emitted for it (plus the round-trip stored
// value), transcribed from a capture whose status.id/code pair is the
// observation.
const SeamLoanStatus = "loan-status"

// SeamLoanTransactionBalance is the capture seam this schema grades: the
// per-transaction outstandingLoanBalance column of the loan read-back, DERIVED
// row by row from the earlier postings by
// LoanBalanceService.updateLoanOutstandingBalances. The balances track
// PRINCIPAL only: a disbursement creates principal, a repayment recognises a
// principal portion, a non-monetary accrual is excluded from the balance
// stream and its row serialises NO balance cell, and an interest waiver
// (which recognises no principal portion) leaves the balance unmoved. A
// capture that observes this column therefore pins the running derivation, the
// null-not-zero absence of a balance cell on an accrual row, and the
// "a waiver does not move the outstanding balance" consequence in one go.
const SeamLoanTransactionBalance = "loan-transaction-balance"

// SeamLoanSummaryOutstanding is the capture seam this schema grades: the loan
// summary's total outstanding, DERIVED from the four outstanding buckets the
// oracle read back. Fineract persists total_outstanding_derived; the port's
// LoanSummary keeps the bucket decomposition and derives the total
// (derive-don't-store). A port that stores the total and reads it back, or sums
// the wrong buckets, returns a total that disagrees with the observed read-back.
const SeamLoanSummaryOutstanding = "loan-summary-outstanding"

// SeamLoanJournalEntryBatchBalance is the capture seam this schema grades: the
// debit and credit totals of a loan-produced journal-entry BATCH read back from
// the journal-entries endpoint. A loan disbursement GENERATES its postings, so
// the observation is a read-back, not a posting command; the batch carries more
// than one pair when a disbursement pair and a fee pair share one loan. The
// property is TWO things at once, and the second is invisible to the first:
//
//   - sum(debits) == sum(credits), exactly, in integer minor units, summed
//     independently over EVERY leg: a port that sums only the first pair, drops
//     a pair, or nets the two legs on one account produces totals that a
//     single-pair batch cannot tell apart; and
//   - WHICH account takes WHICH side in WHICH transaction
//     (expect.journal_entry_account_sides). A port that swaps the two legs of a
//     balanced pair moves equal amounts between the sides, so the totals are
//     UNCHANGED and the batch still balances while the posting is reversed. The
//     per-(transaction, account) side list is the cell that moves.
//
// The property is per-(transaction, account), not per-account globally:
// OHLGR-Fund-Source is CREDIT in the disbursement transaction L17 and DEBIT in
// the fee transaction L18.
const SeamLoanJournalEntryBatchBalance = "loan-journal-entry-batch-balance"

// SeamLoanScheduleAmortization is the capture seam this schema grades: the
// WHOLE-schedule principal amortization of a loan read-back, the property
// "principal amortizes to zero" asserted over every repayment period at once.
// No existing seam grades it: LN-L06 grades ONE period's INTEREST, and the
// loanschedule context's vectors grade the schedule GENERATOR at a different
// seam (they do not read a loan back). The request carries the disbursed
// principal and the observed per-period principalDue components raised to
// integer minor units; the expectation is the sum of every component and the
// final outstanding principal balance. The property holds exactly when the sum
// equals the disbursed principal and the final balance is zero. A port that
// truncates a per-period principal, drops the final adjustment row, or
// reconstructs a uniform per-period component leaves a residue and goes red.
// A port that places the remainder in the wrong PERIOD preserves both the sum
// and the final balance, so this seam does NOT grade placement; no committed
// capture exposes per-period placement on a loan read-back.
const SeamLoanScheduleAmortization = "loan-schedule-amortization"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{LoanContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a loan vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// loan parity tally.
	ClassParity VectorClass = "parity"
)

// ProvenanceKindOracleCapture is the only admissible provenance.kind for a
// parity vector.
const ProvenanceKindOracleCapture = shared.ProvenanceKindOracleCapture

// OracleStamp records where and against what the expectation was captured.
type OracleStamp struct {
	Seam           string `json:"seam"`
	FineractCommit string `json:"fineract_commit"`
}

// Provenance is where a parity vector's expected values came from: a committed
// oracle capture artefact, named by repo-relative path and content hash, and the
// case id within it that was transcribed.
type Provenance struct {
	Kind          string `json:"kind"`
	Note          string `json:"note"`
	CaptureRef    string `json:"capture_ref"`
	CaptureSHA256 string `json:"capture_sha256"`
	CaptureCaseID string `json:"capture_case_id"`
	Citation      string `json:"citation"`
}

// TenantParams is the tenant context a capture was taken under. The loan
// captures were taken under the gerege tenant: HALF_UP (ordinal 4), precision
// 19, currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// AllocationMoney is the four-bucket money breakdown of a repayment allocation,
// each bucket an integer STRING in minor units.
type AllocationMoney struct {
	Penalty   string `json:"penalty"`
	Fee       string `json:"fee"`
	Interest  string `json:"interest"`
	Principal string `json:"principal"`
}

// RepaymentRequest is the loan-repayment-allocation seam's input: the outstanding
// buckets the allocation runs against and the payment amount.
type RepaymentRequest struct {
	Outstanding AllocationMoney `json:"outstanding"`
	AmountMinor string          `json:"amount_minor"`
}

// ScheduleRequest is the loan-schedule-interest seam's input: the MANIFEST's
// discriminating input (principal, annual rate per cent, day conventions).
type ScheduleRequest struct {
	PrincipalMinor  string `json:"principal_minor"`
	RatePerAnnumPct int64  `json:"rate_per_annum_pct"`
	DaysInYear      int64  `json:"days_in_year"`
	DaysInMonth     int64  `json:"days_in_month"`
}

// ScheduleAmortizationRequest is the loan-schedule-amortization seam's input:
// the principal the oracle disbursed and the observed per-period principalDue
// components of a full repayment schedule, each an integer STRING in minor
// units. Period 0 of the capture is the disbursement row and carries no
// principalDue, so the components are exactly the repayment periods that do.
// A component carrying more than 2 decimal places of significance is a
// sub-minor residue: it is REFUSED by admission (G-19 / DEC-2 predicate G-08),
// never rounded and never vectored.
type ScheduleAmortizationRequest struct {
	PrincipalDisbursedMinor  string   `json:"principal_disbursed_minor"`
	PrincipalComponentsMinor []string `json:"principal_components_minor"`
}

// DisburseRequest is the loan-disbursement seam's input: approved principal and
// charges due at disbursement.
type DisburseRequest struct {
	ApprovedPrincipalMinor        string `json:"approved_principal_minor"`
	ChargesDueAtDisbursementMinor string `json:"charges_due_at_disbursement_minor"`
}

// SummaryRequest is the loan-summary-outstanding seam's input: the four
// outstanding buckets of a loan summary read-back, each an integer STRING in
// minor units, transcribed from the capture's "summary" block.
type SummaryRequest struct {
	PrincipalOutstanding string `json:"principal_outstanding_minor"`
	InterestOutstanding  string `json:"interest_outstanding_minor"`
	FeeOutstanding       string `json:"fee_outstanding_minor"`
	PenaltyOutstanding   string `json:"penalty_outstanding_minor"`
}

// StatusRequest is the loan-status seam's input: the persisted
// m_loan.loan_status_id value (Fineract's status.id) whose read-back the vector
// pins.
type StatusRequest struct {
	StoredValue int32 `json:"stored_value"`
}

// TransactionRow is one row of the loan-transaction-balance seam's input: a
// transaction read-back row reduced to the cells the balance derivation reads.
// Type is the row's Fineract transaction_type_enum in code-suffix form —
// "disbursement", "accrual", "repayment" or "waiver", the four type codes the
// committed captures observe on the balance path. AmountMinor is the row's full
// amount; PrincipalMinor is the row's principalPortion, which the read-back
// leaves ABSENT on the observed disbursement, accrual and waiver rows and is
// therefore omitted (zero) there.
type TransactionRow struct {
	Type           string `json:"type"`
	AmountMinor    string `json:"amount_minor"`
	PrincipalMinor string `json:"principal_minor,omitempty"`
}

// JournalEntryLeg is one row of the journal-entry-batch-balance seam's input: a
// journal-entry read-back row reduced to the cells the batch derivation reads.
// TransactionID is the transaction the oracle grouped the leg under (a batch
// with more than one distinct id holds more than one pair). Account is the GL
// account the leg touched, and is what a port that nets same-account legs would
// key on. EntryType is the observed side in code-suffix form — "DEBIT" or
// "CREDIT". AmountMinor is the leg amount, an integer STRING in minor units.
type JournalEntryLeg struct {
	TransactionID string `json:"transaction_id"`
	Account       string `json:"account"`
	EntryType     string `json:"entry_type"`
	AmountMinor   string `json:"amount_minor"`
}

// JournalEntryAccountSideCell is the journal-entry-batch-balance seam's expected
// side for one (transaction_id, account) pair of the request batch. It carries
// the side in its OBSERVED code form ("DEBIT"/"CREDIT") and is the cell a
// swapped-pair port moves while the two totals stay equal.
type JournalEntryAccountSideCell struct {
	TransactionID string `json:"transaction_id"`
	Account       string `json:"account"`
	EntryType     string `json:"entry_type"`
}

// Request is the input the implementation is graded on. It is the union of the
// seams; a vector sets exactly one of the sub-requests.
type Request struct {
	Repayment      *RepaymentRequest `json:"repayment,omitempty"`
	Schedule       *ScheduleRequest  `json:"schedule,omitempty"`
	Disburse       *DisburseRequest  `json:"disburse,omitempty"`
	Summary        *SummaryRequest   `json:"summary,omitempty"`
	Status         *StatusRequest    `json:"status,omitempty"`
	Transactions   []TransactionRow  `json:"transactions,omitempty"`
	JournalEntries []JournalEntryLeg `json:"journal_entries,omitempty"`
	// ScheduleAmortization is the whole-schedule principal-amortization seam's
	// input: the disbursed principal and the observed per-period principalDue
	// components.
	ScheduleAmortization *ScheduleAmortizationRequest `json:"schedule_amortization,omitempty"`
}

// Expect is what the oracle produced for the request. For the repayment seam it
// is the allocated buckets and the leftover; for the schedule seam the
// single-period interest; for the disbursement seam the net disbursal amount;
// for the summary seam the derived total outstanding; for the status seam the
// status_code the read-back emitted plus the round-trip stored value; for the
// transaction-balance seam one per-row verdict for each request row. Every
// money field is an integer STRING in minor units.
type Expect struct {
	Allocation        *AllocationMoney `json:"allocation,omitempty"`
	LeftoverMinor     string           `json:"leftover_minor,omitempty"`
	InterestMinor     string           `json:"interest_minor,omitempty"`
	NetDisbursalMinor string           `json:"net_disbursal_minor,omitempty"`
	// SummaryTotalMinor is total_outstanding, derived from the four request
	// buckets, in integer minor-unit STRING form.
	SummaryTotalMinor string `json:"summary_total_minor,omitempty"`
	// StatusCode is the capture's status.code for the request's stored value.
	StatusCode string `json:"status_code,omitempty"`
	// StatusStoredValue is the stored value the decoded status round-trips back
	// to: m_loan.loan_status_id of the enum the port derived from the request's
	// stored value. It must equal request.status.stored_value.
	StatusStoredValue int32 `json:"status_stored_value,omitempty"`
	// TransactionRows is the transaction-balance seam's per-row verdicts, one
	// entry per request.transactions row in order.
	TransactionRows []TransactionBalanceRow `json:"transaction_rows,omitempty"`
	// JournalEntryDebitsMinor and JournalEntryCreditsMinor are the
	// journal-entry-batch seam's two derived totals, each an integer STRING in
	// minor units, summed independently over every leg of the batch.
	JournalEntryDebitsMinor  string `json:"journal_entry_debits_minor,omitempty"`
	JournalEntryCreditsMinor string `json:"journal_entry_credits_minor,omitempty"`
	// JournalEntryAccountSides is the journal-entry-batch seam's per-leg side
	// expectation, one entry per request.journal_entries leg: WHICH account
	// takes WHICH side in WHICH transaction. It is required, and it is the cell
	// a swapped-pair port moves while both totals stay equal.
	JournalEntryAccountSides []JournalEntryAccountSideCell `json:"journal_entry_account_sides,omitempty"`
	// PrincipalSumMinor is the loan-schedule-amortization seam's derived sum of
	// the per-period principal components, an integer STRING in minor units.
	PrincipalSumMinor string `json:"principal_sum_minor,omitempty"`
	// FinalPrincipalBalanceMinor is the loan-schedule-amortization seam's final
	// outstanding principal balance after the schedule is repaid, an integer
	// STRING in minor units. The property "principal amortizes to zero" holds
	// exactly when this is "0".
	FinalPrincipalBalanceMinor string `json:"final_principal_balance_minor,omitempty"`
}

// TransactionBalanceRow is the transaction-balance seam's verdict for one
// transaction row: does the read-back serialise an outstandingLoanBalance cell
// on the row, and what is its derived value. A non-monetary posting (an
// accrual) serialises NO cell — the oracle returns absent, never zero.
type TransactionBalanceRow struct {
	Serialized bool `json:"serialized"`
	// BalanceMinor is the derived balance when Serialized is true. It is empty
	// (absent) on a row the read-back leaves without a balance cell.
	BalanceMinor string `json:"balance_minor,omitempty"`
}

// Vector is one loan golden vector.
type Vector struct {
	Schema       string        `json:"schema"`
	CaseID       string        `json:"case_id"`
	Title        string        `json:"title"`
	Class        VectorClass   `json:"class"`
	Context      string        `json:"context"`
	Note         string        `json:"_note"`
	Oracle       OracleStamp   `json:"oracle"`
	Provenance   Provenance    `json:"provenance"`
	TenantParams *TenantParams `json:"tenant_params"`
	Request      Request       `json:"request"`
	Expect       Expect        `json:"expect"`
	// CapabilitiesRequired states what this vector exercises, for the capability
	// registry's default-deny check.
	CapabilitiesRequired []string `json:"capabilities_required"`
	// GradedAgainst names the registered implementations this vector grades.
	GradedAgainst []string `json:"graded_against"`

	// Path is the store-relative path, set by LoadVector and never decoded.
	Path string `json:"-"`
}

// LoadError is one file that could not be read as a loan vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "loan") }

// DeclaresLoanSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresLoanSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresLoanSchema is DeclaresLoanSchema over a path.
func FileDeclaresLoanSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// LoanFilePaths walks the store root and returns the store-relative paths of
// every file that declares the loan schema, sorted. The paths are DERIVED, not
// listed, so a loan vector added or removed later needs no edit in the caller
// (the loanschedule store census).
func LoanFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one loan vector file: a raw float scan
// first, then a typed decode with unknown fields disallowed.
func LoadVector(absPath, relPath string) (*Vector, error) {
	raw, err := os.ReadFile(absPath)
	if err != nil {
		return nil, err
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var v Vector
	if err := dec.Decode(&v); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	if dec.More() {
		return nil, fmt.Errorf("decode: trailing content after the vector object")
	}
	v.Path = relPath
	return &v, nil
}

var loanID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every loan-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "loan", loanID, LoadVector)
}

// DuplicateCaseIDs refuses a loan population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, loanID, "loan")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, loanID) }
