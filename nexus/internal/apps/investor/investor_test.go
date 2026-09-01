package investor

import "testing"

func TestTransferDetailsDeriveTotalOutstanding(t *testing.T) {
	d := ExternalAssetOwnerTransferDetails{
		PrincipalOutstanding:      100_000,
		InterestOutstanding:       5_000,
		FeeChargesOutstanding:     250,
		PenaltyChargesOutstanding: 100,
	}
	if got := d.DeriveTotalOutstanding(); got != 105_350 {
		t.Fatalf("DeriveTotalOutstanding = %d, want 105350", got)
	}
}

func TestTransferStatusStoredValue(t *testing.T) {
	cases := []struct {
		in   ExternalTransferStatus
		want string
	}{
		{TransferStatusActive, "ACTIVE"},
		{TransferStatusPendingIntermediate, "PENDING_INTERMEDIATE"},
		{TransferStatusBuyback, "BUYBACK"},
		{TransferStatusCancelled, "CANCELLED"},
	}
	for _, c := range cases {
		if got := c.in.StoredValue(); got != c.want {
			t.Errorf("StoredValue(%q) = %q, want %q", c.in, got, c.want)
		}
	}
}

func TestMinorUnitsRoundTrip(t *testing.T) {
	const text = "12345.67"
	m, err := MinorUnitsFromDecimalText(text, MNTMinorDigits)
	if err != nil {
		t.Fatalf("MinorUnitsFromDecimalText: %v", err)
	}
	if got := m.FormatDecimal(MNTMinorDigits); got != text {
		t.Fatalf("round trip = %q, want %q", got, text)
	}
}

func TestMinorUnitsRefusesSubMinorResidue(t *testing.T) {
	if _, err := MinorUnitsFromDecimalText("1.001", MNTMinorDigits); err == nil {
		t.Fatal("expected error for third-decimal residue")
	}
}

func TestOutstandingInterestStrategyFor(t *testing.T) {
	if s, ok := OutstandingInterestStrategyFor(LoanProductAttribute{
		AttributeKey:   OutstandingInterestStrategyKey,
		AttributeValue: "PAYABLE_OUTSTANDING",
	}); !ok || s != OutstandingInterestStrategyPayableOutstanding {
		t.Fatalf("expected PAYABLE_OUTSTANDING, got %q ok=%v", s, ok)
	}
	if _, ok := OutstandingInterestStrategyFor(LoanProductAttribute{
		AttributeKey:   "SOMETHING_ELSE",
		AttributeValue: "TOTAL_OUTSTANDING",
	}); ok {
		t.Fatal("expected false for non-strategy key")
	}
}
