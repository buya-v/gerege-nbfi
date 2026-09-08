package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.shares.vector/v1"

// SharesContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const SharesContext = "shares"

// SeamShareAccount grades the share-account aggregate readback: the account
// status, the purchase lifecycle (number of shares, purchase price and amount,
// purchase status) all normalised through the port's enum and money vocabulary.
const SeamShareAccount = "share-account"

// SeamShareDividend grades the share-product dividend's dividendAmount field,
// normalised to integer minor units. The capture records the amount the oracle
// STORED (0.010000), which is the HALF_UP-rounded read-back of the 0.005 request;
// the rounding itself is a later slice and not graded here (see doc.go).
const SeamShareDividend = "share-dividend"

// SeamShareProduct grades the share-product readback (the share-product detail
// read or one row of the share-product list): the product's unit price and share
// capital normalised to integer minor units and the total share count.
const SeamShareProduct = "share-product"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{SharesContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a shares vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// shares parity tally.
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

// TenantParams is the tenant context a capture was taken under. The shares
// captures were taken under the gerege tenant: HALF_UP (ordinal 4), precision 19,
// currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// RequestKind selects which seam a request exercises.
type RequestKind string

const (
	// KindAccount is the share-account seam: the account aggregate readback or
	// one row of the share-account list.
	KindAccount RequestKind = "account"
	// KindDividend is the share-dividend seam: the share-product dividend amount
	// (and, when the capture read it back, its stored status).
	KindDividend RequestKind = "dividend"
	// KindProduct is the share-product seam: the share-product detail read or
	// one row of the share-product list.
	KindProduct RequestKind = "product"
)

// Request is the input the implementation is graded on. It is the union of the
// three seams: an account vector sets kind "account" and the account fields; a
// dividend vector sets kind "dividend" and dividend_amount; a product vector
// sets kind "product" and the product money fields. Monetary values are the
// exact decimal text the oracle stored, never a computed float.
type Request struct {
	Kind         RequestKind `json:"kind"`
	CurrencyCode string      `json:"currency_code"`

	// account seam. A purchase row is present iff purchased_shares is non-zero:
	// the account aggregate read-back carries the purchase group, a share-account
	// list row does not, so the group is graded only when the read-back showed it.
	AccountStatusID     int32  `json:"account_status_id"`
	TotalApprovedShares int64  `json:"total_approved_shares"`
	TotalPendingShares  int64  `json:"total_pending_shares"`
	PurchasedShares     int64  `json:"purchased_shares"`
	PurchasedPrice      string `json:"purchased_price"`
	PurchasedAmount     string `json:"purchased_amount"`
	PurchasedStatusID   int32  `json:"purchased_status_id"`

	// dividend seam. dividend_status_id is present iff non-zero: a dividend
	// vector whose capture read the dividend row's status back grades it.
	DividendAmount   string `json:"dividend_amount"`
	DividendStatusID int32  `json:"dividend_status_id"`

	// product seam.
	UnitPrice    string `json:"unit_price"`
	ShareCapital string `json:"share_capital"`
	TotalShares  int64  `json:"total_shares"`
}

// Expect is what the oracle produced for the request, normalised to the port's
// vocabulary: enum stored values and integer STRING minor units.
type Expect struct {
	Kind RequestKind `json:"kind"`

	AccountStatusStored   int32  `json:"account_status_stored"`
	TotalApprovedShares   int64  `json:"total_approved_shares"`
	TotalPendingShares    int64  `json:"total_pending_shares"`
	PurchasedShares       int64  `json:"purchased_shares"`
	PurchasedPriceMinor   string `json:"purchased_price_minor"`
	PurchasedAmountMinor  string `json:"purchased_amount_minor"`
	PurchasedStatusStored int32  `json:"purchased_status_stored"`

	DividendAmountMinor  string `json:"dividend_amount_minor"`
	DividendStatusStored int32  `json:"dividend_status_stored"`

	UnitPriceMinor    string `json:"unit_price_minor"`
	ShareCapitalMinor string `json:"share_capital_minor"`
	TotalShares       int64  `json:"total_shares"`
}

// Vector is one shares golden vector.
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

// LoadError is one file that could not be read as a shares vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer. It runs BEFORE any typed decoding.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "shares") }

// DeclaresSharesSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresSharesSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresSharesSchema is DeclaresSharesSchema over a path.
func FileDeclaresSharesSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// SharesFilePaths walks the store root and returns the store-relative paths of
// every file that declares the shares schema, sorted. The loanschedule loader's
// store census reads this list so it does not refuse shares vectors as unloaded.
func SharesFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one shares vector file.
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

var sharesID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every shares-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "shares", sharesID, LoadVector)
}

// DuplicateCaseIDs refuses a shares population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, sharesID, "shares")
}
