package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.provisioning.vector/v1"

// ProvisioningContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const ProvisioningContext = "provisioning"

// SeamProvisioningCategoryRead is one capture seam this schema grades: the
// m_provision_category aggregate as returned by GET /v1/provisioningcategory.
const SeamProvisioningCategoryRead = "provisioning-category-read"

// SeamProvisioningEntryReserve is the second capture seam this schema grades:
// the reserve amount (and aggregation) observed on
// GET /v1/provisioningentries/{id}/entries.
const SeamProvisioningEntryReserve = "provisioning-entry-reserve"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
//
// A vector's schema, its directory and the comparator that grades it name ONE
// context, and the check is stated in both directions so that copying a vector
// into a new directory and changing two strings cannot raise a parity count.
func SchemaContexts() []string { return []string{ProvisioningContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a provisioning vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// provisioning parity tally.
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

// TenantParams is the tenant context a capture was taken under. The oracle's
// provisioning arithmetic reads this context (rounding mode, precision and
// currency scale), so a capture taken under a different tenant cannot be
// replayed meaningfully. The provisioning captures were taken under the gerege
// tenant: HALF_UP (ordinal 4), precision 19, currency MNT, 2 minor units,
// Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// Request is the input the implementation is graded on. It is the union of the
// two seams: the category read (category_id) and the entry reserve (inputs, a
// list of per-loan reserve rows). A category vector sets exactly category_id; a
// reserve vector sets exactly inputs.
type Request struct {
	CategoryID int64             `json:"category_id"`
	Inputs     []ReserveInputRow `json:"inputs"`
}

// ReserveInputRow is one per-loan provisioning row the entry-reserve seam is
// graded on: the two money inputs (outstanding balance in minor units, reserve
// percentage in micro-per-cent) plus the identity fields that decide which
// aggregated reserve entry the oracle writes. Monetary values are integer
// STRINGS in minor units; Percentage is the integer micro-per-cent Percent
// (50.000000 % -> 50_000_000), never money.
type ReserveInputRow struct {
	OfficeID         int64  `json:"office_id"`
	CurrencyCode     string `json:"currency_code"`
	ProductID        int64  `json:"product_id"`
	CategoryID       int64  `json:"category_id"`
	OverdueInDays    int64  `json:"overdue_in_days"`
	Percentage       int64  `json:"percentage"`
	BalanceMinor     string `json:"balance_minor"`
	LiabilityAccount int64  `json:"liability_account"`
	ExpenseAccount   int64  `json:"expense_account"`
	CriteriaID       int64  `json:"criteria_id"`
}

// Expect is what the oracle produced for the request. For the category seam it
// is the category aggregate's id, name and description; id and name are the
// aggregate's NOT NULL members and description is its nullable member. For the
// entry-reserve seam it is one aggregated reserve entry, with the reserved
// amount as an integer STRING in minor units plus the identity that pins which
// band the amount belongs to.
type Expect struct {
	ID          int64  `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`

	ReservedAmountMinor string `json:"reserved_amount_minor"`
	OfficeID            int64  `json:"office_id"`
	CurrencyCode        string `json:"currency_code"`
	ProductID           int64  `json:"product_id"`
	CategoryID          int64  `json:"category_id"`
	OverdueInDays       int64  `json:"overdue_in_days"`
	LiabilityAccount    int64  `json:"liability_account"`
	ExpenseAccount      int64  `json:"expense_account"`
	CriteriaID          int64  `json:"criteria_id"`
}

// Vector is one provisioning golden vector.
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

// LoadError is one file that could not be read as a provisioning vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
//
// It runs BEFORE any typed decoding, so a float in a field the typed shape
// ignores is still caught. The rule is the shared no-float token rejection; only
// the context label is local.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "provisioning") }

// DeclaresProvisioningSchema reports whether raw is a JSON object whose
// top-level "schema" member is exactly SchemaV1. It decodes one field,
// non-strictly, and answers yes/no: a malformed provisioning vector must reach
// this loader and be reported here BY NAME, not fall back to another loader.
func DeclaresProvisioningSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresProvisioningSchema is DeclaresProvisioningSchema over a path. An
// unreadable file is NOT a provisioning file: it stays with the caller, which
// reports it.
func FileDeclaresProvisioningSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// ProvisioningFilePaths walks the store root and returns the store-relative
// paths of every file that declares the provisioning schema, sorted. It is the
// provisioning analogue of the ledger package's LedgerFilePaths and the charges
// package's ChargesFilePaths: the loanschedule loader's store census must be
// told which files belong to THIS schema so it does not refuse them as
// "unloaded". The paths are DERIVED, not listed, so a provisioning vector added
// or removed later needs no edit in the caller.
func ProvisioningFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one provisioning vector file: a raw
// float scan first, then a typed decode with unknown fields disallowed.
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

var provisioningID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every provisioning-schema .json
// under it.
//
// contextFilter, when non-empty, selects a single context directory. The
// duplicate-case_id census is taken over the WHOLE provisioning population
// before the filter: the filter narrows what is GRADED, never what is CHECKED.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "provisioning", provisioningID, LoadVector)
}

// DuplicateCaseIDs refuses a provisioning population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, provisioningID, "provisioning")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, provisioningID) }
