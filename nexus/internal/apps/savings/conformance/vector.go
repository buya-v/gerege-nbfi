package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.savings.vector/v1"

// SavingsContext is the ONE bounded context this schema's machinery can say
// anything about, and it is the directory name that context's vectors live in.
const SavingsContext = "savings"

// SeamSavingsDailyInterest is the discriminating capture seam this schema
// grades: the single-period daily-balance interest of the discriminating savings
// account, whose one-day raw interest 0.005 ties HALF_UP against HALF_EVEN.
const SeamSavingsDailyInterest = "savings-daily-interest"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{SavingsContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a savings vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// savings parity tally.
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

// TenantParams is the tenant context a capture was taken under. The savings
// captures were taken under the gerege tenant: HALF_UP (ordinal 4), precision
// 19, currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// DailyInterestRequest is the savings-daily-interest seam's input: the MANIFEST's
// discriminating input (balance, annual rate, day conventions and day count).
//
// The rate is the savings Percent convention — whole per cent scaled by 10^6
// (micro-per-cent), so 0.1825 % is 182500. The balance is an integer STRING in
// minor units. DaysInYear is the savings interest-calculation day-count (360 or
// 365); Days is the number of days the daily-balance interest accrues over.
type DailyInterestRequest struct {
	BalanceMinor         string `json:"balance_minor"`
	RatePerAnnumMicroPct int64  `json:"rate_per_annum_micro_pct"`
	DaysInYear           int64  `json:"days_in_year"`
	Days                 int64  `json:"days"`
}

// Request is the input the implementation is graded on. It is the union of the
// seams; a vector sets exactly one sub-request.
type Request struct {
	DailyInterest *DailyInterestRequest `json:"daily_interest,omitempty"`
}

// Expect is what the oracle produced for the request. For the daily-interest
// seam it is the single-period interest, an integer STRING in minor units.
type Expect struct {
	InterestMinor string `json:"interest_minor,omitempty"`
}

// Vector is one savings golden vector.
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

// LoadError is one file that could not be read as a savings vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "savings") }

// DeclaresSavingsSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresSavingsSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresSavingsSchema is DeclaresSavingsSchema over a path.
func FileDeclaresSavingsSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// SavingsFilePaths walks the store root and returns the store-relative paths of
// every file that declares the savings schema, sorted. The paths are DERIVED,
// not listed, so a savings vector added or removed later needs no edit in the
// caller.
func SavingsFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one savings vector file: a raw float
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

var savingsID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every savings-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "savings", savingsID, LoadVector)
}

// DuplicateCaseIDs refuses a savings population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, savingsID, "savings")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, savingsID) }
