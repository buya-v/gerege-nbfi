package conformance

import (
	"fmt"
	"sort"
	"strings"

	"github.com/gerege/nexus/internal/apps/branch"
	shared "github.com/gerege/nexus/internal/conformance"
)

// Admit returns the ordered list of reasons a vector is INADMISSIBLE, empty if
// it is gradeable. The rules are DEFAULT-DENY: every claim is stated or refused.
func Admit(v *Vector, opts Options) []string {
	var problems []string

	if v.Schema != SchemaV1 {
		problems = append(problems, fmt.Sprintf("schema %q, want %q", v.Schema, SchemaV1))
	}
	if v.Context != BranchContext || !IsSchemaContext(v.Context) {
		problems = append(problems, fmt.Sprintf("context %q is not %q", v.Context, BranchContext))
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
	if v.Oracle.Seam != SeamCashierTxnAmount {
		problems = append(problems, fmt.Sprintf("oracle.seam %q: this harness grades only seam %q", v.Oracle.Seam, SeamCashierTxnAmount))
	}
	if v.Oracle.FineractCommit == "" {
		problems = append(problems, "oracle.fineract_commit is empty")
	} else if opts.Pin != nil && v.Oracle.FineractCommit != opts.Pin.FineractCommit {
		problems = append(problems, fmt.Sprintf(
			"oracle.fineract_commit %q does not match the pinned commit %q", v.Oracle.FineractCommit, opts.Pin.FineractCommit))
	}

	// Provenance: a parity vector is a transcription of a committed capture. The
	// shared admission check runs the kind, capture_ref, capture_sha256 and
	// capture_case_id rules.
	problems = append(problems, shared.AdmitCaptureProvenance(shared.CaptureProvenance{
		Kind:          v.Provenance.Kind,
		CaptureRef:    v.Provenance.CaptureRef,
		CaptureSHA256: v.Provenance.CaptureSHA256,
		CaptureCaseID: v.Provenance.CaptureCaseID,
	}, opts.RepoRoot)...)

	if v.TenantParams == nil {
		problems = append(problems, "tenant_params is missing: every parity vector must record the tenant context it was captured under")
	} else if opts.Pin != nil && *v.TenantParams != opts.Pin.TenantParams {
		problems = append(problems, fmt.Sprintf(
			"tenant_params %+v does not match the pinned tenant %+v", *v.TenantParams, opts.Pin.TenantParams))
	} else if err := validateTenantParams(v.TenantParams); err != nil {
		problems = append(problems, err.Error())
	}

	typ, typOK := branch.CashierTxnTypeFromID(v.Request.TxnType)
	if !typOK {
		problems = append(problems, fmt.Sprintf("request.txn_type %d is not a known cashier txn type", v.Request.TxnType))
	}
	if v.Request.CurrencyCode == "" {
		problems = append(problems, "request.currency_code is empty")
	}
	if _, err := branch.MinorUnitsFromDecimalText(v.Request.TxnAmount, branch.MNTMinorDigits); err != nil {
		problems = append(problems, fmt.Sprintf("request.txn_amount: %v", err))
	}
	if typOK {
		if v.Expect.TxnTypeID != typ.ID {
			problems = append(problems, fmt.Sprintf("expect.txn_type_id %d does not match request.txn_type %d", v.Expect.TxnTypeID, v.Request.TxnType))
		}
		if v.Expect.TxnTypeValue != typ.Value {
			problems = append(problems, fmt.Sprintf("expect.txn_type_value %q does not match the known value %q for txn_type %d", v.Expect.TxnTypeValue, typ.Value, v.Request.TxnType))
		}
	}
	if !isIntegerMinorString(v.Expect.TxnAmountMinor) {
		problems = append(problems, fmt.Sprintf("expect.txn_amount_minor %q is not a non-negative integer minor-unit amount", v.Expect.TxnAmountMinor))
	}

	problems = append(problems, checkGradedAgainst(v)...)

	sort.Strings(problems)
	return problems
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
