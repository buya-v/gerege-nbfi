package conformance

import (
	"fmt"

	"github.com/gerege/nexus/internal/apps/ledger"
)

// The property invariants this context can actually grade.
//
// DEC-2 §4.4 settles which, and the list is SHORT ON PURPOSE. Of I-1 … I-7:
//
//	I-1 debits equal credits          -- GRADEABLE, and graded here
//	I-2 splits sum to whole           -- GRADEABLE, and graded here
//	I-3 balances are derived          -- STRUCTURAL ONLY. "A vector is a snapshot
//	                                     of oracle output; it cannot observe the
//	                                     ABSENCE of a write path." Enforced by
//	                                     the source guard (.softhouse/guards/
//	                                     ledgerguard), which conformance.sh runs
//	                                     as guard_ledger_invariants. NOT here.
//	I-4 append-only                   -- STRUCTURAL ONLY, same reason. And note
//	                                     that BOTH of the source guard's I-4 arms
//	                                     (I4-DML and I4-BUILDER) inspect an EMPTY
//	                                     population in this Go tree, so neither
//	                                     form of I-4 detection is exercised by
//	                                     this tree at all (A2-32, §4.4.1).
//	I-5 corrections are reversing     -- UNGRADED. See below.
//	I-6 holds                         -- OUT OF THE CONTRACT DOMAIN.
//	I-7 Idempotency-Key               -- NOT APPLICABLE to this contract: it
//	                                     exposes no HTTP endpoint and moves no
//	                                     money. The obligation is real and lands
//	                                     on A1 and on the adapter's HTTP layer. A
//	                                     ledger conformance PASS says nothing
//	                                     whatever about it.
//
// I-5 IS UNGRADED AND THE REASON HAS CHANGED SINCE DEC-2 WAS WRITTEN, so it is
// stated here rather than inherited. DEC-2 §4.4 records I-5 as ungraded because
// "the A2 corpus contains no reversal". THAT IS NO LONGER TRUE: A2-348 reversed
// transaction a28f573f34c7 and A2-349 read the three legs back carrying
// reversed = true, and the re-run of sql/q4-a2-26-ledger-state.sql confirms the
// reversal pair on the live oracle. What is still missing is the OTHER half of
// I-5's statement — "a correction ADDS a leg pair; it never MUTATES one" — and
// that half is not observable from a snapshot at all: the reversal read-back
// shows the flag SET on the original rows, which is a mutation of a boolean
// column on the entry, and distinguishing "Fineract flags and adds" from
// "Fineract flags and rewrites" needs the write path, not the read-back. So I-5
// stays ungraded, with a corrected reason, and this corpus promotes no reversal
// vector.
//
// THE TWO THAT ARE GRADED ARE ASSERTED ON THE IMPLEMENTATION'S OUTPUT, and both
// call the PORT's own functions (ledger.DoubleEntryBalances,
// ledger.SplitsSumToWhole) rather than re-deriving the sum here. A harness that
// re-implements the check it is grading has two implementations of one rule and
// grades neither.

// InvariantStatus is the outcome of one invariant assertion.
type InvariantStatus string

const (
	// InvariantHeld means every assertion the invariant makes was made and held.
	InvariantHeld InvariantStatus = "HOLD"

	// InvariantViolated means an assertion was made and failed.
	InvariantViolated InvariantStatus = "VIOLATED"

	// InvariantNotApplicable means the invariant HAS NO ASSERTION TO MAKE on
	// this shape, and it is reported by name rather than silently omitted.
	//
	// P-35: a check that inspected zero items is not a pass. A two-leg entry is
	// the case that matters — "splits sum to whole" over a single split is
	// arithmetically true for every implementation, correct or not, so reporting
	// it as HOLD would be reporting a vacuous assertion as evidence. It is
	// N/A instead, it says so, and the report prints the count.
	InvariantNotApplicable InvariantStatus = "N/A"
)

