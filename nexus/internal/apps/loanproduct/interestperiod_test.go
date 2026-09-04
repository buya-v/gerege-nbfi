package loanproduct

import "testing"

// TestOutstandingLoanBalanceIsASweptSnapshot pins the one property that decides
// whether InterestPeriod.outstandingLoanBalance may be turned into an on-demand
// derivation. It may not, and this test is what makes that falsifiable rather
// than asserted.
//
// THE ORACLE BEHAVIOUR BEING PINNED. updateOutstandingLoanBalance is the whole
// refresh mechanism for the cell [VERIFIED: InterestPeriod.java:168-188]. The
// oracle runs it only from explicit sweeps [VERIFIED:
// ProgressiveEMICalculator.java:1254-1256, :1647, :1654, :1667] and deliberately
// leaves the cell unrefreshed in between — RepaymentPeriod.copyWithoutPaidAmounts
// zeroes a summand of the roll-forward and does not re-run the sweep [VERIFIED:
// RepaymentPeriod.java:173-198]. So between sweeps the stored value is NOT what
// re-evaluating the expression would produce, and that difference is observable
// money.
//
// WHY THIS TEST EXISTS. A source guard over the Go tree
// (.softhouse/guards/ledgerguard, class I3-FIELD-WRITE) refuses the assignment
// in UpdateOutstandingLoanBalance because the field's name contains "balance",
// and prescribes "derive by summation over the postings". Applied here that
// prescription is A PARITY BREAK: deriving the cell on read would silently
// change the numbers at every point where the oracle leaves it stale. That, on
// its own, is why the prescription is not the repair — and this test is what
// makes it a failing build rather than an argument. If a later change adopts the
// derive-on-read shape, this test fails instead of the divergence shipping
// unnoticed.
//
// DO NOT SUBSTITUTE EITHER RETIRED ARGUMENT FOR THAT, and this comment is where
// you would be standing when you were tempted to. "It never becomes a database
// column" is FALSE — the cell is serialised into
// m_loan_progressive_model.json_model and read back
// [VERIFIED: InterestPeriod.java:65-66 carry no @JsonExclude;
// InterestScheduleModelRepositoryWrapperImpl.java:95, :110-128]. "There is no
// posting stream behind it" is ALSO FALSE — UpdateOutstandingLoanBalance folds
// the previous period's PaidPrincipal [VERIFIED: InterestPeriod.java:178], which
// is accumulated from real LoanTransactions
// [VERIFIED: RepaymentPeriod.java:405-407; ProgressiveEMICalculator.java:421;
// AdvancedPaymentScheduleTransactionProcessor.java:929, :967, :2912]. doc.go,
// "Two arguments that do not work", carries both counterexamples; the argument
// that does hold is the parity leg this test executes, plus the reachability
// leg (the value's forward trace terminates in DTOs and the oracle's calc
// package emits no journal entry).
func TestOutstandingLoanBalanceIsASweptSnapshot(t *testing.T) {
	r := testRounding()
	cur := testCurrency()
	detail := testDetail()

	rp1 := NewRepaymentPeriod(nil, date(2023, 1, 1), date(2023, 2, 1),
		NewMoney(10000, cur, r), r, cur, InterestDecliningBalance)
	rp2 := NewRepaymentPeriod(rp1, date(2023, 2, 1), date(2023, 3, 1),
		NewMoney(10000, cur, r), r, cur, InterestDecliningBalance)

	rp1.InterestPeriods[0].AddDisbursementAmount(NewMoney(100000, cur, r)) // 1000.00

	m := NewScheduleModel([]*RepaymentPeriod{rp1, rp2}, detail, 0, r, cur)
	CalculateOutstandingBalance(m)

	// Baseline, same arithmetic as TestCalculateOutstandingBalanceRollsAcrossPeriods:
	// 0 + 1000.00 disbursed - 100.00 due principal = 900.00.
	const wantAfterFirstSweep = 90000
	if got := rp2.InterestPeriods[0].OutstandingLoanBalance().Minor(); got != wantAfterFirstSweep {
		t.Fatalf("after sweep: outstanding = %d minor units, want %d", got, wantAfterFirstSweep)
	}

	// Mutate a SUMMAND of the roll-forward on the segment rp2 reads from, and do
	// NOT sweep. The oracle's stored cell does not move; an on-demand derivation
	// would move it to 700.00 immediately.
	rp1.InterestPeriods[0].AddBalanceCorrectionAmount(NewMoney(-20000, cur, r)) // -200.00

	if got := rp2.InterestPeriods[0].OutstandingLoanBalance().Minor(); got != wantAfterFirstSweep {
		t.Fatalf("the cell is a SWEPT SNAPSHOT, not an on-demand derivation: reading it after a "+
			"summand changed but before a sweep gave %d minor units, want the unchanged %d. "+
			"A port that derives this cell on read diverges from the oracle everywhere the "+
			"oracle leaves it stale (RepaymentPeriod.java:173-198).",
			got, wantAfterFirstSweep)
	}

	// The sweep is the only thing that moves it. 0 + 1000.00 - 200.00 correction
	// - 100.00 due principal = 700.00.
	CalculateOutstandingBalance(m)

	const wantAfterSecondSweep = 70000
	if got := rp2.InterestPeriods[0].OutstandingLoanBalance().Minor(); got != wantAfterSecondSweep {
		t.Fatalf("after the second sweep: outstanding = %d minor units, want %d",
			got, wantAfterSecondSweep)
	}
}

// TestBalanceCorrectionAmountIsASignedDelta pins that balanceCorrectionAmount
// accumulates signed amounts and is never floored at zero — the behaviour that
// makes it a DELTA rather than a balance. Every oracle caller adds a negated
// principal amount to it [VERIFIED: ProgressiveEMICalculator.java:922, :952,
// :1129], so a port that clamped it non-negative would zero every real
// correction the oracle makes.
func TestBalanceCorrectionAmountIsASignedDelta(t *testing.T) {
	r := testRounding()
	cur := testCurrency()

	rp := NewRepaymentPeriod(nil, date(2023, 1, 1), date(2023, 2, 1),
		NewMoney(10000, cur, r), r, cur, InterestDecliningBalance)
	ip := rp.InterestPeriods[0]

	ip.AddBalanceCorrectionAmount(NewMoney(-20000, cur, r))
	if got := ip.BalanceCorrectionAmount().Minor(); got != -20000 {
		t.Fatalf("correction after one negated add = %d minor units, want -20000", got)
	}

	ip.AddBalanceCorrectionAmount(NewMoney(-5000, cur, r))
	if got := ip.BalanceCorrectionAmount().Minor(); got != -25000 {
		t.Fatalf("correction after a second negated add = %d minor units, want -25000", got)
	}

	// copyWithoutPaidAmounts nets the cell to exactly zero, matching
	// addBalanceCorrectionAmount(negated) [VERIFIED: RepaymentPeriod.java:192-194].
	c := rp.copyWithoutPaidAmounts(nil)
	if got := c.InterestPeriods[0].BalanceCorrectionAmount().Minor(); got != 0 {
		t.Fatalf("copyWithoutPaidAmounts left correction = %d minor units, want 0", got)
	}
	if got := ip.BalanceCorrectionAmount().Minor(); got != -25000 {
		t.Fatalf("copyWithoutPaidAmounts mutated the ORIGINAL: correction = %d, want -25000", got)
	}
}
