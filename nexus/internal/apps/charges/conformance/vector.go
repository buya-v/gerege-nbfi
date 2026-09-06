package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.charges.vector/v1"

// ChargesContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const ChargesContext = "charges"

// SeamChargeEvaluate is the one capture seam this schema grades: a charge
// definition and a base amount in, validation codes or a fee amount out.
const SeamChargeEvaluate = "charge-evaluate"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
//
// A vector's schema, its directory and the comparator that grades it name ONE
// context, and the check is stated in both directions so that copying a vector
// into a new directory and changing two strings cannot raise a parity count.
func SchemaContexts() []string { return []string{ChargesContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a charges vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// charges parity tally.
	ClassParity VectorClass = "parity"
)

// ExpectKind distinguishes the two shapes an oracle observation can take.
type ExpectKind string

const (
	// ExpectValidation expects an ordered list of construction-validation codes.
	ExpectValidation ExpectKind = "validation"

	// ExpectFee expects a valid charge and a computed fee in integer minor units.
	ExpectFee ExpectKind = "fee"
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
// case id within it that was transcribed. A parity vector is a TRANSCRIPTION,
// never a computation, so provenance is mandatory: capture_ref and
// capture_sha256 must resolve to a real committed file whose bytes hash to the
// cited value, and capture_case_id must name the observation within it.
type Provenance struct {
	Kind          string `json:"kind"`
	Note          string `json:"note"`
	CaptureRef    string `json:"capture_ref"`
	CaptureSHA256 string `json:"capture_sha256"`
	CaptureCaseID string `json:"capture_case_id"`
	Citation      string `json:"citation"`
}

// TenantParams is the tenant context a capture was taken under. The oracle's fee
// arithmetic reads this context (rounding mode, precision and currency scale), so
// a capture taken under a different tenant cannot be replayed meaningfully. The
// charges captures were taken under the gerege tenant: HALF_UP (ordinal 4),
// precision 19, currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// ChargeRequest is the charge definition and base amount the implementation is
// graded on, in the stored/observable form the oracle works from.
//
// Monetary values are INTEGER STRINGS of minor units; Percentage is the integer
// micro-per-cent Percent (not money). The four enum fields carry stored values.
type ChargeRequest struct {
	Name            string  `json:"name"`
	CurrencyCode    string  `json:"currency_code"`
	AmountMinor     string  `json:"amount_minor"`
	Percentage      int64   `json:"percentage"`
	AppliesTo       int32   `json:"applies_to"`
	TimeType        int32   `json:"time_type"`
	CalculationType int32   `json:"calculation_type"`
	PaymentMode     int32   `json:"payment_mode"`
	MinCapMinor     *string `json:"min_cap_minor"`
	MaxCapMinor     *string `json:"max_cap_minor"`
	Penalty         bool    `json:"penalty"`
	Active          bool    `json:"active"`
	Deleted         bool    `json:"deleted"`
	BaseAmountMinor string  `json:"base_amount_minor"`
}

// ChargeExpect is what the oracle produced for the request.
type ChargeExpect struct {
	Kind            ExpectKind `json:"kind"`
	ValidationCodes []string   `json:"validation_codes"`
	FeeMinor        string     `json:"fee_minor"`
}

// Vector is one charges golden vector.
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
	Request      ChargeRequest `json:"request"`
	Expect       ChargeExpect  `json:"expect"`
	// CapabilitiesRequired states what this vector exercises, for the
	// capability registry's default-deny check.
	CapabilitiesRequired []string `json:"capabilities_required"`
	// GradedAgainst names the registered implementations this vector grades.
	GradedAgainst []string `json:"graded_against"`

	// Path is the store-relative path, set by LoadVector and never decoded.
	Path string `json:"-"`
}

// LoadError is one file that could not be read as a charges vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer. It runs BEFORE any typed decoding, so a float in a
// field the typed shape ignores is still caught.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "charges") }

// DeclaresChargesSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresChargesSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresChargesSchema is DeclaresChargesSchema over a path.
func FileDeclaresChargesSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// ChargesFilePaths walks the store root and returns the store-relative paths of
// every file that declares the charges schema, sorted.
func ChargesFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one charges vector file: a raw float
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

var chargesID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every charges-schema .json under it.
//
// contextFilter, when non-empty, selects a single context directory. The
// duplicate-case_id census is taken over the WHOLE charges population before the
// filter: the filter narrows what is GRADED, never what is CHECKED.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "charges", chargesID, LoadVector)
}

// DuplicateCaseIDs refuses a charges population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, chargesID, "charges")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, chargesID) }
