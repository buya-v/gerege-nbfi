package conformance

import (
	"io"

	shared "github.com/gerege/nexus/internal/conformance"
)

// WriteReport prints the run summary in a fixed order so two runs over the same
// store produce byte-identical reports. The report writer lives in
// nexus/internal/conformance; workingcapital has no minor-unit money cell on its
// graded seam (id/external_id/status only), so the money column stays off.
func WriteReport(w io.Writer, s *Summary) { shared.WriteReport(w, s) }
