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
// it is gradeable. The rules are DEFAULT-DENY: every claim is stated or refused,
// and a vector that fails to declare what it exercises, where it came from, or
// who grades it is refused rather than given the benefit of the doubt.
func Admit(v *Vector, opts Options) []string {
	var problems []string

	if v.Schema != SchemaV1 {
		problems = append(problems, fmt.Sprintf("schema %q, want %q", v.Schema, SchemaV1))
	}
	if v.Context != ProvisioningContext || !IsSchemaContext(v.Context) {
		problems = append(problems, fmt.Sprintf("context %q is not %q", v.Context, ProvisioningContext))
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
	case SeamProvisioningCategoryRead, SeamProvisioningEntryReserve:
	default:
		problems = append(problems, fmt.Sprintf(
			"oracle.seam %q: this harness grades only seams %q and %q",
			v.Oracle.Seam, SeamProvisioningCategoryRead, SeamProvisioningEntryReserve))
	}
	if v.Oracle.FineractCommit == "" {
		problems = append(problems, "oracle.fineract_commit is empty")
	} else if opts.Pin != nil && v.Oracle.FineractCommit != opts.Pin.FineractCommit {
		problems = append(problems, fmt.Sprintf(
			"oracle.fineract_commit %q does not match the pinned commit %q", v.Oracle.FineractCommit, opts.Pin.FineractCommit))
	}

	// Provenance: a parity vector is a transcription of a committed capture. The
	// kind is the only admissible one, and the capture must resolve to a real
	// committed file whose content hash matches the cited value.
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

	// Tenant context: the oracle's provisioning arithmetic reads the tenant
	// context, so a capture taken under a different tenant is not a parity
	// observation.
	if v.TenantParams == nil {
		problems = append(problems, "tenant_params is missing: every parity vector must record the tenant context it was captured under")
	} else if opts.Pin != nil && *v.TenantParams != opts.Pin.TenantParams {
		problems = append(problems, fmt.Sprintf(
			"tenant_params %+v does not match the pinned tenant %+v", *v.TenantParams, opts.Pin.TenantParams))
	} else if err := validateTenantParams(v.TenantParams); err != nil {
		problems = append(problems, err.Error())
	}

	switch v.Oracle.Seam {
	case SeamProvisioningCategoryRead:
		if v.Request.CategoryID <= 0 {
			problems = append(problems, fmt.Sprintf("request.category_id %d is not a positive category id", v.Request.CategoryID))
		}
	case SeamProvisioningEntryReserve:
		problems = append(problems, validateReserveInputs(v.Request.Inputs)...)
		if !isIntegerMinorString(v.Expect.ReservedAmountMinor) {
			problems = append(problems, fmt.Sprintf("expect.reserved_amount_minor %q is not a non-negative integer minor-unit amount", v.Expect.ReservedAmountMinor))
		}
		if v.Expect.CategoryID <= 0 {
			problems = append(problems, fmt.Sprintf("expect.category_id %d is not positive", v.Expect.CategoryID))
		}
		if v.Expect.OverdueInDays < 0 {
			problems = append(problems, fmt.Sprintf("expect.overdue_in_days %d is negative", v.Expect.OverdueInDays))
		}
	}

	problems = append(problems, checkGradedAgainst(v)...)

	sort.Strings(problems)
	return problems
}

// validateTenantParams is the tenant context check. The provisioning captures
// were taken under the gerege tenant; a vector must state the exact context and
// it must be the context the oracle used.
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
// registered, and a completely empty graded_against list (a vector that grades
// nobody is a claim that grades nothing).
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
// capture_case_id is the categoryName value of the captured m_provision_category
// row; a plain byte search is the weakest non-fabricating test that the case
// exists in the capture.
func bytesContain(raw []byte, needle string) bool {
	return strings.Contains(string(raw), needle)
}

// validateReserveInputs default-deny-checks the reserve-seam request rows: at
// least one row, a non-empty currency, positive identity keys, a positive
// percentage, and a balance_minor that is a non-negative integer STRING of minor
// units (money is integer minor units, never a float).
func validateReserveInputs(rows []ReserveInputRow) []string {
	if len(rows) == 0 {
		return []string{"request.inputs is empty: a reserve vector must carry at least one per-loan reserve row"}
	}
	var problems []string
	for i, r := range rows {
		at := fmt.Sprintf("request.inputs[%d]", i)
		if r.OfficeID <= 0 {
			problems = append(problems, fmt.Sprintf("%s.office_id %d is not positive", at, r.OfficeID))
		}
		if r.CurrencyCode == "" {
			problems = append(problems, fmt.Sprintf("%s.currency_code is empty", at))
		}
		if r.ProductID <= 0 {
			problems = append(problems, fmt.Sprintf("%s.product_id %d is not positive", at, r.ProductID))
		}
		if r.CategoryID <= 0 {
			problems = append(problems, fmt.Sprintf("%s.category_id %d is not positive", at, r.CategoryID))
		}
		if r.OverdueInDays < 0 {
			problems = append(problems, fmt.Sprintf("%s.overdue_in_days %d is negative", at, r.OverdueInDays))
		}
		if r.Percentage <= 0 {
			problems = append(problems, fmt.Sprintf("%s.percentage %d is not positive", at, r.Percentage))
		}
		if r.LiabilityAccount <= 0 {
			problems = append(problems, fmt.Sprintf("%s.liability_account %d is not positive", at, r.LiabilityAccount))
		}
		if r.ExpenseAccount <= 0 {
			problems = append(problems, fmt.Sprintf("%s.expense_account %d is not positive", at, r.ExpenseAccount))
		}
		if r.CriteriaID <= 0 {
			problems = append(problems, fmt.Sprintf("%s.criteria_id %d is not positive", at, r.CriteriaID))
		}
		if !isIntegerMinorString(r.BalanceMinor) {
			problems = append(problems, fmt.Sprintf("%s.balance_minor %q is not a non-negative integer minor-unit amount", at, r.BalanceMinor))
		}
	}
	return problems
}

// isIntegerMinorString reports whether s is a non-negative integer (money in
// minor units must be an integer, never a float).
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
