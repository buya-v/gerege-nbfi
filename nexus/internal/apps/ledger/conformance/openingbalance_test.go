package conformance

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"testing"
)

// TestOpeningBalanceInputsAreDefaultDeny drives the admissibility rules T294
// added with the opening-balance inputs.
//
// A rule nobody has seen refuse is a rule nobody has tested — P-22, "a control
// that cannot fail is worse than none" — and these are the only thing standing
// between a lifted precondition and a field the comparator would silently ignore.
//
// THE ANTI-VACUITY CONTROL IS THE FIRST SUB-TEST: the committed vector that
// actually carries these inputs must be ADMITTED. Without it, a rule that refused
// everything would satisfy every RED arm below while making the corpus
// inadmissible, and this file would report that as success.
func TestOpeningBalanceInputsAreDefaultDeny(t *testing.T) {
	vs, opts := loadCommitted(t)
	// THE REFUSAL SHAPE, explicitly: these arms perturb the vector that carries
	// posted_non_contra_transaction_ids, and only the refusal has any.
	base := pickOpeningBalance(t, vs, true)

	t.Run("the committed opening-balance vector is ADMITTED", func(t *testing.T) {
		if reasons := Admit(base, opts); len(reasons) != 0 {
			t.Fatalf("the committed vector is refused, so every RED arm below could be red for that "+
				"reason instead of for the rule it tests: %s", strings.Join(reasons, "; "))
		}
	})

	t.Run("an UNKNOWN command REFUSES", func(t *testing.T) {
		v := *base
		v.Request.Command = "seedOpeningBalance"
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "is not one this schema knows") {
			t.Fatalf("an unknown request.command was ADMITTED, or refused for another reason. A "+
				"command string nothing routes on is a field the comparator ignores: %v", reasons)
		}
	})

	t.Run("defineOpeningBalance with NO contra mapping REFUSES", func(t *testing.T) {
		v := *base
		v.Request.ContraGLAccountID = 0
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "contra_gl_account_id is 0") {
			t.Fatalf("an opening-balance vector with no financial-activity-300 mapping was ADMITTED. "+
				":708 resolves that mapping BEFORE the guard at :717, so without it the oracle "+
				"returns a DIFFERENT refusal and the vector describes an observation nobody "+
				"took: %v", reasons)
		}
	})

	t.Run("opening-balance inputs on a PLAIN CREATE vector REFUSE", func(t *testing.T) {
		v := *base
		v.Request.Command = ""
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "contra_gl_account_id is set on a vector") {
			t.Fatalf("the contra mapping survived on a plain-create vector: %v", reasons)
		}
		if !containsSubstring(reasons, "posted_non_contra_transaction_ids is non-empty on a vector") {
			t.Fatalf("the posted-entry list survived on a plain-create vector. These fields must not "+
				"be able to accumulate on the vectors that predate them: %v", reasons)
		}
	})

	t.Run("a BLANK transcribed transaction id REFUSES", func(t *testing.T) {
		v := *base
		ids := make([]string, len(v.Request.PostedNonContraTransactionIDs))
		copy(ids, v.Request.PostedNonContraTransactionIDs)
		if len(ids) == 0 {
			t.Fatal("the committed opening-balance vector carries no transaction ids, so this arm " +
				"would assert nothing")
		}
		ids[0] = "   "
		v.Request.PostedNonContraTransactionIDs = ids
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "is blank") {
			t.Fatalf("a blank member of the oracle's own errors[0].args transcription was "+
				"ADMITTED: %v", reasons)
		}
	})
}

