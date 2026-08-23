package conformance

import (
	"strings"
	"testing"
)

// The T295 date-refusal tests: the two guards of
// validateBusinessRulesForJournalEntries, and the admissibility rules that keep
// the lifted date preconditions honest.
//
// WHY THIS FILE HAS TO EXIST AND NOT JUST THE VECTORS. The two vectors it
// defends were PROMOTED FROM BYTES ALREADY ON DISK and their probes MUST NEVER
// BE RE-FIRED — both are valid, balanced, postable manual journal entries whose
// only defect was an oracle-side precondition, and both preconditions have
// lapsed or lapse imminently. So the usual answer to "is this rule really
// checked?" — re-run the capture — is unavailable here, permanently. Everything
// that can still be demonstrated has to be demonstrated in process, which is
// what this file does.
//
// P-22, "a control that cannot fail is worse than none", is the standard each
// arm below is written to: every RED arm is preceded by a GREEN anti-vacuity arm
// proving the corpus is admitted in the first place, so a rule that refused
// EVERYTHING could not satisfy this file.

// findByRefusalCode returns the one committed vector expecting code.
func findByRefusalCode(t *testing.T, vs []*Vector, code string) *Vector {
	t.Helper()
	var found *Vector
	for _, v := range vs {
		if v.Expect.Refusal.Code == code {
			if found != nil {
				t.Fatalf("two committed vectors expect %q (%s and %s); these tests perturb ONE and "+
					"would otherwise be testing an arbitrary pick", code, found.CaseID, v.CaseID)
			}
			found = v
		}
	}
	if found == nil {
		t.Fatalf("no committed ledger vector expects %q. Every arm below perturbs one, so its "+
			"absence would make this test pass over nothing (P-35)", code)
	}
	return found
}

