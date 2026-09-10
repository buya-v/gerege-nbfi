package main

// The implementation hook.
//
// This file is the ONE place the conformance binary learns about a Go
// implementation of contract.ScheduleGenerator, and it is deliberately the only
// file in the harness that will ever name the port's package.
//
// THE GO PORT HAS LANDED (task T10) and is registered below.
//
// The hook's original instruction was a BLANK import of the port whose own
// init() called conformance.Register. That is not what this does, and the
// difference is deliberate: a blank import would make the production package
// import the conformance harness, so every binary that generates a schedule
// would link the grading rig, its vector loader and its capability registry. The
// dependency is inverted here instead — the harness's own command imports the
// port and registers it — which keeps the port free of any knowledge that it is
// graded, and keeps this file the single place the binary learns of an
// implementation. Nothing else about the arrangement changes.
//
// WHY IT WAS EMPTY UNTIL NOW, AND WHY THAT WAS CORRECT. With nothing registered
// the harness reports NO IMPLEMENTATION REGISTERED and exits 2 — a distinct,
// legible status that is neither a pass nor a crash. The alternative, a stub
// generator living here to "make the harness runnable", would have been a
// schedule generator inside the harness that grades schedule generators, and the
// first thing this task would have done is borrow it. The pipeline's
// independence is worth more than a green run, and the port below was written
// from the reference oracle's own source with nothing borrowed from this tree.
//
// The self-test path (-self-test, the replay implementation) still exists so the
// harness can be proven to work independently of whatever is registered here. A
// replay answers from the vector store and computes nothing.
//
// ONE PROOF IN .softhouse/conformance.sh GOES STALE WITH THIS CHANGE, and it is
// reported rather than fixed, because the harness is not this task's to edit.
// `--prove` case 1 asserts that `$bin -oracle-probe=up` exits 2 with the label
// "no implementation to grade". Its premise is "no implementation registered",
// which registering the port necessarily negates — the same way a refusal vector
// goes STALE the moment its capability enters the graded domain (grade.go's own
// term). Every other proof is unaffected, including case 8, which stays exit 2
// because a self-test fixture buys no parity.

import (
	"github.com/gerege/nexus/internal/apps/loanschedule"
	"github.com/gerege/nexus/internal/apps/loanschedule/conformance"
)

