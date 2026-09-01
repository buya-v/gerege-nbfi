package branch

import "time"

// TellerTransaction is one m_teller_transactions row: a transaction performed
// by a cashier against a client at a teller. The Amount is the client-facing
// value Fineract stored as a Double.
//
// [VERIFIED: TellerTransaction.java — office_id, teller_id, cashier_id,
// client_id, type, amount, posting_date.]
type TellerTransaction struct {
	ID          int64
	OfficeID    int64
	TellerID    int64
	CashierID   int64
	ClientID    int64
	Type        int32
	Amount      MinorUnits
	PostingDate time.Time
}

// CashierTransaction is one m_cashier_transactions row: a till-level movement
// (allocate, settle, cash in, cash out) against a client or savings account
// entity. The TxnAmount is the till value Fineract stored as
// DECIMAL(19,6).
//
// [VERIFIED: CashierTransaction.java — cashier_id, txn_type, txn_date,
// txn_amount, txn_note, entity_type, entity_id, currency_code; txn_amount is
// BigDecimal.]
type CashierTransaction struct {
	ID           int64
	CashierID    int64
	TxnType      CashierTxnType
	TxnDate      time.Time
	TxnAmount    MinorUnits
	TxnNote      string
	EntityType   string
	EntityID     int64
	CurrencyCode string
}
