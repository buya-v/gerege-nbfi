package loan

import "github.com/gerege/nexus/internal/apps/charges"

// LoanCharge is the account-level charge: the Go port of Fineract's LoanCharge
// aggregate reduced to its money-derivation arithmetic. It owns the charge
// amount and the three derived balances the oracle persists beside it (paid,
// waived, written off) plus the outstanding amount and the paid/waived flags
// [VERIFIED: LoanCharge.java:94-129 — amount, amountPaid, amountWaived,
// amountWrittenOff, amountOutstanding, paid, waived].
//
// # G-12 derive-don't-store
//
// amountOutstanding is kept as an explicit field because the oracle treats it
// as the authority in mutation paths — markAsFullyPaid writes it to zero
// independently of the balance invariant, and waive moves it whole into
// amountWaived. Keeping the field makes those transitions faithful; the
// invariant amountOutstanding == CalculateOutstanding() holds after every
// normal operation and is asserted by the tests.
//
// The instalment-fee sub-charge machinery (LoanInstallmentCharge) is out of
// scope for this slice: an instalment-fee charge delegates its paid/waived
// arithmetic to one LoanInstallmentCharge per instalment, and that aggregate is
// owned by the schedule model. The non-instalment paths below are the complete,
// self-contained arithmetic.
type LoanCharge struct {
	// Amount is the charge amount (amount), the flat total of this charge.
	Amount MinorUnits
	// AmountPaid is amountPaid: the cumulative amount paid against this charge.
	AmountPaid MinorUnits
	// AmountWaived is amountWaived: the cumulative amount waived.
	AmountWaived MinorUnits
	// AmountWrittenOff is amountWrittenOff: the cumulative amount written off.
	AmountWrittenOff MinorUnits
	// AmountOutstanding is amountOutstanding: how much remains to be paid,
	// waived or written off on this charge. It is the authority for the
	// payment/waiver mutation paths.
	AmountOutstanding MinorUnits
	// Penalty is is_penalty: true for penalties, false for fees.
	Penalty bool
	// Paid is is_paid_derived: the charge is fully paid.
	Paid bool
	// Waived is waived: the charge is fully waived.
	Waived bool
	// Active is is_active: only active charges participate in disbursement and
	// collection arithmetic [VERIFIED: Loan.java:1259-1263 getActiveCharges].
	Active bool
	// ChargeTime is the effective charge time (charge_time_enum). It is the same
	// value the oracle reads through charge.getCharge().getChargeTimeType() when
	// deciding disbursement/instalment-fee membership.
	ChargeTime charges.ChargeTimeType
	// ChargePaymentMode is charge_payment_mode_enum, used to exclude
	// account-transfer charges from the repayment-at-disbursement collection.
	ChargePaymentMode charges.ChargePaymentMode
}

// CalculateOutstanding ports LoanCharge.calculateOutstanding
// [VERIFIED: LoanCharge.java:298-309]: amount minus the total accounted for
// (paid + waived + written off). This is the balance invariant recompute,
// distinct from the authoritative AmountOutstanding field.
func (c LoanCharge) CalculateOutstanding() MinorUnits {
	return c.Amount - c.AmountPaid - c.AmountWaived - c.AmountWrittenOff
}

// calculateAmountOutstanding ports LoanCharge.calculateAmountOutstanding
// [VERIFIED: LoanCharge.java:286-288]: amount minus waived minus paid. It
// deliberately does NOT subtract written off, matching the oracle's reset paths.
func (c LoanCharge) calculateAmountOutstanding() MinorUnits {
	return c.Amount - c.AmountWaived - c.AmountPaid
}

// IsFullyPaid ports LoanCharge.isFullyPaid [VERIFIED: LoanCharge.java:161-163],
// which returns the paid flag.
func (c LoanCharge) IsFullyPaid() bool { return c.Paid }

// IsPaid ports LoanCharge.isPaid [VERIFIED: LoanCharge.java:392-394], an alias
// for the paid flag.
func (c LoanCharge) IsPaid() bool { return c.Paid }

