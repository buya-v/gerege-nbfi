// Package contract defines the frozen adapter contract for the loan-schedule
// bounded context: the single question "generate a repayment schedule", asked
// in a form that either the Fineract JVM reference oracle or the Go native
// module can answer identically.
//
// This package is ratified by ADR DEC-1
// (docs/adr/DEC-1-schedule-generator-adapter.md). It is the strangler boundary
// for the loan-schedule context of the Fineract -> Go migration.
//
// # Amendment gate
//
// DEC-1 and this package are a `user` decision gate. No agent may add, remove,
// rename, retype or re-document any identifier here. A change to this file is a
// change to the frozen contract and requires human ratification, because every
// captured golden vector is expressed in these types and a shape change
// invalidates the conformance corpus.
//
// # Invariants this package enforces by construction
//
//   - All monetary quantities are int64 counts of the currency's minor unit.
//     There is no float32, float64, big.Float, decimal string or float-backed
//     decimal type in this package, and none is implied by any field.
//   - All rates are exact integer rationals. There is no percentage-shaped
//     float and no lossy basis-point truncation.
//   - All dates are civil dates (year/month/day) interpreted in one explicit
//     IANA time zone carried by the request. There is no time.Time, no UTC
//     offset, and no instant anywhere in this package.
//   - The response's period list has a total, derivable order (see Schedule).
//     No map, and therefore no map iteration, appears in the contract or its
//     semantics.
//   - No Fineract type, class, enum name or Java concept (Money, MathContext,
//     BigDecimal, CurrencyData, DaysInMonthType, DaysInYearType,
//     DaysInYearCustomStrategyType, PeriodFrequencyType,
//     LoanRepaymentScheduleModelData, LoanSchedulePlan) crosses this boundary.
//     The one name this package shares with the Java standard library,
//     RoundingMode, is the neutral term for a tie-breaking rule and is a
//     distinct type here with a deliberately narrower value domain.
//   - No party identity of any kind appears. A schedule generator does not need
//     to know who the borrower is. Should a party ever be required, DEC-1
//     mandates three name fields (ovog, patronymic, given name); first_name /
//     last_name are prohibited.
package contract

import (
	"context"
	"errors"
)

// Currency identifies the unit in which every ...Minor field in a request or
// response is denominated, and supplies the scale at which the generator
// rounds a computed amount to a payable amount.
//
// Only the two properties that change the arithmetic are carried. Display name,
// symbol and label are presentation concerns and are deliberately absent.
type Currency struct {
	// Code is the ISO 4217 alpha-3 code, upper case. For Mongolian tugrik this
	// is "MNT" (ISO 4217 numeric 496). It is carried so that an int64 minor-unit
	// amount is never ambiguous and so a captured golden vector is
	// self-describing; it is not itself an input to the arithmetic.
	Code string

	// MinorUnitDigits is the ISO 4217 minor unit exponent: the number of decimal
	// places at which a computed amount becomes a payable amount. MNT is 2, so
	// 1,250,000.00 MNT is the int64 125000000.
	//
	// This is the scale of the contract's currency-rounding layer (see
	// Rounding). Storage is always 2 decimal places for MNT; presentation at 0
	// decimal places with a postfix symbol is a UI concern outside this
	// contract.
	MinorUnitDigits int32
}

// Rate is an exact non-negative rational number, expressed as a dimensionless
// fraction rather than a percentage.
//
// A 7% per annum nominal rate is Rate{Numerator: 7, Denominator: 100}, NOT
// Rate{7, 1}. A 0.125% per annum rate is Rate{1, 800}. A zero rate is
// Rate{0, 1}.
//
// Canonical form is mandatory and is part of the contract, so that two requests
// carrying the same rate are structurally equal and a golden vector has exactly
// one legal encoding:
//
//   - Denominator > 0 always. The Go zero value Rate{} (0/0) is invalid and
//     must be rejected with ErrInvalidRequest.
//   - Numerator >= 0.
//   - The fraction is in lowest terms (gcd(Numerator, Denominator) == 1), so a
//     zero rate is exactly Rate{0, 1}.
//
// Rationals rather than basis points: an integer basis-point field cannot
// express a rate finer than 0.01% (0.125% per annum is 12.5 basis points), and
// a rate is not required to be a whole number of basis points. A rational is
// exact for every rate the reference oracle can consume, and it is closed under
// the divisions the generator performs on it, so no rounding decision is forced
// at the boundary itself; rounding happens only where Rounding says it happens.
type Rate struct {
	Numerator   int64
	Denominator int64
}

