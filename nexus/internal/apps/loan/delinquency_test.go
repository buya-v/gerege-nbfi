package loan

import (
	"testing"
	"time"
)

func intp(v int) *int { return &v }

func TestAggregateInstallmentDelinquency(t *testing.T) {
	t.Run("empty", func(t *testing.T) {
		if got := AggregateInstallmentDelinquency(nil); got != nil {
			t.Errorf("AggregateInstallmentDelinquency(nil) = %v, want nil", got)
		}
	})

	t.Run("groups and sums by range", func(t *testing.T) {
		tags := []InstallmentDelinquencyTag{
			{RangeID: 2, Classification: "Bucket B", MinimumAgeDays: intp(10), OutstandingAmount: 100},
			{RangeID: 1, Classification: "Bucket A", MinimumAgeDays: intp(0), OutstandingAmount: 50},
			{RangeID: 2, Classification: "Bucket B", MinimumAgeDays: intp(10), OutstandingAmount: 25},
		}
		got := AggregateInstallmentDelinquency(tags)
		if len(got) != 2 {
			t.Fatalf("len = %d, want 2", len(got))
		}
		if got[0].RangeID != 1 || got[0].DelinquentAmount != 50 {
			t.Errorf("got[0] = %+v, want range 1 amount 50", got[0])
		}
		if got[1].RangeID != 2 || got[1].DelinquentAmount != 125 {
			t.Errorf("got[1] = %+v, want range 2 amount 125", got[1])
		}
	})

	t.Run("sorts null minimumAgeDays as zero", func(t *testing.T) {
		tags := []InstallmentDelinquencyTag{
			{RangeID: 3, Classification: "No min", MinimumAgeDays: nil, OutstandingAmount: 10},
			{RangeID: 2, Classification: "Min 10", MinimumAgeDays: intp(10), OutstandingAmount: 20},
			{RangeID: 1, Classification: "Min 0", MinimumAgeDays: intp(0), OutstandingAmount: 30},
		}
		got := AggregateInstallmentDelinquency(tags)
		var ids []int64
		for _, g := range got {
			ids = append(ids, g.RangeID)
		}
		// null -> 0 ties with "Min 0"; tie broken by RangeID ascending.
		if ids[0] != 1 || ids[1] != 3 || ids[2] != 2 {
			t.Errorf("order = %v, want [1 3 2]", ids)
		}
	})
}

func TestOverdueDays(t *testing.T) {
	overdueSince := time.Date(2026, 8, 1, 0, 0, 0, 0, time.UTC)
	business := time.Date(2026, 9, 1, 0, 0, 0, 0, time.UTC)
	if got := OverdueDays(overdueSince, business); got != 31 {
		t.Errorf("OverdueDays() = %d, want 31", got)
	}

	// Future overdueSince clamps to zero (the oracle's overdueDays < 0 -> 0).
	if got := OverdueDays(business, overdueSince); got != 0 {
		t.Errorf("OverdueDays(reversed) = %d, want 0", got)
	}
	if got := OverdueDays(business, business); got != 0 {
		t.Errorf("OverdueDays(same) = %d, want 0", got)
	}
}

func TestDelinquentDays(t *testing.T) {
	cases := []struct {
		overdue, paused, grace, want int64
	}{
		{0, 0, 0, 0},
		{-1, 0, 0, 0},
		{10, 0, 0, 10},
		{10, 3, 0, 7},
		{10, 0, 2, 8},
		{10, 3, 2, 5},
		{10, 20, 0, 0},
		{10, 0, 20, 0},
	}
	for _, c := range cases {
		if got := DelinquentDays(c.overdue, c.paused, c.grace); got != c.want {
			t.Errorf("DelinquentDays(%d, %d, %d) = %d, want %d", c.overdue, c.paused, c.grace, got, c.want)
		}
	}
}
