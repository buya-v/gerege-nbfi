package conformance

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Admit returns the ordered list of reasons a vector is INADMISSIBLE, empty if
// it is gradeable. The rules are DEFAULT-DENY: every claim is stated or refused.
func Admit(v *Vector, opts Options) []string {
	var problems []string

	if v.Schema != SchemaV1 {
		problems = append(problems, fmt.Sprintf("schema %q, want %q", v.Schema, SchemaV1))
	}
	if v.Context != WorkingCapitalContext || !IsSchemaContext(v.Context) {
		problems = append(problems, fmt.Sprintf("context %q is not %q", v.Context, WorkingCapitalContext))
	}
	if v.CaseID == "" {
		problems = append(problems, "case_id is empty")
	}
	if v.Title == "" {
		problems = append(problems, "title is empty")
	}
	if v.Note == "" {
		problems = append(problems, "_note is empty: every vector must carry its provenance")
	}

	if v.Class != ClassParity {
		problems = append(problems, fmt.Sprintf("class %q: only %q vectors may be graded by this harness", v.Class, ClassParity))
	}
	switch v.Oracle.Seam {
	case SeamWorkingCapitalLoansList, SeamWorkingCapitalLoansDetail:
	default:
		problems = append(problems, fmt.Sprintf(
			"oracle.seam %q: this harness grades only the %q and %q seams",
			v.Oracle.Seam, SeamWorkingCapitalLoansList, SeamWorkingCapitalLoansDetail))
	}
	if v.Oracle.FineractCommit == "" {
		problems = append(problems, "oracle.fineract_commit is empty")
	} else if opts.Pin != nil && v.Oracle.FineractCommit != opts.Pin.FineractCommit {
		problems = append(problems, fmt.Sprintf(
			"oracle.fineract_commit %q does not match the pinned commit %q", v.Oracle.FineractCommit, opts.Pin.FineractCommit))
	}

	// Provenance: a parity vector is a transcription of a committed capture.
	if v.Provenance.Kind != ProvenanceKindOracleCapture {
		problems = append(problems, fmt.Sprintf(
			"provenance.kind %q: only %q vectors may be graded by this harness",
			v.Provenance.Kind, ProvenanceKindOracleCapture))
	}
	if v.Provenance.CaptureRef == "" {
		problems = append(problems, "provenance.capture_ref is empty: a parity vector must cite the committed capture artefact it was transcribed from")
	} else if opts.RepoRoot != "" {
		abs := filepath.Join(opts.RepoRoot, filepath.FromSlash(v.Provenance.CaptureRef))
		info, err := os.Stat(abs)
		switch {
		case err != nil:
			problems = append(problems, fmt.Sprintf(
				"provenance.capture_ref %q does not resolve to a file in this repository: %v",
				v.Provenance.CaptureRef, err))
		case info.IsDir():
			problems = append(problems, fmt.Sprintf(
				"provenance.capture_ref %q is a directory, not a capture artefact", v.Provenance.CaptureRef))
		case v.Provenance.CaptureSHA256 != "":
			raw, rerr := os.ReadFile(abs)
			if rerr != nil {
				problems = append(problems, fmt.Sprintf(
					"provenance.capture_ref %q unreadable: %v", v.Provenance.CaptureRef, rerr))
			} else {
				sum := sha256.Sum256(raw)
				if got := hex.EncodeToString(sum[:]); got != v.Provenance.CaptureSHA256 {
					problems = append(problems, fmt.Sprintf(
						"provenance.capture_sha256 %s does not match the referenced capture (%s)",
						v.Provenance.CaptureSHA256, got))
				}
			}
		}
	}
	if v.Provenance.CaptureSHA256 == "" {
		problems = append(problems, "provenance.capture_sha256 is empty: a parity vector must carry the content hash of its capture artefact")
	}
	if v.Provenance.CaptureCaseID == "" {
		problems = append(problems, "provenance.capture_case_id is empty: a parity vector must identify the observation within its capture artefact")
	} else if opts.RepoRoot != "" && v.Provenance.CaptureRef != "" {
		abs := filepath.Join(opts.RepoRoot, filepath.FromSlash(v.Provenance.CaptureRef))
		if raw, rerr := os.ReadFile(abs); rerr == nil {
			if !bytesContain(raw, v.Provenance.CaptureCaseID) {
				problems = append(problems, fmt.Sprintf(
					"provenance.capture_case_id %q does not appear in %q", v.Provenance.CaptureCaseID, v.Provenance.CaptureRef))
			}
		}
	}

	// Tenant context.
	if v.TenantParams == nil {
		problems = append(problems, "tenant_params is missing: every parity vector must record the tenant context it was captured under")
	} else if opts.Pin != nil && *v.TenantParams != opts.Pin.TenantParams {
		problems = append(problems, fmt.Sprintf(
			"tenant_params %+v does not match the pinned tenant %+v", *v.TenantParams, opts.Pin.TenantParams))
	} else if err := validateTenantParams(v.TenantParams); err != nil {
		problems = append(problems, err.Error())
	}

	problems = append(problems, admitRequest(v)...)
	problems = append(problems, admitExpect(v)...)
	problems = append(problems, checkGradedAgainst(v)...)

	sort.Strings(problems)
	return problems
}

