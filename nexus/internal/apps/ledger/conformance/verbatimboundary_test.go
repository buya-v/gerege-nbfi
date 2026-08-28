package conformance

import (
	"strings"
	"testing"
)

// T397 — closing T387's F-T387-2: `verbatimInCapture` was a bare `bytes.Contains`,
// so a NUMERIC PREFIX of the captured amount satisfied it.
//
// "100.12" is contained in a capture holding "100.125", so a divergence vector
// could cite a shorter number than the artefact carries and the byte check would
// say nothing about it. T387 drove that as attack A17 and showed the class
// SELF-CORRECTING — the port converts the representable "100.12" happily, posts,
// and the divergence comparator then FAILs the vector, exit 1 — which is why it
// was MINOR rather than a fail-open.
//
// IT IS CLOSED ANYWAY, AND THE SELF-CORRECTION IS KEPT AS A CONTROL. P-45: a
// check that is only saved by a downstream check is one refactor away from being
// saved by nothing. The first test below is the new primary check; the last is
// the downstream one, asserted directly so that if a later change removes either,
// exactly one test goes red and names which layer was lost.
//
// NOT ONE NUMBER IS FORMED IN THIS FILE OR IN THE CODE IT EXERCISES. No strconv,
// no float, no arithmetic on any captured amount, no exponent — the boundary is
// decided by classifying a single neighbouring BYTE. A numeric comparison would
// be the "proper" fix and it is forbidden: no int64 holds 100.125, and a parse
// here is the defect this class exists to prevent.

// TestANumericPrefixOfTheCapturedAmountIsNotVerbatim is the RED-before-GREEN
// drive. Before T397's change every sub-test below ADMITS; after it, every one
// refuses, and the control at the bottom proves the rule did not simply refuse
// everything.
func TestANumericPrefixOfTheCapturedAmountIsNotVerbatim(t *testing.T) {
	// THE CONTROL COMES FIRST, deliberately. If the committed vector's own
	// unmutated texts stopped being admissible, every arm below would refuse for
	// a reason that has nothing to do with the boundary rule and this whole file
	// would pass while testing nothing (P-35).
	t.Run("control_the_unmutated_vector_still_admits", func(t *testing.T) {
		v, opts := divergenceVector(t)
		if reasons := Admit(v, opts); len(reasons) > 0 {
			t.Fatalf("the COMMITTED divergence vector is now INADMISSIBLE, so the boundary rule "+
				"refuses honest citations too and every arm below is vacuous: %s",
				strings.Join(reasons, "; "))
		}
	})

	// T387's A17, exactly: both request legs truncated from "100.125" to
	// "100.12". The capture (.req) carries `"amount": 100.125}`, so a substring
	// match finds "100.12" and is satisfied by a number the caller never sent.
	t.Run("request_side_prefix_A17", func(t *testing.T) {
		v, opts := divergenceVector(t)
		legs := make([]RequestLeg, len(v.Request.Legs))
		copy(legs, v.Request.Legs)
		for i := range legs {
			legs[i].AmountMajorText = "100.12"
		}
		v.Request.Legs = legs
		mustRefuse(t, v, opts, "ONLY GLUED TO A LONGER NUMBER")
		mustRefuse(t, v, opts, "provenance.request_capture_ref")
	})

	// The same trick on the ORACLE side. "100.12500" still carries a residue
	// beyond the minor unit, so the unrepresentability rule is satisfied and this
	// isolates the boundary rule — and it is a prefix of the captured
	// "100.125000".
	t.Run("oracle_side_prefix", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.OracleAccepted.ObservedAmountTexts = []string{"100.12500"}
		mustRefuse(t, v, opts, "ONLY GLUED TO A LONGER NUMBER")
		mustRefuse(t, v, opts, "provenance.capture_ref")
	})

	// A TAIL, not a prefix. "00.125000" is contained in "100.125000" with a digit
	// glued to its left, and it denotes a different amount.
	t.Run("oracle_side_tail", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.OracleAccepted.ObservedAmountTexts = []string{"00.125000"}
		mustRefuse(t, v, opts, "ONLY GLUED TO A LONGER NUMBER")
	})

	// A text that is not in the artefact AT ALL must still refuse with the OLD
	// diagnostic, not the new one. The two are different mistakes — a
	// transcription from nowhere versus a truncation of the artefact's own number
	// — and collapsing them into one message would lose the reader the
	// difference.
	t.Run("absent_text_keeps_the_original_diagnostic", func(t *testing.T) {
		v, opts := divergenceVector(t)
		v.OracleAccepted.ObservedAmountTexts = []string{"999.999999"}
		reasons := Admit(v, opts)
		if !containsSubstring(reasons, "DO NOT OCCUR in provenance.capture_ref") {
			t.Fatalf("wanted the ABSENT diagnostic, got: %s", strings.Join(reasons, "; "))
		}
		if containsSubstring(reasons, "ONLY GLUED TO A LONGER NUMBER") {
			t.Fatalf("an absent text was reported as a truncation: %s", strings.Join(reasons, "; "))
		}
	})
}

