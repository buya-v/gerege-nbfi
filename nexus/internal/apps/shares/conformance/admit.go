package conformance

import (
	"fmt"
	"sort"
	"strings"

	"github.com/gerege/nexus/internal/apps/shares"
	shared "github.com/gerege/nexus/internal/conformance"
)

// Admit returns the ordered list of reasons a vector is INADMISSIBLE, empty if
// it is gradeable. The rules are DEFAULT-DENY: every claim is stated or refused.
func Admit(v *Vector, opts Options) []string {
	var problems []string

	if v.Schema != SchemaV1 {
		problems = append(problems, fmt.Sprintf("schema %q, want %q", v.Schema, SchemaV1))
	}
	if v.Context != SharesContext || !IsSchemaContext(v.Context) {
		problems = append(problems, fmt.Sprintf("context %q is not %q", v.Context, SharesContext))
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
	if v.Oracle.Seam != SeamShareAccount && v.Oracle.Seam != SeamShareDividend {
		problems = append(problems, fmt.Sprintf("oracle.seam %q: this harness grades only seams %q and %q", v.Oracle.Seam, SeamShareAccount, SeamShareDividend))
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

	problems = append(problems, admitRequestExpect(v)...)
	problems = append(problems, checkGradedAgainst(v)...)

	sort.Strings(problems)
	return problems
}

// admitRequestExpect validates the request/expect pair for whichever seam the
// request names.
func admitRequestExpect(v *Vector) []string {
	var problems []string

	if v.Request.Kind != v.Expect.Kind {
		problems = append(problems, fmt.Sprintf("expect.kind %q does not match request.kind %q", v.Expect.Kind, v.Request.Kind))
	}
	if v.Request.CurrencyCode == "" {
		problems = append(problems, "request.currency_code is empty")
	}

	switch v.Request.Kind {
	case KindAccount:
		acct := shares.ShareAccountStatusFromInt(v.Request.AccountStatusID)
		if acct == shares.ShareAccountStatusInvalid {
			problems = append(problems, fmt.Sprintf("request.account_status_id %d is not a known share-account status", v.Request.AccountStatusID))
		} else if v.Expect.AccountStatusStored != acct.StoredValue() {
			problems = append(problems, fmt.Sprintf(
				"expect.account_status_stored %d does not match the known stored value %d for request.account_status_id %d",
				v.Expect.AccountStatusStored, acct.StoredValue(), v.Request.AccountStatusID))
		}
		purch := shares.PurchaseStatusFromInt(v.Request.PurchasedStatusID)
		if purch == shares.PurchaseStatusInvalid {
			problems = append(problems, fmt.Sprintf("request.purchased_status_id %d is not a known purchase status", v.Request.PurchasedStatusID))
		} else if v.Expect.PurchasedStatusStored != purch.StoredValue() {
			problems = append(problems, fmt.Sprintf(
				"expect.purchased_status_stored %d does not match the known stored value %d for request.purchased_status_id %d",
				v.Expect.PurchasedStatusStored, purch.StoredValue(), v.Request.PurchasedStatusID))
		}
		if _, err := shares.MinorUnitsFromDecimalText(v.Request.PurchasedPrice, shares.MNTMinorDigits); err != nil {
			problems = append(problems, fmt.Sprintf("request.purchased_price: %v", err))
		}
		if _, err := shares.MinorUnitsFromDecimalText(v.Request.PurchasedAmount, shares.MNTMinorDigits); err != nil {
			problems = append(problems, fmt.Sprintf("request.purchased_amount: %v", err))
		}
		if v.Request.TotalApprovedShares < 0 {
			problems = append(problems, fmt.Sprintf("request.total_approved_shares %d must be non-negative", v.Request.TotalApprovedShares))
		}
		if v.Request.PurchasedShares < 0 {
			problems = append(problems, fmt.Sprintf("request.purchased_shares %d must be non-negative", v.Request.PurchasedShares))
		}
		if !isIntegerMinorString(v.Expect.PurchasedPriceMinor) {
			problems = append(problems, fmt.Sprintf("expect.purchased_price_minor %q is not a non-negative integer minor-unit amount", v.Expect.PurchasedPriceMinor))
		}
		if !isIntegerMinorString(v.Expect.PurchasedAmountMinor) {
			problems = append(problems, fmt.Sprintf("expect.purchased_amount_minor %q is not a non-negative integer minor-unit amount", v.Expect.PurchasedAmountMinor))
		}
	case KindDividend:
		if _, err := shares.MinorUnitsFromDecimalText(v.Request.DividendAmount, shares.MNTMinorDigits); err != nil {
			problems = append(problems, fmt.Sprintf("request.dividend_amount: %v", err))
		}
		if !isIntegerMinorString(v.Expect.DividendAmountMinor) {
			problems = append(problems, fmt.Sprintf("expect.dividend_amount_minor %q is not a non-negative integer minor-unit amount", v.Expect.DividendAmountMinor))
		}
	default:
		problems = append(problems, fmt.Sprintf("request.kind %q: this harness grades only kinds %q and %q", v.Request.Kind, KindAccount, KindDividend))
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
