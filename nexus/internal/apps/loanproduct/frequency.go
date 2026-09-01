package loanproduct

import "fmt"

// PeriodFrequencyType is Fineract's PeriodFrequencyType.
// [VERIFIED: PeriodFrequencyType.java:27-32 — DAYS(0), WEEKS(1), MONTHS(2),
// YEARS(3), WHOLE_TERM(4), INVALID(5)]
//
// It has two distinct consumers: interestPeriodFrequencyType (the period the
// nominal rate is quoted against) and repaymentPeriodFrequencyType (the period
// repayments repeat against), both carried on LoanProductRelatedDetail. The
// oracle stores the raw integer in the loan product and decodes it through
// fromInt [VERIFIED: PeriodFrequencyType.java:51-70], which is exactly the
// encoding preserved here.
// The Go ordinal order below is NOT the stored-value order. The zero value is
// PeriodInvalid so that a default-constructed LoanProductRelatedDetail behaves
// like the oracle's null frequency: getInterestPeriodFrequencyType returns
// INVALID. The stored-value table separately maps DAYS->0, WEEKS->1, ... so
// the on-disk encoding is untouched.
type PeriodFrequencyType int32

const (
	PeriodInvalid PeriodFrequencyType = iota
	PeriodDays
	PeriodWeeks
	PeriodMonths
	PeriodYears
	PeriodWholeTerm
)

var periodFrequencyStoredValue = map[PeriodFrequencyType]int32{
	PeriodDays:      0,
	PeriodWeeks:     1,
	PeriodMonths:    2,
	PeriodYears:     3,
	PeriodWholeTerm: 4,
	PeriodInvalid:   5,
}

var periodFrequencyCode = map[PeriodFrequencyType]string{
	PeriodDays:      "periodFrequencyType.days",
	PeriodWeeks:     "periodFrequencyType.weeks",
	PeriodMonths:    "periodFrequencyType.months",
	PeriodYears:     "periodFrequencyType.years",
	PeriodWholeTerm: "periodFrequencyType.whole_term",
	PeriodInvalid:   "periodFrequencyType.invalid",
}

var periodFrequencyName = map[PeriodFrequencyType]string{
	PeriodDays:      "DAYS",
	PeriodWeeks:     "WEEKS",
	PeriodMonths:    "MONTHS",
	PeriodYears:     "YEARS",
	PeriodWholeTerm: "WHOLE_TERM",
	PeriodInvalid:   "INVALID",
}

var periodFrequencyFromStored = map[int32]PeriodFrequencyType{}

// StoredValue returns the raw integer the loan product column persists.
func (p PeriodFrequencyType) StoredValue() int32 {
	v, ok := periodFrequencyStoredValue[p]
	if !ok {
		panic(fmt.Sprintf("loanproduct: unknown PeriodFrequencyType %d", int32(p)))
	}
	return v
}

// Code returns the i18n code emitted on the product read.
func (p PeriodFrequencyType) Code() string { return periodFrequencyCode[p] }

func (p PeriodFrequencyType) String() string {
	if n, ok := periodFrequencyName[p]; ok {
		return n
	}
	return fmt.Sprintf("PeriodFrequencyType(%d)", int32(p))
}

// PeriodFrequencyTypeFromStoredValue decodes a raw period-frequency integer.
// ok is false outside 0..4, matching fromInt's INVALID fallback
// [VERIFIED: PeriodFrequencyType.java:51-70].
func PeriodFrequencyTypeFromStoredValue(v int32) (PeriodFrequencyType, bool) {
	p, ok := periodFrequencyFromStored[v]
	return p, ok
}

// IsMonthly / IsYearly / IsWeekly / IsDaily mirror PeriodFrequencyType's
// isMonthly/isYearly/isWeekly/isDaily [VERIFIED: PeriodFrequencyType.java:73-90].
func (p PeriodFrequencyType) IsMonthly() bool { return p == PeriodMonths }
func (p PeriodFrequencyType) IsYearly() bool  { return p == PeriodYears }
func (p PeriodFrequencyType) IsWeekly() bool  { return p == PeriodWeeks }
func (p PeriodFrequencyType) IsDaily() bool   { return p == PeriodDays }

// DaysInYearType is m_product_loan.days_in_year_enum — Fineract's DaysInYearType.
// [VERIFIED: DaysInYearType.java:25-29 — INVALID(0), ACTUAL(1), DAYS_360(360),
// DAYS_364(364), DAYS_365(365)]
//
// See the package doc for the TRAP: the stored value is the day count, not the
// ordinal. getValue() returns the literal day count and fromInt decodes it
// literally [VERIFIED: DaysInYearType.java:36-48], so ACTUAL has no singular
// stored value (it means "length of the reference year") while the fixed
// conventions store their day count verbatim.
type DaysInYearType int32

const (
	DaysInYearInvalid DaysInYearType = iota
	DaysInYearActual
	DaysInYear360
	DaysInYear364
	DaysInYear365
)

var daysInYearStoredValue = map[DaysInYearType]int32{
	DaysInYearInvalid: 0,
	DaysInYearActual:  1,
	DaysInYear360:     360,
	DaysInYear364:     364,
	DaysInYear365:     365,
}

