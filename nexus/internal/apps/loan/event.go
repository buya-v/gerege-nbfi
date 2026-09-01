package loan

import "fmt"

// LoanEvent is Fineract's LoanEvent — the vocabulary of lifecycle events that
// drive LoanLifecycleStateMachine. [VERIFIED: LoanEvent.java:24-56]
//
// Unlike LoanStatus and LoanTransactionType, LoanEvent has no stored integer:
// the oracle persists no event column for these, it only uses the enum to
// dispatch a transition. The Go type is therefore a plain enumerator with no
// StoredValue() method; the String() names match the Java constants exactly so
// that captured vectors keyed on the Java constant name can be compared
// directly.
type LoanEvent int32

const (
	EventLoanCreated LoanEvent = iota
	EventLoanRejected
	EventLoanWithdrawn
	EventLoanApproved
	EventLoanApprovalUndo
	EventLoanRecoveryPayment
	EventLoanDisbursed
	EventLoanDisbursalUndo
	EventLoanDisbursalUndoLast
	EventLoanRepaymentOrWaiver
	EventRepaidInFull
	EventWriteOffOutstanding
	EventWriteOffOutstandingUndo
	EventLoanReschedule
	EventInterestRebateOwed
	EventLoanOverpayment
	EventLoanChargePayment
	EventLoanClosed
	EventLoanEditMultiDisburseDate
	EventLoanRefund
	EventLoanForeclosure
	EventLoanAdjustTransaction
	EventLoanInitiateTransfer
	EventLoanRejectTransfer
	EventLoanWithdrawTransfer
	EventLoanCompleteTransfer
	EventLoanCreditBalanceRefund
	EventLoanChargeback
	EventLoanChargeAdded
	EventLoanChargeAdjustment
	EventLoanContractTermination
)

var loanEventName = map[LoanEvent]string{
	EventLoanCreated:               "LOAN_CREATED",
	EventLoanRejected:              "LOAN_REJECTED",
	EventLoanWithdrawn:             "LOAN_WITHDRAWN",
	EventLoanApproved:              "LOAN_APPROVED",
	EventLoanApprovalUndo:          "LOAN_APPROVAL_UNDO",
	EventLoanRecoveryPayment:       "LOAN_RECOVERY_PAYMENT",
	EventLoanDisbursed:             "LOAN_DISBURSED",
	EventLoanDisbursalUndo:         "LOAN_DISBURSAL_UNDO",
	EventLoanDisbursalUndoLast:     "LOAN_DISBURSAL_UNDO_LAST",
	EventLoanRepaymentOrWaiver:     "LOAN_REPAYMENT_OR_WAIVER",
	EventRepaidInFull:              "REPAID_IN_FULL",
	EventWriteOffOutstanding:       "WRITE_OFF_OUTSTANDING",
	EventWriteOffOutstandingUndo:   "WRITE_OFF_OUTSTANDING_UNDO",
	EventLoanReschedule:            "LOAN_RESCHEDULE",
	EventInterestRebateOwed:        "INTERST_REBATE_OWED",
	EventLoanOverpayment:           "LOAN_OVERPAYMENT",
	EventLoanChargePayment:         "LOAN_CHARGE_PAYMENT",
	EventLoanClosed:                "LOAN_CLOSED",
	EventLoanEditMultiDisburseDate: "LOAN_EDIT_MULTI_DISBURSE_DATE",
	EventLoanRefund:                "LOAN_REFUND",
	EventLoanForeclosure:           "LOAN_FORECLOSURE",
	EventLoanAdjustTransaction:     "LOAN_ADJUST_TRANSACTION",
	EventLoanInitiateTransfer:      "LOAN_INITIATE_TRANSFER",
	EventLoanRejectTransfer:        "LOAN_REJECT_TRANSFER",
	EventLoanWithdrawTransfer:      "LOAN_WITHDRAW_TRANSFER",
	EventLoanCompleteTransfer:      "LOAN_COMPLETE_TRANSFER",
	EventLoanCreditBalanceRefund:   "LOAN_CREDIT_BALANCE_REFUND",
	EventLoanChargeback:            "LOAN_CHARGEBACK",
	EventLoanChargeAdded:           "LOAN_CHARGE_ADDED",
	EventLoanChargeAdjustment:      "LOAN_CHARGE_ADJUSTMENT",
	EventLoanContractTermination:   "LOAN_CONTRACT_TERMINATION",
}

func (e LoanEvent) String() string {
	if n, ok := loanEventName[e]; ok {
		return n
	}
	return fmt.Sprintf("LoanEvent(%d)", int32(e))
}