// CivilDate is a date on the proleptic Gregorian calendar with no time, no
// offset and no instant. It is interpreted as a calendar day in
// GenerateRequest.TimeZone.
//
// Deliberately not time.Time: a time.Time carries a location and an instant,
// either of which can silently reintroduce a UTC offset or a midnight-boundary
// bug. Mongolia observes no daylight saving time, so a civil day is unambiguous
// once its zone is named.
//
// The Go zero value CivilDate{} is invalid and must be rejected with
// ErrInvalidRequest.
type CivilDate struct {
	Year  int32 // e.g. 2026
	Month int32 // 1..12
	Day   int32 // 1..31, valid for Year and Month
}

// RepaymentFrequencyUnit is the calendar unit in which repayment periods are
// stepped.
type RepaymentFrequencyUnit int32

const (
	// FrequencyUnspecified is the zero value and is never valid in a request.
	FrequencyUnspecified RepaymentFrequencyUnit = iota
	FrequencyDays
	FrequencyWeeks
	FrequencyMonths
	FrequencyYears
)

// DayCountConvention selects the market day-count convention used to convert
// the annual nominal rate into a per-period interest fraction.
//
// This is one field, not a (days-in-month, days-in-year) pair. The pair form
// admits combinations no product uses and no vector covers, and it is the shape
// of the reference implementation rather than the shape of the question. Adding
// a further named convention later widens this enum's value domain without
// changing any struct, which is the cheapest form of contract evolution
// available.
type DayCountConvention int32

const (
	// DayCountUnspecified is the zero value and is never valid in a request.
	DayCountUnspecified DayCountConvention = iota

	// DayCountFixed30Over360 treats every month as exactly 30 days and every
	// year as exactly 360 days. The real calendar length of the month is
	// irrelevant: February and January are treated identically, and a leap year
	// changes nothing.
	//
	// This is the fixed-30 / fixed-360 variant. It is NOT 30E/360 and NOT
	// 30/360 US: no end-of-month day-shifting rule is applied. Real calendar
	// days enter only as a proportional correction when an interest sub-period
	// covers less than a whole repayment period; when the sub-period spans the
	// whole repayment period that correction is exactly 1.
	DayCountFixed30Over360

	// DayCountActualActual uses the real length of each calendar year (365 or
	// 366) and the real number of days elapsed. Where an interest sub-period
	// crosses a calendar-year boundary, the fraction is accumulated per calendar
	// year segment, each over that year's own length.
	DayCountActualActual
)

// InterestMethod selects how interest is derived from the balance.
type InterestMethod int32

const (
	// InterestMethodUnspecified is the zero value and is never valid in a
	// request.
	InterestMethodUnspecified InterestMethod = iota

	// InterestMethodDecliningBalance computes each period's interest from the
	// outstanding principal balance carried into that period.
	//
	// This is the only value currently legal. A request naming any other
	// interest method must be rejected with ErrUnsupportedConfiguration. The
	// field exists so that a response and its golden vector are self-describing
	// about which method produced them, and so that admitting a further method
	// later is a value-domain widening rather than a struct change.
	InterestMethodDecliningBalance
)

// RoundingMode is the tie-breaking rule applied by both rounding layers
// described on Rounding.
//
// The value domain is deliberately narrow. Each admitted mode is a distinct
// tie-breaking behaviour that both implementations must prove identical against
// captured vectors, so a mode is admitted only when a product or a vector
// requires it.
type RoundingMode int32

const (
	// RoundingModeUnspecified is the zero value and is never valid in a request.
	RoundingModeUnspecified RoundingMode = iota

	// RoundingHalfUp rounds to the nearest neighbour; a tie rounds away from
	// zero.
	RoundingHalfUp

	// RoundingHalfEven rounds to the nearest neighbour; a tie rounds towards the
	// even neighbour.
	RoundingHalfEven
)

