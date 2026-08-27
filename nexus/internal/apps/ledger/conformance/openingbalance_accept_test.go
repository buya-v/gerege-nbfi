package conformance

import (
	"testing"
)

// TestAcceptedOpeningBalancePostsTwoEntriesPerLeg drives the STEP 4 contra
// expansion, and it is the RED-DRIVE for it.
//
// P-22: "a control that cannot fail is worse than none — because it is believed."
// The expansion is a NEW behaviour on a money path, added on the strength of one
// capture, so what it does and what it must not do are both asserted here rather
// than left to the corpus run.
//
// WHAT IT ASSERTS, all of it from the COMMITTED vector rather than from constants
// typed into this file:
//
//  1. the port ACCEPTS (arm A, which refuses, is the defect this exists to catch);
//  2. it emits EXACTLY TWICE the request's legs;
//  3. every odd leg is the CONTRA account with the OPPOSITE side and the SAME
//     amount as the leg before it — per leg, never summed;
//  4. both totals equal the sum of the request leg amounts, in integer minor
//     units.
//
// And the two registered wrong implementations both DIE on it, measured through
// the same comparator the corpus run uses, so the graded_against rows in LDG-05
// are evidence rather than assertions.
func TestAcceptedOpeningBalancePostsTwoEntriesPerLeg(t *testing.T) {
	vs, _ := loadCommitted(t)
	v := pickOpeningBalance(t, vs, false)

	got, ref, err := GoPoster{}.PostEntry(v.Request)
	if err != nil {
		t.Fatalf("the port could not answer at all: %v", err)
	}
	if ref != nil {
		t.Fatalf("the port REFUSED (%d %s) a request the reference oracle ACCEPTED with HTTP 200 "+
			"and %d journal entries. That is T296 arm A, and it is the whole reason this vector "+
			"exists", ref.HTTPStatus, ref.Code, len(v.Expect.Legs))
	}
	if len(got.Legs) != 2*len(v.Request.Legs) {
		t.Fatalf("the port emitted %d legs for %d request legs; an accepted opening balance stores "+
			"TWO per leg (:791 the leg, :796 its contra)", len(got.Legs), len(v.Request.Legs))
	}
	if len(v.Request.Legs) < 3 {
		t.Fatalf("the accepting vector carries %d request legs. With fewer than three, a per-leg "+
			"contra and a single summed contra are INDISTINGUISHABLE, and this test would pass "+
			"over a port that nets them", len(v.Request.Legs))
	}

	var sum int64
	for i := 0; i < len(got.Legs); i += 2 {
		leg, contra := got.Legs[i], got.Legs[i+1]
		if contra.AccountID != v.Request.ContraGLAccountID {
			t.Fatalf("legs[%d] is on GL %d; the contra entry :796 writes is on the "+
				"financial-activity-300 account, GL %d", i+1, contra.AccountID, v.Request.ContraGLAccountID)
		}
		if contra.Side == leg.Side {
			t.Fatalf("legs[%d] and legs[%d] are both %s; :796 writes the CONTRA side (getContraType)",
				i, i+1, leg.Side)
		}
		if contra.AmountMinor != leg.AmountMinor {
			t.Fatalf("legs[%d] is %d minor units and its contra legs[%d] is %d. The contra carries the "+
				"SAME amount as its own leg — a port that summed them would show a single large "+
				"contra here", i, leg.AmountMinor, i+1, contra.AmountMinor)
		}
		sum += int64(leg.AmountMinor)
	}
	if int64(got.TotalDebitsMinor) != sum || int64(got.TotalCreditsMinor) != sum {
		t.Fatalf("totals are %d debit / %d credit; each leg contributes one debit and one credit of "+
			"its own amount, so both must be %d", got.TotalDebitsMinor, got.TotalCreditsMinor, sum)
	}
}

// TestAcceptingVectorKillsBothOpeningBalancePorts is the kill, measured.
//
// LDG-05's graded_against names two implementations. DEC-2 precondition P-10:
// "graded_against is a DECLARATIVE record and does not execute anything" — so it
// is executed here, through gradeOne, which is the same path the corpus run takes.
func TestAcceptingVectorKillsBothOpeningBalancePorts(t *testing.T) {
	vs, opts := loadCommitted(t)
	v := pickOpeningBalance(t, vs, false)

	// ANTI-VACUITY FIRST: the CORRECT port must PASS this vector. Without this,
	// a vector nothing can satisfy would make both arms below green.
	right := opts
	right.Implementation = NewGoPoster()
	right.ImplementationName = "ledger-go"
	if r := gradeOne(v, right); r.Outcome != OutcomePass {
		t.Fatalf("the correct port does NOT pass the accepting vector (%s): %v", r.Outcome, r.Detail)
	}

	for _, name := range []string{
		"ledger-wrong-openingbalance-always-refusing",
		"ledger-wrong-openingbalance-no-contra",
	} {
		impl, ok := Lookup(name)
		if !ok {
			t.Fatalf("%s is named in LDG-05's graded_against and is NOT REGISTERED. P-10: a row "+
				"naming an implementation nobody can execute is a sentence, not evidence", name)
		}
		wrong := opts
		wrong.Implementation = impl
		wrong.ImplementationName = name
		r := gradeOne(v, wrong)
		if r.Outcome == OutcomePass {
			t.Fatalf("%s SURVIVED the accepting vector. It is registered as deliberately wrong and "+
				"this vector is the only thing in the store that can see it", name)
		}
	}
}