// TestOpeningBalanceCapabilityIsScopedToTheObservedShape drives the T296 rule RED.
//
// `ledger.opening.balance.and.closure` names three shapes and this store has
// observed one. T294 flipped the row into the graded domain on the strength of
// that one, and T296 MEASURED the consequence: a closure-family refusal vector
// built from T287's raw A1-01 artefacts is INADMISSIBLE against the pre-flip
// registry and ADMITTED AND GRADED against the merged one
// [.softhouse/reviews/T296/out/capgate-arm{A,B}-*.txt]. The rule in admit.go puts
// the width back without renaming or splitting the row, which T289 F-T289-4
// forbids. This is the arm that proves it can refuse — a control that cannot fail
// is worse than none (P-22).
//
// THE ANTI-VACUITY CONTROL IS THE COMMITTED VECTOR ITSELF, which names this same
// capability and must stay ADMITTED; TestOpeningBalanceInputsAreDefaultDeny's
// first sub-test asserts exactly that, so a rule that refused everything would go
// red there rather than pass silently here.
func TestOpeningBalanceCapabilityIsScopedToTheObservedShape(t *testing.T) {
	vs, opts := loadCommitted(t)
	// EITHER SHAPE WOULD DO — the arm blanks the command and asserts the capability
	// claim is then refused — and the REFUSAL is chosen so that the mutation this arm
	// makes (command "", contra 0, ids nil) leaves a vector the OTHER rules also accept,
	// which is what makes the measured refusal attributable to this rule alone.
	base := pickOpeningBalance(t, vs, true)
	var claims bool
	for _, name := range base.CapabilitiesRequired {
		if name == "ledger.opening.balance.and.closure" {
			claims = true
		}
	}
	if !claims {
		t.Fatal("the committed opening-balance vector does not name " +
			"ledger.opening.balance.and.closure, so the rule under test has nothing to scope")
	}

	// THE ANCHOR IS STRUCTURAL, NOT EDITORIAL [T305]. It used to be the sentence
	// "EXACTLY ONE of the three shapes that row names is observed", which stopped
	// matching the moment the message was corrected to say that the accepting side is
	// now observed too — a green rule reported as a red test, for a reason that had
	// nothing to do with the rule. Matching the field name instead means these arms go
	// red only when the RULE stops refusing. [T306: the value is no longer pinned into
	// the anchor, because two of the arms below carry a non-empty command.]
	const scoped = `capabilities_required names "ledger.opening.balance.and.closure" on a vector whose request.command is `

	t.Run("a FOURTH shape with none of the three request-side facts REFUSES", func(t *testing.T) {
		// A CLOSURE-FAMILY shape: a plain create carrying none of the
		// opening-balance inputs and none of the date inputs, so NOTHING else in
		// Admit can account for the refusal this arm demands -- not the command,
		// not either date comparison.
		v := *base
		v.Request.Command = ""
		v.Request.ContraGLAccountID = 0
		v.Request.PostedNonContraTransactionIDs = nil
		v.Request.TransactionDate = ""
		v.Request.BusinessDate = ""
		v.Request.LatestClosingDate = ""
		if reasons := Admit(&v, opts); !containsSubstring(reasons, scoped) {
			t.Fatalf("a vector claiming ledger.opening.balance.and.closure for a shape OUTSIDE the "+
				"four this store observed was ADMITTED, or refused for another reason: %v", reasons)
		}
	})

	t.Run("an ACCEPTANCE at either DATE boundary REFUSES", func(t *testing.T) {
		// T306, THE FOURTH SHAPE AS IT STANDS AFTER T305. LDG-05 made the
		// ACCEPTING side of the defineOpeningBalance COMMAND an observed shape, so
		// that arm rightly takes either expect.kind. The accepting side of the two
		// DATE boundaries is a different claim and it is STILL UNCAPTURED --
		// backlog B-1/B-2 in T295-ADJUDICATION.md. A vector recording an entry
		// ACCEPTED on or before a closing date, or ACCEPTED with a future
		// transaction date, describes an observation nobody took.
		//
		// THE ARMS CARRY THE REQUEST FACTS OF EACH BOUNDARY, which is the whole
		// point: if the date arms ever stop requiring a refusal expectation, these
		// two go red. Both dates are strict zero-padded yyyy-MM-dd, which is what
		// the byte-wise comparison in isoBefore/isoAfter needs.
		for _, arm := range []struct {
			name                   string
			txn, business, closing string
		}{
			{"pre-closure boundary, transaction ON the closing date", "2026-01-31", "2026-08-23", "2026-01-31"},
			{"future-dated, one day after the business date", "2026-08-24", "2026-08-23", ""},
		} {
			v := *base
			v.Request.Command = ""
			v.Request.ContraGLAccountID = 0
			v.Request.PostedNonContraTransactionIDs = nil
			v.Request.TransactionDate = arm.txn
			v.Request.BusinessDate = arm.business
			v.Request.LatestClosingDate = arm.closing
			v.Class = ClassParity
			v.Expect.Kind = "journal-entry"
			v.Expect.HTTPStatus = 200
			v.Expect.Refusal = Refusal{}
			if reasons := Admit(&v, opts); !containsSubstring(reasons, scoped) {
				t.Fatalf("an ACCEPTANCE claiming ledger.opening.balance.and.closure at the %s was "+
					"ADMITTED by the capability gate. No capture in this store observes an entry "+
					"ACCEPTED at either date boundary: %v", arm.name, reasons)
			}
		}
	})

	t.Run("the claim is NOT bought by declaring a refusal CODE", func(t *testing.T) {
		// T306-F-2. Two of the driver's three arms read expect.refusal.code, which
		// is the ANSWER THE VECTOR CLAIMS, not a fact about the request the oracle
		// was given. Here the code is declared and the request-side facts that
		// decide it are ABSENT: a code-keyed gate stays silent -- measured, it
		// contributed no reason at all -- and a request-keyed gate speaks.
		for _, code := range []string{codeAccountingClosed, codeFutureDate} {
			v := *base
			v.Request.Command = ""
			v.Request.ContraGLAccountID = 0
			v.Request.PostedNonContraTransactionIDs = nil
			v.Request.TransactionDate = ""
			v.Request.BusinessDate = ""
			v.Request.LatestClosingDate = ""
			v.Expect.Refusal.Code = code
			if reasons := Admit(&v, opts); !containsSubstring(reasons, scoped) {
				t.Fatalf("declaring expect.refusal.code %q bought the capability claim with no "+
					"request-side fact behind it: %v", code, reasons)
			}
		}
	})

	t.Run("EVERY committed claimant is still ADMITTED, and LDG-05 by name", func(t *testing.T) {
		// THE ANTI-VACUITY CONTROL, and it is the arm T320 required [T320-4]. A
		// rule that refused everything would pass all three arms above. The four
		// committed vectors that claim this row must contribute NO capability-gate
		// reason, and the ACCEPTING one must be named explicitly: T306's first
		// pass put `Kind == "refusal"` in front of all three arms and made LDG-05
		// INADMISSIBLE, which withdrew the ONLY kill of
		// `ledger-wrong-openingbalance-always-refusing` -- T296 arm A, a port that
		// refuses every opening balance and passed 4 of 4 graded ledger parity
		// vectors without it [.softhouse/reviews/T306/out/20-mutant-survival.txt].
		var claimants, sawAccepting int
		for _, c := range vs {
			var names bool
			for _, n := range c.CapabilitiesRequired {
				if n == "ledger.opening.balance.and.closure" {
					names = true
				}
			}
			if !names {
				continue
			}
			claimants++
			if c.Expect.Kind != "refusal" {
				sawAccepting++
			}
			if reasons := Admit(c, opts); containsSubstring(reasons, scoped) {
				t.Fatalf("committed vector %s claims this row and the capability gate REFUSES it. "+
					"The scope may only refuse shapes this store has NOT observed: %v",
					c.CaseID, reasons)
			}
		}
		if claimants != 4 {
			t.Fatalf("%d committed vectors claim ledger.opening.balance.and.closure; the observed "+
				"shapes are LDG-REFUSE-03 (:717), LDG-05 (its accepting side, :812), LDG-REFUSE-04 "+
				"(:636) and LDG-REFUSE-05 (:629-631). A different number means the store moved and "+
				"this control no longer covers what it names", claimants)
		}
		if sawAccepting != 1 {
			t.Fatalf("%d ACCEPTING vectors claim this row, want exactly 1 (LDG-05). If it is 0 the "+
				"corpus has lost the only observation that kills a port refusing every opening "+
				"balance; if it is more than 1, a shape was promoted without widening this control",
				sawAccepting)
		}
	})
}