// TestDateInputsAreDefaultDeny drives the admissibility rules T295 added with
// request.{transaction_date, business_date, latest_closing_date}.
//
// These rules are the whole reason T289's verdict — "NOT PROMOTABLE as a
// literal-date vector" — could be reversed. Lifting a precondition into a vector
// only helps if the vector cannot then LIE about it, and a lifted field with no
// rules is just prose in a different font.
func TestDateInputsAreDefaultDeny(t *testing.T) {
	vs, opts := loadCommitted(t)
	closure := findByRefusalCode(t, vs, codeAccountingClosed)
	future := findByRefusalCode(t, vs, codeFutureDate)

	t.Run("ANTI-VACUITY: both committed date vectors are ADMITTED", func(t *testing.T) {
		for _, v := range []*Vector{closure, future} {
			if reasons := Admit(v, opts); len(reasons) != 0 {
				t.Fatalf("the committed vector %s is refused, so every RED arm below could be red "+
					"for that reason instead of for the rule it tests: %s",
					v.CaseID, strings.Join(reasons, "; "))
			}
		}
	})

	t.Run("a MALFORMED date REFUSES", func(t *testing.T) {
		// "2026-1-31" parses under the layout and would compare WRONG, not
		// merely look wrong: byte-wise, "2026-1-31" > "2026-08-23".
		for _, bad := range []string{"2026-1-31", "26-01-31", "2026-01-31T00:00:00Z", "31/01/2026", ""} {
			if bad == "" {
				continue // the empty case is the ABSENT case, tested separately below
			}
			v := *closure
			v.Request.TransactionDate = bad
			reasons := Admit(&v, opts)
			if !containsSubstring(reasons, "is not a strict `yyyy-MM-dd` calendar date") {
				t.Fatalf("request.transaction_date %q was ADMITTED. The comparator orders these "+
					"dates byte-wise, which is chronological only for zero-padded fixed-width "+
					"ISO-8601: %v", bad, reasons)
			}
		}
	})

	t.Run("a PRECONDITION WITHOUT ITS SUBJECT REFUSES", func(t *testing.T) {
		v := *closure
		v.Request.TransactionDate = ""
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "request.business_date is") {
			t.Fatalf("a vector carrying a business date with no transaction date was ADMITTED. "+
				"Nothing in it is subject to the boundary it records: %v", reasons)
		}
	})

	t.Run("a SUBJECT WITHOUT ITS PRECONDITION REFUSES", func(t *testing.T) {
		v := *closure
		v.Request.BusinessDate = ""
		reasons := Admit(&v, opts)
		// The PAIRING rule specifically, not merely the closure rule that also
		// fires here: this arm exists to prove the pairing rule can go red.
		if !containsSubstring(reasons, "request.business_date is empty") {
			t.Fatalf("a vector carrying a transaction date with no business date was ADMITTED. "+
				"The reference implementation READS NO CLOCK, so it would SKIP the future-date "+
				"rule and the vector would grade one rule fewer than it appears to: %v", reasons)
		}
	})

	t.Run("claiming the CLOSURE refusal without the closing date REFUSES", func(t *testing.T) {
		v := *closure
		v.Request.LatestClosingDate = ""
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "does not carry all three") {
			t.Fatalf("a vector expecting %s with no request.latest_closing_date was ADMITTED. "+
				"That date DECIDES the refusal (:636): %v", codeAccountingClosed, reasons)
		}
	})

	t.Run("a CLOSING DATE with no transaction date REFUSES", func(t *testing.T) {
		v := *closure
		v.Request.TransactionDate = ""
		v.Request.BusinessDate = ""
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "the closure boundary (:636) is compared against the "+
			"transaction date and there is none") &&
			!containsSubstring(reasons, "compared against the transaction date and there is none") {
			t.Fatalf("a vector carrying only a closing date was ADMITTED. There is nothing for the "+
				"boundary to be compared with: %v", reasons)
		}
	})

	t.Run("claiming the FUTURE refusal with NO dates at all REFUSES", func(t *testing.T) {
		v := *future
		v.Request.TransactionDate = ""
		v.Request.BusinessDate = ""
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "does not carry both request.transaction_date") {
			t.Fatalf("a vector expecting %s and carrying neither date was ADMITTED. That refusal IS "+
				"the comparison of those two dates: %v", codeFutureDate, reasons)
		}
	})

	t.Run("a NON-refusal vector tripping the CLOSURE guard REFUSES", func(t *testing.T) {
		// The sibling of the parity arm below, for the second guard: dates that
		// are NOT future-dated but ARE inside a closed period, on a vector that
		// records some other outcome.
		v := *future
		v.Expect.Refusal.Code = "error.msg.glJournalEntry.invalid.mismatch.debits.credits"
		v.Request.TransactionDate = "2026-01-31"
		v.Request.BusinessDate = "2026-08-23"
		v.Request.LatestClosingDate = "2026-01-31"
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "the INCLUSIVE guard at :636 refuses this request") {
			t.Fatalf("a vector recording a LATER refusal, whose transaction date is inside a closed "+
				"period, was ADMITTED. :636 answers first: %v", reasons)
		}
	})

	t.Run("claiming the CLOSURE refusal for a date AFTER the closing date REFUSES", func(t *testing.T) {
		v := *closure
		v.Request.TransactionDate = "2026-02-01" // strictly after latest_closing_date 2026-01-31
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "a date strictly after the closing date is ACCEPTED and WRITES") {
			t.Fatalf("a vector expecting %s with a transaction date AFTER the closing date was "+
				"ADMITTED. :636 refuses transactionDate <= closingDate; strictly after is accepted, "+
				"so that vector records a refusal nobody observed AND describes a request that "+
				"WRITES: %v", codeAccountingClosed, reasons)
		}
	})

	t.Run("claiming the CLOSURE refusal for a FUTURE-DATED entry REFUSES", func(t *testing.T) {
		// :629 runs BEFORE :634-639. A vector whose dates say the future guard
		// fires first cannot legitimately record the closure refusal.
		v := *closure
		v.Request.TransactionDate = "2026-09-01" // after business_date 2026-08-23
		v.Request.LatestClosingDate = "2026-09-30"
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "runs BEFORE :634-639") {
			t.Fatalf("a vector expecting %s whose transaction date is in the FUTURE was ADMITTED. "+
				"The oracle would have answered %s instead: %v",
				codeAccountingClosed, codeFutureDate, reasons)
		}
	})

	t.Run("claiming the FUTURE refusal for a NON-future date REFUSES", func(t *testing.T) {
		// isDateInTheFuture is isAfter and is STRICT: ON the business date is
		// not future-dated. This is the arm that would catch a promoter who
		// transcribed the boundary off by one.
		for _, td := range []string{"2026-08-23", "2026-08-22"} {
			v := *future
			v.Request.TransactionDate = td
			reasons := Admit(&v, opts)
			if !containsSubstring(reasons, "is STRICT") {
				t.Fatalf("a vector expecting %s with transaction date %q and business date %q was "+
					"ADMITTED. isAfter is strict, so the oracle does not take that branch: %v",
					codeFutureDate, td, v.Request.BusinessDate, reasons)
			}
		}
	})

	t.Run("a NON-refusal vector whose dates trip a guard REFUSES", func(t *testing.T) {
		// The direction that would rot silently: dates arriving on a vector
		// that records some LATER outcome the oracle never reached.
		var parity *Vector
		for _, v := range vs {
			if v.Class == ClassParity {
				parity = v
				break
			}
		}
		if parity == nil {
			t.Fatal("no committed parity vector; this arm would pass over nothing")
		}
		v := *parity
		v.Request.TransactionDate = "2026-12-31"
		v.Request.BusinessDate = "2026-08-23"
		reasons := Admit(&v, opts)
		if !containsSubstring(reasons, "The first guard the oracle reaches is the one it answers with") {
			t.Fatalf("a PARITY vector (expecting a posted entry) carrying a future transaction date "+
				"was ADMITTED. :629 refuses that request; the vector records a posting: %v", reasons)
		}
	})
}

