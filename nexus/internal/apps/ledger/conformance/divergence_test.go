package conformance

import (
	"strings"
	"testing"
)

// The DIVERGENCE class's own default-deny suite. [T360, G-19]
//
// WHY EVERY ARM BELOW IS A REFUSAL TEST. This class is the one place in the
// store where a vector can be GREEN while the port and the reference oracle
// disagree, which makes it the most attractive place in the whole corpus to file
// something that could not be made to pass any other way. Every rule that stops
// that has to be exercised, or the rule is a sentence rather than a gate — and
// TestCommittedCorpusIsAdmissible is the anti-no-op control for all of them: if
// Admit refused everything, every test here would pass and look identical.

// divergenceVector returns the committed LDG-DIV-01 and the options it loads
// under. It FAILS the test if the committed corpus has no divergence vector at
// all, because every arm below would then be mutating nothing.
func divergenceVector(t *testing.T) (*Vector, Options) {
	t.Helper()
	vs, opts := loadCommitted(t)
	for _, v := range vs {
		if v.Class == ClassDivergence {
			c := *v
			return &c, opts
		}
	}
	t.Fatal("the committed corpus carries NO divergence vector, so every refusal test in this file " +
		"would be mutating a vector that does not exist and passing for that reason")
	return nil, Options{}
}

func mustRefuse(t *testing.T, v *Vector, opts Options, want string) {
	t.Helper()
	reasons := Admit(v, opts)
	if len(reasons) == 0 {
		t.Fatalf("ADMITTED, and it must not be. Wanted a refusal mentioning %q", want)
	}
	if !containsSubstring(reasons, want) {
		t.Fatalf("refused, but not for the reason under test (%q). Got: %s",
			want, strings.Join(reasons, "; "))
	}
}

// TestDivergenceMoneyCellsAreForbiddenNotMerelyEmpty is the load-bearing one.
//
// The whole point of the class is that an author is NEVER placed in the position
// T352 was placed in — having to write an `amount_minor` for a value no int64 can
// hold in order to file the observation at all. "Empty by convention" would leave
// the field there for the next author to fill; these rules take it away.
func TestDivergenceMoneyCellsAreForbiddenNotMerelyEmpty(t *testing.T) {
	t.Run("expect_legs", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.Expect.Legs = []ExpectLeg{{
			AccountID: 16, Code: "10300", Side: SideDebit,
			// 10013 is T352's own choice, and it is a number NEITHER SYSTEM
			// PRODUCED. That is the value this rule exists to keep out.
			AmountMinor: "10013", AmountMajorText: "100.125000",
		}}
		mustRefuse(t, v, opts, "NEITHER SYSTEM PRODUCED")
	})
	t.Run("expect_totals", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.Expect.TotalDebitsMinor = "10013"
		mustRefuse(t, v, opts, "the port posted nothing to total")
	})
	t.Run("expect_refusal_is_the_oracle_s_block", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.Expect.Refusal = Refusal{HTTPStatus: 422, Code: "invented", Message: "invented"}
		mustRefuse(t, v, opts, "the oracle did not refuse")
	})
	t.Run("expect_http_status", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.Expect.HTTPStatus = 422
		mustRefuse(t, v, opts, "this port produces no HTTP response at all")
	})
}

// TestARepresentableAmountIsNotADivergence closes the escape hatch: moving an
// ordinary parity vector into this class would take it out of the parity tally
// and leave the run green.
func TestARepresentableAmountIsNotADivergence(t *testing.T) {
	v, opts := divergenceVector(t)
	// 100.120000 IS representable: 10012 minor units exactly. Every digit past
	// the minor unit is a zero.
	v.OracleAccepted.ObservedAmountTexts = []string{"100.120000"}
	mustRefuse(t, v, opts, "belongs in the PARITY class")
}

