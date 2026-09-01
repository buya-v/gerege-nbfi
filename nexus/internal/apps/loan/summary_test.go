package loan

import "testing"

func TestLoanSummaryTotalOutstanding(t *testing.T) {
	s := LoanSummary{
		PrincipalOutstanding:      1_000_000,
		InterestOutstanding:       50_000,
		FeeChargesOutstanding:     10_000,
		PenaltyChargesOutstanding: 5_000,
	}
	if got := s.TotalOutstanding(); got != 1_065_000 {
		t.Fatalf("TotalOutstanding() = %d, want 1_065_000", got)
	}
	if s.IsRepaidInFull() {
		t.Error("IsRepaidInFull() = true, want false")
	}
	if !s.HasOutstanding() {
		t.Error("HasOutstanding() = false, want true")
	}
}

func TestLoanSummaryRepaidInFull(t *testing.T) {
	s := LoanSummary{Overpaid: 50_000} // overpaid but nothing outstanding
	if !s.IsRepaidInFull() {
		t.Error("IsRepaidInFull() = false, want true")
	}
	if s.HasOutstanding() {
		t.Error("HasOutstanding() = true, want false")
	}
	if !s.IsOverpaid() {
		t.Error("IsOverpaid() = false, want true")
	}
	if s.OverpaidIsZero() {
		t.Error("OverpaidIsZero() = true, want false")
	}
}

func TestLoanSummaryFactsBridge(t *testing.T) {
	s := LoanSummary{
		PrincipalOutstanding: 0,
		Overpaid:             0,
	}
	f := s.Facts(true)
	if !f.RepaidInFull || f.HasOutstanding || f.TotalOverpaidIsPositive {
		t.Errorf("Facts() = %+v, want repaid-in-full with no outstanding/overpaid", f)
	}
	if !f.AllChargesPaid || !f.TotalOverpaidIsZero {
		t.Errorf("Facts() = %+v, want allChargesPaid and overpaid zero", f)
	}
}

func TestLoanSummaryFactsRoundTripsLifecycle(t *testing.T) {
	// A fully repaid, fully charged loan derives CLOSED_OBLIGATIONS_MET from
	// the active status via the same Facts the state machine reads.
	s := LoanSummary{} // zero outstanding, zero overpaid
	f := s.Facts(true)
	next, ok := NextStatus(StatusActive, EventRepaidInFull, f)
	if !ok || next != StatusClosedObligationsMet {
		t.Errorf("NextStatus(ACTIVE, REPAID_IN_FULL) = %v, %v; want CLOSED_OBLIGATIONS_MET, true", next, ok)
	}

	// An overpaid loan derives OVERPAID from the same balance snapshot.
	over := LoanSummary{Overpaid: 1}
	next, ok = NextStatus(StatusActive, EventLoanOverpayment, over.Facts(true))
	if !ok || next != StatusOverpaid {
		t.Errorf("NextStatus(ACTIVE, OVERPAYMENT) = %v, %v; want OVERPAID, true", next, ok)
	}
}
