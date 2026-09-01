package workingcapital

import (
	"fmt"

	"github.com/gerege/nexus/internal/apps/loan"
)

// WorkingCapitalPaymentAllocationType couples a DueType with an AllocationType
// for the working-capital repayment path. It is the element of a working-capital
// loan's payment-allocation order, stored in m_wc_loan_payment_allocation_rule
// as an ordered, comma-joined list of enum names
// [VERIFIED: WorkingCapitalLoanPaymentAllocationRule.java:24-60,
// WorkingCapitalPaymentAllocationTypeListConverter.java].
//
// It is the working-capital analogue of the loan package's
// PaymentAllocationType, reduced to six values because a working-capital loan
// has no interest and no past-due instalment band. Declaration order is
// preserved so the ordinal matches the oracle
// [VERIFIED: WorkingCapitalPaymentAllocationType.java:24-32]:
//
//	DUE_PENALTY(0)            DUE_FEE(1)
//	DUE_PRINCIPAL(2)
//	IN_ADVANCE_PENALTY(3)     IN_ADVANCE_FEE(4)
//	IN_ADVANCE_PRINCIPAL(5)
//
// As with the loan package's enums there is no integer stored value: the oracle
// persists the enum name, joined by comma in the list converter.
type WorkingCapitalPaymentAllocationType int32

const (
	WCPaymentDuePenalty WorkingCapitalPaymentAllocationType = iota
	WCPaymentDueFee
	WCPaymentDuePrincipal
	WCPaymentInAdvancePenalty
	WCPaymentInAdvanceFee
	WCPaymentInAdvancePrincipal
)

var wcPaymentAllocationName = map[WorkingCapitalPaymentAllocationType]string{
	WCPaymentDuePenalty:         "DUE_PENALTY",
	WCPaymentDueFee:             "DUE_FEE",
	WCPaymentDuePrincipal:       "DUE_PRINCIPAL",
	WCPaymentInAdvancePenalty:   "IN_ADVANCE_PENALTY",
	WCPaymentInAdvanceFee:       "IN_ADVANCE_FEE",
	WCPaymentInAdvancePrincipal: "IN_ADVANCE_PRINCIPAL",
}

var wcPaymentAllocationCode = map[WorkingCapitalPaymentAllocationType]string{
	WCPaymentDuePenalty:         "DUE_PENALTY",
	WCPaymentDueFee:             "DUE_FEE",
	WCPaymentDuePrincipal:       "DUE_PRINCIPAL",
	WCPaymentInAdvancePenalty:   "IN_ADVANCE_PENALTY",
	WCPaymentInAdvanceFee:       "IN_ADVANCE_FEE",
	WCPaymentInAdvancePrincipal: "IN_ADVANCE_PRINCIPAL",
}

var wcPaymentAllocationHuman = map[WorkingCapitalPaymentAllocationType]string{
	WCPaymentDuePenalty:         "Due Penalty",
	WCPaymentDueFee:             "Due Fee",
	WCPaymentDuePrincipal:       "Due Principal",
	WCPaymentInAdvancePenalty:   "In Advance Penalty",
	WCPaymentInAdvanceFee:       "In Advance Fee",
	WCPaymentInAdvancePrincipal: "In Advance Principal",
}

var wcPaymentAllocationDue = map[WorkingCapitalPaymentAllocationType]loan.DueType{
	WCPaymentDuePenalty:         loan.DueDue,
	WCPaymentDueFee:             loan.DueDue,
	WCPaymentDuePrincipal:       loan.DueDue,
	WCPaymentInAdvancePenalty:   loan.DueInAdvance,
	WCPaymentInAdvanceFee:       loan.DueInAdvance,
	WCPaymentInAdvancePrincipal: loan.DueInAdvance,
}

var wcPaymentAllocationAllocation = map[WorkingCapitalPaymentAllocationType]loan.AllocationType{
	WCPaymentDuePenalty:         loan.AllocationPenalty,
	WCPaymentDueFee:             loan.AllocationFee,
	WCPaymentDuePrincipal:       loan.AllocationPrincipal,
	WCPaymentInAdvancePenalty:   loan.AllocationPenalty,
	WCPaymentInAdvanceFee:       loan.AllocationFee,
	WCPaymentInAdvancePrincipal: loan.AllocationPrincipal,
}

// String returns the Java enum constant name, the value the oracle persists.
func (p WorkingCapitalPaymentAllocationType) String() string {
	if n, ok := wcPaymentAllocationName[p]; ok {
		return n
	}
	return fmt.Sprintf("WorkingCapitalPaymentAllocationType(%d)", int32(p))
}

// Code returns the ApiFacingEnum code.
func (p WorkingCapitalPaymentAllocationType) Code() string { return wcPaymentAllocationCode[p] }

// HumanReadableName returns getHumanReadableName.
func (p WorkingCapitalPaymentAllocationType) HumanReadableName() string {
	return wcPaymentAllocationHuman[p]
}

// DueType returns the DueType this allocation applies to.
func (p WorkingCapitalPaymentAllocationType) DueType() loan.DueType {
	return wcPaymentAllocationDue[p]
}

// AllocationType returns the money bucket this allocation fills. It is always
// PENALTY, FEE or PRINCIPAL — never INTEREST.
func (p WorkingCapitalPaymentAllocationType) AllocationType() loan.AllocationType {
	return wcPaymentAllocationAllocation[p]
}
