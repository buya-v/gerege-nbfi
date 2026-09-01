package charges

import "fmt"

// ChargeTimeType is m_charge.charge_time_enum — Fineract's ChargeTimeType.
// [VERIFIED: ChargeTimeType.java:25-41 — INVALID(0), DISBURSEMENT(1),
// SPECIFIED_DUE_DATE(2), SAVINGS_ACTIVATION(3), SAVINGS_CLOSURE(4),
// WITHDRAWAL_FEE(5), ANNUAL_FEE(6), MONTHLY_FEE(7), INSTALMENT_FEE(8),
// OVERDUE_INSTALLMENT(9), OVERDRAFT_FEE(10), WEEKLY_FEE(11),
// TRANCHE_DISBURSEMENT(12), SHAREACCOUNT_ACTIVATION(13), SHARE_PURCHASE(14),
// SHARE_REDEEM(15), SAVINGS_NOACTIVITY_FEE(16)]
type ChargeTimeType int32

const (
	ChargeTimeInvalid ChargeTimeType = iota
	ChargeTimeDisbursement
	ChargeTimeSpecifiedDueDate
	ChargeTimeSavingsActivation
	ChargeTimeSavingsClosure
	ChargeTimeWithdrawalFee
	ChargeTimeAnnualFee
	ChargeTimeMonthlyFee
	ChargeTimeInstalmentFee
	ChargeTimeOverdueInstallment
	ChargeTimeOverdraftFee
	ChargeTimeWeeklyFee
	ChargeTimeTrancheDisbursement
	ChargeTimeShareAccountActivation
	ChargeTimeSharePurchase
	ChargeTimeShareRedeem
	ChargeTimeSavingsNoActivityFee
)

var chargeTimeStoredValue = map[ChargeTimeType]int32{
	ChargeTimeInvalid:                0,
	ChargeTimeDisbursement:           1,
	ChargeTimeSpecifiedDueDate:       2,
	ChargeTimeSavingsActivation:      3,
	ChargeTimeSavingsClosure:         4,
	ChargeTimeWithdrawalFee:          5,
	ChargeTimeAnnualFee:              6,
	ChargeTimeMonthlyFee:             7,
	ChargeTimeInstalmentFee:          8,
	ChargeTimeOverdueInstallment:     9,
	ChargeTimeOverdraftFee:           10,
	ChargeTimeWeeklyFee:              11,
	ChargeTimeTrancheDisbursement:    12,
	ChargeTimeShareAccountActivation: 13,
	ChargeTimeSharePurchase:          14,
	ChargeTimeShareRedeem:            15,
	ChargeTimeSavingsNoActivityFee:   16,
}

var chargeTimeCode = map[ChargeTimeType]string{
	ChargeTimeInvalid:                "chargeTimeType.invalid",
	ChargeTimeDisbursement:           "chargeTimeType.disbursement",
	ChargeTimeSpecifiedDueDate:       "chargeTimeType.specifiedDueDate",
	ChargeTimeSavingsActivation:      "chargeTimeType.savingsActivation",
	ChargeTimeSavingsClosure:         "chargeTimeType.savingsClosure",
	ChargeTimeWithdrawalFee:          "chargeTimeType.withdrawalFee",
	ChargeTimeAnnualFee:              "chargeTimeType.annualFee",
	ChargeTimeMonthlyFee:             "chargeTimeType.monthlyFee",
	ChargeTimeInstalmentFee:          "chargeTimeType.instalmentFee",
	ChargeTimeOverdueInstallment:     "chargeTimeType.overdueInstallment",
	ChargeTimeOverdraftFee:           "chargeTimeType.overdraftFee",
	ChargeTimeWeeklyFee:              "chargeTimeType.weeklyFee",
	ChargeTimeTrancheDisbursement:    "chargeTimeType.tranchedisbursement",
	ChargeTimeShareAccountActivation: "chargeTimeType.activation",
	ChargeTimeSharePurchase:          "chargeTimeType.sharespurchase",
	ChargeTimeShareRedeem:            "chargeTimeType.sharesredeem",
	ChargeTimeSavingsNoActivityFee:   "chargeTimeType.savingsNoActivityFee",
}

var chargeTimeName = map[ChargeTimeType]string{
	ChargeTimeInvalid:                "INVALID",
	ChargeTimeDisbursement:           "DISBURSEMENT",
	ChargeTimeSpecifiedDueDate:       "SPECIFIED_DUE_DATE",
	ChargeTimeSavingsActivation:      "SAVINGS_ACTIVATION",
	ChargeTimeSavingsClosure:         "SAVINGS_CLOSURE",
	ChargeTimeWithdrawalFee:          "WITHDRAWAL_FEE",
	ChargeTimeAnnualFee:              "ANNUAL_FEE",
	ChargeTimeMonthlyFee:             "MONTHLY_FEE",
	ChargeTimeInstalmentFee:          "INSTALMENT_FEE",
	ChargeTimeOverdueInstallment:     "OVERDUE_INSTALLMENT",
	ChargeTimeOverdraftFee:           "OVERDRAFT_FEE",
	ChargeTimeWeeklyFee:              "WEEKLY_FEE",
	ChargeTimeTrancheDisbursement:    "TRANCHE_DISBURSEMENT",
	ChargeTimeShareAccountActivation: "SHAREACCOUNT_ACTIVATION",
	ChargeTimeSharePurchase:          "SHARE_PURCHASE",
	ChargeTimeShareRedeem:            "SHARE_REDEEM",
	ChargeTimeSavingsNoActivityFee:   "SAVINGS_NOACTIVITY_FEE",
}