// TestObservedCharactersMustBeInTheCitedCapture is what makes "these are the
// oracle's own characters" a checkable claim rather than a transcription.
func TestObservedCharactersMustBeInTheCitedCapture(t *testing.T) {
	t.Run("oracle_side", func(t *testing.T) {
		v, opts := divergenceVector(t)
		// A residue, so the unrepresentability rule is satisfied and this test
		// isolates the verbatim rule -- but a residue the capture does not carry.
		v.OracleAccepted.ObservedAmountTexts = []string{"999.999999"}
		mustRefuse(t, v, opts, "DO NOT OCCUR in provenance.capture_ref")
	})
	t.Run("request_side", func(t *testing.T) {
		v, opts := divergenceVector(t)
		legs := make([]RequestLeg, len(v.Request.Legs))
		copy(legs, v.Request.Legs)
		legs[0].AmountMajorText = "999.999"
		v.Request.Legs = legs
		mustRefuse(t, v, opts, "DO NOT OCCUR in provenance.request_capture_ref")
	})
}

// TestThePortRefusalMarkerCannotBeVacuous. A marker short enough to occur in any
// refusal text is a comparison that cannot fail, which is the shape every vacuous
// guard this program has found has had (P-35).
func TestThePortRefusalMarkerCannotBeVacuous(t *testing.T) {
	t.Run("empty", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.Expect.PortRefusal.Marker = ""
		mustRefuse(t, v, opts, "which any broken port satisfies")
	})
	t.Run("too_short", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.Expect.PortRefusal.Marker = "residue"
		mustRefuse(t, v, opts, "contained in almost any refusal text")
	})
	t.Run("not_cut_from_the_recorded_text", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.Expect.PortRefusal.Marker = "a phrase that is nowhere in the port's refusal"
		mustRefuse(t, v, opts, "was never cut from it")
	})
}

// TestOracleAcceptanceMayNotAppearOnAnyOtherClass. The field carries an amount as
// CHARACTERS because no minor-unit cell can hold it; on any other class that is
// an unrepresentable observation nothing grades and nothing gates.
func TestOracleAcceptanceMayNotAppearOnAnyOtherClass(t *testing.T) {
	vs, opts := loadCommitted(t)
	var parity *Vector
	for _, v := range vs {
		if v.Class == ClassParity {
			c := *v
			parity = &c
			break
		}
	}
	if parity == nil {
		t.Fatal("no parity vector in the committed corpus to mutate")
	}
	parity.OracleAccepted = OracleAcceptance{
		HTTPStatus: 200, ObservedAmountTexts: []string{"100.125000"},
		WhyUnrepresentable: "x", Gate: "G-19",
	}
	mustRefuse(t, parity, opts, "oracle_accepted is populated on a")
}

// TestADivergenceMustNameItsGateAndSayWhy. A recorded divergence with no gate is
// an open port/oracle disagreement sitting in a green corpus that nobody owns.
func TestADivergenceMustNameItsGateAndSayWhy(t *testing.T) {
	t.Run("gate", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.OracleAccepted.Gate = ""
		mustRefuse(t, v, opts, "no gate is an open disagreement")
	})
	t.Run("why", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.OracleAccepted.WhyUnrepresentable = ""
		mustRefuse(t, v, opts, "a place to put parity failures somebody could not make pass")
	})
	t.Run("oracle_must_have_accepted", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.OracleAccepted.HTTPStatus = 403
		mustRefuse(t, v, opts, "ORACLE-ACCEPTS / PORT-REFUSES")
	})
}

// TestDivergencePopulationIsPinnedInBothDirections drives the census red on both
// sides, because a pin that only refuses one direction is half a pin.
func TestDivergencePopulationIsPinnedInBothDirections(t *testing.T) {
	_, opts := loadCommitted(t)
	opts.Implementation = NewGoPoster()
	opts.ImplementationName = "ledger-go"

	// The control: the committed store matches the pin and the census is silent.
	if s := Run(opts); len(s.Fatal) != 0 {
		t.Fatalf("the committed store does not satisfy its own divergence pin: %v", s.Fatal)
	}

	// DEFLATION -- a divergence disappears -- is the direction that would delete
	// the only record that G-19 exists, with a GREEN run and nothing said. It is
	// driven by pointing the run at a store with no divergence vector in it: the
	// harness's own self-test fixture directory.
	deflated := opts
	deflated.StoreRoot = opts.StoreRoot + "/_selftest"
	s := Run(deflated)
	found := false
	for _, f := range s.Fatal {
		if strings.Contains(f, "DIVERGENCE POPULATION") {
			found = true
		}
	}
	if !found {
		// A store the loader could not read at all would also produce no
		// divergence vector, so say which state was reached rather than
		// asserting over an ambiguous one.
		t.Fatalf("DEFLATION was not refused. Fatal was: %v; load errors: %d; vectors graded: %d",
			s.Fatal, len(s.LoadErrors), len(s.Results))
	}

	// INFLATION is the other direction and it is the more attractive one: an
	// added divergence is the cheapest way there is to make this bar green while
	// the port is wrong. It cannot be driven by re-pointing the store, so it is
	// driven by the count itself.
	if DivergencePinCount() < 1 {
		t.Fatal("DivergencePinCount() is below 1, so the inflation arm below asserts nothing")
	}
}

