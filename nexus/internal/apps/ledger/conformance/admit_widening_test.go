package conformance

import (
	"strings"
	"testing"
)

// positionalDisagreement is the POSITIONAL amount cross-check's own sentence.
// The arms below assert THIS sentence and never merely "some reason appeared",
// because the shape they perturb is inadmissible for a SECOND, unrelated reason
// ("expect.legs is non-empty on a refusal expectation") and an arm that accepted
// any reason would pass with the money check switched off. That is precisely the
// mistake that let the hole exist unobserved for a whole fire.
const positionalDisagreement = "disagree; both transcribe the same oracle characters"

// TestOpeningBalanceRefusalStillCrossChecksLegAmounts is the RED ARM FOR THE
// HOLE T320-3 FOUND AND T306 CLOSED. Nothing asserted the closure until now.
//
// # THE HOLE, AS IT STOOD
//
// T305 wrote the opening-balance leg condition out THREE TIMES and the copies
// were NOT complements:
//
//	POSITIONAL amount_major_text pairing  skipped when  command == defineOpeningBalance
//	MULTISET   amount_major_text pairing  applied when  command == defineOpeningBalance
//	                                                    AND expect.kind != "refusal"
//
// So for `command == "defineOpeningBalance"` AND `expect.kind == "refusal"` AND
// `len(expect.legs) > 0`, BOTH were off and the request/expect amount
// cross-check was ABSENT ENTIRELY. Before T305 the positional rule covered that
// case. T306 replaced the three copies with the single `obAcceptingLegs`
// boolean, which makes the two gates exact complements; this file is the arm
// that fires when they stop being complements.
//
// # THE FAIL DIRECTION, STATED, BECAUSE A GATE WITHOUT ONE IS A COIN TOSS
//
// `Admit` is FAIL-CLOSED and its output is a REFUSAL TO GRADE, never a verdict.
// A reason added here removes a vector from the graded corpus (the conformance
// run counts it `inadmissible` and compares none of its cells); a reason
// MISSING here lets a vector be graded whose expect amounts were never checked
// against the request amounts the oracle was actually sent.
//
// So the two failure directions are NOT symmetric and must not be confused:
//
//   - CLOSING the hole can only ever make MORE vectors inadmissible. It cannot
//     make a wrong implementation pass, cannot move a money cell, and cannot
//     turn a FAIL into a PASS. Its worst case is a vector this store loses and
//     a bar that goes red loudly.
//   - LEAVING it open lets a transcription defect — an expect amount that is
//     not the amount the request carried — enter the store SILENTLY, be graded
//     as truth, and become the standard a Go port is measured against. That is
//     an unobserved number entering a money corpus, which is the one failure
//     this whole file exists to prevent.
//
// The measured cost of the closure is therefore the thing to check, and the
// third arm checks it: ZERO committed vectors became inadmissible.
//
// # WHY THE ARM IS BUILT ON A COMMITTED VECTOR
//
// The perturbations start from the committed REFUSAL-shaped opening-balance
// capture, so the premise is a real observation and not a fixture invented to
// suit the rule.
func TestOpeningBalanceRefusalStillCrossChecksLegAmounts(t *testing.T) {
	vs, opts := loadCommitted(t)
	base := pickOpeningBalance(t, vs, true)

	// THE PREMISE, CHECKED RATHER THAN ASSUMED (P-35): the arms below build
	// expect legs out of the request legs, so a request with fewer than two legs
	// would make them assert almost nothing, and identical amounts on every leg
	// would make the "agrees" control indistinguishable from the "disagrees" one.
	if len(base.Request.Legs) < 2 {
		t.Fatalf("%s carries %d request legs; these arms need at least two",
			base.CaseID, len(base.Request.Legs))
	}
	if base.Expect.Kind != "refusal" || base.Request.Command != "defineOpeningBalance" {
		t.Fatalf("%s is command %q / kind %q; this file only means anything on the "+
			"defineOpeningBalance REFUSAL shape, which is the exact combination the two gates "+
			"used to leave uncovered", base.CaseID, base.Request.Command, base.Expect.Kind)
	}

	// legsFromRequest transcribes the request legs into expect legs that AGREE
	// positionally. amount_minor is a valid integer string because a malformed
	// one has its own rule, and an arm that tripped two rules at once would not
	// isolate this one.
	legsFromRequest := func() []ExpectLeg {
		out := make([]ExpectLeg, 0, len(base.Request.Legs))
		for _, l := range base.Request.Legs {
			out = append(out, ExpectLeg{
				AccountID:       l.AccountID,
				Side:            l.Side,
				AmountMinor:     "1",
				AmountMajorText: l.AmountMajorText,
			})
		}
		return out
	}

	t.Run("the COMMITTED refusal vector is admitted with NO reason at all", func(t *testing.T) {
		// THE ANTI-VACUITY CONTROL. Without it a rule that refused everything
		// would satisfy every RED arm below while emptying the corpus, and this
		// file would report that as success.
		if reasons := Admit(base, opts); len(reasons) != 0 {
			t.Fatalf("%s -- the committed opening-balance REFUSAL capture -- is INADMISSIBLE, so "+
				"every arm below could be red for that reason instead of for the rule it "+
				"tests: %v", base.CaseID, reasons)
		}
	})

	t.Run("a defineOpeningBalance REFUSAL whose expect amounts DISAGREE is refused BY THE AMOUNT RULE",
		func(t *testing.T) {
			// THE HOLE, MADE EXECUTABLE. Under T305's non-complementary gates this
			// vector collected only the "expect.legs is non-empty on a refusal
			// expectation" reason and NOT ONE WORD about the amounts.
			v := *base
			legs := legsFromRequest()
			legs[0].AmountMajorText = "999999.000000"
			v.Expect.Legs = legs

			reasons := Admit(&v, opts)
			if !containsSubstring(reasons, positionalDisagreement) {
				t.Fatalf("a defineOpeningBalance REFUSAL carrying an expect amount that DISAGREES "+
					"with the request amount at the same position was admitted WITHOUT the amount "+
					"cross-check firing. The positional gate and the multiset gate have stopped "+
					"being complements and the money cross-check is absent on this shape "+
					"again -- T320-3, closed by T306's obAcceptingLegs. Reasons: %v", reasons)
			}
			// AND IT NAMES THE OFFENDING AMOUNT, so a reader of a red bar can act on
			// it. A rule that fires without saying what disagreed is a rule that gets
			// pinned away.
			var named bool
			for _, r := range reasons {
				if strings.Contains(r, positionalDisagreement) && strings.Contains(r, "999999.000000") {
					named = true
				}
			}
			if !named {
				t.Fatalf("the amount cross-check fired but did not name the amount that "+
					"disagreed: %v", reasons)
			}
		})

	t.Run("the SECOND rule is not doing the work: amounts that AGREE draw no amount complaint",
		func(t *testing.T) {
			// THE DISCRIMINATION CONTROL. This shape is still inadmissible -- a
			// refused request created no entry, so ANY expect leg is refused one rule
			// higher -- and that is exactly why the arm above must not be satisfied by
			// "some reason appeared". Here the amounts agree, so the AMOUNT sentence
			// must be ABSENT while the refusal-legs sentence is PRESENT.
			v := *base
			v.Expect.Legs = legsFromRequest()

			reasons := Admit(&v, opts)
			if containsSubstring(reasons, positionalDisagreement) {
				t.Fatalf("the amount cross-check fired on expect legs that transcribe the request "+
					"legs EXACTLY. A rule that cannot tell agreement from disagreement grades "+
					"nothing: %v", reasons)
			}
			if !containsSubstring(reasons, "expect.legs is non-empty on a refusal expectation") {
				t.Fatalf("a refusal vector carrying expect legs was admitted by the rule that "+
					"refuses them outright. THIS ARM EXISTS TO SHOW THE TWO RULES ARE DISTINCT: "+
					"T306's argument that the hole was unreachable rests entirely on this rule, "+
					"and an argument that depends on a rule staying exactly as it is must have "+
					"that rule pinned: %v", reasons)
			}
		})

	t.Run("THE FAIL DIRECTION, MEASURED: the closure made NO committed vector inadmissible",
		func(t *testing.T) {
			// The closure can only ever ADD reasons. The question a reviewer actually
			// has is whether it added one to something real. It did not.
			for _, v := range vs {
				if reasons := Admit(v, opts); len(reasons) != 0 {
					t.Fatalf("%s is INADMISSIBLE. Closing a fail-closed gate removes vectors from "+
						"the graded corpus and never adds any, so this is the ONLY direction in "+
						"which closing the hole could cost anything: %v", v.CaseID, reasons)
				}
			}
			if len(vs) < 2 {
				t.Fatalf("%d vectors loaded; this arm would pass over almost nothing", len(vs))
			}
		})
}

