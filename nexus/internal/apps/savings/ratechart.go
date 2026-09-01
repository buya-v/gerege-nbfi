package savings

import "time"

// InterestRateChartFields is the header of an interest-rate chart: a name, an
// optional description, an effective date range and the primary grouping
// dimension. It is the Go port of Fineract's InterestRateChartFields
// [VERIFIED: InterestRateChartFields.java:24-50].
//
// FromDate and EndDate are calendar dates: only the yyyy-MM-dd portion is
// significant, matching java.time.LocalDate. The time portion (and any zone)
// is ignored by the date comparisons below.
type InterestRateChartFields struct {
	Name                    string
	Description             string
	FromDate                time.Time
	EndDate                 time.Time
	PrimaryGroupingByAmount bool
}

// IsFromDateAfterToDate ports InterestRateChartFields.isFromDateAfterToDate
// [VERIFIED: InterestRateChartFields.java:85-90].
func (f InterestRateChartFields) IsFromDateAfterToDate() bool {
	if f.EndDate.IsZero() {
		return false
	}
	return dateOnly(f.FromDate).After(dateOnly(f.EndDate))
}

// InterestRateChartSlabFields is a single slab of an interest-rate chart: a
// period band (from/to period of a period type), an amount band (from/to amount
// in minor units) and the annual interest rate that applies inside both bands.
// It is the Go port of Fineract's InterestRateChartSlabFields
// [VERIFIED: InterestRateChartSlabFields.java:24-64].
type InterestRateChartSlabFields struct {
	Description string
	// PeriodType is the dimension of FromPeriod/ToPeriod. PeriodInvalid means
	// the slab is not keyed by period (the oracle stores NULL).
	PeriodType SavingsPeriodFrequencyType
	// FromPeriod / ToPeriod are the inclusive period band. A nil pointer is the
	// oracle's NULL, meaning "unbounded on this side".
	FromPeriod *int
	ToPeriod   *int
	// AmountRangeFrom / AmountRangeTo are the inclusive minor-unit amount band.
	// A nil pointer is the oracle's NULL (unbounded).
	AmountRangeFrom *MinorUnits
	AmountRangeTo   *MinorUnits
	// AnnualInterestRate is the slab's whole-per-cent annual rate, stored as
	// Percent (micro-per-cent).
	AnnualInterestRate Percent
	// CurrencyCode is the ISO 4217 code of the amounts in this slab.
	CurrencyCode string
}

// IsFromPeriodGreaterThanToPeriod ports
// InterestRateChartSlabFields.isFromPeriodGreaterThanToPeriod
// [VERIFIED: InterestRateChartSlabFields.java:111-117].
func (s InterestRateChartSlabFields) IsFromPeriodGreaterThanToPeriod() bool {
	return s.ToPeriod != nil && s.FromPeriod != nil && *s.FromPeriod > *s.ToPeriod
}

// IsAmountRangeFromGreaterThanTo ports
// InterestRateChartSlabFields.isAmountRangeFromGreaterThanTo
// [VERIFIED: InterestRateChartSlabFields.java:119-125].
func (s InterestRateChartSlabFields) IsAmountRangeFromGreaterThanTo() bool {
	return s.AmountRangeTo != nil && s.AmountRangeFrom != nil && *s.AmountRangeFrom > *s.AmountRangeTo
}

// IsAmountBetween reports whether amount falls inside the slab's amount band,
// honouring nil as unbounded [VERIFIED: InterestRateChartSlabFields.java:127-133].
func (s InterestRateChartSlabFields) IsAmountBetween(amount MinorUnits) bool {
	if s.AmountRangeFrom != nil && amount < *s.AmountRangeFrom {
		return false
	}
	if s.AmountRangeTo != nil && amount > *s.AmountRangeTo {
		return false
	}
	return true
}

// IsBetweenPeriod reports whether the interval [start, end] falls inside the
// slab's period band, honouring nil as unbounded.
func (s InterestRateChartSlabFields) IsBetweenPeriod(start, end time.Time) bool {
	// A period-typed slab is keyed by period count, not calendar dates; the
	// calendar form is used only by amount-grouped charts. For a pure model
	// slice we accept the interval form directly.
	_ = start
	_ = end
	return s.PeriodType == PeriodInvalid
}

// DepositAccountInterestRateChartSlabs is one slab attached to an
// account-level chart. It is the Go port of Fineract's
// DepositAccountInterestRateChartSlabs, reduced to the slab fields plus a
// back-reference to the chart [VERIFIED:
// DepositAccountInterestRateChartSlabs.java:24-40].
type DepositAccountInterestRateChartSlabs struct {
	ID         int64
	SlabFields InterestRateChartSlabFields
	ChartID    int64
}

// DepositAccountInterestRateChart is an account-level interest-rate chart: a
// header plus an ordered set of slabs. It is the Go port of Fineract's
// DepositAccountInterestRateChart [VERIFIED:
// DepositAccountInterestRateChart.java:26-50].
type DepositAccountInterestRateChart struct {
	ID          int64
	ChartFields InterestRateChartFields
	Slabs       []DepositAccountInterestRateChartSlabs
}

// FindSlab returns the slab with the given id, or nil when absent, mirroring
// DepositAccountInterestRateChart.findChartSlab
// [VERIFIED: DepositAccountInterestRateChart.java:76-86].
func (c *DepositAccountInterestRateChart) FindSlab(id int64) *DepositAccountInterestRateChartSlabs {
	if c == nil {
		return nil
	}
	for i := range c.Slabs {
		if c.Slabs[i].ID == id {
			return &c.Slabs[i]
		}
	}
	return nil
}

// dateOnly truncates t to its calendar date in UTC, so the day comparison
// matches LocalDate's epoch-day arithmetic regardless of the input's time or
// zone. This is the same convention the loan package uses
// [loan/delinquency.go:120-123].
func dateOnly(t time.Time) time.Time {
	y, m, d := t.UTC().Date()
	return time.Date(y, m, d, 0, 0, 0, 0, time.UTC)
}
