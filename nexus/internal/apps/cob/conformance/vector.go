package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.cob.vector/v1"

// PinSchemaV1 is the cob store pin's schema string.
const PinSchemaV1 = "gerege.cob.pin/v1"

// CapabilitySchemaV1 is the cob capability registry's schema string.
const CapabilitySchemaV1 = "gerege.cob.capabilities/v1"

// COBContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const COBContext = "cob"

// SeamCOBBusinessStepOrder is the one capture seam this schema grades: the
// ordered LOAN_CLOSE_OF_BUSINESS business-step list as returned by
// GET /jobs/LOAN_CLOSE_OF_BUSINESS/steps.
const SeamCOBBusinessStepOrder = "cob-business-step-order"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{COBContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool { return ctx == COBContext }

// VectorClass is what a cob vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// cob parity tally.
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

// TenantParams is the tenant context a capture was taken under. The cob captures
// were taken under the gerege tenant; the field set is uniform with the money
// contexts even though this context grades no money.
type TenantParams = shared.TenantParams

// Request is the input the implementation is graded on: a business-step name.
type Request struct {
	StepName string `json:"step_name"`
}

// Expect is what the oracle stored for the request: the step's order (1..6) in
// the LOAN_CLOSE_OF_BUSINESS job.
type Expect struct {
	StepOrder int64 `json:"step_order"`
}

// Vector is one cob golden vector.
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

// LoadError is one file that could not be read as a cob vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "cob") }

// DeclaresCOBSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresCOBSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresCOBSchema is DeclaresCOBSchema over a path.
func FileDeclaresCOBSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// COBFilePaths walks the store root and returns the store-relative paths of
// every file that declares the cob schema, sorted. The paths are DERIVED, not
// listed, so a cob vector added or removed later needs no edit in the caller.
func COBFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one cob vector file: a raw float scan
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

var cobID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every cob-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "cob", cobID, LoadVector)
}

// DuplicateCaseIDs refuses a cob population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, cobID, "cob")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, cobID) }
