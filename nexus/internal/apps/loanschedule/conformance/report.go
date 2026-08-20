package conformance

import (
	"fmt"
	"io"
	"sort"
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
		// FINDING T90 — THIS LINE USED TO MOVE ON ITS OWN. Ranging the map
		// directly printed these lines in a different order between two runs of
		// the SAME binary on the SAME store, because Go randomises map iteration
		// order. Measured on main's bytes: 30 runs, 2 distinct sha256, split
		// 26/4, differing ONLY in whether schedule.core or monthend.reanchor
		// printed first (T81 measured 23/7, T86 27/3, and it bit T86 live).
		//
		// It is not cosmetic. This pipeline uses BYTE-IDENTITY of the harness's
		// own output as evidence: T81 had to normalise a run through a sorted
		// diff to show its change was inert, and reviewers are routinely asked to
		// diff a run against main. Output that reorders itself weakens every such
		// proof and — worse — trains a reader to explain away a diff instead of
		// investigating it.
		//
		// THE ORDER, AND WHY IT IS TOTAL. Keys are capability names, and they are
		// keys of a Go map, so they are pairwise DISTINCT; sort.Strings orders
		// them by Go's byte-wise `<` over the UTF-8 encoding, which is a strict
		// total order on distinct strings. No tie can arise, so the printed
		// sequence is a function of the map's CONTENTS ALONE — never of insertion
		// order, hash seed, map size or toolchain version.
		//
		// The ids WITHIN a line are ordered the same way, on a copy, so that this
		// line's determinism is checkable without leaving this file
		// (CapabilityRegistry.CounterfactualCoverage sorts them too — sorting an
		// already-sorted slice is a no-op, and the report must not inherit its
		// determinism from a function three files away). Ids REPEAT here, one per
		// vector naming that counterfactual, so the sequence is a multiset; a
		// sorted multiset of strings is unique, hence total on this input as
		// well. Equal ids are interchangeable by definition, so sort.Strings
		// being unstable cannot show.
		for _, capName := range sortedKeys(s.CounterfactualCoverage) {
			ids := append([]string(nil), s.CounterfactualCoverage[capName]...)
			sort.Strings(ids)
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
			hold, viol, exempt, na, skipped := 0, 0, 0, 0, 0
			for _, r := range s.Results {
				for _, iv := range r.Invariants {
					if iv.Name != name {
						continue
					}
					skipped += len(iv.NotAsserted)
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
			p("    %-38s hold %-4d violated %-4d exempt %-4d n/a %-4d not-asserted %d",
				name, hold, viol, exempt, na, skipped)
		}
	}
	p("")

	// FINDING T58-N2. An assertion that did not run is reported here in full,
	// never inferred from a HOLD. A HOLD carrying skipped rows is a PARTIAL hold
	// and this section is the only place a reader can see which rows it covered.
	p("--- INVARIANT ASSERTIONS THAT COULD NOT RUN (a cell the capture never recorded) ---")
	p("    An invariant reads the schedule the implementation RETURNED. Where the implementation could not")
	p("    compute a cell — only the self-test replay ever can't, and only for a cell the vector's own")
	p("    unrecorded_fields withdrew — the assertions that read it are DECLARED not-applicable here rather")
	p("    than run against the stand-in. Both directions of that defect were live before this section")
	p("    existed: balance_roll_forward went RED on a placeholder, and principal_amortizes_to_zero went")
	p("    quietly GREEN on one, which is the worse half. A check that stops checking says so, in writing.")
	if s.InvariantAssertionsNotRun == 0 {
		p("    NONE — every invariant assertion ran, on cells somebody actually observed.")
	} else {
		for _, r := range s.Results {
			for _, iv := range r.Invariants {
				if len(iv.NotAsserted) == 0 {
					continue
				}
				p("    %s — %s [%s]", r.CaseID, iv.Name, iv.Status)
				for _, na := range iv.NotAsserted {
					p("        NOT ASSERTED: %s", na)
				}
			}
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
	p("    invariant assertions    %d NOT RUN (a cell nobody observed; listed above, never inferred)",
		s.InvariantAssertionsNotRun)

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

// sortedKeys returns m's keys in ascending byte-wise order.
//
// IT IS THE PACKAGE'S ONE WAY TO WALK A MAP THAT REACHES OUTPUT (finding T90).
// Ranging a map directly is the defect it exists to prevent: Go randomises
// iteration order, so a report line, a diagnostic list or a fatal reason built
// that way changes position between two runs of one binary on one input, and this
// pipeline treats byte-identity of harness output as evidence.
//
// The order is TOTAL, not merely "whatever sort.Strings does": map keys are
// pairwise distinct, and byte-wise `<` on distinct strings is a strict total
// order, so there are no ties to break and the result depends only on the SET of
// keys. A caller that also needs the VALUES ordered must say so itself — a slice
// value carries its own order and this function knows nothing about it.
func sortedKeys[V any](m map[string]V) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
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
