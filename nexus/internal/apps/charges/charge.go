package charges

import "fmt"

// Charge is the Go port of the Fineract Charge aggregate, reduced to the fields
// and invariants that govern fee construction and amount computation. The
// persistence-only fields (GL account, tax-group id, fee frequency/interval,
// free-withdrawal/payment-type switches) are deliberately out of scope for this
// slice and belong to their owning contexts.
//
// A Charge is either flat (Amount is authoritative) or percentage-based
// (Percentage is authoritative); Fineract stores both behind the single
// DECIMAL(19,6) amountOrPercentage column and this port keeps them as two typed
// fields so a percentage is never mistaken for money.
type Charge struct {
	Name            string
	CurrencyCode    string
	Amount          MinorUnits // flat charge amount, authoritative when calculation is FLAT
	Percentage      Percent    // authoritative when calculation is percentage-based
	AppliesTo       ChargeAppliesTo
	TimeType        ChargeTimeType
	CalculationType ChargeCalculationType
	PaymentMode     ChargePaymentMode
	MinCap          *MinorUnits // only assigned for %-of-disbursement/%-of-approved
	MaxCap          *MinorUnits
	Penalty         bool
	Active          bool
	Deleted         bool
}

// ValidationError is a single construction-time invariant violation. Field is
// the parameter name Fineract reports, Value the offending stored value.
type ValidationError struct {
	Field string
	Value any
	Code  string
}

func (e ValidationError) Error() string {
	return fmt.Sprintf("charges: %s (%v): %s", e.Field, e.Value, e.Code)
}

// ValidationErrors is the ordered list of construction failures returned by
// Charge.Validate. An empty slice is success, matching the oracle which throws
// only when dataValidationErrors is non-empty.
type ValidationErrors []ValidationError

func (e ValidationErrors) Error() string {
	if len(e) == 0 {
		return ""
	}
	return fmt.Sprintf("charges: %d validation error(s), first: %s", len(e), e[0])
}

// Predicates mirror Charge.java:300-352.

func (c Charge) IsActive() bool  { return c.Active }
func (c Charge) IsPenalty() bool { return c.Penalty }
func (c Charge) IsDeleted() bool { return c.Deleted }

func (c Charge) IsLoanCharge() bool               { return c.AppliesTo.IsLoanCharge() }
func (c Charge) IsSavingsCharge() bool            { return c.AppliesTo.IsSavingsCharge() }
func (c Charge) IsClientCharge() bool             { return c.AppliesTo.IsClientCharge() }
func (c Charge) IsSharesCharge() bool             { return c.AppliesTo.IsSharesCharge() }
func (c Charge) IsWorkingCapitalLoanCharge() bool { return c.AppliesTo.IsWorkingCapitalLoanCharge() }

func (c Charge) IsAllowedLoanChargeTime() bool    { return c.TimeType.IsAllowedLoanChargeTime() }
func (c Charge) IsAllowedSavingsChargeTime() bool { return c.TimeType.IsAllowedSavingsChargeTime() }

func (c Charge) IsAllowedSavingsChargeCalculationType() bool {
	return c.CalculationType.IsAllowedSavingsChargeCalculationType()
}

func (c Charge) IsAllowedClientChargeCalculationType() bool {
	return c.CalculationType.IsAllowedClientChargeCalculationType()
}

// IsPercentageOfApprovedAmount mirrors Charge.java:344-346: it is the
// PERCENT_OF_AMOUNT calculation (Fineract's legacy name for it).
func (c Charge) IsPercentageOfApprovedAmount() bool {
	return c.CalculationType.IsPercentageOfAmount()
}

func (c Charge) IsPercentageOfDisbursementAmount() bool {
	return c.CalculationType.IsPercentageOfDisbursementAmount()
}

// IsOverdueInstallment mirrors Charge.java:684-686.
func (c Charge) IsOverdueInstallment() bool {
	return c.TimeType.IsOverdueInstallment()
}

// Validate ports the construction invariants of Charge's constructor
// [VERIFIED: Charge.java:240-300]. It does NOT set the min/max caps — the
// caller assigns MinCap/MaxCap only when IsPercentageOfDisbursementAmount or
// IsPercentageOfApprovedAmount, exactly as the oracle assigns them
// conditionally at Charge.java:291-294.
func (c Charge) Validate() ValidationErrors {
	var errs ValidationErrors
	add := func(field string, value any, code string) {
		errs = append(errs, ValidationError{Field: field, Value: value, Code: code})
	}

	if c.IsSavingsCharge() {
		if !c.IsAllowedSavingsChargeTime() {
			add("chargeTimeType", c.TimeType.StoredValue(), "not.allowed.charge.time.for.savings")
		}
		if !c.IsAllowedSavingsChargeCalculationType() {
			add("chargeCalculationType", c.CalculationType.StoredValue(), "not.allowed.charge.calculation.type.for.savings")
		}
		if !(c.TimeType.IsWithdrawalFee() || c.TimeType.IsSavingsNoActivityFee()) &&
			c.CalculationType.IsPercentageOfAmount() {
			add("chargeCalculationType", c.CalculationType.StoredValue(),
				"savings.charge.calculation.type.percentage.allowed.only.for.withdrawal.or.NoActivity")
		}
	} else if c.IsLoanCharge() {
		if c.Penalty && (c.TimeType.IsTimeOfDisbursement() || c.TimeType.IsTrancheDisbursement()) {
			add("name", c.Name, "charge.due.at.disbursement.cannot.be.penalty")
		}
		if !c.Penalty && c.TimeType.IsOverdueInstallment() {
			add("name", c.Name, "charge.must.be.penalty")
		}
		if !c.IsAllowedLoanChargeTime() {
			add("chargeTimeType", c.TimeType.StoredValue(), "not.allowed.charge.time.for.loan")
		}
	}

	return errs
}
