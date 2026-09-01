package charges

import "fmt"

// ChargeAppliesTo is m_charge.charge_applies_to_enum — Fineract's
// ChargeAppliesTo. [VERIFIED: ChargeAppliesTo.java:25-31 — INVALID(0),
// LOAN(1), SAVINGS(2), CLIENT(3), SHARES(4), WORKING_CAPITAL_LOAN(5)]
type ChargeAppliesTo int32

const (
	ChargeAppliesToInvalid ChargeAppliesTo = iota
	ChargeAppliesToLoan
	ChargeAppliesToSavings
	ChargeAppliesToClient
	ChargeAppliesToShares
	ChargeAppliesToWorkingCapitalLoan
)

var chargeAppliesToStoredValue = map[ChargeAppliesTo]int32{
	ChargeAppliesToInvalid:            0,
	ChargeAppliesToLoan:               1,
	ChargeAppliesToSavings:            2,
	ChargeAppliesToClient:             3,
	ChargeAppliesToShares:             4,
	ChargeAppliesToWorkingCapitalLoan: 5,
}

var chargeAppliesToName = map[ChargeAppliesTo]string{
	ChargeAppliesToInvalid:            "INVALID",
	ChargeAppliesToLoan:               "LOAN",
	ChargeAppliesToSavings:            "SAVINGS",
	ChargeAppliesToClient:             "CLIENT",
	ChargeAppliesToShares:             "SHARES",
	ChargeAppliesToWorkingCapitalLoan: "WORKING_CAPITAL_LOAN",
}

var chargeAppliesToFromStored = map[int32]ChargeAppliesTo{}

// StoredValue returns m_charge.charge_applies_to_enum.
func (a ChargeAppliesTo) StoredValue() int32 {
	v, ok := chargeAppliesToStoredValue[a]
	if !ok {
		panic(fmt.Sprintf("charges: unknown ChargeAppliesTo %d", int32(a)))
	}
	return v
}

func (a ChargeAppliesTo) String() string {
	if n, ok := chargeAppliesToName[a]; ok {
		return n
	}
	return fmt.Sprintf("ChargeAppliesTo(%d)", int32(a))
}

// ChargeAppliesToFromStoredValue decodes m_charge.charge_applies_to_enum. ok is
// false for 0/INVALID and values >5, matching ChargeAppliesTo.fromInt's INVALID
// fallback [VERIFIED: ChargeAppliesTo.java:46-72].
func ChargeAppliesToFromStoredValue(v int32) (ChargeAppliesTo, bool) {
	a, ok := chargeAppliesToFromStored[v]
	return a, ok
}

// Predicates mirror ChargeAppliesTo.java:75-95.

func (a ChargeAppliesTo) IsLoanCharge() bool    { return a == ChargeAppliesToLoan }
func (a ChargeAppliesTo) IsSavingsCharge() bool { return a == ChargeAppliesToSavings }
func (a ChargeAppliesTo) IsClientCharge() bool  { return a == ChargeAppliesToClient }
func (a ChargeAppliesTo) IsSharesCharge() bool  { return a == ChargeAppliesToShares }
func (a ChargeAppliesTo) IsWorkingCapitalLoanCharge() bool {
	return a == ChargeAppliesToWorkingCapitalLoan
}

// ValidStoredValues returns every non-INVALID applies-to stored value
// [VERIFIED: ChargeAppliesTo.java:97-101 validValues].
func ValidAppliesToStoredValues() []int32 {
	return []int32{
		ChargeAppliesToLoan.StoredValue(),
		ChargeAppliesToSavings.StoredValue(),
		ChargeAppliesToClient.StoredValue(),
		ChargeAppliesToShares.StoredValue(),
		ChargeAppliesToWorkingCapitalLoan.StoredValue(),
	}
}

func init() {
	for a, v := range chargeAppliesToStoredValue {
		if a == ChargeAppliesToInvalid {
			continue // INVALID (0) is not a decodable stored value
		}
		if _, dup := chargeAppliesToFromStored[v]; dup {
			panic(fmt.Sprintf("charges: charge applies-to encode table is not injective at %d", v))
		}
		chargeAppliesToFromStored[v] = a
	}
}
