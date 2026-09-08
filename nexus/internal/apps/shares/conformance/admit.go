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
	switch v.Oracle.Seam {
	case SeamShareAccount:
		if v.Request.Kind != KindAccount {
			problems = append(problems, fmt.Sprintf("oracle.seam %q requires request.kind %q, got %q", SeamShareAccount, KindAccount, v.Request.Kind))
		}
	case SeamShareDividend:
		if v.Request.Kind != KindDividend {
			problems = append(problems, fmt.Sprintf("oracle.seam %q requires request.kind %q, got %q", SeamShareDividend, KindDividend, v.Request.Kind))
		}
	case SeamShareProduct:
		if v.Request.Kind != KindProduct {
			problems = append(problems, fmt.Sprintf("oracle.seam %q requires request.kind %q, got %q", SeamShareProduct, KindProduct, v.Request.Kind))
		}
	default:
		problems = append(problems, fmt.Sprintf("oracle.seam %q: this harness grades only seams %q, %q and %q",
			v.Oracle.Seam, SeamShareAccount, SeamShareDividend, SeamShareProduct))
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
		if v.Request.TotalApprovedShares < 0 {
			problems = append(problems, fmt.Sprintf("request.total_approved_shares %d must be non-negative", v.Request.TotalApprovedShares))
		}
		if v.Request.TotalPendingShares < 0 {
			problems = append(problems, fmt.Sprintf("request.total_pending_shares %d must be non-negative", v.Request.TotalPendingShares))
		}
		if v.Request.PurchasedShares != 0 {
			// A purchase group is present: the read-back carried it, so every
			// purchase field must be stated, on both sides.
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
			if v.Request.PurchasedShares < 0 {
				problems = append(problems, fmt.Sprintf("request.purchased_shares %d must be non-negative", v.Request.PurchasedShares))
			}
			if !isIntegerMinorString(v.Expect.PurchasedPriceMinor) {
				problems = append(problems, fmt.Sprintf("expect.purchased_price_minor %q is not a non-negative integer minor-unit amount", v.Expect.PurchasedPriceMinor))
			}
			if !isIntegerMinorString(v.Expect.PurchasedAmountMinor) {
				problems = append(problems, fmt.Sprintf("expect.purchased_amount_minor %q is not a non-negative integer minor-unit amount", v.Expect.PurchasedAmountMinor))
			}
		} else {
			// No purchase group: a share-account list row read-back carries no
			// purchase rows, so both sides must be silent about the group.
			if v.Request.PurchasedPrice != "" || v.Request.PurchasedAmount != "" || v.Request.PurchasedStatusID != 0 {
				problems = append(problems, "request.purchased_shares is 0 but a purchase field is set: a list row read-back carries no purchase group")
			}
			if v.Expect.PurchasedShares != 0 || v.Expect.PurchasedPriceMinor != "" || v.Expect.PurchasedAmountMinor != "" || v.Expect.PurchasedStatusStored != 0 {
				problems = append(problems, "request.purchased_shares is 0 but expect carries a purchase group")
			}
		}
	case KindDividend:
		if _, err := shares.MinorUnitsFromDecimalText(v.Request.DividendAmount, shares.MNTMinorDigits); err != nil {
			problems = append(problems, fmt.Sprintf("request.dividend_amount: %v", err))
		}
		if !isIntegerMinorString(v.Expect.DividendAmountMinor) {
			problems = append(problems, fmt.Sprintf("expect.dividend_amount_minor %q is not a non-negative integer minor-unit amount", v.Expect.DividendAmountMinor))
		}
		if v.Request.DividendStatusID != 0 {
			st := shares.ShareAccountDividendStatusFromInt(v.Request.DividendStatusID)
			if st == shares.ShareAccountDividendStatusInvalid {
				problems = append(problems, fmt.Sprintf("request.dividend_status_id %d is not a known share-account dividend status", v.Request.DividendStatusID))
			} else if v.Expect.DividendStatusStored != st.StoredValue() {
				problems = append(problems, fmt.Sprintf(
					"expect.dividend_status_stored %d does not match the known stored value %d for request.dividend_status_id %d",
					v.Expect.DividendStatusStored, st.StoredValue(), v.Request.DividendStatusID))
			}
		} else if v.Expect.DividendStatusStored != 0 {
			problems = append(problems, "request.dividend_status_id is 0 but expect.dividend_status_stored is non-zero")
		}
	case KindProduct:
		if _, err := shares.MinorUnitsFromDecimalText(v.Request.UnitPrice, shares.MNTMinorDigits); err != nil {
			problems = append(problems, fmt.Sprintf("request.unit_price: %v", err))
		}
		if _, err := shares.MinorUnitsFromDecimalText(v.Request.ShareCapital, shares.MNTMinorDigits); err != nil {
			problems = append(problems, fmt.Sprintf("request.share_capital: %v", err))
		}
		if v.Request.TotalShares < 0 {
			problems = append(problems, fmt.Sprintf("request.total_shares %d must be non-negative", v.Request.TotalShares))
		}
		if !isIntegerMinorString(v.Expect.UnitPriceMinor) {
			problems = append(problems, fmt.Sprintf("expect.unit_price_minor %q is not a non-negative integer minor-unit amount", v.Expect.UnitPriceMinor))
		}
		if !isIntegerMinorString(v.Expect.ShareCapitalMinor) {
			problems = append(problems, fmt.Sprintf("expect.share_capital_minor %q is not a non-negative integer minor-unit amount", v.Expect.ShareCapitalMinor))
		}
	default:
		problems = append(problems, fmt.Sprintf("request.kind %q: this harness grades only kinds %q, %q and %q",
			v.Request.Kind, KindAccount, KindDividend, KindProduct))
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
