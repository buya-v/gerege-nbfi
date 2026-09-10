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

// SeamSavingsHoldRelease is the hold/release capture seam CLAUDE.md line 14
// makes non-negotiable: "Holds are postings and alter `available` only, never
// posted `balance`." The observation is the three-point read-back of savings
// account 1 (id 1, accountNo 000000001) in savings-hold-release/: before
// (balance 1000.31, available 1000.31), after an AMOUNT_HOLD of 137.29 (balance
// STILL 1000.31, available 863.02), and after its AMOUNT_RELEASE (balance still
// 1000.31, available restored to 1000.31). The port derives three cells from
// the observed append-only stream — AccountBalanceOf, HeldOf and AvailableOf —
// and this seam pins all three against the oracle's read-back, so all four
// limbs of the rule are graded: (1) the hold posts a transaction (type 20,
// amountHold); (2) available falls by the held amount; (3) the posted balance
// does NOT move; (4) release restores available with the balance still unmoved.
//
// WHY TWO VECTORS AND NOT ONE. A single stream carrying both hold and release
// folds the hold and the release into the posted balance net-zero (part 3 would
// hold trivially) and leaves available at its unheld value, so the natural
// mistake — folding the hold into the posted balance — is INVISIBLE: it reports
// the correct available as its balance and the correct balance as nothing at
// all. The after-hold state is the observation that distinguishes them, and the
// after-release state is the one that pins restoration; both are on this seam.
const SeamSavingsHoldRelease = "savings-hold-release"

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

// HoldReleaseRow is ONE posting of the hold/release account's append-only
// stream, transcribed from the oracle's account read-back (m_savings_account
// transactions). Unlike TransactionRow it carries the two facts the hold
// algebra is built on beyond the amount and the type: the row's own id, and
// (on an AMOUNT_HOLD row) the id of the AMOUNT_RELEASE row that released it
// (release_id_of_hold_amount). Fineract pairs a release to its hold by writing
// the release row's id onto the HOLD row, not by matching amounts
// [VERIFIED: SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953], so
// the pairing is only expressible if both ids are transcribed.
type HoldReleaseRow struct {
	// ID is m_savings_account_transaction.id of the posting.
	ID int64 `json:"id"`
	// TypeStoredValue is transaction_type_enum: 1 DEPOSIT, 3 INTEREST_POSTING,
	// 20 AMOUNT_HOLD, 21 AMOUNT_RELEASE — the four types the captured account
	// carries.
	TypeStoredValue int32 `json:"type_id"`
	// AmountMinor is the row's amount as an integer STRING in minor units.
	AmountMinor string `json:"amount_minor"`
	// ReleaseIDOfHoldAmount is release_id_of_hold_amount on an AMOUNT_HOLD row:
	// the id of the releasing AMOUNT_RELEASE row, or 0 while the hold is
	// outstanding. It is 0 on every other row type.
	ReleaseIDOfHoldAmount int64 `json:"release_id_of_hold_amount"`
}

// HoldReleaseRequest is the savings-hold-release seam's input: the observed
// append-only stream of savings account 1 in id order — (1,2,3,6) after the
// hold, (1,2,3,6,7) after the release — so the posted-balance fold, the held
// fold and available are all derived from the same observed rows.
type HoldReleaseRequest struct {
	Transactions []HoldReleaseRow `json:"transactions"`
}

// Request is the input the implementation is graded on. It is the union of the
// seams; a vector sets exactly one sub-request.
type Request struct {
	DailyInterest *DailyInterestRequest     `json:"daily_interest,omitempty"`
	AccountStatus *AccountStatusRequest     `json:"account_status,omitempty"`
	Stream        *TransactionStreamRequest `json:"transaction_stream,omitempty"`
	HoldRelease   *HoldReleaseRequest       `json:"hold_release,omitempty"`
}

// Expect is what the oracle produced for the request. For the daily-interest
// seam it is the single-period interest, an integer STRING in minor units; for
// the account-status seam it is the m_savings_account.status_enum stored value
// (an integer ordinal, NOT money); for the savings-deposit and
// savings-transactions seams it is the per-row running balance, one integer
// STRING in minor units per observed row, as the read-back recorded them; for
// the savings-hold-release seam it is the three derived cells of the account's
// observed state — AccountBalanceMinor (summary.accountBalance, the posted
// balance), HeldMinor (the transaction-stream hold derived from the AMOUNT_HOLD
// rows, which the read-back exposes only on the row and in
// total_savings_amount_on_hold) and AvailableMinor (summary.availableBalance,
// which the oracle derives as balance less held).
type Expect struct {
	InterestMinor       string   `json:"interest_minor,omitempty"`
	StatusID            int32    `json:"status_id,omitempty"`
	RunningBalances     []string `json:"running_balances,omitempty"`
	AccountBalanceMinor string   `json:"account_balance_minor,omitempty"`
	HeldMinor           string   `json:"held_minor,omitempty"`
	AvailableMinor      string   `json:"available_minor,omitempty"`
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
