package loan

// Facts is the balance-derived snapshot the loan lifecycle state machine reads
// to decide a transition. It is the pure-data stand-in for the Loan aggregate's
// summary and overpaid fields, deliberately limited to the five booleans
// DefaultLoanLifecycleStateMachine actually reads. None of these are stored
// independently of the balances they summarise — they are derived, per the
// G-12 derive-don't-store ruling.
//
// [VERIFIED: DefaultLoanLifecycleStateMachine.java:147-149 (determineTransition),
// :94-99 and :113-128 (getNextStatus's overpaid/repaid checks)]
type Facts struct {
	// HasOutstanding is summary.getTotalOutstanding(currency).isGreaterThanZero()
	// [VERIFIED: DefaultLoanLifecycleStateMachine.java:147].
	HasOutstanding bool
	// RepaidInFull is summary.isRepaidInFull(currency)
	// [VERIFIED: DefaultLoanLifecycleStateMachine.java:148].
	RepaidInFull bool
	// TotalOverpaidIsPositive is totalOverpaid > 0
	// [VERIFIED: DefaultLoanLifecycleStateMachine.java:149].
	TotalOverpaidIsPositive bool
	// TotalOverpaidIsZero is totalOverpaidAsMoney.isZero(), used only by the
	// LOAN_DISBURSED branch from an OVERPAID status whose balance has since been
	// refunded to zero [VERIFIED: DefaultLoanLifecycleStateMachine.java:94-95].
	TotalOverpaidIsZero bool
	// AllChargesPaid is the "every charge is !active || amount<=0 || paid ||
	// waived" predicate [VERIFIED: DefaultLoanLifecycleStateMachine.java:150-151].
	AllChargesPaid bool
}

// NextStatus ports DefaultLoanLifecycleStateMachine.getNextStatus
// [VERIFIED: DefaultLoanLifecycleStateMachine.java:76-140]: it maps
// (current status, event, facts) to a new status, returning ok=false when the
// event is not legal from the current status (the oracle leaves newState null
// and returns the unchanged status). StatusInvalid is the port's sentinel for
// the oracle's null status on a brand-new loan, used only by LOAN_CREATED.
func NextStatus(from LoanStatus, event LoanEvent, f Facts) (LoanStatus, bool) {
	if event == EventLoanCreated && from == StatusInvalid {
		return StatusSubmittedAndPendingApproval, true
	}

	switch event {
	case EventLoanRejected:
		if from == StatusSubmittedAndPendingApproval {
			return StatusRejected, true
		}
	case EventLoanApproved:
		if from == StatusSubmittedAndPendingApproval {
			return StatusApproved, true
		}
	case EventLoanWithdrawn:
		if from == StatusSubmittedAndPendingApproval {
			return StatusWithdrawnByClient, true
		}
	case EventLoanDisbursed:
		if from == StatusApproved || from == StatusClosedObligationsMet {
			return StatusActive, true
		}
		if from == StatusOverpaid && f.TotalOverpaidIsZero {
			if f.TotalOutstandingIsZero() {
				return StatusClosedObligationsMet, true
			}
			return StatusActive, true
		}
	case EventLoanApprovalUndo:
		if from == StatusApproved {
			return StatusSubmittedAndPendingApproval, true
		}
	case EventLoanDisbursalUndo:
		if from == StatusActive {
			return StatusApproved, true
		}
	case EventLoanChargePayment, EventLoanRepaymentOrWaiver, EventLoanChargeback:
		if from == StatusClosedObligationsMet || from == StatusOverpaid {
			return StatusActive, true
		}
	case EventRepaidInFull:
		if from == StatusActive || from == StatusOverpaid {
			return StatusClosedObligationsMet, true
		}
	case EventWriteOffOutstanding:
		if from == StatusActive {
			return StatusClosedWrittenOff, true
		}
	case EventLoanReschedule:
		if from == StatusActive {
			return StatusClosedRescheduleOutstandingAmount, true
		}
	case EventLoanOverpayment:
		if from == StatusClosedObligationsMet || from == StatusActive {
			return StatusOverpaid, true
		}
	case EventLoanAdjustTransaction:
		if from == StatusClosedObligationsMet || from == StatusClosedWrittenOff || from == StatusClosedRescheduleOutstandingAmount {
			if f.TotalOverpaidIsPositive {
				return StatusOverpaid, true
			}
			return StatusActive, true
		}
	case EventLoanInitiateTransfer:
		// Unconditional: any status may initiate a transfer
		// [VERIFIED: DefaultLoanLifecycleStateMachine.java:124-126].
		return StatusTransferInProgress, true
	case EventLoanRejectTransfer:
		if from == StatusTransferInProgress {
			return StatusTransferOnHold, true
		}
	case EventLoanWithdrawTransfer:
		if from == StatusTransferInProgress {
			return StatusActive, true
		}
	case EventLoanCompleteTransfer:
		if from == StatusTransferInProgress {
			if f.TotalOverpaidIsPositive {
				return StatusOverpaid, true
			}
			if f.RepaidInFull {
				return StatusClosedObligationsMet, true
			}
			return StatusActive, true
		}
	case EventWriteOffOutstandingUndo:
		if from == StatusClosedWrittenOff {
			return StatusActive, true
		}
	case EventLoanCreditBalanceRefund:
		if from == StatusOverpaid {
			return StatusClosedObligationsMet, true
		}
	case EventLoanChargeAdded:
		if from == StatusClosedObligationsMet {
			return StatusActive, true
		}
	case EventLoanChargeAdjustment:
		if from == StatusClosedObligationsMet {
			return StatusOverpaid, true
		}
	}
	return from, false
}

