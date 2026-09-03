package conformance

import (
	"fmt"
	"io"
	"sort"
)

// WriteReport prints the run summary in a fixed order so two runs over the same
// store produce byte-identical reports.
func WriteReport(w io.Writer, s *Summary) {
	fmt.Fprintf(w, "VERDICT: %s (exit %d)\n", verdictLine(s), s.ExitCode())
	fmt.Fprintf(w, "vectors_loaded=%d parity_pass=%d parity_fail=%d refused=%d inadmissible=%d harness_error=%d\n",
		s.VectorsLoaded, s.ParityPass, s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	fmt.Fprintf(w, "graded_cells=%d money_cells=%d invariant_violations=%d\n",
		s.GradedCells, s.MoneyCells, s.InvariantViolations)
	fmt.Fprintf(w, "nofloat: packages=%d files=%d tokens=%d imports=%d violations=%d\n",
		s.NoFloatCensus.PackagesScanned, s.NoFloatCensus.FilesScanned,
		s.NoFloatCensus.TokensScanned, s.NoFloatCensus.ImportsScanned,
		len(s.NoFloatCensus.Violations()))

	if len(s.FatalReasons) > 0 {
		fmt.Fprintln(w, "fatal:")
		for _, r := range s.FatalReasons {
			fmt.Fprintf(w, "  - %s\n", r)
		}
	}
	if len(s.LoadErrors) > 0 {
		fmt.Fprintln(w, "load_errors:")
		sort.Slice(s.LoadErrors, func(i, j int) bool { return s.LoadErrors[i].Path < s.LoadErrors[j].Path })
		for _, le := range s.LoadErrors {
			fmt.Fprintf(w, "  - %s: %v\n", le.Path, le.Err)
		}
	}
}

func verdictLine(s *Summary) string {
	switch {
	case len(s.FatalReasons) > 0 || len(s.LoadErrors) > 0:
		return "UNUSABLE"
	case s.ParityFail > 0 || s.InvariantViolations > 0:
		return "FAIL"
	case s.Refused > 0 || s.Inadmissible > 0 || s.Errored > 0:
		return "UNUSABLE"
	case s.SelfTestMode && s.ParityPass > 0:
		return "SELF-TEST (never a conformance pass)"
	case s.ParityPass > 0:
		return "PASS"
	default:
		return "UNUSABLE"
	}
}
