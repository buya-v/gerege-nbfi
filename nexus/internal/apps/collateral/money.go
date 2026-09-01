package collateral

import (
	"fmt"
	"strconv"
	"strings"
)

// ScaledInt is an exact fixed-point quantity expressed as an integer count of
// 10^-scale major units. The scale is NOT stored on the type; callers carry it
// at the encode/decode boundary. Collateral management columns use scale 5
// (DecimalScale) and the classic loan-collateral value uses scale 6
// (CollateralValueScale). This mirrors the existing app-package money codecs:
// no floating-point type appears on any decimal path.
type ScaledInt int64

// DecimalScale is the fixed scale of the management-side collateral columns:
// base_price DECIMAL(19,5), pct_to_base DECIMAL(20,5), quantity DECIMAL(20,5).
const DecimalScale = 5

// CollateralValueScale is the scale of m_loan_collateral.value DECIMAL(19,6).
const CollateralValueScale = 6

// FormatDecimal renders the scaled count back into major-unit decimal text with
// exactly scale fraction digits, so a value in and a value out round-trip.
func (d ScaledInt) FormatDecimal(scale int) string {
	neg := d < 0
	v := int64(d)
	if neg {
		v = -v
	}
	mul := int64(1)
	for i := 0; i < scale; i++ {
		mul *= 10
	}
	s := strconv.FormatInt(v/mul, 10)
	if scale > 0 {
		frac := strconv.FormatInt(v%mul, 10)
		for len(frac) < scale {
			frac = "0" + frac
		}
		s = s + "." + frac
	}
	if neg {
		s = "-" + s
	}
	return s
}

// ScaledIntFromText converts exact major-unit decimal text into a scaled integer
// count. It is EXACT or it is an error: fewer fraction digits than scale are
// zero-padded, trailing zeros beyond scale are dropped, and any NON-ZERO digit
// beyond scale is refused (there is no truncation rule).
func ScaledIntFromText(text string, scale int) (ScaledInt, error) {
	if scale < 0 {
		return 0, fmt.Errorf("collateral: scale must not be negative, got %d", scale)
	}
	s := strings.TrimSpace(text)
	if s == "" {
		return 0, fmt.Errorf("collateral: empty decimal text")
	}
	neg := false
	switch s[0] {
	case '-':
		neg, s = true, s[1:]
	case '+':
		return 0, fmt.Errorf("collateral: decimal text %q: leading '+' is not a canonical spelling", text)
	}
	intPart, fracPart, hasDot := strings.Cut(s, ".")
	if intPart == "" {
		return 0, fmt.Errorf("collateral: decimal text %q: no integer digits before the decimal point", text)
	}
	if hasDot && fracPart == "" {
		return 0, fmt.Errorf("collateral: decimal text %q: decimal point with no fraction digits", text)
	}
	for _, part := range []string{intPart, fracPart} {
		for i := 0; i < len(part); i++ {
			if part[i] < '0' || part[i] > '9' {
				return 0, fmt.Errorf("collateral: decimal text %q: not a base-10 decimal", text)
			}
		}
	}

	keep, rest := fracPart, ""
	if len(fracPart) > scale {
		keep, rest = fracPart[:scale], fracPart[scale:]
	}
	for i := 0; i < len(rest); i++ {
		if rest[i] != '0' {
			return 0, fmt.Errorf(
				"collateral: decimal text %q carries residue at scale %d (digit %q beyond %d decimal places)",
				text, scale, string(rest[i]), scale)
		}
	}
	for len(keep) < scale {
		keep += "0"
	}

	digits := intPart + keep
	var acc int64
	for i := 0; i < len(digits); i++ {
		d := int64(digits[i] - '0')
		next := acc*10 + d
		if next/10 != acc {
			return 0, fmt.Errorf("collateral: decimal text %q overflows int64", text)
		}
		acc = next
	}
	if neg {
		acc = -acc
	}
	return ScaledInt(acc), nil
}
