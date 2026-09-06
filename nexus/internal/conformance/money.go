package conformance

import (
	"fmt"
	"strconv"
	"strings"
)

// ParseMinorInt parses a monetary text field as a base-10 integer count of
// minor units. The value may be signed, but it must be a plain integer: no
// fraction, no exponent, no thousands separator. No floating-point type is
// constructed at any point.
func ParseMinorInt(text string) (int64, error) {
	s := strings.TrimSpace(text)
	if s == "" {
		return 0, fmt.Errorf("empty minor-unit amount")
	}
	i := 0
	if s[0] == '-' || s[0] == '+' {
		i = 1
	}
	if i == len(s) {
		return 0, fmt.Errorf("minor-unit amount %q is not an integer count of minor units", text)
	}
	for ; i < len(s); i++ {
		if s[i] < '0' || s[i] > '9' {
			return 0, fmt.Errorf("minor-unit amount %q is not an integer count of minor units", text)
		}
	}
	n, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("minor-unit amount %q: %w", text, err)
	}
	return n, nil
}
