package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.investor.vector/v1"

// InvestorContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const InvestorContext = "investor"

// SeamExternalAssetOwnerTransferRead is the one capture seam this schema
// grades: the m_external_asset_owner_transfer row as returned by the transfer
// read-back (GET /external-asset-owners/transfers?loanId=...).
const SeamExternalAssetOwnerTransferRead = "external-asset-owner-transfer-read"

// SeamExternalAssetOwnerTransferSettlement is the second capture seam this
// schema grades: the SETTLED m_external_asset_owner_transfer row together with
// its one-to-one m_external_asset_owner_transfer_details snapshot (the four
// outstanding buckets and their DERIVED total) and the journal entries the COB
// transfer step posted. The read seam above observes a PENDING transfer with NO
// details row; this seam observes an ACTIVE transfer with details present, so
// absent-versus-present is itself a graded fact, distinct from any cell value.
const SeamExternalAssetOwnerTransferSettlement = "external-asset-owner-transfer-settlement"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{InvestorContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what an investor vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// investor parity tally.
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

// TenantParams is the tenant context a capture was taken under. The investor
// captures were taken under the gerege tenant: HALF_UP (ordinal 4), precision
// 19, currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// Request is the input the implementation is graded on. The read seam is keyed
// by the loanId query parameter alone. The settlement seam names both the loan
// the transfer was read under and the transfer id whose one-to-one details
// snapshot and posted journal entries are read back.
type Request struct {
	LoanID     int64 `json:"loan_id"`
	TransferID int64 `json:"transfer_id,omitempty"`
}

// TransferDetails is the m_external_asset_owner_transfer_details row observed
// for a settled transfer, transcribed into INTEGER MINOR UNITS (MNT, 2 digits).
// The capture holds float-formatted money (106775.53); the four buckets and the
// observed total are transcribed exactly, with no arithmetic performed here.
//
// total_outstanding_minor is the oracle's stored derived total. The port's
// derivation (investor.ExternalAssetOwnerTransferDetails.DeriveTotalOutstanding)
// is the sum of the four buckets and EXCLUDES total_overpaid; a vector
// transcribed from a capture with a non-zero overpaid would be the only
// observation able to discriminate whether overpaid belongs in the total. This
// capture's overpaid is 0.0, so no such discrimination is possible here.
type TransferDetails struct {
	DetailsID int64 `json:"details_id"`

	TotalPrincipalOutstandingMinor      int64 `json:"total_principal_outstanding_minor"`
	TotalInterestOutstandingMinor       int64 `json:"total_interest_outstanding_minor"`
	TotalFeeChargesOutstandingMinor     int64 `json:"total_fee_charges_outstanding_minor"`
	TotalPenaltyChargesOutstandingMinor int64 `json:"total_penalty_charges_outstanding_minor"`
	TotalOutstandingMinor               int64 `json:"total_outstanding_minor"`
	TotalOverpaidMinor                  int64 `json:"total_overpaid_minor"`
}

// JournalSummary is the aggregate of the journal entries the COB transfer step
// posted for one transfer, transcribed from the capture's journalEntryData. All
// amounts are integer minor units. The posted amount is the
// Transfers-Suspense leg, which is the full outstanding — never
// purchase_price_ratio × outstanding. debit_total_minor == credit_total_minor is
// the double-entry fact the capture must exhibit.
type JournalSummary struct {
	EntryCount        int64 `json:"entry_count"`
	DebitTotalMinor   int64 `json:"debit_total_minor"`
	CreditTotalMinor  int64 `json:"credit_total_minor"`
	PostedAmountMinor int64 `json:"posted_amount_minor"`
}

// Expect is what the oracle produced for the request: the
// m_external_asset_owner_transfer row's identity, state and stored columns as
// returned by the transfer read-back. purchase_price_ratio is transcribed
// verbatim as a string (the port stores it as a string and performs no
// arithmetic on it); the dates are calendar-date strings exactly as the oracle
// serialised them.
//
// Empty marks a read-back whose content page is EMPTY — the oracle returned no
// transfer for the loan (transfer-read-loan-1: loanId=1 -> content [], the
// discriminating counterpart of loan 6's single row). A row vector omits Empty
// (false); an empty-page vector sets it true and states no row cells, because a
// page with no transfer has no row to transcribe and stating one would be
// fabrication.
type Expect struct {
	Empty bool `json:"empty,omitempty"`

	TransferID         int64  `json:"transfer_id"`
	OwnerExternalID    string `json:"owner_external_id"`
	LoanExternalID     string `json:"loan_external_id"`
	TransferExternalID string `json:"transfer_external_id"`
	PurchasePriceRatio string `json:"purchase_price_ratio"`
	Status             string `json:"status"`
	SettlementDate     string `json:"settlement_date"`
	EffectiveFrom      string `json:"effective_from"`
	EffectiveTo        string `json:"effective_to"`

	// Details is the m_external_asset_owner_transfer_details snapshot a settled
	// transfer carries. It is nil for the read seam (a PENDING transfer has no
	// details row) and non-nil for the settlement seam. Presence is graded: an
	// implementation that invents details where the oracle observed none, or
	// drops details the oracle observed, diverges on a fact that no cell value
	// can express.
	Details *TransferDetails `json:"details,omitempty"`
	// Journal is the aggregate of the journal entries the transfer posted. It is
	// nil for the read seam and non-nil for the settlement seam.
	Journal *JournalSummary `json:"journal,omitempty"`
}

// Vector is one investor golden vector.
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
	// CapabilitiesRequired states what this vector exercises, for the
	// capability registry's default-deny check.
	CapabilitiesRequired []string `json:"capabilities_required"`
	// GradedAgainst names the registered implementations this vector grades.
	GradedAgainst []string `json:"graded_against"`

	// Path is the store-relative path, set by LoadVector and never decoded.
	Path string `json:"-"`
}

// LoadError is one file that could not be read as an investor vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "investor") }

// DeclaresInvestorSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresInvestorSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresInvestorSchema is DeclaresInvestorSchema over a path.
func FileDeclaresInvestorSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// InvestorFilePaths walks the store root and returns the store-relative paths of
// every file that declares the investor schema, sorted. The paths are DERIVED,
// not listed, so an investor vector added or removed later needs no edit in the
// caller (the loanschedule store census).
func InvestorFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one investor vector file: a raw float
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

var investorID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every investor-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "investor", investorID, LoadVector)
}

// DuplicateCaseIDs refuses an investor population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, investorID, "investor")
}
