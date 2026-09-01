package ledger

import (
	"reflect"
	"testing"
)

// TestRunningBalanceColumnsPinned pins the G-12 storage-layer carve-out. The
// list is deliberately exact: a widening (or narrowing) of the derive-only
// exclusion is a source diff that a reviewer must see, not a prose sentence.
func TestRunningBalanceColumnsPinned(t *testing.T) {
	want := []string{
		"office_running_balance",
		"organization_running_balance",
		"is_running_balance_calculated",
	}
	if got := RunningBalanceColumns(); !reflect.DeepEqual(got, want) {
		t.Fatalf("RunningBalanceColumns() = %v, want %v", got, want)
	}
}

// TestPostgresMappingStoreNullShortCircuits proves the two NULL-argument paths
// that return before issuing a query, so they need no Querier and can be graded
// without a database.
func TestPostgresMappingStoreNullShortCircuits(t *testing.T) {
	s := &PostgresMappingStore{NullPaymentTypePolicy: NullPaymentTypeMatchesNothing}

	row, err := s.FindByCharge(1, ProductLoan.StoredValue(), 1, nil)
	if err != nil || row != nil {
		t.Fatalf("FindByCharge(nil charge) = (%v, %v), want (nil, nil)", row, err)
	}

	row, err = s.FindByPaymentType(1, ProductLoan.StoredValue(), 1, nil)
	if err != nil || row != nil {
		t.Fatalf("FindByPaymentType(nil, MatchesNothing) = (%v, %v), want (nil, nil)", row, err)
	}
}
