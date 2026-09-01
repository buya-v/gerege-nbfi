package loan

import "fmt"

// FutureInstallmentAllocationRule selects which future instalment(s) receive an
// in-advance payment when a repayment exceeds the amounts currently due. It is
// the Go port of Fineract's FutureInstallmentAllocationRule
// [VERIFIED: FutureInstallmentAllocationRule.java:24-29 — NEXT_INSTALLMENT(0),
// LAST_INSTALLMENT(1), NEXT_LAST_INSTALLMENT(2), REAMORTIZATION(3)].
//
// The arithmetic slice only needs the rule's identity: which concrete
// instalment a future rule points at is schedule machinery owned by the
// repayment processors, not by the bucket allocation itself. As with the other
// allocation enums, the oracle persists the enum name rather than an integer.
type FutureInstallmentAllocationRule int32

const (
	FutureNextInstallment FutureInstallmentAllocationRule = iota
	FutureLastInstallment
	FutureNextLastInstallment
	FutureReamortization
)

var futureInstallmentRuleName = map[FutureInstallmentAllocationRule]string{
	FutureNextInstallment:     "NEXT_INSTALLMENT",
	FutureLastInstallment:     "LAST_INSTALLMENT",
	FutureNextLastInstallment: "NEXT_LAST_INSTALLMENT",
	FutureReamortization:      "REAMORTIZATION",
}

var futureInstallmentRuleHuman = map[FutureInstallmentAllocationRule]string{
	FutureNextInstallment:     "Next installment",
	FutureLastInstallment:     "Last installment",
	FutureNextLastInstallment: "Next installment or last installment",
	FutureReamortization:      "Reamortization",
}

// String returns the Java enum constant name.
func (f FutureInstallmentAllocationRule) String() string {
	if n, ok := futureInstallmentRuleName[f]; ok {
		return n
	}
	return fmt.Sprintf("FutureInstallmentAllocationRule(%d)", int32(f))
}

// HumanReadableName returns getHumanReadableName
// [VERIFIED: FutureInstallmentAllocationRule.java:24-29].
func (f FutureInstallmentAllocationRule) HumanReadableName() string {
	return futureInstallmentRuleHuman[f]
}
