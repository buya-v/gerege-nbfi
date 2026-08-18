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
// DEC-1 and this package are a decision gate. Once DEC-1 is ratified, no agent
// may add, remove, rename, retype or re-document any identifier here: a change
// to this file is a change to the frozen contract and must be raised as a
// `user` gate, because every captured golden vector is expressed in these types
// and a shape change invalidates the conformance corpus.
//
// # The two reference-oracle paths, and why the difference is normative
//
// The reference oracle can be driven two ways, and they DO NOT have the same
// capability. Every clause below states which path can grade it.
//
//   - Path A, the embeddable seam: ProgressiveLoanScheduleGenerator.generate(
//     MathContext, LoanRepaymentScheduleModelData), in-process, no database.
//     Cheap, but it silently DROPS two of its own 19 inputs.
//     LoanApplicationTerms.assembleFrom (:579-606) never reads
//     installmentAmountInMultiplesOf, and the private
//     LoanApplicationTerms(Builder) constructor (:304-351) never copies
//     daysInYearCustomStrategy or interestCalculationPeriodMethod out of the
//     builder. A schedule generated through Path A is therefore blind to
//     InstallmentRoundingMultipleMinor, to the DayCountConvention members that
//     carry a leap-day strategy, and to InterestCalculationPeriod.
//   - Path B, the running server: POST /loans?command=calculateLoanSchedule
//     against PostgreSQL. It honours all of them, and they move money.
//
// A conformance run built on Path A alone would score an implementation
// identically whether it implemented those inputs or ignored them. Clauses
// marked "Path B only" can only be graded against Path-B vectors.
//
// # Invariants this package enforces by construction
//
//   - All monetary quantities are int64 counts of the currency's minor unit.
//     There is no float32, float64, big.Float, decimal string or float-backed
//     decimal type in this package, and none is implied by any field. This
//     extends to the capture pipeline: the reference oracle exposes double
//     overloads (Money.java:134-148, :261-267) and the Path-B server renders
//     amounts as unquoted JSON numbers, so a harness must carry raw decimal
//     text and must never route an amount through binary floating point.
//   - All rates are exact integer rationals. There is no percentage-shaped
//     float and no lossy basis-point truncation.
//   - All dates are civil dates (year/month/day) interpreted in one explicit
//     IANA time zone carried by the request. There is no time.Time, no UTC
//     offset, and no instant anywhere in this package.
//   - The response's period list has a total order that reproduces the
//     reference oracle's emission order (see Schedule). No map, and therefore
//     no map iteration, appears in the contract or its semantics.
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
//   - No input value is ever silently dropped. An implementation that cannot
//     honour a legal input must return ErrUnsupportedConfiguration or
//     ErrUnvectored. Producing a schedule as if the input had not been supplied
//     is a conformance failure, not a degradation.
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
	//
	// Upper case is normative for this contract and for the vector store. The
	// reference oracle accepts any case and its own shipped fixture uses "usd";
	// an adapter must upper-case on capture and may pass either case downstream,
	// because the code reaches no arithmetic. Two vectors differing only in the
	// case of this field are the same vector and must not both exist.
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
//
// One representable-domain limit, stated rather than hidden: both adapters must
// render a Rate as the decimal percentage the reference oracle's input expects.
// A reduced denominator with a prime factor other than 2 or 5 (Rate{1, 3}) has
// no exact terminating decimal percentage and must be rejected with
// ErrUnsupportedConfiguration rather than silently rounded.
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
// This is one field, not the reference oracle's (days-in-month, days-in-year,
// leap-day-strategy) triple. The triple form admits combinations no product
// uses and no vector covers, and it is the shape of the reference
// implementation rather than the shape of the question. Adding a further named
// convention later widens this enum's value domain without changing any struct,
// which is the cheapest form of contract evolution available.
//
// The mapping from each member onto the reference oracle's three inputs is
// NORMATIVE and is what makes the Fineract-JVM adapter fully determined:
//
//	member                              daysInMonth  daysInYear  daysInYearCustomStrategy
//	DayCountFixed30Over360              DAYS_30      DAYS_360    null
//	DayCountActualActual                ACTUAL       ACTUAL      null
//	DayCountActualActualFullLeapYear    ACTUAL       ACTUAL      FULL_LEAP_YEAR
//	DayCountActualActualFeb29PeriodOnly ACTUAL       ACTUAL      FEB_29_PERIOD_ONLY
//
// This field does NOT reach the rate factor when InterestCalculationPeriod is
// InterestCalculationSameAsRepaymentPeriod and RepaymentFrequencyUnit is
// FrequencyMonths or FrequencyWeeks: that combination returns a fixed 1/12 or
// 1/52 fraction before any day-count branch is evaluated
// (ProgressiveEMICalculator.java:1510-1521, :1377-1388). It is still carried on
// the request, because a vector must record what produced it.
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
	// 366) and the real number of days elapsed, with no leap-day override.
	// Where an interest sub-period crosses a calendar-year boundary, the
	// fraction is accumulated per calendar-year segment, each over that year's
	// own length.
	DayCountActualActual

	// DayCountActualActualFullLeapYear is DayCountActualActual with the
	// reference oracle's FULL_LEAP_YEAR strategy: a period falling in a leap
	// year is always divided by 366, whether or not it contains 29 February.
	//
	// Path B only. The reference oracle consults the strategy at exactly two
	// places (ProgressiveEMICalculator.java:1346-1352 and :1372-1374) and at
	// both of them FULL_LEAP_YEAR and an absent strategy take the same branch,
	// so this member and DayCountActualActual are believed to be
	// indistinguishable. That belief is derived from source and is NOT observed;
	// until a capture pins it, the two members must be treated as distinct and
	// an adapter must render exactly the one it was given.
	DayCountActualActualFullLeapYear

	// DayCountActualActualFeb29PeriodOnly is DayCountActualActual with the
	// reference oracle's FEB_29_PERIOD_ONLY strategy: a period in a leap year is
	// divided by 366 only if it actually contains 29 February, and by 365
	// otherwise.
	//
	// Path B only, and it moves money: on MNT 1,200,000 over 12 monthly
	// installments at 21.6% p.a. spanning 29 February 2024, total interest is
	// 145,011.43 under this member against 144,659.21 under
	// DayCountActualActualFullLeapYear, all twelve periods differing.
	DayCountActualActualFeb29PeriodOnly
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

