package conformance

import (
	"fmt"
	"io"
	"strings"
)

// WriteReport prints the per-vector table and the summary.
//
// Two rules govern the layout. First, REFUSED and INADMISSIBLE get their own
// columns and their own sections, because the interesting outcomes of this
// program are not PASS and FAIL. Second, the summary states what was NOT graded
// as prominently as what was — the self-test count, the ungraded cell count, the
// refusals — because a reader who sees only green numbers will believe them.
func WriteReport(w io.Writer, s *Summary) {
	p := func(format string, args ...any) { fmt.Fprintf(w, format+"\n", args...) }

	p("")
	if s.SelfTestMode {
		p("=== GOLDEN-VECTOR CONFORMANCE HARNESS — SELF-TEST MODE ===")
		p("    Grading the HARNESS, not an implementation. A green run here means the harness works.")
		p("    IT IS NOT A CONFORMANCE PASS AND MAKES NO CLAIM ABOUT ANY PORT.")
	} else {
		p("=== GOLDEN-VECTOR CONFORMANCE — Fineract reference oracle vs Go module ===")
	}
	p("    store           %s", s.StoreRoot)
	if s.ContextFilter != "" {
		p("    context filter  %s", s.ContextFilter)
	}
	p("    implementation  %s", s.ImplementationName)
	p("    oracle probe    %s", strings.ToUpper(s.OracleProbe))
	p("")

	if len(s.Results) > 0 {
		p("%-28s %-16s %-11s %-12s %6s %8s  %s",
			"CASE", "CLASS", "SEAM", "OUTCOME", "CELLS", "UNGRADED", "REASON")
		p("%s", strings.Repeat("-", 118))
		for _, r := range s.Results {
			seam := r.Seam
			if seam == "" {
				seam = "-"
			}
			reason := string(r.Reason)
			if reason == "" && len(r.Detail) > 0 && r.Outcome != OutcomePass {
				reason = firstLine(r.Detail[0])
			}
			if r.Class == ClassSelfTest {
				reason = "SELF-TEST FIXTURE — EXCLUDED FROM THE PARITY COUNT"
			}
			p("%-28s %-16s %-11s %-12s %6d %8d  %s",
				trunc(r.CaseID, 28), r.Class, trunc(seam, 11), r.Outcome,
				r.GradedCells, r.UngradedCells, trunc(reason, 44))
		}
		p("")
	}

	for _, r := range s.Results {
		if r.Outcome == OutcomePass && !anyViolation(r.Invariants) {
			continue
		}
		p("--- %s (%s, %s) : %s", r.CaseID, r.Class, r.Path, r.Outcome)
		if hint := FormatRefusalHint(r.Reason); hint != "" {
			p("    reason  %s", r.Reason)
			p("    retire  %s", hint)
		}
		for _, d := range r.Detail {
			p("    %s", d)
		}
		for _, iv := range r.Invariants {
			if iv.Status == InvariantViolated {
				p("    INVARIANT %s VIOLATED: %s", iv.Name, iv.Detail)
			}
		}
		p("")
	}

	if len(s.LoadErrors) > 0 {
		p("--- FILES THAT COULD NOT BE READ AS VECTORS (each one makes this run unusable) ---")
		for _, le := range s.LoadErrors {
			p("    %s: %v", le.Path, le.Err)
		}
		p("")
	}

	p("--- WHAT THIS RUN ACTUALLY GRADES (named wrong implementations killed) ---")
	p("    Gradeability is NOT \"two captures differing only in a setting differ in some cell\". That test is")
	p("    false in both directions: LB-DEC31 reports ZERO cells differing across the day-count setting and")
	p("    still kills a no-arm port by 6,015 minor units (finding T55-N1). An all-products-identical capture")
	p("    is therefore not evidence of non-gradeability.")
	p("    counterfactuals named by admissible vectors: %d  (%d money kills, %d structural kills)",
		s.CounterfactualsNamed, s.MoneyKills, s.StructuralKills)
	p("    The two are NEVER merged. A MONEY kill separates the oracle from a wrong implementation by a")
	p("    non-zero minor-unit margin. A STRUCTURAL kill separates it by a cell that carries no money at")
	p("    all — a due date, a period boundary, a row kind, the row order — and its margin is honestly 0.")
	p("    P-02's month-end re-anchor and P-03's row ordering are graded ONLY structurally: every money")
	p("    column is identical to the baseline and the port is still wrong. A store of nothing but")
	p("    structural kills grades no amount, and this line is how a reader can tell (finding D-4).")
	if len(s.CounterfactualCoverage) == 0 {
		p("    no graded capability is backed by a parity vector yet")
	} else {
		for capName, ids := range s.CounterfactualCoverage {
			p("    %-42s killed by %s", capName, strings.Join(ids, ", "))
		}
	}
	if len(s.UncoveredGradedCapabilities) > 0 {
		p("    UNBACKED in_graded_domain claims: %s", strings.Join(s.UncoveredGradedCapabilities, ", "))
	}
	p("")
	p("--- WHAT THIS RUN DOES NOT GRADE, EVEN THOUGH IT RECORDS IT ---")
	p("    The MathContext every parity vector records — (19, HALF_UP) — is PROVENANCE AND COMPARABILITY,")
	p("    not a graded claim. T55 witnessed no shape separating precision 19 from 12, or HALF_UP from")
	p("    HALF_EVEN (29 of 36 periods agree at all of them; precision 8 does separate, 22 of 36). Recording")
	p("    the setting stays mandatory; claiming a vector PROVES it would be false.")
	for _, rt := range RoundedTranscriptions() {
		p("    %s: %s at %d decimal places, parity status %s.",
			strings.ToUpper(rt.Quantity), PrecisionTranscribedRounded, rt.TranscribedScale, rt.ParityStatus)
		p("        %s", rt.Trap)
		p("        %s", rt.Citation)
	}
	p("    rate-factor observations carried by this run: %d — recorded, NEVER compared.", s.RateFactorsRecorded)
	p("    money cells whose wire text is over-scaled and declared as such: %d (T17-F5; an UNDECLARED one",
		s.OverScaledCells)
	p("        is inadmissible, because a rig that silently rounded it would grade the port against a")
	p("        number the oracle never produced).")
	p("")

	p("--- CROSS-CHECK SOURCES, AND THE COLUMNS THEY DO NOT COVER (T17-F2) ---")
	p("    A second attestation of the same output corroborates only the columns it actually prints. This")
	p("    harness refuses any vector claiming corroboration a source cannot give, and prints the gap here")
	p("    so that a partial match is never read as a whole-row match.")
	p("    corroboration claims made by admissible vectors: %d", s.CorroborationsClaimed)
	for _, src := range AttestationSources() {
		p("    %s — %s", src.ID, src.Citation)
		for _, rk := range src.RowKinds() {
			p("        %-12s attests %d of %d: %s", rk,
				len(src.ColumnsByRowKind[rk]), len(PeriodColumns()),
				strings.Join(src.ColumnsByRowKind[rk], ", "))
			p("        %-12s SILENT on: %s", "", strings.Join(src.Unattested(rk), ", "))
		}
		for _, c := range src.Caveats {
			p("        caveat: %s", c)
		}
	}
	p("")

	p("--- STRUCTURAL COVERAGE GAPS IN THE CORPUS (closed by capture, never by code) ---")
	for _, g := range CoverageGaps() {
		p("    [%s] %s — %s", g.Status, g.ID, g.Title)
		p("        %s", g.Statement)
		p("        owner: %s", g.Owner)
		p("        %s", g.Evidence)
		if g.Status == GapClosed {
			p("        closed by: %s", g.ClosedBy)
		}
	}
	p("")

	p("--- STANDING CLAIMS THIS HARNESS'S RULES DEPEND ON ---")
	for _, c := range Claims() {
		p("    %s [%s]", c.ID, c.Status)
		p("        %s", c.Statement)
		if c.OriginalWording != "" {
			p("        originally: %s", c.OriginalWording)
		}
		if c.NarrowedBy != "" {
			p("        %s", c.NarrowedBy)
		}
		p("        evidence: %s", c.Evidence)
	}
	p("")

	p("--- INVARIANT COVERAGE (checked against what the implementation RETURNED) ---")
	if len(s.Results) == 0 {
		p("    nothing graded")
	} else {
		for _, name := range AllInvariants() {
			hold, viol, exempt, na := 0, 0, 0, 0
			for _, r := range s.Results {
				for _, iv := range r.Invariants {
					if iv.Name != name {
						continue
					}
					switch iv.Status {
					case InvariantHold:
						hold++
					case InvariantViolated:
						viol++
					case InvariantExempted:
						exempt++
					case InvariantNoData:
						na++
					}
				}
			}
			p("    %-38s hold %-4d violated %-4d exempt %-4d n/a %d", name, hold, viol, exempt, na)
		}
	}
	p("")

	p("--- SUMMARY ---")
	p("    parity vectors          PASS %-4d FAIL %d", s.ParityPass, s.ParityFail)
	p("    contract-refusal        PASS %-4d FAIL %d   (derived from the ratified contract, NOT oracle-observed)",
		s.ContractPass, s.ContractFail)
	p("    self-test fixtures      PASS %-4d FAIL %d   (hand-authored; EXCLUDED from the parity count)",
		s.SelfTestPass, s.SelfTestFail)
	p("    refused                 %d   (no discriminating vector / seam blind — not a pass, not a failure)",
		s.Refused)
	p("    inadmissible            %d", s.Inadmissible)
	p("    harness errors          %d", s.Errored)
	p("    cells compared          %d graded, %d ungraded (never recorded by the capture)",
		s.GradedCells, s.UngradedCells)
	p("    kills named             %d money, %d structural (zero-margin by construction, never merged)",
		s.MoneyKills, s.StructuralKills)
	p("    recorded, never graded  %d rate factors (%s), %d declared over-scaled money cells",
		s.RateFactorsRecorded, PrecisionTranscribedRounded, s.OverScaledCells)
	p("    invariant violations    %d", s.InvariantViolations)

	if len(s.FatalReasons) > 0 {
		p("")
		p("--- WHY THIS RUN CANNOT BE TRUSTED ---")
		for _, fr := range s.FatalReasons {
			p("    * %s", fr)
		}
	}

	code := s.ExitCode()
	p("")
	switch {
	case code == 0 && s.SelfTestMode:
		p("VERDICT: SELF-TEST PASS (exit 0). The harness grades correctly. NOT a conformance PASS.")
	case code == 0:
		p("VERDICT: PASS (exit 0) — %d parity vectors match the pinned reference oracle, %d cells compared.",
			s.ParityPass, s.GradedCells)
		p("         This means \"matches the reference oracle on captured vectors, within the graded domain\".")
		p("         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.")
	case code == 1:
		p("VERDICT: FAIL (exit 1) — %d mismatched vector(s), %d invariant violation(s).",
			s.ParityFail+s.ContractFail+s.SelfTestFail, s.InvariantViolations)
	default:
		p("VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.")
	}
	p("")
}

func anyViolation(ivs []InvariantResult) bool {
	for _, iv := range ivs {
		if iv.Status == InvariantViolated {
			return true
		}
	}
	return false
}

func trunc(s string, n int) string {
	if len(s) <= n {
		return s
	}
	if n <= 3 {
		return s[:n]
	}
	return s[:n-3] + "..."
}

func firstLine(s string) string {
	if i := strings.IndexByte(s, '\n'); i >= 0 {
		return s[:i]
	}
	return s
}
