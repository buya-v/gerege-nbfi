package parties

import (
	"errors"
	"strings"
	"testing"
)

// Cyrillic letters as explicit code points, so a Latin look-alike can never be
// typed by accident into an ID that is meant to be valid.
const (
	cyrA  = "\u0410" // А
	cyrB  = "\u0411" // Б
	cyrE  = "\u0401" // Ё
	cyrOe = "\u04E8" // Ө
	cyrUe = "\u04AE" // Ү
)

// Every ID in this file is SYNTHETIC. The trailing check pair is arbitrary
// because the real algorithm is unpublished, and no real person's number may
// appear here.
func TestValidateNationalID(t *testing.T) {
	cases := []struct {
		name string
		id   string
		rule NationalIDRule // "" means the ID is valid
	}{
		// valid, 19xx: MM 01-12
		{"19xx January", cyrA + cyrB + "90010112", ""},
		{"19xx December 31", cyrA + cyrB + "99123134", ""},
		// valid, 20xx: MM 21-32
		{"20xx month 21 is January", cyrA + cyrB + "01210134", ""},
		{"20xx month 32 is December 31", cyrA + cyrB + "05323199", ""},
		// valid, the three letters outside the А-Я block
		{"Ё and Ө accepted", cyrE + cyrOe + "00010199", ""},
		{"Ү accepted", cyrUe + cyrA + "00123110", ""},

		// the 29-February leap/non-leap pair
		{"2000-02-29 is a leap day", cyrA + cyrB + "00222912", ""},
		{"2024-02-29 is a leap day", cyrA + cyrB + "24222912", ""},
		{"1900-02-29 is NOT a leap year", cyrA + cyrB + "00022912", NationalIDRuleDay},
		{"2023-02-29 is NOT a leap year", cyrA + cyrB + "23222912", NationalIDRuleDay},

		// length is runes, not bytes
		{"9 runes", cyrA + cyrB + "9001011", NationalIDRuleLength},
		{"11 runes", cyrA + cyrB + "900101123", NationalIDRuleLength},
		{"empty", "", NationalIDRuleLength},
		{"five Cyrillic letters would be 10 bytes but only 5 runes", cyrA + cyrB + "\u0412\u0413\u0414", NationalIDRuleLength},

		// letters
		{"lowercase Cyrillic a", "\u0430" + cyrB + "90010112", NationalIDRuleLetter},
		{"Latin look-alike A", "A" + cyrB + "90010112", NationalIDRuleLetter},
		{"digit in letter position", cyrA + "1" + "90010112", NationalIDRuleLetter},
		{"leading whitespace", " " + cyrA + "90010112", NationalIDRuleLetter},

		// digits
		{"letter in digit position", cyrA + cyrB + "9001011" + cyrA, NationalIDRuleDigit},
		{"non-ASCII digit", cyrA + cyrB + "9001011\u0662", NationalIDRuleDigit},

		// embedded birth date: month
		{"month 00", cyrA + cyrB + "90000112", NationalIDRuleMonth},
		{"month 13", cyrA + cyrB + "90130112", NationalIDRuleMonth},
		{"month 20 is the gap", cyrA + cyrB + "90200112", NationalIDRuleMonth},
		{"month 33", cyrA + cyrB + "90330112", NationalIDRuleMonth},

		// embedded birth date: day
		{"day 00", cyrA + cyrB + "90010012", NationalIDRuleDay},
		{"day 31 in April", cyrA + cyrB + "90043112", NationalIDRuleDay},
		{"day 30 in February", cyrA + cyrB + "90023012", NationalIDRuleDay},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			err := ValidateNationalID(c.id)
			if c.rule == "" {
				if err != nil {
					t.Fatalf("ValidateNationalID(%q) = %v, want nil", c.id, err)
				}
				return
			}
			if err == nil {
				t.Fatalf("ValidateNationalID(%q) = nil, want rule %q", c.id, c.rule)
			}
			var ne *NationalIDError
			if !errors.As(err, &ne) {
				t.Fatalf("ValidateNationalID(%q) error type = %T, want *NationalIDError", c.id, err)
			}
			if ne.Rule != c.rule {
				t.Fatalf("ValidateNationalID(%q) failed rule %q, want %q (%v)", c.id, ne.Rule, c.rule, err)
			}
		})
	}
}

// TestValidateNationalIDAcceptsMongolianCyrillicUppercase proves the accepted
// letter set exactly: А-Я plus Ё, Ө, Ү, and nothing asserted about any other
// rune.
func TestValidateNationalIDAcceptsMongolianCyrillicUppercase(t *testing.T) {
	var letters []rune
	for r := '\u0410'; r <= '\u042F'; r++ {
		letters = append(letters, r)
	}
	letters = append(letters, '\u0401', '\u04E8', '\u04AE') // Ё Ө Ү

	for _, l := range letters {
		// Pair each letter with А so the second letter position is known-good.
		id := string([]rune{l, '\u0410'}) + "90010112"
		if err := ValidateNationalID(id); err != nil {
			t.Errorf("letter %q: ValidateNationalID(%q) = %v, want nil", l, id, err)
		}
	}
}

// TestValidateNationalIDRejectsNonMongolianCyrillicUppercase covers the letters
// that must NOT pass: lowercase, Latin look-alikes, a Cyrillic letter outside
// А-Я, and whitespace.
func TestValidateNationalIDRejectsNonMongolianCyrillicUppercase(t *testing.T) {
	rejected := []rune{
		'\u0430', // а lowercase Cyrillic
		'\u0431', // б lowercase Cyrillic
		'\u0451', // ё lowercase Cyrillic
		'\u04E9', // ө lowercase
		'\u04AF', // ү lowercase
		'A',      // Latin A
		'P',      // Latin P
		'O',      // Latin O
		'B',      // Latin B
		'\u0402', // Ђ, Cyrillic but outside А-Я
		' ',      // whitespace
	}
	for _, l := range rejected {
		id := string([]rune{l, '\u0410'}) + "90010112"
		err := ValidateNationalID(id)
		var ne *NationalIDError
		if !errors.As(err, &ne) || ne.Rule != NationalIDRuleLetter {
			t.Errorf("letter %q: ValidateNationalID(%q) = %v, want a %q error", l, id, err, NationalIDRuleLetter)
		}
	}
}

// TestNationalIDErrorNamesTheFailedRule proves the error carries the rule, not
// merely a message a caller would have to parse.
func TestNationalIDErrorNamesTheFailedRule(t *testing.T) {
	err := ValidateNationalID("\u0430" + cyrB + "90010112")
	var ne *NationalIDError
	if !errors.As(err, &ne) {
		t.Fatalf("error type = %T, want *NationalIDError", err)
	}
	if ne.Rule != NationalIDRuleLetter {
		t.Fatalf("Rule = %q, want %q", ne.Rule, NationalIDRuleLetter)
	}
	if !strings.Contains(err.Error(), string(NationalIDRuleLetter)) {
		t.Fatalf("message %q does not name the rule %q", err.Error(), NationalIDRuleLetter)
	}
}
