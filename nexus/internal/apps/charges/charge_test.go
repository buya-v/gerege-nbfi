package charges

import "testing"

func TestChargeTimeTypeRoundTrip(t *testing.T) {
	for stored := int32(0); stored <= 16; stored++ {
		got, ok := ChargeTimeTypeFromStoredValue(stored)
		if !ok {
			t.Fatalf("ChargeTimeTypeFromStoredValue(%d) not ok", stored)
		}
		if got.StoredValue() != stored {
			t.Fatalf("round trip %d -> %s -> %d", stored, got, got.StoredValue())
		}
	}
	if _, ok := ChargeTimeTypeFromStoredValue(17); ok {
		t.Fatal("stored value 17 must not decode")
	}
	if _, ok := ChargeTimeTypeFromStoredValue(-1); ok {
		t.Fatal("stored value -1 must not decode")
	}
}

func TestChargeCalculationTypeFromStoredValue(t *testing.T) {
	if _, ok := ChargeCalculationTypeFromStoredValue(0); ok {
		t.Fatal("INVALID (0) must not decode")
	}
	for stored := int32(1); stored <= 5; stored++ {
		got, ok := ChargeCalculationTypeFromStoredValue(stored)
		if !ok || got.StoredValue() != stored {
			t.Fatalf("decode %d -> %v ok=%v", stored, got, ok)
		}
	}
	if _, ok := ChargeCalculationTypeFromStoredValue(6); ok {
		t.Fatal("stored value 6 must not decode")
	}
}

func TestChargeAppliesToFromStoredValue(t *testing.T) {
	if _, ok := ChargeAppliesToFromStoredValue(0); ok {
		t.Fatal("INVALID (0) must not decode")
	}
	for stored := int32(1); stored <= 5; stored++ {
		got, ok := ChargeAppliesToFromStoredValue(stored)
		if !ok || got.StoredValue() != stored {
			t.Fatalf("decode %d -> %v ok=%v", stored, got, ok)
		}
	}
	if _, ok := ChargeAppliesToFromStoredValue(6); ok {
		t.Fatal("stored value 6 must not decode")
	}
}

func TestChargePaymentModeFromStoredValue(t *testing.T) {
	for stored := int32(0); stored <= 1; stored++ {
		got, ok := ChargePaymentModeFromStoredValue(stored)
		if !ok || got.StoredValue() != stored {
			t.Fatalf("decode %d -> %v ok=%v", stored, got, ok)
		}
	}
	if _, ok := ChargePaymentModeFromStoredValue(2); ok {
		t.Fatal("stored value 2 must not decode")
	}
}

func TestPercentageOf(t *testing.T) {
	cases := []struct {
		name    string
		value   MinorUnits
		percent Percent
		want    MinorUnits
	}{
		{"zero value yields zero", 0, 1_000_000, 0},
		{"negative value yields zero", -5, 1_000_000, 0},
		{"one percent of 1.00", 100, 1_000_000, 1},
		{"fifty percent of 1.00", 100, 50_000_000, 50},
		{"1.2345 percent of 12000.00 is exact", 1_200_000, 1_234_500, 14_814},
		{"one percent of 33.33 rounds half-up down", 3_333, 1_000_000, 33},
		{"one percent of 99.99 rounds half-up up", 9_999, 1_000_000, 100},
		{"one percent of 0.50 rounds half-up up", 50, 1_000_000, 1},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := PercentageOf(tc.value, tc.percent)
			if err != nil {
				t.Fatalf("PercentageOf(%d, %d) error: %v", tc.value, tc.percent, err)
			}
			if got != tc.want {
				t.Fatalf("PercentageOf(%d, %d) = %d, want %d", tc.value, tc.percent, got, tc.want)
			}
		})
	}
}