// InterestCalculationPeriod selects the granularity at which the reference
// oracle forms the per-period interest fraction.
//
// It is a request field rather than a pinned constant because the two paths
// disagree about it and the grading vectors need both values: every Path-A
// capture runs the InterestCalculationDaily branch, while the Path-B captures
// that grade InstallmentRoundingMultipleMinor run
// InterestCalculationSameAsRepaymentPeriod. A boundary that cannot express its
// own vectors cannot be graded.
type InterestCalculationPeriod int32

const (
	// InterestCalculationUnspecified is the zero value and is never valid in a
	// request.
	InterestCalculationUnspecified InterestCalculationPeriod = iota

	// InterestCalculationDaily forms the per-period fraction from the day-count
	// convention: the DayCount branches are evaluated in full.
	//
	// The Path-A seam has no way to set the reference oracle's
	// interestCalculationPeriodMethod at all, so it arrives null. The oracle
	// consults that field at exactly three places
	// (ProgressiveEMICalculator.java:128-129, :1377-1378, :1510-1511) and every
	// one of them is the predicate `!= null && isSameAsRepaymentPeriod()`, so a
	// null setting takes the same branch as DAILY throughout this bounded
	// context. Path-A vectors are therefore labelled with this member, and the
	// Fineract-JVM adapter renders it onto Path A by leaving the field null and
	// onto Path B as DAILY.
	InterestCalculationDaily

	// InterestCalculationSameAsRepaymentPeriod makes the per-period fraction a
	// fixed RepaymentEvery/12 for FrequencyMonths and RepaymentEvery/52 for
	// FrequencyWeeks, evaluated before any day-count branch and therefore
	// ignoring DayCount entirely (ProgressiveEMICalculator.java:1510-1521).
	// For FrequencyDays and FrequencyYears the branch does not apply and the
	// day-count path is taken as usual.
	//
	// Path B only: the Path-A seam cannot render it, and a request carrying it
	// must be rejected with ErrUnsupportedConfiguration by a Path-A adapter.
	//
	// It also arms PartialPeriodInterest, which is inert under
	// InterestCalculationDaily.
	InterestCalculationSameAsRepaymentPeriod
)

