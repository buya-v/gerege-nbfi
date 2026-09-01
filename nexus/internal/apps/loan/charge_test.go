package loan

import (
	"testing"

	"github.com/gerege/nexus/internal/apps/charges"
)

// freshCharge builds an unsettled charge with the given amount and no
// paid/waived/written-off balances.
func freshCharge(amount MinorUnits) LoanCharge {
	return LoanCharge{
		Amount:            amount,
		AmountOutstanding: amount,
		Active:            true,
		ChargeTime:        charges.ChargeTimeSpecifiedDueDate,
	}
}

func TestLoanChargeCalculateOutstandingAndChargeAmount(t *testing.T) {
	c := LoanCharge{
		Amount:            1_000,
		AmountPaid:        300,
		AmountWaived:      200,
		AmountWrittenOff:  100,
		AmountOutstanding: 400,
		ChargePaymentMode: charges.ChargePaymentModeRegular,
	}
	if got := c.CalculateOutstanding(); got != 400 {
		t.Errorf("CalculateOutstanding() = %d, want 400", got)
	}
	if got := c.ChargeAmount(); got != 1_000 {
		t.Errorf("ChargeAmount() = %d, want 1000", got)
	}
	if !c.IsPaidOrPartiallyPaid() {
		t.Error("IsPaidOrPartiallyPaid() = false, want true")
	}
}

func TestLoanChargeMarkAsFullyPaid(t *testing.T) {
	c := freshCharge(1_000)
	c.MarkAsFullyPaid()
	if c.AmountPaid != 1_000 || c.AmountOutstanding != 0 || !c.Paid {
		t.Errorf("MarkAsFullyPaid() = %+v, want paid=1000 outstanding=0 paid=true", c)
	}
	if got := c.CalculateOutstanding(); got != 0 {
		t.Errorf("CalculateOutstanding() = %d, want 0", got)
	}
	if got := c.ChargeAmount(); got != 1_000 {
		t.Errorf("ChargeAmount() = %d, want 1000", got)
	}
}

func TestLoanChargeReconcileFullyPaid(t *testing.T) {
	t.Run("with waiver", func(t *testing.T) {
		c := LoanCharge{Amount: 1_000, AmountWaived: 200, AmountWrittenOff: 100}
		c.ReconcileFullyPaid()
		if c.AmountPaid != 700 {
			t.Errorf("AmountPaid = %d, want 700", c.AmountPaid)
		}
		if c.AmountOutstanding != 0 {
			t.Errorf("AmountOutstanding = %d, want 0", c.AmountOutstanding)
		}
		if !c.Waived || c.Paid {
			t.Errorf("Waived/Paid = %v/%v, want true/false", c.Waived, c.Paid)
		}
	})
	t.Run("no waiver", func(t *testing.T) {
		c := LoanCharge{Amount: 1_000, AmountWrittenOff: 100}
		c.ReconcileFullyPaid()
		if c.AmountPaid != 900 {
			t.Errorf("AmountPaid = %d, want 900", c.AmountPaid)
		}
		if c.Waived || !c.Paid {
			t.Errorf("Waived/Paid = %v/%v, want false/true", c.Waived, c.Paid)
		}
	})
}

func TestLoanChargeReset(t *testing.T) {
	t.Run("resetToOriginal", func(t *testing.T) {
		c := LoanCharge{Amount: 1_000, AmountPaid: 300, AmountWaived: 200, AmountWrittenOff: 100, AmountOutstanding: 400}
		c.ResetToOriginal()
		if c.AmountPaid != 0 || c.AmountWaived != 0 || c.AmountWrittenOff != 0 {
			t.Errorf("ResetToOriginal() balances = %+v, want all zero", c)
		}
		if c.AmountOutstanding != 1_000 {
			t.Errorf("AmountOutstanding = %d, want 1000", c.AmountOutstanding)
		}
		if c.Paid || c.Waived {
			t.Errorf("Paid/Waived = %v/%v, want false/false", c.Paid, c.Waived)
		}
	})
	t.Run("resetPaidAmount", func(t *testing.T) {
		c := LoanCharge{Amount: 1_000, AmountPaid: 300, AmountWaived: 200, AmountOutstanding: 500}
		c.ResetPaidAmount()
		if c.AmountPaid != 0 {
			t.Errorf("AmountPaid = %d, want 0", c.AmountPaid)
		}
		if c.AmountOutstanding != 800 {
			t.Errorf("AmountOutstanding = %d, want 800", c.AmountOutstanding)
		}
		if c.Paid {
			t.Error("Paid = true, want false")
		}
		if c.AmountWaived != 200 {
			t.Errorf("AmountWaived = %d, want unchanged 200", c.AmountWaived)
		}
	})
}

func TestLoanChargeWaiveAndUndoWaive(t *testing.T) {
	c := freshCharge(1_000)
	if got := c.Waive(); got != 1_000 {
		t.Errorf("Waive() = %d, want 1000", got)
	}
	if c.AmountWaived != 1_000 || c.AmountOutstanding != 0 || !c.Waived || c.Paid {
		t.Errorf("after Waive() = %+v, want waived=1000 outstanding=0 waived=true paid=false", c)
	}

	c.UndoWaive()
	if c.AmountWaived != 0 || c.AmountOutstanding != 1_000 || c.Waived || c.Paid {
		t.Errorf("after UndoWaive() = %+v, want waived=0 outstanding=1000 waived=false paid=false", c)
	}
}