// Rounding is the precision and rounding policy under which the schedule is
// computed. It is an input to the arithmetic, not a deployment constant,
// because it changes the answer: the same loan computed at 12 significant
// digits and at 19 significant digits can differ by a minor unit, and a golden
// vector is only meaningful if it records the policy it was captured under.
//
// The contract defines two rounding layers and exactly one mode shared by both:
//
//  1. Intermediate layer. Every dimensionless intermediate — the per-period
//     interest fraction, its running product, the recurrence that yields the
//     level installment, and the level installment before it becomes money — is
//     carried as an exact decimal quantity that is rounded to
//     IntermediatePrecisionDigits significant decimal digits under Mode after
//     each multiplication and each division, in the order the reference oracle
//     performs them. Intermediates are ratios, not money: they are never
//     represented as int64 minor units.
//
//  2. Currency layer. A quantity becomes money exactly once, when it is scaled
//     to Currency.MinorUnitDigits decimal places under the same Mode and
//     recorded as an int64 count of minor units. Money is never re-rounded
//     after that point.
//
// Expressing the policy this way replaces the reference oracle's Java
// MathContext without importing it: the pair (significant digits, tie rule) is
// the whole of what MathContext carries, while the ORDER of rounding operations
// is fixed by the schedule algorithm itself and is a conformance obligation
// proven by golden vectors, not a field.
type Rounding struct {
	// IntermediatePrecisionDigits is the number of significant decimal digits
	// retained by the intermediate layer. It must be > 0. The reference oracle's
	// hosted configuration uses 19; its shipped conformance test uses 12.
	IntermediatePrecisionDigits int32

	// Mode is the tie-breaking rule for both layers. One mode, not two: the
	// reference oracle derives its currency-scale tie rule from the same source
	// as its intermediate tie rule, and two independently settable modes would
	// admit combinations no deployment can produce.
	Mode RoundingMode
}

// Disbursement is one advance of principal to the borrower.
type Disbursement struct {
	// Date is the civil date on which the principal is advanced.
	Date CivilDate

	// AmountMinor is the principal advanced, in minor units of
	// GenerateRequest.Currency. It must be > 0.
	AmountMinor int64
}

// GenerateRequest is the complete input to schedule generation. Two
// implementations given an equal GenerateRequest must return an equal Schedule.
//
// Every field changes the numeric output. Anything that a schedule can be
// generated without — the borrower, the loan account, the product catalogue,
// charges, taxes, ledger accounts, business dates, tenants — is absent by
// design.
//
// The Go zero value of GenerateRequest is invalid: every enum has an
// Unspecified zero value, every Rate requires a positive denominator, and every
// CivilDate requires a real date. A request that was never populated therefore
// fails loudly rather than defaulting to some implementation's idea of normal.
type GenerateRequest struct {
	// TimeZone is the IANA zone name in which every CivilDate in this request
	// and in the resulting Schedule is interpreted as a calendar day, and in
	// which the loan's due days are reckoned. Mongolia uses "Asia/Ulaanbaatar"
	// (+08) and "Asia/Hovd" (+07), neither of which observes daylight saving
	// time.
	//
	// It must be an IANA zone name. A fixed offset ("+08:00", "UTC+8", "GMT+8")
	// is invalid and must be rejected with ErrInvalidRequest. The generation
	// arithmetic itself is zone-free civil-date arithmetic; the zone is carried
	// so that no caller can smuggle an implicit offset across the boundary and
	// so that downstream contexts inherit an explicit zone rather than guessing
	// one.
	TimeZone string

	// Currency denominates every ...Minor field in this request and in the
	// resulting Schedule, and supplies the currency rounding layer's scale.
	Currency Currency

	// Rounding is the precision and tie-breaking policy under which the whole
	// schedule is computed. See Rounding.
	Rounding Rounding

	// ScheduleStartDate is the civil date from which repayment period
	// boundaries are stepped. The first repayment period runs from this date;
	// the nth period's due date is this date advanced by n * RepaymentEvery
	// units of RepaymentFrequencyUnit.
	//
	// It is a separate input from a disbursement date because the two can
	// legitimately differ, and because collapsing them would make the boundary
	// unable to express a loan whose repayments start on a date other than the
	// advance.
	//
	// Month-end stepping clamps: advancing 31 January by one month yields
	// 28 February (29 February in a leap year), and advancing that result by a
	// further month yields 28 March, not 31 March. The clamped day is not
	// remembered. Both implementations must reproduce this exactly; it is
	// covered by golden vectors.
	ScheduleStartDate CivilDate

	// Disbursements are the advances of principal, ordered ascending by Date.
	//
	// This is a slice, not a scalar pair, although exactly one element is
	// currently legal: a request carrying zero or more than one element must be
	// rejected with ErrUnsupportedConfiguration. Multi-tranche disbursement is a
	// known, already-implemented behaviour of the reference oracle that arrives
	// with the loan lifecycle, and widening a cardinality is a value-domain
	// change whereas turning a scalar into a list is a shape change that would
	// invalidate every captured vector.
	Disbursements []Disbursement

	// NumberOfRepayments is the count of repayment installments in the loan
	// term. It must be >= 1. A down-payment period, if any, is not counted here.
	NumberOfRepayments int32

	// RepaymentEvery is the step multiplier: a repayment falls due every
	// RepaymentEvery units of RepaymentFrequencyUnit. It must be >= 1. Monthly
	// repayment is RepaymentEvery 1 with FrequencyMonths.
	RepaymentEvery int32

	// RepaymentFrequencyUnit is the calendar unit stepped by RepaymentEvery. It
	// also determines which day-count expansion the interest fraction uses.
	RepaymentFrequencyUnit RepaymentFrequencyUnit

	// AnnualNominalInterestRate is the nominal annual rate as a dimensionless
	// fraction: 24% per annum is Rate{24, 100}. It is nominal, not effective:
	// the conversion to a per-period fraction is performed by DayCount, not by
	// compounding this value.
	//
	// Zero interest is Rate{0, 1} and is a supported, non-special-cased case.
	AnnualNominalInterestRate Rate

	// InterestMethod selects how interest is derived from the balance. See
	// InterestMethod.
	InterestMethod InterestMethod

	// DayCount selects the day-count convention converting
	// AnnualNominalInterestRate into a per-period interest fraction.
	DayCount DayCountConvention

	// DownPaymentPercentage is the fraction of the disbursed principal taken as
	// a down payment on the disbursement date. Rate{0, 1} means no down
	// payment and no down-payment period in the response; Rate{1, 10} means
	// 10%. It must be < 1.
	//
	// A non-zero value adds a PeriodKindDownPayment period to the response and
	// reduces the principal amortized across the repayment periods. It is a
	// single field: a separate enabled/disabled boolean would admit the
	// contradictory state "enabled with a zero percentage".
	DownPaymentPercentage Rate

	// InstallmentRoundingMultipleMinor rounds the level installment (and the
	// down payment, if any) to the nearest whole multiple of this many minor
	// units, under Rounding.Mode. 0 means no such rounding. A Mongolian retail
	// product rounding installments to whole 100 MNT sets this to 10000 (100.00
	// MNT expressed in minor units).
	//
	// Rounding is to the NEAREST multiple under Rounding.Mode, not always up and
	// not always down. A positive installment is never rounded down to zero: if
	// the multiple exceeds the installment, the unrounded installment stands.
	//
	// This field is a known parity hazard against the reference oracle, which
	// sources the tie rule for the installment and for the down payment from two
	// different places. The contract resolves that here: both use
	// Rounding.Mode, and the reference-oracle adapter is responsible for
	// configuring its tenant so that its two call sites agree with
	// Rounding.Mode. See DEC-1.
	InstallmentRoundingMultipleMinor int64
}