// InvariantResult is one invariant's verdict on one vector.
type InvariantResult struct {
	Name   string
	Status InvariantStatus

	// Assertions is how many non-vacuous assertions were actually made. It is 0
	// on N/A, and the report prints it, so "asserted" can never be inferred from
	// "did not fail".
	Assertions int

	// Independent says whether this invariant's assertion could have gone RED
	// while every OTHER invariant on the same entry stayed GREEN.
	//
	// IT EXISTS BECAUSE "TWO INVARIANTS ASSERTED" IS NOT THE SAME CLAIM AS "TWO
	// THINGS CHECKED", and the difference bit this task. On a journal entry with
	// one leg on one side and N on the other, the leg-derived form of
	// splits_sum_to_whole is character-for-character the equation
	// double_entry_balances already asserts. Both would print HOLD; no
	// implementation could fail one and pass the other; and a reader counting two
	// green lines would be counting one assertion twice. The report prints this
	// flag on every line so that a DEPENDENT hold can never be quoted as a second
	// piece of evidence.
	Independent bool

	Detail string
}

// AssertInvariants runs every gradeable ledger invariant against the entry an
// implementation returned.
func AssertInvariants(e PostedEntry) []InvariantResult {
	return []InvariantResult{
		assertDoubleEntry(e),
		assertSplitsSumToWhole(e),
	}
}