// IsNotFullyPaid ports LoanCharge.isNotFullyPaid [VERIFIED:
// LoanCharge.java:386-388].
func (c LoanCharge) IsNotFullyPaid() bool { return !c.Paid }

// IsWaived ports LoanCharge.isWaived [VERIFIED: LoanCharge.java:395-397].
func (c LoanCharge) IsWaived() bool { return c.Waived }

// IsChargePending ports LoanCharge.isChargePending [VERIFIED:
// LoanCharge.java:390-392]: not fully paid and not waived.
func (c LoanCharge) IsChargePending() bool { return !c.Paid && !c.Waived }

// IsFeeCharge ports LoanCharge.isFeeCharge [VERIFIED: LoanCharge.java:380-382].
func (c LoanCharge) IsFeeCharge() bool { return !c.Penalty }

// IsPenaltyCharge ports LoanCharge.isPenaltyCharge [VERIFIED:
// LoanCharge.java:384-386].
func (c LoanCharge) IsPenaltyCharge() bool { return c.Penalty }

// IsDueAtDisbursement ports LoanCharge.isDueAtDisbursement [VERIFIED:
// LoanCharge.java:270-274]: charge time is DISBURSEMENT or
// TRANCHE_DISBURSEMENT.
func (c LoanCharge) IsDueAtDisbursement() bool {
	return c.ChargeTime.IsTimeOfDisbursement() || c.ChargeTime.IsTrancheDisbursement()
}

// IsInstalmentFee ports LoanCharge.isInstalmentFee [VERIFIED:
// LoanCharge.java:278-280].
func (c LoanCharge) IsInstalmentFee() bool { return c.ChargeTime.IsInstalmentFee() }

// IsPaidOrPartiallyPaid ports LoanCharge.isPaidOrPartiallyPaid [VERIFIED:
// LoanCharge.java:399-403]: paid + waived + written off is greater than zero.
func (c LoanCharge) IsPaidOrPartiallyPaid() bool {
	return c.AmountPaid+c.AmountWaived+c.AmountWrittenOff > 0
}

// ChargeAmount ports LoanCharge.chargeAmount [VERIFIED: LoanCharge.java:533-545]:
// the total accounted amount, which is the charge's full amount once every
// balance is reconciled.
func (c LoanCharge) ChargeAmount() MinorUnits {
	return c.AmountOutstanding + c.AmountPaid + c.AmountWaived + c.AmountWrittenOff
}

// MarkAsFullyPaid ports LoanCharge.markAsFullyPaid [VERIFIED:
// LoanCharge.java:155-159]: paid = amount, outstanding = 0, paid = true.
func (c *LoanCharge) MarkAsFullyPaid() {
	c.AmountPaid = c.Amount
	c.AmountOutstanding = 0
	c.Paid = true
}

// ReconcileFullyPaid ports LoanCharge.reconcileFullyPaid [VERIFIED:
// LoanCharge.java:161-171]: recompute paid = amount - waived - writtenOff and
// clear outstanding, flagging waived if any amount was waived, else paid.
func (c *LoanCharge) ReconcileFullyPaid() {
	waived := c.AmountWaived
	writtenOff := c.AmountWrittenOff
	c.AmountPaid = c.Amount - waived - writtenOff
	c.AmountOutstanding = 0
	if waived > 0 {
		c.Waived = true
	} else {
		c.Paid = true
	}
}

// ResetToOriginal ports LoanCharge.resetToOriginal [VERIFIED:
// LoanCharge.java:173-182]: clear paid/waived/writtenOff, restore outstanding
// to the full amount, and clear both flags.
func (c *LoanCharge) ResetToOriginal() {
	c.AmountPaid = 0
	c.AmountWaived = 0
	c.AmountWrittenOff = 0
	c.AmountOutstanding = c.calculateAmountOutstanding() // amount - 0 - 0
	c.Paid = false
	c.Waived = false
}