// TestTheBoundaryRuleFormsNoNumber exercises tokenBoundedIndex directly, on
// values chosen so that any implementation that parsed either side would answer
// differently or lose digits: 19+ significant digits, an exponent form, a sign,
// and trailing-zero forms that are numerically equal but textually distinct.
//
// THE RULE IS ABOUT CHARACTERS, NOT VALUES, and these rows say so. "100.12" and
// "100.120" denote the same number; the second is not present in a capture
// holding only the first, and this function must say so without knowing that they
// are numerically equal.
func TestTheBoundaryRuleFormsNoNumber(t *testing.T) {
	cases := []struct {
		name   string
		raw    string
		needle string
		want   bool // want a token-bounded occurrence
	}{
		{"exact_json_number", `{"amount":100.125000,"x":1}`, "100.125000", true},
		{"prefix_of_a_longer_number", `{"amount":100.125000,"x":1}`, "100.12", false},
		{"prefix_by_one_digit", `{"amount":100.125,"x":1}`, "100.12", false},
		{"tail_of_a_longer_number", `{"amount":100.125000}`, "00.125000", false},
		{"quoted_string_form", `{"amount":"100.125"}`, "100.125", true},
		{"whole_number_glued_to_a_fraction", `{"amount":100.125}`, "100", false},
		{"sign_on_the_left", `{"amount":-100.125}`, "100.125", false},
		{"exponent_on_the_right", `{"amount":100.12e3}`, "100.12", false},
		// The needle is genuinely absent. -1 either way, and the caller reports
		// that case with the older, different diagnostic.
		{"absent", `{"amount":100.125000}`, "999.999", false},
		// Numerically equal, textually different. The rule must not "helpfully"
		// find this.
		{"trailing_zero_form_is_a_different_string", `{"amount":100.12}`, "100.120", false},
		// SECOND OCCURRENCE RESCUES. Both legs of a balanced entry carry the same
		// characters; the first here is glued, the second is not, and one honest
		// occurrence is the whole claim.
		{"one_bounded_occurrence_is_enough", `{"a":1100.125,"b":100.125}`, "100.125", true},
		// 19 significant digits — past float64 entirely. A parsing implementation
		// would have lost the tail before it could compare anything.
		{"nineteen_significant_digits", `{"a":1234567890123456.001}`, "1234567890123456.001", true},
		{"nineteen_significant_digits_prefix", `{"a":1234567890123456.001}`, "1234567890123456.00", false},
		{"at_start_of_buffer", `100.125,`, "100.125", true},
		{"at_end_of_buffer", `x=100.125`, "100.125", true},
		{"empty_needle_never_matches", `{"amount":100.125}`, "", false},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := tokenBoundedIndex([]byte(c.raw), []byte(c.needle)) >= 0
			if got != c.want {
				t.Errorf("tokenBoundedIndex(%q, %q) bounded = %v, want %v", c.raw, c.needle, got, c.want)
			}
		})
	}
}

// TestThePrefixIsStillCaughtDownstreamIfAdmissionIsBypassed is T387's
// self-correction, RETAINED AS A CONTROL rather than retired now that admission
// closes the hole.
//
// It grades the A17 mutation the way gradeOne would AFTER Admit — deliberately
// skipping Admit, because after T397 the vector never reaches the comparator and
// the downstream check would otherwise become unobservable and then, silently,
// removable. Two independent layers now refuse the prefix, and this test is the
// one that goes red if the second is lost.
func TestThePrefixIsStillCaughtDownstreamIfAdmissionIsBypassed(t *testing.T) {
	v, _ := divergenceVector(t)
	legs := make([]RequestLeg, len(v.Request.Legs))
	copy(legs, v.Request.Legs)
	for i := range legs {
		// The representable truncation. The port has no residue to refuse for,
		// so it posts — which is exactly why the comparator catches it.
		legs[i].AmountMajorText = "100.12"
	}
	v.Request.Legs = legs

	_, refusal, err := NewGoPoster().PostEntry(v.Request)
	var ds cellSink
	diffDivergence(&ds, v, refusal, err)

	if len(ds.diffs) == 0 {
		t.Fatal("the divergence comparator ACCEPTED the prefix mutation. T387 measured this same " +
			"shape FAILing with `divergence.port_outcome: want \"REFUSED\", got \"ACCEPTED\"`, and " +
			"that downstream refusal is the SECOND of the two layers guarding F-T387-2. If it is " +
			"gone, admission is the only thing left and P-45's shape has re-appeared")
	}
	if !containsSubstring(ds.diffs, `divergence.port_outcome: want "REFUSED", got "ACCEPTED"`) {
		t.Errorf("the comparator failed, but not for the recorded reason. Diffs: %s",
			strings.Join(ds.diffs, "; "))
	}
	if !containsSubstring(ds.diffs, "THE DIVERGENCE HAS MOVED") {
		t.Errorf("the comparator did not say the divergence had moved. Diffs: %s",
			strings.Join(ds.diffs, "; "))
	}
	if ds.money != 0 {
		t.Errorf("the divergence comparator graded %d MONEY cells; the class has none and must "+
			"never acquire one", ds.money)
	}

	// AND THE CONTROL FOR THE CONTROL: the UNMUTATED vector still passes the same
	// comparator, so the FAIL above is caused by the mutation and not by a
	// comparator that fails everything.
	u, _ := divergenceVector(t)
	_, uRefusal, uErr := NewGoPoster().PostEntry(u.Request)
	var us cellSink
	diffDivergence(&us, u, uRefusal, uErr)
	if len(us.diffs) != 0 {
		t.Fatalf("the UNMUTATED divergence vector also fails the comparator, so the arm above "+
			"demonstrates nothing: %s", strings.Join(us.diffs, "; "))
	}
}
