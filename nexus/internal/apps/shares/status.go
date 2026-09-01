package shares

// ShareAccountStatusType is the m_share_account.status_enum value. The name
// carries Fineract's "SUBMITED_AND_PENDING_APPROVAL" spelling (single T) on
// purpose, matching the enum in the oracle.
//
// [VERIFIED: ShareAccountStatusType.java — INVALID(0),
// SUBMITED_AND_PENDING_APPROVAL(100), APPROVED(200), ACTIVE(300),
// REJECTED(400), CLOSED(600); fromInt defaults to INVALID.]
type ShareAccountStatusType int32

const (
	ShareAccountStatusInvalid                     ShareAccountStatusType = 0
	ShareAccountStatusSubmittedAndPendingApproval ShareAccountStatusType = 100
	ShareAccountStatusApproved                    ShareAccountStatusType = 200
	ShareAccountStatusActive                      ShareAccountStatusType = 300
	ShareAccountStatusRejected                    ShareAccountStatusType = 400
	ShareAccountStatusClosed                      ShareAccountStatusType = 600
)

// StoredValue returns the integer Fineract persists in status_enum.
func (s ShareAccountStatusType) StoredValue() int32 { return int32(s) }

// ShareAccountStatusFromInt ports ShareAccountStatusType.fromInt.
func ShareAccountStatusFromInt(v int32) ShareAccountStatusType {
	switch v {
	case 100:
		return ShareAccountStatusSubmittedAndPendingApproval
	case 200:
		return ShareAccountStatusApproved
	case 300:
		return ShareAccountStatusActive
	case 400:
		return ShareAccountStatusRejected
	case 600:
		return ShareAccountStatusClosed
	default:
		return ShareAccountStatusInvalid
	}
}

// PurchaseStatus is the purchase-lifecycle status Fineract tracks per
// m_share_account_transaction (status_enum).
//
// [VERIFIED: PurchaseStatus.java — INVALID(0), APPLIED(100), APPROVED(200),
// REJECTED(300), WITHDRAWN(400); fromInt defaults to INVALID. Note Fineract's
// message key for WITHDRAWN is misspelled "withdrawan"; the port uses the clean
// name and does not reproduce the typo.]
type PurchaseStatus int32

const (
	PurchaseStatusInvalid   PurchaseStatus = 0
	PurchaseStatusApplied   PurchaseStatus = 100
	PurchaseStatusApproved  PurchaseStatus = 200
	PurchaseStatusRejected  PurchaseStatus = 300
	PurchaseStatusWithdrawn PurchaseStatus = 400
)

// StoredValue returns the integer Fineract persists in the status column.
func (s PurchaseStatus) StoredValue() int32 { return int32(s) }

// PurchaseStatusFromInt ports PurchaseStatus.fromInt.
func PurchaseStatusFromInt(v int32) PurchaseStatus {
	switch v {
	case 100:
		return PurchaseStatusApplied
	case 200:
		return PurchaseStatusApproved
	case 300:
		return PurchaseStatusRejected
	case 400:
		return PurchaseStatusWithdrawn
	default:
		return PurchaseStatusInvalid
	}
}

// ShareAccountTransactionType is the m_share_account_transaction
// transaction_type_enum value.
//
// [VERIFIED: ShareAccountTransactionType.java — INVALID(0), ISSUED(1),
// REDEEMED(2), CHARGE_PAYMENT(3), DIVIDEND_PAYMENT(4), CHARGE_ADJUSTMENT(5),
// ACTIVATE(6), APPROVE(7), REJECT(8), WITHDRAW(9); fromInt defaults to INVALID.]
type ShareAccountTransactionType int32

const (
	ShareTxnInvalid          ShareAccountTransactionType = 0
	ShareTxnIssued           ShareAccountTransactionType = 1
	ShareTxnRedeemed         ShareAccountTransactionType = 2
	ShareTxnChargePayment    ShareAccountTransactionType = 3
	ShareTxnDividendPayment  ShareAccountTransactionType = 4
	ShareTxnChargeAdjustment ShareAccountTransactionType = 5
	ShareTxnActivate         ShareAccountTransactionType = 6
	ShareTxnApprove          ShareAccountTransactionType = 7
	ShareTxnReject           ShareAccountTransactionType = 8
	ShareTxnWithdraw         ShareAccountTransactionType = 9
)

// StoredValue returns the integer Fineract persists in transaction_type_enum.
func (s ShareAccountTransactionType) StoredValue() int32 { return int32(s) }

// ShareAccountTransactionTypeFromInt ports ShareAccountTransactionType.fromInt.
func ShareAccountTransactionTypeFromInt(v int32) ShareAccountTransactionType {
	switch v {
	case 1:
		return ShareTxnIssued
	case 2:
		return ShareTxnRedeemed
	case 3:
		return ShareTxnChargePayment
	case 4:
		return ShareTxnDividendPayment
	case 5:
		return ShareTxnChargeAdjustment
	case 6:
		return ShareTxnActivate
	case 7:
		return ShareTxnApprove
	case 8:
		return ShareTxnReject
	case 9:
		return ShareTxnWithdraw
	default:
		return ShareTxnInvalid
	}
}
