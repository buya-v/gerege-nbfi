package postgres

import (
	"fmt"
	"strconv"
	"strings"
)

// MinorUnit is a monetary quantity expressed as an integer count of a
// currency's minor unit. It is the only money type this package will ever
// emit: PostgreSQL's numeric(19,6) columns are read as exact decimal TEXT and
// converted here, and bigint minor-unit columns are read directly. No
// float4/float8/numeric-to-float conversion exists on any money path.
//
// The adopted Fineract schema stores ledger amounts as numeric(19,6), not as a
// bigint minor-unit column; the bigint-column case this codec also covers is
// the shadow-parity representation the port writes into its own side tables,
// and it is exercised by the unit tests here regardless of which DDL the
// current phase reads.
type MinorUnit int64

// ParseMinorUnit converts exact decimal TEXT for a major-unit amount into an
// integer minor-unit count. It is exact or it is an error:
//
//   - fewer fraction digits than minorDigits are zero-padded ("100.5" == "100.50");
//   - trailing zeros beyond minorDigits are dropped ("1200000.000000" == 120000000);
//   - any NON-ZERO digit beyond minorDigits is refused: there is no truncation
//     rule, so the codec refuses rather than inventing an amount.
func ParseMinorUnit(text string, minorDigits int) (MinorUnit, error) {
	if minorDigits < 0 {
		return 0, fmt.Errorf("postgres: minorDigits must not be negative, got %d", minorDigits)
	}
	s := strings.TrimSpace(text)
	if s == "" {
		return 0, fmt.Errorf("postgres: empty monetary text")
	}

	neg := false
	switch s[0] {
	case '-':
		neg, s = true, s[1:]
	case '+':
		return 0, fmt.Errorf("postgres: monetary text %q: leading '+' is not a canonical spelling", text)
	}

	intPart, fracPart, hasDot := strings.Cut(s, ".")
	if intPart == "" {
		return 0, fmt.Errorf("postgres: monetary text %q: no integer digits before the decimal point", text)
	}
	if hasDot && fracPart == "" {
		return 0, fmt.Errorf("postgres: monetary text %q: decimal point with no fraction digits", text)
	}
	for _, part := range []string{intPart, fracPart} {
		for i := 0; i < len(part); i++ {
			if part[i] < '0' || part[i] > '9' {
				return 0, fmt.Errorf("postgres: monetary text %q: not a base-10 decimal", text)
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
				"postgres: monetary text %q carries sub-minor-unit residue at scale %d (digit %q beyond %d decimal places)",
				text, minorDigits, string(rest[i]), minorDigits)
		}
	}
	for len(keep) < minorDigits {
		keep += "0"
	}

	digits := intPart + keep
	var acc uint64
	for i := 0; i < len(digits); i++ {
		d := uint64(digits[i] - '0')
		next := acc*10 + d
		if next/10 != acc {
			return 0, fmt.Errorf("postgres: monetary text %q overflows int64 minor units", text)
		}
		acc = next
	}

	const maxInt64 = uint64(1<<63 - 1)
	const minInt64Magnitude = uint64(1 << 63)
	if neg {
		// The magnitude of MinInt64 is 2^63, one more than MaxInt64; it is the
		// only negative value whose magnitude does not fit MaxInt64.
		if acc == minInt64Magnitude {
			return MinorUnit(-1 << 63), nil
		}
		if acc > maxInt64 {
			return 0, fmt.Errorf("postgres: monetary text %q overflows int64 minor units", text)
		}
		return MinorUnit(-int64(acc)), nil
	}
	if acc > maxInt64 {
		return 0, fmt.Errorf("postgres: monetary text %q overflows int64 minor units", text)
	}
	return MinorUnit(int64(acc)), nil
}

// Format renders the minor-unit count as a major-unit decimal string with
// exactly minorDigits fraction digits. minorDigits < 0 is a programming error
// and renders the bare integer count.
func (m MinorUnit) Format(minorDigits int) string {
	if minorDigits <= 0 {
		return strconv.FormatInt(int64(m), 10)
	}
	neg := m < 0
	mag := uint64(m)
	if neg {
		mag = uint64(-(m + 1)) + 1 // avoid overflow on MinInt64
	}
	div := uint64(1)
	for i := 0; i < minorDigits; i++ {
		div *= 10
	}
	whole := mag / div
	frac := mag % div
	fracStr := strconv.FormatUint(frac, 10)
	for len(fracStr) < minorDigits {
		fracStr = "0" + fracStr
	}
	out := strconv.FormatUint(whole, 10) + "." + fracStr
	if neg {
		out = "-" + out
	}
	return out
}

// ScanMinorUnit decodes a database driver value into MinorUnit without ever
// routing the value through a floating-point type. It accepts the integer
// kinds pgx yields for bigint/smallint/integer columns and the exact decimal
// TEXT pgx yields for numeric columns, and refuses every other source —
// including the floating-point kinds — through the default arm, so the
// forbidden spellings never need to appear in code.
func ScanMinorUnit(src any, minorDigits int) (MinorUnit, error) {
	switch v := src.(type) {
	case nil:
		return 0, fmt.Errorf("postgres: cannot scan NULL into a monetary amount")
	case int64:
		return MinorUnit(v), nil
	case int32:
		return MinorUnit(v), nil
	case int16:
		return MinorUnit(v), nil
	case int8:
		return MinorUnit(v), nil
	case uint64:
		if v > uint64(^uint64(0)>>1) {
			return 0, fmt.Errorf("postgres: monetary value %d overflows int64", v)
		}
		return MinorUnit(int64(v)), nil
	case int:
		return MinorUnit(v), nil
	case string:
		return ParseMinorUnit(v, minorDigits)
	case []byte:
		return ParseMinorUnit(string(v), minorDigits)
	default:
		return 0, fmt.Errorf("postgres: unsupported money scan source %T (want integer or exact decimal text)", src)
	}
}
