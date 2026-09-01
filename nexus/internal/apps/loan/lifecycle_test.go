package loan

import "testing"

func TestLoanStatusRoundTrip(t *testing.T) {
	want := map[int32]string{
		0:   "INVALID",
		100: "SUBMITTED_AND_PENDING_APPROVAL",
		200: "APPROVED",
		300: "ACTIVE",
		303: "TRANSFER_IN_PROGRESS",
		304: "TRANSFER_ON_HOLD",
		400: "WITHDRAWN_BY_CLIENT",
		500: "REJECTED",
		600: "CLOSED_OBLIGATIONS_MET",
		601: "CLOSED_WRITTEN_OFF",
		602: "CLOSED_RESCHEDULE_OUTSTANDING_AMOUNT",
		700: "OVERPAID",
	}
	for stored, name := range want {
		got, ok := LoanStatusFromStoredValue(stored)
		if !ok || got.String() != name {
			t.Fatalf("stored %d -> %v(%v), want %s", stored, got, ok, name)
		}
		if got.StoredValue() != stored {
			t.Fatalf("%s.StoredValue() = %d, want %d", got, got.StoredValue(), stored)
		}
	}
	for _, bad := range []int32{99, 301, 305, 399, 603} {
		if _, ok := LoanStatusFromStoredValue(bad); ok {
			t.Fatalf("stored %d must not decode", bad)
		}
	}
}

func TestLoanTransactionTypeGapAtEleven(t *testing.T) {
	// The 11 gap is the trap: without it every transfer/refund value shifts.
	if _, ok := LoanTransactionTypeFromStoredValue(11); ok {
		t.Fatal("stored 11 is a gap and must not decode")
	}
	if got, ok := LoanTransactionTypeFromStoredValue(12); !ok || got != TransactionInitiateTransfer {
		t.Fatalf("stored 12 -> %v(%v), want INITIATE_TRANSFER", got, ok)
	}
	if got, ok := LoanTransactionTypeFromStoredValue(10); !ok || got != TransactionAccrual {
		t.Fatalf("stored 10 -> %v(%v), want ACCRUAL", got, ok)
	}
	if got, ok := LoanTransactionTypeFromStoredValue(47); !ok || got != TransactionDiscountFeeAmortizationAdjustment {
		t.Fatalf("stored 47 -> %v(%v), want DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT", got, ok)
	}
	if _, ok := LoanTransactionTypeFromStoredValue(48); ok {
		t.Fatal("stored 48 must not decode")
	}

	// Repayment-type union is what allocation code consumes.
	if !TransactionRepayment.IsRepaymentType() {
		t.Fatal("REPAYMENT must be a repayment type")
	}
	if !TransactionDownPayment.IsRepaymentType() {
		t.Fatal("DOWN_PAYMENT must be a repayment type")
	}
	if TransactionDisbursement.IsRepaymentType() {
		t.Fatal("DISBURSEMENT must not be a repayment type")
	}
}

func TestNextStatusHappyPath(t *testing.T) {
	steps := []struct {
		from  LoanStatus
		event LoanEvent
		want  LoanStatus
	}{
		{StatusInvalid, EventLoanCreated, StatusSubmittedAndPendingApproval},
		{StatusSubmittedAndPendingApproval, EventLoanApproved, StatusApproved},
		{StatusApproved, EventLoanDisbursed, StatusActive},
		{StatusActive, EventRepaidInFull, StatusClosedObligationsMet},
		{StatusClosedObligationsMet, EventLoanOverpayment, StatusOverpaid},
		{StatusOverpaid, EventLoanCreditBalanceRefund, StatusClosedObligationsMet},
	}
	for _, s := range steps {
		got, ok := NextStatus(s.from, s.event, Facts{})
		if !ok || got != s.want {
			t.Fatalf("NextStatus(%v,%v) = %v(%v), want %v", s.from, s.event, got, ok, s.want)
		}
	}
}

func TestNextStatusIllegal(t *testing.T) {
	if got, ok := NextStatus(StatusActive, EventLoanApproved, Facts{}); ok || got != StatusActive {
		t.Fatalf("LOAN_APPROVED from ACTIVE = %v(%v), want no transition", got, ok)
	}
}

