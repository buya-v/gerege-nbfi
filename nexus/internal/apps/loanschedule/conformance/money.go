package conformance

import (
	"fmt"
	"strconv"
	"strings"
)

// MinorText is a monetary quantity: a base-10 integer count of the currency's
// minor unit, carried in a vector file as a JSON STRING and never as a JSON
// number.
//
// Why a string. The vector store's hardest rule is that no monetary value may
// ever be represented by, or pass through, a floating-point type. A JSON number
// is the one place that rule cannot be enforced by inspection alone: most JSON
// readers (jq among them) decode every number into an IEEE-754 double, so a
// perfectly integral JSON number can be corrupted by the reader rather than by
// the file. Making every monetary field a string removes the question — there
// is no monetary JSON number to decode — and it lets the harness's float guard
// state a rule with no exceptions: NO JSON number anywhere in a vector file may
// contain '.', 'e' or 'E'.
//
// Non-monetary counts (number_of_repayments, repayment_every, a date's
// year/month/day, a Rate's numerator and denominator) remain JSON integers.
// They are dimensionless and small, and they are not money.
type MinorText string

// Int64 parses m as a canonical base-10 integer.
//
// Canonical means: an optional leading '-', then either "0" or a digit string
// with no leading zero. "007", "+7", "1_000", "1e3", "1.0" and "" are all
// errors. A vector is machine-written, so there is no reason to be liberal, and
// two spellings of one amount would let two structurally-equal vectors compare
// unequal.
func (m MinorText) Int64() (int64, error) {
	s := string(m)
	if s == "" {
		return 0, fmt.Errorf("empty monetary value: want a base-10 integer string of minor units")
	}
	body := s
	if strings.HasPrefix(body, "-") {
		body = body[1:]
	}
	if body == "" {
		return 0, fmt.Errorf("monetary value %q: sign with no digits", s)
	}
	for i := 0; i < len(body); i++ {
		if body[i] < '0' || body[i] > '9' {
			return 0, fmt.Errorf("monetary value %q: not a base-10 integer string of minor units", s)
		}
	}
	if len(body) > 1 && body[0] == '0' {
		return 0, fmt.Errorf("monetary value %q: non-canonical leading zero", s)
	}
	v, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("monetary value %q: %w", s, err)
	}
	return v, nil
}

// MinorFromMajorText converts the reference oracle's exact wire text for a
// monetary amount in MAJOR units into an integer count of minor units, using
// only integer and string arithmetic. No floating-point type is constructed at
// any point, in either direction.
//
// This exists so that a promoted vector's integer minor-unit value can be
// mechanically re-checked against the oracle's own emitted characters. The
// oracle emits money as a decimal in major units ("112082.37"); the promotion
// step converts it; and a transcription slip in that step is invisible to every
// other check the harness performs, because the promoted number is internally
// consistent with itself. Carrying the wire text alongside the integer and
// re-deriving one from the other closes that hole.
//
// The conversion is EXACT or it is an error. A wire text carrying a NON-ZERO
// fraction digit beyond the currency's minor-unit digits is rejected rather than
// rounded: rounding here would silently invent a value the oracle never emitted,
// and deciding how to round is the calculation's job, not the transcription's.
// Fewer fraction digits than the currency's scale are padded with zeros, because
// "100.5" and "100.50" are the same amount; TRAILING ZEROS beyond the scale are
// accepted for the same reason, because the observed corpus is not uniform in
// scale — Path A emits "0" for one hard-coded total while every sibling is scale
// 2, and Path B persists product rows at scale 6 ("1200000.000000"). A scale
// difference is a finding to record, never a reason to reject an exact value.
func MinorFromMajorText(text string, minorUnitDigits int32) (int64, error) {
	if minorUnitDigits < 0 || minorUnitDigits > 18 {
		return 0, fmt.Errorf("minor unit digits %d out of range", minorUnitDigits)
	}
	s := strings.TrimSpace(text)
	if s == "" {
		return 0, fmt.Errorf("empty major-unit wire text")
	}
	neg := false
	if strings.HasPrefix(s, "-") {
		neg = true
		s = s[1:]
	}
	intPart, fracPart := s, ""
	if i := strings.IndexByte(s, '.'); i >= 0 {
		intPart, fracPart = s[:i], s[i+1:]
	}
	if intPart == "" {
		return 0, fmt.Errorf("major-unit wire text %q: no integer part (write 0.50, never .50)", text)
	}
	if err := allDigits(intPart); err != nil {
		return 0, fmt.Errorf("major-unit wire text %q: %w", text, err)
	}
	if fracPart != "" {
		if err := allDigits(fracPart); err != nil {
			return 0, fmt.Errorf("major-unit wire text %q: %w", text, err)
		}
	}
	if int32(len(fracPart)) > minorUnitDigits {
		excess := fracPart[minorUnitDigits:]
		if strings.Trim(excess, "0") != "" {
			return 0, fmt.Errorf(
				"major-unit wire text %q carries significant digits (%q) beyond the currency's %d minor-unit "+
					"digits: an exact conversion is impossible and this harness will not round a transcription",
				text, excess, minorUnitDigits)
		}
		fracPart = fracPart[:minorUnitDigits]
	}
	digits := intPart + fracPart + strings.Repeat("0", int(minorUnitDigits)-len(fracPart))
	// Strip leading zeros so ParseInt sees a canonical string; keep one digit.
	trimmed := strings.TrimLeft(digits, "0")
	if trimmed == "" {
		trimmed = "0"
	}
	if neg {
		trimmed = "-" + trimmed
	}
	v, err := strconv.ParseInt(trimmed, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("major-unit wire text %q: %w", text, err)
	}
	return v, nil
}

func allDigits(s string) error {
	for i := 0; i < len(s); i++ {
		if s[i] < '0' || s[i] > '9' {
			return fmt.Errorf("character %q is not a decimal digit", s[i])
		}
	}
	return nil
}

// FormatMinor renders an integer minor-unit amount for a report line, in minor
// units, with no thousands separator and no decimal point. It is a display
// helper for the PASS/FAIL table only; nothing compares its output.
func FormatMinor(v int64) string { return strconv.FormatInt(v, 10) }
