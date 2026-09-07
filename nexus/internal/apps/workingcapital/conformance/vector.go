package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.workingcapital.vector/v1"

// WorkingCapitalContext is the ONE bounded context this schema's machinery can
// say anything about, and the directory name that context's vectors live in.
const WorkingCapitalContext = "workingcapital"

// SeamWorkingCapitalLoansList is the one capture seam this schema grades today:
// the m_wc_loan list as returned by GET /working-capital-loans.
const SeamWorkingCapitalLoansList = "working-capital-loans-list"

// SeamWorkingCapitalLoansDetail is the capture seam that reads one
// working-capital loan by id (GET /working-capital-loans/{loanId}): the read-back
// that serialises the m_wc_loan_balance row — its thirteen stored columns plus
// the derived outstanding/due figures — as the response's "balance" block.
const SeamWorkingCapitalLoansDetail = "working-capital-loans-detail"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim.
func SchemaContexts() []string { return []string{WorkingCapitalContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a working-capital vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit.
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

// Provenance is where a parity vector's expected values came from.
type Provenance struct {
	Kind          string `json:"kind"`
	Note          string `json:"note"`
	CaptureRef    string `json:"capture_ref"`
	CaptureSHA256 string `json:"capture_sha256"`
	CaptureCaseID string `json:"capture_case_id"`
	Citation      string `json:"citation"`
}

// TenantParams is the tenant context a capture was taken under. The
// working-capital captures were taken under the gerege tenant: HALF_UP (ordinal
// 4), precision 19, currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// Request is the input the implementation is graded on. LoanID 0 means "list
// all working-capital loans"; a positive LoanID selects one loan by id.
type Request struct {
	LoanID int64 `json:"loan_id"`
}

// LoanExpect is one working-capital loan row as the oracle serialises it.
type LoanExpect struct {
	ID         string `json:"id"`
	ExternalID string `json:"external_id"`
	Status     string `json:"status"`
}

// BalanceExpect is the read-back of one m_wc_loan_balance row: the subset of
// the response's "balance" block whose cells the port's derive-don't-store rule
// can reproduce. Every money cell is an integer STRING in minor units,
// transcribed from the committed capture — never computed here.
//
// The thirteen stored columns (principal, principalPaid, principalAdjustment,
// fee, feePaid, penalty, penaltyPaid, realizedIncomeFromDiscountFee,
// overpaymentAmount, totalDisbursement, totalDiscountFee,
// totalDiscountFeeAdjustment, breachPastDueAmount) are the authority; the
// outstanding/due figures (principalOutstanding, totalExpectedRepayment,
// totalRepayment, totalOutstanding, unrealizedIncomeFromDiscountFee) are DERIVED
// from them by the port's balance getters.
type BalanceExpect struct {
	Principal                       string `json:"principal"`                           // stored: balance.principal
	PrincipalPaid                   string `json:"principal_paid"`                      // stored: balance.principalPaid
	TotalDisbursement               string `json:"total_disbursement"`                  // stored: balance.totalDisbursement
	TotalDiscountFee                string `json:"total_discount_fee"`                  // stored: balance.totalDiscountFee
	PrincipalOutstanding            string `json:"principal_outstanding"`               // derived: balance.principalOutstanding
	TotalExpectedRepayment          string `json:"total_expected_repayment"`            // derived: balance.totalExpectedRepayment
	TotalRepayment                  string `json:"total_repayment"`                     // derived: balance.totalRepayment
	TotalOutstanding                string `json:"total_outstanding"`                   // derived: balance.totalOutstanding
	UnrealizedIncomeFromDiscountFee string `json:"unrealized_income_from_discount_fee"` // derived
}

// DetailExpect is the working-capital-loans-detail seam's expected cells: the
// row identity, its status (loan-status code) and the balance read-back above.
type DetailExpect struct {
	ID      string        `json:"id"`
	Status  string        `json:"status"`
	Balance BalanceExpect `json:"balance"`
}

// Expect is what the oracle produced for the request. For a list request it is
// the full list plus the totalElements count the oracle returned; for a detail
// request it is the one loan's balance read-back. A vector sets exactly one of
// the two shapes, named by its seam.
type Expect struct {
	Loans         []LoanExpect  `json:"loans"`
	TotalElements int64         `json:"total_elements"`
	Detail        *DetailExpect `json:"detail,omitempty"`
}

// Vector is one working-capital golden vector.
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
	// CapabilitiesRequired states what this vector exercises.
	CapabilitiesRequired []string `json:"capabilities_required"`
	// GradedAgainst names the registered implementations this vector grades.
	GradedAgainst []string `json:"graded_against"`

	// Path is the store-relative path, set by LoadVector and never decoded.
	Path string `json:"-"`
}

// LoadError is one file that could not be read as a working-capital vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error {
	return shared.RejectFloatTokens(raw, "workingcapital")
}

// DeclaresWorkingCapitalSchema reports whether raw declares SchemaV1.
func DeclaresWorkingCapitalSchema(raw []byte) bool {
	return shared.DeclaresSchema(raw, SchemaV1)
}

// FileDeclaresWorkingCapitalSchema is DeclaresWorkingCapitalSchema over a path.
func FileDeclaresWorkingCapitalSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// WorkingCapitalFilePaths walks the store root and returns the store-relative
// paths of every file that declares the schema, sorted.
func WorkingCapitalFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one working-capital vector file.
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

var workingCapitalID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every working-capital-schema .json.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "workingcapital", workingCapitalID, LoadVector)
}

// DuplicateCaseIDs refuses a population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, workingCapitalID, "workingcapital")
}
