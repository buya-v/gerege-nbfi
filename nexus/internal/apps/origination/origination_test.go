package origination

import (
	"errors"
	"testing"
)

func TestLoanOriginatorStatusFromString(t *testing.T) {
	for _, tc := range []struct {
		in   string
		want LoanOriginatorStatus
		ok   bool
	}{
		{"ACTIVE", OriginatorActive, true},
		{"active", OriginatorActive, true},
		{"PENDING", OriginatorPending, true},
		{"INACTIVE", OriginatorInactive, true},
		{" Active ", 0, false}, // oracle does not trim; equalsIgnoreCase only
		{"UNKNOWN", 0, false},
		{"", 0, false},
	} {
		got, ok := LoanOriginatorStatusFromString(tc.in)
		if ok != tc.ok || (ok && got != tc.want) {
			t.Fatalf("FromString(%q) = (%v, %v), want (%v, %v)", tc.in, got, ok, tc.want, tc.ok)
		}
	}
	if got := OriginatorActive.StoredValue(); got != "ACTIVE" {
		t.Fatalf("ACTIVE StoredValue = %q, want ACTIVE", got)
	}
	if !OriginatorActive.IsActive() || OriginatorPending.IsActive() {
		t.Fatal("only ACTIVE may report IsActive")
	}
}

func TestNewLoanOriginatorDefaultsActive(t *testing.T) {
	o := NewLoanOriginator("ext-1", "Originator A", 1, 2)
	if o.Status != OriginatorActive {
		t.Fatalf("new originator status = %v, want ACTIVE", o.Status)
	}
	if o.OriginatorTypeID != 1 || o.ChannelTypeID != 2 {
		t.Fatalf("code-value IDs not carried: %+v", o)
	}
	o.Update("Originator B", OriginatorInactive, 3, 4)
	if o.Name != "Originator B" || o.Status != OriginatorInactive || o.OriginatorTypeID != 3 || o.ChannelTypeID != 4 {
		t.Fatalf("Update did not replace all fields: %+v", o)
	}
}

func TestValidateAttachRuleChain(t *testing.T) {
	active := LoanOriginator{ID: 7, Status: OriginatorActive}
	inactive := LoanOriginator{ID: 8, Status: OriginatorInactive}

	// Loan not submitted is the first failure.
	err := ValidateAttach(1, false, "ACTIVE", active, false)
	var notSubmitted *ErrLoanNotSubmitted
	if !errors.As(err, &notSubmitted) {
		t.Fatalf("ValidateAttach not-submitted = %v, want ErrLoanNotSubmitted", err)
	}

	// Non-active originator is the second failure.
	err = ValidateAttach(1, true, "SUBMITTED_AND_PENDING_APPROVAL", inactive, false)
	var notActive *ErrOriginatorNotActive
	if !errors.As(err, &notActive) {
		t.Fatalf("ValidateAttach not-active = %v, want ErrOriginatorNotActive", err)
	}

	// Existing mapping is the third failure.
	err = ValidateAttach(1, true, "SUBMITTED_AND_PENDING_APPROVAL", active, true)
	var already *ErrMappingAlreadyExists
	if !errors.As(err, &already) {
		t.Fatalf("ValidateAttach already-exists = %v, want ErrMappingAlreadyExists", err)
	}

	// Happy path.
	if err := ValidateAttach(1, true, "SUBMITTED_AND_PENDING_APPROVAL", active, false); err != nil {
		t.Fatalf("ValidateAttach happy path = %v, want nil", err)
	}
}

func TestValidateDetachAndDelete(t *testing.T) {
	if err := ValidateDetach(false, 1, "ACTIVE"); err == nil {
		t.Fatal("ValidateDetach on a non-submitted loan must fail")
	}
	if err := ValidateDetach(true, 1, "SUBMITTED_AND_PENDING_APPROVAL"); err != nil {
		t.Fatalf("ValidateDetach happy path = %v, want nil", err)
	}
	if err := ValidateDelete(5, true); err == nil {
		t.Fatal("ValidateDelete with mappings must fail")
	}
	if err := ValidateDelete(5, false); err != nil {
		t.Fatalf("ValidateDelete without mappings = %v, want nil", err)
	}
}

func TestReconcileMappings(t *testing.T) {
	toAdd, toRemove := ReconcileMappings([]int64{1, 2, 3}, []int64{2, 3, 4})
	if len(toAdd) != 1 || toAdd[0] != 4 {
		t.Fatalf("toAdd = %v, want [4]", toAdd)
	}
	if len(toRemove) != 1 || toRemove[0] != 1 {
		t.Fatalf("toRemove = %v, want [1]", toRemove)
	}

	// Empty request removes all; null semantics are a caller concern.
	toAdd, toRemove = ReconcileMappings([]int64{1, 2}, nil)
	if len(toAdd) != 0 {
		t.Fatalf("toAdd = %v, want empty", toAdd)
	}
	if len(toRemove) != 2 {
		t.Fatalf("toRemove = %v, want [1 2]", toRemove)
	}
}
