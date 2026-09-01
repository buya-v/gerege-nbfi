package shares

import (
	"fmt"
	"strconv"
	"strings"
)

// MinorUnits is a monetary quantity expressed as an integer count of the
// currency's minor unit (MNT minor unit = 2), the same convention used by the
// ledger, charges, loan, savings, investor and branch packages.
type MinorUnits int64

// MNTMinorDigits is MNT's minor unit: ISO 4217 numeric 496, 2 decimal digits.
const MNTMinorDigits = 2

// FormatDecimal renders an integer minor-unit count into major-unit decimal
// text with exactly minorDigits fraction digits.
func (m MinorUnits) FormatDecimal(minorDigits int) string {
	neg := m < 0
	v := int64(m)
	if neg {
		v = -v
	}
	scale := int64(1)
	for i := 0; i < minorDigits; i++ {
		scale *= 10
	}
	s := strconv.FormatInt(v/scale, 10)
	if minorDigits > 0 {
		frac := strconv.FormatInt(v%scale, 10)
		for len(frac) < minorDigits {
			frac = "0" + frac
		}
		s = s + "." + frac
	}
	if neg {
		s = "-" + s
	}
	return s
}

// MinorUnitsFromDecimalText converts exact major-unit decimal text into an
// integer minor-unit count. Any non-zero digit beyond minorDigits is refused.
func MinorUnitsFromDecimalText(text string, minorDigits int) (MinorUnits, error) {
	if minorDigits < 0 {
		return 0, fmt.Errorf("shares: minorDigits must not be negative, got %d", minorDigits)
	}
	s := strings.TrimSpace(text)
	if s == "" {
		return 0, fmt.Errorf("shares: empty monetary text")
	}
	neg := false
	switch s[0] {
	case '-':
		neg, s = true, s[1:]
	case '+':
		return 0, fmt.Errorf("shares: monetary text %q: leading '+' is not a canonical spelling", text)
	}
	intPart, fracPart, hasDot := strings.Cut(s, ".")
	if intPart == "" {
		return 0, fmt.Errorf("shares: monetary text %q: no integer digits before the decimal point", text)
	}
	if hasDot && fracPart == "" {
		return 0, fmt.Errorf("shares: monetary text %q: decimal point with no fraction digits", text)
	}
	for _, part := range []string{intPart, fracPart} {
		for i := 0; i < len(part); i++ {
			if part[i] < '0' || part[i] > '9' {
				return 0, fmt.Errorf("shares: monetary text %q: not a base-10 decimal", text)
			}
		}
	}
	keep, rest := fracPart, ""
	if len(fracPart) > minorDigits {
		keep, rest = fracPart[:minorDigits], fracPart[minorDigits:]
	}
	for i := 0; i < len(rest); i++ {
		if rest[i] != '0' {
			return 0, fmt.Errorf(
				"shares: monetary text %q carries sub-minor-unit residue at scale %d (digit %q beyond %d decimal places)",
				text, minorDigits, string(rest[i]), minorDigits)
		}
	}
	for len(keep) < minorDigits {
		keep += "0"
	}
	digits := intPart + keep
	var acc int64
	for i := 0; i < len(digits); i++ {
		d := int64(digits[i] - '0')
		next := acc*10 + d
		if next/10 != acc {
			return 0, fmt.Errorf("shares: monetary text %q overflows int64 minor units", text)
		}
		acc = next
	}
	if neg {
		acc = -acc
	}
	return MinorUnits(acc), nil
}
