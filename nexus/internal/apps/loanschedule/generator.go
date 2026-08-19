// Package loanschedule is the Go native implementation of the loan-schedule
// bounded context: a faithful port of the reference oracle's progressive-loan
// schedule generator, behind the ratified DEC-1 adapter contract.
//
// "The reference oracle" always means the Fineract reference implementation at
// pinned commit 426a23544e8426a38ae43ae404670a0a7e85b9eb, which this program
// grades Go output against. It never means Oracle Database, which is a
// prohibited product in this program. Nothing here touches a database at all:
// schedule generation is pure computation.
//
// The specification this package implements is the doc comments of
// internal/apps/loanschedule/contract, which are the ratified artefact. Where a
// behaviour is stated there, this package does that; where the contract cites a
// line of the reference oracle, this package cites the same line. Every rule
// carries its file:line so a reviewer re-derives against the source rather than
// against this code.
//
// # What is NOT here, and why that is correct
//
// The capture seam this context's corpus is taken through hard-wires two nulls --
// generate(mc, loanApplicationTerms, null, null)
// [VERIFIED: ProgressiveLoanScheduleGenerator.java:83] -- so loanCharges and
// holidayDetailDTO are structurally invisible to it. Charges, holidays and
// working-day adjustment are therefore outside the graded domain, and a request
// that would need them is REFUSED with the contract's own sentinel rather than
// answered with a number nothing can check. The same discipline applies to every
// value outside the graded domain: an explicit refusal turns a silent wrong
// answer into a loud missing feature, which is the failure this program exists
// to prevent.
//
// # Determinism
//
// Generation reads no clock, no ambient locale, no environment and no map
// iteration order. Every date is a civil date and every calendar operation is
// integer arithmetic on year/month/day, so the request's time zone -- which the
// contract carries so that no caller can smuggle an implicit offset across the
// boundary -- does not and cannot enter the arithmetic.
package loanschedule

