package savings

import "fmt"

// SavingsPeriodFrequencyType is the period dimension an interest-rate chart slab
// is keyed by — days, weeks, months or years. It is the Go port of Fineract's
// SavingsPeriodFrequencyType.
// [VERIFIED: SavingsPeriodFrequencyType.java:24-31 — DAYS(0), WEEKS(1),
// MONTHS(2), YEARS(3), INVALID(4)].
type SavingsPeriodFrequencyType int32

const (
	PeriodDays SavingsPeriodFrequencyType = iota
	PeriodWeeks
	PeriodMonths
	PeriodYears
	PeriodInvalid
)

var savingsPeriodFrequencyName = map[SavingsPeriodFrequencyType]string{
	PeriodDays:    "DAYS",
	PeriodWeeks:   "WEEKS",
	PeriodMonths:  "MONTHS",
	PeriodYears:   "YEARS",
	PeriodInvalid: "INVALID",
}

func (p SavingsPeriodFrequencyType) StoredValue() int32 { return int32(p) }

func (p SavingsPeriodFrequencyType) String() string {
	if n, ok := savingsPeriodFrequencyName[p]; ok {
		return n
	}
	return fmt.Sprintf("SavingsPeriodFrequencyType(%d)", int32(p))
}

// SavingsPeriodFrequencyTypeFromStoredValue decodes a stored period-type value.
// Unlike the non-contiguous enums in this package the values are a true iota,
// so the decoder is a simple range check [VERIFIED: SavingsPeriodFrequencyType
// .java:39-49].
func SavingsPeriodFrequencyTypeFromStoredValue(v int32) SavingsPeriodFrequencyType {
	if v < 0 || v > 3 {
		return PeriodInvalid
	}
	return SavingsPeriodFrequencyType(v)
}

// SavingsCompoundingInterestPeriodType is the interest compounding cadence.
// [VERIFIED: SavingsCompoundingInterestPeriodType.java:24-35]
//
//	INVALID(0), DAILY(1), MONTHLY(4), QUATERLY(5), BI_ANNUAL(6), ANNUAL(7)
//
// The commented-out WEEKLY(2), BIWEEKLY(3) and NO_COMPOUNDING_SIMPLE_INTEREST(8)
// are intentionally absent: Fineract reserves the ordinals but exposes no such
// value. The stored values are NOT contiguous (there is no 2 or 3), so the
// explicit table below is the contract.
type SavingsCompoundingInterestPeriodType int32

const (
	CompoundingInvalid SavingsCompoundingInterestPeriodType = iota
	CompoundingDaily
	CompoundingMonthly
	CompoundingQuarterly
	CompoundingBiAnnual
	CompoundingAnnual
)

var compoundingStoredValue = map[SavingsCompoundingInterestPeriodType]int32{
	CompoundingInvalid:   0,
	CompoundingDaily:     1,
	CompoundingMonthly:   4,
	CompoundingQuarterly: 5,
	CompoundingBiAnnual:  6,
	CompoundingAnnual:    7,
}

var compoundingName = map[SavingsCompoundingInterestPeriodType]string{
	CompoundingInvalid:   "INVALID",
	CompoundingDaily:     "DAILY",
	CompoundingMonthly:   "MONTHLY",
	CompoundingQuarterly: "QUATERLY",
	CompoundingBiAnnual:  "BI_ANNUAL",
	CompoundingAnnual:    "ANNUAL",
}

var compoundingFromStored = map[int32]SavingsCompoundingInterestPeriodType{}

func (c SavingsCompoundingInterestPeriodType) StoredValue() int32 {
	v, ok := compoundingStoredValue[c]
	if !ok {
		panic(fmt.Sprintf("savings: unknown SavingsCompoundingInterestPeriodType %d", int32(c)))
	}
	return v
}

func (c SavingsCompoundingInterestPeriodType) String() string {
	if n, ok := compoundingName[c]; ok {
		return n
	}
	return fmt.Sprintf("SavingsCompoundingInterestPeriodType(%d)", int32(c))
}

// SavingsCompoundingInterestPeriodTypeFromStoredValue decodes a stored
// compounding value, mirroring SavingsCompoundingInterestPeriodType.fromInt
// [VERIFIED: SavingsCompoundingInterestPeriodType.java:44-70].
func SavingsCompoundingInterestPeriodTypeFromStoredValue(v int32) SavingsCompoundingInterestPeriodType {
	if c, ok := compoundingFromStored[v]; ok {
		return c
	}
	return CompoundingInvalid
}

// SavingsPostingInterestPeriodType is the interest posting cadence.
// [VERIFIED: SavingsPostingInterestPeriodType.java:24-40]
//
//	INVALID(0), DAILY(1), MONTHLY(4), QUATERLY(5), BIANNUAL(6), ANNUAL(7),
//	ANNIVERSARY_MONTHLY(8), ANNIVERSARY_QUARTERLY(9),
//	ANNIVERSARY_BIANNUAL(10), ANNIVERSARY_ANNUAL(11)
//
// The stored values are NOT contiguous (no 2 or 3), so the explicit table
// below is the contract.
type SavingsPostingInterestPeriodType int32

const (
	PostingInvalid SavingsPostingInterestPeriodType = iota
	PostingDaily
	PostingMonthly
	PostingQuarterly
	PostingBiAnnual
	PostingAnnual
	PostingAnniversaryMonthly
	PostingAnniversaryQuarterly
	PostingAnniversaryBiAnnual
	PostingAnniversaryAnnual
)

