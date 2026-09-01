package provisioning

import "testing"

func TestPercentageOfPositive(t *testing.T) {
	cases := []struct {
		name       string
		value      MinorUnits
		percentage Percent
		want       MinorUnits
	}{
		{"whole per cent halves exactly", 1_200_000, 50_000_000, 600_000},
		{"sub-unit residue rounds down", 100, 33_333_333, 33},
		{"half rounds up (away from zero)", 1, 50_000_000, 1},
		{"quarter rounds down", 1, 25_000_000, 0},
		{"zero value", 0, 50_000_000, 0},
		{"zero percent", 1_000_000, 0, 0},
		{"one hundred percent", 1_234_567, 100_000_000, 1_234_567},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got, err := PercentageOf(c.value, c.percentage)
			if err != nil {
				t.Fatalf("PercentageOf(%d, %d) returned error: %v", c.value, c.percentage, err)
			}
			if got != c.want {
				t.Fatalf("PercentageOf(%d, %d) = %d, want %d", c.value, c.percentage, got, c.want)
			}
		})
	}
}

func TestPercentageOfNegativeHasNoGate(t *testing.T) {
	// Money.percentageOf has no "value <= 0 -> 0" gate: a negative amount
	// produces a negative reserve under HALF_UP. The port must preserve that.
	got, err := PercentageOf(-1, 50_000_000)
	if err != nil {
		t.Fatalf("PercentageOf(-1, 50%%) returned error: %v", err)
	}
	if got != -1 {
		t.Fatalf("PercentageOf(-1, 50%%) = %d, want -1", got)
	}
}

func TestCriteriaDefinitionMatches(t *testing.T) {
	d := CriteriaDefinition{MinimumAge: 31, MaximumAge: 60}
	for age, want := range map[int64]bool{30: false, 31: true, 45: true, 60: true, 61: false} {
		if got := d.Matches(age); got != want {
			t.Errorf("Matches(%d) = %v, want %v", age, got, want)
		}
	}
}

func TestCriteriaDefinitionOverlaps(t *testing.T) {
	d := CriteriaDefinition{MinimumAge: 31, MaximumAge: 60}
	cases := []struct {
		other CriteriaDefinition
		want  bool
	}{
		{CriteriaDefinition{MinimumAge: 1, MaximumAge: 30}, false},
		{CriteriaDefinition{MinimumAge: 1, MaximumAge: 31}, true},
		{CriteriaDefinition{MinimumAge: 60, MaximumAge: 90}, true},
		{CriteriaDefinition{MinimumAge: 61, MaximumAge: 90}, false},
		{CriteriaDefinition{MinimumAge: 31, MaximumAge: 60}, true},
		{CriteriaDefinition{MinimumAge: 40, MaximumAge: 50}, true}, // nested
	}
	for _, c := range cases {
		if got := d.Overlaps(c.other); got != c.want {
			t.Errorf("Overlaps(%v) = %v, want %v", c.other, got, c.want)
		}
	}
}

func TestCriteriaReserveRateGap(t *testing.T) {
	c := Criteria{
		Name: "standard",
		Definitions: []CriteriaDefinition{
			{ID: 1, MinimumAge: 1, MaximumAge: 30, Percentage: 10_000_000},
			{ID: 2, MinimumAge: 61, MaximumAge: 90, Percentage: 50_000_000},
		},
	}
	if _, ok := c.ReserveRate(0); ok {
		t.Error("ReserveRate(0) should be a gap, got ok")
	}
	if _, ok := c.ReserveRate(45); ok {
		t.Error("ReserveRate(45) should be a gap, got ok")
	}
	if d, ok := c.ReserveRate(15); !ok || d.ID != 1 {
		t.Errorf("ReserveRate(15) = %+v, %v; want ID 1, true", d, ok)
	}
}

func TestCriteriaValidateRange(t *testing.T) {
	overlapping := Criteria{
		Name: "bad",
		Definitions: []CriteriaDefinition{
			{ID: 1, MinimumAge: 1, MaximumAge: 30},
			{ID: 2, MinimumAge: 30, MaximumAge: 60},
		},
	}
	if err := overlapping.ValidateRange(); err == nil {
		t.Error("ValidateRange() should reject overlapping definitions")
	}

	disjoint := Criteria{
		Name: "good",
		Definitions: []CriteriaDefinition{
			{ID: 1, MinimumAge: 1, MaximumAge: 30},
			{ID: 2, MinimumAge: 31, MaximumAge: 60},
		},
	}
	if err := disjoint.ValidateRange(); err != nil {
		t.Errorf("ValidateRange() should accept disjoint definitions, got %v", err)
	}
}

func TestGenerateReserveEntriesAggregates(t *testing.T) {
	inputs := []ReserveInput{
		{OfficeID: 1, CurrencyCode: "MNT", ProductID: 1, CategoryID: 1, OverdueInDays: 15, Percentage: 10_000_000, Balance: 100_000, LiabilityAccount: 100, ExpenseAccount: 200, CriteriaID: 1},
		{OfficeID: 1, CurrencyCode: "MNT", ProductID: 1, CategoryID: 1, OverdueInDays: 15, Percentage: 10_000_000, Balance: 200_000, LiabilityAccount: 100, ExpenseAccount: 200, CriteriaID: 1},
		{OfficeID: 1, CurrencyCode: "MNT", ProductID: 2, CategoryID: 2, OverdueInDays: 45, Percentage: 50_000_000, Balance: 1_000_000, LiabilityAccount: 100, ExpenseAccount: 200, CriteriaID: 1},
	}

	got, err := GenerateReserveEntries(inputs)
	if err != nil {
		t.Fatalf("GenerateReserveEntries returned error: %v", err)
	}
	if len(got) != 2 {
		t.Fatalf("GenerateReserveEntries returned %d entries, want 2", len(got))
	}

	// First key: product 1 aggregated to 10% of 300,000 = 30,000.
	if got[0].ProductID != 1 || got[0].ReservedAmount != 30_000 {
		t.Errorf("entry[0] = %+v, want product 1 reserved 30_000", got[0])
	}
	// Second key: product 2, 50% of 1,000,000 = 500,000.
	if got[1].ProductID != 2 || got[1].ReservedAmount != 500_000 {
		t.Errorf("entry[1] = %+v, want product 2 reserved 500_000", got[1])
	}
}