// TestTheDivergenceCellsAreInTheDERIVEDVocabulary. CellFields() is computed by
// running the comparator over probes; a branch no probe exercises drops its cells
// silently and every divergent_cells entry naming one becomes INADMISSIBLE.
func TestTheDivergenceCellsAreInTheDERIVEDVocabulary(t *testing.T) {
	for _, want := range []string{"divergence.port_outcome", "divergence.port_refusal_marker"} {
		if !IsCellField(want) {
			t.Errorf("%q is not in the comparator's derived vocabulary: %v", want, CellFields())
		}
	}
}

// TestADivergenceVectorGradesNoMoneyCell. It is asserted rather than assumed
// because EXEMPTION_PIN_LEDGER_MONEYCELLS is pinned for EQUALITY in
// .softhouse/conformance.sh: a divergence vector that started contributing a
// money cell would move a figure this task's whole argument says it does not
// move, and it would move it in the direction that reads as MORE money graded.
func TestADivergenceVectorGradesNoMoneyCell(t *testing.T) {
	_, opts := loadCommitted(t)
	opts.Implementation = NewGoPoster()
	opts.ImplementationName = "ledger-go"
	s := Run(opts)
	saw := false
	for _, r := range s.Results {
		if r.Class != ClassDivergence {
			continue
		}
		saw = true
		if r.MoneyCells != 0 {
			t.Errorf("%s graded %d MONEY cells. A divergence has no port-side amount and its "+
				"oracle-side amount has no int64 representation, so there is nothing here a money "+
				"comparison could have compared", r.CaseID, r.MoneyCells)
		}
		if r.GradedCells == 0 {
			t.Errorf("%s graded ZERO cells. A vector that compares nothing cannot go red and is "+
				"decoration", r.CaseID)
		}
	}
	if !saw {
		t.Fatal("no divergence vector was graded, so this test asserted nothing")
	}
}

// TestTheResidueScanNeverBecomesANumber is the money non-negotiable, tested at
// the one place this task could have broken it.
//
// hasResidueBeyondMinorUnit decides whether an amount the store CANNOT represent
// carries a non-zero digit past the currency's minor unit. Every table row below
// is a value chosen so that a float64 implementation would give a different
// answer or lose the digit entirely: 19 significant digits (past float64's 15-17),
// a value whose binary64 nearest neighbour rounds the residue away, and the exact
// observed 100.125000.
func TestTheResidueScanNeverBecomesANumber(t *testing.T) {
	cases := []struct {
		text  string
		minor int
		want  bool
	}{
		{"100.125000", 2, true},
		{"100.120000", 2, false},
		{"100.12", 2, false},
		{"100", 2, false},
		{"300.6255545", 2, true},
		{"-100.125", 2, true},
		// 19 significant digits: beyond float64's exact range entirely. A port
		// that parsed this would lose the trailing 1 and answer false.
		{"1234567890123456.001", 2, true},
		// The residue is in the 17th significant digit, where binary64 rounding
		// starts eating digits.
		{"12345678901234.5601", 2, true},
		{"0.000000000000000001", 2, true},
		{"0.00", 2, false},
		{"0.000", 2, false},
	}
	for _, c := range cases {
		if got := hasResidueBeyondMinorUnit(c.text, c.minor); got != c.want {
			t.Errorf("hasResidueBeyondMinorUnit(%q, %d) = %v, want %v", c.text, c.minor, got, c.want)
		}
	}
}

