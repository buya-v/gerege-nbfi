package loanproduct

// LoanProductRelatedDetail is the Go port of Fineract's
// LoanProductRelatedDetail value object: the set of related-detail columns that
// are embedded into m_product_loan and carried into every loan account created
// from that product. [VERIFIED: LoanProductRelatedDetail.java:58-175 for the
// field/column names below.]
//
// It is deliberately narrower than the oracle class. The oracle embeds a
// MonetaryCurrency, several supplementary enums (LoanScheduleType,
// LoanScheduleProcessingType, LoanSupportedInterestRefundTypes,
// LoanChargeOffBehaviour, DaysInYearCustomStrategyType) and down-payment
// tuning. Those are scheduling/behaviour concerns whose arithmetic is already
// owned and graded by nexus/internal/apps/loanschedule under DEC-1, so this
// port carries the rate/repayment/amortization core and marks the rest as
// deferred rather than importing a second, ungraded copy of schedule logic.
//
// Money and rate values are stored here with the oracle's column scale:
// principal and the two interest rates are scale-6 decimals in the source
// schema, so their Go representation is the integer minor-unit convention the
// whole port uses — int64 counts of the currency's minor unit. See the note on
// Principal below before changing anything.
type LoanProductRelatedDetail struct {
	// Principal is m_product_loan.principal_amount (numeric(19,6)). It is an
	// integer count of the currency's minor units at scale 6, i.e. a stored
	// "1000.000000" is 1_000_000_000. The schedule generator, not this value
	// object, is the authority on how that count scales into per-period money.
	Principal int64

	// NominalInterestRatePerPeriod is
	// m_product_loan.nominal_interest_rate_per_period (numeric(19,6)): the rate
	// quoted per interestPeriodFrequencyType period. Stored as integer scale-6
	// units (a rate of 1.250000% per period is 1_250_000).
	NominalInterestRatePerPeriod int64

	InterestPeriodFrequencyType PeriodFrequencyType

	// AnnualNominalInterestRate is m_product_loan.annual_nominal_interest_rate
	// (numeric(19,6)). It is DERIVED from NominalInterestRatePerPeriod during
	// product assembly in the oracle; this port keeps it as a carried column
	// and lets loanschedule remain the single source of derivation truth.
	AnnualNominalInterestRate int64

	InterestMethod                 InterestMethod
	InterestCalculationPeriodMethod InterestCalculationPeriodMethod
	AllowPartialPeriodInterestCalc bool

	RepayEvery               int
	RepaymentPeriodFrequencyType PeriodFrequencyType
	NumberOfRepayments       int

	GraceOnPrincipalPayment int
	GraceOnInterestPayment  int

	AmortizationMethod AmortizationMethod

	InArrearsTolerance int64
	GraceOnArrearsAgeing int

	DaysInMonthType DaysInMonthType
	DaysInYearType  DaysInYearType

	InterestRecalculationEnabled bool
	IsEqualAmortization          bool
}

// GetInterestPeriodFrequencyType mirrors the oracle accessor: a null frequency
// decodes as INVALID rather than any concrete period [VERIFIED:
// LoanProductRelatedDetail.java:349-351]. PeriodInvalid is the zero value of
// PeriodFrequencyType in this port, so the accessor is the identity for the
// default case and simply documents the invariant for the non-default case.
func (d LoanProductRelatedDetail) GetInterestPeriodFrequencyType() PeriodFrequencyType {
	return d.InterestPeriodFrequencyType
}

// GetDaysInYearType mirrors getDaysInYearType, which decodes the raw
// m_product_loan.days_in_year_enum column through DaysInYearType.fromInt
// [VERIFIED: LoanProductRelatedDetail.java:369-371]. It is deliberately
// value-based: the column is an int in the oracle, not the enum, and fromInt's
// INVALID fallback is preserved by the (value, ok) decoder.
func (d LoanProductRelatedDetail) GetDaysInYearType() DaysInYearType {
	v, ok := DaysInYearTypeFromStoredValue(d.DaysInYearType.StoredValue())
	if !ok {
		return DaysInYearInvalid
	}
	return v
}

// ResetToInvalid mirrors clearLoanProductRelatedDetails, which blanks the
// interest fields and forces the two frequency axes to INVALID so an updated
// product cannot silently inherit a previous product's rate geometry
// [VERIFIED: LoanProductRelatedDetail.java:374-377].
func (d *LoanProductRelatedDetail) ResetToInvalid() {
	d.NominalInterestRatePerPeriod = 0
	d.InterestPeriodFrequencyType = PeriodInvalid
	d.AnnualNominalInterestRate = 0
}
