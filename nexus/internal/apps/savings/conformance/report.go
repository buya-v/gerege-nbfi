package conformance

import (
	"io"

	shared "github.com/gerege/nexus/internal/conformance"
)

// WriteReport prints the run summary in a fixed order so two runs over the same
// store produce byte-identical reports. The rendering lives in
// nexus/internal/conformance; savings contributes its money-cell vocabulary,
// which Summary.ReportMoneyCells turns on in Run.
func WriteReport(w io.Writer, s *Summary) {
	shared.WriteReport(w, s)
}
