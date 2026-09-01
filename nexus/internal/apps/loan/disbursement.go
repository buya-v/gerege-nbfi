package loan

// Disbursement arithmetic ports the money derivations of the loan
// disbursement flow: the charges due at disbursement, the net disbursal amount,
// and the repayment-at-disbursement charge settlement loop. It is deliberately
// a pure function of the charge list — the schedule, journal-entry and
// validator orchestration around it (LoanDisbursementService) is out of scope.

// SumChargesDueAtDisbursement ports Loan.deriveSumTotalOfChargesDueAtDisbursement
// [VERIFIED: Loan.java:614-619]: the sum of the amount of every active charge
// that is due at disbursement (DISBURSEMENT or TRANCHE_DISBURSEMENT charge
// time).
func SumChargesDueAtDisbursement(charges []*LoanCharge) MinorUnits {
	var total MinorUnits
	for _, c := range charges {
		if c == nil {
			continue
		}
		if c.Active && c.IsDueAtDisbursement() {
			total += c.Amount
		}
	}
	return total
}

// NetDisbursalAmount ports the netDisbursalAmount derivation in Loan's
// constructor [VERIFIED: Loan.java:564]:
// approvedPrincipal - sumTotalOfChargesDueAtDisbursement.
func NetDisbursalAmount(approvedPrincipal, chargesDueAtDisbursement MinorUnits) MinorUnits {
	return approvedPrincipal - chargesDueAtDisbursement
}

// AdjustNetDisbursalAmount ports Loan.adjustNetDisbursalAmount [VERIFIED:
// Loan.java:1710-1711]: adjustedAmount - sumTotalOfChargesDueAtDisbursement.
func AdjustNetDisbursalAmount(adjustedAmount, chargesDueAtDisbursement MinorUnits) MinorUnits {
	return adjustedAmount - chargesDueAtDisbursement
}

// DeductFromNetDisbursalAmount ports Loan.deductFromNetDisbursalAmount
// [VERIFIED: Loan.java:1808-1809]: netDisbursalAmount - subtrahend.
func DeductFromNetDisbursalAmount(netDisbursalAmount, subtrahend MinorUnits) MinorUnits {
	return netDisbursalAmount - subtrahend
}

// SettleDisbursementCharges ports the charge-settlement loop of
// LoanDisbursementService.handleDisbursementTransaction [VERIFIED:
// LoanDisbursementService.java:218-268].
//
// For every active charge that is a disbursement or tranche-disbursement charge
// due on the disbursement date (resolved by the caller via
// dueOnDisbursementDate, standing in for the oracle's
// disbursedOn.equals(actualDisbursementDate)), that is neither waived nor fully
// paid, and that is not paid by account transfer, the charge is marked fully
// paid and its amount is accumulated into the repayment-at-disbursement
// transaction — but only when totalFeeChargesDueAtDisbursement is positive.
//
// The returned value is the oracle's disbursentMoney: the total the
// repayment-at-disbursement transaction collects. The charges are mutated in
// place via MarkAsFullyPaid.
func SettleDisbursementCharges(charges []*LoanCharge, dueOnDisbursementDate func(LoanCharge) bool, totalFeeChargesDueAtDisbursement MinorUnits) MinorUnits {
	if totalFeeChargesDueAtDisbursement <= 0 {
		return 0
	}
	var collected MinorUnits
	for _, c := range charges {
		if c == nil {
			continue
		}
		if !c.Active || c.Waived || c.Paid || !c.IsDueAtDisbursement() {
			continue
		}
		if !dueOnDisbursementDate(*c) {
			continue
		}
		if c.ChargePaymentMode.IsPaymentModeAccountTransfer() {
			continue
		}
		c.MarkAsFullyPaid()
		collected += c.Amount
	}
	return collected
}
