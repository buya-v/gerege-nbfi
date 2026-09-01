package loanproduct

import "testing"

// The stored-value tables are the contract with m_product_loan's enum columns.
// These tests pin every stored value, every code, and both decode directions so
// a future edit cannot silently shift a column encoding.

func TestInterestMethodRoundTrip(t *testing.T) {
	want := map[int32]string{
		0: "DECLINING_BALANCE",
		1: "FLAT",
		2: "INVALID",
	}
	for stored, name := range want {
		got, ok := InterestMethodFromStoredValue(stored)
		if !ok {
			t.Fatalf("InterestMethodFromStoredValue(%d) not ok", stored)
		}
		if got.String() != name {
			t.Fatalf("stored %d -> %s, want %s", stored, got, name)
		}
		if got.StoredValue() != stored {
			t.Fatalf("%s.StoredValue() = %d, want %d", got, got.StoredValue(), stored)
		}
	}
	if _, ok := InterestMethodFromStoredValue(3); ok {
		t.Fatal("stored 3 must not decode (INVALID fallback only)")
	}
	if !InterestDecliningBalance.IsDecliningBalance() || InterestDecliningBalance.IsFlat() {
		t.Fatal("InterestDecliningBalance predicate mismatch")
	}
}

func TestAmortizationMethodRoundTrip(t *testing.T) {
	want := map[int32]string{
		0: "EQUAL_PRINCIPAL",
		1: "EQUAL_INSTALLMENTS",
		2: "INVALID",
	}
	for stored, name := range want {
		got, ok := AmortizationMethodFromStoredValue(stored)
		if !ok || got.String() != name {
			t.Fatalf("stored %d -> %v(%v), want %s", stored, got, ok, name)
		}
		if got.StoredValue() != stored {
			t.Fatalf("%s.StoredValue() = %d, want %d", got, got.StoredValue(), stored)
		}
	}
	if _, ok := AmortizationMethodFromStoredValue(-1); ok {
		t.Fatal("stored -1 must not decode")
	}
}

func TestInterestCalcPeriodRoundTrip(t *testing.T) {
	want := map[int32]string{
		0: "DAILY",
		1: "SAME_AS_REPAYMENT_PERIOD",
		2: "INVALID",
	}
	for stored, name := range want {
		got, ok := InterestCalculationPeriodMethodFromStoredValue(stored)
		if !ok || got.String() != name {
			t.Fatalf("stored %d -> %v(%v), want %s", stored, got, ok, name)
		}
		if got.StoredValue() != stored {
			t.Fatalf("%s.StoredValue() = %d, want %d", got, got.StoredValue(), stored)
		}
	}
}

func TestPeriodFrequencyRoundTrip(t *testing.T) {
	want := map[int32]string{
		0: "DAYS",
		1: "WEEKS",
		2: "MONTHS",
		3: "YEARS",
		4: "WHOLE_TERM",
		5: "INVALID",
	}
	for stored, name := range want {
		got, ok := PeriodFrequencyTypeFromStoredValue(stored)
		if !ok || got.String() != name {
			t.Fatalf("stored %d -> %v(%v), want %s", stored, got, ok, name)
		}
		if got.StoredValue() != stored {
			t.Fatalf("%s.StoredValue() = %d, want %d", got, got.StoredValue(), stored)
		}
	}
	// Zero value must be INVALID, not DAYS, matching the null-frequency getter.
	var zero PeriodFrequencyType
	if zero != PeriodInvalid {
		t.Fatalf("zero PeriodFrequencyType = %v, want INVALID", zero)
	}
}

// TestDaysInYearNotOrdinal pins the single most important non-obvious fact in
// this package: the stored value is the literal day count, not the ordinal.
func TestDaysInYearNotOrdinal(t *testing.T) {
	if DaysInYear360.StoredValue() != 360 {
		t.Fatalf("DAYS_360 stored = %d, want 360", DaysInYear360.StoredValue())
	}
	if DaysInYear364.StoredValue() != 364 {
		t.Fatalf("DAYS_364 stored = %d, want 364", DaysInYear364.StoredValue())
	}
	if DaysInYear365.StoredValue() != 365 {
		t.Fatalf("DAYS_365 stored = %d, want 365", DaysInYear365.StoredValue())
	}
	if DaysInYearActual.StoredValue() != 1 {
		t.Fatalf("ACTUAL stored = %d, want 1", DaysInYearActual.StoredValue())
	}

	want := map[int32]string{
		0:   "INVALID",
		1:   "ACTUAL",
		360: "DAYS_360",
		364: "DAYS_364",
		365: "DAYS_365",
	}
	for stored, name := range want {
		got, ok := DaysInYearTypeFromStoredValue(stored)
		if !ok || got.String() != name {
			t.Fatalf("stored %d -> %v(%v), want %s", stored, got, ok, name)
		}
		if got.StoredValue() != stored {
			t.Fatalf("%s.StoredValue() = %d, want %d", got, got.StoredValue(), stored)
		}
	}
	if _, ok := DaysInYearTypeFromStoredValue(366); ok {
		t.Fatal("stored 366 must not decode")
	}
}

func TestDaysInMonthNotOrdinal(t *testing.T) {
	if DaysInMonth30.StoredValue() != 30 {
		t.Fatalf("DAYS_30 stored = %d, want 30", DaysInMonth30.StoredValue())
	}
	want := map[int32]string{
		0:  "INVALID",
		1:  "ACTUAL",
		30: "DAYS_30",
	}
	for stored, name := range want {
		got, ok := DaysInMonthTypeFromStoredValue(stored)
		if !ok || got.String() != name {
			t.Fatalf("stored %d -> %v(%v), want %s", stored, got, ok, name)
		}
	}
	if _, ok := DaysInMonthTypeFromStoredValue(31); ok {
		t.Fatal("stored 31 must not decode")
	}
}

func TestRelatedDetailResetToInvalid(t *testing.T) {
	d := LoanProductRelatedDetail{
		NominalInterestRatePerPeriod: 1_250_000,
		InterestPeriodFrequencyType:  PeriodMonths,
		AnnualNominalInterestRate:    15_000_000,
	}
	d.ResetToInvalid()
	if d.NominalInterestRatePerPeriod != 0 || d.AnnualNominalInterestRate != 0 {
		t.Fatal("ResetToInvalid must blank rate fields")
	}
	if d.InterestPeriodFrequencyType != PeriodInvalid {
		t.Fatalf("ResetToInvalid frequency = %v, want INVALID", d.InterestPeriodFrequencyType)
	}
}
