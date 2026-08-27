package conformance

import (
	"fmt"
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

	// A CLOSURE-FAMILY shape: a plain create, carrying none of the
	// opening-balance inputs, so nothing else in Admit can account for the
	// refusal this arm demands.
	v := *base
	v.Request.Command = ""
	v.Request.ContraGLAccountID = 0
	v.Request.PostedNonContraTransactionIDs = nil
	reasons := Admit(&v, opts)
	// THE ANCHOR IS STRUCTURAL, NOT EDITORIAL [T305]. It used to be the sentence
	// "EXACTLY ONE of the three shapes that row names is observed", which stopped
	// matching the moment the message was corrected to say that the accepting side is
	// now observed too — a green rule reported as a red test, for a reason that had
	// nothing to do with the rule. Matching the field name and the offending value
	// instead means this arm goes red only when the RULE stops refusing.
	if !containsSubstring(reasons,
		`capabilities_required names "ledger.opening.balance.and.closure" on a vector whose request.command is ""`) {
		t.Fatalf("a vector claiming ledger.opening.balance.and.closure for a NON-opening-balance "+
			"shape was ADMITTED, or refused for another reason. The ACCEPTING sides of the "+
			"pre-closure and future-dated boundaries are still uncaptured, and a vector claiming "+
			"this row for one of them reads as covered when it is not: %v", reasons)
	}
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
