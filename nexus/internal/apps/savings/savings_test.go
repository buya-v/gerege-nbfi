package savings

import (
	"strings"
	"testing"
)

func TestSavingsAccountStatusStoredValues(t *testing.T) {
	cases := []struct {
		status SavingsAccountStatusType
		want   int32
	}{
		{StatusInvalid, 0},
		{StatusSubmittedAndPendingApproval, 100},
		{StatusApproved, 200},
		{StatusActive, 300},
		{StatusTransferInProgress, 303},
		{StatusTransferOnHold, 304},
		{StatusWithdrawnByApplicant, 400},
		{StatusRejected, 500},
		{StatusClosed, 600},
		{StatusPreMatureClosure, 700},
		{StatusMatured, 800},
	}
	for _, c := range cases {
		if got := c.status.StoredValue(); got != c.want {
			t.Errorf("%s.StoredValue() = %d, want %d", c.status, got, c.want)
		}
		if got, ok := SavingsAccountStatusTypeFromStoredValue(c.want); !ok || got != c.status {
			t.Errorf("FromStoredValue(%d) = %v, %v; want %v, true", c.want, got, ok, c.status)
		}
	}
	// Every legal stored value must round-trip exactly once (injective table).
	if got, ok := SavingsAccountStatusTypeFromStoredValue(299); ok || got != 0 {
		t.Errorf("FromStoredValue(299) = %v, %v; want invalid, false", got, ok)
	}
}

func TestSavingsAccountTransactionStoredValues(t *testing.T) {
	cases := []struct {
		txn  SavingsAccountTransactionType
		want int32
	}{
		{TxnInvalid, 0},
		{TxnDeposit, 1},
		{TxnWithdrawal, 2},
		{TxnInterestPosting, 3},
		{TxnAccrual, 10}, // no 9 — gap is the contract
		{TxnInitiateTransfer, 12},
		{TxnAmountHold, 20},
		{TxnAmountRelease, 21},
	}
	for _, c := range cases {
		if got := c.txn.StoredValue(); got != c.want {
			t.Errorf("%s.StoredValue() = %d, want %d", c.txn, got, c.want)
		}
		if got, ok := SavingsAccountTransactionTypeFromStoredValue(c.want); !ok || got != c.txn {
			t.Errorf("FromStoredValue(%d) = %v, %v; want %v, true", c.want, got, ok, c.txn)
		}
	}
	if _, ok := SavingsAccountTransactionTypeFromStoredValue(9); ok {
		t.Error("FromStoredValue(9) = ok; want false (there is no transaction type 9)")
	}
	if _, ok := SavingsAccountTransactionTypeFromStoredValue(11); ok {
		t.Error("FromStoredValue(11) = ok; want false (there is no transaction type 11)")
	}
}

func TestDepositAccountTypeStoredValues(t *testing.T) {
	cases := []struct {
		dt   DepositAccountType
		want int32
	}{
		{DepositInvalid, 0},
		{DepositSavings, 100},
		{DepositFixed, 200},
		{DepositRecurring, 300},
		{DepositCurrent, 400},
	}
	for _, c := range cases {
		if got := c.dt.StoredValue(); got != c.want {
			t.Errorf("%s.StoredValue() = %d, want %d", c.dt, got, c.want)
		}
		if got, ok := DepositAccountTypeFromStoredValue(c.want); !ok || got != c.dt {
			t.Errorf("FromStoredValue(%d) = %v, %v; want %v, true", c.want, got, ok, c.dt)
		}
	}
}

