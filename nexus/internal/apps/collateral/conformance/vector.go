package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.collateral.vector/v1"

// CollateralContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const CollateralContext = "collateral"

// SeamCollateralProductRead is one capture seam this schema grades: the
// m_collateral_management product row as returned by the product read-back.
const SeamCollateralProductRead = "collateral-product-read"

// SeamCollateralLinkRead is the second capture seam this schema grades: the
// m_loan_collateral row as returned by the loan-collateral read-back.
const SeamCollateralLinkRead = "collateral-link-read"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{CollateralContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a collateral vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// collateral parity tally.
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

// TenantParams is the tenant context a capture was taken under. The collateral
// captures were taken under the gerege tenant: HALF_UP (ordinal 4), precision
// 19, currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// Request is the input the implementation is graded on. It is the union of the
// two seams: the product read (product_id) and the link read (link_id). A
// product vector sets exactly product_id; a link vector sets exactly link_id.
type Request struct {
	ProductID int64 `json:"product_id"`
	LinkID    int64 `json:"link_id"`
}

// Expect is what the oracle produced for the request. For the product seam it is
// the m_collateral_management row's identity and stored columns; base_price and
// pct_to_base are integer strings of the scale-5 count. For the link seam it is
// the m_loan_collateral row's id and type_cv_id (the LoanCollateral code value).
type Expect struct {
	ID        int64  `json:"id"`
	Name      string `json:"name"`
	Quality   string `json:"quality"`
	UnitType  string `json:"unit_type"`
	Currency  string `json:"currency"`
	BasePrice string `json:"base_price"`
	PctToBase string `json:"pct_to_base"`

	TypeID int64 `json:"type_id"`
}

// Vector is one collateral golden vector.
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

// LoadError is one file that could not be read as a collateral vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "collateral") }

// DeclaresCollateralSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresCollateralSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresCollateralSchema is DeclaresCollateralSchema over a path.
func FileDeclaresCollateralSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// CollateralFilePaths walks the store root and returns the store-relative paths
// of every file that declares the collateral schema, sorted. The paths are
// DERIVED, not listed, so a collateral vector added or removed later needs no
// edit in the caller (the loanschedule store census).
func CollateralFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one collateral vector file: a raw float
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

var collateralID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every collateral-schema .json under
// it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "collateral", collateralID, LoadVector)
}

// DuplicateCaseIDs refuses a collateral population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, collateralID, "collateral")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, collateralID) }
