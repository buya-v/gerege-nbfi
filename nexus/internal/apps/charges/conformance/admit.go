package conformance

import (
	"fmt"
	"sort"

	"github.com/gerege/nexus/internal/apps/charges"
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
	if v.Context != ChargesContext || !IsSchemaContext(v.Context) {
		problems = append(problems, fmt.Sprintf("context %q is not %q", v.Context, ChargesContext))
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
	if v.Oracle.Seam != SeamChargeEvaluate {
		problems = append(problems, fmt.Sprintf("oracle.seam %q: this harness grades only seam %q", v.Oracle.Seam, SeamChargeEvaluate))
	}
	if v.Oracle.FineractCommit == "" {
		problems = append(problems, "oracle.fineract_commit is empty")
	} else if opts.Pin != nil && v.Oracle.FineractCommit != opts.Pin.FineractCommit {
		problems = append(problems, fmt.Sprintf(
			"oracle.fineract_commit %q does not match the pinned commit %q", v.Oracle.FineractCommit, opts.Pin.FineractCommit))
	}

	_, appliesToOK := charges.ChargeAppliesToFromStoredValue(v.Request.AppliesTo)
	if !appliesToOK {
		problems = append(problems, fmt.Sprintf("request.applies_to %d is not a known stored value", v.Request.AppliesTo))
	}
	_, timeTypeOK := charges.ChargeTimeTypeFromStoredValue(v.Request.TimeType)
	if !timeTypeOK {
		problems = append(problems, fmt.Sprintf("request.time_type %d is not a known stored value", v.Request.TimeType))
	}
	calcType, calcTypeOK := charges.ChargeCalculationTypeFromStoredValue(v.Request.CalculationType)
	if !calcTypeOK {
		problems = append(problems, fmt.Sprintf("request.calculation_type %d is not a known stored value", v.Request.CalculationType))
	}
	_, paymentModeOK := charges.ChargePaymentModeFromStoredValue(v.Request.PaymentMode)
	if !paymentModeOK {
		problems = append(problems, fmt.Sprintf("request.payment_mode %d is not a known stored value", v.Request.PaymentMode))
	}

	if amount, err := parseMinorText(v.Request.AmountMinor); err != nil {
		problems = append(problems, fmt.Sprintf("request.amount_minor: %v", err))
	} else if amount < 0 {
		problems = append(problems, fmt.Sprintf("request.amount_minor %d is negative", amount))
	}
	if v.Request.Percentage < 0 {
		problems = append(problems, fmt.Sprintf("request.percentage %d is negative", v.Request.Percentage))
	}

	if v.Request.MinCapMinor != nil {
		if m, err := parseMinorText(*v.Request.MinCapMinor); err != nil {
			problems = append(problems, fmt.Sprintf("request.min_cap_minor: %v", err))
		} else if m < 0 {
			problems = append(problems, fmt.Sprintf("request.min_cap_minor %d is negative", m))
		}
	}
	if v.Request.MaxCapMinor != nil {
		if m, err := parseMinorText(*v.Request.MaxCapMinor); err != nil {
			problems = append(problems, fmt.Sprintf("request.max_cap_minor: %v", err))
		} else if m < 0 {
			problems = append(problems, fmt.Sprintf("request.max_cap_minor %d is negative", m))
		}
	}

	// A base amount is required only when the expectation is a percentage fee;
	// that is asserted in the ExpectFee branch below.
	if v.Request.BaseAmountMinor != "" {
		if base, err := parseMinorText(v.Request.BaseAmountMinor); err != nil {
			problems = append(problems, fmt.Sprintf("request.base_amount_minor: %v", err))
		} else if base < 0 {
			problems = append(problems, fmt.Sprintf("request.base_amount_minor %d is negative", base))
		}
	}

	switch v.Expect.Kind {
	case ExpectValidation:
		if len(v.Expect.ValidationCodes) == 0 {
			problems = append(problems, "expect.kind \"validation\" with an empty validation_codes list: "+
				"a validation vector must expect at least one code, or it grades nothing")
		}
		if v.Expect.FeeMinor != "" {
			problems = append(problems, "expect.kind \"validation\" must not carry a fee_minor; "+
				"the fee is asserted only by a \"fee\" vector")
		}
	case ExpectFee:
		if !calcType.IsFlat() && !calcType.IsPercentageOfAmount() && !calcType.IsPercentageOfDisbursementAmount() {
			problems = append(problems, fmt.Sprintf(
				"expect.kind \"fee\" with calculation type %d: the fee of an interest-based charge is not "+
					"computable from a base amount alone and cannot be graded here", v.Request.CalculationType))
		}
		if !calcType.IsFlat() && v.Request.BaseAmountMinor == "" {
			problems = append(problems, "expect.kind \"fee\" with a percentage calculation type "+
				"requires request.base_amount_minor")
		}
		if fee, err := parseMinorText(v.Expect.FeeMinor); err != nil {
			problems = append(problems, fmt.Sprintf("expect.fee_minor: %v", err))
		} else if fee < 0 {
			problems = append(problems, fmt.Sprintf("expect.fee_minor %d is negative", fee))
		}
	default:
		problems = append(problems, fmt.Sprintf("expect.kind %q: want %q or %q", v.Expect.Kind, ExpectValidation, ExpectFee))
	}

	problems = append(problems, checkGradedAgainst(v)...)

	sort.Strings(problems)
	return problems
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
