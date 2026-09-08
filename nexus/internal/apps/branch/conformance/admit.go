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

	seam := requestSeam(&v.Request)
	if seam == "" {
		problems = append(problems, "request sets none or more than one seam: exactly one of cashier-txn-amount fields, cashier_summary and teller_status must be set")
	}
	if v.Oracle.Seam != seam {
		problems = append(problems, fmt.Sprintf(
			"oracle.seam %q does not match the seam %q the request names", v.Oracle.Seam, seam))
	}
	switch seam {
	case SeamCashierSummary:
		problems = append(problems, admitSummary(v.Request.Summary, &v.Expect)...)
	case SeamTellerStatus:
		problems = append(problems, admitTellerStatus(v.Request.TellerStatus, &v.Expect)...)
	case SeamCashierTxnAmount:
		problems = append(problems, admitTxn(&v.Request, &v.Expect)...)
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

	problems = append(problems, checkGradedAgainst(v)...)

	sort.Strings(problems)
	return problems
}

// requestSeam names the seam the request sets, or "" if the request sets none
// or more than one seam. A branch vector exercises exactly one seam.
func requestSeam(r *Request) string {
	if r.Summary != nil && r.TellerStatus != nil {
		return ""
	}
	if r.Summary != nil {
		return SeamCashierSummary
	}
	if r.TellerStatus != nil {
		return SeamTellerStatus
	}
	// The cashier-txn-amount seam is the movement's only spelling; there are no
	// optional movement fields to disambiguate, so a bare Request is that seam.
	if r.TxnType != 0 || r.TxnAmount != "" || r.CurrencyCode != "" {
		return SeamCashierTxnAmount
	}
	return ""
}

// admitTxn validates a cashier-txn-amount vector: the movement's request fields
// and the expect cells transcribed from the resulting m_cashier_transactions row.
func admitTxn(req *Request, exp *Expect) []string {
	var problems []string
	typ, typOK := branch.CashierTxnTypeFromID(req.TxnType)
	if !typOK {
		problems = append(problems, fmt.Sprintf("request.txn_type %d is not a known cashier txn type", req.TxnType))
	}
	if req.CurrencyCode == "" {
		problems = append(problems, "request.currency_code is empty")
	}
	if _, err := branch.MinorUnitsFromDecimalText(req.TxnAmount, branch.MNTMinorDigits); err != nil {
		problems = append(problems, fmt.Sprintf("request.txn_amount: %v", err))
	}
	if typOK {
		if exp.TxnTypeID != typ.ID {
			problems = append(problems, fmt.Sprintf("expect.txn_type_id %d does not match request.txn_type %d", exp.TxnTypeID, req.TxnType))
		}
		if exp.TxnTypeValue != typ.Value {
			problems = append(problems, fmt.Sprintf("expect.txn_type_value %q does not match the known value %q for txn_type %d", exp.TxnTypeValue, typ.Value, req.TxnType))
		}
	}
	if !isIntegerMinorString(exp.TxnAmountMinor) {
		problems = append(problems, fmt.Sprintf("expect.txn_amount_minor %q is not a non-negative integer minor-unit amount", exp.TxnAmountMinor))
	}
	return problems
}

// admitSummary validates a cashier-summary vector: every row the request names
// must be a known txn type with parseable exact money text, and the expect must
// state the three bucket cells as integer minor-unit amounts.
func admitSummary(req *SummaryRequest, exp *Expect) []string {
	var problems []string
	if req == nil || len(req.Rows) == 0 {
		problems = append(problems, "request.cashier_summary.rows is empty: a summary read-back needs at least one row")
		return problems
	}
	for i, row := range req.Rows {
		if _, ok := branch.CashierTxnTypeFromID(row.TxnType); !ok {
			problems = append(problems, fmt.Sprintf("request.cashier_summary.rows[%d].txn_type %d is not a known cashier txn type", i, row.TxnType))
		}
		if _, err := branch.MinorUnitsFromDecimalText(row.TxnAmount, branch.MNTMinorDigits); err != nil {
			problems = append(problems, fmt.Sprintf("request.cashier_summary.rows[%d].txn_amount: %v", i, err))
		}
	}
	for name, v := range map[string]string{
		"expect.sum_cash_allocation": exp.SumCashAllocation,
		"expect.sum_cash_settlement": exp.SumCashSettlement,
		"expect.net_cash":            exp.NetCash,
	} {
		if !isIntegerMinorString(v) {
			problems = append(problems, fmt.Sprintf("%s %q is not a non-negative integer minor-unit amount", name, v))
		}
	}
	return problems
}

// admitTellerStatus validates a teller-status vector: the status label the
// request names must be one the read-back observed (never invented), and the
// expect must state that status's stored integer.
func admitTellerStatus(req *TellerStatusRequest, exp *Expect) []string {
	var problems []string
	if req == nil {
		problems = append(problems, "request.teller_status is missing")
		return problems
	}
	switch req.StatusLabel {
	case "ACTIVE":
		if exp.TellerStatusStored != branch.TellerStatusActive.StoredValue() {
			problems = append(problems, fmt.Sprintf(
				"expect.teller_status_stored %d does not match the stored value %d for the observed status label %q",
				exp.TellerStatusStored, branch.TellerStatusActive.StoredValue(), req.StatusLabel))
		}
	default:
		problems = append(problems, fmt.Sprintf(
			"request.teller_status.status_label %q was not observed in any capture: only the label(s) the oracle serialised may be pinned", req.StatusLabel))
	}
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
