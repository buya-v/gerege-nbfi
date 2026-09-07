package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.parties.vector/v1"

// PinSchemaV1 is the parties store pin's schema string.
const PinSchemaV1 = "gerege.parties.pin/v1"

// CapabilitySchemaV1 is the parties capability registry's schema string.
const CapabilitySchemaV1 = "gerege.parties.capabilities/v1"

// PartiesContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const PartiesContext = "parties"

// Vocabulary is the identity of one of the three enum vocabularies this context
// owns. Each is graded by its own capture seam because each is observed from a
// different place.
type Vocabulary string

const (
	// VocabularyClientStatus is m_client.status_enum — ClientStatus.java.
	VocabularyClientStatus Vocabulary = "client-status"
	// VocabularyLegalForm is m_client.legal_form_enum — LegalForm.java.
	VocabularyLegalForm Vocabulary = "legal-form"
	// VocabularyGroupingStatus is m_group.status_enum — GroupingTypeStatus.java.
	VocabularyGroupingStatus Vocabulary = "grouping-status"
)

// IsVocabulary reports whether v names one of the three graded vocabularies.
func IsVocabulary(v string) bool {
	switch Vocabulary(v) {
	case VocabularyClientStatus, VocabularyLegalForm, VocabularyGroupingStatus:
		return true
	}
	return false
}

// Seam names — one capture seam per vocabulary, because each vocabulary is
// observed from a different place: the m_client.status_enum read-back, the
// clientLegalFormOptions template, and (Java-source-only) GroupingTypeStatus.
const (
	SeamClientStatus   = "client-status-ordinal"
	SeamLegalForm      = "legal-form-ordinal"
	SeamGroupingStatus = "grouping-status-ordinal"
)

// IsSchemaSeam reports whether s is one of the three capture seams this harness
// grades.
func IsSchemaSeam(s string) bool {
	switch s {
	case SeamClientStatus, SeamLegalForm, SeamGroupingStatus:
		return true
	}
	return false
}

// seamForVocabulary returns the one seam a vocabulary grades against.
func seamForVocabulary(vocab string) string {
	switch Vocabulary(vocab) {
	case VocabularyClientStatus:
		return SeamClientStatus
	case VocabularyLegalForm:
		return SeamLegalForm
	case VocabularyGroupingStatus:
		return SeamGroupingStatus
	}
	return ""
}

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{PartiesContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool { return ctx == PartiesContext }

// VectorClass is what a parties vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// parties parity tally.
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

// TenantParams is the tenant context a capture was taken under. The parties
// captures were taken under the gerege tenant; the field set is uniform with the
// money contexts even though this context grades no money.
type TenantParams = shared.TenantParams

// Request is the input the implementation is graded on: one enum NAME within a
// named vocabulary.
type Request struct {
	Vocabulary string `json:"vocabulary"`
	Name       string `json:"name"`
}

// Expect is the integer ordinal Fineract persists for that enum name. Fineract
// stores these enums as ORDINALS (m_client.status_enum, m_client.legal_form_enum,
// m_group.status_enum); a wrong ordinal is silent data corruption, not a crash —
// the same class of defect as the HALF_UP/HALF_EVEN rounding ordinal.
type Expect struct {
	Ordinal int32 `json:"ordinal"`
}

// Vector is one parties golden vector.
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

// LoadError is one file that could not be read as a parties vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "parties") }

// DeclaresPartiesSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresPartiesSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresPartiesSchema is DeclaresPartiesSchema over a path.
func FileDeclaresPartiesSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// PartiesFilePaths walks the store root and returns the store-relative paths of
// every file that declares the parties schema, sorted. The paths are DERIVED,
// not listed, so a parties vector added or removed later needs no edit in the
// caller.
func PartiesFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one parties vector file: a raw float
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

var partiesID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every parties-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "parties", partiesID, LoadVector)
}

// DuplicateCaseIDs refuses a parties population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, partiesID, "parties")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, partiesID) }
