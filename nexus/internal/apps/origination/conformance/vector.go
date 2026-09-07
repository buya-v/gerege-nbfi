package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.origination.vector/v1"

// PinSchemaV1 is the origination store pin's schema string.
const PinSchemaV1 = "gerege.origination.pin/v1"

// CapabilitySchemaV1 is the origination capability registry's schema string.
const CapabilitySchemaV1 = "gerege.origination.capabilities/v1"

// OriginationContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const OriginationContext = "origination"

// SeamLoanOriginatorStatus is the one capture seam this schema grades: the
// LoanOriginatorStatus vocabulary as returned by GET /loan-originators/template
// statusOptions and declared in LoanOriginatorStatus.java.
const SeamLoanOriginatorStatus = "origination-loan-originator-status"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{OriginationContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool { return ctx == OriginationContext }

// VectorClass is what an origination vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// origination parity tally.
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

// Provenance is where a parity vector's expected value came from: a committed
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

// TenantParams is the tenant context a capture was taken under. The origination
// captures were taken under the gerege tenant; the field set is uniform with the
// money contexts even though this context grades no money.
type TenantParams = shared.TenantParams

// Request is the input the implementation is graded on: a LoanOriginatorStatus
// enum name.
type Request struct {
	Name string `json:"name"`
}

// Expect is what the oracle stored for the request. LoanOriginatorStatus is a
// STRING enum (there is no integer ordinal column): the stored value is the enum
// name itself, so expect.stored equals the name for a faithful port. A wrong
// mapping (e.g. PENDING stored as ACTIVE) silently corrupts every originator
// written.
type Expect struct {
	Stored string `json:"stored"`
}

// Vector is one origination golden vector.
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

// LoadError is one file that could not be read as an origination vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "origination") }

// DeclaresOriginationSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresOriginationSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresOriginationSchema is DeclaresOriginationSchema over a path.
func FileDeclaresOriginationSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// OriginationFilePaths walks the store root and returns the store-relative paths
// of every file that declares the origination schema, sorted. The paths are
// DERIVED, not listed, so an origination vector added or removed later needs no
// edit in the caller.
func OriginationFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one origination vector file: a raw float
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

var originationID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every origination-schema .json under
// it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "origination", originationID, LoadVector)
}

// DuplicateCaseIDs refuses an origination population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, originationID, "origination")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, originationID) }