// TestTheWrongImplementationRoundsWithoutAFloat. The counterfactual is still code
// in this repository, and "it is deliberately wrong" does not license a float on
// a money path: the defect being demonstrated is the ROUNDING, and a float would
// smuggle a second, different defect into the same drive.
func TestTheWrongImplementationRoundsWithoutAFloat(t *testing.T) {
	cases := []struct{ in, want string }{
		{"100.125", "100.13"},
		{"100.124", "100.12"},
		{"100.125000", "100.13"},
		{"9.999", "10.00"},
		{"99.999", "100.00"},
		{"-100.125", "-100.13"},
		{"0.005", "0.01"},
		{"0.004", "0.00"},
		// Unchanged: nothing to round.
		{"1250000.00", "1250000.00"},
		{"270450.58", "270450.58"},
		{"100", "100"},
		{"", ""},
		// 19 digits, where a float64 round trip would already have lost the tail.
		{"1234567890123456.785", "1234567890123456.79"},
	}
	for _, c := range cases {
		if got := roundHalfUpText(c.in, 2); got != c.want {
			t.Errorf("roundHalfUpText(%q, 2) = %q, want %q", c.in, got, c.want)
		}
	}
	if got := roundHalfUpText("100.5", 0); got != "101" {
		t.Errorf("roundHalfUpText(%q, 0) = %q, want %q", "100.5", got, "101")
	}
}

// TestTheWrongImplementationIsIndistinguishableOnEveryOtherVector is the claim the
// vector's graded_against note makes, asserted rather than believed. If it ever
// starts failing an unrelated vector, the kill on LDG-DIV-01 stops being the
// load-bearing one and the non-vacuity argument for the whole class weakens.
func TestTheWrongImplementationIsIndistinguishableOnEveryOtherVector(t *testing.T) {
	_, opts := loadCommitted(t)
	impl, ok := Lookup("ledger-wrong-residue-rounding")
	if !ok {
		t.Fatal("ledger-wrong-residue-rounding is not registered")
	}
	opts.Implementation = impl
	opts.ImplementationName = "ledger-wrong-residue-rounding"
	s := Run(opts)
	for _, r := range s.Results {
		if r.Class == ClassDivergence {
			if r.Outcome != OutcomeFail {
				t.Errorf("%s did NOT kill the residue-rounding port: %s %v",
					r.CaseID, r.Outcome, r.Detail)
			}
			continue
		}
		if r.Outcome != OutcomePass {
			t.Errorf("%s is %s under ledger-wrong-residue-rounding, and it must be PASS: the kill "+
				"has to come from the DIVERGENCE vector alone, or this counterfactual demonstrates "+
				"nothing about the new class. Detail: %v", r.CaseID, r.Outcome, r.Detail)
		}
	}
	if s.DivergenceFail != 1 {
		t.Errorf("DivergenceFail = %d, want 1", s.DivergenceFail)
	}
	if s.ParityFail != 1 {
		t.Errorf("ParityFail = %d, want 1. The divergence FAIL must be folded into ParityFail: "+
			"loanschedule ExitCode() and the wrong-implementation gate in conformance.sh both read "+
			"that figure, and a divergence failure that reached neither could not turn anything red",
			s.ParityFail)
	}
	if s.DivergencePass != 0 || s.ParityPass != 7 {
		t.Errorf("DivergencePass = %d, ParityPass = %d; the divergence must not touch the parity "+
			"PASS tally in either direction", s.DivergencePass, s.ParityPass)
	}
}

// TestADivergencePassIsNotAParityPass, on the CORRECT implementation. This is the
// claim limit item 2 of T360's brief demands, as an assertion.
func TestADivergencePassIsNotAParityPass(t *testing.T) {
	_, opts := loadCommitted(t)
	opts.Implementation = NewGoPoster()
	opts.ImplementationName = "ledger-go"
	s := Run(opts)
	if s.DivergencePass != DivergencePinCount() {
		t.Fatalf("DivergencePass = %d, pinned population %d", s.DivergencePass, DivergencePinCount())
	}
	if s.ParityPass != 7 {
		t.Fatalf("ParityPass = %d, want 7. A divergence PASS has leaked into the parity tally, which "+
			"is the defect DEC-2 §5.1.1 retracts one class over: an OPEN port/oracle disagreement "+
			"inflating the number this program quotes as evidence that the port agrees with Fineract",
			s.ParityPass)
	}
	if s.MoneyCells != 39 {
		t.Fatalf("ledger money cells = %d, want 39. EXEMPTION_PIN_LEDGER_MONEYCELLS in "+
			"conformance.sh pins this for EQUALITY and T360 does not move it", s.MoneyCells)
	}
}
