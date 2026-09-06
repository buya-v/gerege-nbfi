package conformance

import (
	"fmt"
	"io"
	"sort"
)

// LoadError is a vector file that could not be read or decoded. It is never a
// skip: every LoadError makes the run unusable.
type LoadError struct {
	Path string
	Err  error
}

// Summary is the aggregate outcome of a run. Every count is explicit so that a
// zero is visible rather than assumed.
type Summary struct {
	SelfTestMode        bool
	ParityPass          int
	ParityFail          int
	Refused             int
	Inadmissible        int
	Errored             int
	InvariantViolations int
	GradedCells         int
	MoneyCells          int
	VectorsLoaded       int
	FatalReasons        []string
	LoadErrors          []LoadError
	NoFloatCensus       FloatingPointCensus

	// ReportMoneyCells controls whether the graded-cells report line also names
	// the money-cell count. Contexts that grade money cells set it; contexts
	// whose cell vocabulary has no money column leave it false and keep the
	// shorter line.
	ReportMoneyCells bool
}

// ExitCode maps the run to a process exit code.
//
//	0  every graded vector passed and at least one PARITY vector was graded
//	1  a mismatch or an invariant violation (an actionable finding)
//	2  the harness or corpus is unusable — including ZERO vectors graded
func (s *Summary) ExitCode() int {
	if s.ParityFail > 0 || s.InvariantViolations > 0 {
		return 1
	}
	if len(s.FatalReasons) > 0 || len(s.LoadErrors) > 0 ||
		s.Refused > 0 || s.Inadmissible > 0 || s.Errored > 0 {
		return 2
	}
	if !s.SelfTestMode && s.ParityPass == 0 {
		// A run that graded no PARITY vector cannot support a parity claim.
		return 2
	}
	return 0
}

// VerdictLine renders the one-word verdict for the summary.
func VerdictLine(s *Summary) string {
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

// WriteReport prints the run summary in a fixed order so two runs over the same
// store produce byte-identical reports.
func WriteReport(w io.Writer, s *Summary) {
	fmt.Fprintf(w, "VERDICT: %s (exit %d)\n", VerdictLine(s), s.ExitCode())
	fmt.Fprintf(w, "vectors_loaded=%d parity_pass=%d parity_fail=%d refused=%d inadmissible=%d harness_error=%d\n",
		s.VectorsLoaded, s.ParityPass, s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	if s.ReportMoneyCells {
		fmt.Fprintf(w, "graded_cells=%d money_cells=%d invariant_violations=%d\n",
			s.GradedCells, s.MoneyCells, s.InvariantViolations)
	} else {
		fmt.Fprintf(w, "graded_cells=%d invariant_violations=%d\n",
			s.GradedCells, s.InvariantViolations)
	}
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
