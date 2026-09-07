package conformance

import (
	"io"

	shared "github.com/gerege/nexus/internal/conformance"
)

// WriteReport prints the run summary in a fixed order so two runs over the same
// store produce byte-identical reports. The report writer lives in
// nexus/internal/conformance.
func WriteReport(w io.Writer, s *Summary) { shared.WriteReport(w, s) }