// PartialPeriodInterest selects whether a disbursement that lands inside a
// repayment period accrues interest from its own date or from the start of the
// period it falls in.
//
// It is consulted at exactly one place in the schedule-generating path
// (ProgressiveEMICalculator.java:128-134) and only when
// InterestCalculationPeriod is InterestCalculationSameAsRepaymentPeriod; under
// InterestCalculationDaily the predicate short-circuits and this field has no
// effect on any figure.
type PartialPeriodInterest int32

const (
	// PartialPeriodUnspecified is the zero value and is never valid in a
	// request.
	PartialPeriodUnspecified PartialPeriodInterest = iota

	// PartialPeriodAllowed accrues interest on a disbursement from the
	// disbursement date itself.
	PartialPeriodAllowed

	// PartialPeriodNotAllowed moves a disbursement's effective interest start
	// date forward to the from-date of the first repayment period whose due
	// date is after the disbursement date. When the disbursement date already
	// is that from-date — which is the ordinary case of a loan disbursed on its
	// schedule start date — the move is a no-op and this member is
	// indistinguishable from PartialPeriodAllowed.
	PartialPeriodNotAllowed
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
	// zero. This is the ratified Gerege tenant mode.
	RoundingHalfUp

	// RoundingHalfEven rounds to the nearest neighbour; a tie rounds towards the
	// even neighbour. It is the reference oracle's stock configuration default
	// and is admitted so that a deployment inheriting that default is
	// expressible rather than unrepresentable.
	RoundingHalfEven
)

