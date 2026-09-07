package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.loan.vector/v1"

// LoanContext is the ONE bounded context this schema's machinery can say anything
// about, and it is the directory name that context's vectors live in.
const LoanContext = "loan"

// SeamLoanRepaymentAllocation is the capture seam this schema grades: the
// four-bucket greedy allocation of a repayment across penalty/fee/interest/
// principal, observed on the SEED-L03 repayment.
const SeamLoanRepaymentAllocation = "loan-repayment-allocation"

// SeamLoanScheduleInterest is the discriminating capture seam: the single-period
// interest of the discriminating loan SEED-L06, whose period-1 interest ties
// HALF_UP against HALF_EVEN.
const SeamLoanScheduleInterest = "loan-schedule-interest"

// SeamLoanDisbursement is the capture seam this schema grades: the net disbursal
// amount of the SEED-L06 disbursal.
const SeamLoanDisbursement = "loan-disbursement"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{LoanContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a loan vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// loan parity tally.
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

// TenantParams is the tenant context a capture was taken under. The loan
// captures were taken under the gerege tenant: HALF_UP (ordinal 4), precision
// 19, currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// AllocationMoney is the four-bucket money breakdown of a repayment allocation,
// each bucket an integer STRING in minor units.
type AllocationMoney struct {
	Penalty   string `json:"penalty"`
	Fee       string `json:"fee"`
	Interest  string `json:"interest"`
	Principal string `json:"principal"`
}

// RepaymentRequest is the loan-repayment-allocation seam's input: the outstanding
// buckets the allocation runs against and the payment amount.
type RepaymentRequest struct {
	Outstanding AllocationMoney `json:"outstanding"`
	AmountMinor string          `json:"amount_minor"`
}

// ScheduleRequest is the loan-schedule-interest seam's input: the MANIFEST's
// discriminating input (principal, annual rate per cent, day conventions).
type ScheduleRequest struct {
	PrincipalMinor  string `json:"principal_minor"`
	RatePerAnnumPct int64  `json:"rate_per_annum_pct"`
	DaysInYear      int64  `json:"days_in_year"`
	DaysInMonth     int64  `json:"days_in_month"`
}

// DisburseRequest is the loan-disbursement seam's input: approved principal and
// charges due at disbursement.
type DisburseRequest struct {
	ApprovedPrincipalMinor        string `json:"approved_principal_minor"`
	ChargesDueAtDisbursementMinor string `json:"charges_due_at_disbursement_minor"`
}

// Request is the input the implementation is graded on. It is the union of the
// three seams; a vector sets exactly one of the three sub-requests.
type Request struct {
	Repayment *RepaymentRequest `json:"repayment,omitempty"`
	Schedule  *ScheduleRequest  `json:"schedule,omitempty"`
	Disburse  *DisburseRequest  `json:"disburse,omitempty"`
}

// Expect is what the oracle produced for the request. For the repayment seam it
// is the allocated buckets and the leftover; for the schedule seam the
// single-period interest; for the disbursement seam the net disbursal amount.
// Every money field is an integer STRING in minor units.
type Expect struct {
	Allocation        *AllocationMoney `json:"allocation,omitempty"`
	LeftoverMinor     string           `json:"leftover_minor,omitempty"`
	InterestMinor     string           `json:"interest_minor,omitempty"`
	NetDisbursalMinor string           `json:"net_disbursal_minor,omitempty"`
}

// Vector is one loan golden vector.
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

// LoadError is one file that could not be read as a loan vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "loan") }

// DeclaresLoanSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresLoanSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresLoanSchema is DeclaresLoanSchema over a path.
func FileDeclaresLoanSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// LoanFilePaths walks the store root and returns the store-relative paths of
// every file that declares the loan schema, sorted. The paths are DERIVED, not
// listed, so a loan vector added or removed later needs no edit in the caller
// (the loanschedule store census).
func LoanFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one loan vector file: a raw float scan
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

var loanID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every loan-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "loan", loanID, LoadVector)
}

// DuplicateCaseIDs refuses a loan population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, loanID, "loan")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, loanID) }
