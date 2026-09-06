package conformance

import (
	"io"

	shared "github.com/gerege/nexus/internal/conformance"
)

// WriteReport prints the run summary in a fixed order so two runs over the same
// store produce byte-identical reports. The rendering (the report line, the
// verdict mapping and the exit-code mapping) is shared across contexts; charges
// contributes only its money-cell vocabulary, which Summary.ReportMoneyCells
// turns on in Run.
func WriteReport(w io.Writer, s *Summary) {
	shared.WriteReport(w, s)
}
