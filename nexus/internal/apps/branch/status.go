package branch

// TellerStatus is the m_tellers.state column: an integer status code with the
// Fineract teller lifecycle semantics. INVALID(0) is the missing/unrecognised
// sentinel; a fromInt on an unknown value returns INVALID without error.
//
// [VERIFIED: TellerStatus.java — INVALID(0), PENDING(100), ACTIVE(300),
// INACTIVE(400), CLOSED(600); fromInt maps 100/300/400/600 and defaults to
// INVALID.]
type TellerStatus int32

const (
	TellerStatusInvalid  TellerStatus = 0
	TellerStatusPending  TellerStatus = 100
	TellerStatusActive   TellerStatus = 300
	TellerStatusInactive TellerStatus = 400
	TellerStatusClosed   TellerStatus = 600
)

// StoredValue returns the integer Fineract persists in the state column.
func (s TellerStatus) StoredValue() int32 { return int32(s) }

// TellerStatusFromInt ports TellerStatus.fromInt: it maps the four known codes
// and returns INVALID for anything else (including nil, which the port's callers
// represent as 0).
func TellerStatusFromInt(v int32) TellerStatus {
	switch v {
	case 100:
		return TellerStatusPending
	case 300:
		return TellerStatusActive
	case 400:
		return TellerStatusInactive
	case 600:
		return TellerStatusClosed
	default:
		return TellerStatusInvalid
	}
}

// IsPending ports TellerStatus.isPending.
func (s TellerStatus) IsPending() bool { return s == TellerStatusPending }

// IsActive ports TellerStatus.isActive.
func (s TellerStatus) IsActive() bool { return s == TellerStatusActive }

// IsInactive ports TellerStatus.isInactive.
func (s TellerStatus) IsInactive() bool { return s == TellerStatusInactive }

// IsClosed ports TellerStatus.isClosed.
func (s TellerStatus) IsClosed() bool { return s == TellerStatusClosed }

// CashierTxnType is one row of the cashier transaction-type table. Fineract
// models it as a small value object with a numeric id and a display value; the
// four live rows are the constants below.
//
// [VERIFIED: CashierTxnType.java — ALLOCATE(101), SETTLE(102),
// INWARD_CASH_TXN(103), OUTWARD_CASH_TXN(104); getCashierTxnType returns null
// for any other id.]
type CashierTxnType struct {
	ID    int32
	Value string
}

var (
	// TxnAllocate is "Allocate Cash": cash moved from the office float into a
	// cashier's till.
	TxnAllocate = CashierTxnType{ID: 101, Value: "Allocate Cash"}
	// TxnSettle is "Settle Cash": cash moved out of a cashier's till back to the
	// office float.
	TxnSettle = CashierTxnType{ID: 102, Value: "Settle Cash"}
	// TxnInwardCash is "Cash In": a client deposit taken at the till.
	TxnInwardCash = CashierTxnType{ID: 103, Value: "Cash In"}
	// TxnOutwardCash is "Cash Out": a client withdrawal paid at the till.
	TxnOutwardCash = CashierTxnType{ID: 104, Value: "Cash Out"}
)

// CashierTxnTypeFromID ports CashierTxnType.getCashierTxnType, returning the
// matching type and false for an unknown id (Fineract returns null).
func CashierTxnTypeFromID(id int32) (CashierTxnType, bool) {
	switch id {
	case 101:
		return TxnAllocate, true
	case 102:
		return TxnSettle, true
	case 103:
		return TxnInwardCash, true
	case 104:
		return TxnOutwardCash, true
	default:
		return CashierTxnType{}, false
	}
}