// assertDoubleEntry is I-1.
//
// NON-VACUITY: an entry with fewer than two legs cannot balance non-trivially,
// and an entry with legs on only one side is a different defect. Both are
// reported N/A rather than HOLD.
func assertDoubleEntry(e PostedEntry) InvariantResult {
	r := InvariantResult{Name: "double_entry_balances"}
	var debits, credits int
	legs := make([]ledger.PostingLeg, 0, len(e.Legs))
	for _, l := range e.Legs {
		var side ledger.EntrySide
		switch l.Side {
		case SideDebit:
			side = ledger.EntryDebit
			debits++
		case SideCredit:
			side = ledger.EntryCredit
			credits++
		default:
			r.Status = InvariantViolated
			r.Assertions = 1
			r.Detail = fmt.Sprintf("leg on GL %d carries entry side %q, which is neither DEBIT nor CREDIT",
				l.AccountID, l.Side)
			return r
		}
		legs = append(legs, ledger.PostingLeg{Side: side, Amount: l.AmountMinor})
	}
	if debits == 0 || credits == 0 {
		r.Status = InvariantNotApplicable
		r.Detail = fmt.Sprintf(
			"the entry has %d debit and %d credit legs; with a side missing there are not two sums to "+
				"compare, so no assertion is made rather than a trivial one being reported as a hold",
			debits, credits)
		return r
	}
	r.Assertions = 1
	r.Independent = true
	if err := ledger.DoubleEntryBalances(legs); err != nil {
		r.Status = InvariantViolated
		r.Detail = err.Error()
		return r
	}
	// THE TOTALS THE IMPLEMENTATION REPORTED ARE ASSERTED TOO, not just the legs
	// it returned. A port whose legs balance and whose reported totals do not is
	// a port whose totals came from somewhere else — the netting defect exactly.
	r.Assertions++
	if e.TotalDebitsMinor != e.TotalCreditsMinor {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf(
			"the legs balance but the REPORTED totals do not: total_debits %d, total_credits %d "+
				"(minor units). A port whose reported totals disagree with its own legs is deriving them "+
				"from somewhere this harness cannot see",
			e.TotalDebitsMinor, e.TotalCreditsMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("debits %d == credits %d (minor units), over %d legs",
		e.TotalDebitsMinor, e.TotalCreditsMinor, len(e.Legs))
	return r
}

// assertSplitsSumToWhole is I-2, and the NON-VACUITY RULE is the whole of it.
//
// THE SHAPE IT ASSERTS. A journal entry with ONE leg on one side and N > 1 on
// the other is a SPLIT: the single leg is the whole and the N are the splits.
// That is the shape the A2 corpus's multi-leg entries have — a repayment debits
// the fund source once and credits principal, interest and fee; a manual entry
// debits two accounts and credits one — and it is the shape "splits sum to the
// whole" is a statement about.
//
// WHY A 2-LEG ENTRY IS N/A AND NOT A HOLD. With one split and one whole the
// assertion is `whole == split`, which is the same equation I-1 already made and
// which every implementation satisfies whenever I-1 does. Reporting it as HOLD
// would add a green line that no wrong implementation can turn red — P-22's
// "a control that cannot fail is worse than none, because it is believed".
//
// THIS IS THE ASSERTION THE PRE-A2-26 CORPUS COULD NOT MAKE AT ALL. Every
// journal entry in the A2 captures had exactly two legs (7 transactions / 14
// rows) until A2-26, so this invariant was graded by NOTHING (DEC-2 §5.0.1, and
// brief item 6). It is graded now because the corpus finally carries 2 four-leg
// and 4 three-leg transactions.
func assertSplitsSumToWhole(e PostedEntry) InvariantResult {
	r := InvariantResult{Name: "splits_sum_to_whole"}
	var debits, credits []ledger.MinorUnits
	for _, l := range e.Legs {
		switch l.Side {
		case SideDebit:
			debits = append(debits, l.AmountMinor)
		case SideCredit:
			credits = append(credits, l.AmountMinor)
		}
	}
	var whole ledger.MinorUnits
	var splits []ledger.MinorUnits
	var shape string
	// THE INDEPENDENT FORM, PREFERRED WHENEVER THE CAPTURE SUPPORTS IT. The whole
	// is the amount THE CALLER REQUESTED, read from the recorded request body and
	// converted by the implementation; the splits are the legs the oracle's
	// accounting produced on the many-leg side. Nothing in double_entry_balances
	// reads the requested amount, so this form can go RED while I-1 stays GREEN
	// — and the registered wrong implementation `ledger-wrong-split-drift` does
	// exactly that.
	if e.HasRequestedAmount && (len(debits) > 1 || len(credits) > 1) {
		splits = credits
		shape = "the REQUESTED transaction amount against the CREDIT splits"
		if len(debits) > 1 {
			splits = debits
			shape = "the REQUESTED transaction amount against the DEBIT splits"
		}
		r.Assertions = 1
		r.Independent = true
		if err := ledger.SplitsSumToWhole(e.RequestedAmountMinor, splits); err != nil {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("%s: %v", shape, err)
			return r
		}
		r.Status = InvariantHeld
		r.Detail = fmt.Sprintf("%s: %d == sum of %d splits (minor units). INDEPENDENT of "+
			"double_entry_balances: the whole comes from the recorded REQUEST, not from a leg",
			shape, e.RequestedAmountMinor, len(splits))
		return r
	}
	switch {
	case len(debits) == 1 && len(credits) > 1:
		whole, splits, shape = debits[0], credits, "one DEBIT whole against the CREDIT splits"
	case len(credits) == 1 && len(debits) > 1:
		whole, splits, shape = credits[0], debits, "one CREDIT whole against the DEBIT splits"
	default:
		r.Status = InvariantNotApplicable
		r.Detail = fmt.Sprintf(
			"the entry has %d debit and %d credit legs, which is not a split shape: this invariant needs "+
				"exactly one leg on one side and more than one on the other. A 2-leg entry would make the "+
				"assertion `whole == split`, identical to double_entry_balances and true for every "+
				"implementation that satisfies it, so it is declared not-applicable rather than reported "+
				"as a hold that nothing could fail",
			len(debits), len(credits))
		return r
	}
	r.Assertions = 1
	if err := ledger.SplitsSumToWhole(whole, splits); err != nil {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("%s: %v", shape, err)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("%s: %d == sum of %d splits (minor units). ⚠ DEPENDENT ON "+
		"double_entry_balances, NOT a second piece of evidence: the whole here IS one of the "+
		"entry's own legs, so this equation is character-for-character the one I-1 already "+
		"asserted on this shape, and no implementation can fail one and pass the other. It is "+
		"independent only where the recorded request carries its own transaction amount",
		shape, whole, len(splits))
	return r
}