// TestClosureBoundaryIsInclusive is the money-path assertion of this arm, made
// against the ported decision function rather than against prose.
//
// THE FINDING IT DEFENDS: :636 is
// `!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)`,
// which refuses `transactionDate <= closingDate`. The message the same throw
// returns says "Journal entry cannot be made PRIOR TO last account closing date
// for the branch". The two disagree about ONE DAY and that day is THE CLOSING
// DATE ITSELF — the day a period-end adjustment carries. A port written from the
// message fails OPEN there.
//
// The equal case is the only case that separates the two readings, and it is the
// case A2-01 captured, so this test is not a restatement of the vector: the
// vector fixes ONE point on the boundary and this walks BOTH SIDES of it.
func TestClosureBoundaryIsInclusive(t *testing.T) {
	base := Request{
		Seam:              "ledger_rest_posting",
		OfficeID:          1,
		Currency:          Currency{Code: "MNT", MinorUnitDigits: 2},
		ManualEntry:       true,
		BusinessDate:      "2026-08-23",
		LatestClosingDate: "2026-01-31",
		Accounts: []Account{
			{ID: 4, Code: "10201", Name: "Loan Portfolio", Usage: "DETAIL", ManualEntriesAllowed: true},
			{ID: 2, Code: "10100", Name: "Fund Source", Usage: "DETAIL", ManualEntriesAllowed: true},
		},
		Legs: []RequestLeg{
			{AccountID: 4, Side: SideDebit, AmountMajorText: "1000000"},
			{AccountID: 2, Side: SideCredit, AmountMajorText: "1000000"},
		},
	}

	cases := []struct {
		transactionDate string
		wantRefusal     bool
		why             string
	}{
		{"2026-01-30", true, "strictly before the closing date: refused under BOTH readings"},
		{"2026-01-31", true, "ON the closing date: refused ONLY under the INCLUSIVE reading, and " +
			"THIS IS THE CASE A2-01 CAPTURED"},
		{"2026-02-01", false, "strictly after the closing date: ACCEPTED under both readings"},
	}

	for _, c := range cases {
		req := base
		req.TransactionDate = c.transactionDate
		_, ref, err := GoPoster{}.PostEntry(req)
		if err != nil {
			t.Fatalf("%s: the reference implementation could not answer: %v", c.transactionDate, err)
		}
		switch {
		case c.wantRefusal && ref == nil:
			t.Fatalf("transaction date %s (%s): the reference implementation POSTED. :636 refuses "+
				"transactionDate <= closingDate", c.transactionDate, c.why)
		case c.wantRefusal && ref.Code != codeAccountingClosed:
			t.Fatalf("transaction date %s: refused with %q, want %q",
				c.transactionDate, ref.Code, codeAccountingClosed)
		case !c.wantRefusal && ref != nil:
			t.Fatalf("transaction date %s (%s): the reference implementation REFUSED with %q. A date "+
				"strictly after the closing date is accepted by the oracle -- refusing it would be "+
				"an 'improvement' on the oracle, which is a divergence from it",
				c.transactionDate, c.why, ref.Code)
		}
	}

	// AND THE WRONG PORT MUST DISAGREE ON EXACTLY ONE OF THE THREE, or the
	// counterfactual is not a counterfactual. This is the anti-vacuity control
	// for the whole finding: if the exclusive port agreed everywhere, there
	// would be no defect to have found.
	disagreements := 0
	for _, c := range cases {
		req := base
		req.TransactionDate = c.transactionDate
		_, right, err1 := GoPoster{}.PostEntry(req)
		_, wrong, err2 := closureBoundaryExclusivePoster{}.PostEntry(req)
		if err1 != nil || err2 != nil {
			t.Fatalf("%s: %v / %v", c.transactionDate, err1, err2)
		}
		if (right == nil) != (wrong == nil) {
			disagreements++
			if c.transactionDate != "2026-01-31" {
				t.Fatalf("the exclusive port disagrees with the reference on %s. The two readings "+
					"can only differ ON the closing date", c.transactionDate)
			}
		}
	}
	if disagreements != 1 {
		t.Fatalf("ledger-wrong-closure-boundary-exclusive disagreed with the reference on %d of 3 "+
			"dates, want exactly 1 (the closing date itself). At 0 the wrong implementation is not "+
			"wrong and the vector kills nothing", disagreements)
	}
}

