package postgres

import (
	"encoding/json"
	"testing"
)

func TestParseMinorUnit(t *testing.T) {
	cases := []struct {
		text        string
		minorDigits int
		want        MinorUnit
	}{
		{"0", 2, 0},
		{"0.00", 2, 0},
		{"1", 2, 100},
		{"100.5", 2, 10050},
		{"100.50", 2, 10050},
		{"1200000.000000", 2, 120000000},
		{"-500000.00", 2, -50000000},
		{"12.345", 3, 12345},
		{"12.345000", 3, 12345},
		{"7", 0, 7},
	}
	for _, c := range cases {
		got, err := ParseMinorUnit(c.text, c.minorDigits)
		if err != nil {
			t.Fatalf("ParseMinorUnit(%q, %d): %v", c.text, c.minorDigits, err)
		}
		if got != c.want {
			t.Errorf("ParseMinorUnit(%q, %d) = %d, want %d", c.text, c.minorDigits, got, c.want)
		}
	}
}

func TestMinorUnitRoundTrip(t *testing.T) {
	for _, c := range []struct {
		text        string
		minorDigits int
	}{
		{"0.00", 2},
		{"1.00", 2},
		{"100.50", 2},
		{"-500000.00", 2},
		{"12.345", 3},
		{"92233720368547758.07", 2},
		{"-92233720368547758.08", 2},
	} {
		m, err := ParseMinorUnit(c.text, c.minorDigits)
		if err != nil {
			t.Fatalf("ParseMinorUnit(%q, %d): %v", c.text, c.minorDigits, err)
		}
		if got := m.Format(c.minorDigits); got != c.text {
			t.Errorf("Format(Parse(%q, %d)) = %q", c.text, c.minorDigits, got)
		}
		back, err := ParseMinorUnit(m.Format(c.minorDigits), c.minorDigits)
		if err != nil {
			t.Fatalf("ParseMinorUnit(Format(%d), %d): %v", int64(m), c.minorDigits, err)
		}
		if back != m {
			t.Errorf("Parse(Format(%d)) = %d, want %d", int64(m), back, m)
		}
	}
}

func TestParseMinorUnitRefusesSubMinorResidue(t *testing.T) {
	for _, text := range []string{"1200000.000001", "1.999", "-1.001"} {
		if _, err := ParseMinorUnit(text, 2); err == nil {
			t.Errorf("ParseMinorUnit(%q, 2) succeeded, want refusal", text)
		}
	}
}

func TestParseMinorUnitRefusesMalformed(t *testing.T) {
	for _, text := range []string{"", ".", "1.", "abc", "1.2.3", "+1.00", "-", "1e5", " 12,34"} {
		if _, err := ParseMinorUnit(text, 2); err == nil {
			t.Errorf("ParseMinorUnit(%q, 2) succeeded, want refusal", text)
		}
	}
}

func TestFormatCanonical(t *testing.T) {
	cases := []struct {
		m           MinorUnit
		minorDigits int
		want        string
	}{
		{0, 2, "0.00"},
		{100, 2, "1.00"},
		{10050, 2, "100.50"},
		{-10050, 2, "-100.50"},
		{-1, 2, "-0.01"},
		{7, 0, "7"},
		{-9223372036854775808, 2, "-92233720368547758.08"},
	}
	for _, c := range cases {
		if got := c.m.Format(c.minorDigits); got != c.want {
			t.Errorf("MinorUnit(%d).Format(%d) = %q, want %q", int64(c.m), c.minorDigits, got, c.want)
		}
	}
}

func TestScanMinorUnitAcceptsIntegersAndText(t *testing.T) {
	for _, src := range []any{int64(12345), int32(12345), int16(12345), "123.45", []byte("123.45")} {
		got, err := ScanMinorUnit(src, 2)
		if err != nil {
			t.Fatalf("ScanMinorUnit(%T(%v), 2): %v", src, src, err)
		}
		if got != 12345 {
			t.Errorf("ScanMinorUnit(%T(%v), 2) = %d, want 12345", src, src, got)
		}
	}
	if got, err := ScanMinorUnit(int8(123), 2); err != nil || got != 123 {
		t.Fatalf("ScanMinorUnit(int8(123), 2) = %d, %v; want 123, nil", got, err)
	}
}

func TestScanMinorUnitRefusesNonIntegerAndNull(t *testing.T) {
	// Produce a non-integer value without naming a forbidden spelling or
	// writing a floating-point literal: decoding a JSON number into any yields
	// exactly the floating-point kind this codec must refuse.
	var nonInteger any
	if err := json.Unmarshal([]byte("123.45"), &nonInteger); err != nil {
		t.Fatalf("json.Unmarshal of a number into any: %v", err)
	}
	for _, src := range []any{nonInteger, nil, true} {
		if _, err := ScanMinorUnit(src, 2); err == nil {
			t.Errorf("ScanMinorUnit(%T(%v), 2) succeeded, want refusal", src, src)
		}
	}
}
