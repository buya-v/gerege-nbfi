package charges

import "fmt"

// ChargePaymentMode is m_charge.charge_payment_mode_enum — Fineract's
// ChargePaymentMode. [VERIFIED: ChargePaymentMode.java:25-28 — REGULAR(0),
// ACCOUNT_TRANSFER(1)]
type ChargePaymentMode int32

const (
	ChargePaymentModeRegular ChargePaymentMode = iota
	ChargePaymentModeAccountTransfer
)

var chargePaymentModeStoredValue = map[ChargePaymentMode]int32{
	ChargePaymentModeRegular:         0,
	ChargePaymentModeAccountTransfer: 1,
}

var chargePaymentModeName = map[ChargePaymentMode]string{
	ChargePaymentModeRegular:         "REGULAR",
	ChargePaymentModeAccountTransfer: "ACCOUNT_TRANSFER",
}

var chargePaymentModeFromStored = map[int32]ChargePaymentMode{}

// StoredValue returns m_charge.charge_payment_mode_enum.
func (p ChargePaymentMode) StoredValue() int32 {
	v, ok := chargePaymentModeStoredValue[p]
	if !ok {
		panic(fmt.Sprintf("charges: unknown ChargePaymentMode %d", int32(p)))
	}
	return v
}

func (p ChargePaymentMode) String() string {
	if n, ok := chargePaymentModeName[p]; ok {
		return n
	}
	return fmt.Sprintf("ChargePaymentMode(%d)", int32(p))
}

// ChargePaymentModeFromStoredValue decodes m_charge.charge_payment_mode_enum.
// The oracle exposes no fromInt and no INVALID for this enum; only 0 and 1 are
// legal stored values.
func ChargePaymentModeFromStoredValue(v int32) (ChargePaymentMode, bool) {
	p, ok := chargePaymentModeFromStored[v]
	return p, ok
}

// IsPaymentModeAccountTransfer mirrors ChargePaymentMode.java:31-33.
func (p ChargePaymentMode) IsPaymentModeAccountTransfer() bool {
	return p == ChargePaymentModeAccountTransfer
}

func init() {
	for p, v := range chargePaymentModeStoredValue {
		if _, dup := chargePaymentModeFromStored[v]; dup {
			panic(fmt.Sprintf("charges: charge payment-mode encode table is not injective at %d", v))
		}
		chargePaymentModeFromStored[v] = p
	}
}