func TestMinimumAndMaximumCap(t *testing.T) {
	min := MinorUnits(10)
	max := MinorUnits(100)

	if got := MinimumAndMaximumCap(50, &min, &max); got != 50 {
		t.Fatalf("within caps = %d, want 50", got)
	}
	if got := MinimumAndMaximumCap(5, &min, &max); got != 10 {
		t.Fatalf("below min = %d, want 10", got)
	}
	if got := MinimumAndMaximumCap(500, &min, &max); got != 100 {
		t.Fatalf("above max = %d, want 100", got)
	}
	if got := MinimumAndMaximumCap(50, nil, &max); got != 50 {
		t.Fatalf("no min = %d, want 50", got)
	}
	if got := MinimumAndMaximumCap(500, nil, &max); got != 100 {
		t.Fatalf("no min above max = %d, want 100", got)
	}
	if got := MinimumAndMaximumCap(5, &min, nil); got != 10 {
		t.Fatalf("no max below min = %d, want 10", got)
	}
}

func TestChargeValidateSavingsTime(t *testing.T) {
	c := Charge{
		Name:            "savings fee",
		AppliesTo:       ChargeAppliesToSavings,
		TimeType:        ChargeTimeDisbursement, // illegal for savings
		CalculationType: ChargeCalculationFlat,
		Active:          true,
	}
	errs := c.Validate()
	if len(errs) != 1 || errs[0].Code != "not.allowed.charge.time.for.savings" {
		t.Fatalf("expected one savings-time error, got %v", errs)
	}
}

func TestChargeValidateSavingsPercentageRestriction(t *testing.T) {
	c := Charge{
		Name:            "savings fee",
		AppliesTo:       ChargeAppliesToSavings,
		TimeType:        ChargeTimeSavingsActivation, // legal time, but not withdrawal/no-activity
		CalculationType: ChargeCalculationPercentOfAmount,
		Active:          true,
	}
	errs := c.Validate()
	if len(errs) != 1 || errs[0].Code != "savings.charge.calculation.type.percentage.allowed.only.for.withdrawal.or.NoActivity" {
		t.Fatalf("expected one percentage-restriction error, got %v", errs)
	}
}

func TestChargeValidateSavingsWithdrawalPercentageAllowed(t *testing.T) {
	c := Charge{
		Name:            "withdrawal fee",
		AppliesTo:       ChargeAppliesToSavings,
		TimeType:        ChargeTimeWithdrawalFee,
		CalculationType: ChargeCalculationPercentOfAmount,
		Active:          true,
	}
	if errs := c.Validate(); len(errs) != 0 {
		t.Fatalf("withdrawal percentage fee must validate, got %v", errs)
	}
}

func TestChargeValidateLoanPenaltyAtDisbursement(t *testing.T) {
	c := Charge{
		Name:            "penalty",
		AppliesTo:       ChargeAppliesToLoan,
		TimeType:        ChargeTimeDisbursement,
		CalculationType: ChargeCalculationFlat,
		Penalty:         true,
		Active:          true,
	}
	errs := c.Validate()
	if len(errs) != 1 || errs[0].Code != "charge.due.at.disbursement.cannot.be.penalty" {
		t.Fatalf("expected one penalty-at-disbursement error, got %v", errs)
	}
}

func TestChargeValidateLoanNonPenaltyOverdue(t *testing.T) {
	c := Charge{
		Name:            "overdue",
		AppliesTo:       ChargeAppliesToLoan,
		TimeType:        ChargeTimeOverdueInstallment,
		CalculationType: ChargeCalculationFlat,
		Penalty:         false,
		Active:          true,
	}
	errs := c.Validate()
	if len(errs) != 1 || errs[0].Code != "charge.must.be.penalty" {
		t.Fatalf("expected one must-be-penalty error, got %v", errs)
	}
}

func TestChargeValidateLoanValid(t *testing.T) {
	c := Charge{
		Name:            "disbursement fee",
		AppliesTo:       ChargeAppliesToLoan,
		TimeType:        ChargeTimeDisbursement,
		CalculationType: ChargeCalculationFlat,
		Amount:          100,
		Active:          true,
	}
	if errs := c.Validate(); len(errs) != 0 {
		t.Fatalf("flat disbursement fee must validate, got %v", errs)
	}
}
