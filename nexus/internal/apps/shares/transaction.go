package shares

import "time"

// ShareAccountTransaction is one m_share_account_transactions row: a purchase,
// redemption, dividend or charge movement on a share account. TotalShares is the
// number of shares moved; Amount and ChargeAmount are monetary and therefore
// integer minor units.
//
// [VERIFIED: ShareAccountTransaction.java — transaction_date, total_shares,
// transaction_type, amount, status, charge_amount, charge_id.]
type ShareAccountTransaction struct {
	ID              int64
	AccountID       int64
	TransactionDate time.Time
	TotalShares     int64
	Type            ShareAccountTransactionType
	Amount          MinorUnits
	Status          PurchaseStatus
	ChargeAmount    MinorUnits
	ChargeID        *int64
}
