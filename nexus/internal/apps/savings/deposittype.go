package savings

import "fmt"

// DepositAccountType is m_savings_product.deposit_type_enum — Fineract's
// DepositAccountType.
// [VERIFIED: DepositAccountType.java:24-39]
//
//	INVALID(0)                 SAVINGS_DEPOSIT(100)
//	FIXED_DEPOSIT(200)         RECURRING_DEPOSIT(300)
//	CURRENT_DEPOSIT(400)
//
// The stored values are NOT the declaration ordinal: each deposit family sits
// in its own 100-wide band (100 savings, 200 fixed, 300 recurring, 400
// current). An iota would collapse every value past SAVINGS_DEPOSIT, so the
// explicit StoredValue table below is the contract.
type DepositAccountType int32

const (
	DepositInvalid DepositAccountType = iota
	DepositSavings
	DepositFixed
	DepositRecurring
	DepositCurrent
)

var depositTypeStoredValue = map[DepositAccountType]int32{
	DepositInvalid:   0,
	DepositSavings:   100,
	DepositFixed:     200,
	DepositRecurring: 300,
	DepositCurrent:   400,
}

var depositTypeName = map[DepositAccountType]string{
	DepositInvalid:   "INVALID",
	DepositSavings:   "SAVINGS_DEPOSIT",
	DepositFixed:     "FIXED_DEPOSIT",
	DepositRecurring: "RECURRING_DEPOSIT",
	DepositCurrent:   "CURRENT_DEPOSIT",
}

var depositTypeFromStored = map[int32]DepositAccountType{}

// StoredValue returns m_savings_product.deposit_type_enum.
func (t DepositAccountType) StoredValue() int32 {
	v, ok := depositTypeStoredValue[t]
	if !ok {
		panic(fmt.Sprintf("savings: unknown DepositAccountType %d", int32(t)))
	}
	return v
}

func (t DepositAccountType) String() string {
	if n, ok := depositTypeName[t]; ok {
		return n
	}
	return fmt.Sprintf("DepositAccountType(%d)", int32(t))
}

// DepositAccountTypeFromStoredValue decodes m_savings_product.deposit_type_enum.
// ok is false outside the five legal values, matching DepositAccountType
// .fromInt's INVALID fallback [VERIFIED: DepositAccountType.java:41-58].
func DepositAccountTypeFromStoredValue(v int32) (DepositAccountType, bool) {
	t, ok := depositTypeFromStored[v]
	return t, ok
}

// IsSavingsDeposit / IsFixedDeposit / IsRecurringDeposit / IsCurrentDeposit
// mirror DepositAccountType's predicates [VERIFIED: DepositAccountType.java:59-65].
func (t DepositAccountType) IsSavingsDeposit() bool   { return t == DepositSavings }
func (t DepositAccountType) IsFixedDeposit() bool     { return t == DepositFixed }
func (t DepositAccountType) IsRecurringDeposit() bool { return t == DepositRecurring }
func (t DepositAccountType) IsCurrentDeposit() bool   { return t == DepositCurrent }

func init() {
	for t, v := range depositTypeStoredValue {
		if _, dup := depositTypeFromStored[v]; dup {
			panic(fmt.Sprintf("savings: deposit type encode table is not injective at %d", v))
		}
		depositTypeFromStored[v] = t
	}
}