var chargeTimeFromStored = map[int32]ChargeTimeType{}

// StoredValue returns m_charge.charge_time_enum.
func (t ChargeTimeType) StoredValue() int32 {
	v, ok := chargeTimeStoredValue[t]
	if !ok {
		panic(fmt.Sprintf("charges: unknown ChargeTimeType %d", int32(t)))
	}
	return v
}

// Code returns the i18n code emitted on the charge read.
func (t ChargeTimeType) Code() string { return chargeTimeCode[t] }

func (t ChargeTimeType) String() string {
	if n, ok := chargeTimeName[t]; ok {
		return n
	}
	return fmt.Sprintf("ChargeTimeType(%d)", int32(t))
}

// ChargeTimeTypeFromStoredValue decodes m_charge.charge_time_enum. ok is false
// outside [0,16], matching ChargeTimeType.fromInt's INVALID fallback
// [VERIFIED: ChargeTimeType.java:89-142].
func ChargeTimeTypeFromStoredValue(v int32) (ChargeTimeType, bool) {
	t, ok := chargeTimeFromStored[v]
	return t, ok
}

// Predicates mirror ChargeTimeType.java:154-237.

func (t ChargeTimeType) IsTimeOfDisbursement() bool     { return t == ChargeTimeDisbursement }
func (t ChargeTimeType) IsOnSpecifiedDueDate() bool     { return t == ChargeTimeSpecifiedDueDate }
func (t ChargeTimeType) IsSavingsActivation() bool      { return t == ChargeTimeSavingsActivation }
func (t ChargeTimeType) IsSavingsClosure() bool         { return t == ChargeTimeSavingsClosure }
func (t ChargeTimeType) IsWithdrawalFee() bool          { return t == ChargeTimeWithdrawalFee }
func (t ChargeTimeType) IsSavingsNoActivityFee() bool   { return t == ChargeTimeSavingsNoActivityFee }
func (t ChargeTimeType) IsAnnualFee() bool              { return t == ChargeTimeAnnualFee }
func (t ChargeTimeType) IsMonthlyFee() bool             { return t == ChargeTimeMonthlyFee }
func (t ChargeTimeType) IsWeeklyFee() bool              { return t == ChargeTimeWeeklyFee }
func (t ChargeTimeType) IsInstalmentFee() bool          { return t == ChargeTimeInstalmentFee }
func (t ChargeTimeType) IsSpecifiedDueDate() bool       { return t == ChargeTimeSpecifiedDueDate }
func (t ChargeTimeType) IsOverdueInstallment() bool     { return t == ChargeTimeOverdueInstallment }
func (t ChargeTimeType) IsOverdraftFee() bool           { return t == ChargeTimeOverdraftFee }
func (t ChargeTimeType) IsTrancheDisbursement() bool    { return t == ChargeTimeTrancheDisbursement }
func (t ChargeTimeType) IsShareAccountActivation() bool { return t == ChargeTimeShareAccountActivation }
func (t ChargeTimeType) IsSharesPurchase() bool         { return t == ChargeTimeSharePurchase }
func (t ChargeTimeType) IsSharesRedeem() bool           { return t == ChargeTimeShareRedeem }

// IsDisbursementOrTrancheDisbursementCharge mirrors the same-named helper
// [VERIFIED: ChargeTimeType.java:235-236].
func (t ChargeTimeType) IsDisbursementOrTrancheDisbursementCharge() bool {
	return t.IsTimeOfDisbursement() || t.IsTrancheDisbursement()
}

// IsAllowedLoanChargeTime is the union of loan-legal charge times
// [VERIFIED: ChargeTimeType.java:202-204].
func (t ChargeTimeType) IsAllowedLoanChargeTime() bool {
	return t.IsTimeOfDisbursement() || t.IsOnSpecifiedDueDate() || t.IsInstalmentFee() ||
		t.IsOverdueInstallment() || t.IsTrancheDisbursement()
}

// IsAllowedSavingsChargeTime mirrors the savings-legal union
// [VERIFIED: ChargeTimeType.java:210-212].
func (t ChargeTimeType) IsAllowedSavingsChargeTime() bool {
	return t.IsOnSpecifiedDueDate() || t.IsSavingsActivation() || t.IsSavingsClosure() ||
		t.IsWithdrawalFee() || t.IsAnnualFee() || t.IsMonthlyFee() || t.IsWeeklyFee() ||
		t.IsOverdraftFee() || t.IsSavingsNoActivityFee()
}

// ValidLoanStoredValues returns the stored values legal for a loan charge
// [VERIFIED: ChargeTimeType.java:61-64 validLoanValues].
func ValidLoanStoredValues() []int32 {
	return []int32{
		ChargeTimeDisbursement.StoredValue(),
		ChargeTimeSpecifiedDueDate.StoredValue(),
		ChargeTimeInstalmentFee.StoredValue(),
		ChargeTimeOverdueInstallment.StoredValue(),
		ChargeTimeTrancheDisbursement.StoredValue(),
	}
}

func init() {
	for t, v := range chargeTimeStoredValue {
		if _, dup := chargeTimeFromStored[v]; dup {
			panic(fmt.Sprintf("charges: charge time encode table is not injective at %d", v))
		}
		chargeTimeFromStored[v] = t
	}
}
