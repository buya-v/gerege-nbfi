package loanschedule

import (
	"context"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// Wrong drives, and the single mechanism that produces them.
//
// A wrong drive is a REGISTERED, deliberately wrong implementation of a seam in
// this port: the same validated front half and the same exact-arithmetic engine
// as the graded Generator, with exactly one defect switched in. Its job is to
// prove the conformance vectors can fail — that the store can SEE the seam — by
// being a defect a competent porter could actually produce, run against the
// corpus, and measured to die on the vectors that carry the fact the defect
// falsifies.
//
// The ledger context's wrong implementations are the standard this file mirrors
// (ledger/conformance/impl.go). Each one there keeps everything right except the
// one thing it is wrong about, and each defect string is an argument: what the
// wrong port does, WHY a competent porter would write it (a real misreading of
// the Fineract source, cited by file and line), and which vector kills it.
//
// The graded port must stay byte-identical to what it was before any wrong drive
// existed, and there is a mechanism for that rather than a promise: the graded
// Generator calls generateFor with the ZERO variant, and every switch below
// defaults to the pinned behaviour. A wrong drive sets exactly one switch. The
// engine reads the switch at the exact spot the defect lives and nowhere else.
//
// Registration lives in cmd/conformance/impl_hook.go, which is the one file that
// names this package — the same boundary that registers loanschedule-go itself
// (conformance/registry.go). Nothing in the conformance package imports the
// port, so the wrong drives must be constructible here and handed over by name.

// variant is the set of wrong-drive switches. The ZERO value is the graded
// port's exact behaviour; see wrongdrives.go for the scheme.
type variant struct {
	// halfEvenMoney makes every MONEY quantization round ties to the nearest
	// EVEN neighbour (java RoundingMode HALF_EVEN, ordinal 6) instead of the
	// tenant's HALF_UP (ordinal 4). Loanschedule-wrong-half-even. Only the
	// currency layer changes — roundSignificant/roundScale, the significant-
	// digit arithmetic of the rate factor and the installment, still round
	// HALF_UP exactly as the MathContext does, because the counterfactual is
	// about the mode a SCHEDULE's money cells are quantised in, not about the
	// BigDecimal context the rate arithmetic runs under.
	halfEvenMoney bool

	// daysInYear365 reads the DAYS_360 convention's days-in-year constant as
	// 365. Loanschedule-wrong-days-in-year-365.
	daysInYear365 bool

	// frequencyUnitAsMonths replaces every RepaymentFrequencyUnit with MONTHS
	// before any guard or stepping reads it.
	// Loanschedule-wrong-frequency-unit-ignored.
	frequencyUnitAsMonths bool

	// repaymentCountAsOne replaces NumberOfRepayments with the minimum the
	// contract admits, so the term never comes from the request.
	// Loanschedule-wrong-repayments-fixed-one.
	repaymentCountAsOne bool

	// interestRateAsZero replaces AnnualNominalInterestRate with the Go zero
	// value, so no interest cell is ever charged.
	// Loanschedule-wrong-rate-zero.
	interestRateAsZero bool

	// scheduleStartAsDisbursement replaces ScheduleStartDate with the
	// disbursement date, so the two are never distinguished.
	// Loanschedule-wrong-schedule-start-ignored.
	scheduleStartAsDisbursement bool

	// disbursementSeedAsScheduleStart re-anchors the month-end rule to
	// ScheduleStartDate instead of the disbursement date.
	// Loanschedule-wrong-disbursement-seed-ignored.
	disbursementSeedAsScheduleStart bool
}

// applyRequest rewrites the request fields that a request-level wrong drive
// never reads. Everything a drive does not switch is passed through untouched.
func (v variant) applyRequest(req contract.GenerateRequest) contract.GenerateRequest {
	if v.frequencyUnitAsMonths {
		req.RepaymentFrequencyUnit = contract.FrequencyMonths
	}
	if v.repaymentCountAsOne {
		req.NumberOfRepayments = 1
	}
	if v.interestRateAsZero {
		req.AnnualNominalInterestRate = contract.Rate{Numerator: 0, Denominator: 1}
	}
	if v.scheduleStartAsDisbursement {
		req.ScheduleStartDate = req.Disbursements[0].Date
	}
	return req
}

// dueDateSeed returns the seed the month-end rule re-anchors to. The graded
// port seeds on the disbursement date (contract.Disbursement.Date); a drive may
// substitute the schedule start.
func (v variant) dueDateSeed(req contract.GenerateRequest) civilDate {
	if v.disbursementSeedAsScheduleStart {
		return req.ScheduleStartDate
	}
	return req.Disbursements[0].Date
}

// wrongScheduleGenerator is the one wrong-drive type: a validated generator
// running under exactly one variant switch (the field comment for each switch
// names the drive that sets it).
type wrongScheduleGenerator struct {
	v variant
}

func (w wrongScheduleGenerator) Generate(ctx context.Context, req contract.GenerateRequest) (contract.Schedule, error) {
	return generateFor(ctx, req, w.v)
}

var _ contract.ScheduleGenerator = wrongScheduleGenerator{}

// NewWrongHalfEven returns the wrong drive that rounds every MONEY cell's
// quantization tie to the nearest even neighbour.
//
// WHY A COMPETENT PORTER WRITES THIS. The request carries the tenant's
// RoundingMode and the generator VALIDATES it, so this port never rounds money
// any way but HALF_UP — but that validation is a seam a porter must build, and
// Fineract itself threads a MathContext whose mode a loan schedule does not
// control the same way at every rounding point. java.math.RoundingMode.HALF_EVEN
// (ordinal 6) is the BigDecimal default and the IEEE-754 default, and a porter
// who reaches for "the usual rounding" at the currency boundary — rather than
// reading MoneyHelper.getMathContext()'s (19, HALF_UP), which the ledger
// context's wrong-drive corpus already names as the ratifying citation — writes
// exactly this drive. It differs from the graded port ONLY on a money value
// that sits exactly on a half-minor-unit tie; on every other cell it is
// byte-identical, which is why the vectors that kill it are precisely the ones
// built to force such a tie.
func NewWrongHalfEven() contract.ScheduleGenerator {
	return wrongScheduleGenerator{v: variant{halfEvenMoney: true}}
}

// NewWrongDaysInYear365 returns the wrong drive that charges interest against a
// 365-day year where the DAYS_360 convention fixes 360.
//
// WHY A COMPETENT PORTER WRITES THIS. The convention's name carries "360", but
// the constant a porter reads at the rate-factor seam is daysInYear, and Fineract
// names both conventions DAYS_360 and DAYS_365 with the day-count classes
// choosing the constant (the loanproduct context's own wrong drive
// loanproduct-wrong-swap-days360-365 registers the same confusion one field
// upstream). Every interest cell is interest-for-days * rate / daysInYear, so
// reading 365 charges a slightly different rate on every period; this drive is
// the loanschedule-side measurement that loanproduct's swap is actually
// CONSUMED — that a schedule request which reaches a generator with the wrong
// days-in-year constant yields a schedule the vectors can tell from the pinned
// one.
func NewWrongDaysInYear365() contract.ScheduleGenerator {
	return wrongScheduleGenerator{v: variant{daysInYear365: true}}
}

// NewWrongFrequencyUnitIgnored returns the wrong drive that never reads
// RepaymentFrequencyUnit: it normalises every unit to MONTHS before the
// unsupported-configuration arm and the graded-domain guard.
//
// WHY A COMPETENT PORTER WRITES THIS. Every capture in the corpus is monthly
// and the contract says MONTHS "is the only unit in the graded domain", so the
// only arm any working porter ever exercises is plusMonths. A porter who wires
// the stepping directly to a monthly calendar add and never carries the enum
// into the two guards that read it writes exactly this. The field's only
// observable effect in the corpus is that REFUSE-03 is refused; with the unit
// erased, its YEARS plus FIXED_30_360 request is answered instead.
func NewWrongFrequencyUnitIgnored() contract.ScheduleGenerator {
	return wrongScheduleGenerator{v: variant{frequencyUnitAsMonths: true}}
}

// NewWrongRepaymentsFixedOne returns the wrong drive that never reads
// NumberOfRepayments and builds a single-repayment contract.
//
// WHY A COMPETENT PORTER WRITES THIS. NumberOfRepayments is the field that
// decides how many periods exist, so a port with it unwired does not produce a
// wrong interest cell, it produces a wrong SHAPE -- one period where the
// request asked for many. 1 is the minimum the contract admits and is well
// formed and inside the graded domain (contract.GenerateRequest.NumberOfRepayments),
// so this drive passes the front half unchanged and differs only in the count.
func NewWrongRepaymentsFixedOne() contract.ScheduleGenerator {
	return wrongScheduleGenerator{v: variant{repaymentCountAsOne: true}}
}

// NewWrongRateZero returns the wrong drive that never reads
// AnnualNominalInterestRate and charges 0% on every period.
//
// WHY A COMPETENT PORTER WRITES THIS. A rate that is never wired takes Go's
// zero value, and Rate{0,1} is explicitly a legal, un-special-cased request
// (contract.GenerateRequest.AnnualNominalInterestRate): the recurrence yields
// the installment count and the installment is principal/count. So the port
// validates, generates and answers -- it is only the graded cells that move.
func NewWrongRateZero() contract.ScheduleGenerator {
	return wrongScheduleGenerator{v: variant{interestRateAsZero: true}}
}

// NewWrongScheduleStartIgnored returns the wrong drive that never reads
// ScheduleStartDate and uses the disbursement date as the period anchor.
//
// WHY A COMPETENT PORTER WRITES THIS. A simple loan model has one date, the
// day the money moves, and the contract spends a paragraph insisting the two
// dates "reach different places in the reference oracle"
// (contract.GenerateRequest.ScheduleStartDate). A porter who collapses them
// onto the disbursement date writes exactly this.
func NewWrongScheduleStartIgnored() contract.ScheduleGenerator {
	return wrongScheduleGenerator{v: variant{scheduleStartAsDisbursement: true}}
}

// NewWrongDisbursementSeedIgnored returns the wrong drive that re-anchors the
// month-end rule to ScheduleStartDate instead of the disbursement date.
//
// WHY A COMPETENT PORTER WRITES THIS. The disbursement date is the seed of the
// month-end rule only because LoanApplicationTerms.java:583-589 selects it;
// the request also carries a schedule start that looks like the more natural
// anchor. A porter who seeds on ScheduleStartDate writes exactly this, and the
// two agree on every vector whose two dates fall on the same day.
func NewWrongDisbursementSeedIgnored() contract.ScheduleGenerator {
	return wrongScheduleGenerator{v: variant{disbursementSeedAsScheduleStart: true}}
}