// surplusCount pulls the COUNT out of the multiset rule's surplus sentence, so
// an arm can assert the NUMBER rather than a spelling of it.
var surplusCount = regexp.MustCompile(`carry amount "[^"]*" (-?\d+) time\(s\) more than twice-per-request-leg allows`)

// TestOpeningBalanceLegPairingIsRedDrivable drives T305's TWO leg rules RED.
//
// Neither shipped with an arm that fires [T320-3]. They are the rules that make
// LDG-05 admissible at all -- 6 expect legs for 3 request legs, paired by
// MULTISET rather than by position -- so a relaxation of either would not show
// up as a red bar, it would show up as a vector nobody could refuse.
//
//	THE LENGTH RULE. saveAllDebitOrCreditOpeningBalanceEntries persists the leg
//	at :791 AND its contra at :796 INSIDE the per-leg loop, so an ACCEPTED
//	opening balance stores exactly 2*len(legs) journal entries [VERIFIED:
//	JournalEntryWritePlatformServiceJpaRepositoryImpl.java:759-797 at the pinned
//	commit 426a23544; OB-ACCEPT-01 sent three legs and the oracle wrote six].
//
//	THE MULTISET RULE. :796 writes the contra with the SAME amount as its leg,
//	so every request amount must occur EXACTLY TWICE among the expect legs.
//
// The mutations are made on the COMMITTED accepting vector, so the premise is
// the real capture and not a fixture invented for the test.
func TestOpeningBalanceLegPairingIsRedDrivable(t *testing.T) {
	vs, opts := loadCommitted(t)
	base := pickOpeningBalance(t, vs, false)

	// THE PREMISE, CHECKED RATHER THAN ASSUMED. If a later capture changed the
	// shape, these arms would mutate something they no longer describe.
	if got, want := len(base.Expect.Legs), 2*len(base.Request.Legs); got != want {
		t.Fatalf("%s carries %d expect legs for %d request legs; the accepting shape this test "+
			"mutates is 2 expect legs per request leg", base.CaseID, got, len(base.Request.Legs))
	}

	t.Run("the COMMITTED accepting vector is admitted with NO reason at all", func(t *testing.T) {
		// THE ANTI-VACUITY CONTROL FOR EVERY ARM BELOW, and the one that catches a
		// relaxation as well as a tightening. Asserting "some reason appeared" is
		// how a mutation survives: a rule that computed the WRONG expected length
		// would still produce a reason for a mutated vector while quietly refusing
		// the real one. This arm demands ZERO reasons on the real capture.
		if reasons := Admit(base, opts); len(reasons) != 0 {
			t.Fatalf("%s -- the committed ACCEPTING opening-balance capture -- is INADMISSIBLE. "+
				"It is the only observation in this store of an accepted opening balance and the "+
				"only vector that kills a port refusing every one of them: %v", base.CaseID, reasons)
		}
	})

	t.Run("a leg SHORT of 2*request.legs is refused, and the rule NAMES 2*legs", func(t *testing.T) {
		// THE NUMBER IS THE ASSERTION, not the sentence. A first draft of this arm
		// asserted only the substring "an accepted entry stores" and a mutant that
		// relaxed `want` from 2*len(legs) to len(legs) SURVIVED it -- the mutant
		// still produced that sentence, for the wrong number, while making the
		// committed LDG-05 inadmissible. Measured, then fixed
		// [.softhouse/reviews/T306/out/30-mutation-arms.txt, MUTANT L].
		v := *base
		v.Expect.Legs = append([]ExpectLeg(nil), base.Expect.Legs[:len(base.Expect.Legs)-1]...)
		want := fmt.Sprintf("an accepted entry stores %d ", 2*len(v.Request.Legs))
		if reasons := Admit(&v, opts); !containsSubstring(reasons, want) {
			t.Fatalf("%d expect legs for %d request legs was ADMITTED on defineOpeningBalance, or "+
				"refused for a DIFFERENT expected length than %d. saveAllDebitOrCredit"+
				"OpeningBalanceEntries writes the leg at :791 AND its contra at :796 inside the "+
				"per-leg loop: %v", len(v.Expect.Legs), len(v.Request.Legs), 2*len(v.Request.Legs),
				reasons)
		}
	})

	t.Run("an amount carried a THIRD time is refused as a SURPLUS", func(t *testing.T) {
		// Also exercises the length rule -- 7 legs for 3 -- so the arm asserts the
		// MULTISET sentence specifically, not merely "some reason appeared".
		v := *base
		v.Expect.Legs = append(append([]ExpectLeg(nil), base.Expect.Legs...), base.Expect.Legs[0])
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "more than twice-per-request-leg allows") {
			t.Fatalf("an expect amount carried THREE times was ADMITTED by the multiset rule: %v",
				reasons)
		}
		// T306, closing a T320 defect: the count in that sentence is a SURPLUS and
		// must never be printed negative. A shortfall is the OTHER loop's sentence.
		for _, r := range reasons {
			if strings.Contains(r, "more than twice-per-request-leg allows") &&
				strings.Contains(r, "-1 time(s) more") {
				t.Fatalf("the SURPLUS message printed a NEGATIVE count: %q", r)
			}
		}
	})

	t.Run("an amount occurring ONCE is reported as a shortfall, not as a negative surplus",
		func(t *testing.T) {
			// Replace one contra leg's amount with a duplicate of another, so one
			// request amount occurs once and another occurs three times. LENGTH is
			// unchanged, which is what isolates the multiset rule.
			v := *base
			legs := append([]ExpectLeg(nil), base.Expect.Legs...)
			legs[1].AmountMajorText = legs[0].AmountMajorText
			// legs[1] was the contra of legs[0]; giving it legs[0]'s text leaves
			// legs[0]'s amount at 2 and drops legs[1]'s original amount to... it had
			// no original of its own, so mutate a DIFFERENT pair instead.
			legs = append([]ExpectLeg(nil), base.Expect.Legs...)
			legs[2].AmountMajorText = legs[0].AmountMajorText
			v.Expect.Legs = legs
			reasons := Admit(&v, opts)
			if !containsSubstring(reasons, "occurs fewer than twice among the expect legs") {
				t.Fatalf("a request amount occurring FEWER than twice was ADMITTED: %v", reasons)
			}
			// THE SIGN IS THE ASSERTION. T305's loop reported every non-zero
			// residue through the SURPLUS sentence, so a shortfall came out as
			// "carry amount X -1 time(s) MORE than twice-per-request-leg allows" --
			// the same defect named twice, once backwards. A first draft of this
			// arm asserted a SPELLING and could never fire; the mutant survived it
			// [.softhouse/reviews/T306/out/30-mutation-arms.txt, MUTANT S].
			for _, r := range reasons {
				m := surplusCount.FindStringSubmatch(r)
				if m == nil {
					continue
				}
				n, err := strconv.Atoi(m[1])
				if err != nil || n <= 0 {
					t.Fatalf("the SURPLUS sentence reported a count of %q, which is not a positive "+
						"surplus. A shortfall has its own sentence and must not be reported through "+
						"this one: %q", m[1], r)
				}
			}
		})

	t.Run("the SURPLUS report is ORDER-STABLE across runs", func(t *testing.T) {
		// T306, closing the second T320 defect: the surplus loop used to range over
		// a Go MAP and append to the reason slice, so with two surplus amounts the
		// ORDER of an inadmissibility report varied run to run. In a harness whose
		// discipline is byte-stable transcripts that is a diff nobody can read.
		v := *base
		v.Expect.Legs = append(append([]ExpectLeg(nil), base.Expect.Legs...),
			base.Expect.Legs[0], base.Expect.Legs[2])
		first := strings.Join(Admit(&v, opts), "\n")
		for i := 0; i < 64; i++ {
			if got := strings.Join(Admit(&v, opts), "\n"); got != first {
				t.Fatalf("the inadmissibility report is NOT order-stable; run %d differs:\n%s\n---\n%s",
					i, first, got)
			}
		}
		if !strings.Contains(first, "more than twice-per-request-leg allows") {
			t.Fatalf("this arm asserts stability over a report that does not contain the surplus "+
				"sentence, so it proves nothing: %s", first)
		}
	})
}