// TestFutureDateGuardReadsTheBusinessDateAndNoClock pins the other guard, and
// pins the property that makes the whole promotion legitimate: the reference
// implementation NEVER consults a clock.
//
// If it did, this corpus would go red on a specific morning with nobody
// watching — which is precisely the defect T289 found in T287's captures and
// this vector schema was extended to remove.
func TestFutureDateGuardReadsTheBusinessDateAndNoClock(t *testing.T) {
	base := Request{
		Seam:        "ledger_rest_posting",
		OfficeID:    1,
		Currency:    Currency{Code: "MNT", MinorUnitDigits: 2},
		ManualEntry: true,
		Accounts: []Account{
			{ID: 4, Code: "10201", Name: "Loan Portfolio", Usage: "DETAIL", ManualEntriesAllowed: true},
			{ID: 2, Code: "10100", Name: "Fund Source", Usage: "DETAIL", ManualEntriesAllowed: true},
		},
		Legs: []RequestLeg{
			{AccountID: 4, Side: SideDebit, AmountMajorText: "1000000"},
			{AccountID: 2, Side: SideCredit, AmountMajorText: "1000000"},
		},
	}

	t.Run("STRICT: the business date itself is NOT future-dated", func(t *testing.T) {
		req := base
		req.BusinessDate, req.TransactionDate = "2026-08-23", "2026-08-23"
		if _, ref, err := (GoPoster{}).PostEntry(req); err != nil || ref != nil {
			t.Fatalf("an entry dated ON the business date was refused (%v / %v). "+
				"isDateInTheFuture is isAfter and is STRICT [DateUtils.java:258-264]", ref, err)
		}
	})

	t.Run("one day after the business date IS refused", func(t *testing.T) {
		req := base
		req.BusinessDate, req.TransactionDate = "2026-08-23", "2026-08-24"
		_, ref, err := GoPoster{}.PostEntry(req)
		if err != nil || ref == nil || ref.Code != codeFutureDate {
			t.Fatalf("want %q, got refusal %v err %v. This is A1-02's exact relation",
				codeFutureDate, ref, err)
		}
	})

	t.Run("NO CLOCK: an absent business date SKIPS the rule, it does not default to today",
		func(t *testing.T) {
			req := base
			req.BusinessDate, req.TransactionDate = "", "2999-12-31"
			if _, ref, err := (GoPoster{}).PostEntry(req); err != nil || ref != nil {
				t.Fatalf("with NO business date supplied, an entry dated 2999-12-31 was REFUSED "+
					"(%v / %v). That can only mean the implementation read a clock, which is the "+
					"ambient dependence T289 rejected and this schema exists to remove", ref, err)
			}
		})

	t.Run("THE PROMOTED VECTOR IS DATE-STABLE: the same answer whatever year it is read in",
		func(t *testing.T) {
			// The relation is what is stored, so shifting BOTH dates by the same
			// offset must not change the answer. A vector whose truth moved with
			// the calendar would fail this.
			for _, pair := range [][2]string{
				{"2026-08-23", "2026-08-24"},
				{"2030-02-28", "2030-03-01"},
				{"1999-12-31", "2000-01-01"},
			} {
				req := base
				req.BusinessDate, req.TransactionDate = pair[0], pair[1]
				_, ref, err := GoPoster{}.PostEntry(req)
				if err != nil || ref == nil || ref.Code != codeFutureDate {
					t.Fatalf("business date %s, transaction date %s: want %q, got %v / %v",
						pair[0], pair[1], codeFutureDate, ref, err)
				}
			}
		})
}

