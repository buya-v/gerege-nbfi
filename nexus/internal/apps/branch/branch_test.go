package branch

import "testing"

func TestTellerStatusFromInt(t *testing.T) {
	cases := []struct {
		in   int32
		want TellerStatus
	}{
		{100, TellerStatusPending},
		{300, TellerStatusActive},
		{400, TellerStatusInactive},
		{600, TellerStatusClosed},
		{999, TellerStatusInvalid},
	}
	for _, c := range cases {
		if got := TellerStatusFromInt(c.in); got != c.want {
			t.Errorf("TellerStatusFromInt(%d) = %d, want %d", c.in, got, c.want)
		}
	}
}

func TestCashierTxnTypeFromID(t *testing.T) {
	if got, ok := CashierTxnTypeFromID(103); !ok || got.ID != 103 || got.Value != "Cash In" {
		t.Fatalf("CashierTxnTypeFromID(103) = %+v ok=%v", got, ok)
	}
	if _, ok := CashierTxnTypeFromID(0); ok {
		t.Fatal("expected unknown id to be rejected")
	}
}

func TestMinorUnitsRoundTrip(t *testing.T) {
	m, err := MinorUnitsFromDecimalText("-12.34", MNTMinorDigits)
	if err != nil {
		t.Fatalf("MinorUnitsFromDecimalText: %v", err)
	}
	if got := m.FormatDecimal(MNTMinorDigits); got != "-12.34" {
		t.Fatalf("round trip = %q, want -12.34", got)
	}
}
