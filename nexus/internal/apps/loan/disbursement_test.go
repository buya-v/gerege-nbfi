package loan

import (
	"testing"

	"github.com/gerege/nexus/internal/apps/charges"
)

func chargePtr(c LoanCharge) *LoanCharge { return &c }

func TestSumChargesDueAtDisbursement(t *testing.T) {
	charges_ := []*LoanCharge{
		chargePtr(LoanCharge{Amount: 100, Active: true, ChargeTime: charges.ChargeTimeDisbursement}),
		chargePtr(LoanCharge{Amount: 200, Active: true, ChargeTime: charges.ChargeTimeTrancheDisbursement}),
		chargePtr(LoanCharge{Amount: 400, Active: true, ChargeTime: charges.ChargeTimeSpecifiedDueDate}),
		chargePtr(LoanCharge{Amount: 800, Active: false, ChargeTime: charges.ChargeTimeDisbursement}),
		chargePtr(LoanCharge{Amount: 1600, Active: true, ChargeTime: charges.ChargeTimeInstalmentFee}),
	}
	if got := SumChargesDueAtDisbursement(charges_); got != 300 {
		t.Errorf("SumChargesDueAtDisbursement() = %d, want 300", got)
	}
}

func TestNetDisbursalAmount(t *testing.T) {
	if got := NetDisbursalAmount(10_000, 1_500); got != 8_500 {
		t.Errorf("NetDisbursalAmount() = %d, want 8500", got)
	}
	if got := AdjustNetDisbursalAmount(12_000, 1_500); got != 10_500 {
		t.Errorf("AdjustNetDisbursalAmount() = %d, want 10500", got)
	}
	if got := DeductFromNetDisbursalAmount(8_500, 250); got != 8_250 {
		t.Errorf("DeductFromNetDisbursalAmount() = %d, want 8250", got)
	}
}

func TestSettleDisbursementCharges(t *testing.T) {
	onDate := func(LoanCharge) bool { return true }

	t.Run("no fee due at disbursement collects nothing", func(t *testing.T) {
		c := chargePtr(freshCharge(100))
		c.ChargeTime = charges.ChargeTimeDisbursement
		if got := SettleDisbursementCharges([]*LoanCharge{c}, onDate, 0); got != 0 {
			t.Errorf("SettleDisbursementCharges() = %d, want 0", got)
		}
		if c.Paid {
			t.Error("charge should not be marked paid when no fee due at disbursement")
		}
	})

	t.Run("disbursement charges are settled", func(t *testing.T) {
		a := chargePtr(freshCharge(100))
		a.ChargeTime = charges.ChargeTimeDisbursement
		b := chargePtr(freshCharge(200))
		b.ChargeTime = charges.ChargeTimeTrancheDisbursement
		got := SettleDisbursementCharges([]*LoanCharge{a, b}, onDate, 300)
		if got != 300 {
			t.Errorf("SettleDisbursementCharges() = %d, want 300", got)
		}
		if !a.Paid || !b.Paid {
			t.Errorf("charges = %+v / %+v, want both paid", a, b)
		}
	})

	t.Run("account-transfer and non-disbursement charges are skipped", func(t *testing.T) {
		transfer := chargePtr(freshCharge(100))
		transfer.ChargeTime = charges.ChargeTimeDisbursement
		transfer.ChargePaymentMode = charges.ChargePaymentModeAccountTransfer
		specified := chargePtr(freshCharge(200))
		specified.ChargeTime = charges.ChargeTimeSpecifiedDueDate
		disb := chargePtr(freshCharge(400))
		disb.ChargeTime = charges.ChargeTimeDisbursement

		got := SettleDisbursementCharges([]*LoanCharge{transfer, specified, disb}, onDate, 500)
		if got != 400 {
			t.Errorf("SettleDisbursementCharges() = %d, want 400", got)
		}
		if transfer.Paid || specified.Paid {
			t.Error("transfer/specified charge should not be marked paid")
		}
		if !disb.Paid {
			t.Error("disbursement charge should be marked paid")
		}
	})

	t.Run("waived and fully paid charges are skipped", func(t *testing.T) {
		waived := chargePtr(freshCharge(100))
		waived.ChargeTime = charges.ChargeTimeDisbursement
		waived.Waived = true
		paid := chargePtr(freshCharge(200))
		paid.ChargeTime = charges.ChargeTimeDisbursement
		paid.Paid = true
		got := SettleDisbursementCharges([]*LoanCharge{waived, paid}, onDate, 300)
		if got != 0 {
			t.Errorf("SettleDisbursementCharges() = %d, want 0", got)
		}
	})

	t.Run("charges not due on the disbursement date are skipped", func(t *testing.T) {
		disb := chargePtr(freshCharge(100))
		disb.ChargeTime = charges.ChargeTimeDisbursement
		got := SettleDisbursementCharges([]*LoanCharge{disb}, func(LoanCharge) bool { return false }, 100)
		if got != 0 {
			t.Errorf("SettleDisbursementCharges() = %d, want 0", got)
		}
		if disb.Paid {
			t.Error("charge not due on date should not be marked paid")
		}
	})
}
