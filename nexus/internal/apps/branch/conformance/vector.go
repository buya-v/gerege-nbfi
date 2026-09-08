package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.branch.vector/v1"

// BranchContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const BranchContext = "branch"

// SeamCashierTxnAmount is a capture seam this schema grades: the
// m_cashier_transactions row produced by an allocate/settle cash movement, whose
// txn_amount the port normalises to integer minor units with no rounding surface.
const SeamCashierTxnAmount = "cashier-txn-amount"

// SeamCashierSummary is a capture seam this schema grades: the cashier summary
// read-back (GET /cashiers/{cashierId}/summary) of the m_cashier_transactions
// row set. The row set is a three-point series — the same cashier read at the
// pre, post and final moments of the allocate/settle run — and each read-back's
// sumCashAllocation / sumCashSettlement / netCash buckets are derived from the
// rows by the port's summary fold.
const SeamCashierSummary = "cashier-summary"

// SeamTellerStatus is a capture seam this schema grades: the m_tellers.state
// stored value behind the teller list's status label. The list serialises the
// state enum as its display label ("ACTIVE"); the port's TellerStatus enum maps
// the label to the stored integer the read-back stands for.
const SeamTellerStatus = "teller-status"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{BranchContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a branch vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// branch parity tally.
	ClassParity VectorClass = "parity"
)

// ProvenanceKindOracleCapture is the only admissible provenance.kind for a
// parity vector: its expected values were transcribed from an oracle capture,
// never computed by the promotion.
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
}

// TenantParams is the tenant context a capture was taken under. The branch
// captures were taken under the gerege tenant: HALF_UP (ordinal 4), precision 19,
// currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// CashierSummaryRow is one m_cashier_transactions row of a summary request: its
// observed transaction type (101 allocate, 102 settle, 103 cash in, 104 cash
// out) and its observed DECIMAL(19,6) amount as exact decimal text, in the order
// the read-back listed them.
type CashierSummaryRow struct {
	ID        int32  `json:"id"`
	TxnType   int32  `json:"txn_type"`
	TxnAmount string `json:"txn_amount"`
}

// SummaryRequest is the cashier-summary seam's input: the row set a summary
// read-back was taken from. The port folds the rows into the four till buckets
// and derives the net till cash, so the graded cells are the read-back's bucket
// sums transcribed from the capture.
type SummaryRequest struct {
	Rows []CashierSummaryRow `json:"rows"`
}

// TellerStatusRequest is the teller-status seam's input: the status label the
// teller list read-back serialised.
type TellerStatusRequest struct {
	StatusLabel string `json:"status_label"`
}

// Request is the input the implementation is graded on. A vector sets exactly
// one of the three seams: the cashier-transaction cash movement (TxnType +
// TxnAmount + CurrencyCode, the cashier-txn-amount seam), the cashier summary
// row set (CashierSummary, the cashier-summary seam), or the teller status label
// (TellerStatus, the teller-status seam). Monetary values are the exact decimal
// text the oracle received or stored, never a computed float.
type Request struct {
	TxnType      int32                `json:"txn_type"`
	TxnAmount    string               `json:"txn_amount"`
	CurrencyCode string               `json:"currency_code"`
	Summary      *SummaryRequest      `json:"cashier_summary,omitempty"`
	TellerStatus *TellerStatusRequest `json:"teller_status,omitempty"`
}

// Expect is what the oracle produced for the request, normalised to the port's
// vocabulary. The cashier-txn-amount seam fills the transaction type as stored
// (id + display value) and the amount as an INTEGER STRING of minor units; the
// cashier-summary seam fills the three bucket sums as integer minor-unit
// strings; the teller-status seam fills the stored state integer. Money is
// integer minor units, never a float.
type Expect struct {
	TxnTypeID      int32  `json:"txn_type_id"`
	TxnTypeValue   string `json:"txn_type_value"`
	TxnAmountMinor string `json:"txn_amount_minor"`

	SumCashAllocation string `json:"sum_cash_allocation,omitempty"`
	SumCashSettlement string `json:"sum_cash_settlement,omitempty"`
	NetCash           string `json:"net_cash,omitempty"`

	TellerStatusStored int32 `json:"teller_status_stored,omitempty"`
}

// Vector is one branch golden vector.
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

// LoadError is one file that could not be read as a branch vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer. It runs BEFORE any typed decoding.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "branch") }

// DeclaresBranchSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresBranchSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresBranchSchema is DeclaresBranchSchema over a path.
func FileDeclaresBranchSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// BranchFilePaths walks the store root and returns the store-relative paths of
// every file that declares the branch schema, sorted.
func BranchFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one branch vector file.
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

var branchID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every branch-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "branch", branchID, LoadVector)
}

// DuplicateCaseIDs refuses a branch population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, branchID, "branch")
}
