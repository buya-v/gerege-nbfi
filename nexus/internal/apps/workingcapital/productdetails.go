package workingcapital

import (
	"fmt"
	"strings"

	"github.com/gerege/nexus/internal/apps/loan"
)

// WorkingCapitalLoanPeriodFrequencyType is the repayment-frequency dimension of
// a working-capital loan product. It is the Go port of Fineract's
// WorkingCapitalLoanPeriodFrequencyType
// [VERIFIED: WorkingCapitalLoanPeriodFrequencyType.java:24-60]:
//
//	DAYS(1), WEEKS(2), MONTHS(3), YEARS(4)
//
// The stored value is the explicit integer value field, not the ordinal, so it
// is a true 1-based iota in practice.
type WorkingCapitalLoanPeriodFrequencyType int32

const (
	WCFrequencyDays WorkingCapitalLoanPeriodFrequencyType = 1 + iota
	WCFrequencyWeeks
	WCFrequencyMonths
	WCFrequencyYears
)

var wcFrequencyName = map[WorkingCapitalLoanPeriodFrequencyType]string{
	WCFrequencyDays:   "DAYS",
	WCFrequencyWeeks:  "WEEKS",
	WCFrequencyMonths: "MONTHS",
	WCFrequencyYears:  "YEARS",
}

// StoredValue returns the integer value field.
func (f WorkingCapitalLoanPeriodFrequencyType) StoredValue() int32 { return int32(f) }

func (f WorkingCapitalLoanPeriodFrequencyType) String() string {
	if n, ok := wcFrequencyName[f]; ok {
		return n
	}
	return fmt.Sprintf("WorkingCapitalLoanPeriodFrequencyType(%d)", int32(f))
}

// WorkingCapitalLoanPeriodFrequencyTypeFromString resolves the enum from its
// case-insensitive name, mirroring fromString
// [VERIFIED: WorkingCapitalLoanPeriodFrequencyType.java:35-52].
func WorkingCapitalLoanPeriodFrequencyTypeFromString(s string) (WorkingCapitalLoanPeriodFrequencyType, bool) {
	for f, n := range wcFrequencyName {
		if strings.EqualFold(strings.TrimSpace(s), n) {
			return f, true
		}
	}
	return 0, false
}

// WorkingCapitalAmortizationType is the amortization method of a working-capital
// loan product [VERIFIED: WorkingCapitalAmortizationType.java:24-48]:
//
//	EIR(1), FLAT(2)
type WorkingCapitalAmortizationType int32

const (
	WCAmortizationEIR WorkingCapitalAmortizationType = 1 + iota
	WCAmortizationFlat
)

var wcAmortizationName = map[WorkingCapitalAmortizationType]string{
	WCAmortizationEIR:  "EIR",
	WCAmortizationFlat: "FLAT",
}

// StoredValue returns the integer value field.
func (a WorkingCapitalAmortizationType) StoredValue() int32 { return int32(a) }

func (a WorkingCapitalAmortizationType) String() string {
	if n, ok := wcAmortizationName[a]; ok {
		return n
	}
	return fmt.Sprintf("WorkingCapitalAmortizationType(%d)", int32(a))
}

// IsEIR reports whether this is the effective-interest-rate method
// [VERIFIED: WorkingCapitalAmortizationType.java:50-52].
func (a WorkingCapitalAmortizationType) IsEIR() bool { return a == WCAmortizationEIR }

// WorkingCapitalAmortizationTypeFromString resolves the enum from its
// case-insensitive name, mirroring fromString
// [VERIFIED: WorkingCapitalAmortizationType.java:37-52].
func WorkingCapitalAmortizationTypeFromString(s string) (WorkingCapitalAmortizationType, bool) {
	for a, n := range wcAmortizationName {
		if strings.EqualFold(strings.TrimSpace(s), n) {
			return a, true
		}
	}
	return 0, false
}

// WorkingCapitalStartType is the "when does the delinquency/breach clock start"
// dimension. Fineract declares it twice — WorkingCapitalLoanDelinquencyStartType
// and WorkingCapitalLoanBreachStartType — with identical values; the port
// collapses them into one type and documents the source of each
// [VERIFIED: WorkingCapitalLoanDelinquencyStartType.java:24-45,
// WorkingCapitalLoanBreachStartType.java:24-45]:
//
//	LOAN_CREATION(1), DISBURSEMENT(2)
type WorkingCapitalStartType int32

const (
	WCStartLoanCreation WorkingCapitalStartType = 1 + iota
	WCStartDisbursement
)

var wcStartName = map[WorkingCapitalStartType]string{
	WCStartLoanCreation: "LOAN_CREATION",
	WCStartDisbursement: "DISBURSEMENT",
}

// StoredValue returns the integer value field.
func (s WorkingCapitalStartType) StoredValue() int32 { return int32(s) }

func (s WorkingCapitalStartType) String() string {
	if n, ok := wcStartName[s]; ok {
		return n
	}
	return fmt.Sprintf("WorkingCapitalStartType(%d)", int32(s))
}

// WorkingCapitalStartTypeFromString resolves the enum from its case-insensitive
// name, mirroring the shared fromString of WorkingCapitalLoanDelinquencyStartType
// and WorkingCapitalLoanBreachStartType
// [VERIFIED: WorkingCapitalLoanDelinquencyStartType.java:37-52,
// WorkingCapitalLoanBreachStartType.java:37-52].
func WorkingCapitalStartTypeFromString(s string) (WorkingCapitalStartType, bool) {
	for st, n := range wcStartName {
		if strings.EqualFold(strings.TrimSpace(s), n) {
			return st, true
		}
	}
	return 0, false
}

// WorkingCapitalLoanProductRelatedDetails is the product facts a working-capital
// loan persists alongside itself. It is the Go port of Fineract's
// WorkingCapitalLoanProductRelatedDetails [VERIFIED:
// WorkingCapitalLoanProductRelatedDetails.java:24-110], reduced to the
// monetary, rate, frequency and start-type fields a repayment write path reads.
// Cross-aggregate references (delinquency bucket, breach, near-breach) are kept
// as IDs.
type WorkingCapitalLoanProductRelatedDetails struct {
	CurrencyCode string // currency.code

	Principal         loan.MinorUnits // principal_amount
	PeriodPaymentRate loan.MinorUnits // period_payment_rate
	RepaymentEvery    int             // repayment_every

	RepaymentFrequencyType WorkingCapitalLoanPeriodFrequencyType
	AmortizationType       WorkingCapitalAmortizationType

	NpvDayCount int // npv_day_count

	Discount         loan.MinorUnits
	DiscountProposed loan.MinorUnits
	DiscountApproved loan.MinorUnits

	DelinquencyBucketID int64 // delinquency_bucket_classification_id
	BreachID            int64 // breach_id
	NearBreachID        int64 // near_breach_id

	DelinquencyGraceDays int                     // delinquency_grace_days
	DelinquencyStartType WorkingCapitalStartType // delinquency_start_type
	BreachGraceDays      int                     // breach_grace_days
	BreachStartType      WorkingCapitalStartType // breach_start_type
}