// TestDateGuardsPrecedeTheLaterRules records, as an executable statement, that
// the two date guards run before everything in this port that follows them.
//
// THE HONEST LABEL ON THIS TEST: the ORDERING IS SOURCE-DERIVED, NOT OBSERVED.
// :629 and :636 sit inside validateBusinessRulesForJournalEntries (:626), which
// runs at :157 before saveAllDebitOrCreditEntries, and checkDebitAndCreditAmounts
// is at :650 inside the same function and after both. But NO CAPTURED REQUEST
// violates a date rule AND another rule — all four of T287's probes are balanced,
// on manual-permitted DETAIL accounts — so nothing in this corpus orders them by
// measurement, and nothing may be re-fired to make one.
//
// Contrast LDG-REFUSE-03, whose precedence IS observed: OB-01's body was
// unbalanced by one minor unit, so the oracle had two grounds and picked one.
// This test asserts what the port does; it does not claim the oracle was asked.
func TestDateGuardsPrecedeTheLaterRules(t *testing.T) {
	// Unbalanced by one minor unit AND on a manual-forbidden account AND
	// future-dated: three grounds, and the date guard must be the one that
	// answers.
	req := Request{
		Seam:         "ledger_rest_posting",
		OfficeID:     1,
		Currency:     Currency{Code: "MNT", MinorUnitDigits: 2},
		ManualEntry:  true,
		BusinessDate: "2026-08-23",
		Accounts: []Account{
			{ID: 18, Code: "10500", Name: "No Manual Entries Asset", Usage: "DETAIL"},
			{ID: 2, Code: "10100", Name: "Fund Source", Usage: "DETAIL", ManualEntriesAllowed: true},
		},
		Legs: []RequestLeg{
			{AccountID: 18, Side: SideDebit, AmountMajorText: "250000.25"},
			{AccountID: 2, Side: SideCredit, AmountMajorText: "250000.24"},
		},
	}

	req.TransactionDate = "2026-08-24"
	_, ref, err := GoPoster{}.PostEntry(req)
	if err != nil || ref == nil || ref.Code != codeFutureDate {
		t.Fatalf("with a future date, a manual-forbidden account AND a one-minor-unit imbalance, the "+
			"port answered %v / %v; :629 runs first so it must answer %q", ref, err, codeFutureDate)
	}

	// Take the future date away and the closure guard is next.
	req.TransactionDate = "2026-01-31"
	req.LatestClosingDate = "2026-01-31"
	_, ref, err = GoPoster{}.PostEntry(req)
	if err != nil || ref == nil || ref.Code != codeAccountingClosed {
		t.Fatalf("with a pre-closure date, a manual-forbidden account AND an imbalance, the port "+
			"answered %v / %v; :636 runs before saveAllDebitOrCreditEntries so it must answer %q",
			ref, err, codeAccountingClosed)
	}

	// And take BOTH away: the later rules are still reachable, which is the
	// anti-vacuity control — without it the two arms above would pass on a port
	// that refused everything for one reason.
	req.TransactionDate = "2026-02-01"
	req.LatestClosingDate = "2026-01-31"
	_, ref, err = GoPoster{}.PostEntry(req)
	if err != nil || ref == nil || ref.Code == codeFutureDate || ref.Code == codeAccountingClosed {
		t.Fatalf("with both date guards satisfied the port answered %v / %v. A later rule must still "+
			"be reachable, or the two arms above prove nothing about ORDER", ref, err)
	}
}