// ResetPaidAmount ports LoanCharge.resetPaidAmount [VERIFIED:
// LoanCharge.java:184-190]: clear only the paid amount, restore outstanding to
// amount minus waived, and clear the paid flag (waived is left untouched).
func (c *LoanCharge) ResetPaidAmount() {
	c.AmountPaid = 0
	c.AmountOutstanding = c.calculateAmountOutstanding()
	c.Paid = false
}

// Waive ports the non-instalment branch of LoanCharge.waive [VERIFIED:
// LoanCharge.java:212-222]: move the entire outstanding into waived and clear
// outstanding. It returns the amount waived.
func (c *LoanCharge) Waive() MinorUnits {
	waived := c.AmountOutstanding
	c.AmountWaived = waived
	c.AmountOutstanding = 0
	c.Paid = false
	c.Waived = true
	return waived
}

// UndoWaive ports the non-instalment branch of LoanCharge.undoWaive [VERIFIED:
// LoanCharge.java:235-244]: restore outstanding from waived and clear waived.
func (c *LoanCharge) UndoWaive() {
	c.AmountOutstanding = c.AmountWaived
	c.AmountWaived = 0
	c.Paid = false
	c.Waived = false
}

// UpdatePaidAmountBy ports the non-instalment branch of
// LoanCharge.updatePaidAmountBy [VERIFIED: LoanCharge.java:423-464]. It applies
// increment to this charge, capping the amount actually paid at the current
// outstanding, and returns the amount paid on this charge.
func (c *LoanCharge) UpdatePaidAmountBy(increment MinorUnits) MinorUnits {
	processAmount := increment
	amountPaidToDate := c.AmountPaid
	amountOutstanding := c.AmountOutstanding

	var amountPaidOnThisCharge MinorUnits
	if processAmount >= amountOutstanding {
		amountPaidOnThisCharge = amountOutstanding
		amountPaidToDate += amountOutstanding
		c.AmountPaid = amountPaidToDate
		c.AmountOutstanding = 0
		if c.AmountWaived > 0 {
			c.Waived = true
		} else {
			c.Paid = true
		}
	} else {
		amountPaidOnThisCharge = processAmount
		amountPaidToDate += processAmount
		c.AmountPaid = amountPaidToDate
		c.AmountOutstanding = c.calculateAmountOutstanding()
	}
	return amountPaidOnThisCharge
}

// UndoPaidOrPartiallyAmountBy ports the non-instalment branch of
// LoanCharge.undoPaidOrPartiallyAmountBy [VERIFIED: LoanCharge.java:641-663]. It
// removes increment from the paid amount, returning the amount actually
// deducted.
func (c *LoanCharge) UndoPaidOrPartiallyAmountBy(increment MinorUnits) MinorUnits {
	processAmount := increment
	amountPaidToDate := c.AmountPaid

	var amountDeducted MinorUnits
	if processAmount >= amountPaidToDate {
		amountDeducted = amountPaidToDate
		amountPaidToDate = 0
		c.AmountPaid = amountPaidToDate
		c.AmountOutstanding = c.Amount // note: full original amount, not the recompute
		c.Paid = false
	} else {
		amountDeducted = processAmount
		amountPaidToDate -= processAmount
		c.AmountPaid = amountPaidToDate
		c.AmountOutstanding = c.calculateAmountOutstanding()
	}
	return amountDeducted
}

// UpdateWaivedAmount ports the non-instalment branch of
// LoanCharge.updateWaivedAmount [VERIFIED: LoanCharge.java:586-603]: clamp an
// over-waived charge to its full amount, flagging waived/paid appropriately.
func (c *LoanCharge) UpdateWaivedAmount() {
	if c.AmountWaived <= 0 {
		return
	}
	if c.AmountWaived > c.Amount {
		c.AmountWaived = c.Amount
		c.AmountOutstanding = 0
		c.Paid = false
		c.Waived = true
	} else if c.AmountWaived < c.Amount {
		c.Paid = false
		c.Waived = false
	}
}
