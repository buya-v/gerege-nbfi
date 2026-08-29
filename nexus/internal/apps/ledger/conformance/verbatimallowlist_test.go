package conformance

import "testing"

// T416 — THE BOUNDARY RULE IS AN ALLOWLIST, closing T405's F-T405-2 and F-T405-3.
//
// The rule T397 shipped was a BLACKLIST — four bytes named on the left
// (`digit . - +`), four on the right (`digit . e E`) — so every byte nobody had
// thought of was accepted as a boundary. It failed OPEN six ways and, for
// exactly the same reason, CLOSED six ways. Both sets are asserted here, in one
// table, because they are one defect: a rule that classifies by exclusion cannot
// answer a question it was never asked.
//
// It lives beside verbatimboundary_test.go rather than inside it so that T397's
// own drive stays byte-identical and readable as the record of what T397 fixed.
//
// STILL NOT ONE NUMBER IS FORMED IN THIS FILE OR IN THE CODE IT EXERCISES. Every
// row is decided by asking whether a single byte is a digit or a letter. No
// strconv, no float, no arithmetic on any amount — only on byte offsets. A
// numeric comparison would be the "proper" fix and it is forbidden: no int64
// holds 100.125 (CLAUDE.md, first non-negotiable).

func TestTheBoundaryAllowlistClosesBothDirections(t *testing.T) {
	cases := []struct {
		name    string
		raw     string
		needle  string
		want    bool // want a token-bounded occurrence
		finding string
	}{
		// F-T405-2 — FALSE ADMISSIONS. Each of these ADMITTED before T416 and
		// each cites a value the artefact does not carry.
		{"thousands_separator_tail", `{"formatted":"1,250,000.00"}`, "250,000.00", false,
			"F-T405-2: `,` was in neither neighbour set, so a prefix wearing a thousands separator admitted"},
		{"thousands_separator_A17", `{"formatted":"1,100.12"}`, "100.12", false,
			"F-T405-2: F-T387-2's own case, wearing a thousands separator"},
		{"trailing_minus_accounting", `{"formatted":"100.12-"}`, "100.12", false,
			"F-T405-2: the captured value is NEGATIVE. `-` was put in the LEFT set because a sign " +
				"changes the value; that argument is symmetric and was not applied on the right"},
		{"trailing_plus", `{"formatted":"100.12+"}`, "100.12", false,
			"F-T405-2: the same row, other sign"},
		{"space_separated_group", `{"formatted":"1 250 000.00"}`, "250 000.00", false,
			"F-T405-2: a space group separator"},
		{"underscore_separator", `{"raw":100_125}`, "125", false,
			"F-T405-2: an underscore digit separator"},

		// F-T405-3 — FALSE REFUSALS. Each of these REFUSED an honest citation
		// before T416. P-98: a false refusal is as serious as a false admission.
		{"prose_full_stop", `Total posted was 100.125. See note.`, "100.125", true,
			"F-T405-3: a sentence-ending full stop is not a decimal point"},
		{"form_encoded_plus", `note=paid+100.125&locale=en`, "100.125", true,
			"F-T405-3: `+` in x-www-form-urlencoded is a SPACE, not a sign"},
		{"currency_code_EUR", `{"formatted":"100.125EUR"}`, "100.125", true,
			"F-T405-3: `E` here begins a currency code, not an exponent"},
		{"hyphen_identifier_prefix", `id-100.125`, "100.125", true,
			"F-T405-3: a hyphen separating an identifier from a number is not a sign"},
		{"range_dash", `range 50.00-100.125`, "100.125", true,
			"F-T405-3: a range dash is not a sign"},
		{"filename_extension_dot", `T352-amount-100.125.req`, "100.125", true,
			"F-T405-3: an extension dot is not a decimal point"},

		// THE CURRENCY ASYMMETRY, asserted as a PAIR. Before T416 `...MNT`
		// admitted while `...EUR` refused, so whether an honest citation was
		// accepted depended on which currency code happened to begin with `e`.
		// This corpus is MNT today and need not be forever.
		{"currency_code_MNT", `{"formatted":"100.125MNT"}`, "100.125", true,
			"F-T405-3: the MNT half of the pair — it must agree with the EUR row"},

		// STILL REFUSED, and T405 records this one as CORRECT: the artefact
		// carries a negative and the citation claims a positive.
		{"csv_field_with_a_negative", `16,-100.125,DEBIT`, "100.125", false,
			"a leading sign with no token beside it is a SIGN, and a sign changes the value"},

		// THE EXPONENT IS STILL AN EXPONENT wherever one can actually follow.
		{"exponent_bare", `{"a":100.12e3}`, "100.12", false, "e followed by a digit"},
		{"exponent_signed_plus", `{"a":100.12e+3}`, "100.12", false, "e, a sign, then a digit"},
		{"exponent_signed_minus", `{"a":100.12e-3}`, "100.12", false, "e, a sign, then a digit"},

		// AND THE SEPARATOR READING OF `-`/`+` DOES NOT SWALLOW THE SIGN
		// READING. A sign at the start of the buffer, or after a delimiter, is
		// still a sign, which is T397's `sign_on_the_left` row generalised.
		{"sign_at_start_of_buffer", `-100.125`, "100.125", false, "nothing beside the sign to separate"},
		{"sign_after_a_bracket", `[-100.125]`, "100.125", false, "a delimiter beside the sign, so it signs"},
		{"sign_after_a_quote", `{"a":"-100.125"}`, "100.125", false, "the same, in string form"},

		// THE LIVE CAPTURE ALPHABET — THE HEALTHY CONTROL (P-98). A rule that
		// refuses everything is the same defect as one that cannot fail, so
		// every byte shape the cited artefacts actually use is asserted to
		// ADMIT. MEASURED, not guessed: across the 37 artefacts this vector
		// store cites, the bytes observed immediately beside a cited amount text
		// are ` ` and `:` on the left, and newline, `)`, `,` and `}` on the
		// right.
		{"live_left_space", "amount: 100.125\n", "100.125", true, "control"},
		{"live_left_colon", `{"amount":100.125}`, "100.125", true, "control"},
		{"live_right_comma", `{"amount":100.125,"x":1}`, "100.125", true, "control"},
		{"live_right_brace", `{"amount":100.125}`, "100.125", true, "control"},
		{"live_right_paren", `total(100.125)`, "100.125", true, "control"},
		{"live_right_newline", "amount: 100.125\nnext", "100.125", true, "control"},
		{"live_quoted", `{"amount":"100.125"}`, "100.125", true, "control"},
		{"live_end_of_buffer", `x=100.125`, "100.125", true, "control"},
		{"live_start_of_buffer", `100.125,`, "100.125", true, "control"},
		{"live_currency_symbol_utf8", "1250000₮", "1250000", true,
			"a byte >= 0x80 cannot be part of an ASCII decimal literal, so it delimits"},
	}
	var admits, refuses int
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := tokenBoundedIndex([]byte(c.raw), []byte(c.needle)) >= 0
			if got != c.want {
				t.Errorf("tokenBoundedIndex(%q, %q) bounded = %v, want %v\n    %s",
					c.raw, c.needle, got, c.want, c.finding)
			}
		})
		if c.want {
			admits++
		} else {
			refuses++
		}
	}
	// THE TABLE'S OWN ANTI-VACUITY ARM. A table that had drifted to all-refuse
	// or all-admit rows would still pass every sub-test above while asserting
	// nothing about a RULE. Both directions have to be populated for this file
	// to be evidence of one.
	if admits == 0 || refuses == 0 {
		t.Fatalf("the table asserts only one direction (%d admit, %d refuse); it cannot "+
			"distinguish a rule from a constant", admits, refuses)
	}
}

