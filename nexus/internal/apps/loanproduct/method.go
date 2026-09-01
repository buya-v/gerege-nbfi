package loanproduct

import "fmt"

// InterestMethod is m_product_loan.interest_method_enum — Fineract's
// InterestMethod. [VERIFIED: InterestMethod.java:24-27 — DECLINING_BALANCE(0),
// FLAT(1), INVALID(2)]
//
// It is the single most consequential discriminator in the whole loan-product
// surface: declining balance and flat interest produce different schedules for
// the same nominal rate, principal and term. The schedule generator in
// nexus/internal/apps/loanschedule is the authority on what each one MEANS; this
// type only declares the stored-value <-> enum mapping so the two packages agree.
type InterestMethod int32

const (
	InterestDecliningBalance InterestMethod = iota
	InterestFlat
	InterestInvalid
)

var interestMethodStoredValue = map[InterestMethod]int32{
	InterestDecliningBalance: 0,
	InterestFlat:             1,
	InterestInvalid:          2,
}

var interestMethodCode = map[InterestMethod]string{
	InterestDecliningBalance: "interestType.declining.balance",
	InterestFlat:             "interestType.flat",
	InterestInvalid:          "interestType.invalid",
}

var interestMethodName = map[InterestMethod]string{
	InterestDecliningBalance: "DECLINING_BALANCE",
	InterestFlat:             "FLAT",
	InterestInvalid:          "INVALID",
}

var interestMethodFromStored = map[int32]InterestMethod{}

// StoredValue returns m_product_loan.interest_method_enum.
func (m InterestMethod) StoredValue() int32 {
	v, ok := interestMethodStoredValue[m]
	if !ok {
		panic(fmt.Sprintf("loanproduct: unknown InterestMethod %d", int32(m)))
	}
	return v
}

// Code returns the i18n code emitted on the product read.
func (m InterestMethod) Code() string { return interestMethodCode[m] }

func (m InterestMethod) String() string {
	if n, ok := interestMethodName[m]; ok {
		return n
	}
	return fmt.Sprintf("InterestMethod(%d)", int32(m))
}

// InterestMethodFromStoredValue decodes interest_method_enum. ok is false
// outside 0..2, matching InterestMethod.fromInt's INVALID fallback
// [VERIFIED: InterestMethod.java:45-49].
func InterestMethodFromStoredValue(v int32) (InterestMethod, bool) {
	m, ok := interestMethodFromStored[v]
	return m, ok
}

// IsDecliningBalance and IsFlat mirror InterestMethod.isDecliningBalance /
// isFlat, which compare getValue() and never ordinal()
// [VERIFIED: InterestMethod.java:52-59].
func (m InterestMethod) IsDecliningBalance() bool { return m == InterestDecliningBalance }
func (m InterestMethod) IsFlat() bool             { return m == InterestFlat }

// AmortizationMethod is m_product_loan.amortization_method_enum — Fineract's
// AmortizationMethod. [VERIFIED: AmortizationMethod.java:23-26 —
// EQUAL_PRINCIPAL(0), EQUAL_INSTALLMENTS(1), INVALID(2)]
type AmortizationMethod int32

const (
	AmortizationEqualPrincipal AmortizationMethod = iota
	AmortizationEqualInstallments
	AmortizationInvalid
)

var amortizationMethodStoredValue = map[AmortizationMethod]int32{
	AmortizationEqualPrincipal:    0,
	AmortizationEqualInstallments: 1,
	AmortizationInvalid:           2,
}

var amortizationMethodCode = map[AmortizationMethod]string{
	AmortizationEqualPrincipal:    "amortizationType.equal.principal",
	AmortizationEqualInstallments: "amortizationType.equal.installments",
	AmortizationInvalid:           "amortizationType.invalid",
}

var amortizationMethodName = map[AmortizationMethod]string{
	AmortizationEqualPrincipal:    "EQUAL_PRINCIPAL",
	AmortizationEqualInstallments: "EQUAL_INSTALLMENTS",
	AmortizationInvalid:           "INVALID",
}

var amortizationMethodFromStored = map[int32]AmortizationMethod{}

// StoredValue returns m_product_loan.amortization_method_enum.
func (m AmortizationMethod) StoredValue() int32 {
	v, ok := amortizationMethodStoredValue[m]
	if !ok {
		panic(fmt.Sprintf("loanproduct: unknown AmortizationMethod %d", int32(m)))
	}
	return v
}

// Code returns the i18n code emitted on the product read.
func (m AmortizationMethod) Code() string { return amortizationMethodCode[m] }

func (m AmortizationMethod) String() string {
	if n, ok := amortizationMethodName[m]; ok {
		return n
	}
	return fmt.Sprintf("AmortizationMethod(%d)", int32(m))
}

