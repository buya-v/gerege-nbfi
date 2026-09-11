package parties

import "fmt"

// NationalIDRule names the single structural rule a national ID failed. It
// exists so a caller can tell a length defect from a birth-date defect without
// parsing the message text.
type NationalIDRule string

const (
	// NationalIDRuleLength: the value is not exactly 10 runes.
	NationalIDRuleLength NationalIDRule = "length"
	// NationalIDRuleLetter: one of the first two runes is not an uppercase
	// Mongolian Cyrillic letter.
	NationalIDRuleLetter NationalIDRule = "letter"
	// NationalIDRuleDigit: one of the eight digit positions is not an ASCII
	// 0-9.
	NationalIDRuleDigit NationalIDRule = "digit"
	// NationalIDRuleMonth: the MM field is outside 01-12 and 21-32.
	NationalIDRuleMonth NationalIDRule = "month"
	// NationalIDRuleDay: the DD field is not a real day of the embedded month.
	NationalIDRuleDay NationalIDRule = "day"
)

// NationalIDError is returned by ValidateNationalID and names the rule that
// failed.
type NationalIDError struct {
	Rule   NationalIDRule
	Detail string
}

func (e *NationalIDError) Error() string {
	if e.Detail == "" {
		return "invalid national ID: " + string(e.Rule)
	}
	return "invalid national ID: " + string(e.Rule) + ": " + e.Detail
}

// nationalIDRunes is the exact rune length of a national ID.
const nationalIDRunes = 10

// ValidateNationalID validates a Mongolian national ID structurally. It says
// whether the value COULD be a national ID; it never says a real person holds
// it.
//
// The stated structure is 10 characters: two uppercase Mongolian Cyrillic
// letters followed by eight ASCII digits. The eight digits are YYMMDDNN, where
// the first six encode the birth date and the last two are the check pair.
//
// The birth date uses the "+20" rule: MM 01-12 means a 19YY birth, and MM 21-32
// means a 20YY birth whose calendar month is MM-20. DD must be a real day of
// that month and year, with leap years by the Gregorian rule (1900 is not a leap
// year; 2000 is).
//
// Two things this deliberately does NOT do:
//
//   - It does not validate the last two digits (positions 7-8 of the digit
//     field). The check-digit algorithm is unpublished; inventing one would
//     refuse real citizens.
//   - It does not infer sex, age, or any other attribute from the digits. The
//     rule states none of them.
//
// Length is counted in RUNES, not bytes: each Cyrillic letter is two bytes in
// UTF-8, so a byte length of 10 would accept five Cyrillic letters. The first
// two runes are accepted only as the exact uppercase Mongolian Cyrillic letters
// А-Я, Ё, Ө, Ү. There is no normalisation: a lowercase letter, a Latin
// look-alike such as A/P/O, or surrounding whitespace is refused, because
// silently accepting a mistyped ID hides a data-quality defect at the only place
// it can be caught.
//
// This is a Gerege rule, not a port. Fineract has no Mongolian national-ID rule
// and no reference-oracle behaviour exists for it, so no parity vector may be
// written and none is. The rule is proved by unit tests derived from the stated
// structure alone.
//
// ValidateNationalID is pure: it reads no I/O, consults no clock, and allocates
// only the message of the error it returns.
func ValidateNationalID(s string) error {
	r := []rune(s)
	if len(r) != nationalIDRunes {
		return &NationalIDError{
			Rule:   NationalIDRuleLength,
			Detail: fmt.Sprintf("got %d runes, want %d", len(r), nationalIDRunes),
		}
	}
	for i := 0; i < 2; i++ {
		if !isMongolianCyrillicUpper(r[i]) {
			return &NationalIDError{
				Rule: NationalIDRuleLetter,
				Detail: fmt.Sprintf(
					"letter position %d holds %q, not an uppercase Mongolian Cyrillic letter", i+1, r[i]),
			}
		}
	}
	var digits [8]int
	for i := range digits {
		c := r[2+i]
		if c < '0' || c > '9' {
			return &NationalIDError{
				Rule: NationalIDRuleDigit,
				Detail: fmt.Sprintf(
					"digit position %d holds %q, not an ASCII digit", i+1, c),
			}
		}
		digits[i] = int(c - '0')
	}
	mm := digits[2]*10 + digits[3]
	year, month, ok := nationalIDYearMonth(digits[0]*10+digits[1], mm)
	if !ok {
		return &NationalIDError{
			Rule:   NationalIDRuleMonth,
			Detail: fmt.Sprintf("month field %02d is outside 01-12 and 21-32", mm),
		}
	}
	day := digits[4]*10 + digits[5]
	if day < 1 || day > daysInGregorianMonth(year, month) {
		return &NationalIDError{
			Rule:   NationalIDRuleDay,
			Detail: fmt.Sprintf("day %02d is not a real day of %04d-%02d", day, year, month),
		}
	}
	return nil
}

// isMongolianCyrillicUpper reports whether r is an uppercase letter of the
// Mongolian Cyrillic alphabet: А (U+0410) through Я (U+042F), plus Ё (U+0401),
// Ө (U+04E8) and Ү (U+04AE), the three letters the contiguous block omits.
func isMongolianCyrillicUpper(r rune) bool {
	return (r >= '\u0410' && r <= '\u042F') ||
		r == '\u0401' || r == '\u04E8' || r == '\u04AE'
}

// nationalIDYearMonth decodes the two-digit year and the month field under the
// "+20" rule: MM 01-12 is year 19YY; MM 21-32 is year 20YY with calendar month
// MM-20. Any other MM is refused.
func nationalIDYearMonth(yy, mm int) (year, month int, ok bool) {
	switch {
	case mm >= 1 && mm <= 12:
		return 1900 + yy, mm, true
	case mm >= 21 && mm <= 32:
		return 2000 + yy, mm - 20, true
	default:
		return 0, 0, false
	}
}

// daysInGregorianMonth returns the number of days in month (1-12) of a Gregorian
// year. February has 29 days only on a leap year.
func daysInGregorianMonth(year, month int) int {
	switch month {
	case 1, 3, 5, 7, 8, 10, 12:
		return 31
	case 4, 6, 9, 11:
		return 30
	case 2:
		if isGregorianLeapYear(year) {
			return 29
		}
		return 28
	default:
		return 0
	}
}

// isGregorianLeapYear reports the Gregorian leap-year rule: divisible by 4,
// except centuries, but including every 400th year.
func isGregorianLeapYear(year int) bool {
	return year%4 == 0 && (year%100 != 0 || year%400 == 0)
}