func TestLoanChargeUpdatePaidAmountBy(t *testing.T) {
	t.Run("partial payment", func(t *testing.T) {
		c := freshCharge(1_000)
		if got := c.UpdatePaidAmountBy(300); got != 300 {
			t.Errorf("UpdatePaidAmountBy(300) = %d, want 300", got)
		}
		if c.AmountPaid != 300 || c.AmountOutstanding != 700 || c.Paid {
			t.Errorf("after partial = %+v, want paid=300 outstanding=700 paid=false", c)
		}
	})
	t.Run("full payment", func(t *testing.T) {
		c := freshCharge(1_000)
		if got := c.UpdatePaidAmountBy(1_000); got != 1_000 {
			t.Errorf("UpdatePaidAmountBy(1000) = %d, want 1000", got)
		}
		if c.AmountPaid != 1_000 || c.AmountOutstanding != 0 || !c.Paid {
			t.Errorf("after full = %+v, want paid=1000 outstanding=0 paid=true", c)
		}
	})
	t.Run("overpayment capped at outstanding", func(t *testing.T) {
		c := freshCharge(1_000)
		if got := c.UpdatePaidAmountBy(1_500); got != 1_000 {
			t.Errorf("UpdatePaidAmountBy(1500) = %d, want 1000", got)
		}
		if c.AmountPaid != 1_000 || c.AmountOutstanding != 0 || !c.Paid {
			t.Errorf("after overpayment = %+v, want paid=1000 outstanding=0 paid=true", c)
		}
	})
	t.Run("full payment with existing waiver flags waived", func(t *testing.T) {
		c := LoanCharge{Amount: 1_000, AmountWaived: 300, AmountOutstanding: 700, ChargeTime: charges.ChargeTimeSpecifiedDueDate}
		if got := c.UpdatePaidAmountBy(700); got != 700 {
			t.Errorf("UpdatePaidAmountBy(700) = %d, want 700", got)
		}
		if c.AmountPaid != 700 || c.AmountOutstanding != 0 || !c.Waived {
			t.Errorf("after full with waiver = %+v, want paid=700 outstanding=0 waived=true", c)
		}
	})
}

func TestLoanChargeUndoPaidOrPartiallyAmountBy(t *testing.T) {
	t.Run("partial undo", func(t *testing.T) {
		c := freshCharge(1_000)
		c.UpdatePaidAmountBy(1_000) // fully paid
		if got := c.UndoPaidOrPartiallyAmountBy(300); got != 300 {
			t.Errorf("UndoPaidOrPartiallyAmountBy(300) = %d, want 300", got)
		}
		if c.AmountPaid != 700 || c.AmountOutstanding != 300 {
			t.Errorf("after partial undo = %+v, want paid=700 outstanding=300", c)
		}
	})
	t.Run("full undo", func(t *testing.T) {
		c := freshCharge(1_000)
		c.UpdatePaidAmountBy(1_000)
		if got := c.UndoPaidOrPartiallyAmountBy(1_000); got != 1_000 {
			t.Errorf("UndoPaidOrPartiallyAmountBy(1000) = %d, want 1000", got)
		}
		if c.AmountPaid != 0 || c.AmountOutstanding != 1_000 || c.Paid {
			t.Errorf("after full undo = %+v, want paid=0 outstanding=1000 paid=false", c)
		}
	})
}

func TestLoanChargeUpdateWaivedAmount(t *testing.T) {
	t.Run("over-waived clamps to amount", func(t *testing.T) {
		c := LoanCharge{Amount: 1_000, AmountWaived: 1_200, AmountOutstanding: 0}
		c.UpdateWaivedAmount()
		if c.AmountWaived != 1_000 || c.AmountOutstanding != 0 || !c.Waived {
			t.Errorf("UpdateWaivedAmount() = %+v, want waived=1000 outstanding=0 waived=true", c)
		}
	})
	t.Run("partial waiver is not flagged waived", func(t *testing.T) {
		c := LoanCharge{Amount: 1_000, AmountWaived: 500, AmountOutstanding: 500}
		c.UpdateWaivedAmount()
		if c.Waived || c.Paid {
			t.Errorf("Paid/Waived = %v/%v, want false/false", c.Paid, c.Waived)
		}
		if c.AmountWaived != 500 {
			t.Errorf("AmountWaived = %d, want unchanged 500", c.AmountWaived)
		}
	})
}

func TestLoanChargePredicates(t *testing.T) {
	fee := LoanCharge{ChargeTime: charges.ChargeTimeSpecifiedDueDate}
	if !fee.IsFeeCharge() || fee.IsPenaltyCharge() {
		t.Error("specified-due-date charge should be fee, not penalty")
	}
	if fee.IsDueAtDisbursement() {
		t.Error("specified-due-date charge should not be due at disbursement")
	}
	if fee.IsInstalmentFee() {
		t.Error("specified-due-date charge should not be instalment fee")
	}

	penalty := LoanCharge{Penalty: true, ChargeTime: charges.ChargeTimeOverdueInstallment}
	if !penalty.IsPenaltyCharge() || penalty.IsFeeCharge() {
		t.Error("overdue-installment charge should be penalty, not fee")
	}

	disb := LoanCharge{ChargeTime: charges.ChargeTimeDisbursement}
	if !disb.IsDueAtDisbursement() {
		t.Error("disbursement charge should be due at disbursement")
	}
	tranche := LoanCharge{ChargeTime: charges.ChargeTimeTrancheDisbursement}
	if !tranche.IsDueAtDisbursement() {
		t.Error("tranche-disbursement charge should be due at disbursement")
	}
	instal := LoanCharge{ChargeTime: charges.ChargeTimeInstalmentFee}
	if !instal.IsInstalmentFee() {
		t.Error("instalment-fee charge should be instalment fee")
	}

	pending := LoanCharge{}
	if !pending.IsChargePending() {
		t.Error("unpaid unwaved charge should be pending")
	}
	pending.Paid = true
	if pending.IsChargePending() {
		t.Error("paid charge should not be pending")
	}
}
