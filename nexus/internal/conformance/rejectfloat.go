package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"strings"
)

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
//
// It runs BEFORE any typed decoding, so a float in a field the typed shape
// ignores is still caught. The rule is shared by every harness; label names the
// document's context in the refusal so the reader knows which store is at fault.
func RejectFloatTokens(raw []byte, label string) error {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	for {
		tok, err := dec.Token()
		if err != nil {
			if err.Error() == "EOF" {
				return nil
			}
			return fmt.Errorf("scanning for float tokens: %w", err)
		}
		n, ok := tok.(json.Number)
		if !ok {
			continue
		}
		s := n.String()
		if strings.ContainsAny(s, ".eE") {
			return fmt.Errorf(
				"FLOAT TOKEN %q in %s vector JSON: every number in a vector file must be an integer, "+
					"and every monetary value must be an integer STRING in minor units", s, label)
		}
	}
}
