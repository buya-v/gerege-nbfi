package workingcapital

import "strings"

// WorkingCapitalLoanPaymentAllocationRule is one row of a working-capital loan's
// payment-allocation order: a transaction type coupled with the ordered list of
// allocation types that a repayment of that type must follow. It is the Go port
// of Fineract's WorkingCapitalLoanPaymentAllocationRule [VERIFIED:
// WorkingCapitalLoanPaymentAllocationRule.java:24-60].
type WorkingCapitalLoanPaymentAllocationRule struct {
	ID     int64
	LoanID int64 // wc_loan_id

	// TransactionType is the persisted PaymentAllocationTransactionType enum
	// name (e.g. "DEFAULT", "REPAYMENT"), stored as an EnumType.STRING. It is
	// kept as a string here rather than a re-declared enum because the source
	// type lives in the loanproduct domain, not the working-capital domain.
	TransactionType string

	// AllocationTypes is the ordered, unique allocation list.
	AllocationTypes []WorkingCapitalPaymentAllocationType
}

// allocationTypeSeparator is the join/split character of the oracle's list
// converter [VERIFIED: GenericEnumListConverter.java:29 — SPLIT_CHAR = ","].
const allocationTypeSeparator = ","

// JoinAllocationTypes mirrors GenericEnumListConverter.convertToDatabaseColumn:
// empty lists become an empty string (the oracle's null), and values are joined
// with the enum name (String), de-duplicated [VERIFIED:
// GenericEnumListConverter.java:43-57, isUnique=true].
func JoinAllocationTypes(types []WorkingCapitalPaymentAllocationType) string {
	if len(types) == 0 {
		return ""
	}
	seen := make(map[WorkingCapitalPaymentAllocationType]bool, len(types))
	parts := make([]string, 0, len(types))
	for _, t := range types {
		if seen[t] {
			continue
		}
		seen[t] = true
		parts = append(parts, t.String())
	}
	return strings.Join(parts, allocationTypeSeparator)
}

// SplitAllocationTypes mirrors GenericEnumListConverter.convertToEntityAttribute:
// a blank string yields an empty list, and each comma-separated token is decoded
// by enum name, de-duplicated in order [VERIFIED:
// GenericEnumListConverter.java:60-69, isUnique=true].
func SplitAllocationTypes(s string) ([]WorkingCapitalPaymentAllocationType, error) {
	s = strings.TrimSpace(s)
	if s == "" {
		return nil, nil
	}
	names := strings.Split(s, allocationTypeSeparator)
	seen := make(map[WorkingCapitalPaymentAllocationType]bool, len(names))
	out := make([]WorkingCapitalPaymentAllocationType, 0, len(names))
	for _, n := range names {
		n = strings.TrimSpace(n)
		t, ok := workingCapitalPaymentAllocationTypeFromName(n)
		if !ok {
			return nil, &unknownAllocationTypeError{name: n}
		}
		if seen[t] {
			continue
		}
		seen[t] = true
		out = append(out, t)
	}
	return out, nil
}

// workingCapitalPaymentAllocationTypeFromName decodes an enum constant name.
func workingCapitalPaymentAllocationTypeFromName(name string) (WorkingCapitalPaymentAllocationType, bool) {
	for t, n := range wcPaymentAllocationName {
		if n == name {
			return t, true
		}
	}
	return 0, false
}

type unknownAllocationTypeError struct{ name string }

func (e *unknownAllocationTypeError) Error() string {
	return "workingcapital: unknown WorkingCapitalPaymentAllocationType " + e.name
}
