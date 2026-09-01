package loan

// MinorUnits is a monetary quantity expressed as an integer count of the
// currency's minor unit (MNT minor unit = 2), the same convention the ledger,
// charges, provisioning and loanschedule packages use. The loan lifecycle is
// single-currency per account in the port, so LoanSummary is currency-agnostic:
// the caller supplies balances already normalised to one currency.
type MinorUnits int64

// LoanSummary is the balance-derived money core of the loan lifecycle. It is
// the Go port of the outstanding-bucket portion of Fineract's LoanSummary
// embeddable — specifically the four outstanding buckets and the overpaid
// amount the lifecycle state machine reads to derive a status.
//
// [VERIFIED: LoanSummary.java:143-176 — totalPrincipalOutstanding,
// totalInterestOutstanding, totalFeeChargesOutstanding,
// totalPenaltyChargesOutstanding, totalOutstanding; Loan.java:1350-1351 —
// totalOverpaid as Money.]
//
// It is deliberately a pure, immutable value object: every field is DERIVED
// from transaction and charge balances, never stored independently of them,
// per the G-12 derive-don't-store ruling. The four outstanding buckets
// decompose the single totalOutstanding the oracle also persists, so the port
// keeps the decomposition (the authority) and derives the total.
type LoanSummary struct {
	// PrincipalOutstanding is totalPrincipalOutstanding: principal disbursed and
	// not yet repaid/written off.
	PrincipalOutstanding MinorUnits
	// InterestOutstanding is totalInterestOutstanding: interest accrued and not
	// yet repaid/waived/written off.
	InterestOutstanding MinorUnits
	// FeeChargesOutstanding is totalFeeChargesOutstanding: fees charged and not
	// yet repaid/waived/written off.
	FeeChargesOutstanding MinorUnits
	// PenaltyChargesOutstanding is totalPenaltyChargesOutstanding: penalties
	// charged and not yet repaid/waived/written off.
	PenaltyChargesOutstanding MinorUnits
	// Overpaid is totalOverpaid: money received in excess of totalOutstanding.
	Overpaid MinorUnits
}

// TotalOutstanding ports LoanSummary.getTotalOutstanding
// [VERIFIED: LoanSummary.java:280-282 — Money.of(totalOutstanding)], which is
// the sum of the four outstanding buckets [VERIFIED: LoanSummary.java:262-265].
func (s LoanSummary) TotalOutstanding() MinorUnits {
	return s.PrincipalOutstanding + s.InterestOutstanding + s.FeeChargesOutstanding + s.PenaltyChargesOutstanding
}

// IsRepaidInFull ports LoanSummary.isRepaidInFull
// [VERIFIED: LoanSummary.java:304-306 — getTotalOutstanding().isZero()]. A loan
// is repaid in full when nothing is outstanding, regardless of how much was
// overpaid on top.
func (s LoanSummary) IsRepaidInFull() bool { return s.TotalOutstanding() == 0 }

// HasOutstanding ports the getTotalOutstanding().isGreaterThanZero() read the
// state machine makes [VERIFIED: DefaultLoanLifecycleStateMachine.java:311].
func (s LoanSummary) HasOutstanding() bool { return s.TotalOutstanding() > 0 }

// IsOverpaid ports MathUtil.isGreaterThanZero(loan.getTotalOverpaid())
// [VERIFIED: DefaultLoanLifecycleStateMachine.java:313].
func (s LoanSummary) IsOverpaid() bool { return s.Overpaid > 0 }

// OverpaidIsZero ports the totalOverpaid.isZero() read in the
// LOAN_DISBURSED-from-OVERPAID branch [VERIFIED:
// DefaultLoanLifecycleStateMachine.java:94-95].
func (s LoanSummary) OverpaidIsZero() bool { return s.Overpaid == 0 }

// Facts derives the pure boolean snapshot the lifecycle state machine consumes,
// collapsing the money balances into exactly the five predicates
// DefaultLoanLifecycleStateMachine reads [VERIFIED:
// DefaultLoanLifecycleStateMachine.java:311-316]. allChargesPaid is supplied by
// the caller because it is a predicate over the active charge list (a charge
// domain concern owned by the charges package), not over these balances.
func (s LoanSummary) Facts(allChargesPaid bool) Facts {
	return Facts{
		HasOutstanding:          s.HasOutstanding(),
		RepaidInFull:            s.IsRepaidInFull(),
		TotalOverpaidIsPositive: s.IsOverpaid(),
		TotalOverpaidIsZero:     s.OverpaidIsZero(),
		AllChargesPaid:          allChargesPaid,
	}
}
