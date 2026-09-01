package investor

// ExternalTransferStatus is the status column of an external asset owner
// transfer. Fineract persists it by NAME into a VARCHAR(50) column and does not
// assign it an integer code, so this port stores the string value directly.
//
// [VERIFIED: ExternalTransferStatus.java — enum ACTIVE, ACTIVE_INTERMEDIATE,
// DECLINED, PENDING, PENDING_INTERMEDIATE, BUYBACK, BUYBACK_INTERMEDIATE,
// CANCELLED; ExternalAssetOwnerTransfer.java @Column(name="status")
// @Enumerated(EnumType.STRING).]
type ExternalTransferStatus string

const (
	TransferStatusActive              ExternalTransferStatus = "ACTIVE"
	TransferStatusActiveIntermediate  ExternalTransferStatus = "ACTIVE_INTERMEDIATE"
	TransferStatusDeclined            ExternalTransferStatus = "DECLINED"
	TransferStatusPending             ExternalTransferStatus = "PENDING"
	TransferStatusPendingIntermediate ExternalTransferStatus = "PENDING_INTERMEDIATE"
	TransferStatusBuyback             ExternalTransferStatus = "BUYBACK"
	TransferStatusBuybackIntermediate ExternalTransferStatus = "BUYBACK_INTERMEDIATE"
	TransferStatusCancelled           ExternalTransferStatus = "CANCELLED"
)

// StoredValue returns the exact string Fineract persists in the status column.
func (s ExternalTransferStatus) StoredValue() string { return string(s) }

// ExternalTransferSubStatus is the optional sub-status column of an external
// asset owner transfer, also persisted by name (VARCHAR(50), nullable).
//
// [VERIFIED: ExternalTransferSubStatus.java — BALANCE_ZERO, BALANCE_NEGATIVE,
// SAMEDAY_TRANSFERS, USER_REQUESTED, UNSOLD; ExternalAssetOwnerTransfer.java
// @Column(name="sub_status") @Enumerated(EnumType.STRING).]
type ExternalTransferSubStatus string

const (
	TransferSubStatusBalanceZero      ExternalTransferSubStatus = "BALANCE_ZERO"
	TransferSubStatusBalanceNegative  ExternalTransferSubStatus = "BALANCE_NEGATIVE"
	TransferSubStatusSamedayTransfers ExternalTransferSubStatus = "SAMEDAY_TRANSFERS"
	TransferSubStatusUserRequested    ExternalTransferSubStatus = "USER_REQUESTED"
	TransferSubStatusUnsold           ExternalTransferSubStatus = "UNSOLD"
)

// StoredValue returns the exact string Fineract persists in the sub_status column.
func (s ExternalTransferSubStatus) StoredValue() string { return string(s) }
