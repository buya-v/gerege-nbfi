package conformance

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"
)

// strictDecodeRefusalForTest decodes with the SAME strictness LoadStore uses
// (vector.go:920, dec.DisallowUnknownFields()). It is spelled out here rather
// than reached through LoadStore because the property under test is a property
// of the TYPE — that Refusal has no JSON name for its answer-side field — and
// routing it through a whole-file load would make a failure ambiguous between
// the type and the loader.
func strictDecodeRefusalForTest(raw []byte, r *Refusal) error {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	return dec.Decode(r)
}

// TestArgEchoIsASelectorAndNotADate drives the FORMULATION T307 landed, rather
// than trusting the doc comments that describe it.
//
// THE FORMULATION, IN ONE SENTENCE: `errors[0].args[0].value` is gradeable where
// it carries a SCALAR CALENDAR DATE the vector already declares as an input with
// provenance INDEPENDENT of the body being graded, and is NOT gradeable where it
// carries tenant-mutable history. The vector names a SELECTOR; the comparator
// resolves it; no date literal is ever an expectation.
//
// EVERY ARM BELOW IS PAIRED. A rule that refused everything would satisfy the RED
// arms and nothing else, which is P-22 — "a control that cannot fail is worse
// than none" — applied to an admissibility gate.
func TestArgEchoIsASelectorAndNotADate(t *testing.T) {
	vs, opts := loadCommitted(t)

	byID := map[string]*Vector{}
	for _, v := range vs {
		byID[v.CaseID] = v
	}
	const (
		refuse03 = "LDG-REFUSE-03-openingbalance-after-posted-entries"
		refuse04 = "LDG-REFUSE-04-preclosure-entry-on-closing-date"
		refuse05 = "LDG-REFUSE-05-future-dated-entry-one-day-after-business-date"
		refuse06 = "LDG-REFUSE-06-preclosure-entry-before-closing-date-echoes-the-closing-date"
	)
	for _, id := range []string{refuse03, refuse04, refuse05, refuse06} {
		if byID[id] == nil {
			t.Fatalf("the committed store does not carry %s, so this file would measure nothing", id)
		}
	}

	t.Run("ANTI-VACUITY: the three committed date refusals are ADMITTED and carry a selector",
		func(t *testing.T) {
			want := map[string]string{
				refuse04: ArgEchoLatestClosingDate,
				refuse05: ArgEchoTransactionDate,
				refuse06: ArgEchoLatestClosingDate,
			}
			for id, sel := range want {
				v := byID[id]
				if got := v.Expect.Refusal.ArgEcho; got != sel {
					t.Fatalf("%s carries arg_echo %q, want %q", id, got, sel)
				}
				if reasons := Admit(v, opts); len(reasons) != 0 {
					t.Fatalf("%s is REFUSED, so every RED arm below could be red for that reason "+
						"instead of for the rule it tests: %s", id, strings.Join(reasons, "; "))
				}
			}
		})

	// ---------------------------------------------------------------------
	// T294's REFUSAL, RE-ADJUDICATED AND UPHELD — as a RULE, not a judgement
	// ---------------------------------------------------------------------
	t.Run("OB-01's 26-id args CANNOT be graded, and the store cannot express the claim",
		func(t *testing.T) {
			// LDG-REFUSE-03's refusal code is neither of the two whose throw sites
			// pass a LocalDate, so ANY selector on it is refused. This is the whole
			// of T294's position, mechanised: it no longer depends on a later
			// author remembering why OB-01 was left alone.
			for _, sel := range []string{ArgEchoLatestClosingDate, ArgEchoTransactionDate} {
				v := *byID[refuse03]
				v.Expect.Refusal.ArgEcho = sel
				reasons := Admit(&v, opts)
				if !containsSubstring(reasons, "An arg echo is admitted ONLY on") {
					t.Fatalf("LDG-REFUSE-03 with arg_echo %q was ADMITTED. Its args carries 26 LIVE "+
						"TRANSACTION IDS and any unrelated posting to the tenant changes them; "+
						"grading it would pin a parity claim to mutable tenant history (T294): %v",
						sel, reasons)
				}
			}

			// AND THE LIST ITSELF HAS NO NAME. There is no selector that resolves to
			// request.posted_non_contra_transaction_ids, so even on a vector whose
			// code WERE admitted the claim could not be written down. Checked
			// through ResolveArgEcho, which is the single definition the comparator
			// and the gate share.
			for _, sel := range []string{
				"posted_non_contra_transaction_ids", "args", "transaction_ids", "value",
			} {
				if _, ok := ResolveArgEcho(sel, byID[refuse03].Request); ok {
					t.Fatalf("the selector vocabulary resolves %q. It is CLOSED to the two scalar "+
						"calendar dates on purpose: a selector naming tenant-mutable history is "+
						"how the OB-01 refusal would be quietly reversed", sel)
				}
			}
		})

	t.Run("the vocabulary is CLOSED and an unknown selector REFUSES", func(t *testing.T) {
		for _, sel := range []string{"business_date", "closing_date", "TRANSACTION_DATE", "x"} {
			v := *byID[refuse04]
			v.Expect.Refusal.ArgEcho = sel
			if reasons := Admit(&v, opts); !containsSubstring(reasons, "The vocabulary is CLOSED to") {
				t.Fatalf("arg_echo %q was admitted as a known selector: %v", sel, reasons)
			}
		}
		// PAIRED GREEN: `business_date` is refused above even though it IS a
		// declared request input and IS a scalar date. That is deliberate and it is
		// the T329 half of the formulation — the business date is derived from a
		// WALL CLOCK (DateUtils.getLocalDateOfTenant), and :631 does not echo it.
		// A vocabulary admitting it would let a vector grade a clock-derived value
		// as a literal, which is the hazard T329 measured.
		if _, ok := ResolveArgEcho("business_date", byID[refuse04].Request); ok {
			t.Fatal("business_date resolves as a selector. It is the WALL-CLOCK-derived date on " +
				"this path and the oracle never echoes it (:631 passes transactionDate); admitting " +
				"it would let a vector grade a value that moves with the hour CI runs")
		}
	})

	t.Run("the selector is BOUND TO THE CODE, both directions", func(t *testing.T) {
		// Wrong way round on each of the two date refusals.
		v := *byID[refuse04] // accounting.closed
		v.Expect.Refusal.ArgEcho = ArgEchoTransactionDate
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "it must be \"latest_closing_date\"") {
			t.Fatalf("accounting.closed with arg_echo transaction_date was admitted: %v", reasons)
		}
		w := *byID[refuse05] // future.date
		w.Expect.Refusal.ArgEcho = ArgEchoLatestClosingDate
		if reasons := Admit(&w, opts); !containsSubstring(reasons, "it must be \"transaction_date\"") {
			t.Fatalf("future.date with arg_echo latest_closing_date was admitted: %v", reasons)
		}
	})

	t.Run("the selector is REQUIRED, not optional", func(t *testing.T) {
		// The deflation direction. An optional cell is one an author drops the day
		// it becomes inconvenient, and nothing would notice.
		for _, id := range []string{refuse04, refuse05, refuse06} {
			v := *byID[id]
			v.Expect.Refusal.ArgEcho = ""
			if reasons := Admit(&v, opts); !containsSubstring(reasons, "grades one cell fewer than the capture supports") {
				t.Fatalf("%s with arg_echo dropped was ADMITTED: %v", id, reasons)
			}
		}
	})

	t.Run("a selector resolving to NOTHING refuses", func(t *testing.T) {
		v := *byID[refuse06]
		v.Request.LatestClosingDate = ""
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "a comparison that cannot fail") {
			t.Fatalf("a selector resolving to the empty string was admitted, so the comparator "+
				"would grade \"\" against \"\": %v", reasons)
		}
	})

	t.Run("the store cannot express a graded DATE LITERAL", func(t *testing.T) {
		// Refusal.Arg0Value is `json:"-"`, so a vector trying to write the answer
		// side dies at STRICT DECODE with an unknown field. The rule "grade the
		// relation, never the calendar" is therefore enforced by the type rather
		// than by a reviewer noticing.
		raw := []byte(`{"http_status":403,"code":"c","message":"m","arg0_value":"2026-01-31"}`)
		var r Refusal
		if err := strictDecodeRefusalForTest(raw, &r); err == nil {
			t.Fatalf("a Refusal carrying arg0_value decoded cleanly to %+v. The store must not be "+
				"able to write a date literal into an expectation", r)
		} else if !strings.Contains(err.Error(), "unknown field") {
			t.Fatalf("decoding arg0_value failed for the wrong reason: %v", err)
		}
	})

	// ---------------------------------------------------------------------
	// THE CELL IS REALLY COMPARED, AND IT REALLY DISCRIMINATES
	// ---------------------------------------------------------------------
	t.Run("refusal.arg0_value is in the DERIVED cell vocabulary", func(t *testing.T) {
		if !IsCellField("refusal.arg0_value") {
			t.Fatalf("the comparator's derived vocabulary does not contain refusal.arg0_value; "+
				"every graded_against row naming it would be INADMISSIBLE. Vocabulary: %v",
				CellFields())
		}
	})

	t.Run("the mutant dies on LDG-REFUSE-06 ALONE, and passes LDG-REFUSE-04", func(t *testing.T) {
		o := opts
		o.Implementation = accountingClosedEchoesTransactionDatePoster{}
		var died []string
		for _, v := range vs {
			if r := gradeOne(v, o); r.Outcome == OutcomeFail {
				died = append(died, v.CaseID)
			} else if r.Outcome != OutcomePass {
				t.Fatalf("%s produced %q, which this measurement cannot interpret: %v",
					v.CaseID, r.Outcome, r.Detail)
			}
		}
		if len(died) != 1 || died[0] != refuse06 {
			t.Fatalf("the mutant died on %v, want exactly [%s]. If it died on LDG-REFUSE-04 too "+
				"the corpus is not measuring what it claims: A2-01 was posted ON the closing date, "+
				"so the two dates are EQUAL there and a port echoing either one is correct on it. "+
				"If it died nowhere, LDG-REFUSE-06 is corpus inflation", died, refuse06)
		}
	})

	t.Run("A2-01 and A2-02 differ ONLY in the selector's resolved value", func(t *testing.T) {
		// The measurement that makes LDG-REFUSE-06 worth a file: T295 recorded that
		// the two captured BODIES are byte-identical (both sha256 c12e977f…), so the
		// two vectors must agree on all three original cells and disagree on the
		// fourth. Re-derived here from the committed vectors rather than quoted.
		a, b := byID[refuse04], byID[refuse06]
		if a.Provenance.CaptureSHA256 != b.Provenance.CaptureSHA256 {
			t.Fatalf("the two vectors cite different response digests (%s vs %s). The whole reason "+
				"LDG-REFUSE-06 needed a fourth cell is that its body is BYTE-IDENTICAL to A2-01's",
				a.Provenance.CaptureSHA256, b.Provenance.CaptureSHA256)
		}
		for _, pair := range []struct{ name, x, y string }{
			{"code", a.Expect.Refusal.Code, b.Expect.Refusal.Code},
			{"message", a.Expect.Refusal.Message, b.Expect.Refusal.Message},
			{"arg_echo", a.Expect.Refusal.ArgEcho, b.Expect.Refusal.ArgEcho},
		} {
			if pair.x != pair.y {
				t.Fatalf("refusal.%s differs between the two vectors (%q vs %q) and it must not: "+
					"their captured bodies are the same bytes", pair.name, pair.x, pair.y)
			}
		}
		if a.Expect.Refusal.HTTPStatus != b.Expect.Refusal.HTTPStatus {
			t.Fatal("refusal.http_status differs between two vectors built from identical bytes")
		}
		// AND THE RESOLVED VALUES ARE WHERE THEY PART. On LDG-REFUSE-04 the two
		// candidate selectors resolve to the SAME string, which is precisely why it
		// cannot discriminate; on LDG-REFUSE-06 they differ.
		aClose, _ := ResolveArgEcho(ArgEchoLatestClosingDate, a.Request)
		aTxn, _ := ResolveArgEcho(ArgEchoTransactionDate, a.Request)
		bClose, _ := ResolveArgEcho(ArgEchoLatestClosingDate, b.Request)
		bTxn, _ := ResolveArgEcho(ArgEchoTransactionDate, b.Request)
		if aClose != aTxn {
			t.Fatalf("LDG-REFUSE-04's two dates differ (%q vs %q); the vector's whole claim is that "+
				"A2-01 was posted ON the closing date", aClose, aTxn)
		}
		if bClose == bTxn {
			t.Fatalf("LDG-REFUSE-06's two dates are EQUAL (%q). It is promoted for exactly one "+
				"reason -- that they differ -- and if they did not, it would kill nothing that "+
				"LDG-REFUSE-04 does not already kill", bClose)
		}
		t.Logf("LDG-REFUSE-04 closing==txn==%q (cannot discriminate); "+
			"LDG-REFUSE-06 closing=%q txn=%q (discriminates)", aClose, bClose, bTxn)
	})
}
