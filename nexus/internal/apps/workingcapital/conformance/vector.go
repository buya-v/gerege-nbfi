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
//
// A list vector pins the cells a wrong implementation could corrupt on the LIST
// read without disturbing the balance read-back: the row identity (account_no,
// the loan row's own account number, and client_id, the borrowing client's id).
// The list seam grades NO money cell — the balance is read through the detail
// endpoint, never the list — so these cells are structural. They are OPTIONAL on
// the vector: a comparator grades a cell only when the vector pins it, so WC-01
// keeps grading id/external_id/status alone.
type LoanExpect struct {
	ID         string `json:"id"`
	ExternalID string `json:"external_id"`
	Status     string `json:"status"`
	AccountNo  string `json:"account_no,omitempty"` // the loan row's own account number
	ClientID   string `json:"client_id,omitempty"`  // the borrowing client's id
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

// DisbursementExpect is one working-capital disbursement tranche as the read-back
// serialises it in "disbursementDetails": the tranche's principal (the amount
// scheduled/expected for the tranche) and its actualAmount (what the draw
// actually recorded). A disbursement that updates the balance row but never
// records the tranche row renders no disbursement block, so a detail vector can
// pin these cells to discriminate that write-path defect.
type DisbursementExpect struct {
	Principal    string `json:"principal,omitempty"`     // tranche principal, integer minor
	ActualAmount string `json:"actual_amount,omitempty"` // tranche actualAmount, integer minor
}

// AllocationRuleExpect is one decoded entry of a loan's payment-allocation
// order. Name is the observed value the read-back serialises (the
// WorkingCapitalPaymentAllocationType's persisted name, via the oracle mapper's
// type.name()); Code is the ApiFacingEnum code, which for this enum carries the
// SAME literal as the name [VERIFIED:
// WorkingCapitalPaymentAllocationType.java: DUE_PENALTY(DUE, PENALTY,
// "DUE_PENALTY", "Due Penalty")], so it is graded from the same observed token.
// DueType and AllocationType are the two classifications the port derives FROM
// that name — which instalment the bucket applies to (DUE / IN_ADVANCE) and
// which money bucket it fills (PENALTY / FEE / PRINCIPAL). This is a
// decode/classification cell: no money moves through it.
type AllocationRuleExpect struct {
	Name           string `json:"name"`            // observed: e.g. "DUE_PENALTY"
	Code           string `json:"code"`            // observed-equal: ApiFacingEnum code (== name for this enum)
	DueType        string `json:"due_type"`        // derived: "DUE" / "IN_ADVANCE"
	AllocationType string `json:"allocation_type"` // derived: "PENALTY" / "FEE" / "PRINCIPAL"
}

// PaymentAllocationExpect is a loan's payment-allocation rule as the detail
// read-back serialises it: the transaction type and the ordered decode of its
// allocation buckets. The rules are positional — the order the observation
// records is the order graded.
type PaymentAllocationExpect struct {
	TransactionType string                 `json:"transaction_type"` // observed: e.g. "DEFAULT"
	Rules           []AllocationRuleExpect `json:"rules"`
}

// DetailExpect is the working-capital-loans-detail seam's expected cells: the
// row id, its loan-status code, the balance read-back above, and the OPTIONAL
// cells a vector may pin — the stored status ordinal (status_id) and active flag
// (status_active) the status block carries, and the disbursement tranche the
// seeded draw recorded. An optional cell is graded only when the vector pins it,
// so WC-02 keeps grading id/status/balance alone.
type DetailExpect struct {
	ID            string                   `json:"id"`
	Status        string                   `json:"status"`
	StatusOrdinal string                   `json:"status_id,omitempty"`     // stored status ordinal (300 = active), integer
	StatusActive  string                   `json:"status_active,omitempty"` // "true"/"false" active flag
	Balance       BalanceExpect            `json:"balance"`
	Disbursement  *DisbursementExpect      `json:"disbursement,omitempty"` // the tranche the seeded draw recorded
	Allocation    *PaymentAllocationExpect `json:"allocation,omitempty"`   // the loan's payment-allocation rule decode
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