// Rounding is the precision and rounding policy under which the schedule is
// computed. It is an input to the arithmetic, not a deployment constant,
// because it changes the answer, and a golden vector is only meaningful if it
// records the policy it was captured under.
//
// The reference oracle threads a single java.math.MathContext through the
// calculation and consumes it in TWO INCOMPATIBLE SENSES. This contract carries
// the two senses as two fields, because a single integer described by a single
// sentence is exactly the ambiguity that produced a one-minor-unit error in the
// first draft of this contract:
//
//  1. As a count of SIGNIFICANT DECIMAL DIGITS, for every multiplication and
//     division of a dimensionless intermediate (SignificantDigits).
//  2. As a count of DECIMAL PLACES — a scale — applied once to the fully
//     computed per-period rate factor (RateFactorScale).
//
// The contract defines three rounding layers and exactly one mode shared by all
// of them:
//
//  1. Intermediate layer. Every dimensionless intermediate — the per-period
//     interest fraction, the running product of the per-period growth factors,
//     the recurrence that yields the level installment, and the level
//     installment before it becomes money — is carried as an exact decimal
//     quantity rounded to SignificantDigits significant decimal digits under
//     Mode after each multiplication and each division, in the order the
//     reference oracle performs them. Intermediates are ratios, not money: they
//     are never represented as int64 minor units.
//
//  2. Rate-factor quantization. The per-period rate factor, and only it, is
//     additionally quantized to RateFactorScale decimal places under Mode once
//     it is fully computed and before it enters anything else.
//
//  3. Currency layer. A quantity becomes money when it is scaled to
//     Currency.MinorUnitDigits decimal places under Mode and recorded as an
//     int64 count of minor units.
//
// The addition that forms the per-period growth factor, 1 + rateFactor, is
// EXACT: the reference oracle performs it with no MathContext
// (RepaymentPeriod.java:216-218), so the quantized rate factor's full width
// propagates unrounded into the recurrence.
type Rounding struct {
	// SignificantDigits is the number of significant decimal digits retained
	// after each multiplication and each division of a dimensionless
	// intermediate. It must be > 0.
	//
	// The reference oracle takes it from MathContext.getPrecision() at the four
	// mc-qualified operations of the rate-factor computation and at every other
	// mc-qualified operation in the calculation. Gerege's production value is
	// 19: MoneyHelper.PRECISION is the compile-time constant 19
	// (MoneyHelper.java:35) and getMathContext() returns
	// new MathContext(19, tenantRoundingMode) (:91-93), so only the mode is
	// tenant-configurable. The reference oracle's shipped conformance test uses
	// 12, which is a probe setting and not production-representative.
	SignificantDigits int32

	// RateFactorScale is the number of DECIMAL PLACES to which the fully
	// computed per-period rate factor is quantized under Mode, before it is
	// used anywhere else. It must be > 0.
	//
	// The reference oracle performs this at
	// ProgressiveEMICalculator.java:1962 and :1979:
	//
	//	interestRate.multiply(interestFractionPerPeriod, mc)
	//	            .multiply(actualDaysInPeriod, mc)
	//	            .divide(calculatedDaysInPeriod, mc)
	//	            .setScale(mc.getPrecision(), mc.getRoundingMode())
	//
	// The three mc-qualified operations are SignificantDigits; the trailing
	// setScale is RateFactorScale. Because a rate factor is a small number
	// (typically of order 0.005 to 0.02), a scale is strictly lossier than the
	// same number of significant digits on this quantity — the leading zeros
	// buy nothing — and the loss is observable in a payable amount. Observed on
	// the pinned oracle at SignificantDigits 12, HALF_UP, 18 monthly
	// installments at 18.5% p.a. on principal 87,654,321 major units: period 5
	// pays principal 4,531,420.25 and interest 1,082,346.53, and total interest
	// is 13,393,481.05. Omitting the quantization gives 4,531,420.26 /
	// 1,082,346.52 and total interest 13,393,481.04 — a divergence that appears
	// in period 5 and never heals. An implementation that applies only sense 1
	// still passes the reference oracle's shipped conformance vector, and then
	// misprices an ordinary Mongolian loan.
	//
	// Because the reference oracle derives both senses from one integer,
	// RateFactorScale must equal SignificantDigits. A request in which they
	// differ describes a configuration no deployment of the reference oracle
	// can produce and must be rejected with ErrUnsupportedConfiguration. They
	// are nonetheless two fields: one integer with two documented meanings is
	// the defect this pair exists to make unrepeatable, and a captured vector
	// must echo both so it can never be replayed under a policy it was not
	// captured at.
	RateFactorScale int32

	// Mode is the tie-breaking rule for all three layers. One mode, not three:
	// the reference oracle derives every tie rule from one source — the threaded
	// MathContext where one is passed, and the tenant-global MathContext where
	// one is not (Money.java:52, :102-104, :159-161, :169) — and independently
	// settable modes would admit combinations no deployment can produce.
	//
	// The Fineract-JVM adapter must therefore initialise its tenant rounding
	// mode to Mode, and its tenant precision to SignificantDigits, before every
	// call: several paths construct Money without an explicit MathContext and
	// read the tenant-global one, and outside an initialised tenant they throw.
	Mode RoundingMode
}

// Disbursement is one advance of principal to the borrower.
type Disbursement struct {
	// Date is the civil date on which the principal is advanced.
	//
	// It is also the SEED of the month-end date rule described on
	// GenerateRequest.ScheduleStartDate — not ScheduleStartDate itself.
	Date CivilDate

	// AmountMinor is the principal advanced, in minor units of
	// GenerateRequest.Currency. It must be > 0.
	AmountMinor int64
}

