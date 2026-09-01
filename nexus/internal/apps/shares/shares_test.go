package shares

import "testing"

func TestShareAccountStatusFromInt(t *testing.T) {
	cases := []struct {
		in   int32
		want ShareAccountStatusType
	}{
		{100, ShareAccountStatusSubmittedAndPendingApproval},
		{200, ShareAccountStatusApproved},
		{300, ShareAccountStatusActive},
		{400, ShareAccountStatusRejected},
		{600, ShareAccountStatusClosed},
		{0, ShareAccountStatusInvalid},
	}
	for _, c := range cases {
		if got := ShareAccountStatusFromInt(c.in); got != c.want {
			t.Errorf("ShareAccountStatusFromInt(%d) = %d, want %d", c.in, got, c.want)
		}
	}
}

func TestPurchaseStatusFromInt(t *testing.T) {
	if got := PurchaseStatusFromInt(400); got != PurchaseStatusWithdrawn {
		t.Fatalf("PurchaseStatusFromInt(400) = %d, want WITHDRAWN", got)
	}
}

func TestShareAccountTransactionTypeFromInt(t *testing.T) {
	if got := ShareAccountTransactionTypeFromInt(4); got != ShareTxnDividendPayment {
		t.Fatalf("ShareAccountTransactionTypeFromInt(4) = %d, want DIVIDEND_PAYMENT", got)
	}
	if got := ShareAccountTransactionTypeFromInt(42); got != ShareTxnInvalid {
		t.Fatalf("ShareAccountTransactionTypeFromInt(42) = %d, want INVALID", got)
	}
}

func TestMinorUnitsRoundTrip(t *testing.T) {
	m, err := MinorUnitsFromDecimalText("0.05", MNTMinorDigits)
	if err != nil {
		t.Fatalf("MinorUnitsFromDecimalText: %v", err)
	}
	if got := m.FormatDecimal(MNTMinorDigits); got != "0.05" {
		t.Fatalf("round trip = %q, want 0.05", got)
	}
}
