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
	var base *Vector
	for _, v := range vs {
		if v.Request.Command == "defineOpeningBalance" {
			base = v
			break
		}
	}
	if base == nil {
		t.Fatal("no committed ledger vector carries request.command == \"defineOpeningBalance\". " +
			"Every arm below perturbs one, so their absence would make this test pass over nothing")
	}

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
	var v *Vector
	for _, c := range vs {
		if c.Request.Command == "defineOpeningBalance" {
			v = c
			break
		}
	}
	if v == nil {
		t.Fatal("no committed opening-balance vector; this test would assert nothing")
	}
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