func TestInterestPeriodStoredValues(t *testing.T) {
	if got := CompoundingQuarterly.StoredValue(); got != 5 {
		t.Errorf("CompoundingQuarterly.StoredValue() = %d, want 5", got)
	}
	if got := CompoundingMonthly.StoredValue(); got != 4 {
		t.Errorf("CompoundingMonthly.StoredValue() = %d, want 4", got)
	}
	if got := SavingsCompoundingInterestPeriodTypeFromStoredValue(2); got != CompoundingInvalid {
		t.Errorf("FromStoredValue(2) = %v; want CompoundingInvalid (no WEEKLY)", got)
	}

	if got := PostingAnniversaryAnnual.StoredValue(); got != 11 {
		t.Errorf("PostingAnniversaryAnnual.StoredValue() = %d, want 11", got)
	}
	if got := SavingsPostingInterestPeriodTypeFromStoredValue(7); got != PostingAnnual {
		t.Errorf("FromStoredValue(7) = %v; want PostingAnnual", got)
	}

	if got := SavingsInterestCalculationDaysInYearTypeFromStoredValue(360); got != DaysInYear360 {
		t.Errorf("FromStoredValue(360) = %v; want DaysInYear360", got)
	}
	if got := SavingsInterestCalculationDaysInYearTypeFromStoredValue(1); got != DaysInYearInvalid {
		t.Errorf("FromStoredValue(1) = %v; want DaysInYearInvalid", got)
	}
}

func TestDefaultConfigIsDisabled(t *testing.T) {
	c := DefaultConfig()
	if c.Enabled {
		t.Fatal("DefaultConfig().Enabled = true; savings must ship disabled")
	}
	if got := (Config{}).Enabled; got {
		t.Fatal("zero Config{}.Enabled = true; the zero value must be disabled")
	}
}

func TestMoneyRoundTrip(t *testing.T) {
	cases := []struct {
		major string
		minor MinorUnits
	}{
		{"0", 0},
		{"0.00", 0},
		{"12.50", 1250},
		{"12.5", 1250},
		{"100", 10000},
		{"-12.50", -1250},
		{"1234567.89", 123456789},
	}
	for _, c := range cases {
		got, err := MinorUnitsFromDecimalText(c.major, MNTMinorDigits)
		if err != nil {
			t.Fatalf("FromDecimalText(%q): %v", c.major, err)
		}
		if got != c.minor {
			t.Errorf("FromDecimalText(%q) = %d, want %d", c.major, got, c.minor)
		}
		if back := c.minor.FormatDecimal(MNTMinorDigits); back != c.major && back != c.major+".00" && back != canonical(c.major) {
			t.Errorf("FormatDecimal(%d) = %q; not a canonical spelling of %q", c.minor, back, c.major)
		}
	}

	// A non-zero sixth decimal must be refused, not truncated.
	if _, err := MinorUnitsFromDecimalText("1.234567", MNTMinorDigits); err == nil {
		t.Error("FromDecimalText(\"1.234567\") = nil error; want refusal of sub-minor residue")
	}
	// Trailing zeros beyond the minor digits are dropped.
	if got, err := MinorUnitsFromDecimalText("1.2300", MNTMinorDigits); err != nil || got != 123 {
		t.Errorf("FromDecimalText(\"1.2300\") = %d, %v; want 123, nil", got, err)
	}
}

// canonical renders the canonical two-decimal spelling of a major-unit string
// that may be missing its decimal point or fraction digits.
func canonical(major string) string {
	if !strings.Contains(major, ".") {
		return major + ".00"
	}
	dot := strings.Index(major, ".")
	return major[:dot+1] + (major[dot+1:] + "00")[:2]
}

func TestSavingsStatusStringsAreNotInsuranceClaims(t *testing.T) {
	for _, s := range []SavingsAccountStatusType{
		StatusInvalid, StatusSubmittedAndPendingApproval, StatusApproved, StatusActive,
		StatusTransferInProgress, StatusTransferOnHold, StatusWithdrawnByApplicant,
		StatusRejected, StatusClosed, StatusPreMatureClosure, StatusMatured,
	} {
		str := s.String()
		for _, banned := range []string{"insured", "protected", "guaranteed", "Insured", "Protected", "Guaranteed"} {
			if strings.Contains(str, banned) {
				t.Errorf("%s.String() = %q contains forbidden claim %q", s, str, banned)
			}
		}
	}
}
