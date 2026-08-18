// Package contract defines the frozen adapter contract for the loan-schedule
// bounded context: the single question "generate a repayment schedule", asked
// in a form that either the Fineract reference oracle or the Go native module
// can answer identically.
//
// This package is specified by ADR DEC-1
// (docs/adr/DEC-1-schedule-generator-adapter.md). It is the strangler boundary
// for the loan-schedule context of the Fineract -> Go migration. The doc
// comments in this file ARE the specification: where a behaviour is stated
// here, an implementation that does something else is wrong, whatever any
// prose elsewhere says.
//
// "The reference oracle" in this package always means the Fineract reference
// implementation at pinned commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
// which this program grades Go output against. It never means Oracle Database,
// which is a prohibited product in this program.
//
// # Amendment gate
//
// Ratifying DEC-1 is a decision the driver may take on a clean independent
// review (standing policy P-1..P-3, .softhouse/gates-proposed-answers.md).
// Once DEC-1 is RATIFIED, amending it — adding, removing, renaming, retyping
// or re-documenting any identifier in this package, or changing any behaviour
// the doc comments below specify — requires raising a gate. It is not an
// agent's call, because every captured golden vector is expressed in these
// types and a shape change invalidates the conformance corpus.
//
// Widening the GRADED DOMAIN (see below) is not an amendment. It is behaviour,
// not shape: no type changes, no vector's field set moves, and no ratified
// sentence is contradicted.
//
// # The two domains, and why there are two
//
// This contract distinguishes:
//
//   - The CONTRACT DOMAIN — every value these types admit as well formed. It
//     is frozen by ratification.
//   - The GRADED DOMAIN — the strict subset of the contract domain for which a
//     capture from the reference oracle exists that can actually tell a correct
//     implementation from an incorrect one. It is listed on GenerateRequest and
//     it grows as vectors land.
//
// A value inside the contract domain but outside the graded domain must be
// REFUSED with ErrNoDiscriminatingVector, never silently accepted and never
// silently dropped. The failure mode this program exists to prevent is a port
// that passes its corpus and is wrong; an explicit refusal converts a silent
// wrong answer into a loud missing feature.
//
// This is not hypothetical. The capture seam the Run-1 corpus is taken through
// accepts a 19-component input record and honours 17 of them: it never reads
// installmentAmountInMultiplesOf (the field exists at
// LoanApplicationTerms.java:217, but its Builder has no setter for it and
// assembleFrom builds exclusively through the Builder,
// LoanApplicationTerms.java:579-607), and it never copies daysInYearCustomStrategy
// out of its Builder (set at LoanApplicationTerms.java:604, stored by the
// Builder at :380/:567-568, and absent from the private Builder copy
// constructor at :304-351, whose only sibling assignment is in a positional
// constructor at :881). For both fields that seam has ZERO discriminating
// power: an implementation honouring them and one ignoring them score
// identically. Both facts were re-confirmed differentially and reflectively at
// the production MathContext (19, HALF_UP).
//
// # Invariants this package enforces by construction
//
//   - All monetary quantities are int64 counts of the currency's minor unit.
//     There is no float32, float64, big.Float, decimal string or float-backed
//     decimal type in this package, and none is implied by any field —
//     including for intermediate calculation.
//   - All rates are exact integer rationals. There is no percentage-shaped
//     float and no lossy basis-point truncation.
//   - All dates are civil dates (year/month/day) interpreted in one explicit
//     IANA time zone carried by the request. There is no time.Time, no fixed
//     zone, no UTC offset and no instant anywhere in this package.
//   - The response's period list has a total order derivable from the response
//     itself (see Schedule). No map, and therefore no map iteration order,
//     appears in the contract or its semantics.
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
//   - No persistence, no ledger posting, no money movement. Generate is pure,
//     so no Idempotency-Key is carried; that mandate is on money-movement
//     requests.
package contract

import (
	"context"
	"errors"
	"fmt"
)