var daysInYearCode = map[DaysInYearType]string{
	DaysInYearInvalid: "DaysInYearType.invalid",
	DaysInYearActual:  "DaysInYearType.actual",
	DaysInYear360:     "DaysInYearType.days360",
	DaysInYear364:     "DaysInYearType.days364",
	DaysInYear365:     "DaysInYearType.days365",
}

var daysInYearName = map[DaysInYearType]string{
	DaysInYearInvalid: "INVALID",
	DaysInYearActual:  "ACTUAL",
	DaysInYear360:     "DAYS_360",
	DaysInYear364:     "DAYS_364",
	DaysInYear365:     "DAYS_365",
}

var daysInYearFromStored = map[int32]DaysInYearType{}

// StoredValue returns the literal day count (or 0/1 for the two sentinel
// members), NOT the ordinal.
func (d DaysInYearType) StoredValue() int32 {
	v, ok := daysInYearStoredValue[d]
	if !ok {
		panic(fmt.Sprintf("loanproduct: unknown DaysInYearType %d", int32(d)))
	}
	return v
}

// Code returns the i18n code emitted on the product read.
func (d DaysInYearType) Code() string { return daysInYearCode[d] }

func (d DaysInYearType) String() string {
	if n, ok := daysInYearName[d]; ok {
		return n
	}
	return fmt.Sprintf("DaysInYearType(%d)", int32(d))
}

// DaysInYearTypeFromStoredValue decodes the literal day-count stored value.
// ok is false for anything that is not 0, 1, 360, 364 or 365, matching
// fromInt's INVALID fallback [VERIFIED: DaysInYearType.java:49-60].
func DaysInYearTypeFromStoredValue(v int32) (DaysInYearType, bool) {
	d, ok := daysInYearFromStored[v]
	return d, ok
}

// IsActual mirrors DaysInYearType.isActual [VERIFIED: DaysInYearType.java:62-64].
func (d DaysInYearType) IsActual() bool { return d == DaysInYearActual }

// DaysInMonthType is m_product_loan.days_in_month_enum — Fineract's DaysInMonthType.
// [VERIFIED: DaysInMonthType.java:24-26 — INVALID(0), ACTUAL(1), DAYS_30(30)]
//
// Same non-ordinal stored-value trap as DaysInYearType (see package doc).
type DaysInMonthType int32

const (
	DaysInMonthInvalid DaysInMonthType = iota
	DaysInMonthActual
	DaysInMonth30
)

var daysInMonthStoredValue = map[DaysInMonthType]int32{
	DaysInMonthInvalid: 0,
	DaysInMonthActual:  1,
	DaysInMonth30:      30,
}

var daysInMonthCode = map[DaysInMonthType]string{
	DaysInMonthInvalid: "DaysInMonthType.invalid",
	DaysInMonthActual:  "DaysInMonthType.actual",
	DaysInMonth30:      "DaysInMonthType.days360",
}

var daysInMonthName = map[DaysInMonthType]string{
	DaysInMonthInvalid: "INVALID",
	DaysInMonthActual:  "ACTUAL",
	DaysInMonth30:      "DAYS_30",
}

var daysInMonthFromStored = map[int32]DaysInMonthType{}

// StoredValue returns the literal day count (or 0/1 for the sentinels), NOT
// the ordinal.
func (d DaysInMonthType) StoredValue() int32 {
	v, ok := daysInMonthStoredValue[d]
	if !ok {
		panic(fmt.Sprintf("loanproduct: unknown DaysInMonthType %d", int32(d)))
	}
	return v
}

// Code returns the i18n code emitted on the product read.
func (d DaysInMonthType) Code() string { return daysInMonthCode[d] }

func (d DaysInMonthType) String() string {
	if n, ok := daysInMonthName[d]; ok {
		return n
	}
	return fmt.Sprintf("DaysInMonthType(%d)", int32(d))
}

// DaysInMonthTypeFromStoredValue decodes the literal day-count stored value.
// ok is false for anything that is not 0, 1 or 30, matching fromInt's INVALID
// fallback [VERIFIED: DaysInMonthType.java:49-60].
func DaysInMonthTypeFromStoredValue(v int32) (DaysInMonthType, bool) {
	d, ok := daysInMonthFromStored[v]
	return d, ok
}

// IsDaysInMonth30 mirrors DaysInMonthType.isDaysInMonth_30
// [VERIFIED: DaysInMonthType.java:62-64].
func (d DaysInMonthType) IsDaysInMonth30() bool { return d == DaysInMonth30 }

func init() {
	for p, v := range periodFrequencyStoredValue {
		if _, dup := periodFrequencyFromStored[v]; dup {
			panic(fmt.Sprintf("loanproduct: period frequency encode table is not injective at %d", v))
		}
		periodFrequencyFromStored[v] = p
	}
	for d, v := range daysInYearStoredValue {
		if _, dup := daysInYearFromStored[v]; dup {
			panic(fmt.Sprintf("loanproduct: days-in-year encode table is not injective at %d", v))
		}
		daysInYearFromStored[v] = d
	}
	for d, v := range daysInMonthStoredValue {
		if _, dup := daysInMonthFromStored[v]; dup {
			panic(fmt.Sprintf("loanproduct: days-in-month encode table is not injective at %d", v))
		}
		daysInMonthFromStored[v] = d
	}
}
