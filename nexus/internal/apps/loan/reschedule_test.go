package loan

import "testing"

func TestRescheduleRequestStatus(t *testing.T) {
	cases := []struct {
		in       RescheduleRequestStatus
		stored   int32
		name     string
		pending  bool
		approved bool
		rejected bool
	}{
		{RescheduleSubmittedAndPendingApproval, 100, "SUBMITTED_AND_PENDING_APPROVAL", true, false, false},
		{RescheduleApproved, 200, "APPROVED", false, true, false},
		{RescheduleRejected, 500, "REJECTED", false, false, true},
	}
	for _, c := range cases {
		if got := c.in.StoredValue(); got != c.stored {
			t.Errorf("%s StoredValue() = %d, want %d", c.in, got, c.stored)
		}
		if got := c.in.String(); got != c.name {
			t.Errorf("String() = %q, want %q", got, c.name)
		}
		if c.in.IsPendingApproval() != c.pending || c.in.IsApproved() != c.approved || c.in.IsRejected() != c.rejected {
			t.Errorf("%s predicates = %v/%v/%v, want %v/%v/%v",
				c.in, c.in.IsPendingApproval(), c.in.IsApproved(), c.in.IsRejected(), c.pending, c.approved, c.rejected)
		}
	}
}

func TestRescheduleRequestRecalculateInterest(t *testing.T) {
	if got := (RescheduleRequest{}).GetRecalculateInterest(); got {
		t.Errorf("GetRecalculateInterest() = true, want false for nil")
	}
	yes := true
	no := false
	if got := (RescheduleRequest{RecalculateInterest: &yes}).GetRecalculateInterest(); !got {
		t.Error("GetRecalculateInterest() = false, want true")
	}
	if got := (RescheduleRequest{RecalculateInterest: &no}).GetRecalculateInterest(); got {
		t.Error("GetRecalculateInterest() = true, want false")
	}
}

func TestRescheduleRequestApproveReject(t *testing.T) {
	r := RescheduleRequest{Status: RescheduleSubmittedAndPendingApproval}

	r.Approve(false)
	if r.Status != RescheduleSubmittedAndPendingApproval {
		t.Errorf("Approve(false) = %v, want unchanged pending", r.Status)
	}
	r.Approve(true)
	if r.Status != RescheduleApproved {
		t.Errorf("Approve(true) = %v, want approved", r.Status)
	}

	r = RescheduleRequest{Status: RescheduleSubmittedAndPendingApproval}
	r.Reject(false)
	if r.Status != RescheduleSubmittedAndPendingApproval {
		t.Errorf("Reject(false) = %v, want unchanged pending", r.Status)
	}
	r.Reject(true)
	if r.Status != RescheduleRejected {
		t.Errorf("Reject(true) = %v, want rejected", r.Status)
	}
}