// PeriodKind discriminates the three kinds of row a schedule contains.
type PeriodKind int32

const (
	// PeriodKindUnspecified is the zero value and never appears in a response.
	PeriodKindUnspecified PeriodKind = iota

	// PeriodKindDisbursement is an advance of principal to the borrower. Its
	// FromDate and DueDate are both the disbursement date, its PrincipalMinor is
	// the amount advanced, and its InterestMinor is 0.
	PeriodKindDisbursement

	// PeriodKindDownPayment is the down payment taken on the disbursement date.
	// Its FromDate and DueDate are both the disbursement date, its
	// PrincipalMinor is the amount taken, and its InterestMinor is 0.
	PeriodKindDownPayment

	// PeriodKindRepayment is an ordinary scheduled installment.
	PeriodKindRepayment
)

// Period is one row of the generated schedule.
//
// Only the quantities that cannot be recomputed from the others are carried.
// The total due for a period is PrincipalMinor + InterestMinor; the level
// installment is that sum on any ordinary period; the remaining total
// repayable is the sum over later periods; the loan term in days is the span
// from the first date to the last. None of these is a field, because a derived
// total in the response is a second source of truth that lets an implementation
// be simultaneously right about the split and wrong about the sum, and because
// a derived total's meaning silently changes the moment charges are introduced.
type Period struct {
	// Kind discriminates this row. See PeriodKind.
	Kind PeriodKind

	// InstallmentNumber is the payable-installment sequence number: a dense,
	// 1-based counter running across down-payment and repayment periods in
	// order. It is 0 for a PeriodKindDisbursement period, which is not payable
	// and carries no installment number.
	InstallmentNumber int32

	// FromDate is the civil date on which the period opens, interpreted in
	// GenerateRequest.TimeZone. Interest accrues over [FromDate, DueDate).
	FromDate CivilDate

	// DueDate is the civil date on which the period's amount falls due,
	// interpreted in GenerateRequest.TimeZone.
	DueDate CivilDate

	// PrincipalMinor is this period's principal component, in minor units of
	// GenerateRequest.Currency. It is never negative.
	//
	// For PeriodKindDisbursement it is the principal advanced TO the borrower;
	// for the other kinds it is the principal repaid BY the borrower. The sign
	// convention is the row's Kind, not a negative number, so that no consumer
	// can sum the column without first deciding what it is summing.
	//
	// On a repayment period, principal is the balancing remainder of the level
	// installment after interest, never an independently computed figure. The
	// final unpaid period additionally absorbs the whole accumulated rounding
	// residual, so its PrincipalMinor + InterestMinor generally differs from the
	// other periods'. That residual is expressible without loss precisely
	// because this contract carries the per-period split and carries no
	// separate installment field that could contradict it.
	PrincipalMinor int64

	// InterestMinor is this period's interest component, in minor units of
	// GenerateRequest.Currency. It is never negative, and is 0 for
	// PeriodKindDisbursement and PeriodKindDownPayment periods.
	InterestMinor int64

	// OutstandingPrincipalMinor is the principal balance remaining after this
	// period is applied, in minor units of GenerateRequest.Currency. It is never
	// negative, and it is 0 on the final period of a fully amortizing schedule.
	//
	// It is carried rather than derived because the reference oracle clamps this
	// roll-forward at zero rather than computing it as a pure running
	// difference, so the two are not provably identical in every configuration,
	// and because it is the field against which the per-period amortization
	// invariant is checked without summing the whole schedule.
	OutstandingPrincipalMinor int64
}