// TestAcceptedOpeningBalanceIsNotPairedPOSITIONALLY is the arm for the OTHER
// direction of the same boolean, and it is the reason the hole could not be
// closed by simply deleting the exemption.
//
// The oracle emits ALL DEBIT legs (:742) before ALL CREDIT legs (:745)
// irrespective of the order the request listed them in, and it writes a CONTRA
// entry per leg (:796), so an accepted opening balance's expect legs do not line
// up with the request legs by POSITION at all -- they line up as a MULTISET, two
// occurrences of each request amount.
//
// If a future edit "simplified" `!obAcceptingLegs` away and applied the
// positional rule everywhere, THE COMMITTED ACCEPTING CAPTURE WOULD BECOME
// INADMISSIBLE and this store would silently lose the only observation that
// kills a port refusing every opening balance. This arm makes that loud.
func TestAcceptedOpeningBalanceIsNotPairedPOSITIONALLY(t *testing.T) {
	vs, opts := loadCommitted(t)
	base := pickOpeningBalance(t, vs, false)

	// THE PREMISE, MEASURED: the accepting capture really does disagree
	// positionally somewhere. If a later capture happened to line up, this arm
	// would be asserting over a vector the positional rule would accept anyway,
	// and it must say so rather than pass.
	var disagreements int
	for i, l := range base.Expect.Legs {
		if i < len(base.Request.Legs) && base.Request.Legs[i].AmountMajorText != l.AmountMajorText {
			disagreements++
		}
	}
	if disagreements == 0 {
		t.Fatalf("%s's expect legs agree with its request legs at EVERY position, so this arm "+
			"cannot distinguish the positional rule being exempted from it being satisfied. The "+
			"accepting shape is 2 expect legs per request leg with debits emitted before credits "+
			"(:742/:745, :796); a capture that lines up positionally is a different observation "+
			"and this arm must be re-derived against it", base.CaseID)
	}

	if reasons := Admit(base, opts); len(reasons) != 0 {
		t.Fatalf("%s -- the ONLY accepted-opening-balance observation this program has taken, and "+
			"the only vector that kills ledger-wrong-openingbalance-always-refusing -- is "+
			"INADMISSIBLE. It disagrees positionally at %d of its legs BY CONSTRUCTION, so a "+
			"positional amount rule applied to this shape withdraws a mutant kill: %v",
			base.CaseID, disagreements, reasons)
	}
}
