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
			"rules differ ONLY on an exact half-minor-unit tie with an odd truncated value, so the "+
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
}
