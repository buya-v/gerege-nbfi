package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.savings.vector/v1"

// SavingsContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const SavingsContext = "savings"

// SeamSavingsDailyInterest is the discriminating capture seam this schema
// grades: the single-period daily-balance interest of the discriminating savings
// account, whose one-day raw interest 0.005 ties HALF_UP against HALF_EVEN.
const SeamSavingsDailyInterest = "savings-daily-interest"

// SeamSavingsAccountStatus is the account-status capture seam this schema
// grades: the m_savings_account.status_enum stored value Fineract wrote back in
// the acknowledgement of a lifecycle command on the discriminating savings
// account. The oracle observed exactly two values here — 200 after the approve
// step and 300 after the activate step — and only those two steps are
// transcriptable.
const SeamSavingsAccountStatus = "savings-account-status"

// SeamSavingsDeposit is the deposit capture seam this schema grades: what one
// observed DEPOSIT posting does to the posted balance of the discriminating
// savings account. The oracle's account read-back records the opening deposit
// of 1000.00 MNT against a zero opening balance, and the running balance
// straight after that row is 1000.00 (transactionType.id 1, entryType CREDIT).
// The deposit row is the account's FIRST row in both read-backs, so the seam
// pins that a deposit CREDITS the posted balance by its full amount and that
// the fold starts from a zero opening balance.
const SeamSavingsDeposit = "savings-deposit"

// SeamSavingsTransactions is the transaction-stream capture seam this schema
// grades: the append-only read-back of the discriminating savings accounts,
// folded to per-row running balances. The oracle's read-back already carries the
// derived running_balance column; this seam does not read that column — it
// derives the fold over the observed rows and pins the observed values, so a
// port whose deposit/posting classification differs (deposit or interest
// posting not credited, running balance folded before instead of after the row)
// goes red. Rows are transcribed in the running-balance chain order the
// read-back's recorded running balances make — the opening deposit first, then
// each posting on its posted date. On the daily account that is also the row
// (id) order; on the monthly account it is not (the read-back lists rows
// date-descending, and the account's ids are not monotonic with posting date:
// the 0.16 posting has id 2, the 0.15 posting id 3), so the transcription
// follows the recorded balance chain, never a raw array or id order. Two
// accounts are captured: the daily account (deposit 1000.00 then an interest
// posting of 0.01) and the monthly account (deposit 1000.00 then interest
// postings of 0.15 and 0.16).
const SeamSavingsTransactions = "savings-transactions"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{SavingsContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a savings vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// savings parity tally.
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

// TenantParams is the tenant context a capture was taken under. The savings
// captures were taken under the gerege tenant: HALF_UP (ordinal 4), precision
// 19, currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// DailyInterestRequest is the savings-daily-interest seam's input: the MANIFEST's
// discriminating input (balance, annual rate, day conventions and day count).
//
// The rate is the savings Percent convention — whole per cent scaled by 10^6
// (micro-per-cent), so 0.1825 % is 182500. The balance is an integer STRING in
// minor units. DaysInYear is the savings interest-calculation day-count (360 or
// 365); Days is the number of days the daily-balance interest accrues over.
type DailyInterestRequest struct {
	BalanceMinor         string `json:"balance_minor"`
	RatePerAnnumMicroPct int64  `json:"rate_per_annum_micro_pct"`
	DaysInYear           int64  `json:"days_in_year"`
	Days                 int64  `json:"days"`
}

// AccountStatusRequest is the savings-account-status seam's input: the account
// lifecycle step whose command acknowledgement the oracle captured on the
// discriminating savings account. Only the two steps the oracle was observed
// executing are admissible — "approve" and "activate" — because a parity vector
// transcribes an observed status and never extrapolates to an unobserved step.
type AccountStatusRequest struct {
	Step string `json:"step"`
}

// TransactionRow is ONE posting of the account's append-only transaction
// stream, transcribed from the oracle's account read-back (m_savings_account
// transactions). Only the cells that feed the running-balance fold are carried:
// the transaction_type_enum stored value (transactionType.id on the read-back
// row) and the row amount. Rows are transcribed in the running-balance chain
// order the read-back's recorded running balances make — the order a port must
// fold to reproduce them. On the daily account that equals the read-back's id
// order; on the monthly account it does not (the read-back lists rows
// date-descending and the ids are not monotonic with posting date: the 0.15
// posting has id 3 and precedes the 0.16 posting with id 2 in the balance
// chain).
type TransactionRow struct {
	// TypeStoredValue is transaction_type_enum: 1 DEPOSIT, 3 INTEREST_POSTING.
	// Only those two are transcriptable — the two types the captured accounts
	// carry.
	TypeStoredValue int32 `json:"type_id"`
	// AmountMinor is the row's amount as an integer STRING in minor units.
	AmountMinor string `json:"amount_minor"`
}

// TransactionStreamRequest is the savings-deposit and savings-transactions
// seams' input: the observed postings in row (id) order. For the deposit seam
// it is the opening DEPOSIT row alone; for the transactions seam it is the full
// stream of the captured account.
type TransactionStreamRequest struct {
	Transactions []TransactionRow `json:"transactions"`
}

// Request is the input the implementation is graded on. It is the union of the
// seams; a vector sets exactly one sub-request.
type Request struct {
	DailyInterest *DailyInterestRequest     `json:"daily_interest,omitempty"`
	AccountStatus *AccountStatusRequest     `json:"account_status,omitempty"`
	Stream        *TransactionStreamRequest `json:"transaction_stream,omitempty"`
}

// Expect is what the oracle produced for the request. For the daily-interest
// seam it is the single-period interest, an integer STRING in minor units; for
// the account-status seam it is the m_savings_account.status_enum stored value
// (an integer ordinal, NOT money); for the savings-deposit and
// savings-transactions seams it is the per-row running balance, one integer
// STRING in minor units per observed row, as the read-back recorded them.
type Expect struct {
	InterestMinor   string   `json:"interest_minor,omitempty"`
	StatusID        int32    `json:"status_id,omitempty"`
	RunningBalances []string `json:"running_balances,omitempty"`
}

// Vector is one savings golden vector.
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

// LoadError is one file that could not be read as a savings vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "savings") }

// DeclaresSavingsSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresSavingsSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresSavingsSchema is DeclaresSavingsSchema over a path.
func FileDeclaresSavingsSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// SavingsFilePaths walks the store root and returns the store-relative paths of
// every file that declares the savings schema, sorted. The paths are DERIVED,
// not listed, so a savings vector added or removed later needs no edit in the
// caller.
func SavingsFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one savings vector file: a raw float
// scan first, then a typed decode with unknown fields disallowed.
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

var savingsID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every savings-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "savings", savingsID, LoadVector)
}

// DuplicateCaseIDs refuses a savings population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, savingsID, "savings")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, savingsID) }