func init() {
	conformance.Register("loanschedule-go", loanschedule.New())
	// THE WRONG DRIVES. Each is the graded generator with exactly one variant
	// switch set (loanschedule/wrongdrives.go); RegisterWrong is what lets the
	// report say which implementations are known-wrong, and what keeps the
	// default selection (CorrectImplementationNames, main.go) from ever landing
	// on one. The defect string is the ARGUMENT, in the ledger corpus's style
	// (ledger/conformance/impl.go init): what the wrong port does, WHY a
	// competent porter would write it from the Fineract source, and which vector
	// kills it.
	conformance.RegisterWrong("loanschedule-wrong-half-even",
		"quantizes every MONEY cell with HALF_EVEN (java RoundingMode ordinal 6) instead of the "+
			"tenant's pinned HALF_UP (ordinal 4), at the currency layer only -- MoneyHelper's "+
			"(19, HALF_UP) is the compile-time pin the ledger corpus already cites as the ratifying "+
			"citation, but HALF_EVEN is the stock BigDecimal and IEEE-754 default, and a porter who "+
			"reaches for 'the usual rounding' at Money.java:52's setScale(currency.getDecimalPlaces(), "+
			"mc.getRoundingMode()) instead of reading the tenant pin writes exactly this. The two "+
			"rules differ ONLY on an exact half-minor-unit tie WHOSE TRUNCATED VALUE IS EVEN (0.025 -> HALF_UP 0.03, HALF_EVEN 0.02; 0.035 -> 0.04 under BOTH), so the "+
			"drive is byte-identical on every vector that does not land a quantization on a tie. "+
			"MEASURED (2026-09-08, oracle probe up): parity PASS 41 FAIL 5 -- the store's four "+
			"declared killers T61-HE-A, T61-HE-B, T61-HE-C and T149-PATHB-TIE (graded_against "+
			"MONEY-QUANTIZATION-HALF-EVEN, each margin measured) AND T116-G8-CLEAN-N103, the "+
			"600%-rate vector whose extreme daily interest lands money quantizations on "+
			"half-minor-unit ties no tie-built vector reaches",
		loanschedule.NewWrongHalfEven())
	// OH-CAP-I removed two drives that OH-RED-G had registered with a measured
	// kill count of ZERO and a defect string ending in "the answer is zero":
	// loanschedule-wrong-round-segments-then-sum and
	// loanschedule-wrong-due-date-exclusive. Both change money and NOTHING in
	// the graded domain can see them, and no vector CAN be built that grades
	// them (see that commit's message for the algebra): the port admits exactly
	// ONE balance change per loan (validateSupported refuses a second), so no
	// period ever carries two non-zero interest segments (aggregation fold
	// unobservable) and the only date on which the M1/M3 boundary rules differ
	// observably is the MATURITY due date, which validateGradedDomain refuses
	// as an all-zero degenerate schedule. A registered drive that can never die
	// asserts coverage the store does not have, so the two were deleted rather
	// than left green. The two drives below are the ones the corpus can fail.
	conformance.RegisterWrong("loanschedule-wrong-days-in-year-365",
		"charges interest against a 365-day year where the DAYS_360 convention fixes 360 -- the "+
			"convention's name carries '360' but the constant a porter reads at the rate-factor seam "+
			"is daysInYear, and the loanproduct context's own loanproduct-wrong-swap-days360-365 "+
			"registers the same confusion one field upstream. Every interest cell is "+
			"interest-for-days * rate / daysInYear, so reading 365 moves every interest cell of "+
			"every period; this drive is the loanschedule-side measurement that the DAYS_360 "+
			"constant is actually CONSUMED -- that a schedule request which reaches a generator with "+
			"the wrong days-in-year constant yields a schedule the vectors can tell from the pinned "+
			"one. MEASURED (2026-09-08, oracle probe up): parity PASS 1 FAIL 45 -- every vector with "+
			"a nonzero interest cell dies. The single survivor is T64-ZP-C (17 minor units at 36%): "+
			"its per-period interest is ~0.51 minor under 360 and ~0.503 minor under 365, and both "+
			"round to the SAME whole minor unit (1) on all 34 periods, so the switched constant "+
			"moves not one graded cell",
		loanschedule.NewWrongDaysInYear365())
	conformance.RegisterWrong("loanschedule-wrong-frequency-unit-ignored",
		"never reads RepaymentFrequencyUnit: it normalises every unit to MONTHS before the "+
			"unsupported-configuration arm (generator.go's FrequencyYears plus FIXED_30_360) and before "+
			"validateGradedDomain's monthly-only guard. Every capture in the corpus is monthly, so the "+
			"only arm any working porter exercises is plusMonths and the enum never has to be carried "+
			"into the guards at all. The field's one observable effect in the corpus is that REFUSE-03 "+
			"is refused; with the unit erased its YEARS request is answered instead. "+
			"MEASURED (2026-09-10, oracle probe down): parity PASS 46 FAIL 0, contract-refusal PASS 3 "+
			"FAIL 1 -- parity_fail=1. THE SINGLE KILL IS REFUSE-03 (its expected "+
			"ErrUnsupportedConfiguration becomes an answer). This is also the finding: the corpus "+
			"varies the unit but its ONLY non-monthly request is a REFUSAL vector, and the graded "+
			"domain refuses every YEARS request, so the field's money effect is STRUCTURALLY "+
			"unreachable -- no vector can carry a graded annual schedule. The unit is proven CONSUMED "+
			"only at the refusal seam.",
		loanschedule.NewWrongFrequencyUnitIgnored())
	conformance.RegisterWrong("loanschedule-wrong-repayments-fixed-one",
		"never reads NumberOfRepayments and builds a single-repayment contract. The field decides "+
			"the schedule's SHAPE, so an unwired count does not move an interest cell, it collapses "+
			"the term: 1 is the minimum the contract admits and is well formed and inside the graded "+
			"domain, so this drive passes the front half unchanged and differs only in the count. "+
			"MEASURED (2026-09-10, oracle probe down): parity PASS 0 FAIL 46, contract-refusal PASS 4 "+
			"FAIL 0, self-test fixture FAIL -- parity_fail=47. EVERY graded vector dies: the row count "+
			"depends on the field, so each of the 46 parity vectors reports 'row count: expected N, "+
			"got 2'. The 4 refusal vectors are unaffected (a refusal does not read the count).",
		loanschedule.NewWrongRepaymentsFixedOne())
	conformance.RegisterWrong("loanschedule-wrong-rate-zero",
		"never reads AnnualNominalInterestRate and charges 0% on every period. An unwired rate takes "+
			"Go's zero value, and the contract states Rate{0,1} is legal and not special-cased -- every "+
			"rate factor is 0, every growth factor is 1, the installment is principal/count. The port "+
			"validates, generates and answers, and only the graded cells move. "+
			"MEASURED (2026-09-10, oracle probe down): parity PASS 0 FAIL 46, contract-refusal PASS 4 "+
			"FAIL 0, self-test fixture PASS -- parity_fail=46. Every graded vector carries a nonzero "+
			"rate, so every parity cell moves; the 4 refusal vectors do not read the rate and survive, "+
			"and the self-test fixture is already zero-rate so it is byte-identical.",
		loanschedule.NewWrongRateZero())
	// NO `loanschedule-wrong-currency-code-ignored` DRIVE. A sixth varying field
	// (Currency) was built and measured and is NOT registered, because it killed
	// ZERO and a zero-kill drive must not be merged. Currency varies only in its
	// Code (MNT vs USD); the port's output path never reads the code -- it scales
	// money off Currency.MinorUnitDigits, which is 2 for both -- so a port that
	// erases the code returns the recorded schedule on every vector. MEASURED
	// (2026-09-10): the drive ran to a per-vector table with all 46 parity vectors
	// PASS and all 4 refusal vectors PASS. The harness could not print a NUL
	// count because with the oracle probe down it refuses to say PASS at all (its
	// exit is UNUSABLE, which kills.sh correctly reports as a failed measurement,
	// never as zero); the all-PASS table is the evidence. THE FINDING: at this
	// seam Currency.Code is DECORATIVE -- the corpus varies it, but no vector's
	// recorded OUTPUT depends on it. A vector that sees the code would need a
	// second currency with a different MinorUnitDigits (the only part the money
	// path reads), which the corpus does not carry.
	conformance.RegisterWrong("loanschedule-wrong-schedule-start-ignored",
		"never reads ScheduleStartDate and anchors the periods on the disbursement date. The contract "+
			"insists the two dates reach different places in the reference oracle; a porter who collapses "+
			"them onto the one date the money moves writes exactly this. "+
			"MEASURED (2026-09-10, oracle probe down): parity PASS 37 FAIL 9, contract-refusal PASS 3 "+
			"FAIL 1 -- parity_fail=10. The 9 parity kills are P-03 (its first row kind becomes "+
			"DISBURSEMENT) and P-DRIFT-A..H (their first from_date moves), and the refusal kill is "+
			"REFUSE-04, whose disbursement-after-maturity request becomes well formed once the anchor "+
			"moves. The 37 survivors have ScheduleStartDate == Disbursements[0].Date, so collapsing the "+
			"two is a no-op on them.",
		loanschedule.NewWrongScheduleStartIgnored())
	conformance.RegisterWrong("loanschedule-wrong-disbursement-seed-ignored",
		"re-anchors the month-end rule to ScheduleStartDate instead of Disbursements[0].Date. The "+
			"disbursement date is the seed only because LoanApplicationTerms.java:583-589 selects it, "+
			"and the request carries a schedule start that looks like the more natural anchor; the two "+
			"agree on every vector whose dates fall on the same day. "+
			"MEASURED (2026-09-10, oracle probe down): parity PASS 38 FAIL 8, contract-refusal PASS 4 "+
			"FAIL 0 -- parity_fail=8. The 8 kills are P-DRIFT-A..H exactly, all with seed day 29/30/31 "+
			"and start day 28/29. Six of them fail first on a due_date; P-DRIFT-C and P-DRIFT-E fail "+
			"first on row 1 principal_minor, because their first due date coincides under the two seeds "+
			"while a later date diverges and moves the level installment solved over the whole schedule. "+
			"Every vector whose two dates share a day-of-month is byte-identical.",
		loanschedule.NewWrongDisbursementSeedIgnored())
	conformance.RegisterWrong("loanschedule-wrong-disbursement-amount-ignored",
		"never reads Disbursements[0].AmountMinor and advances one minor unit as principal. The "+
			"disbursement record is the only copy of the principal, so an unwired amount leaves the "+
			"schedule sized from a constant; 1 is positive and keeps the request inside the graded "+
			"domain, so the port still validates and answers and only the money moves. "+
			"MEASURED (2026-09-10, oracle probe down): parity PASS 3 FAIL 43, contract-refusal PASS 4 "+
			"FAIL 0, self-test fixture FAIL; kills.sh = 44. The three survivors are exactly the vectors "+
			"whose recorded principal is already 1 minor unit (T116-G8-CLEAN-N103, T116-G8-FAMB-N104, "+
			"T116-G8-FAMB-N108), where the substitute coincides with the request -- they prove the "+
			"drive's value IS the principal, not that the field is decorative.",
		loanschedule.NewWrongDisbursementAmountIgnored())
}