// TestAnUnnamedByteRefusesRatherThanAdmits is THE INVERSION ITSELF, asserted
// directly rather than left as a property of the code's shape. [T416, F-T405-2]
//
// The old rule enumerated the bytes that make a match NOT verbatim, so anything
// unlisted admitted — and "anything unlisted" is precisely the set nobody has
// reasoned about. The new rule enumerates the bytes that DELIMIT, so the
// unreasoned-about set refuses: exit 2 with a named reason a human fixes in the
// same fire, instead of a wrong amount accepted as the oracle's own characters.
//
// The residual set in ASCII is small — the C0 controls and DEL — and that is a
// fact about ASCII rather than a weakness of the shape. What matters is the
// DIRECTION: whichever bytes are not named, they fail closed.
func TestAnUnnamedByteRefusesRatherThanAdmits(t *testing.T) {
	const hex = "0123456789abcdef"
	for _, b := range []byte{0x00, 0x01, 0x07, 0x08, 0x0e, 0x1b, 0x1f, 0x7f} {
		name := "byte_0x" + string(hex[b>>4]) + string(hex[b&0x0f])
		t.Run(name+"_left", func(t *testing.T) {
			raw := append([]byte{b}, []byte("100.125")...)
			if tokenBoundedIndex(raw, []byte("100.125")) >= 0 {
				t.Errorf("byte %#02x was accepted as a left boundary without being named as one. "+
					"That is the blacklist's failure direction: an unforeseen byte admits silently", b)
			}
		})
		t.Run(name+"_right", func(t *testing.T) {
			raw := append([]byte("100.125"), b)
			if tokenBoundedIndex(raw, []byte("100.125")) >= 0 {
				t.Errorf("byte %#02x was accepted as a right boundary without being named as one", b)
			}
		})
	}
	// THE CONTROL: a NAMED byte in the same position admits, so the arms above
	// are testing the allowlist and not a function that refuses everything.
	if tokenBoundedIndex([]byte(`{"a":100.125}`), []byte("100.125")) < 0 {
		t.Fatal("a named delimiter also refuses, so the arms above demonstrate nothing")
	}
}

// TestTheAmbiguousGroupSeparatorResolvesTowardRefusal records a DECISION rather
// than a discovery. [T416, F-T405-2]
//
// `16,100.125,DEBIT` (a CSV field separator) and `1,100.125` (a thousands
// separator) are the same bytes in the same order, and nothing local can tell
// them apart. This rule refuses both. The cost is that a CSV artefact would have
// to widen its citation — exit 2, named reason, fixed in the same fire. The
// alternative cost is a wrong amount accepted, silently, as the reference
// oracle's own characters for a money value. Those two costs are not symmetric,
// and this test exists so the choice cannot be reversed by accident.
func TestTheAmbiguousGroupSeparatorResolvesTowardRefusal(t *testing.T) {
	if tokenBoundedIndex([]byte(`16,100.125,DEBIT`), []byte("100.125")) >= 0 {
		t.Error("digit-COMMA-digit admitted. It is indistinguishable from a thousands separator, " +
			"and the safe reading of an ambiguity about money is the refusing one")
	}
	// The unambiguous JSON forms are unaffected, which is the whole reason the
	// comma rule is conditional rather than making `,` an outright
	// non-delimiter — that would have refused the live capture alphabet.
	for _, raw := range []string{`{"a":100.125,"b":2}`, `[16, 100.125]`, `{"a":100.125}`} {
		if tokenBoundedIndex([]byte(raw), []byte("100.125")) < 0 {
			t.Errorf("%q refused, so the comma rule is not conditional at all", raw)
		}
	}
}