// GenerateRequest is the complete input to schedule generation. Two
// implementations given an equal GenerateRequest must return an equal Schedule.
//
// Every field changes the numeric output, or records which of two reference
// oracle branches produced it. Anything that a schedule can be generated
// without — the borrower, the loan account, the product catalogue, charges,
// taxes, ledger accounts, business dates, tenants — is absent by design.
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
	// boundaries are stepped. The first repayment period runs from this date.
	//
	// It is a separate input from a disbursement date because the reference
	// oracle keeps them separate — the period start is the submitted-on date and
	// the month-end seed is the disbursement date
	// (LoanApplicationTerms.java:583-589, ProgressiveLoanScheduleGenerator.java
	// :93-95) — and because collapsing them would make the boundary unable to
	// express a loan whose repayments start on a date other than the advance.
	//
	// # Date stepping, normative
	//
	// Due dates are produced ITERATIVELY, each from the previous one, never by
	// multiplying the step (DefaultScheduledDateGenerator.java:55-73):
	//
	//	due[0] = ScheduleStartDate
	//	due[k] = adjust(step(due[k-1]), seed)
	//
	// step adds RepaymentEvery units of RepaymentFrequencyUnit using calendar
	// arithmetic that clamps to the target month's length — 31 January plus one
	// month is 29 February in 2024 (:311-333, java.time.LocalDate.plusMonths).
	// Iteration matters: stepping years one at a time from 29 February 2024
	// reaches 28 February 2028, whereas adding four years at once would reach
	// 29 February 2028.
	//
	// adjust re-anchors the day to the SEED, and the seed is
	// Disbursements[0].Date, not this field (:168-176):
	//
	//	if RepaymentFrequencyUnit is FrequencyMonths
	//	   and seed.Day > 28 and stepped.Day >= 28:
	//	       stepped.Day = min(days in stepped's month, seed.Day)
	//
	// So the clamped day IS remembered, in the seed. Observed on the pinned
	// oracle, seed and start both 31 January 2024, six monthly installments:
	// due dates 29 February, 31 March, 30 April, 31 May, 30 June, 31 July, loan
	// term 182 days. Reading the clamp as sticky instead would give 29 February
	// then 29 March, 29 April, 29 May, 29 June, 29 July and a 180-day term, and
	// would misprice or misdate every month-end loan. For a 30 January seed the
	// oracle gives 29 February, 30 March, 30 April, 30 May, 30 June, 30 July.
	//
	// adjust applies to FrequencyMonths only; for FrequencyDays, FrequencyWeeks
	// and FrequencyYears the stepped date stands.
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
	//
	// A disbursement whose Date lies outside [ScheduleStartDate, last due date)
	// is legal and is REPRODUCED, not rejected: the reference oracle emits no
	// disbursement row for it and amortizes nothing, because the only pass that
	// would emit it is gated on the multi-disbursement flag this contract pins
	// false (ProgressiveLoanScheduleGenerator.java:305-310, :147-150). The
	// result is a degenerate all-zero schedule. Refusing it would break shadow
	// parity, which is the one thing the boundary exists to preserve; forbidding
	// it belongs in a business validation in FRONT of both implementations.
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
	// the conversion to a per-period fraction is performed by DayCount and
	// InterestCalculationPeriod, not by compounding this value.
	//
	// Zero interest is Rate{0, 1} and is a supported, non-special-cased case.
	AnnualNominalInterestRate Rate

	// InterestMethod selects how interest is derived from the balance. See
	// InterestMethod.
	InterestMethod InterestMethod

	// DayCount selects the day-count convention converting
	// AnnualNominalInterestRate into a per-period interest fraction. See
	// DayCountConvention, whose mapping onto the reference oracle's three inputs
	// is normative.
	DayCount DayCountConvention

	// InterestCalculationPeriod selects the granularity at which the per-period
	// interest fraction is formed. See InterestCalculationPeriod.
	InterestCalculationPeriod InterestCalculationPeriod

	// PartialPeriodInterest selects whether a disbursement accrues from its own
	// date or from the start of the period containing it. Inert unless
	// InterestCalculationPeriod is InterestCalculationSameAsRepaymentPeriod.
	// See PartialPeriodInterest.
	PartialPeriodInterest PartialPeriodInterest

	// DownPaymentPercentage is the fraction of the disbursed principal taken as
	// a down payment on the disbursement date. Rate{0, 1} means no down
	// payment and no down-payment period in the response; Rate{1, 10} means
	// 10%. It must be < 1.
	//
	// A non-zero value adds a PeriodKindDownPayment period to the response
	// immediately after the disbursement row it belongs to, consumes an
	// InstallmentNumber, and reduces the principal amortized across the
	// repayment periods. If InstallmentRoundingMultipleMinor is non-zero the
	// down payment is rounded by the same rule as the installment
	// (ProgressiveLoanScheduleGenerator.java:331-343).
	//
	// It is a single field: a separate enabled/disabled boolean would admit the
	// contradictory state "enabled with a zero percentage". Like
	// AnnualNominalInterestRate it must be renderable as an exact terminating
	// decimal percentage, or ErrUnsupportedConfiguration.
	DownPaymentPercentage Rate

	// InstallmentRoundingMultipleMinor rounds the level installment (and the
	// down payment, if any) to the nearest whole multiple of this many minor
	// units, under Rounding.Mode. 0 means no such rounding. A Mongolian retail
	// product rounding installments to whole 100 MNT sets this to 10000 (100.00
	// MNT expressed in minor units).
	//
	// # Representable domain
	//
	// The reference oracle's counterpart is an Integer count of MAJOR currency
	// units, divided into an amount already at currency scale
	// (Money.java:150-157 and :163-170). So this value must be 0, or a positive
	// exact multiple of 10^Currency.MinorUnitDigits whose quotient by that
	// power of ten does not exceed 2147483647. 10000 minor units of MNT is
	// legal and denotes 100 MNT; 50 (0.50 MNT) and 1 (0.01 MNT) are not
	// representable to the reference oracle and must be rejected with
	// ErrUnsupportedConfiguration rather than silently rounded or dropped.
	//
	// # Semantics, normative
	//
	// Rounding is to the NEAREST multiple under Rounding.Mode — the reference
	// oracle divides by the multiple to a scale-0 quotient under that mode and
	// multiplies back — not always up and not always down. If the result would
	// be zero while the unrounded installment is positive, the UNROUNDED
	// installment stands (ProgressiveEMICalculator.java:1761-1776), so a small
	// principal stays spread across installments instead of piling onto one.
	// The rounding is applied to the level installment before the per-period
	// split, and the last period's residual absorption (see Period) happens
	// AFTER it and is not re-rounded, so the final installment is generally not
	// a multiple.
	//
	// # Grading
	//
	// Path B only. The Path-A seam never reads the field
	// (LoanApplicationTerms.java:579-606 reads 18 of its input record's 19
	// components; this is the one it omits), so a Path-A conformance run cannot
	// tell an implementation that honours this field from one that ignores it.
	// Observed on the Path-B server, MNT 1,200,000 over 12 monthly installments
	// at 21.6% p.a.: with the field unset the installment is 112,082.37 and
	// total interest 144,988.47; set to 100 major units the installment is
	// 112,100.00, total interest 144,966.22, all twelve periods differ, and the
	// final installment is 111,866.22 — not a multiple of 100, because it
	// carries the residual.
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

	// PeriodKindRepayment is an ordinary scheduled installment. It may be
	// all-zero: a repayment period that closes before the principal is advanced
	// is emitted with zero principal, zero interest and zero outstanding
	// balance.
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
	// and carries no installment number. This is the one place the reference
	// oracle's null is normalised, and it is normalised to a value that cannot
	// collide with a real installment.
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
	// installment after interest, never an independently computed figure, and
	// it is clamped at zero (RepaymentPeriod.java:345-350).
	//
	// # The last period's residual, normative
	//
	// Let I be the level installment after any InstallmentRoundingMultipleMinor
	// rounding, N the number of repayment periods, interest[k] each period's
	// interest, and A the principal advanced. Every sum is accumulated at
	// currency scale under Rounding.Mode, not at intermediate precision
	// (ProgressiveEMICalculator.java:1190-1205):
	//
	//	residual        = (A + sum interest[k]) - N*I
	//	installment[N]  = I + residual
	//	installment[k]  = I                       for k < N
	//
	// and each period's principal is then its installment minus its interest.
	// The residual may be positive or negative. It is the last period, not "the
	// last unpaid period": this contract has no notion of payment, so every
	// period is unpaid and the reference oracle's filter selects the last one.
	// Under this contract's pinned configuration the reference oracle's
	// capitalized-income and credited-principal terms are identically zero and
	// drop out of the formula.
	//
	// Observed at production settings on the pinned oracle: MNT 1,200,000 over
	// 12 at 21.6% p.a. gives I = 112,082.37 and a final installment of
	// 112,082.40 (residual +0.03); the same loan with the installment rounded to
	// multiples of 100 gives I = 112,100.00 and a final installment of
	// 111,866.22 (residual -233.78).
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
	// difference (RepaymentPeriod.java:389-403, InterestPeriod.java:168-179), so
	// the two are not provably identical in every configuration, and because it
	// is the field against which the per-period amortization invariant is
	// checked without summing the whole schedule.
	OutstandingPrincipalMinor int64
}