func TestNextStatusWriteOffAndReschedule(t *testing.T) {
	if got, ok := NextStatus(StatusActive, EventWriteOffOutstanding, Facts{}); !ok || got != StatusClosedWrittenOff {
		t.Fatalf("WRITE_OFF_OUTSTANDING from ACTIVE = %v(%v)", got, ok)
	}
	if got, ok := NextStatus(StatusClosedWrittenOff, EventWriteOffOutstandingUndo, Facts{}); !ok || got != StatusActive {
		t.Fatalf("WRITE_OFF_OUTSTANDING_UNDO = %v(%v)", got, ok)
	}
	if got, ok := NextStatus(StatusActive, EventLoanReschedule, Facts{}); !ok || got != StatusClosedRescheduleOutstandingAmount {
		t.Fatalf("LOAN_RESCHEDULE from ACTIVE = %v(%v)", got, ok)
	}
}

func TestNextStatusTransfer(t *testing.T) {
	if got, ok := NextStatus(StatusActive, EventLoanInitiateTransfer, Facts{}); !ok || got != StatusTransferInProgress {
		t.Fatalf("LOAN_INITIATE_TRANSFER = %v(%v)", got, ok)
	}
	if got, ok := NextStatus(StatusTransferInProgress, EventLoanRejectTransfer, Facts{}); !ok || got != StatusTransferOnHold {
		t.Fatalf("LOAN_REJECT_TRANSFER = %v(%v)", got, ok)
	}
	if got, ok := NextStatus(StatusTransferInProgress, EventLoanWithdrawTransfer, Facts{}); !ok || got != StatusActive {
		t.Fatalf("LOAN_WITHDRAW_TRANSFER = %v(%v)", got, ok)
	}
	if got, ok := NextStatus(StatusTransferInProgress, EventLoanCompleteTransfer, Facts{RepaidInFull: true}); !ok || got != StatusClosedObligationsMet {
		t.Fatalf("LOAN_COMPLETE_TRANSFER (repaid) = %v(%v)", got, ok)
	}
	if got, ok := NextStatus(StatusTransferInProgress, EventLoanCompleteTransfer, Facts{}); !ok || got != StatusActive {
		t.Fatalf("LOAN_COMPLETE_TRANSFER (outstanding) = %v(%v)", got, ok)
	}
}

func TestNextStatusDisbursedFromOverpaid(t *testing.T) {
	// OVERPAID with a zero overpaid balance: outstanding -> ACTIVE, else CLOSED.
	got, ok := NextStatus(StatusOverpaid, EventLoanDisbursed, Facts{TotalOverpaidIsZero: true, HasOutstanding: true})
	if !ok || got != StatusActive {
		t.Fatalf("DISBURSED from OVERPAID(zero,outstanding) = %v(%v)", got, ok)
	}
	got, ok = NextStatus(StatusOverpaid, EventLoanDisbursed, Facts{TotalOverpaidIsZero: true})
	if !ok || got != StatusClosedObligationsMet {
		t.Fatalf("DISBURSED from OVERPAID(zero,no outstanding) = %v(%v)", got, ok)
	}
}

func TestDetermineTransitionActive(t *testing.T) {
	// Active + overpaid -> OVERPAID.
	tr := DetermineTransition(StatusActive, Facts{TotalOverpaidIsPositive: true})
	if !tr.Needed || tr.Status != StatusOverpaid || tr.Event != EventLoanOverpayment {
		t.Fatalf("Active/overpaid -> %+v", tr)
	}
	// Active + repaid + all charges paid -> CLOSED.
	tr = DetermineTransition(StatusActive, Facts{RepaidInFull: true, AllChargesPaid: true})
	if !tr.Needed || tr.Status != StatusClosedObligationsMet || tr.Event != EventRepaidInFull {
		t.Fatalf("Active/repaid -> %+v", tr)
	}
	// Active + repaid but an active charge remains -> no transition.
	tr = DetermineTransition(StatusActive, Facts{RepaidInFull: true})
	if tr.Needed {
		t.Fatalf("Active/repaid-but-unpaid-charge must not transition, got %+v", tr)
	}
}

func TestDetermineTransitionClosedWrittenOff(t *testing.T) {
	tr := DetermineTransition(StatusClosedWrittenOff, Facts{HasOutstanding: true})
	if !tr.Needed || tr.Status != StatusActive || tr.Event != EventLoanAdjustTransaction {
		t.Fatalf("ClosedWrittenOff/outstanding -> %+v", tr)
	}
	tr = DetermineTransition(StatusClosedWrittenOff, Facts{})
	if tr.Needed {
		t.Fatalf("ClosedWrittenOff/settled must not transition, got %+v", tr)
	}
}
