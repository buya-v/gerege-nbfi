package loan

import "fmt"

// PaymentAllocationType couples a DueType with an AllocationType. It is the
// element of a product's payment-allocation order: the product's
// m_loan_product_payment_allocation_rule stores an ordered list of these, and
// that list is exactly what dictates how a repayment is spread across
// penalties, fees, interest and principal
// [VERIFIED: LoanProductPaymentAllocationRule.java:50-62].
//
// Ported from Fineract's PaymentAllocationType, declaration order preserved so
// the ordinal matches the oracle
// [VERIFIED: PaymentAllocationType.java:26-43]:
//
//	PAST_DUE_PENALTY(0)     PAST_DUE_FEE(1)
//	PAST_DUE_PRINCIPAL(2)   PAST_DUE_INTEREST(3)
//	DUE_PENALTY(4)          DUE_FEE(5)
//	DUE_PRINCIPAL(6)        DUE_INTEREST(7)
//	IN_ADVANCE_PENALTY(8)   IN_ADVANCE_FEE(9)
//	IN_ADVANCE_PRINCIPAL(10) IN_ADVANCE_INTEREST(11)
//
// As with AllocationType and DueType, there is no integer stored value: the
// oracle persists the enum name, joined by comma in the list converter
// [VERIFIED: PaymentAllocationTypeListConverter.java:25-33].
type PaymentAllocationType int32

const (
	PaymentPastDuePenalty PaymentAllocationType = iota
	PaymentPastDueFee
	PaymentPastDuePrincipal
	PaymentPastDueInterest
	PaymentDuePenalty
	PaymentDueFee
	PaymentDuePrincipal
	PaymentDueInterest
	PaymentInAdvancePenalty
	PaymentInAdvanceFee
	PaymentInAdvancePrincipal
	PaymentInAdvanceInterest
)

var paymentAllocationTypeName = map[PaymentAllocationType]string{
	PaymentPastDuePenalty:     "PAST_DUE_PENALTY",
	PaymentPastDueFee:         "PAST_DUE_FEE",
	PaymentPastDuePrincipal:   "PAST_DUE_PRINCIPAL",
	PaymentPastDueInterest:    "PAST_DUE_INTEREST",
	PaymentDuePenalty:         "DUE_PENALTY",
	PaymentDueFee:             "DUE_FEE",
	PaymentDuePrincipal:       "DUE_PRINCIPAL",
	PaymentDueInterest:        "DUE_INTEREST",
	PaymentInAdvancePenalty:   "IN_ADVANCE_PENALTY",
	PaymentInAdvanceFee:       "IN_ADVANCE_FEE",
	PaymentInAdvancePrincipal: "IN_ADVANCE_PRINCIPAL",
	PaymentInAdvanceInterest:  "IN_ADVANCE_INTEREST",
}

var paymentAllocationTypeDue = map[PaymentAllocationType]DueType{
	PaymentPastDuePenalty:     DuePastDue,
	PaymentPastDueFee:         DuePastDue,
	PaymentPastDuePrincipal:   DuePastDue,
	PaymentPastDueInterest:    DuePastDue,
	PaymentDuePenalty:         DueDue,
	PaymentDueFee:             DueDue,
	PaymentDuePrincipal:       DueDue,
	PaymentDueInterest:        DueDue,
	PaymentInAdvancePenalty:   DueInAdvance,
	PaymentInAdvanceFee:       DueInAdvance,
	PaymentInAdvancePrincipal: DueInAdvance,
	PaymentInAdvanceInterest:  DueInAdvance,
}

var paymentAllocationTypeAllocation = map[PaymentAllocationType]AllocationType{
	PaymentPastDuePenalty:     AllocationPenalty,
	PaymentPastDueFee:         AllocationFee,
	PaymentPastDuePrincipal:   AllocationPrincipal,
	PaymentPastDueInterest:    AllocationInterest,
	PaymentDuePenalty:         AllocationPenalty,
	PaymentDueFee:             AllocationFee,
	PaymentDuePrincipal:       AllocationPrincipal,
	PaymentDueInterest:        AllocationInterest,
	PaymentInAdvancePenalty:   AllocationPenalty,
	PaymentInAdvanceFee:       AllocationFee,
	PaymentInAdvancePrincipal: AllocationPrincipal,
	PaymentInAdvanceInterest:  AllocationInterest,
}

// String returns the Java enum constant name.
func (p PaymentAllocationType) String() string {
	if n, ok := paymentAllocationTypeName[p]; ok {
		return n
	}
	return fmt.Sprintf("PaymentAllocationType(%d)", int32(p))
}

// DueType returns the DueType this allocation applies to
// [VERIFIED: PaymentAllocationType.java:29-43].
func (p PaymentAllocationType) DueType() DueType { return paymentAllocationTypeDue[p] }

// AllocationType returns the money bucket this allocation fills
// [VERIFIED: PaymentAllocationType.java:29-43].
func (p PaymentAllocationType) AllocationType() AllocationType {
	return paymentAllocationTypeAllocation[p]
}
