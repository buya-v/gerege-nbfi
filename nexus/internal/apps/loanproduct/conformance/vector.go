package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.loanproduct.vector/v1"

// PinSchemaV1 is the loanproduct store pin's schema string.
const PinSchemaV1 = "gerege.loanproduct.pin/v1"

// CapabilitySchemaV1 is the loanproduct capability registry's schema string.
const CapabilitySchemaV1 = "gerege.loanproduct.capabilities/v1"

// LoanProductContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const LoanProductContext = "loanproduct"

// Vocabulary is the identity of one of the six enum vocabularies this context
// owns: the stored-value <-> code <-> name tables that carry the loan-product
// configuration into every loan account created from a product. All six are
// observed from the same place — the loanproducts template read-back — so they
// share one capture seam.
type Vocabulary string

const (
	// VocabularyAmortizationMethod is m_product_loan.amortization_method_enum.
	VocabularyAmortizationMethod Vocabulary = "amortization-method"
	// VocabularyInterestMethod is m_product_loan.interest_method_enum.
	VocabularyInterestMethod Vocabulary = "interest-method"
	// VocabularyInterestCalcPeriod is m_product_loan.interest_calculated_in_period_enum.
	VocabularyInterestCalcPeriod Vocabulary = "interest-calc-period"
	// VocabularyPeriodFrequency is PeriodFrequencyType, the period axis shared by
	// interestPeriodFrequencyType and repaymentPeriodFrequencyType.
	VocabularyPeriodFrequency Vocabulary = "period-frequency"
	// VocabularyDaysInMonth is m_product_loan.days_in_month_enum.
	VocabularyDaysInMonth Vocabulary = "days-in-month"
	// VocabularyDaysInYear is m_product_loan.days_in_year_enum.
	VocabularyDaysInYear Vocabulary = "days-in-year"
)

// IsVocabulary reports whether v names one of the six graded vocabularies.
func IsVocabulary(v string) bool {
	switch Vocabulary(v) {
	case VocabularyAmortizationMethod, VocabularyInterestMethod, VocabularyInterestCalcPeriod,
		VocabularyPeriodFrequency, VocabularyDaysInMonth, VocabularyDaysInYear:
		return true
	}
	return false
}

// SeamLoanProductConfig is the one capture seam this schema grades: the
// loan-products template read-back, whose enum option lists carry every stored
// value -> code mapping the port's configuration model must reproduce.
const SeamLoanProductConfig = "loanproduct-config"

// IsSchemaSeam reports whether s is the capture seam this harness grades.
func IsSchemaSeam(s string) bool { return s == SeamLoanProductConfig }

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{LoanProductContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool { return ctx == LoanProductContext }

// VectorClass is what a loanproduct vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// loanproduct parity tally.
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

// TenantParams is the tenant context a capture was taken under. The loanproduct
// captures were taken under the gerege tenant; the field set is uniform with the
// money contexts even though this context grades no money.
type TenantParams = shared.TenantParams

// Request is the input the implementation is graded on: one stored enum value
// (the integer the product column persists) within a named vocabulary.
type Request struct {
	Vocabulary string `json:"vocabulary"`
	Stored     int32  `json:"stored"`
}

// Expect is what the port decodes a stored enum value to: the round-trip stored
// value, the i18n code, and the enum constant name. A stored value decoding to
// the wrong code or name is silent configuration corruption — the loan-product
// analog of a wrong enum ordinal.
type Expect struct {
	Stored int32  `json:"stored"`
	Code   string `json:"code"`
	Name   string `json:"name"`
}

// Vector is one loanproduct golden vector.
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

// LoadError is one file that could not be read as a loanproduct vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer. It runs BEFORE any typed decoding.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "loanproduct") }

// DeclaresLoanProductSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresLoanProductSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresLoanProductSchema is DeclaresLoanProductSchema over a path.
func FileDeclaresLoanProductSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// LoanProductFilePaths walks the store root and returns the store-relative paths
// of every file that declares the loanproduct schema, sorted. The paths are
// DERIVED, not listed, so a vector added or removed later needs no edit in the
// caller.
func LoanProductFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one loanproduct vector file: a raw float
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

var loanProductID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every loanproduct-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "loanproduct", loanProductID, LoadVector)
}

// DuplicateCaseIDs refuses a loanproduct population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, loanProductID, "loanproduct")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, loanProductID) }
