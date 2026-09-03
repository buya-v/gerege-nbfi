package conformance

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/gerege/nexus/internal/apps/charges"
)

// parseMinorText parses a vector's monetary text field into integer minor units.
//
// A monetary value in a charges vector is an INTEGER STRING of minor units, never
// a decimal. This function is the typed half of the discipline that
// RejectFloatTokens enforces on the raw document: the raw pass rejects any
// non-integer JSON number anywhere in the file, and this pass rejects any
// monetary string that is not a plain decimal integer, so a float cannot reach
// the money path through either the JSON number or the JSON string route.
func parseMinorText(text string) (charges.MinorUnits, error) {
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
	return charges.MinorUnits(n), nil
}
