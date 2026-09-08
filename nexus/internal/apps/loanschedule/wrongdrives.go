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

	// roundSegmentsThenSum rounds each interest segment to a whole minor unit
	// and THEN sums, where the graded engine sums the exact segments and makes
	// money once. Loanschedule-wrong-round-segments-then-sum.
	roundSegmentsThenSum bool

	// registrationBoundaryDueExclusive reads the balance-change membership rule
	// as [FromDate, DueDate) — half-open at the due date — on EVERY period,
	// where the graded engine applies M1 ([FromDate, DueDate] on the first
	// period, (FromDate, DueDate] on every later one). A balance change dated
	// exactly on a repayment due date then registers into the NEXT period
	// instead of the one the date closes. Loanschedule-wrong-due-date-exclusive.
	registrationBoundaryDueExclusive bool

	// daysInYear365 reads the DAYS_360 convention's days-in-year constant as
	// 365. Loanschedule-wrong-days-in-year-365.
	daysInYear365 bool
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

// NewWrongRoundSegmentsThenSum returns the wrong drive that sums interest
// SEGMENTS ROUNDED to the minor unit, where the graded engine sums the exact
// segments and quantizes once.
//
// WHY A COMPETENT PORTER WRITES THIS. The reference oracle's own structure
// invites the misread: RepaymentPeriod.java:246-252 sums the segments and hands
// the SUM to Money.of, whose constructor applies the currency scale
// (Money.java:52) — but a porter who reads the interest-row construction as
// "each segment is interest, each becomes money" and generalises the Money.of
// call to the SEGMENT fold rounds per segment. The graded fold's own comment
// states the two functions differ; this drive is the executable version of the
// wrong one. It dies only where two or more segments in one period carry
// sub-minor-unit residues that round to different whole minor units than their
// exact sum — the aggregation-order seam.
func NewWrongRoundSegmentsThenSum() contract.ScheduleGenerator {
	return wrongScheduleGenerator{v: variant{roundSegmentsThenSum: true}}
}

// NewWrongDueDateExclusive returns the wrong drive that registers every balance
// change into the period whose half-open window [FromDate, DueDate) contains the
// date, reading the membership rule at the disbursement-row EMISSION site and
// generalising it to the balance-change REGISTRATION site.
//
// WHY A COMPETENT PORTER WRITES THIS. ProgressiveLoanScheduleGenerator.java
// emits the disbursement row against the HALF-OPEN window [FromDate, DueDate)
// (:306-307) and ProgressiveLoanInterestScheduleModel.java registers the balance
// change against M1 (:238-245, via
// LoanRepaymentScheduleProcessingWrapper.java:251-254), which is [FromDate,
// DueDate] on the first period and (FromDate, DueDate] on every later one. The
// two rules disagree on exactly one date — a change dated on a repayment due
// date, which M1 puts in the period the date CLOSES and the half-open rule puts
// in the NEXT period — and both sites live five files apart. A porter who reads
// the emission site (the one that prints the row the corpus transcribes) and
// generalises it to the registration path writes exactly this drive. It is the
// loan-schedule twin of ledger-wrong-closure-boundary-exclusive: a boundary
// read the wrong way, INDISTINGUISHABLE from the correct port on every vector
// whose balance changes avoid the boundary date.
func NewWrongDueDateExclusive() contract.ScheduleGenerator {
	return wrongScheduleGenerator{v: variant{registrationBoundaryDueExclusive: true}}
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