var postingStoredValue = map[SavingsPostingInterestPeriodType]int32{
	PostingInvalid:              0,
	PostingDaily:                1,
	PostingMonthly:              4,
	PostingQuarterly:            5,
	PostingBiAnnual:             6,
	PostingAnnual:               7,
	PostingAnniversaryMonthly:   8,
	PostingAnniversaryQuarterly: 9,
	PostingAnniversaryBiAnnual:  10,
	PostingAnniversaryAnnual:    11,
}

var postingName = map[SavingsPostingInterestPeriodType]string{
	PostingInvalid:              "INVALID",
	PostingDaily:                "DAILY",
	PostingMonthly:              "MONTHLY",
	PostingQuarterly:            "QUATERLY",
	PostingBiAnnual:             "BIANNUAL",
	PostingAnnual:               "ANNUAL",
	PostingAnniversaryMonthly:   "ANNIVERSARY_MONTHLY",
	PostingAnniversaryQuarterly: "ANNIVERSARY_QUARTERLY",
	PostingAnniversaryBiAnnual:  "ANNIVERSARY_BIANNUAL",
	PostingAnniversaryAnnual:    "ANNIVERSARY_ANNUAL",
}

var postingFromStored = map[int32]SavingsPostingInterestPeriodType{}

func (p SavingsPostingInterestPeriodType) StoredValue() int32 {
	v, ok := postingStoredValue[p]
	if !ok {
		panic(fmt.Sprintf("savings: unknown SavingsPostingInterestPeriodType %d", int32(p)))
	}
	return v
}

func (p SavingsPostingInterestPeriodType) String() string {
	if n, ok := postingName[p]; ok {
		return n
	}
	return fmt.Sprintf("SavingsPostingInterestPeriodType(%d)", int32(p))
}

// SavingsPostingInterestPeriodTypeFromStoredValue decodes a stored posting
// value, mirroring SavingsPostingInterestPeriodType.fromInt
// [VERIFIED: SavingsPostingInterestPeriodType.java:49-80].
func SavingsPostingInterestPeriodTypeFromStoredValue(v int32) SavingsPostingInterestPeriodType {
	if p, ok := postingFromStored[v]; ok {
		return p
	}
	return PostingInvalid
}

// SavingsInterestCalculationType is the interest calculation method.
// [VERIFIED: SavingsInterestCalculationType.java:24-29 — INVALID(0),
// DAILY_BALANCE(1), AVERAGE_DAILY_BALANCE(2)].
type SavingsInterestCalculationType int32

const (
	CalculationInvalid SavingsInterestCalculationType = iota
	CalculationDailyBalance
	CalculationAverageDailyBalance
)

var calculationName = map[SavingsInterestCalculationType]string{
	CalculationInvalid:             "INVALID",
	CalculationDailyBalance:        "DAILY_BALANCE",
	CalculationAverageDailyBalance: "AVERAGE_DAILY_BALANCE",
}

func (c SavingsInterestCalculationType) StoredValue() int32 { return int32(c) }

func (c SavingsInterestCalculationType) String() string {
	if n, ok := calculationName[c]; ok {
		return n
	}
	return fmt.Sprintf("SavingsInterestCalculationType(%d)", int32(c))
}

// SavingsInterestCalculationTypeFromStoredValue mirrors the oracle's fromInt
// [VERIFIED: SavingsInterestCalculationType.java:31-43].
func SavingsInterestCalculationTypeFromStoredValue(v int32) SavingsInterestCalculationType {
	if v < 1 || v > 2 {
		return CalculationInvalid
	}
	return SavingsInterestCalculationType(v)
}

// SavingsInterestCalculationDaysInYearType is the day-count convention the
// interest calculation uses: 360 or 365 days per year.
// [VERIFIED: SavingsInterestCalculationDaysInYearType.java:24-30 — INVALID(0),
// DAYS_360(360), DAYS_365(365)].
type SavingsInterestCalculationDaysInYearType int32

const (
	DaysInYearInvalid SavingsInterestCalculationDaysInYearType = 0
	DaysInYear360     SavingsInterestCalculationDaysInYearType = 360
	DaysInYear365     SavingsInterestCalculationDaysInYearType = 365
)

var daysInYearName = map[SavingsInterestCalculationDaysInYearType]string{
	DaysInYearInvalid: "INVALID",
	DaysInYear360:     "DAYS_360",
	DaysInYear365:     "DAYS_365",
}

func (d SavingsInterestCalculationDaysInYearType) StoredValue() int32 { return int32(d) }

func (d SavingsInterestCalculationDaysInYearType) String() string {
	if n, ok := daysInYearName[d]; ok {
		return n
	}
	return fmt.Sprintf("SavingsInterestCalculationDaysInYearType(%d)", int32(d))
}

// SavingsInterestCalculationDaysInYearTypeFromStoredValue mirrors the oracle's
// fromInt [VERIFIED: SavingsInterestCalculationDaysInYearType.java:32-44].
func SavingsInterestCalculationDaysInYearTypeFromStoredValue(v int32) SavingsInterestCalculationDaysInYearType {
	switch v {
	case 360:
		return DaysInYear360
	case 365:
		return DaysInYear365
	default:
		return DaysInYearInvalid
	}
}

func init() {
	for c, v := range compoundingStoredValue {
		if _, dup := compoundingFromStored[v]; dup {
			panic(fmt.Sprintf("savings: compounding encode table is not injective at %d", v))
		}
		compoundingFromStored[v] = c
	}
	for p, v := range postingStoredValue {
		if _, dup := postingFromStored[v]; dup {
			panic(fmt.Sprintf("savings: posting encode table is not injective at %d", v))
		}
		postingFromStored[v] = p
	}
}
