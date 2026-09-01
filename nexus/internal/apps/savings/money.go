package savings

import (
	"fmt"
	"strconv"
	"strings"
)

// MinorUnits is a monetary quantity expressed as an integer count of the
// currency's minor unit (MNT minor unit = 2). It is the same convention the
// ledger, charges, loan and provisioning packages use, so an amount computed
// here can be handed to the A1 posting engine without a unit conversion. No
// floating-point type appears on any money path in this package.
type MinorUnits int64

// Percent is an interest rate stored exactly as Fineract stores it: a
// DECIMAL(19,6) value whose meaning is "whole per cent", so 12.500000 means
// 12.5 %. A Percent therefore carries six fraction digits: it is the
// percentage scaled by 10^6 (micro-per-cent). This is NOT a money amount.
//
// Examples (whole per cent -> Percent):
//
//	12.500000 % ->  12_500_000
//	 1.234500 % ->   1_234_500
//	 0.500000 % ->     500_000
type Percent int64

// MNTMinorDigits is MNT's minor unit: ISO 4217 numeric 496, 2 decimal digits.
const MNTMinorDigits = 2

// FormatDecimal renders an integer minor-unit count back into major-unit
// decimal text with exactly minorDigits fraction digits, so a value in and a
// value out round-trip byte-for-byte. It is the formatter a persistence layer
// uses to write a money column.
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

// MinorUnitsFromDecimalText converts the oracle's exact wire or column text for
// a monetary amount in MAJOR units into an integer count of minor units, using
// only integer and string arithmetic.
//
// It is EXACT or it is an error: fewer fraction digits than minorDigits are
// zero-padded; trailing zeros beyond minorDigits are dropped; and any NON-ZERO
// digit beyond minorDigits is REFUSED. No vector establishes a truncation rule
// for a residual sixth decimal, so this port applies none and refuses instead
// of silently inventing an amount (the same rule the ledger package states in
// its money.go trap-4 comment).
func MinorUnitsFromDecimalText(text string, minorDigits int) (MinorUnits, error) {
	if minorDigits < 0 {
		return 0, fmt.Errorf("savings: minorDigits must not be negative, got %d", minorDigits)
	}
	s := strings.TrimSpace(text)
	if s == "" {
		return 0, fmt.Errorf("savings: empty monetary text")
	}
	neg := false
	switch s[0] {
	case '-':
		neg, s = true, s[1:]
	case '+':
		return 0, fmt.Errorf("savings: monetary text %q: leading '+' is not a canonical spelling", text)
	}
	intPart, fracPart, hasDot := strings.Cut(s, ".")
	if intPart == "" {
		return 0, fmt.Errorf("savings: monetary text %q: no integer digits before the decimal point", text)
	}
	if hasDot && fracPart == "" {
		return 0, fmt.Errorf("savings: monetary text %q: decimal point with no fraction digits", text)
	}
	for _, part := range []string{intPart, fracPart} {
		for i := 0; i < len(part); i++ {
			if part[i] < '0' || part[i] > '9' {
				return 0, fmt.Errorf("savings: monetary text %q: not a base-10 decimal", text)
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
				"savings: monetary text %q carries sub-minor-unit residue at scale %d (digit %q beyond %d decimal places)",
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
			return 0, fmt.Errorf("savings: monetary text %q overflows int64 minor units", text)
		}
		acc = next
	}
	if neg {
		acc = -acc
	}
	return MinorUnits(acc), nil
}
