package loan

import (
	"sort"
	"time"
)

// Delinquency arithmetic ports the two self-contained money computations of
// Fineract's installment-level delinquency: the aggregation of instalment tags
// into per-range delinquent amounts, and the delinquent-days derivation. The
// full overdue-collection loop (chargeback adjustment across instalments,
// grace/pause handling against effective delinquency actions) is a schedule
// and transaction concern that depends on the schedule model, and remains out
// of scope for this slice.

// InstallmentDelinquencyTag is the Go port of
// LoanInstallmentDelinquencyTagData [VERIFIED:
// LoanInstallmentDelinquencyTagData.java:18-36]: one instalment's membership in
// a delinquency range and its outstanding amount.
type InstallmentDelinquencyTag struct {
	RangeID           int64
	Classification    string
	MinimumAgeDays    *int // nil mirrors the oracle's nullable Integer
	MaximumAgeDays    *int
	OutstandingAmount MinorUnits
}

// InstallmentLevelDelinquency is the Go port of InstallmentLevelDelinquency
// [VERIFIED: InstallmentLevelDelinquency.java:23-45]: a delinquency range with
// the delinquent amount aggregated across the instalments tagged into it.
type InstallmentLevelDelinquency struct {
	RangeID          int64
	Classification   string
	MinimumAgeDays   *int
	MaximumAgeDays   *int
	DelinquentAmount MinorUnits
}

// AggregateInstallmentDelinquency ports
// InstallmentDelinquencyAggregator.aggregateAndSort [VERIFIED:
// InstallmentDelinquencyAggregator.java:42-53]. It groups instalment tags by
// range, sums the delinquent amount per range (preserving the range metadata),
// and returns the ranges sorted by minimumAgeDays ascending (null treated as
// zero). The oracle's tie order among equal minimumAgeDays is the iteration
// order of a HashMap and therefore non-deterministic; the port breaks ties by
// RangeID ascending to make the result reproducible.
func AggregateInstallmentDelinquency(tags []InstallmentDelinquencyTag) []InstallmentLevelDelinquency {
	if len(tags) == 0 {
		return nil
	}

	byRange := make(map[int64]*InstallmentLevelDelinquency, len(tags))
	var order []int64
	for _, t := range tags {
		agg, ok := byRange[t.RangeID]
		if !ok {
			agg = &InstallmentLevelDelinquency{
				RangeID:        t.RangeID,
				Classification: t.Classification,
				MinimumAgeDays: t.MinimumAgeDays,
				MaximumAgeDays: t.MaximumAgeDays,
			}
			byRange[t.RangeID] = agg
			order = append(order, t.RangeID)
		}
		agg.DelinquentAmount += t.OutstandingAmount
	}

	result := make([]InstallmentLevelDelinquency, 0, len(order))
	for _, id := range order {
		result = append(result, *byRange[id])
	}

	sort.SliceStable(result, func(i, j int) bool {
		mi := minimumAgeOrZero(result[i].MinimumAgeDays)
		mj := minimumAgeOrZero(result[j].MinimumAgeDays)
		if mi != mj {
			return mi < mj
		}
		return result[i].RangeID < result[j].RangeID
	})
	return result
}

func minimumAgeOrZero(v *int) int {
	if v == nil {
		return 0
	}
	return *v
}

// OverdueDays ports the overdue-days derivation [VERIFIED:
// LoanDelinquencyDomainServiceImpl.java:190-194]: the calendar-day difference
// between overdueSinceDate and businessDate, clamped to zero when negative
// (DateUtils.getDifferenceInDays == DAYS.between(first, second)).
func OverdueDays(overdueSinceDate, businessDate time.Time) int64 {
	days := int64(dateOnly(businessDate).Sub(dateOnly(overdueSinceDate)) / (24 * time.Hour))
	if days < 0 {
		return 0
	}
	return days
}

// DelinquentDays ports LoanDelinquencyDomainServiceImpl.calculateAndSetDelinquentDays
// [VERIFIED: LoanDelinquencyDomainServiceImpl.java:324-334]:
//
//	delinquentDays = 0                       when overdueDays <= 0
//	delinquentDays = overdueDays - pausedDays - graceDays, floored at 0, otherwise
func DelinquentDays(overdueDays, pausedDays, graceDays int64) int64 {
	if overdueDays <= 0 {
		return 0
	}
	d := overdueDays - pausedDays - graceDays
	if d < 0 {
		return 0
	}
	return d
}

// dateOnly truncates a time.Time to its calendar date in UTC, so the
// day-count matches LocalDate's epoch-day arithmetic regardless of the input's
// time zone or clock time.
func dateOnly(t time.Time) time.Time {
	y, m, d := t.Date()
	return time.Date(y, m, d, 0, 0, 0, 0, time.UTC)
}
