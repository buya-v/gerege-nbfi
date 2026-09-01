package loan

// Write-off arithmetic ports the write-off allocation of the repayment
// schedule transaction processors: how a write-off transaction is broken down
// across the principal, interest, fee and penalty buckets.

// WriteOffInstallment is the subset of a repayment-schedule instalment the
// write-off arithmetic reads. The four outstanding buckets are the oracle's
// getPrincipalOutstanding/getInterestOutstanding/getFeeChargesOutstanding/
// getPenaltyChargesOutstanding, each of which is charged minus (paid + waived +
// written off) for its component [VERIFIED:
// LoanRepaymentScheduleInstallment.java:317,338,364,390]. The port consumes the
// pre-derived outstanding values; deriving them from charged/paid/waived/
// written-off is the schedule model's job.
type WriteOffInstallment struct {
	PrincipalOutstanding MinorUnits
	InterestOutstanding  MinorUnits
	FeeOutstanding       MinorUnits
	PenaltyOutstanding   MinorUnits
	// ObligationsMet is the instalment's obligationsMet flag. An instalment is
	// written off only while it is not fully paid off, i.e. while
	// !obligationsMet [VERIFIED: LoanRepaymentScheduleInstallment.java:513-515
	// isNotFullyPaidOff].
	ObligationsMet bool
}

// WriteOffOutstanding ports AbstractLoanRepaymentScheduleTransactionProcessor.handleWriteOff
// [VERIFIED: AbstractLoanRepaymentScheduleTransactionProcessor.java:764-788]:
// for each instalment that is not fully paid off, add its outstanding
// principal, interest, fee and penalty charges to the four write-off buckets.
//
// The returned Allocation's buckets are the oracle's principalPortion,
// interestPortion, feeChargesPortion and penaltychargesPortion, which the
// processor then writes onto the write-off transaction via
// updateComponentsAndTotal.
func WriteOffOutstanding(installments []WriteOffInstallment) Allocation {
	var a Allocation
	for _, in := range installments {
		if in.ObligationsMet {
			continue
		}
		a.Principal += in.PrincipalOutstanding
		a.Interest += in.InterestOutstanding
		a.Fee += in.FeeOutstanding
		a.Penalty += in.PenaltyOutstanding
	}
	return a
}