// Schedule is the generated repayment schedule.
//
// It is a struct with one field rather than a bare slice so that the response
// can gain a field in some later ratified version without changing the
// interface's return type.
type Schedule struct {
	// Periods are the schedule's rows in a total, derivable order:
	// non-decreasing by DueDate; ties broken by Kind with
	// PeriodKindDisbursement before PeriodKindDownPayment before
	// PeriodKindRepayment; remaining ties broken by ascending
	// InstallmentNumber.
	//
	// The order is a property of the values, not of any implementation's loop
	// structure, so two implementations agree on it without mirroring each
	// other's control flow. Two Schedules are equal when their Periods are
	// element-wise equal in this order. No map appears in this contract and no
	// map iteration order is ever observable through it.
	Periods []Period
}

// ScheduleGenerator answers exactly one question: given the terms of a loan,
// what is its repayment schedule?
//
// It is implemented twice — once as an adapter onto the Fineract JVM reference
// oracle, once by the Go native module — and callers depend only on this
// interface. Which implementation a deployment resolves is a per-bounded-context
// configuration decision described in DEC-1; changing it in a live environment
// is a separate `user` gate and is not expressible through this interface.
//
// Generation is a pure function of its request: it moves no money, writes no
// ledger entry and has no side effect. It therefore carries no Idempotency-Key
// — that mandate applies to money-movement requests, and a request that can be
// replayed freely without consequence needs no deduplication key. Any later
// operation that commits a schedule to an account is a different operation
// under a different contract.
//
// Implementations must be deterministic: an equal GenerateRequest yields an
// equal Schedule, on every call, in every process, forever. Conformance is
// judged by replaying captured golden vectors through both implementations and
// comparing the resulting Schedules element-wise.
type ScheduleGenerator interface {
	// Generate returns the repayment schedule for req, or an error.
	//
	// ctx carries deadline and cancellation across the boundary because the
	// boundary may be crossed in-process or over a network hop depending on
	// which implementation is resolved; a purely computational implementation
	// may honour cancellation and otherwise ignore it.
	//
	// On error the returned Schedule is the zero value and must not be
	// inspected.
	Generate(ctx context.Context, req GenerateRequest) (Schedule, error)
}

// Errors returned by every implementation of ScheduleGenerator. They are part
// of the contract: two implementations must reject the same requests, or a
// request accepted by one and refused by the other would be indistinguishable
// from a conformance failure.
//
// The taxonomy is deliberately two-valued — is the request well formed, and can
// it be answered — because golden vectors compare successful schedules, and a
// finer error vocabulary would be contract surface no vector exercises.
var (
	// ErrInvalidRequest reports a request that is not well formed: a zero or
	// out-of-range enum, a non-canonical or non-positive-denominator Rate, an
	// impossible CivilDate, a non-IANA TimeZone, a non-positive precision, a
	// non-positive amount or count.
	ErrInvalidRequest = errors.New("loanschedule: invalid request")

	// ErrUnsupportedConfiguration reports a well-formed request whose values lie
	// outside what this contract currently admits or what this implementation
	// can answer identically to its counterpart: an interest method other than
	// declining balance, or a Disbursements slice whose length is not one.
	ErrUnsupportedConfiguration = errors.New("loanschedule: unsupported configuration")
)