import (
	"context"
	"fmt"
	"math/big"
	"strings"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// civilDate is the contract's own date type. Deliberately an alias and not a
// conversion: a second date type would be a second place to disagree.
type civilDate = contract.CivilDate

// Generator is the Go native contract.ScheduleGenerator.
//
// It holds no state, so the zero value is usable and every call is independent.
type Generator struct{}

// New returns the Go native schedule generator.
func New() Generator { return Generator{} }

var _ contract.ScheduleGenerator = Generator{}

// Generate returns the repayment schedule for req, or one of the contract's
// three sentinels.
//
// The refusal order is the contract's normative error precedence, strongest
// obstruction first: not well formed, then not admitted or unanswerable, then
// well formed and computable but outside the graded domain. Two implementations
// must return the SAME sentinel for the same request, or a request one refuses
// and the other answers is indistinguishable from a conformance failure.
func (Generator) Generate(ctx context.Context, req contract.GenerateRequest) (contract.Schedule, error) {
	if err := ctx.Err(); err != nil {
		return contract.Schedule{}, err
	}
	if err := validateWellFormed(req); err != nil {
		return contract.Schedule{}, err
	}
	if err := validateSupported(req); err != nil {
		return contract.Schedule{}, err
	}

	// The repayment windows come first because the graded domain's last
	// predicate is SEMANTIC: it needs the last repayment due date, which is a
	// function of the schedule start, the term, the frequency and the month-end
	// rule. Producing them costs nothing and refuses nothing.
	dueDates := repaymentDueDates(req.ScheduleStartDate, req.NumberOfRepayments,
		int64(req.RepaymentEvery), req.RepaymentFrequencyUnit, req.Disbursements[0].Date)

	if err := validateGradedDomain(req, dueDates[len(dueDates)-1]); err != nil {
		return contract.Schedule{}, err
	}

	return generate(req, dueDates), nil
}

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

func invalid(format string, args ...any) error {
	return fmt.Errorf("%w: %s", contract.ErrInvalidRequest, fmt.Sprintf(format, args...))
}

func unsupported(format string, args ...any) error {
	return fmt.Errorf("%w: %s", contract.ErrUnsupportedConfiguration, fmt.Sprintf(format, args...))
}

func ungraded(format string, args ...any) error {
	return fmt.Errorf("%w: %s", contract.ErrNoDiscriminatingVector, fmt.Sprintf(format, args...))
}

// validateWellFormed rejects a request that is not well formed. Nothing
// downstream is meaningful on a malformed request, so this always wins.
func validateWellFormed(req contract.GenerateRequest) error {
	if err := validateTimeZone(req.TimeZone); err != nil {
		return err
	}
	if len(req.Currency.Code) != 3 || strings.ToUpper(req.Currency.Code) != req.Currency.Code ||
		strings.Trim(req.Currency.Code, "ABCDEFGHIJKLMNOPQRSTUVWXYZ") != "" {
		return invalid("currency.Code %q is not an upper-case ISO 4217 alpha-3 code", req.Currency.Code)
	}
	if req.Currency.MinorUnitDigits < 0 || req.Currency.MinorUnitDigits > 9 {
		return invalid("currency.MinorUnitDigits is %d", req.Currency.MinorUnitDigits)
	}
	if req.Rounding.SignificantDigits <= 0 {
		return invalid("rounding.SignificantDigits is %d, it must be positive", req.Rounding.SignificantDigits)
	}
	if req.Rounding.RateFactorScale <= 0 {
		return invalid("rounding.RateFactorScale is %d, it must be positive", req.Rounding.RateFactorScale)
	}
	switch req.Rounding.Mode {
	case contract.RoundingHalfUp, contract.RoundingHalfEven:
	default:
		return invalid("rounding.Mode %d is not a value of the contract's RoundingMode", int32(req.Rounding.Mode))
	}
	if !validDate(req.ScheduleStartDate) {
		return invalid("ScheduleStartDate %s is not a real calendar date", formatDate(req.ScheduleStartDate))
	}
	if req.NumberOfRepayments < 1 {
		return invalid("NumberOfRepayments is %d, it must be at least 1", req.NumberOfRepayments)
	}
	if req.RepaymentEvery < 1 {
		return invalid("RepaymentEvery is %d, it must be at least 1", req.RepaymentEvery)
	}
	switch req.RepaymentFrequencyUnit {
	case contract.FrequencyDays, contract.FrequencyWeeks, contract.FrequencyMonths, contract.FrequencyYears:
	default:
		return invalid("RepaymentFrequencyUnit %d is not a value of the contract's enum",
			int32(req.RepaymentFrequencyUnit))
	}
	switch req.DayCount {
	case contract.DayCountFixed30Over360, contract.DayCountActualActual:
	default:
		return invalid("DayCount %d is not a value of the contract's enum", int32(req.DayCount))
	}
	if req.InterestMethod != contract.InterestMethodDecliningBalance {
		return invalid("InterestMethod %d is not a value of the contract's enum", int32(req.InterestMethod))
	}
	if err := validateRate("AnnualNominalInterestRate", req.AnnualNominalInterestRate); err != nil {
		return err
	}
	if err := validateRate("DownPaymentPercentage", req.DownPaymentPercentage); err != nil {
		return err
	}
	if req.DownPaymentPercentage.Numerator >= req.DownPaymentPercentage.Denominator {
		return invalid("DownPaymentPercentage %d/%d must be below 1",
			req.DownPaymentPercentage.Numerator, req.DownPaymentPercentage.Denominator)
	}
	for i, d := range req.Disbursements {
		if !validDate(d.Date) {
			return invalid("Disbursements[%d].Date %s is not a real calendar date", i, formatDate(d.Date))
		}
		if d.AmountMinor <= 0 {
			return invalid("Disbursements[%d].AmountMinor is %d, it must be positive", i, d.AmountMinor)
		}
		if i > 0 && compareDates(req.Disbursements[i-1].Date, d.Date) > 0 {
			return invalid("Disbursements are not ordered ascending by Date at index %d", i)
		}
	}
	if req.InstallmentRoundingMultipleMinor < 0 {
		return invalid("InstallmentRoundingMultipleMinor is %d, it may not be negative",
			req.InstallmentRoundingMultipleMinor)
	}
	return nil
}

// validateTimeZone requires an IANA zone NAME and rejects a fixed offset, which
// encodes a fact about a zone into a field that should name the zone.
//
// The check is structural rather than a zone-database lookup, on purpose: the
// contract records that no capture can discriminate this field and that the
// arithmetic is zone-free civil-date arithmetic, so making generation depend on
// the host's tzdata would add a failure mode that changes no answer. Mongolia's
// two zones, "Asia/Ulaanbaatar" (+08) and "Asia/Hovd" (+07), neither observing
// daylight saving, both pass; "+08:00", "UTC+8" and "GMT+8" are all rejected.
func validateTimeZone(tz string) error {
	if tz == "" {
		return invalid("TimeZone is empty; it must be an IANA zone name such as Asia/Ulaanbaatar")
	}
	if looksLikeOffset(tz) {
		return invalid("TimeZone %q is a fixed offset; it must be an IANA zone name such as "+
			"Asia/Ulaanbaatar (UTC+08) or Asia/Hovd (UTC+07)", tz)
	}
	for i, seg := range strings.Split(tz, "/") {
		if seg == "" {
			return invalid("TimeZone %q is not an IANA zone name", tz)
		}
		if !isASCIILetter(seg[0]) {
			return invalid("TimeZone %q is not an IANA zone name", tz)
		}
		for j := 0; j < len(seg); j++ {
			c := seg[j]
			if isASCIILetter(c) || (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '+' {
				continue
			}
			return invalid("TimeZone %q is not an IANA zone name", tz)
		}
		_ = i
	}
	return nil
}

func looksLikeOffset(tz string) bool {
	rest := tz
	for _, prefix := range []string{"UTC", "GMT", "utc", "gmt", "Z"} {
		if strings.HasPrefix(rest, prefix) {
			rest = rest[len(prefix):]
			break
		}
	}
	if rest == "" {
		// Bare "UTC" or "GMT" is a real zone name, not an offset.
		return false
	}
	if rest[0] != '+' && rest[0] != '-' {
		return false
	}
	rest = rest[1:]
	if rest == "" {
		return false
	}
	for i := 0; i < len(rest); i++ {
		if (rest[i] < '0' || rest[i] > '9') && rest[i] != ':' {
			return false
		}
	}
	return true
}

func isASCIILetter(c byte) bool { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') }

// validateRate enforces the contract's canonical form: a positive denominator, a
// non-negative numerator, and lowest terms -- so two requests carrying the same
// rate are structurally equal and a golden vector has exactly one legal encoding.
func validateRate(name string, r contract.Rate) error {
	if r.Denominator <= 0 {
		return invalid("%s %d/%d has a non-positive denominator", name, r.Numerator, r.Denominator)
	}
	if r.Numerator < 0 {
		return invalid("%s %d/%d has a negative numerator", name, r.Numerator, r.Denominator)
	}
	g := new(big.Int).GCD(nil, nil, big.NewInt(r.Numerator), big.NewInt(r.Denominator))
	if g.Cmp(big.NewInt(1)) != 0 {
		return invalid("%s %d/%d is not in lowest terms", name, r.Numerator, r.Denominator)
	}
	return nil
}

// validateSupported rejects a well-formed request this contract does not admit,
// or that the reference oracle cannot be asked at all. It wins over a
// graded-domain refusal because "cannot be answered" is a stronger and more
// permanent statement than "answerable but not yet graded".
func validateSupported(req contract.GenerateRequest) error {
	if len(req.Disbursements) != 1 {
		return unsupported("len(Disbursements) is %d; exactly one is legal today", len(req.Disbursements))
	}
	if req.RepaymentFrequencyUnit == contract.FrequencyYears &&
		req.DayCount == contract.DayCountFixed30Over360 {
		// The day-count switch sends DAYS_30 through a per-frequency dispatch that
		// handles DAYS, WEEKS and MONTHS and throws for anything else
		// [VERIFIED: ProgressiveEMICalculator.java:1536 -> :1598-1610, default at
		// :1609]. The oracle genuinely cannot be asked, so this is a missing
		// ANSWER and not a missing VECTOR.
		return unsupported("annual repayment on the fixed-30/360 arm: the reference oracle throws " +
			"\"Invalid repayment frequency\" rather than returning a schedule")
	}
	if req.Rounding.RateFactorScale != req.Rounding.SignificantDigits {
		// The oracle derives both from ONE integer, so a request in which they
		// differ describes a configuration no deployment of it can produce.
		return unsupported("rounding.RateFactorScale %d differs from rounding.SignificantDigits %d; "+
			"the reference oracle derives both from one MathContext",
			req.Rounding.RateFactorScale, req.Rounding.SignificantDigits)
	}
	if !terminatingDenominator(req.AnnualNominalInterestRate.Denominator) {
		// The adapter must render the rate as the decimal percentage the oracle's
		// input record expects; a reduced denominator with a prime factor other
		// than 2 or 5 has no exact terminating decimal percentage and cannot be
		// handed over without a rounding decision the contract has not specified.
		return unsupported("AnnualNominalInterestRate %d/%d has no exact terminating decimal percentage",
			req.AnnualNominalInterestRate.Numerator, req.AnnualNominalInterestRate.Denominator)
	}
	if !terminatingDenominator(req.DownPaymentPercentage.Denominator) {
		return unsupported("DownPaymentPercentage %d/%d has no exact terminating decimal percentage",
			req.DownPaymentPercentage.Numerator, req.DownPaymentPercentage.Denominator)
	}
	if req.InstallmentRoundingMultipleMinor != 0 {
		unit := pow10(req.Currency.MinorUnitDigits)
		if new(big.Int).Mod(big.NewInt(req.InstallmentRoundingMultipleMinor), unit).Sign() != 0 {
			// The oracle's counterpart is a whole number of MAJOR units, so a value
			// that is not one has no representation the adapter can render.
			return unsupported("InstallmentRoundingMultipleMinor %d is not a whole number of major units",
				req.InstallmentRoundingMultipleMinor)
		}
	}
	return nil
}

// terminatingDenominator reports whether d is a product of 2s and 5s.
func terminatingDenominator(d int64) bool {
	for d%2 == 0 {
		d /= 2
	}
	for d%5 == 0 {
		d /= 5
	}
	return d == 1
}

// validateGradedDomain refuses every value for which no capture exists that
// could tell a correct implementation from an incorrect one.
//
// Returning a number here instead would be the exact failure this program exists
// to prevent -- a port that passes its corpus and is wrong. The list is the
// contract's own, in the contract's own order.
func validateGradedDomain(req contract.GenerateRequest, lastDue civilDate) error {
	if req.Currency.MinorUnitDigits != 2 {
		return ungraded("currency.MinorUnitDigits is %d, the graded domain requires 2 (at 0 a second "+
			"rounding channel switches on inside the reference oracle)", req.Currency.MinorUnitDigits)
	}
	if req.Rounding.SignificantDigits != 19 {
		return ungraded("rounding.SignificantDigits is %d, the graded domain requires 19",
			req.Rounding.SignificantDigits)
	}
	if req.Rounding.RateFactorScale != 19 {
		return ungraded("rounding.RateFactorScale is %d, the graded domain requires 19",
			req.Rounding.RateFactorScale)
	}
	if req.Rounding.Mode != contract.RoundingHalfUp {
		return ungraded("rounding.Mode is not HALF_UP, which is the only mode any capture was taken at")
	}
	if req.RepaymentEvery != 1 {
		return ungraded("RepaymentEvery is %d, the graded domain requires 1", req.RepaymentEvery)
	}
	if req.RepaymentFrequencyUnit != contract.FrequencyMonths {
		return ungraded("RepaymentFrequencyUnit is not MONTHS, and every capture in the corpus is monthly")
	}
	if req.DayCount != contract.DayCountFixed30Over360 {
		return ungraded("DayCount is not the fixed-30/360 convention, and no vector for another arm " +
			"has been promoted")
	}
	if req.DownPaymentPercentage != (contract.Rate{Numerator: 0, Denominator: 1}) {
		return ungraded("DownPaymentPercentage %d/%d is non-zero; no capture has ever produced a "+
			"down-payment row", req.DownPaymentPercentage.Numerator, req.DownPaymentPercentage.Denominator)
	}
	if req.InstallmentRoundingMultipleMinor != 0 {
		return ungraded("InstallmentRoundingMultipleMinor is %d; the capture seam DROPS this field "+
			"silently, so no capture taken through it can grade it",
			req.InstallmentRoundingMultipleMinor)
	}
	// The window predicate. A single disbursement dated before the schedule start,
	// or on or after the last computed due date, is silently discarded by the
	// reference oracle into an all-zero schedule with no disbursement row
	// [VERIFIED: ProgressiveLoanScheduleGenerator.java:304-310 with
	// isMultiDisburseLoan() false]. Rather than reproduce that degenerate answer,
	// the shape is refused.
	d := req.Disbursements[0].Date
	if compareDates(req.ScheduleStartDate, d) > 0 {
		return ungraded("the disbursement %s is before ScheduleStartDate %s: the reference oracle "+
			"silently discards it into an all-zero schedule", formatDate(d), formatDate(req.ScheduleStartDate))
	}
	if compareDates(d, lastDue) >= 0 {
		return ungraded("the disbursement %s is on or after the last repayment due date %s: the "+
			"reference oracle silently discards it into an all-zero schedule",
			formatDate(d), formatDate(lastDue))
	}
	return nil
}

// ---------------------------------------------------------------------------
// Generation
// ---------------------------------------------------------------------------

// generate is the port of ProgressiveLoanScheduleGenerator.generate's main loop
// [VERIFIED: ProgressiveLoanScheduleGenerator.java:115-145].
//
// THE ROW ORDER IS THE LOOP'S OWN, AND IT IS NOT "SORT BY DATE, DISBURSEMENT
// FIRST". Disbursements are emitted at the TOP of each period's iteration (:121)
// and that period's repayment row is appended at the BOTTOM (:141), and
// membership is tested against the HALF-OPEN window [FromDate, DueDate) (:306).
// A disbursement dated exactly on period k's due date therefore belongs to
// period k+1 and is emitted AFTER repayment k -- and repayment k, read from a
// model in which no disbursement has yet been registered, is entirely zero.
//
// That sequencing is also why a pre-disbursement row reports a ZERO outstanding
// balance rather than the principal awaiting advance: the row's cells are read
// inside its own iteration (:126-133) while the registration happens in the
// iteration of the period that owns the date (:121 -> :350). The mechanism is
// sequencing, not arithmetic.
func generate(req contract.GenerateRequest, dueDates []civilDate) contract.Schedule {
	model := newScheduleModel(req, dueDates)

	disbursement := req.Disbursements[0]
	pending := true
	periods := make([]contract.Period, 0, len(model.periods)+1)

	for _, p := range model.periods {
		if pending && inPeriodM3(disbursement.Date, p.from, p.due) {
			periods = append(periods, contract.Period{
				Kind:              contract.PeriodKindDisbursement,
				InstallmentNumber: 0,
				FromDate:          disbursement.Date,
				DueDate:           disbursement.Date,
				PrincipalMinor:    disbursement.AmountMinor,
				InterestMinor:     0,
				// The plan carries the advanced amount as BOTH the row's principal
				// and its outstanding balance
				// [VERIFIED: LoanSchedulePlan.java:52-56].
				OutstandingPrincipalMinor: disbursement.AmountMinor,
			})
			model.addDisbursement(disbursement.Date, disbursement.AmountMinor)
			pending = false
		}
		periods = append(periods, contract.Period{
			Kind: contract.PeriodKindRepayment,
			// One shared counter runs across payable rows and is read before it is
			// incremented [VERIFIED: ProgressiveLoanScheduleGenerator.java:126, :143].
			InstallmentNumber:         installmentNumberOf(periods),
			FromDate:                  p.from,
			DueDate:                   p.due,
			PrincipalMinor:            model.duePrincipalMinor(p),
			InterestMinor:             model.dueInterestMinor(p),
			OutstandingPrincipalMinor: model.outstandingLoanBalanceMinor(p),
		})
	}
	return contract.Schedule{Periods: periods}
}

// installmentNumberOf returns the next payable-installment number given the rows
// already emitted: a dense, 1-based counter over down-payment and repayment rows,
// which a disbursement row does not advance.
func installmentNumberOf(emitted []contract.Period) int32 {
	var n int32
	for _, p := range emitted {
		if p.Kind == contract.PeriodKindDownPayment || p.Kind == contract.PeriodKindRepayment {
			n++
		}
	}
	return n + 1
}

// newScheduleModel builds the interest schedule model: one repayment period per
// due date, each carrying exactly one interest period spanning its whole window
// [VERIFIED: ProgressiveEMICalculator.java:100-111 ->
// RepaymentPeriod.java:143-151].
func newScheduleModel(req contract.GenerateRequest, dueDates []civilDate) *scheduleModel {
	m := &scheduleModel{
		minorDigits:    req.Currency.MinorUnitDigits,
		precision:      req.Rounding.SignificantDigits,
		scale:          req.Rounding.RateFactorScale,
		repaymentEvery: int64(req.RepaymentEvery),
		// The oracle's input is a PERCENTAGE and it divides by 100 under the
		// MathContext [VERIFIED: ProgressiveEMICalculator.java:1318-1320]; the
		// contract's Rate is already the dimensionless fraction, so the division
		// has been performed exactly and only the MathContext rounding remains.
		rate: roundSignificant(new(big.Rat).SetFrac64(
			req.AnnualNominalInterestRate.Numerator,
			req.AnnualNominalInterestRate.Denominator), req.Rounding.SignificantDigits),
		// DayCountFixed30Over360 maps onto (DaysInMonthType.DAYS_30,
		// DaysInYearType.DAYS_360); the mapping is normative on the contract's
		// DayCountConvention.
		daysInMonth: ratInt64(30),
		daysInYear:  ratInt64(360),
	}
	from := req.ScheduleStartDate
	for i, due := range dueDates {
		p := newRepaymentPeriod(from, due)
		p.idx = i
		m.periods = append(m.periods, p)
		from = due
	}
	return m
}

// ---------------------------------------------------------------------------
// Repayment date stepping
// ---------------------------------------------------------------------------

// repaymentDueDates produces the schedule's period boundaries
// [VERIFIED: DefaultScheduledDateGenerator.java:49-73].
//
// The first repayment is stepped like every other one, because the seam's
// assembler builds exclusively through the Builder and the Builder never assigns
// calculatedRepaymentsStartingFromDate [VERIFIED: LoanApplicationTerms.java:304-351
// against :803], so the first-repayment shortcut at
// DefaultScheduledDateGenerator.java:121-123 is unreachable here.
//
// Two adjustments the oracle applies on this path are provably identities and
// are therefore absent rather than approximated: fixedLength is pinned null by
// the contract, and adjustRepaymentDate short-circuits when holidayDetailDTO is
// null [VERIFIED: DefaultScheduledDateGenerator.java:224], which the seam
// hard-wires it to be [VERIFIED: ProgressiveLoanScheduleGenerator.java:83].
func repaymentDueDates(start civilDate, count int32, every int64,
	unit contract.RepaymentFrequencyUnit, seed civilDate) []civilDate {

	out := make([]civilDate, 0, count)
	last := start
	for i := int32(0); i < count; i++ {
		next := stepDate(last, every, unit)
		next = reAnchorToSeed(next, seed, unit)
		out = append(out, next)
		last = next
	}
	return out
}

// stepDate advances one boundary by the repayment frequency
// [VERIFIED: DefaultScheduledDateGenerator.java:310-332].
func stepDate(d civilDate, every int64, unit contract.RepaymentFrequencyUnit) civilDate {
	switch unit {
	case contract.FrequencyDays:
		return plusDays(d, every)
	case contract.FrequencyWeeks:
		return plusDays(d, 7*every)
	case contract.FrequencyMonths:
		return plusMonths(d, every)
	case contract.FrequencyYears:
		return plusMonths(d, 12*every)
	}
	return d
}

// reAnchorToSeed is the month-end rule, and it is the trap of this whole file.
//
// [VERIFIED: DefaultScheduledDateGenerator.java:168-176, adjustDate, reached from
// :130-131.] Stepping clamps the day into the target month, and this then
// re-anchors it on the SEED -- which is the DISBURSEMENT date, not the schedule
// start [VERIFIED: LoanApplicationTerms.java:583-589 selects the disbursement
// date as the seed; the Builder copies it at :324].
//
// THE CLAMPED DAY IS REMEMBERED IN THE SEED AND NEVER BECOMES THE NEW SEED. A
// schedule seeded on 31 January returns to the 31st the moment a month is long
// enough: 2024-02-29, then 2024-03-31 -- NOT 2024-03-29. An implementation that
// merely clamps and forgets produces the same MONEY on this convention, because
// a fixed 30/360 day count makes the amounts date-independent, so the defect is
// invisible in every money column and shows up only in the date column.
func reAnchorToSeed(d, seed civilDate, unit contract.RepaymentFrequencyUnit) civilDate {
	if unit != contract.FrequencyMonths {
		return d
	}
	if seed.Day > 28 && d.Day >= 28 {
		day := daysInMonth(d.Year, d.Month)
		if seed.Day < day {
			day = seed.Day
		}
		return civilDate{Year: d.Year, Month: d.Month, Day: day}
	}
	return d
}

// ---------------------------------------------------------------------------
// Civil-date arithmetic
// ---------------------------------------------------------------------------
//
// Hand-rolled proleptic Gregorian arithmetic, matching java.time.LocalDate,
// because the contract's dates carry no instant and no offset and because a
// conversion through an instant is a place to reintroduce a midnight-boundary
// bug. No clock is read anywhere.

func isLeapYear(y int32) bool { return y%4 == 0 && (y%100 != 0 || y%400 == 0) }

func daysInMonth(y, mo int32) int32 {
	switch mo {
	case 1, 3, 5, 7, 8, 10, 12:
		return 31
	case 4, 6, 9, 11:
		return 30
	case 2:
		if isLeapYear(y) {
			return 29
		}
		return 28
	}
	return 0
}

func validDate(d civilDate) bool {
	if d.Month < 1 || d.Month > 12 || d.Day < 1 {
		return false
	}
	return d.Day <= daysInMonth(d.Year, d.Month)
}

func compareDates(a, b civilDate) int {
	switch {
	case a.Year != b.Year:
		if a.Year < b.Year {
			return -1
		}
		return 1
	case a.Month != b.Month:
		if a.Month < b.Month {
			return -1
		}
		return 1
	case a.Day != b.Day:
		if a.Day < b.Day {
			return -1
		}
		return 1
	}
	return 0
}

func formatDate(d civilDate) string {
	return fmt.Sprintf("%04d-%02d-%02d", d.Year, d.Month, d.Day)
}

// floorDiv and floorMod round toward negative infinity, as java.lang.Math does.
func floorDiv(a, b int64) int64 {
	q := a / b
	if (a%b != 0) && ((a < 0) != (b < 0)) {
		q--
	}
	return q
}

func floorMod(a, b int64) int64 { return a - floorDiv(a, b)*b }

// epochDay is days since 1970-01-01 on the proleptic Gregorian calendar,
// matching LocalDate.toEpochDay.
func epochDay(d civilDate) int64 {
	y := int64(d.Year)
	m := int64(d.Month)
	total := int64(0)
	total += 365 * y
	if y >= 0 {
		total += (y+3)/4 - (y+99)/100 + (y+399)/400
	} else {
		total -= y/-4 - y/-100 + y/-400
	}
	total += (367*m - 362) / 12
	total += int64(d.Day) - 1
	if m > 2 {
		total--
		if !isLeapYear(d.Year) {
			total--
		}
	}
	return total - 719528
}

func fromEpochDay(epoch int64) civilDate {
	// java.time.LocalDate.ofEpochDay, transcribed.
	zeroDay := epoch + 719528 - 60
	adjust := int64(0)
	if zeroDay < 0 {
		adjustCycles := (zeroDay+1)/146097 - 1
		adjust = adjustCycles * 400
		zeroDay += -adjustCycles * 146097
	}
	yearEst := (400*zeroDay + 591) / 146097
	doyEst := zeroDay - (365*yearEst + yearEst/4 - yearEst/100 + yearEst/400)
	if doyEst < 0 {
		yearEst--
		doyEst = zeroDay - (365*yearEst + yearEst/4 - yearEst/100 + yearEst/400)
	}
	yearEst += adjust
	marchDoy0 := doyEst
	marchMonth0 := (marchDoy0*5 + 2) / 153
	month := (marchMonth0+2)%12 + 1
	dom := marchDoy0 - (marchMonth0*306+5)/10 + 1
	yearEst += marchMonth0 / 10
	return civilDate{Year: int32(yearEst), Month: int32(month), Day: int32(dom)}
}

// daysBetween is ChronoUnit.DAYS.between: whole days from a to b, signed
// [VERIFIED: DateUtils.java:308-312 delegates to the unit].
func daysBetween(a, b civilDate) int64 { return epochDay(b) - epochDay(a) }

func plusDays(d civilDate, n int64) civilDate { return fromEpochDay(epochDay(d) + n) }

// plusMonths matches LocalDate.plusMonths: the day is CLAMPED into the target
// month, so 31 January plus one month is 28 or 29 February.
func plusMonths(d civilDate, n int64) civilDate {
	months := int64(d.Year)*12 + int64(d.Month) - 1 + n
	y := int32(floorDiv(months, 12))
	mo := int32(floorMod(months, 12)) + 1
	day := d.Day
	if limit := daysInMonth(y, mo); day > limit {
		day = limit
	}
	return civilDate{Year: y, Month: mo, Day: day}
}

// monthsBetween is ChronoUnit.MONTHS.between, which is LocalDate.monthsUntil:
// each date is PACKED as (proleptic month)*32 + day-of-month and the difference
// is divided by 32, truncated toward zero.
//
// THIS IS NOT "the largest k with a + k months <= b". The two differ exactly when
// plusMonths would have clamped -- which is exactly the condition periodRatio's
// month-end special case tests, so they coincide while that special case is
// present and part company the moment it is dropped.
func monthsBetween(a, b civilDate) int64 {
	packedA := (int64(a.Year)*12 + int64(a.Month) - 1) * 32
	packedA += int64(a.Day)
	packedB := (int64(b.Year)*12 + int64(b.Month) - 1) * 32
	packedB += int64(b.Day)
	return (packedB - packedA) / 32
}