// TestOpeningBalanceRefusalPrecedesTheBalanceRule locks the ONE precedence this
// corpus actually observed.
//
// OB-01's request violates TWO rules at once — it is a defineOpeningBalance
// command on a tenant with posted entries AND it is unbalanced by exactly one
// minor unit — and the oracle answered with the opening-balance code. That makes
// it the only ORDERED pair of refusals in the ledger corpus; the manual-permission
// / balance pair is still [UNVERIFIED] because no capture violates both. A port
// that reorders these two passes every other vector in this store.
func TestOpeningBalanceRefusalPrecedesTheBalanceRule(t *testing.T) {
	vs, _ := loadCommitted(t)
	// THE REFUSAL SHAPE, AND ONLY IT. The accepting vector's request is BALANCED by
	// construction (:724 refuses an unbalanced opening balance before any write), so
	// asserting this premise over it would fail for a reason that has nothing to do
	// with precedence. That is exactly what happened when this selector was "the first
	// defineOpeningBalance vector" and LDG-05 sorted ahead of LDG-REFUSE-03.
	v := pickOpeningBalance(t, vs, true)
	// THE PREMISE, CHECKED RATHER THAN ASSUMED: the request really is unbalanced.
	// If a later edit balanced it, the oracle would have had only one ground to
	// refuse, and this test would still go green while proving nothing about
	// order.
	var debits, credits int64
	for _, l := range v.Request.Legs {
		m, err := parseMajorTextForTest(l.AmountMajorText, v.Request.Currency.MinorUnitDigits)
		if err != nil {
			t.Fatalf("leg on GL %d: %v", l.AccountID, err)
		}
		switch l.Side {
		case SideDebit:
			debits += m
		case SideCredit:
			credits += m
		}
	}
	if debits == credits {
		t.Fatalf("the opening-balance vector's request is BALANCED (%d == %d minor units), so the "+
			"oracle had only ONE ground to refuse it and this vector no longer orders the two "+
			"rules. The precedence claim in its _note is then unsupported", debits, credits)
	}
	got, ref, err := GoPoster{}.PostEntry(v.Request)
	if err != nil {
		t.Fatalf("the port could not answer at all: %v", err)
	}
	if ref == nil {
		t.Fatalf("the port POSTED an entry (%d legs) where the oracle refused", len(got.Legs))
	}
	if ref.Code != "error.msg.journalentry.defining.openingbalance.not.allowed" {
		t.Fatalf("the port refused with %q. The oracle answered the OPENING-BALANCE code for a "+
			"request that also violates the balance rule, so a port that checks the balance "+
			"first diverges: :717 runs before :724, and :651 checkDebitAndCreditAmounts is "+
			"inside :724", ref.Code)
	}
}

