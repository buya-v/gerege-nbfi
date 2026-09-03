package savings

import "testing"

func txn(typ SavingsAccountTransactionType, amount MinorUnits, flags ...bool) SavingsAccountTransaction {
	t := SavingsAccountTransaction{Type: typ, Amount: amount}
	if len(flags) > 0 {
		t.Reversed = flags[0]
	}
	if len(flags) > 1 {
		t.Reversal = flags[1]
	}
	return t
}

func TestAccountBalanceOfPostings(t *testing.T) {
	cases := []struct {
		name string
		txns []SavingsAccountTransaction
		want MinorUnits
	}{
		{
			name: "deposit then withdrawal",
			txns: []SavingsAccountTransaction{
				txn(TxnDeposit, 100_000),
				txn(TxnWithdrawal, 25_000),
			},
			want: 75_000,
		},
		{
			name: "interest posting is a credit",
			txns: []SavingsAccountTransaction{
				txn(TxnDeposit, 100_000),
				txn(TxnInterestPosting, 500),
			},
			want: 100_500,
		},
		{
			name: "fees and withhold tax are debits",
			txns: []SavingsAccountTransaction{
				txn(TxnDeposit, 100_000),
				txn(TxnWithdrawalFee, 1_000),
				txn(TxnWithholdTax, 200),
			},
			want: 98_800,
		},
		{
			name: "hold release and escheat never move posted balance",
			txns: []SavingsAccountTransaction{
				txn(TxnDeposit, 100_000),
				txn(TxnAmountHold, 30_000),
				txn(TxnAmountRelease, 30_000),
				txn(TxnEscheat, 100_000),
			},
			want: 100_000,
		},
		{
			name: "unclassified types never move posted balance",
			txns: []SavingsAccountTransaction{
				txn(TxnDeposit, 100_000),
				txn(TxnWaiveCharges, 5_000),
				txn(TxnAccrual, 7_000),
				txn(TxnInitiateTransfer, 9_000),
				txn(TxnApproveTransfer, 9_000),
				txn(TxnWithdrawTransfer, 9_000),
				txn(TxnRejectTransfer, 9_000),
				txn(TxnWrittenOff, 1_000),
			},
			want: 100_000,
		},
		{
			name: "amount is a magnitude so negative never double-negates",
			txns: []SavingsAccountTransaction{
				txn(TxnDeposit, -100_000),
				txn(TxnWithdrawal, -25_000),
			},
			want: 75_000,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := AccountBalanceOf(tc.txns); got != tc.want {
				t.Fatalf("AccountBalanceOf = %d, want %d", got, tc.want)
			}
		})
	}
}

func TestAccountBalanceOfReversalsCancel(t *testing.T) {
	// A DEPOSIT undone leaves TWO DEPOSIT rows: the original (is_reversed) and
	// the appended correction (is_reversal). Neither may contribute.
	txns := []SavingsAccountTransaction{
		txn(TxnDeposit, 100_000),
		txn(TxnDeposit, 100_000, true, false), // reversed original
		txn(TxnDeposit, 100_000, false, true), // the reversal row
		txn(TxnWithdrawal, 25_000),
	}
	if got := AccountBalanceOf(txns); got != 75_000 {
		t.Fatalf("AccountBalanceOf = %d, want 75_000", got)
	}
}

func TestHeldAndAvailable(t *testing.T) {
	txns := []SavingsAccountTransaction{
		txn(TxnDeposit, 100_000),
		txn(TxnAmountHold, 30_000),
		txn(TxnAmountRelease, 10_000),
	}
	if got := HeldOf(txns); got != 20_000 {
		t.Fatalf("HeldOf = %d, want 20_000", got)
	}
	if got := AvailableOf(txns); got != 80_000 {
		t.Fatalf("AvailableOf = %d, want 80_000", got)
	}
}

func TestRunningBalancesOfPrefixes(t *testing.T) {
	txns := []SavingsAccountTransaction{
		txn(TxnDeposit, 100_000),
		txn(TxnAmountHold, 30_000), // leaves running unchanged
		txn(TxnWithdrawal, 25_000),
		txn(TxnAmountRelease, 10_000), // leaves running unchanged
	}
	want := []MinorUnits{100_000, 100_000, 75_000, 75_000}
	got := RunningBalancesOf(txns)
	if len(got) != len(want) {
		t.Fatalf("RunningBalancesOf length = %d, want %d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("RunningBalancesOf[%d] = %d, want %d", i, got[i], want[i])
		}
	}
	if last := got[len(got)-1]; last != AccountBalanceOf(txns) {
		t.Fatalf("RunningBalancesOf last = %d, AccountBalanceOf = %d", last, AccountBalanceOf(txns))
	}
}
