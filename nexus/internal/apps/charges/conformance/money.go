package conformance

import (
	"github.com/gerege/nexus/internal/apps/charges"
	shared "github.com/gerege/nexus/internal/conformance"
)

// parseMinorText parses a vector's monetary text field into integer minor units.
//
// A monetary value in a charges vector is an INTEGER STRING of minor units, never
// a decimal. This function is the typed half of the discipline that
// RejectFloatTokens enforces on the raw document: the raw pass rejects any
// non-integer JSON number anywhere in the file, and this pass rejects any
// monetary string that is not a plain decimal integer, so a float cannot reach
// the money path through either the JSON number or the JSON string route.
//
// The parse itself lives in nexus/internal/conformance; this wrapper only
// adapts the shared int64 result to the charges MinorUnits type.
func parseMinorText(text string) (charges.MinorUnits, error) {
	n, err := shared.ParseMinorInt(text)
	if err != nil {
		return 0, err
	}
	return charges.MinorUnits(n), nil
}