// Currency identifies the unit in which every ...Minor field in a request or
// response is denominated, and supplies the scale at which the generator
// rounds a computed quantity into a payable amount.
//
// Only the properties that change the arithmetic are carried. Display name,
// symbol and label are presentation concerns and are deliberately absent.
type Currency struct {
	// Code is the ISO 4217 alpha-3 code, upper case. For the Mongolian tugrik
	// this is "MNT" (ISO 4217 numeric 496, minor unit 2).
	//
	// It is carried so that an int64 minor-unit amount is never ambiguous and
	// so a captured golden vector is self-describing. It is NOT an input to the
	// arithmetic: the reference oracle's currency record reaches the
	// calculation only through its decimal places and its inMultiplesOf
	// (Money.java:40-53), never through its code, name or symbol.
	//
	// Normalisation, because it is observable in a captured vector: the
	// reference oracle's shipped conformance fixture spells its currency code
	// in lower case ("usd", EmbeddableProgressiveLoanScheduleGeneratorTest.java:47).
	// This contract requires upper case, and an adapter MUST upper-case on the
	// way in and MUST NOT let the oracle's spelling leak back out, so that two
	// capture runs of the same loan are structurally equal.
	Code string

	// MinorUnitDigits is the ISO 4217 minor unit exponent: the number of
	// decimal places at which a computed quantity becomes a payable amount.
	// MNT is 2, so 1,250,000.00 MNT is the int64 125000000.
	//
	// This is the scale of the currency-rounding layer (see Rounding). Storage
	// is 2 decimal places for MNT; the 0-decimal postfix presentation
	// (1,250,000₮) is a UI concern outside this contract.
	//
	// It is a field rather than a constant because it is a genuine input to the
	// oracle and because the shipped conformance fixtures are in USD. Graded
	// domain: 2 only. No capture in the corpus varies it, and at 0 decimal
	// places a second, entirely different rounding channel switches on inside
	// the oracle (Money.java:48-51 applies the currency's own inMultiplesOf
	// only when decimal places are 0) — a channel that was measured to move
	// money and that this contract deliberately does not expose.
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
// Rationals rather than a float: a float rate is prohibited on any money path,
// and it would diverge from the oracle after enough compounding periods.
//
// One representable-domain limit, stated rather than hidden. The Fineract-JVM
// adapter must render the rate as the decimal percentage the oracle's input
// record expects, which the oracle then divides by 100 under its own rounding
// policy (ProgressiveEMICalculator.java:1318-1320). A rate whose reduced
// denominator has a prime factor other than 2 or 5 — Rate{1, 3} — has no exact
// terminating decimal percentage and cannot be handed over without a rounding
// decision the contract has not specified. Such a request must be rejected with
// ErrUnsupportedConfiguration, never silently rounded.
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
// bug. Deliberately not a formatted string: parsing is a second place to
// disagree.
//
// The Go zero value CivilDate{} is invalid and must be rejected with
// ErrInvalidRequest, as is any triple that is not a real calendar date.
type CivilDate struct {
	Year  int32 // e.g. 2026
	Month int32 // 1..12
	Day   int32 // 1..31, and valid for Year and Month
}

// RepaymentFrequencyUnit is the calendar unit in which repayment periods are
// stepped, and it also selects which day-count expansion converts the annual
// nominal rate into a per-period interest fraction.
type RepaymentFrequencyUnit int32

const (
	// FrequencyUnspecified is the zero value and is never valid in a request.
	FrequencyUnspecified RepaymentFrequencyUnit = iota

	// FrequencyDays steps by calendar days.
	//
	// Computable by the reference oracle
	// (ProgressiveEMICalculator.java:1603-1604, interest fraction
	// RepaymentEvery / days-in-year), but no capture in the corpus uses it:
	// every capture is monthly. Outside the graded domain — refuse with
	// ErrNoDiscriminatingVector.
	FrequencyDays

	// FrequencyWeeks steps by calendar weeks.
	//
	// Computable by the reference oracle
	// (ProgressiveEMICalculator.java:1605-1606, interest fraction
	// 7 * RepaymentEvery / days-in-year), but no capture uses it. Outside the
	// graded domain — refuse with ErrNoDiscriminatingVector.
	//
	// Note for whoever grades it later: weekly is the frequency at which the
	// oracle's two internal rate-factor branches DISAGREE. Under a
	// same-as-repayment-period interest configuration the weekly fraction is
	// RepaymentEvery / 52 (ProgressiveEMICalculator.java:1517-1519); under a
	// 30/360 day count it is 7 * RepaymentEvery / 360. Those are different
	// numbers. Monthly is the frequency at which they coincide (see
	// GenerateRequest.DayCount).
	FrequencyWeeks

	// FrequencyMonths steps by calendar months, with the month-end rule
	// specified on Disbursement.Date. This is the only unit in the graded
	// domain.
	FrequencyMonths

	// FrequencyYears steps by calendar years.
	//
	// The reference oracle throws ONLY on the fixed-30/360 arm — the revision-2
	// claim that it "cannot answer it at all" was refuted by observation and is
	// corrected here (P0-3). The day-count switch at
	// ProgressiveEMICalculator.java:1533-1539 sends DAYS_30 (:1536) through
	// calculateRateFactorPerPeriodBasedOnRepaymentFrequency, whose per-frequency
	// switch (:1602-1610) handles DAYS, WEEKS and MONTHS and throws
	// UnsupportedOperationException for anything else — so FrequencyYears under
	// DayCountFixed30Over360 throws. NEITHER ACTUAL path reaches that dispatch
	// (revision 3 named the wrong arm here; corrected in revision 4, P1-T26-1):
	// for an ANNUAL period, partialPeriodCalculationNeeded (:1505-1507) requires
	// daysInYearType == ACTUAL && numberOfYearsDifferenceInPeriod > 0, and an
	// annual period ALWAYS crosses a calendar-year boundary, so the method
	// returns at :1526-1531 through rateFactorByRepaymentPartialPeriod and the
	// switch at :1533 is never evaluated. The case ACTUAL arm at :1534-1535 —
	// which calls rateFactorByRepaymentPeriod directly — is UNREACHABLE for
	// FrequencyYears, and is reached only for sub-annual periods that stay
	// within one calendar year. This is consistent with what DayCountActualActual
	// says below. Either way
	// DefaultScheduledDateGenerator.getRepaymentPeriodDate (:311-333) handles
	// case YEARS with plusYears, so the schedule generates. The conclusion is
	// unaffected — only the arm cited was wrong — but note that the observation
	// below therefore came out of the cross-year partial-period arm, which DEC-1
	// section 8 item 5 names as the largest un-re-derived hole in the evidence.
	// Observed on the pinned oracle, MNT 1,200,000, 3 annual installments, 21.6%:
	// DayCountFixed30Over360 throws "Invalid repayment frequency"; DayCountActualActual
	// returns a complete schedule (loan term 1096 days, total interest 551,982.62).
	//
	// The refusal therefore depends on the day-count arm, and both arms still
	// refuse, for the honest reason:
	//
	//   - with DayCountFixed30Over360 the oracle genuinely cannot be asked, so
	//     reject with ErrUnsupportedConfiguration (a missing ANSWER);
	//   - with DayCountActualActual the oracle answers, but DayCountActualActual
	//     is itself outside the graded domain, so reject with
	//     ErrNoDiscriminatingVector (a missing VECTOR), which wraps
	//     ErrUnsupportedConfiguration.
	//
	// When a request is refusable for more than one reason, the sentinel is
	// chosen by the precedence rule stated on the error variables below, so both
	// implementations return the same one. FrequencyYears is retained in the
	// value domain so that an annual product is expressible the day the graded
	// domain reaches it, and because removing an enum member later is a
	// narrowing.
	FrequencyYears
)

// DayCountConvention selects the market day-count convention used to convert
// the annual nominal rate into a per-period interest fraction.
//
// This is one field, not the reference oracle's (days-in-month, days-in-year)
// pair plus a leap-day override. The pair form admits combinations no product
// uses and no vector covers, and it is the shape of the implementation rather
// than the shape of the question. Adding a further named convention widens this
// enum without changing any struct — the cheapest form of contract evolution
// available.
//
// The mapping onto the reference oracle's enums is NORMATIVE, so that the
// Fineract-JVM adapter is fully determined by this contract:
//
//	DayCountFixed30Over360 -> (DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360)
//	DayCountActualActual   -> (DaysInMonthType.ACTUAL,  DaysInYearType.ACTUAL)
//
// The pair is load-bearing: it selects between materially different arms of
// ProgressiveEMICalculator.calculateRateFactorPerPeriod
// (ProgressiveEMICalculator.java:1533-1539, and the cross-year partial-period
// arm at :1505-1507 and :1526-1531 which only ACTUAL can reach).
type DayCountConvention int32

const (
	// DayCountUnspecified is the zero value and is never valid in a request.
	DayCountUnspecified DayCountConvention = iota

	// DayCountFixed30Over360 treats every month as exactly 30 days and every
	// year as exactly 360 days. The real calendar length of the month is
	// irrelevant to the fraction: February and January are treated identically,
	// and a leap year changes nothing.
	//
	// This is the fixed-30 / fixed-360 variant. It is NOT 30E/360 and NOT
	// 30/360 US: no end-of-month day-shifting rule is applied to the DAYS
	// count. Real calendar days do enter, as the proportional correction
	// actualDaysInPeriod / calculatedDaysInPeriod
	// (ProgressiveEMICalculator.java:1500-1503, :1961-1962). That ratio is 1
	// ONLY when the interest period spans the whole enclosing repayment period,
	// which a disbursement dated STRICTLY INSIDE a repayment period makes false;
	// on such a period the correction is days(span) / days(repayment period) and
	// is strictly less than 1. Both day counts are defined normatively on
	// Rounding.RateFactorScale under "The two day counts in the ratio", which is
	// the authoritative statement.
	//
	// (Revision 6, P0-T32-1: revision 5 said the ratio is "exactly 1 ... which
	// is every period in the graded domain". That clause was FALSE — a
	// strictly-inside-a-period disbursement is admissible under the graded
	// domain's window predicate and produces a ratio below 1 — and it is
	// deleted. Re-review T32 re-derived that hard-coding the ratio to 1 changes
	// the money on 2,913 of 2,913 such shapes, up to MNT 1,816,050.11 in total
	// interest; a re-derivation, not an observation.)
	//
	// This is the only convention in the graded domain. All twelve Run-1
	// captures use it.
	DayCountFixed30Over360

	// DayCountActualActual uses the real length of each calendar year (365 or
	// 366) and the real number of days elapsed. Where an interest sub-period
	// crosses a calendar-year boundary, the reference oracle stops using the
	// day-count fraction entirely and accumulates a per-calendar-year fraction
	// instead (ProgressiveEMICalculator.java:1505-1507 selecting :1526-1531).
	//
	// Outside the graded domain — refuse with ErrNoDiscriminatingVector. No
	// capture in the corpus exercises it, and the arm it selects is the one
	// arm of the algorithm that no independent re-derivation has yet
	// reproduced from source. A code path returning plausible numbers nobody
	// has compared against the oracle is exactly the unverifiable promise this
	// contract exists to prevent.
	//
	// Admitting it later is behaviour, not shape. It carries one consequence
	// that IS shape, and that consequence is the reason it is named here: under
	// an actual-days year the oracle's daysInYearCustomStrategy leap-day
	// override stops being inert (see GenerateRequest, "pinned oracle inputs"),
	// so admitting this convention requires either a new field or a new
	// DayCountConvention member for the override — and that is an amendment.
	DayCountActualActual
)

// InterestMethod selects how interest is derived from the outstanding balance.
type InterestMethod int32

const (
	// InterestMethodUnspecified is the zero value and is never valid in a
	// request.
	InterestMethodUnspecified InterestMethod = iota

	// InterestMethodDecliningBalance computes each period's interest from the
	// outstanding principal balance carried into that period.
	//
	// This is the only value currently legal; anything else must be rejected
	// with ErrUnsupportedConfiguration. The field exists so that a response and
	// its golden vector are self-describing about which method produced them,
	// and so that admitting flat interest later is a value-domain widening
	// rather than a struct change.
	InterestMethodDecliningBalance
)

// RoundingMode is the tie-breaking rule applied by every rounding layer
// described on Rounding.
//
// The value domain is deliberately narrow. Each admitted mode is a distinct
// tie-breaking behaviour that both implementations must prove identical against
// captured vectors, so a mode is admitted only when a product or a deployment
// requires it. The remaining five Java rounding modes are not admitted; each
// would be contract surface carrying an unproven claim.
type RoundingMode int32

const (
	// RoundingModeUnspecified is the zero value and is never valid in a request.
	RoundingModeUnspecified RoundingMode = iota

	// RoundingHalfUp rounds to the nearest neighbour; a tie rounds away from
	// zero. This is Gerege's ratified tenant mode (Fineract RoundingMode
	// ordinal 4) and the only mode in the graded domain: all twelve Run-1
	// captures were taken at it.
	RoundingHalfUp

	// RoundingHalfEven rounds to the nearest neighbour; a tie rounds towards
	// the even neighbour.
	//
	// It is admitted because it is the reference oracle's own stock
	// configuration default (a tenant seeded from FINERACT_CONFIG_ROUNDING_MODE
	// with default ordinal 6), so a deployment that inherits that default must
	// be expressible rather than unrepresentable. It is outside the graded
	// domain — refuse with ErrNoDiscriminatingVector — because no capture in
	// the corpus was taken at it.
	//
	// The mode is demonstrably live, so this is not a theoretical distinction:
	// the same request put to two tenants of one running oracle differing only
	// in rounding mode returned period-1 interest 20,925.05 under HALF_UP and
	// 20,925.04 under HALF_EVEN on a principal of MNT 1,162,502.50, the tie
	// being taken at Money.java:52.
	RoundingHalfEven
)

// Rounding is the precision and rounding policy under which the schedule is
// computed. It is an input to the arithmetic, not a deployment constant,
// because it changes the answer, and a golden vector is only meaningful if it
// records the policy it was captured under.
//
// # Why two integers and not one
//
// The reference oracle threads a single java.math.MathContext through the
// calculation and consumes it in TWO INCOMPATIBLE SENSES:
//
//  1. as a count of SIGNIFICANT DECIMAL DIGITS, at every MathContext-qualified
//     multiplication and division; and
//  2. as a count of DECIMAL PLACES — a scale — applied once to the fully
//     computed per-period rate factor.
//
// A single integer documented with a single sentence is exactly the ambiguity
// that put a one-minor-unit error into the first draft of this contract, so the
// two senses are two fields. They are constrained to be equal (see
// RateFactorScale), which is why splitting them adds no configuration the
// oracle cannot produce.
//
// # The three rounding layers, and one mode shared by all of them
//
//  1. Intermediate layer. Every dimensionless intermediate — the per-period
//     interest fraction, the running product of the per-period growth factors,
//     the recurrence that yields the level installment, and the level
//     installment before it becomes money — is carried as an exact decimal
//     quantity that is rounded to SignificantDigits significant decimal digits
//     under Mode after each multiplication and each division, in the order the
//     reference oracle performs them. Intermediates are ratios, not money:
//     they are never represented as int64 minor units, and never as a float.
//
//  2. Rate-factor quantization. The per-period rate factor, and only it, is
//     additionally quantized to RateFactorScale decimal places under Mode once
//     it is fully computed and before it enters anything else.
//
//  3. Currency layer. A quantity becomes money when it is scaled to
//     Currency.MinorUnitDigits decimal places under Mode and recorded as an
//     int64 count of minor units.
//
// Two facts about what is NOT rounded, both load-bearing:
//
//   - The additions that form each repayment period's growth factor are EXACT.
//     A repayment period's growth factor is 1 PLUS THE SUM OF ITS INTEREST
//     PERIODS' RATE FACTORS, not 1 + a single rate factor: the reference oracle
//     computes it as interestPeriods.stream().map(InterestPeriod::getRateFactor)
//     .reduce(BigDecimal.ONE, BigDecimal::add) (RepaymentPeriod.java:216-217) —
//     one addition per interest period, every one of them performed with no
//     MathContext at all (:216-218), so the quantized rate factors' full width
//     propagates unrounded into the recurrence.
//
//     (Revision 6, P1-T32-1: revisions 1-5 wrote the singular "1 + rateFactor",
//     which is correct only for a repayment period carrying exactly ONE interest
//     period. A disbursement dated inside a repayment period gives it two — see
//     the segmentation table on Period — and the singular form then leaves an
//     implementer to invent a composition rule. Re-review T32 measured the two
//     forms INERT on today's graded domain: 0 divergences over 2,913 re-derived
//     strictly-inside shapes, because under the day counts above the segment
//     factors sum to the whole-period factor at scale 19 on those shapes. It
//     stops being inert the moment an interest pause, a mid-term rate change or
//     a multi-tranche disbursement enters the domain.)
//
//   - The residual sums of the final-period adjustment (see Period) are
//     accumulated at CURRENCY scale, not at SignificantDigits: each term is
//     already money before it is added (ProgressiveEMICalculator.java:1190-1203).
//
// The ORDER of rounding operations is not a field. It is fixed by the algorithm,
// it is a conformance obligation, and it is proven by golden vectors. A field
// for it would be a licence to disagree.
type Rounding struct {
	// SignificantDigits is the number of significant decimal digits retained
	// after each multiplication and each division of a dimensionless
	// intermediate. It must be > 0.
	//
	// Gerege's production value is 19, and it is not a choice:
	// MoneyHelper.PRECISION is the compile-time constant 19
	// (MoneyHelper.java:35) and getMathContext() returns
	// new MathContext(19, tenantRoundingMode) (MoneyHelper.java:91-93), so only
	// the mode is tenant-configurable. 19 is the only value in the graded
	// domain.
	//
	// The reference oracle's shipped conformance test uses 12
	// (EmbeddableProgressiveLoanScheduleGeneratorTest.java:44). A capture at 12
	// is a rig calibration and can never be a parity vector, because production
	// never runs at 12 — and the difference is not cosmetic. Observed on the
	// pinned oracle, 18 monthly installments at 18.5% p.a. on principal
	// 87,654,321 major units, HALF_UP:
	//
	//	SignificantDigits 12: period 5 principal 4,531,420.25, interest 1,082,346.53,
	//	                      outstanding 65,674,840.83, total interest 13,393,481.05
	//	SignificantDigits 19: period 5 principal 4,531,420.26, interest 1,082,346.52,
	//	                      outstanding 65,674,840.82, total interest 13,393,481.04
	//
	// ALL EIGHTEEN per-period rows diverge, and never heal. (Revision 3 and
	// earlier said "seventeen"; the committed capture files show every one of the
	// 18 repayment rows differing — corrected in revision 4, P1-T26-3.)
	//
	// There is NO principal size below which this is safe. The oracle's own
	// 12-vs-19 pair diverges at a principal of 4.00 on a 36-period 16.8% shape
	// and is identical at 50,000,000 on that same shape. Sensitivity is a
	// rounding-boundary property of the (principal, term, rate) triple, not a
	// magnitude property of the principal, and no implementation may shortcut
	// on the basis of loan size.
	SignificantDigits int32

	// RateFactorScale is the number of DECIMAL PLACES to which the fully
	// computed per-period rate factor is quantized under Mode, before it is
	// used anywhere else. It must be > 0.
	//
	// The reference oracle performs this at ProgressiveEMICalculator.java:1959-1962
	// (and, on the cross-year partial-period arm, at :1976-1979):
	//
	//	interestRate.multiply(interestFractionPerPeriod, mc)
	//	            .multiply(actualDaysInPeriod, mc)
	//	            .divide(calculatedDaysInPeriod, mc)
	//	            .setScale(mc.getPrecision(), mc.getRoundingMode())
	//
	// The three mc-qualified operations are SignificantDigits; the trailing
	// setScale is RateFactorScale. setScale takes a SCALE, not a precision, so
	// one integer is being read in two senses.
	//
	// # The two day counts in the ratio (NORMATIVE; revision 6, P0-T32-1)
	//
	// The snippet's last two operations are a PRORATION, and revision 5 defined
	// neither of its day counts anywhere in either artefact. Both are whole-day
	// counts, both are exact integers, and they are NOT taken from the same
	// interval:
	//
	//   - actualDaysInPeriod is the NUMERATOR: whole days across THE SPAN THE
	//     RATE FACTOR IS COMPUTED OVER —
	//     DateUtils.getDifferenceInDays(interestPeriodFromDate, interestPeriodDueDate),
	//     both of them the routine's own parameters, so this is the span the
	//     caller passed (ProgressiveEMICalculator.java:1367-1368 for
	//     rateFactorTillPeriodDueDate, :1500-1501 for the recurrence's rate
	//     factor).
	//   - calculatedDaysInPeriod is the DENOMINATOR: whole days from the
	//     ENCLOSING REPAYMENT PERIOD's FromDate to its DueDate —
	//     DateUtils.getDifferenceInDays(repaymentPeriod.getFromDate(), repaymentPeriod.getDueDate())
	//     (ProgressiveEMICalculator.java:1369-1370; the same pair spelled
	//     calculatedDaysInRepaymentPeriod at :1502-1503). IT IS NEVER THE SPAN'S
	//     OWN LENGTH, and never a function of the span at all.
	//
	// The ratio is applied as .multiply(actualDaysInPeriod, mc)
	// .divide(calculatedDaysInPeriod, mc) (:1961-1962), and a guard returns
	// exactly BigDecimal.ZERO when calculatedDaysInPeriod is zero (:1953-1955),
	// before any of the four operations runs.
	//
	// THE RATIO IS 1 IF AND ONLY IF THE SPAN IS EXACTLY THE ENCLOSING REPAYMENT
	// PERIOD'S OWN WINDOW. It is strictly less than 1 whenever the span starts
	// after that period's FromDate — which is exactly what a disbursement dated
	// STRICTLY INSIDE a repayment period produces (see "The per-period interest
	// computation" on Period, third segmentation row), an in-graded-domain shape
	// under GenerateRequest's window predicate. This term is the whole mechanism
	// by which a mid-period disbursement is charged less than a full period's
	// interest.
	//
	// The two call sites pass two different spans
	// (ProgressiveEMICalculator.java:638-643), so an interest period's two rate
	// factors share a denominator and differ in numerator:
	//
	//	rateFactor              span = the interest period's own [FromDate, DueDate]   (:639-640)
	//	                        ratio = days(interest period) / days(repayment period)
	//	                        used by the fn recurrence (see the Rounding doc above)
	//	rateFactorTillPeriodDueDate
	//	                        span = [interest period FromDate, repayment period DueDate] (:641-642)
	//	                        ratio = days(that span) / days(repayment period)
	//	                        used by the per-period interest (see Period)
	//
	// When a repayment period carries ONE interest period — every committed
	// observation — both numerators equal the denominator and both ratios are 1.
	// That is why NO CAPTURE IN THE CORPUS CAN GRADE THIS RULE, and why it is
	// specified from source with a named missing vector (DEC-1 section 8 item
	// 3d) rather than left to a phrase.
	//
	// Because a rate factor is a small number (of order 0.005 to 0.02), a scale
	// is strictly lossier than the same count of significant digits on this
	// quantity — the leading zeros buy nothing — and the loss reaches a payable
	// amount. Re-derived from source at SignificantDigits 12, HALF_UP, 7% p.a.,
	// 30/360, a 31-day period: the mc-qualified operations alone yield
	// 0.00583333333332 (14 decimal places, 12 significant digits); the trailing
	// setScale then yields 0.005833333333, and 0.005833333333 is the value that
	// must enter the recurrence. Without the quantization the six periods of
	// that schedule carry three DIFFERENT rate factors tracking 31/29/30-day
	// months; with it they collapse to one. The two readings are not a fixed
	// offset apart, they have different shape.
	//
	// An implementation that applies only the significant-digit sense still
	// passes the reference oracle's shipped conformance vector — the difference
	// is absorbed by the currency layer on a 100.00 principal — and then
	// misprices an ordinary loan.
	//
	// RateFactorScale MUST equal SignificantDigits. The oracle derives both
	// from one integer, so a request in which they differ describes a
	// configuration no deployment of the reference oracle can produce and must
	// be rejected with ErrUnsupportedConfiguration. They are nonetheless two
	// fields: one integer with two documented meanings is the defect this pair
	// exists to make unrepeatable, and a captured vector must echo both so it
	// can never be replayed under a policy it was not captured at.
	RateFactorScale int32

	// Mode is the tie-breaking rule for all three layers. One mode, not three.
	//
	// The reference oracle takes every tie rule from one of two places — the
	// threaded MathContext where one is passed, and the tenant-global
	// MathContext where one is not (Money.java:52; Money.java:102-104;
	// Money.java:150-157; Money.java:159-161 and :163-170, whose return path
	// goes through the two-argument Money.of and therefore reads the
	// tenant-global context even though its own division used the threaded
	// one). Independently settable modes would admit combinations no deployment
	// can produce and would double the vector matrix.
	//
	// ADAPTER OBLIGATION, and it is wider than a single call site: the
	// Fineract-JVM adapter MUST initialise the tenant rounding mode to Mode
	// before EVERY call, because every path that constructs Money without an
	// explicit MathContext reads the tenant-global one, and outside an
	// initialised tenant those paths throw IllegalStateException
	// (MoneyHelper.java:74-82).
	//
	// The tenant PRECISION cannot be pinned the same way — it is the
	// compile-time constant 19 (MoneyHelper.java:35). Within the graded domain
	// that is harmless, and the argument is FROM SOURCE, not from a capture
	// (revision 5, P1-T29-2; DEC-1 section 4.1 retired the capture argument in
	// revision 4 and this comment had not followed). Inside the graded domain
	// every Money is constructed through the three-argument Money.of(..., mc)
	// carrying the threaded context, and the Money constructor reads only the
	// ROUNDING MODE from getMc() (Money.java:52), never the precision. The call
	// sites that DO read the tenant-global precision (Money.java:103, :115,
	// :160, :169, :377) all sit on the installment-multiple and
	// multipliedBy(double) paths, and applyInstallmentAmountInMultiplesOf is
	// the identity inside the graded domain
	// (ProgressiveEMICalculator.java:1761-1766), so no reached call site
	// consults it.
	//
	// The earlier justification — a calibration capture threaded at precision
	// 12 on a precision-19 tenant reproducing the oracle's shipped conformance
	// literal — is NOT sufficient on its own and must not be relied on: that
	// 100.00 / 6 * 7% shape is largely precision-insensitive, so reproducing it
	// is weak evidence either way. An implementation must not assume the
	// source argument above survives widening the graded domain.
	Mode RoundingMode
}

// Disbursement is one advance of principal to the borrower.
type Disbursement struct {
	// Date is the civil date on which the principal is advanced.
	//
	// It is ALSO the seed of the month-end date rule, which is why the rule is
	// specified here rather than on GenerateRequest.ScheduleStartDate.
	//
	// # Month-end rule (normative, monthly frequency only)
	//
	// Repayment due dates are produced in two steps:
	//
	//  1. Step: add RepaymentEvery calendar months to the previous boundary,
	//     clamping the day to the target month's length (31 January + 1 month
	//     = 28 or 29 February).
	//  2. Re-anchor: if the frequency is monthly AND the SEED day-of-month is
	//     greater than 28 AND the stepped date's day-of-month is at least 28,
	//     set the day to min(days in the target month, seed day).
	//
	// The seed is THIS field — the disbursement date — not ScheduleStartDate
	// (LoanApplicationTerms.java:583-589 selects the disbursement date as the
	// seed; DefaultScheduledDateGenerator.java:128-131 passes it to the
	// re-anchor at :168-176).
	//
	// The clamped day IS remembered, in the seed. A schedule seeded on 31
	// January therefore returns to the 31st whenever the month is long enough.
	// Observed on the pinned oracle, 6 monthly periods, seed and schedule start
	// 2024-01-31:
	//
	//	2024-02-29, 2024-03-31, 2024-04-30, 2024-05-31, 2024-06-30, 2024-07-31
	//	loan term 182 days
	//
	// and for seed 2024-01-30:
	//
	//	2024-02-29, 2024-03-30, 2024-04-30, 2024-05-30, 2024-06-30, 2024-07-30
	//	loan term 182 days
	//
	// An implementation that merely clamps and forgets returns 2024-03-29 for
	// the second period of the first schedule and a loan term of 180 days.
	// Month-end disbursement is routine in retail lending; this is not an edge
	// case. Graded by two captures (seed day 31 and seed day 30, both spanning
	// a leap February).
	Date CivilDate

	// AmountMinor is the principal advanced, in minor units of
	// GenerateRequest.Currency. It must be > 0.
	//
	// The reference oracle takes a decimal in MAJOR units; converting an
	// integer count of minor units into that decimal is exact, and is the
	// adapter's job. No float may exist at that conversion, in either
	// direction, and no capture harness may route an amount through a
	// floating-point type — the oracle's own Money class exposes double-typed
	// overloads (Money.java:134-148) and its shipped test helper converts
	// through doubleValue (EmbeddableProgressiveLoanScheduleGeneratorTest.java:120-122),
	// both of which are traps for a harness author rather than parts of the
	// calculation.
	AmountMinor int64
}

// GenerateRequest is the complete input to schedule generation. Two
// implementations given an equal GenerateRequest must return an equal Schedule.
//
// Every field changes the numeric output. Anything a schedule can be generated
// without — the borrower, the loan account, the product catalogue, charges,
// taxes, ledger accounts, business dates, tenants — is absent by design.
//
// The Go zero value of GenerateRequest is invalid: every enum has an
// Unspecified zero value, every Rate requires a positive denominator, and every
// CivilDate requires a real date. A request that was never populated therefore
// fails loudly rather than defaulting to some implementation's idea of normal.
//
// # The graded domain
//
// A request is in the GRADED DOMAIN when all of the following hold. Outside it,
// an implementation must return ErrNoDiscriminatingVector (or, where the
// oracle cannot answer at all, ErrUnsupportedConfiguration) rather than a
// number:
//
//	Currency.MinorUnitDigits          == 2
//	Rounding.SignificantDigits        == 19
//	Rounding.RateFactorScale          == 19
//	Rounding.Mode                     == RoundingHalfUp
//	len(Disbursements)                == 1
//	RepaymentEvery                    == 1
//	RepaymentFrequencyUnit            == FrequencyMonths
//	InterestMethod                    == InterestMethodDecliningBalance
//	DayCount                          == DayCountFixed30Over360
//	DownPaymentPercentage             == Rate{0, 1}
//	InstallmentRoundingMultipleMinor  == 0
//	ScheduleStartDate <= Disbursements[0].Date < the last repayment DueDate
//
// NumberOfRepayments >= 1 was listed here in revision 3 and is NOT a
// graded-domain predicate (revision 4, P2-T26-1): it is a WELL-FORMEDNESS
// condition, so NumberOfRepayments < 1 is ErrInvalidRequest, which by the
// precedence rule on the error variables below wins over any graded-domain
// refusal. This list and the one in DEC-1 section 3.1 are now identical.
// NumberOfRepayments == 1 is well formed and inside the graded domain; note
// that the EMI re-adjust loop (see Period) cannot fire on a one-period
// schedule, because getEmiAdjustment's scan requires idx > 0
// (ProgressiveEMICalculator.java:1779) and the degenerate branch at :1788
// yields a zero emiDifference. Revision 5 corrects the SUFFICIENT CONDITION
// (P0-T29-1): what makes the pair degenerate is that the RELATED repayment
// period list holds a single element, which NumberOfRepayments == 1 implies
// but does not exhaust — a disbursement dated on repayment period N-1's due
// date leaves one related period on a schedule of any length, and is equally
// degenerate. See Period for the definition of the related periods.
//
// The last predicate is SEMANTIC, not a static field comparison (added in
// revision 3, P0-2). The last repayment due date is derived from
// ScheduleStartDate, NumberOfRepayments, RepaymentEvery, the frequency and the
// month-end rule (see Disbursement.Date) — all of which an implementation
// already computes — so the predicate is checkable without asking the oracle. A
// single disbursement dated BEFORE ScheduleStartDate, or ON OR AFTER the last
// computed due date, is silently discarded by the reference oracle into an
// all-zero schedule (no disbursement row, no amortized principal;
// ProgressiveLoanScheduleGenerator.java:305-308 with isMultiDisburseLoan()
// false). Rather than reproduce that degenerate answer, such a request is
// OUTSIDE the graded domain and must be refused with ErrNoDiscriminatingVector,
// matching the standing "refuse rather than guess" disposition. When
// multi-tranche vectors later exist this window widens with no amendment.
//
// AnnualNominalInterestRate, the principal, the dates and NumberOfRepayments
// are continuous or unbounded inputs; a corpus cannot enumerate them, so they
// are graded by sampling rather than by enumeration. The Run-1 corpus samples
// terms of 6, 12, 18 and 36 monthly installments; rates of 7.0%, 16.8%, 18.5%
// and 21.6%; principals of 100, 1,200,000, 4,999,999, 5,000,000, 50,000,000 and
// 87,654,321 major units in USD and MNT; schedule starts on the 1st, the 30th
// and the 31st of a month; and one schedule whose disbursement falls on a later
// repayment due date. No claim is made that any un-sampled value is safe — see
// Rounding.SignificantDigits on why loan size in particular licenses nothing.
//
// # Pinned oracle inputs (normative, and an obligation on the Go module)
//
// The Fineract-JVM adapter must construct a 19-component input record. Six of
// those components have no counterpart in this contract, and the Go module must
// behave exactly as if these constants held:
//
//	allowFullTermForTranche               = false
//	allowPartialPeriodInterestCalculation = true
//	interestRecognitionOnDisbursementDate = false
//	fixedLength                           = null
//	daysInYearCustomStrategy              = null
//	currency.inMultiplesOf                = null
//	(and interestCalculationPeriodMethod is left unset, which the seam's
//	 assembler never populates, LoanApplicationTerms.java:579-607)
//
// Each pin, with the reason it is safe — the reasons matter, because a future
// reader will use them to decide whether a pin can be relaxed:
//
//   - allowFullTermForTranche = false is a REAL BEHAVIOURAL PIN, not a dead
//     field. Its Builder setter is reached (LoanApplicationTerms.java:606, copied
//     out at :348) and the guard that consumes it never consults multi-disbursement
//     at all: isAllowFullTermForTranche() && numberOfRepayments > 0 &&
//     action == DISBURSEMENT (ProgressiveEMICalculator.java:142-144). Setting it
//     true on an ordinary single disbursement routes into a full re-amortization
//     through a synthetic terms object and a temporary schedule model (:155-174).
//     Fineract forbids the combination only at PRODUCT validation, a layer this
//     entry point does not pass through. Graded: two captures differing only in
//     this flag were taken at (19, HALF_UP) and are identical, so on this shape
//     the alternative path coincides — which is a measurement, not a licence to
//     ignore the flag.
//   - allowPartialPeriodInterestCalculation = true is inert here, but NOT for
//     the reason a reader might guess. Its only calculation-path uses
//     (ProgressiveEMICalculator.java:130 and the interest-period variant) sit
//     behind a guard that first requires interestCalculationPeriodMethod to be
//     non-null and same-as-repayment-period (:128-130). That field has no
//     initialiser and is never set by the seam's assembler, so it is null and
//     the branch short-circuits.
//   - interestRecognitionOnDisbursementDate = false shifts the year-end
//     fraction boundary and is reachable only on the actual/actual arm, which is
//     outside the graded domain.
//   - fixedLength = null is a real pin: a non-null value overrides the final
//     due date (DefaultScheduledDateGenerator.java:61-66, :108-111, :184-189).
//   - daysInYearCustomStrategy = null is PROVABLY inert within the graded
//     domain, twice over. It has TWO effects, and revisions 1-4 stated only the
//     first (revision 5, P1-T29-1). (a) It substitutes a 365/366-day year for a
//     period containing 29 February, which requires the year length to be 366
//     in the first place (ProgressiveEMICalculator.java:1346-1352); under a
//     fixed 360-day year it never is. (b) Under FEB_29_PERIOD_ONLY it is the
//     third conjunct of partialPeriodCalculationNeeded (:1505-1507), so it
//     SUPPRESSES the cross-year partial-period calculation for any period
//     containing no 29 February, sending that period back through the day-count
//     switch at :1533 — an effect on periods that have nothing to do with 29
//     February. Both effects are gated on daysInYearType == ACTUAL and are
//     therefore unreachable under DayCountFixed30Over360; the oracle also
//     rejects the field at product creation unless days-in-year is ACTUAL
//     (LoanProduct.java:462-472). Effect (b) is why the FrequencyYears note on
//     RepaymentFrequencyUnit holds only while this field is null.
//     It is NOT inert in general — through a running server, at a daily interest
//     calculation with an actual/actual year, FEB_29_PERIOD_ONLY moves all
//     twelve periods of a one-year schedule — so it becomes a contract question
//     the moment DayCountActualActual enters the graded domain, and not before.
//     Note also that the seam this contract's corpus is captured through drops
//     this field silently, so no Path-A capture could ever grade it.
//   - currency.inMultiplesOf = null is inert because the oracle applies it only
//     when the currency has zero decimal places (Money.java:48-51) and MNT has
//     two. It was measured to move money at zero decimal places, which is a
//     second reason Currency.MinorUnitDigits is pinned to 2 in the graded
//     domain. It is a different thing from InstallmentRoundingMultipleMinor.
//
// Also absent, and never to be added here: borrower or party identity of any
// kind, loan or account identifiers, product references, tenant identifiers,
// business dates, charges, taxes, ledger accounts, and any notion of insurance,
// protection or guarantee.
type GenerateRequest struct {
	// TimeZone is the IANA zone name in which every CivilDate in this request
	// and in the resulting Schedule is interpreted as a calendar day, and in
	// which the loan's due days are reckoned. Mongolia uses "Asia/Ulaanbaatar"
	// (UTC+08) and "Asia/Hovd" (UTC+07), neither of which observes daylight
	// saving time; Gerege operates in both.
	//
	// It must be an IANA zone name. A fixed offset ("+08:00", "UTC+8", "GMT+8")
	// is invalid and must be rejected with ErrInvalidRequest: an offset literal
	// encodes a fact about a zone into a field that should name the zone.
	//
	// The generation arithmetic itself is zone-free civil-date arithmetic, and
	// no capture can discriminate this field — deliberately so. It is carried
	// so that no caller can smuggle an implicit offset across the boundary and
	// so that downstream contexts (aging, COB, delinquency) inherit an explicit
	// zone rather than guessing one. Measured rather than assumed: the same
	// four server-path captures were re-taken on a tenant whose zone was
	// changed to Asia/Ulaanbaatar and came back byte-identical, because every
	// date in them is an explicit civil date. That equivalence will NOT hold
	// for any later operation that depends on "today".
	TimeZone string

	// Currency denominates every ...Minor field in this request and in the
	// resulting Schedule, and supplies the currency rounding layer's scale.
	Currency Currency

	// Rounding is the precision and tie-breaking policy under which the whole
	// schedule is computed. See Rounding.
	Rounding Rounding

	// ScheduleStartDate is the civil date from which repayment period
	// boundaries are stepped: the first repayment period runs from this date,
	// and the nth period's due date is this date advanced by n * RepaymentEvery
	// units of RepaymentFrequencyUnit, subject to the month-end rule specified
	// on Disbursement.Date.
	//
	// It is a separate input from Disbursement.Date, and the separation is real
	// rather than decorative: the two reach different places in the reference
	// oracle. This date becomes the schedule generation start
	// (ProgressiveLoanScheduleGenerator.java:94-96 resolves the period start to
	// it, since the seam never sets a repayment-start-date type), while the
	// disbursement date becomes the month-end seed. It is also the anchor from
	// which the loan's term in days is measured: the oracle measures term as
	// the span from the FIRST period's from-date to the LAST period's due date,
	// so a loan disbursed after its schedule starts still reports a term
	// measured from the schedule start.
	//
	// Graded: one capture separates them (schedule start 2024-01-01,
	// disbursement 2024-02-01), and it reports a 182-day term measured from
	// 2024-01-01 with a first repayment period that is entirely zero.
	ScheduleStartDate CivilDate

	// Disbursements are the advances of principal, ordered ascending by Date.
	//
	// This is a slice, not a scalar pair, although exactly one element is
	// currently legal: a request carrying zero or more than one element must be
	// rejected with ErrUnsupportedConfiguration. Multi-tranche disbursement is
	// already-built oracle behaviour merely unreachable from this entry point
	// (the seam's assembler hands it a fixed empty list at
	// LoanApplicationTerms.java:600, and the generator then synthesises exactly
	// one tranche from the expected disbursement date and the principal at
	// ProgressiveLoanScheduleGenerator.java:285-292), and it arrives with the
	// loan lifecycle. Widening a cardinality is a value-domain change; turning
	// a scalar into a list later would be a shape change invalidating every
	// captured vector.
	Disbursements []Disbursement

	// NumberOfRepayments is the count of repayment installments in the loan
	// term. It must be >= 1; a value below 1 is not well formed and is
	// ErrInvalidRequest, not a graded-domain refusal (revision 4, P2-T26-1). A
	// down-payment period, if any, is not counted here.
	NumberOfRepayments int32

	// RepaymentEvery is the step multiplier: a repayment falls due every
	// RepaymentEvery units of RepaymentFrequencyUnit. It must be >= 1. Monthly
	// repayment is RepaymentEvery 1 with FrequencyMonths.
	//
	// Graded domain: 1. It is kept separate from the unit so that "every 2
	// weeks" needs no new enum member, and it enters the interest fraction
	// directly (ProgressiveEMICalculator.java:1956-1958), so a value other than
	// 1 changes every period's interest and needs its own vector.
	RepaymentEvery int32

	// RepaymentFrequencyUnit is the calendar unit stepped by RepaymentEvery. It
	// also determines which day-count expansion the interest fraction uses. See
	// RepaymentFrequencyUnit.
	//
	// The reference oracle takes this as a String and parses it by name — a
	// stringly-typed input this contract refuses to inherit.
	RepaymentFrequencyUnit RepaymentFrequencyUnit

	// AnnualNominalInterestRate is the nominal annual rate as a dimensionless
	// fraction: 24% per annum is Rate{24, 100}. It is nominal, not effective:
	// the conversion to a per-period fraction is performed by DayCount and
	// RepaymentFrequencyUnit, not by compounding this value.
	//
	// Explicitly a FRACTION, not the reference oracle's percentage-shaped
	// decimal where 7.0 means 7% — that shape has produced a factor-of-100
	// error in every system that has ever carried it. The oracle divides the
	// percentage by 100 under its own rounding policy
	// (ProgressiveEMICalculator.java:1318-1320); a Rate reaches that arithmetic
	// with zero prior loss.
	//
	// Zero interest is Rate{0, 1} and is not special-cased by the algorithm:
	// every rate factor is 0, every growth factor is exactly 1, the recurrence
	// yields exactly the installment count, and the installment is the
	// principal divided by that count. It is nonetheless outside the graded
	// domain, because no capture exercises it.
	AnnualNominalInterestRate Rate

	// InterestMethod selects how interest is derived from the balance. See
	// InterestMethod.
	InterestMethod InterestMethod

	// DayCount selects the day-count convention converting
	// AnnualNominalInterestRate into a per-period interest fraction. See
	// DayCountConvention.
	//
	// One consistency result worth recording, because it is what lets a capture
	// taken through the embeddable seam and a capture taken through a running
	// server grade the same contract: for MONTHLY repayment, and only for
	// monthly, the oracle's 30/360 arm and its same-as-repayment-period arm
	// compute the identical interest fraction — 30 * RepaymentEvery / 360 and
	// RepaymentEvery / 12 are the same rational evaluated at the same
	// precision (ProgressiveEMICalculator.java:1513-1515 versus :1536 through
	// :1922-1927). Observed: a 12-period MNT 1,200,000 loan at 21.6% captured
	// through the seam at 30/360 and through the server at
	// same-as-repayment-period agrees on all twelve periods and all three
	// totals to the minor unit. For WEEKLY repayment the two arms disagree
	// (RepaymentEvery / 52 against 7 * RepaymentEvery / 360), which is one more
	// reason FrequencyWeeks is outside the graded domain.
	DayCount DayCountConvention

	// DownPaymentPercentage is the fraction of the disbursed principal taken as
	// a down payment on the disbursement date. Rate{0, 1} means no down payment
	// and no down-payment period in the response; Rate{1, 10} means 10%. It
	// must be >= 0 and < 1.
	//
	// A non-zero value adds a PeriodKindDownPayment row to the response and
	// reduces the principal amortized across the repayment periods
	// (ProgressiveLoanScheduleGenerator.java:331-351). It is a single field: the
	// oracle carries both a boolean and a percentage, admitting the
	// contradictory state "enabled at 0%", and its own shipped fixture derives
	// the boolean from the percentage anyway.
	//
	// The request must be able to ask for a down payment because the response
	// must be able to describe one; but a non-zero value is outside the graded
	// domain — refuse with ErrNoDiscriminatingVector. Every capture in the
	// Run-1 corpus has down payments disabled, so no vector has ever produced a
	// PeriodKindDownPayment row, and the down-payment path additionally reaches
	// a rounding call site this contract has pinned away (the multiple-rounding
	// of the down payment at ProgressiveLoanScheduleGenerator.java:335-338).
	DownPaymentPercentage Rate

	// InstallmentRoundingMultipleMinor rounds the level installment (and the
	// down payment, if any) to a whole multiple of this many minor units.
	// 0 means no such rounding. A Mongolian retail product rounding
	// installments to whole 100 ₮ sets this to 10000.
	//
	// # Semantics (normative, and stated here because they are counter-intuitive)
	//
	//   - The installment is rounded to the NEAREST multiple under
	//     Rounding.Mode. It is NOT raised to the next multiple and NOT floored.
	//     The oracle divides by the multiple at scale 0 under the rounding mode
	//     and multiplies back (Money.java:163-170, reached from
	//     ProgressiveEMICalculator.java:1770-1776 via :1761-1766). Observed
	//     rounding DOWN on a running oracle: principal MNT 1,190,000 with a
	//     multiple of 100 major units takes an unrounded installment of
	//     111,148.35 to an applied installment of 111,100.00.
	//   - There is a ZERO GUARD: if rounding would take a positive installment
	//     to zero, the UNROUNDED installment is used instead
	//     (ProgressiveEMICalculator.java:1772-1774). So the rounding is not
	//     unconditional.
	//   - The rounded installment is the installment for every period except
	//     the last, which absorbs the residual as usual (see Period). The last
	//     period's total is therefore deliberately NOT a multiple.
	//   - The tie rule for this rounding comes from the TENANT-GLOBAL context,
	//     not from the threaded one (the two-argument
	//     Money.roundToMultiplesOf at Money.java:159-161), which is why
	//     Rounding.Mode carries the adapter obligation it does.
	//   - The EMI re-adjust smoothing loop also runs afterwards
	//     (ProgressiveEMICalculator.java:1258-1308) and CAN absorb a
	//     multiple-rounding difference entirely — observed converging two
	//     different rounding modes to one identical schedule. But that loop is
	//     NOT specific to installment rounding: it fires on every ordinary
	//     generation and its guard has no dependence on this field. It is a
	//     Go-module obligation in its own right, specified normatively on Period,
	//     NOT here — do not read it as conditional on a non-zero multiple.
	//
	// # Representable domain
	//
	// The oracle's counterpart is a whole number of MAJOR units, not minor
	// units. So the value must be 0, or a positive exact multiple of
	// 10^Currency.MinorUnitDigits; 5000 (50.00 ₮) and 1 (0.01 ₮) have no
	// representation the adapter can render and must be rejected with
	// ErrUnsupportedConfiguration rather than silently rounded or dropped.
	//
	// # Grading
	//
	// Outside the graded domain: a non-zero value must be refused with
	// ErrNoDiscriminatingVector. Run-1 products launch without installment
	// rounding. The seam this corpus is captured through DROPS this field
	// silently — it has no Builder setter at all
	// (LoanApplicationTerms.java:217, :579-607) — so no Path-A capture can ever
	// grade it, and a port that honours it and a port that ignores it score
	// identically. A running server does honour it (four server-path captures
	// exist in which a multiple of 100 major units moves all twelve periods),
	// and when those captures become admissible vectors this value can enter
	// the graded domain with no contract amendment.
	//
	// The field stays in the contract regardless, for two reasons: rounding
	// installments to whole 100 ₮ is an ordinary Mongolian product feature and
	// a contract that cannot express it is wrong for this market; and it
	// changes the value of every row, so it could never be layered on later
	// without re-capturing every vector.
	InstallmentRoundingMultipleMinor int64
}

// PeriodKind discriminates the three kinds of row a schedule contains.
type PeriodKind int32

const (
	// PeriodKindUnspecified is the zero value and never appears in a response.
	PeriodKindUnspecified PeriodKind = iota

	// PeriodKindDisbursement is an advance of principal to the borrower. Its
	// FromDate and DueDate are both the disbursement date, its PrincipalMinor
	// is the amount advanced, its InterestMinor is 0, and its
	// InstallmentNumber is 0 because it is not payable.
	//
	// Its OutstandingPrincipalMinor IS THE AMOUNT ADVANCED — equal to this row's
	// PrincipalMinor (normative; revision 6, P1-T32-2). The reference oracle
	// passes disbursementPeriod.getPrincipalDisbursed().getAmount() as BOTH the
	// plan row's principalAmount and its outstandingLoanBalance
	// (LoanSchedulePlan.java:52-56; the record's field order is
	// LoanSchedulePlanDisbursementPeriod.java:28-31). Every committed capture
	// contains a disbursement row, so this is GRADED. Revision 5 fixed the other
	// five fields of this row and left this one unstated.
	PeriodKindDisbursement

	// PeriodKindDownPayment is the down payment taken on the disbursement date.
	// Its FromDate and DueDate are both the disbursement date, its
	// PrincipalMinor is the amount taken, and its InterestMinor is 0.
	//
	// Its OutstandingPrincipalMinor is the balance outstanding immediately
	// before the disbursement, plus the amount disbursed, minus the down payment
	// taken — outstandingBalance.plus(disbursedAmount, mc).minus(downPaymentAmount, mc)
	// (ProgressiveLoanScheduleGenerator.java:340-343), carried to the plan at
	// LoanSchedulePlan.java:57-65 (record field
	// LoanSchedulePlanDownPaymentPeriod.java:33). UNGRADED: DownPaymentPercentage
	// is pinned to Rate{0, 1} in the graded domain and no capture has ever
	// produced a row of this kind, so the value is specified from source and
	// refused rather than exercised (revision 6, P1-T32-2).
	//
	// No capture in the Run-1 corpus produces a row of this kind; see
	// GenerateRequest.DownPaymentPercentage.
	PeriodKindDownPayment

	// PeriodKindRepayment is an ordinary scheduled installment.
	PeriodKindRepayment
)

// Period is one row of the generated schedule.
//
// Only quantities that cannot be recomputed from the others are carried. The
// total due for a period is PrincipalMinor + InterestMinor; the level
// installment is that sum on any ordinary repayment row; the remaining total
// repayable is the sum over later rows; the loan term in days is the span from
// the first row's FromDate to the last row's DueDate. None of these is a field,
// because a derived total in the response is a second source of truth that lets
// an implementation be simultaneously right about the split and wrong about the
// sum, and because a derived total's meaning changes silently the moment
// charges are introduced.
//
// # EMI re-adjust smoothing loop (normative, and an obligation on the Go module)
//
// The per-period PrincipalMinor/InterestMinor split depends on the level
// installment, and the level installment is produced by TWO steps that a port
// must both reproduce: the recurrence that yields the raw installment (see
// Rounding), and then a smoothing loop that adjusts it. The loop
// checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods
// (ProgressiveEMICalculator.java:1258-1308, at most three iterations) runs on
// EVERY ordinary generation — it is called at ProgressiveEMICalculator.java:749
// gated on onlyOnActualModelShouldApply, true whenever the schedule model is
// empty, i.e. on the initial disbursement of every loan. It is NOT specific to
// installment rounding and it fires INSIDE the graded domain.
//
// Whether it changes the schedule is decided by its guard
// EmiAdjustment.shouldBeAdjusted (EmiAdjustment.java:31-36), which compares
// |lastEMI - penultimateEMI| * 100 against a Money whose amount is floor(n/2)
// currency units (3.00 for a 6-period loan, 18.00 for 36). Money.copy(double)
// (Money.java:220-222) REPLACES the amount rather than scaling it, so the
// threshold is floor(n/2) units flat and the guard has NO dependence on
// InstallmentRoundingMultipleMinor: it fires whenever the final-period residual
// exceeds floor(n/2)/100 of a currency unit, installment rounding or none.
//
// This moves money on ordinary loans. Observed on the pinned oracle at
// (19, HALF_UP), strictly inside the graded domain (single disbursement on the
// schedule start, RepaymentEvery 1, MONTHS, declining balance, 30/360, no down
// payment, no installment rounding, MNT 2 decimals):
//
//	MNT 1,014,632 / 6 * 7.0%:  oracle level installment 172,574.64;
//	                           no-loop model 172,574.63 (every period shifts).
//	MNT 127,704 / 36 * 16.8%:  oracle total interest 35,746.56;
//	                           no-loop model 35,746.69.
//
// None of the twelve Run-1 captures trips this guard, so the corpus cannot
// catch a port that omits the loop — the exact "passes its corpus and is wrong"
// failure this contract exists to prevent. Reproducing the loop is therefore a
// conformance obligation, not backlog.
//
// ## RELATED REPAYMENT PERIODS — the normative definition (revision 5, P0-T29-1)
//
// Revision 4 parameterised the whole loop by n and then defined n wrongly: it
// said n "inside the graded domain is NumberOfRepayments" and cited
// ProgressiveLoanInterestScheduleModel.java:191-194 — which is the null branch,
// the one branch this call path can never take. n is NOT NumberOfRepayments.
// The notion it depends on is defined here, once.
//
// The RELATED REPAYMENT PERIODS of a generation are the repayment periods whose
// DueDate is NOT BEFORE the effective due date
// (ProgressiveLoanInterestScheduleModel.java:195-197):
//
//	related = [ p in repaymentPeriods : !(p.DueDate < effectiveDueDate) ]
//
// The EFFECTIVE DUE DATE is derived from the single disbursement date D in two
// steps (ProgressiveEMICalculator.java:149-151 -> :250-263):
//
//  1. Find the repayment period CONTAINING D. Membership is [FromDate, DueDate]
//     — inclusive at both ends — for the FIRST repayment period, and
//     (FromDate, DueDate] — from-exclusive, due-inclusive — for every later one
//     (ProgressiveLoanInterestScheduleModel.java:238-245,
//     LoanRepaymentScheduleProcessingWrapper.java:251-254).
//  2. If that period's DueDate EQUALS D, the effective due date is the NEXT
//     period's DueDate; otherwise it is the matched period's own DueDate
//     (ProgressiveEMICalculator.java:252-262). When the matched period is the
//     last one there is no next period — but that is a disbursement on the last
//     due date, which the graded domain excludes and which is refused above.
//
// Writing N = NumberOfRepayments and numbering periods 1..N, inside the graded
// domain:
//
//	disbursement strictly inside period 1   -> related = 1..N,   n = N
//	disbursement on period j's due date     -> related = j+1..N, n = N - j
//	disbursement strictly inside period j>1 -> related = j..N,   n = N - j + 1
//
// Every one of those is inside the graded domain, whose disbursement window is
// ScheduleStartDate <= Disbursements[0].Date < the last repayment DueDate, and
// the second is OBSERVED in the Run-1 corpus (schedule start 2024-01-01,
// disbursement 2024-02-01, MNT 1,200,000 / 6 * 21.6%, which returns installments
// over FIVE periods with repayment row 1 entirely zero).
//
// Three rules follow from the same definition, each stated wrongly or not at all
// in revision 4:
//
//   - THE LEVEL INSTALLMENT IS COMPUTED OVER, AND WRITTEN TO, THE RELATED
//     PERIODS ONLY. calculateEMIOnActualModel is handed relatedRepaymentPeriods
//     (ProgressiveEMICalculator.java:741, list built at :732) and the declining
//     balance variant takes its starting balance from that list's first element
//     and writes the installment back onto that list only (:1722-1741). Rows
//     before the first related period keep a ZERO installment and produce an
//     all-zero row — which is exactly the observed row above.
//   - THE TRIAL REBUILD OVERWRITES THE RELATED PERIODS ONLY (step 6), not "all
//     n periods".
//   - uncountablePeriods IS COUNTED OVER THE RELATED LIST (step 3), not over the
//     whole schedule.
//
// ## What the loop DOES (normative; revision 4, P0-T26-1; n corrected in revision 5)
//
// Revision 3 stated only WHEN the loop fires. That is not enough to determine
// money: two loop bodies consistent with everything revision 3 said return
// different installments on the majority of in-graded-domain shapes where the
// guard fires. The body is therefore specified here, step by step, each step
// with its source. All quantities are int64 MINOR UNITS.
//
// n is the number of RELATED REPAYMENT PERIODS as defined immediately above —
// relatedRepaymentPeriods.size() (EmiAdjustment.java:54-56, list at
// ProgressiveEMICalculator.java:732, passed at :749). n == NumberOfRepayments IF
// AND ONLY IF the disbursement falls strictly inside the first repayment period;
// otherwise n is strictly smaller.
//
// rows is the schedule as it stands after the level installment and the
// final-period residual have been applied, INDEXED OVER THE RELATED PERIODS,
// 0-based: rows[0] is the first related period and rows[n-1] the last repayment
// period of the schedule. Rows before the first related period carry a zero
// installment, take no part in the loop, and are never overwritten by it.
//
//	adjustCounter := 1                                        // :1262
//	loop {                          // do { … } while (adjustCounter <= 3)  :1265, :1307-1308
//
//	  // 1. The pair the adjustment is measured on.       :1266 -> :1778-1785
//	  //    getEmiAdjustment scans from the END for the last ADJACENT pair in
//	  //    which NEITHER period is fully paid. Nothing is paid on a schedule
//	  //    this contract generates, so that pair is (n-2, n-1).
//	  if n < 2 { break }        // the scan at :1779 requires idx > 0, so n == 1
//	                            // falls to the degenerate branch :1788, whose
//	                            // emiDifference is copy(0.0) == 0. n == 1 is NOT
//	                            // the same as NumberOfRepayments == 1: a
//	                            // disbursement on period N-1's due date leaves
//	                            // one related period on a schedule of any length.
//	  original      := rows[n-2].emi        // the PENULTIMATE installment  :1781, :1784
//	  emiDifference := rows[n-1].emi - original                 // SIGNED   :1783
//
//	  // 2. Guard — ALL THREE conjuncts.    :1267-1269, EmiAdjustment.java:31-36
//	  lowerHalf := n / 2                    // integer division = floor(n/2)  EmiAdjustment.java:32
//	  if !( lowerHalf > 0                                     // EmiAdjustment.java:33
//	        && emiDifference != 0                             // EmiAdjustment.java:33
//	        && abs(emiDifference)*100 > lowerHalf*10^MinorUnitDigits ) {  // :34-35
//	      break
//	  }
//
//	  // 3. Adjustment magnitude.   EmiAdjustment.java:38-40, Money.java:352-358, :52
//	  uncountablePeriods := count(i in 0..n-1 : rows[i].totalPaid > original)
//	                            // :2027-2031, argument at :1785 — counted over the
//	                            // RELATED list, NOT the whole schedule (P0-T29-1).
//	                            // == 0 on every schedule this contract generates
//	  d := max(1, n - uncountablePeriods)   // == n in the graded domain  EmiAdjustment.java:39
//	  adjustment := emiDifference / d, rounded to a whole minor unit under Rounding.Mode
//	             //  = sign(emiDifference) * (2*abs(emiDifference) + d) / (2*d)
//	             //    [integer division; HALF_UP = nearest, ties away from zero]
//
//	  // 4. Candidate level installment.               EmiAdjustment.java:42-44
//	  adjusted := original + adjustment
//	  adjusted  = applyInstallmentAmountInMultiplesOf(adjusted)  // :1270 -> :1761-1766;
//	                            // the IDENTITY inside the graded domain, where
//	                            // InstallmentRoundingMultipleMinor is 0
//
//	  // 5. Break when the candidate is not a change.               :1271-1273
//	  if adjusted == original { break }
//
//	  // 6. TRIAL schedule, built on a copy — never in place.       :1274-1288
//	  //    `adjusted` is written onto exactly the RELATED periods (:1279-1286:
//	  //    from-date not before the first related period's from-date AND due-date
//	  //    not before its due-date, candidate not below the period's paid amount,
//	  //    period not a re-aged early-repayment holder) — that is the n rows of
//	  //    `rows` and NOT the whole schedule (P0-T29-1, revision 5). Rows before
//	  //    the first related period are NOT overwritten and keep their zero
//	  //    installment. Balances are then recomputed (:1287) and the final-period
//	  //    residual re-applied (:1288 -> :1160-1219).
//	  trial := split(principal, rateFactors, level = adjusted)  // the per-period
//	                            // split specified below, applied to the related periods
//	  applyFinalPeriodResidual(trial)
//
//	  // 7. ADOPTION TEST — strict; failure DISCARDS the trial.     :1289-1291,
//	  //                                             EmiAdjustment.java:46-48
//	  newDifference := trial[n-1].emi - trial[n-2].emi
//	  //  The oracle re-measures with getEmiAdjustment over the trial model's FULL
//	  //  period list (:1289), not the related sublist; because nothing is paid the
//	  //  scan at :1779-1785 returns the last ADJACENT pair of the whole schedule,
//	  //  which for n >= 2 is the last two RELATED rows — the pair written above.
//	  //  Only |newDifference| is read here, so the differing list does not matter.
//	  if !( abs(newDifference) < abs(emiDifference) ) { break }  // keep rows UNCHANGED
//
//	  // 8. Adopt, then bound the iteration.                        :1293-1306
//	  rows = trial
//	  adjustCounter++
//	  if adjustCounter > 3 { break }                               // :1307-1308
//	}
//
// Eight things an implementation can get wrong while still satisfying every
// sentence of revision 3 (the eighth, while still satisfying revision 4):
//
//  1. THE DIVISOR IS n, NOT 1. The gap is spread across all related periods
//     (EmiAdjustment.java:39), so the level installment moves by roughly 1/n of
//     it per iteration; it does NOT absorb the whole gap. uncountablePeriods is
//     a payment-history term (ProgressiveEMICalculator.java:2027-2031),
//     identically zero here, written into the rule so the rule stays true when
//     payment history enters the contract.
//  2. THE ADJUSTMENT IS ROUNDED TO A WHOLE MINOR UNIT, AND IS SIGNED.
//     Money.dividedBy(long) (Money.java:352-358) divides at the threaded
//     MathContext and the Money constructor then re-scales to the currency's
//     decimal places under the same mode (Money.java:52). The integer form above
//     reproduces both steps for every amount this contract can express: the
//     quotient is a rational with denominator d <= n, so it either sits exactly
//     on a half-minor-unit boundary (both forms then round away from zero under
//     HALF_UP) or lies at least 1/(2n) of a minor unit from one — far outside the
//     SignificantDigits-19 intermediate error for any |emiDifference| below
//     10^17/n minor units. The form is written for HALF_UP, the only mode in the
//     graded domain. dividedBy also short-circuits at d == 1 (Money.java:353-355),
//     which the integer form matches.
//  3. THE TRIAL IS A REBUILD, NOT A PATCH. Every related period gets the
//     candidate installment and the whole schedule is recomputed from it —
//     balances (:1287), then the residual (:1288). Moving the level installment
//     and leaving the per-period split alone is wrong.
//  4. THE ADOPTION TEST IS STRICT AND ITS FAILURE DISCARDS. hasLessEmiDifference
//     is |newDiff| < |oldDiff| (EmiAdjustment.java:46-48); equality is NOT
//     adoption. On failure the loop breaks at :1290 BEFORE the copy-back at
//     :1293-1305, so the live schedule keeps its PRE-TRIAL values. This single
//     omission changes the money returned on most shapes where the guard fires.
//  5. break MEANS STOP. All four exits — degenerate pair, guard, no-change,
//     failed adoption — terminate the loop; none skips to the next iteration.
//  6. AT MOST THREE ITERATIONS, AND THE COUNTER ADVANCES ONLY ON ADOPTION.
//     adjustCounter starts at 1 (:1262), is incremented only after a trial is
//     adopted (:1307), and is tested by while (adjustCounter <= 3) at :1308.
//  7. THE ONLY STATE CARRIED BETWEEN ITERATIONS IS rows. The oracle reuses one
//     deep copy (:1274-1276) and copies adopted values back (:1293-1306), so the
//     two models agree at the top of every iteration; inside the graded domain
//     the trial is fully determined by (principal, rateFactors, adjusted), and no
//     port needs the copy machinery.
//  8. n IS THE RELATED-PERIOD COUNT, AND A PORT THAT READS NumberOfRepayments
//     RETURNS DIFFERENT MONEY (revision 5, P0-T29-1). Both the guard threshold
//     floor(n/2) and the divisor max(1, n - uncountablePeriods) read n, so a
//     wrong n changes WHETHER the loop fires AND BY HOW MUCH it moves the
//     installment; the trial's overwrite set moves with it as well. Isolating n
//     alone — identical rebuild semantics in both arms — over 120,000 random
//     in-graded-domain requests with the disbursement on period 1's or period 2's
//     due date, 2,143 (1.79%) return different money, in total interest as well
//     as in the per-period split. That count is a RE-DERIVATION from source over
//     synthetic shapes, not a capture, and must never be promoted to the vector
//     store; the shape class itself, however, IS observed in the corpus, so this
//     is not a hypothetical region of the graded domain.
//
// SPECIFIED BUT UNGRADED. No Run-1 capture trips the guard, none separates the
// adoption test, and none exercises the loop in the later-disbursement window,
// so conformance cannot yet detect a wrong body. No conformance PASS for this
// context may be read as evidence that a port implements this rule; see the
// capture obligation in DEC-1 section 8 items 3, 3a, 3b and 3c.
//
// EXACT-INTEGER ARITHMETIC, NEVER A FLOAT. Math.floor(n/2.0) and the
// BigDecimal.valueOf(double) inside Money.copy(double) operate on values that
// are always exact small integers (floor(n/2) and 0.0). A Go port reproduces
// the guard with integer arithmetic — n/2 in int, compared as
// |lastEMI - penultimateEMI| * 100 > floor(n/2) * 10^MinorUnitDigits in int64
// minor units — and every step of the body above is stated in whole minor units
// for the same reason. The doubles in the Java source are an artefact of the
// reference implementation and MUST NOT be reproduced as float32/float64/
// big.Float here; a float on a money path is a non-negotiable rejection.
//
// # The per-period interest computation (normative; revision 5, P0-T29-2)
//
// Revisions 1-4 said only that "interest is computed first and capped at the
// installment; principal is the balancing non-negative remainder". They NEVER
// SAID HOW THE INTEREST IS PRODUCED: the multiplication by the rate factor was
// never written down, the point at which the quantity becomes money was never
// written down, and the order of operations was delegated to "the order the
// reference oracle performs them" — the one thing an implementer reading only
// this contract cannot see. The oracle's arithmetic and the textbook
// balance * rateFactor an implementer would otherwise write return DIFFERENT
// MONEY on 699 of 43,992 (1.59%) in-graded-domain shapes, and all thirteen
// committed observations are consistent with BOTH readings, so the corpus is
// entirely blind to the difference. (That count is a re-derivation from source
// over synthetic shapes, not a capture.) This section removes the ambiguity; it
// is a conformance obligation on the Go module.
//
// ## The interest of one interest period
//
// A repayment period is partitioned into one or more INTEREST PERIODS. It is
// created carrying exactly one, spanning its whole window
// (RepaymentPeriod.java:149). A balance change on date D inside the period is
// then registered like this (ProgressiveLoanInterestScheduleModel.java:251-262,
// :264-296, :439-442):
//
//   - if some interest period already ENDS EXACTLY ON D, no split occurs and the
//     amount is recorded on that interest period (:275-277);
//   - otherwise the interest period containing D has its DueDate moved back to D
//     (clamped into its own window) and receives the amount, and a NEW interest
//     period [D, the original DueDate] is inserted after it (:280-296).
//
// The amount enters the balance of the LATER segment, never the earlier one
// (InterestPeriod.java:168-188, the plus(disbursementAmount) at :174 and :186).
//
// Inside the graded domain the only balance change is the single disbursement,
// so exactly three shapes occur:
//
//	D on period j's FromDate    -> a ZERO-LENGTH [FromDate, FromDate] holding the
//	                               amount, then [FromDate, DueDate] carrying it
//	                               as balance
//	D on period j's DueDate     -> ONE, unchanged; the amount is recorded on it
//	                               and enters period j+1's balance (:169-179)
//	D strictly inside period j  -> [FromDate, D] with a ZERO balance, then
//	                               [D, DueDate] carrying the amount
//
// In every one of the three, every interest period that carries a NON-ZERO
// balance has lengthTillPeriodDueDate == length, and every interest period where
// they differ carries a zero balance and therefore exactly zero interest.
//
// For an interest period, let
//
//   - length = whole days from the INTEREST period's FromDate to its DueDate
//     (InterestPeriod.java:160-162);
//   - lengthTillPeriodDueDate = whole days from the INTEREST period's FromDate
//     to the ENCLOSING REPAYMENT period's DueDate (InterestPeriod.java:164-166);
//   - rateFactorTillPeriodDueDate = the rate factor (see Rounding) computed over
//     the span [interest period FromDate, repayment period DueDate]
//     (ProgressiveEMICalculator.java:641-642 -> :1355-1356).
//
// THE RATE FACTOR IS PRORATED, AND THE DENOMINATOR IS THE REPAYMENT PERIOD, NOT
// THE SPAN (normative; revision 6, P0-T32-1 — the full definitions are on
// Rounding.RateFactorScale under "The two day counts in the ratio"). Written out
// for this call site:
//
//	actualDaysInPeriod     = days(interest period FromDate -> repayment period DueDate)   // :1367-1368
//	calculatedDaysInPeriod = days(repayment period FromDate -> repayment period DueDate)  // :1369-1370
//	rateFactorTillPeriodDueDate =
//	    setScale( (rate * 30 * RepaymentEvery / 360)
//	              * actualDaysInPeriod / calculatedDaysInPeriod, RateFactorScale )        // :1961-1962
//
// so the ratio is 1 ONLY when the interest period opens on the enclosing
// repayment period's FromDate — rows 1 and 2 of the segmentation table above,
// and every shape the corpus samples. On ROW 3, the strictly-inside case, IT IS
// STRICTLY LESS THAN 1 on the segment carrying the balance. The same denominator
// applies to the interest period's own rateFactor (:639-640 -> :1500-1503),
// which the growth factor sums (see Rounding).
//
// Re-derived, NOT OBSERVED — MNT 1,200,000 / 6 x 21.6%, schedule start
// 2024-01-01, single disbursement 2024-01-15. Repayment period 1 is
// [2024-01-01, 2024-02-01], 31 days, splitting into [01-01, 01-15] (zero
// balance) and [01-15, 02-01] (carrying MNT 1,200,000):
//
//	this rule (17/31):        segment rate factor 0.0098709677419354839,
//	                          period-1 interest 11,845.16, level 211,087.95,
//	                          final 211,088.97, total interest 66,528.72
//	the deleted ratio-1 form: segment rate factor 0.0180000000000000000,
//	                          period-1 interest 21,600.00, level 212,786.91,
//	                          final 212,789.26, total interest 76,723.81
//
// — a full month's interest charged on a 17-day exposure. Re-review T32
// re-derived that the two readings diverge on 2,913 of 2,913 (100%)
// strictly-inside-a-period in-graded-domain shapes, worst total-interest gap MNT
// 1,816,050.11. EVERY FIGURE HERE IS A RE-DERIVATION FROM THE PINNED CHECKOUT,
// recorded as a candidate shape to capture (DEC-1 section 8 item 3d), and NONE
// may be promoted to the vector store.
//
// Then, with InterestMethodDecliningBalance (InterestPeriod.java:145-158):
//
//	if lengthTillPeriodDueDate == 0 { interest := 0 }        // :146-148, exactly zero
//	else {
//	  B  := the OUTSTANDING PRINCIPAL BALANCE carried into this interest period  // :151
//	  t1 := round_mc( B  * rateFactorTillPeriodDueDate )     // :155  operation (1)
//	  t2 := round_mc( t1 / lengthTillPeriodDueDate    )      // :156  operation (2)
//	  t3 := round_mc( t2 * length                     )      // :157  operation (3)
//	  interest := t3
//	}
//
// where round_mc is rounding to Rounding.SignificantDigits SIGNIFICANT DIGITS
// under Rounding.Mode — the same MathContext sense documented on Rounding —
// applied SEPARATELY TO EACH OF THE THREE OPERATIONS, IN THAT ORDER.
//
// OPERATIONS (2) AND (3) CANCEL ALGEBRAICALLY AND DO NOT CANCEL NUMERICALLY.
// As shown above, inside the graded domain lengthTillPeriodDueDate == length on
// every interest period that carries a balance, so "/ L * L" is the identity in
// exact arithmetic — and is NOT the identity once each step is rounded to 19
// significant digits. A PORT MUST PERFORM ALL THREE. Collapsing them to
// round_mc(B * rateFactor) is the divergence measured above; dropping only the
// rounding between them is the same defect in a different disguise.
//
// ## From interest period to row
//
//  1. SUM, THEN MAKE IT MONEY. A repayment period's calculated due interest is
//     the sum of its interest periods' t3 values, converted to money exactly
//     once — Money.of(currency, sum, mc), whose constructor applies
//     setScale(Currency.MinorUnitDigits, Rounding.Mode)
//     (RepaymentPeriod.java:252-257, Money.java:40-53, scale at :52) — and
//     clamped at zero (RepaymentPeriod.java:264). The sum happens BEFORE the
//     currency-scale rounding, not after: rounding each interest period to the
//     minor unit and then adding is a different function.
//  2. CAP AT THE INSTALLMENT. InterestMinor = min(calculated due interest, the
//     period's installment) (RepaymentPeriod.java:272-286, the min at :280).
//  3. PRINCIPAL IS THE BALANCING NON-NEGATIVE REMAINDER.
//     PrincipalMinor = max(0, installment - InterestMinor) (:345-350).
//  4. ROLL THE BALANCE FORWARD, CLAMPED AT ZERO. OutstandingPrincipalMinor =
//     max(0, balance carried in + amounts disbursed in this period -
//     PrincipalMinor) (:389-403, the clamp at :399). That clamp is why
//     OutstandingPrincipalMinor is carried rather than derived.
//  5. THE FINAL PERIOD'S INSTALLMENT IS THEN ADJUSTED BY THE RESIDUAL and its
//     SPLIT RECOMPUTED FROM STEPS 2-4. The order is: split every row, then
//     absorb the residual — never the reverse. (Revision 6, P2-T32-1: revision 5
//     said "its principal recomputed from step 3", which understates the
//     recomputation. getDueInterest is memoised on the period's emi
//     (RepaymentPeriod.java:272-286), so a residual that moved the installment
//     re-evaluates the CAP at step 2 as well, and the roll-forward at step 4
//     with it. T32 measured that the cap never actually bites on the final row
//     over 1,500 in-graded-domain schedules — a re-derivation, not an
//     observation — so this is editorial precision, not a money change; a port
//     that recomputes only the principal is nonetheless under-specified.)
//
// EXACT ARITHMETIC, NEVER A FLOAT. B is an int64 count of minor units rendered
// as an exact decimal; rateFactorTillPeriodDueDate is an exact decimal of at
// most Rounding.RateFactorScale fractional digits; length and
// lengthTillPeriodDueDate are exact small integers. Every one of the three
// operations is therefore an exact-decimal operation followed by an explicit
// rounding to a stated number of significant digits, and every one of steps 1-5
// is exact integer arithmetic in minor units. A port MUST use an
// arbitrary-precision decimal (or an exact rational with explicit rounding at
// each of the three points) and never float32, float64 or big.Float — a float on
// a money path is a non-negotiable rejection, and here it would additionally
// destroy the very non-cancellation this section exists to specify.
//
// SPECIFIED BUT UNGRADED, in three places:
//
//   - the DAY-COUNT PRORATION above. No committed observation places a
//     disbursement anywhere but on a repayment-period boundary, so on all
//     thirteen the ratio is 1 either way and the corpus cannot separate this
//     rule from the reading revision 6 deletes. DEC-1 section 8 item 3d.
//   - the STRICTLY-INSIDE-A-PERIOD SEGMENTATION (row 3), the only
//     in-graded-domain shape that gives one repayment period two interest
//     periods. The same capture settles it. DEC-1 section 8 item 3d.
//   - the THREE-OPERATION ROUND-TRIP against the textbook balance * rateFactor.
//     DEC-1 section 8 item 3b.
//
// All three are specified from source and ungraded, on the same terms as the
// loop above: until 3b and 3d land, no conformance PASS for loanschedule may be
// read as evidence that a port implements this section.
type Period struct {
	// Kind discriminates this row. See PeriodKind.
	Kind PeriodKind

	// InstallmentNumber is the payable-installment sequence number: a dense,
	// 1-based counter running across down-payment and repayment rows in order.
	// The reference oracle increments one shared counter for both
	// (ProgressiveLoanScheduleGenerator.java:123, :143 for repayments and :341,
	// :346 for down payments).
	//
	// It is 0 for a PeriodKindDisbursement row, which is not payable and which
	// the oracle leaves null. This is the one place a Java null is normalised,
	// and it is normalised to a value that cannot collide with a real
	// installment number.
	InstallmentNumber int32

	// FromDate is the civil date on which the period opens, interpreted in
	// GenerateRequest.TimeZone. Interest accrues over [FromDate, DueDate) —
	// the window is half-open, which is what decides where a disbursement
	// dated exactly on a due date lands (see Schedule).
	FromDate CivilDate

	// DueDate is the civil date on which the period's amount falls due,
	// interpreted in GenerateRequest.TimeZone.
	DueDate CivilDate

	// PrincipalMinor is this row's principal component, in minor units of
	// GenerateRequest.Currency. It is never negative.
	//
	// For PeriodKindDisbursement it is principal advanced TO the borrower; for
	// the other kinds it is principal repaid BY the borrower. The direction is
	// the row's Kind, never a sign bit, so that no consumer can sum the column
	// without first deciding what it is summing. This is the same discipline
	// the ledger non-negotiable enforces elsewhere.
	//
	// On a repayment row, principal is the BALANCING REMAINDER of the
	// installment after interest, never an independently computed figure:
	// interest is taken first, capped at the installment, and principal is the
	// non-negative remainder (RepaymentPeriod.java:272-286 and :345-350).
	//
	// The interest it balances against is NOT the textbook balance * rateFactor.
	// See "The per-period interest computation" on Period: three separately
	// rounded operations (InterestPeriod.java:145-158) whose middle pair cancels
	// algebraically and not numerically. That section is normative and this
	// field's value is not determined without it.
	PrincipalMinor int64

	// InterestMinor is this row's interest component, in minor units of
	// GenerateRequest.Currency. It is never negative, and it is 0 on
	// PeriodKindDisbursement and PeriodKindDownPayment rows.
	//
	// How it is produced is specified normatively in "The per-period interest
	// computation" on Period — base amount, three separately rounded operations
	// in a fixed order, the single conversion to currency scale, and the cap at
	// the installment. A port that performs balance * rateFactor instead returns
	// different money on ordinary in-graded-domain loans, and no committed
	// observation can tell the two apart (DEC-1 section 8 item 3b).
	InterestMinor int64

	// OutstandingPrincipalMinor is the principal balance remaining after this
	// row is applied, in minor units of GenerateRequest.Currency. It is never
	// negative, and it is 0 on the final row of a fully amortizing schedule.
	//
	// It is carried rather than derived — the one deliberate exception to this
	// contract's "derive what can be derived" rule — because the oracle clamps
	// this roll-forward at zero rather than computing a pure running difference
	// (RepaymentPeriod.java:389-403), so the two are not provably identical in
	// every configuration; and because it is the field against which the
	// per-period amortization invariant is checked without summing the whole
	// schedule. It is observably 0 on a repayment row that falls entirely
	// before the disbursement.
	//
	// "After this row is applied" is defined for EVERY kind of row, not only
	// repayment rows (revision 6, P1-T32-2 — revision 5 left the other two
	// unstated):
	//
	//	PeriodKindRepayment     max(0, balance carried in + amounts disbursed in
	//	                        this period - PrincipalMinor)
	//	                        (RepaymentPeriod.java:389-403, clamp at :399)
	//	PeriodKindDisbursement  the amount advanced, == this row's PrincipalMinor
	//	                        (LoanSchedulePlan.java:52-56)          [GRADED]
	//	PeriodKindDownPayment   balance before the disbursement + amount disbursed
	//	                        - down payment taken
	//	                        (ProgressiveLoanScheduleGenerator.java:340-343)
	//	                                                             [UNGRADED]
	//
	// See the PeriodKind constants for the full citation of each.
	OutstandingPrincipalMinor int64
}

// Schedule is the generated repayment schedule.
//
// It is a struct with one field rather than a bare slice so that the response
// can gain a field in some later ratified version without changing the
// interface's return type.
type Schedule struct {
	// Periods are the schedule's rows in the order specified below. Two
	// Schedules are equal when their Periods are element-wise equal in that
	// order. No map appears in this contract and no map iteration order is ever
	// observable through it.
	//
	// # Ordering (normative)
	//
	// The order REPRODUCES the reference oracle's emitted order rather than
	// imposing a tidier one, because the oracle is this program's fallback and
	// its shadow-parity partner: a boundary that reordered or refused what the
	// oracle emits could not be run against the same traffic, and that is what
	// shadow testing is.
	//
	// Assign each row a window key:
	//
	//   - a PeriodKindRepayment row's key is its own DueDate;
	//   - a PeriodKindDisbursement or PeriodKindDownPayment row's key is the
	//     DueDate of the repayment period whose HALF-OPEN window
	//     [FromDate, DueDate) contains that row's date.
	//
	// Revision 2 carried a third clause here — "if the row's date is on or after
	// the last repayment period's DueDate, its key sorts after every repayment
	// row". That clause is DELETED in revision 3 (P0-2): it described a
	// disbursement row this seam never emits. A single disbursement dated on or
	// after the last repayment DueDate, or before ScheduleStartDate, is silently
	// discarded by the reference oracle into an all-zero schedule with no
	// disbursement row (ProgressiveLoanScheduleGenerator.java:305-308, the
	// after-maturity arm being gated on isMultiDisburseLoan() == false on this
	// seam). Such a disbursement is therefore OUTSIDE the graded domain and
	// refused with ErrNoDiscriminatingVector (see GenerateRequest), so the
	// ordering rule never has to key a row in that position. Every disbursement
	// this rule orders falls within some repayment period's half-open window.
	//
	// Rows are ordered by ascending window key; ties are broken by Kind, with
	// PeriodKindDisbursement before PeriodKindDownPayment before
	// PeriodKindRepayment; remaining ties by ascending InstallmentNumber, then
	// by ascending row date.
	//
	// The key is derivable from the response itself — the repayment rows carry
	// the windows — so two implementations agree on it without mirroring each
	// other's control flow.
	//
	// # Why the window key, and not simply DueDate
	//
	// A naive "sort by date, disbursement first" rule is REFUTED at a reachable
	// boundary. The oracle tests disbursement membership against a half-open
	// window (ProgressiveLoanScheduleGenerator.java:307-308) and emits
	// disbursements at the TOP of each period's iteration while appending that
	// period's repayment row at the BOTTOM (:121 versus :141). A disbursement
	// dated exactly on period k's due date therefore belongs to period k+1 and
	// is emitted AFTER repayment k. Observed on the pinned oracle, schedule
	// start 2024-01-01 and disbursement 2024-02-01, six monthly periods:
	//
	//	repayment 1 (due 2024-02-01, all zero), disbursement (2024-02-01),
	//	repayment 2 (due 2024-03-01), ... , repayment 6 (due 2024-07-01)
	//
	// The naive rule puts the disbursement first and is wrong. The window-key
	// rule reproduces the observed order, and also reproduces the ordinary case
	// where the disbursement opens the schedule.
	Periods []Period
}

// ScheduleGenerator answers exactly one question: given the terms of a loan,
// what is its repayment schedule?
//
// It is implemented twice — once as an adapter onto the Fineract reference
// oracle, once by the Go native module — and callers depend only on this
// interface. Which implementation a deployment resolves is a per-bounded-context
// configuration decision described in DEC-1; changing it in a live environment
// is a CUTOVER, which is a hard user gate and is not expressible through this
// interface.
//
// Generation is a pure function of its request: it moves no money, writes no
// ledger entry, posts nothing and has no side effect. It therefore carries no
// Idempotency-Key — that mandate applies to money-movement requests, and a
// request that can be replayed freely without consequence needs no
// deduplication key. Any later operation that commits a schedule to an account
// is a different operation under a different contract.
//
// Implementations must be deterministic: an equal GenerateRequest yields an
// equal Schedule, on every call, in every process, forever. Conformance is
// judged by replaying captured golden vectors through both implementations and
// comparing the resulting Schedules element-wise. A conformance PASS means
// "matches the reference oracle on captured vectors, within the graded domain".
// It never means "safe to cut over".
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
// The taxonomy is three-valued and no finer: is the request well formed, can it
// be answered at all, and has anyone ever checked the answer.
//
// # Error precedence (normative, added in revision 3 — P0-3)
//
// A single request can be refusable for more than one reason — for example
// FrequencyYears on the fixed-30/360 arm (ErrUnsupportedConfiguration) together
// with RoundingHalfEven (outside the graded domain, ErrNoDiscriminatingVector).
// Without a precedence rule, two conforming implementations could return
// DIFFERENT sentinels for the identical request, violating the equal-rejection
// requirement above: a request one refuses as unsupported and the other as
// ungraded is indistinguishable from a conformance failure. An implementation
// MUST evaluate refusal reasons in this order and return the FIRST applicable
// sentinel, strongest obstruction first:
//
//  1. ErrInvalidRequest      — not well formed. Nothing downstream is
//     meaningful on a malformed request, so this always wins.
//  2. ErrUnsupportedConfiguration — well formed, but this contract does not
//     admit it or the oracle cannot be asked at all. Wins over
//     ErrNoDiscriminatingVector because "cannot be answered" is a stronger and
//     more permanent statement than "answerable but not yet graded", and
//     because ErrNoDiscriminatingVector wraps this one — collapsing to the
//     stronger claim is consistent with the wrapping.
//  3. ErrNoDiscriminatingVector — well formed and computable, but outside the
//     graded domain.
//
// So the two-reason example above returns ErrUnsupportedConfiguration,
// deterministically, from both implementations.
var (
	// ErrInvalidRequest reports a request that is not well formed: a zero or
	// out-of-range enum, a non-canonical or non-positive-denominator Rate, an
	// impossible CivilDate, a TimeZone that is not an IANA zone name, a
	// non-positive precision or scale, a non-positive amount or count.
	ErrInvalidRequest = errors.New("loanschedule: invalid request")

	// ErrUnsupportedConfiguration reports a well-formed request this contract
	// does not admit, or that the reference oracle cannot be asked at all:
	// an interest method other than declining balance; a Disbursements slice
	// whose length is not one; FrequencyYears on the fixed-30/360 arm, which the
	// oracle throws on (on the ACTUAL arm the oracle answers but the request is
	// ungraded — see FrequencyYears and the precedence rule above);
	// a Rounding whose RateFactorScale differs from its SignificantDigits;
	// a Rate whose reduced denominator is not a product of 2s and 5s; an
	// InstallmentRoundingMultipleMinor that is not a whole number of major
	// units.
	ErrUnsupportedConfiguration = errors.New("loanschedule: unsupported configuration")

	// ErrNoDiscriminatingVector reports a well-formed request that this
	// contract admits and the reference oracle can compute, but for which no
	// capture exists that could tell a correct implementation from an incorrect
	// one — a request outside the GRADED DOMAIN listed on GenerateRequest.
	//
	// It is deliberately distinct from ErrUnsupportedConfiguration in meaning
	// and deliberately indistinguishable from it to a caller that does not
	// care: it wraps it, so errors.Is(err, ErrUnsupportedConfiguration) is
	// true. The distinction records WHY the request was refused, which decides
	// how the refusal is retired: a missing vector is retired by capturing one,
	// which is behaviour and needs no amendment.
	//
	// Returning a number here instead would be the exact failure this program
	// exists to prevent — a port that passes its corpus and is wrong.
	ErrNoDiscriminatingVector = fmt.Errorf(
		"loanschedule: unsupported: no discriminating vector: %w", ErrUnsupportedConfiguration)
)