// TotalOutstandingIsZero is a derived fact: the complement of HasOutstanding,
// used by the LOAN_DISBURSED-from-OVERPAID branch.
func (f Facts) TotalOutstandingIsZero() bool { return !f.HasOutstanding }

// Transition describes the result of DetermineTransition: the target status and
// the canonical event that would effect it, mirroring the oracle's private
// LoanStatusTransition record [VERIFIED:
// DefaultLoanLifecycleStateMachine.java:196-213].
type Transition struct {
	Status LoanStatus
	Event  LoanEvent
	Needed bool
}

// NoTransition reports the status is already settled.
func NoTransition(current LoanStatus) Transition {
	return Transition{Status: current, Needed: false}
}

// DetermineTransition ports DefaultLoanLifecycleStateMachine.determineTransition
// [VERIFIED: DefaultLoanLifecycleStateMachine.java:143-174]: it recomputes the
// status from balance facts for a loan that is currently in a terminal or
// active state. Unlike NextStatus it is not event-dispatched; it asks "given
// the balances, has this loan crossed a status boundary?".
//
// The date side effects (setClosedOnDate, setActualMaturityDate,
// handleMaturityDateActivate, setOverpaidOnDate) are deliberately NOT ported:
// those mutate the aggregate and are the caller's responsibility once the
// derived status is applied. Only the status/event decision is reproduced.
func DetermineTransition(from LoanStatus, f Facts) Transition {
	switch {
	case from.IsOverpaid():
		if !f.TotalOverpaidIsPositive {
			if f.RepaidInFull && f.AllChargesPaid {
				return Transition{Status: StatusClosedObligationsMet, Event: EventLoanCreditBalanceRefund, Needed: true}
			}
			if f.HasOutstanding {
				return Transition{Status: StatusActive, Event: EventLoanRepaymentOrWaiver, Needed: true}
			}
		}
		return NoTransition(StatusOverpaid)
	case from.IsClosedObligationsMet():
		if f.TotalOverpaidIsPositive {
			return Transition{Status: StatusOverpaid, Event: EventLoanOverpayment, Needed: true}
		}
		if f.HasOutstanding {
			return Transition{Status: StatusActive, Event: EventLoanRepaymentOrWaiver, Needed: true}
		}
		return NoTransition(StatusClosedObligationsMet)
	case from.IsActive():
		if f.TotalOverpaidIsPositive {
			return Transition{Status: StatusOverpaid, Event: EventLoanOverpayment, Needed: true}
		}
		if f.RepaidInFull && f.AllChargesPaid {
			return Transition{Status: StatusClosedObligationsMet, Event: EventRepaidInFull, Needed: true}
		}
		return NoTransition(StatusActive)
	case from.IsClosedWrittenOff() || from.IsClosedRescheduleOutstandingAmount():
		if f.HasOutstanding {
			return Transition{Status: StatusActive, Event: EventLoanAdjustTransaction, Needed: true}
		}
		return NoTransition(from)
	}
	return NoTransition(from)
}
