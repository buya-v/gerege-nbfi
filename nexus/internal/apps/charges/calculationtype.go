package charges

import "fmt"

// ChargeCalculationType is m_charge.charge_calculation_enum — Fineract's
// ChargeCalculationType. [VERIFIED: ChargeCalculationType.java:25-31 —
// INVALID(0), FLAT(1), PERCENT_OF_AMOUNT(2), PERCENT_OF_AMOUNT_AND_INTEREST(3),
// PERCENT_OF_INTEREST(4), PERCENT_OF_DISBURSEMENT_AMOUNT(5)]
type ChargeCalculationType int32

const (
	ChargeCalculationInvalid ChargeCalculationType = iota
	ChargeCalculationFlat
	ChargeCalculationPercentOfAmount
	ChargeCalculationPercentOfAmountAndInterest
	ChargeCalculationPercentOfInterest
	ChargeCalculationPercentOfDisbursementAmount
)

var chargeCalculationStoredValue = map[ChargeCalculationType]int32{
	ChargeCalculationInvalid:                     0,
	ChargeCalculationFlat:                        1,
	ChargeCalculationPercentOfAmount:             2,
	ChargeCalculationPercentOfAmountAndInterest:  3,
	ChargeCalculationPercentOfInterest:           4,
	ChargeCalculationPercentOfDisbursementAmount: 5,
}

var chargeCalculationCode = map[ChargeCalculationType]string{
	ChargeCalculationInvalid:                     "chargeCalculationType.invalid",
	ChargeCalculationFlat:                        "chargeCalculationType.flat",
	ChargeCalculationPercentOfAmount:             "chargeCalculationType.percent.of.amount",
	ChargeCalculationPercentOfAmountAndInterest:  "chargeCalculationType.percent.of.amount.and.interest",
	ChargeCalculationPercentOfInterest:           "chargeCalculationType.percent.of.interest",
	ChargeCalculationPercentOfDisbursementAmount: "chargeCalculationType.percent.of.disbursement.amount",
}

var chargeCalculationName = map[ChargeCalculationType]string{
	ChargeCalculationInvalid:                     "INVALID",
	ChargeCalculationFlat:                        "FLAT",
	ChargeCalculationPercentOfAmount:             "PERCENT_OF_AMOUNT",
	ChargeCalculationPercentOfAmountAndInterest:  "PERCENT_OF_AMOUNT_AND_INTEREST",
	ChargeCalculationPercentOfInterest:           "PERCENT_OF_INTEREST",
	ChargeCalculationPercentOfDisbursementAmount: "PERCENT_OF_DISBURSEMENT_AMOUNT",
}

var chargeCalculationFromStored = map[int32]ChargeCalculationType{}

// StoredValue returns m_charge.charge_calculation_enum.
func (c ChargeCalculationType) StoredValue() int32 {
	v, ok := chargeCalculationStoredValue[c]
	if !ok {
		panic(fmt.Sprintf("charges: unknown ChargeCalculationType %d", int32(c)))
	}
	return v
}

func (c ChargeCalculationType) Code() string { return chargeCalculationCode[c] }

func (c ChargeCalculationType) String() string {
	if n, ok := chargeCalculationName[c]; ok {
		return n
	}
	return fmt.Sprintf("ChargeCalculationType(%d)", int32(c))
}

// ChargeCalculationTypeFromStoredValue decodes m_charge.charge_calculation_enum.
// ok is false outside [1,5] (0/INVALID and >5 fall back to INVALID), matching
// ChargeCalculationType.fromInt [VERIFIED: ChargeCalculationType.java:86-94].
func ChargeCalculationTypeFromStoredValue(v int32) (ChargeCalculationType, bool) {
	c, ok := chargeCalculationFromStored[v]
	return c, ok
}

// Predicates mirror ChargeCalculationType.java:97-132.

func (c ChargeCalculationType) IsPercentageOfAmount() bool {
	return c == ChargeCalculationPercentOfAmount
}
func (c ChargeCalculationType) IsPercentageOfAmountAndInterest() bool {
	return c == ChargeCalculationPercentOfAmountAndInterest
}
func (c ChargeCalculationType) IsPercentageOfInterest() bool {
	return c == ChargeCalculationPercentOfInterest
}
func (c ChargeCalculationType) IsFlat() bool { return c == ChargeCalculationFlat }

func (c ChargeCalculationType) IsPercentageOfDisbursementAmount() bool {
	return c == ChargeCalculationPercentOfDisbursementAmount
}

// IsAllowedSavingsChargeCalculationType mirrors the savings-legal union
// [VERIFIED: ChargeCalculationType.java:113-115].
func (c ChargeCalculationType) IsAllowedSavingsChargeCalculationType() bool {
	return c.IsFlat() || c.IsPercentageOfAmount()
}

// IsAllowedClientChargeCalculationType mirrors the client-legal union
// [VERIFIED: ChargeCalculationType.java:117-119].
func (c ChargeCalculationType) IsAllowedClientChargeCalculationType() bool {
	return c.IsFlat()
}

// IsPercentageBased is true for every percentage variant (all but FLAT)
// [VERIFIED: ChargeCalculationType.java:121-123].
func (c ChargeCalculationType) IsPercentageBased() bool {
	return c.IsPercentageOfAmount() || c.IsPercentageOfAmountAndInterest() ||
		c.IsPercentageOfInterest() || c.IsPercentageOfDisbursementAmount()
}

// HasInterest is true for the two variants whose base includes interest
// [VERIFIED: ChargeCalculationType.java:126-128].
func (c ChargeCalculationType) HasInterest() bool {
	return c.IsPercentageOfInterest() || c.IsPercentageOfAmountAndInterest()
}

func init() {
	for c, v := range chargeCalculationStoredValue {
		if c == ChargeCalculationInvalid {
			continue // INVALID (0) is not a decodable stored value
		}
		if _, dup := chargeCalculationFromStored[v]; dup {
			panic(fmt.Sprintf("charges: charge calculation encode table is not injective at %d", v))
		}
		chargeCalculationFromStored[v] = c
	}
}