// Schedule is the generated repayment schedule.
//
// It is a struct with one field rather than a bare slice so that the response
// can gain a field in some later ratified version without changing the
// interface's return type.
type Schedule struct {
	// Periods are the schedule's rows in the order the reference oracle emits
	// them. The order is normative, is fully determined by the request, and is
	// NOT a sort by due date.
	//
	// Let P[1..N] be the repayment periods in ascending period number, P[k]
	// spanning the half-open window [FromDate[k], DueDate[k]). Emission runs
	// k = 1..N and, for each k, in this order
	// (ProgressiveLoanScheduleGenerator.java:114-143, :298-346):
	//
	//  1. every disbursement whose date d satisfies
	//     FromDate[k] <= d < DueDate[k], in ascending d and, for equal d, in
	//     request order; each such disbursement row is immediately followed by
	//     its own down-payment row when DownPaymentPercentage is non-zero;
	//  2. then P[k]'s own repayment row.
	//
	// The consequence a naive sort gets wrong: because the window is half-open,
	// a disbursement dated exactly on P[k]'s due date belongs to P[k+1] and is
	// emitted AFTER P[k]'s repayment row. Observed on the pinned oracle with
	// ScheduleStartDate 2024-01-01, disbursement 2024-02-01, six monthly
	// installments: the emitted order is the all-zero repayment row numbered 1
	// and due 2024-02-01, THEN the disbursement row dated 2024-02-01, then
	// repayments 2 to 6. Sorting by due date and breaking ties by kind would
	// put the disbursement first and is wrong.
	//
	// The order is a property of the request and the rows, not of any
	// implementation's loop structure, so two implementations agree on it
	// without mirroring each other's control flow. Two Schedules are equal when
	// their Periods are element-wise equal in this order. No map appears in this
	// contract and no map iteration order is ever observable through it.
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
// The taxonomy is three-valued, and the third value is load-bearing. "This
// contract does not admit that" and "no captured vector proves what either of
// us would do" are different facts with different remedies, and collapsing them
// hides the second — which is the failure mode this whole programme exists to
// prevent. What is never legal is answering anyway.
var (
	// ErrInvalidRequest reports a request that is not well formed: a zero or
	// out-of-range enum, a non-canonical or non-positive-denominator Rate, an
	// impossible CivilDate, a non-IANA TimeZone, a non-positive precision or
	// scale, a non-positive amount or count.
	ErrInvalidRequest = errors.New("loanschedule: invalid request")

	// ErrUnsupportedConfiguration reports a well-formed request whose values lie
	// outside what this contract admits, or which the resolved implementation
	// provably cannot render onto its reference-oracle path: an interest method
	// other than declining balance; a Disbursements slice whose length is not
	// one; a Rounding whose RateFactorScale differs from its SignificantDigits;
	// a Rate or DownPaymentPercentage with no exact terminating decimal
	// percentage; an InstallmentRoundingMultipleMinor that is not a whole number
	// of major units; or InterestCalculationSameAsRepaymentPeriod asked of an
	// adapter that drives the reference oracle through its embeddable seam.
	ErrUnsupportedConfiguration = errors.New("loanschedule: unsupported configuration")

	// ErrUnvectored reports a well-formed request this contract admits, and
	// whose semantics are specified, but for which the conformance corpus holds
	// no captured vector — so no implementation may claim its answer matches the
	// reference oracle.
	//
	// It is returned rather than a plausible number, because a money path
	// nobody has ever compared against the oracle is exactly the unverifiable
	// promise this migration exists to avoid; and it is returned rather than
	// silently ignoring the input, because a silent drop is a wrong answer
	// dressed as a right one.
	//
	// Which values are unvectored is a property of the corpus, not of the
	// contract, so lifting a refusal is a behaviour change needing no
	// amendment. At the time of ratification the corpus covers only monthly
	// repayment at RepaymentEvery 1, declining balance, and a zero down
	// payment; DEC-1 carries the authoritative list.
	ErrUnvectored = errors.New("loanschedule: no golden vector for this configuration")
)