// parseMajorTextForTest converts major-unit decimal CHARACTERS to int64 minor
// units by exact string arithmetic. No float, not even to check a premise — the
// money rule binds a test fixture exactly as it binds a code path.
func parseMajorTextForTest(text string, digits int) (int64, error) {
	whole, frac := text, ""
	if i := strings.IndexByte(text, '.'); i >= 0 {
		whole, frac = text[:i], text[i+1:]
	}
	if len(frac) > digits {
		if strings.Trim(frac[digits:], "0") != "" {
			return 0, fmt.Errorf("%q carries a non-zero digit beyond %d minor digits", text, digits)
		}
		frac = frac[:digits]
	}
	frac += strings.Repeat("0", digits-len(frac))
	n, err := strconv.ParseInt(whole+frac, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("%q is not a decimal amount: %w", text, err)
	}
	return n, nil
}

// pickOpeningBalance returns the committed opening-balance vector of the wanted
// SHAPE — refusal or acceptance.
//
// WHY IT EXISTS [T305]. Every selector in this file used to be "the first vector
// whose command is defineOpeningBalance", written when there was exactly one. There
// are now TWO: LDG-REFUSE-03 (the refusal T294 captured) and LDG-05 (the accepting
// side). Load order made the accept the first match, and three arms written about the
// refusal silently began asserting over the accept — which is the P-7 shape, a test
// that asserts a FACT ABOUT TODAY'S CORPUS and goes stale on the next promotion. The
// fix is to say which shape each arm needs, and to FAIL LOUDLY when it is missing
// rather than pass over nothing.
func pickOpeningBalance(t *testing.T, vs []*Vector, wantRefusal bool) *Vector {
	t.Helper()
	for _, v := range vs {
		if v.Request.Command != "defineOpeningBalance" {
			continue
		}
		if (v.Expect.Kind == "refusal") == wantRefusal {
			return v
		}
	}
	shape := "ACCEPTING"
	if wantRefusal {
		shape = "REFUSAL"
	}
	t.Fatalf("no committed opening-balance vector of the %s shape; this arm would assert nothing", shape)
	return nil
}