// AmortizationMethodFromStoredValue decodes amortization_method_enum. ok is
// false outside 0..2, matching AmortizationMethod.fromInt's INVALID fallback
// [VERIFIED: AmortizationMethod.java:47-52].
func AmortizationMethodFromStoredValue(v int32) (AmortizationMethod, bool) {
	m, ok := amortizationMethodFromStored[v]
	return m, ok
}

// IsEqualInstallment and IsEqualPrincipal mirror
// AmortizationMethod.isEqualInstallment / isEqualPrincipal
// [VERIFIED: AmortizationMethod.java:54-61].
func (m AmortizationMethod) IsEqualInstallment() bool { return m == AmortizationEqualInstallments }
func (m AmortizationMethod) IsEqualPrincipal() bool   { return m == AmortizationEqualPrincipal }

// InterestCalculationPeriodMethod is
// m_product_loan.interest_calculated_in_period_enum — Fineract's
// InterestCalculationPeriodMethod. [VERIFIED: InterestCalculationPeriodMethod.java:23-26 —
// DAILY(0), SAME_AS_REPAYMENT_PERIOD(1), INVALID(2)]
type InterestCalculationPeriodMethod int32

const (
	InterestCalcDaily InterestCalculationPeriodMethod = iota
	InterestCalcSameAsRepaymentPeriod
	InterestCalcInvalid
)

var interestCalcPeriodStoredValue = map[InterestCalculationPeriodMethod]int32{
	InterestCalcDaily:                 0,
	InterestCalcSameAsRepaymentPeriod: 1,
	InterestCalcInvalid:               2,
}

var interestCalcPeriodCode = map[InterestCalculationPeriodMethod]string{
	InterestCalcDaily:                 "interestCalculationPeriodType.daily",
	InterestCalcSameAsRepaymentPeriod: "interestCalculationPeriodType.same.as.repayment.period",
	InterestCalcInvalid:               "interestCalculationPeriodType.invalid",
}

var interestCalcPeriodName = map[InterestCalculationPeriodMethod]string{
	InterestCalcDaily:                 "DAILY",
	InterestCalcSameAsRepaymentPeriod: "SAME_AS_REPAYMENT_PERIOD",
	InterestCalcInvalid:               "INVALID",
}

var interestCalcPeriodFromStored = map[int32]InterestCalculationPeriodMethod{}

// StoredValue returns m_product_loan.interest_calculated_in_period_enum.
func (m InterestCalculationPeriodMethod) StoredValue() int32 {
	v, ok := interestCalcPeriodStoredValue[m]
	if !ok {
		panic(fmt.Sprintf("loanproduct: unknown InterestCalculationPeriodMethod %d", int32(m)))
	}
	return v
}

// Code returns the i18n code emitted on the product read.
func (m InterestCalculationPeriodMethod) Code() string { return interestCalcPeriodCode[m] }

func (m InterestCalculationPeriodMethod) String() string {
	if n, ok := interestCalcPeriodName[m]; ok {
		return n
	}
	return fmt.Sprintf("InterestCalculationPeriodMethod(%d)", int32(m))
}

// InterestCalculationPeriodMethodFromStoredValue decodes
// interest_calculated_in_period_enum. ok is false outside 0..2, matching
// InterestCalculationPeriodMethod.fromInt's INVALID fallback
// [VERIFIED: InterestCalculationPeriodMethod.java:45-49].
func InterestCalculationPeriodMethodFromStoredValue(v int32) (InterestCalculationPeriodMethod, bool) {
	m, ok := interestCalcPeriodFromStored[v]
	return m, ok
}

// IsDaily and IsSameAsRepaymentPeriod mirror
// InterestCalculationPeriodMethod.isDaily / isSameAsRepaymentPeriod
// [VERIFIED: InterestCalculationPeriodMethod.java:51-58].
func (m InterestCalculationPeriodMethod) IsDaily() bool { return m == InterestCalcDaily }
func (m InterestCalculationPeriodMethod) IsSameAsRepaymentPeriod() bool {
	return m == InterestCalcSameAsRepaymentPeriod
}

func init() {
	for m, v := range interestMethodStoredValue {
		if _, dup := interestMethodFromStored[v]; dup {
			panic(fmt.Sprintf("loanproduct: interest method encode table is not injective at %d", v))
		}
		interestMethodFromStored[v] = m
	}
	for m, v := range amortizationMethodStoredValue {
		if _, dup := amortizationMethodFromStored[v]; dup {
			panic(fmt.Sprintf("loanproduct: amortization method encode table is not injective at %d", v))
		}
		amortizationMethodFromStored[v] = m
	}
	for m, v := range interestCalcPeriodStoredValue {
		if _, dup := interestCalcPeriodFromStored[v]; dup {
			panic(fmt.Sprintf("loanproduct: interest calculation period encode table is not injective at %d", v))
		}
		interestCalcPeriodFromStored[v] = m
	}
}