// admitRequest enforces the request/expect shape its seam names. A list request
// selects the whole table (loan_id 0) and expects the list; a detail request
// selects one loan (positive loan_id) and expects its balance read-back.
func admitRequest(v *Vector) []string {
	switch v.Oracle.Seam {
	case SeamWorkingCapitalLoansList:
		if v.Request.LoanID != 0 {
			return []string{fmt.Sprintf(
				"list seam must request the whole table (loan_id 0), got loan_id %d", v.Request.LoanID)}
		}
	case SeamWorkingCapitalLoansDetail:
		if v.Request.LoanID <= 0 {
			return []string{fmt.Sprintf(
				"detail seam must request one loan by positive loan_id, got loan_id %d", v.Request.LoanID)}
		}
	}
	return nil
}

// admitExpect enforces that the expected cells a seam needs are present and
// sane: a list expectation's length agrees with its total and every loan
// id/external_id is non-empty; a detail expectation carries a balance read-back
// whose money cells are non-negative integer minor amounts.
func admitExpect(v *Vector) []string {
	var problems []string
	switch v.Oracle.Seam {
	case SeamWorkingCapitalLoansList:
		if int64(len(v.Expect.Loans)) != v.Expect.TotalElements {
			problems = append(problems, fmt.Sprintf(
				"expect.total_elements %d does not match the loan list length %d", v.Expect.TotalElements, len(v.Expect.Loans)))
		}
		for i, l := range v.Expect.Loans {
			if l.ID == "" {
				problems = append(problems, fmt.Sprintf("expect.loans[%d].id is empty", i))
			}
			if l.ExternalID == "" {
				problems = append(problems, fmt.Sprintf("expect.loans[%d].external_id is empty", i))
			}
		}
	case SeamWorkingCapitalLoansDetail:
		if v.Expect.Detail == nil {
			return append(problems, "expect.detail is missing for the detail seam")
		}
		if len(v.Expect.Loans) != 0 {
			problems = append(problems, "detail seam must not set expect.loans")
		}
		if v.Expect.Detail.ID == "" {
			problems = append(problems, "expect.detail.id is empty")
		}
		if v.Expect.Detail.Status == "" {
			problems = append(problems, "expect.detail.status is empty")
		}
		b := v.Expect.Detail.Balance
		for name, val := range map[string]string{
			"principal":                           b.Principal,
			"principal_paid":                      b.PrincipalPaid,
			"total_disbursement":                  b.TotalDisbursement,
			"total_discount_fee":                  b.TotalDiscountFee,
			"principal_outstanding":               b.PrincipalOutstanding,
			"total_expected_repayment":            b.TotalExpectedRepayment,
			"total_repayment":                     b.TotalRepayment,
			"total_outstanding":                   b.TotalOutstanding,
			"unrealized_income_from_discount_fee": b.UnrealizedIncomeFromDiscountFee,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf("expect.detail.balance.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
	}
	return problems
}

// isIntegerMinorString reports whether s is a non-negative integer (money in
// integer form must never be a float).
func isIntegerMinorString(s string) bool {
	if s == "" {
		return false
	}
	for _, c := range s {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}

// validateTenantParams is the tenant context check.
func validateTenantParams(tp *TenantParams) error {
	var problems []string
	if tp.RoundingMode == "" {
		problems = append(problems, "tenant_params.rounding_mode is empty")
	}
	if tp.RoundingOrdinal == 0 {
		problems = append(problems, "tenant_params.rounding_ordinal is 0")
	}
	if tp.Precision == 0 {
		problems = append(problems, "tenant_params.precision is 0")
	}
	if tp.Currency == "" {
		problems = append(problems, "tenant_params.currency is empty")
	}
	if tp.MinorUnits == 0 {
		problems = append(problems, "tenant_params.minor_units is 0")
	}
	if tp.Timezone == "" {
		problems = append(problems, "tenant_params.timezone is empty")
	}
	if len(problems) > 0 {
		sort.Strings(problems)
		return fmt.Errorf("tenant_params: %s", strings.Join(problems, "; "))
	}
	return nil
}

// checkGradedAgainst refuses a graded_against name that no implementation
// registered, and a completely empty graded_against list.
func checkGradedAgainst(v *Vector) []string {
	var problems []string
	if len(v.GradedAgainst) == 0 {
		return []string{"graded_against is empty: a vector must name at least one registered implementation it grades"}
	}
	for _, name := range v.GradedAgainst {
		if _, ok := Lookup(name); !ok {
			problems = append(problems, fmt.Sprintf("graded_against %q is not a registered implementation", name))
		}
	}
	return problems
}

// bytesContain reports whether the raw capture bytes contain the given needle.
func bytesContain(raw []byte, needle string) bool {
	return strings.Contains(string(raw), needle)
}
