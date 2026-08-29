package conformance

import (
	"fmt"
	"io"
	"sort"
	"strings"

	ledgerconf "github.com/gerege/nexus/internal/apps/ledger/conformance"
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
	// THE GRADED CHECKOUT, PRINTED WHETHER OR NOT ANYTHING IS WRONG (P-35).
	//
	// One root decides four things — the corpus, the no-float census tree, the
	// contract.go that is hashed against the store pin, and the checkout every
	// capture_ref is resolved in. Until T165 that root was `FindRepoRoot(".")`,
	// the caller's WORKING DIRECTORY, and no line of this report named it. One
	// binary compiled from a tree carrying an unratified edit to the frozen
	// DEC-1 contract printed exit 2 from its own tree and VERDICT: PASS from a
	// clean sibling checkout — and the passing report was indistinguishable from
	// an honest one, because nothing in it said which tree had been read.
	//
	// So the root is printed, and HOW it was decided is printed beside it, and
	// the working directory's own answer is printed under it even when the two
	// agree. A line that only appears when something is wrong cannot be told
	// apart from a line that never runs.
	writeRepoRootLines(p, s)
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
	p("    counterfactuals named by GRADED vectors: %d  (%d money kills, %d structural kills)",
		s.CounterfactualsNamed, s.MoneyKills, s.StructuralKills)
	// PRINTED WHETHER OR NOT IT IS ZERO (P-35). A disclosure that only appears
	// when something is wrong is indistinguishable from one that never ran, and
	// on the committed store this line reads 0 — which is itself the evidence
	// that today's exposure is nil rather than merely unmeasured.
	p("    kills carried by REFUSED vectors: %d, credited to NOTHING (%d corroboration claims likewise)",
		s.RefusedCounterfactualsNamed, s.RefusedCorroborationsClaimed)
	p("    kills carried by HARNESS-ERROR vectors: %d, credited to NOTHING (%d corroboration claims "+
		"likewise)", s.ErroredCounterfactualsNamed, s.ErroredCorroborationsClaimed)
	p("        An errored vector is the strongest case of \"graded nothing\": a refusal is at least a")
	p("        decision about the vector, an error is the absence of one. Before A2-27 these credited")
	p("        the count above, so a run with NO implementation registered — 0 cells compared — printed")
	p("        113 kills and no UNBACKED claim at all. Reachable, not hypothetical: it is the standing")
	p("        state of cmd/conformance/impl_hook.go until a port is registered (finding A2-22-F3).")
	p("        A refusal is not a pass and not a failure: it says no discriminating vector exists here, or")
	p("        the seam is blind to the behaviour. A vector that graded nothing kills nothing, so its named")
	p("        kills do not enter the count above and do not remove a capability from the UNBACKED list.")
	p("        Until A2-22 they did both, and a refusal therefore made this report QUIETER — the one case")
	p("        with LESS evidence going silent (finding A2-19 F3).")
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
	p("    corroboration claims made by GRADED vectors: %d (a further %d are carried by REFUSED vectors "+
		"and %d by HARNESS-ERROR vectors, counted nowhere)",
		s.CorroborationsClaimed, s.RefusedCorroborationsClaimed, s.ErroredCorroborationsClaimed)
	p("        The claim itself SURVIVES a refusal — a corroboration is a fact about the RECORD, checked")
	p("        offline at admission, and no refusal reason impugns it. It is scoped to the graded")
	p("        population anyway, because this report scopes by POLARITY: hazards (rate factors,")
	p("        over-scaled cells) take the widest population, SUPPORT takes the narrowest, and a")
	p("        corroboration can only ever make the corpus look better attested. Add the numbers above to")
	p("        recover the corpus total; none of them is ever hidden (A2-22, adjudicated A2-24).")
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
	// FINDING T116-N1. An EXEMPTED invariant is a check that was switched off BY
	// THE VECTOR, on purpose, and until this section existed the only trace of it
	// in the run output was a count in the `exempt` column above — the reason was
	// readable nowhere but the JSON. That is the vacuous-guard class (P-22) with
	// extra steps: a silenced check that does not say who silenced it or why is
	// indistinguishable, from the report alone, from a check that passed.
	//
	// The rule this section enforces is the same one the NOT-RUN section below
	// enforces for placeholders: A CHECK THAT STOPS CHECKING SAYS SO, IN WRITING,
	// in the output a reader actually reads.
	p("--- INVARIANT ASSERTIONS DELIBERATELY EXEMPTED BY A VECTOR (the vector says why, here) ---")
	p("    An exemption is a check the VECTOR switched off, not one the harness could not run. It is")
	p("    admissible only for a shape where the REFERENCE ORACLE ITSELF violates the invariant and the")
	p("    implementation reproduces it, because there the assertion would be a claim about the oracle")
	p("    rather than about the port — and that is a graded-domain question, not a harness one. Every")
	p("    exemption below is named, scoped to one vector, and carries its own reason in full.")
	// BOTH CONJUNCTS ARE NOW ASSERTED, AND THE REPORT SAYS WHICH IS ASSERTED WHERE.
	// The sentence above has claimed two conjuncts since T116-N1 while the harness
	// asserted one; T222 raised that as F-3 and T230 as F-4, and both left it open.
	p("    THAT SENTENCE HAS TWO CONJUNCTS AND BOTH ARE NOW ASSERTED, in different places and with")
	p("    different consequences. (1) THE ORACLE CONJUNCT is decided OFFLINE, from the vector file")
	p("    alone, in the EXEMPTION GROUNDING section below: the exempted invariant is re-run against the")
	p("    schedule the CAPTURE recorded and must come back VIOLATED there, or the vector is refused.")
	p("    (2) THE PORT CONJUNCT is a statement about THIS RUN and is measured in the PORT CONJUNCT")
	p("    section below: the exempted invariant is run again, against the schedule THE IMPLEMENTATION")
	p("    RETURNED, and what it said is printed beside every exemption here. It is REPORTED, never")
	p("    refused — a port that satisfies an invariant the oracle violates has DIVERGED, and a")
	p("    divergence is the cell diff's finding, not a second admissibility verdict that could disagree")
	p("    with it. Until this run it was asserted by nothing, and the sentence above claimed it anyway.")
	// The count comes from the SUMMARY, not from a second walk of the results
	// (T220-N1). A number the report recomputes for itself is a number no test can
	// pin, and this one is now a corpus-wide tripwire.
	exemptCount := s.InvariantsExempted
	if exemptCount == 0 {
		p("    NONE — every invariant was asserted against every vector.")
	} else {
		for _, r := range s.Results {
			for _, iv := range r.Invariants {
				if iv.Status != InvariantExempted {
					continue
				}
				p("    %s — %s [EXEMPT]", r.CaseID, iv.Name)
				p("        REASON: %s", iv.Detail)
				switch {
				case iv.PortConjunctUndetermined():
					p("        PORT CONJUNCT: COULD NOT SAY — the implementation declared a placeholder on a")
					p("            cell this invariant reads, so the returned schedule answers neither way.")
					for _, na := range iv.PortNotAsserted {
						p("            THE RUN COULD NOT SAY: %s", na)
					}
				case iv.PortConjunctReproduced():
					p("        PORT CONJUNCT: REPRODUCED — the schedule the implementation RETURNED violates")
					p("            this invariant too, which is the second half of the sentence above: %s",
						iv.PortDetail)
				default:
					p("        PORT CONJUNCT: *** DIVERGED *** — the schedule the implementation RETURNED")
					p("            reports %s for this invariant, so the port does NOT reproduce the oracle")
					p("            behaviour this exemption exists for: %s", iv.PortObserved, iv.PortDetail)
				}
			}
		}
	}
	p("")

	// FINDING T220-N1 — THE EXEMPTION MECHANISM'S OWN POPULATION, STATED.
	//
	// The section above lists the exemptions that were EXERCISED on the graded
	// vectors. This one states what the ADMISSIBILITY check inspected, which is a
	// wider population (every loaded vector) and a different question: not "which
	// checks were switched off" but "was each one switched off over a violation
	// the capture actually recorded". It is printed whether or not anything is
	// wrong, because a guard that speaks only when it fires cannot be told apart
	// from a guard that never ran (P-22, P-35) — and if the corpus ever carries no
	// exemption at all, the NIL-COVERAGE notice says so in as many words rather
	// than letting an empty population read as a clean bill of health.
	ec := s.ExemptionCensus
	p("--- EXEMPTION GROUNDING (every exemption re-run against the schedule ITS OWN VECTOR recorded) ---")
	p("    An exemption is admissible only where the REFERENCE ORACLE ITSELF violates the invariant. That")
	p("    is asserted, not assumed: each exempted invariant is re-run against the vector's own recorded")
	p("    schedule, honouring that vector's unrecorded_fields, and must come back VIOLATED there. This")
	p("    section reports the ORACLE conjunct only; whether the PORT reproduces the oracle's behaviour is")
	p("    a grading-time question and nothing here asserts it. Three verdicts are INADMISSIBLE, refused")
	p("    in Admit and never a warning: DECORATION (the invariant holds OUTRIGHT on the oracle's own")
	p("    numbers, with no assertion withheld, so the exemption silences nothing and only inflates the")
	p("    count above), NOT-EVALUABLE (the invariant has nothing to assert here at all, with nothing")
	p("    withdrawn) and SCHEDULE-UNREADABLE (the recorded rows do not parse into a schedule). A fourth,")
	p("    UNDETERMINED-ON-THE-RECORD, is REPORTED AND ADMITTED: this vector's own unrecorded_fields")
	p("    withdrew a cell the invariant reads, so the record is SILENT — which is not evidence against")
	p("    the exemption, and refusing it would kill a legitimate vector for a gap in the CAPTURE")
	p("    (finding T225-F1). It is counted apart from GROUNDED because it is not evidence either way.")
	if ec.Declared == 0 {
		p("    NIL-COVERAGE — no vector in this store exempts any invariant, so the exemption-grounding")
		p("    check inspected an empty population. It inspected %d loaded vector(s) to find that out.",
			ec.VectorsInspected)
	} else {
		p("    INSPECTED %d loaded vector(s); %d of them exempt at least one invariant; %d exemption "+
			"declaration(s) examined.", ec.VectorsInspected, ec.VectorsExempting, ec.Declared)
		p("    %d GROUNDED (the recorded schedule VIOLATES the exempted invariant), %d UNGROUNDED.",
			ec.Grounded, ec.Ungrounded)
		p("    %d UNDETERMINED-ON-THE-RECORD (a cell the invariant reads was never recorded; admitted, "+
			"not evidence).", ec.Undetermined)
		for _, name := range ec.UngroundedNames {
			p("        UNGROUNDED: %s", name)
		}
		for _, u := range ec.UndeterminedExemptions {
			p("        UNDETERMINED: %s", u.Name)
			for _, na := range u.NotAsserted {
				p("            THE RECORD COULD NOT SAY: %s", na)
			}
		}
	}
	p("")

	// FINDING T222-F4 — THE CITATION, PRINTED. See exemption.go's citation block.
	//
	// The grounding section above says the exemption is grounded IN THE RECORD.
	// This one says WHICH record, and proves the harness opened it: the artefact,
	// its size in bytes, the case id, and the byte offset the id was found at. A
	// reason that cites nothing is an assertion; the numbers below could not have
	// been produced without resolving the citation.
	p("--- EXEMPTION CITATIONS (which observation each admissible exemption rests on) ---")
	p("    An exemption's whole argument is that THE REFERENCE ORACLE WAS OBSERVED TO BEHAVE THIS WAY.")
	p("    Its `reason` is free prose and always was; until finding T222-F4 was closed, nothing required")
	p("    that prose to point at anything, so an OBSERVATION and an ASSERTION were indistinguishable to")
	p("    this harness. The citation is MINTED by the harness, not read from the vector, and it is")
	p("    refused in Admit unless all three components resolve: the committed capture ARTEFACT exists")
	p("    in this repository and is non-empty; the capture CASE ID occurs inside that artefact's bytes")
	p("    (a bundle citation that names no case in the bundle is a page that is not in the book); and")
	p("    the RECORD'S OWN SENTENCE — the exempted invariant re-run against the captured schedule — is")
	p("    non-empty. The byte offsets below are the proof the artefact was opened.")
	switch {
	case ec.Declared == 0:
		p("    NIL-COVERAGE — no vector in this store exempts any invariant, so no citation was required")
		p("    and none was minted. Stated rather than left as silence (P-35).")
	case len(ec.Citations) == 0:
		p("    NO CITATION WAS MINTED over %d declared exemption(s). Every one of them was refused on some")
		p("    other ground before a citation was required — see the refusals above; this run has no")
		p("    admissible exemption to cite.", ec.Declared)
	default:
		admissible := ec.Grounded + ec.Undetermined
		p("    MINTED %d citation(s) for %d admissible exemption(s) (%d GROUNDED + %d "+
			"UNDETERMINED-ON-THE-RECORD) out of %d declared.",
			len(ec.Citations), admissible, ec.Grounded, ec.Undetermined, ec.Declared)
		if len(ec.Citations) != admissible {
			p("    *** THE CITATION WALK AND THE GROUNDING WALK DISAGREE: %d citation(s) for %d admissible",
				len(ec.Citations), admissible)
			p("    *** exemption(s). One of the two stopped counting; neither number is evidence.")
		}
		unresolved := 0
		for _, c := range ec.Citations {
			if !c.Resolved() {
				unresolved++
			}
		}
		p("    %d of %d RESOLVED in full; %d did not (each one's refusal is printed above and the vector",
			len(ec.Citations)-unresolved, len(ec.Citations), unresolved)
		p("    carrying it is INADMISSIBLE).")
		for _, c := range ec.Citations {
			p("        %s — %s [%s]", c.CaseID, c.Invariant, c.Verdict)
			if c.CaseIDAt >= 0 {
				p("            ARTEFACT: %s (%d bytes); CASE %s found at byte offset %d",
					c.CaptureRef, c.ArtefactBytes, c.CaptureCaseID, c.CaseIDAt)
			} else {
				p("            ARTEFACT: %q (%d bytes); CASE %q *** DID NOT RESOLVE ***",
					c.CaptureRef, c.ArtefactBytes, c.CaptureCaseID)
			}
			p("            THE RECORD SAYS: %s", c.Observation)
		}
	}
	p("")

	// FINDING T222-F3 / T230-F4 — THE PORT CONJUNCT, MEASURED.
	//
	// Printed whether or not anything diverged, with its own NIL-COVERAGE notice,
	// because a guard that speaks only when it fires cannot be told apart from one
	// that never ran (P-22, P-35) — and this one spent two tasks as prose saying
	// it was not asserted at all.
	pc := s.PortConjunct
	p("--- PORT CONJUNCT (every exempted invariant re-run against the schedule THE IMPLEMENTATION RETURNED) ---")
	p("    The exemption sentence has two conjuncts: the oracle violates the invariant, AND the")
	p("    implementation reproduces it. The section above asserts the first, offline, and refuses when")
	p("    it fails. This asserts the second, on THIS run's output, and REPORTS rather than refuses: a")
	p("    port that SATISFIES an invariant the oracle violates has diverged from the oracle, which is a")
	p("    parity finding the cell diff owns. Nothing in this section can fail a vector, and nothing in")
	p("    it is a licence: DIVERGED here means the exemption is excusing a behaviour the port does not")
	p("    actually have, which is worth a reader's attention even when every graded cell matched.")
	if pc.Assertions == 0 {
		p("    NIL-COVERAGE — no graded vector exempted any invariant on this run, so the port conjunct")
		p("    had an empty population. It is stated rather than left as silence.")
	} else {
		p("    INSPECTED %d exempted assertion(s) on the graded vectors.", pc.Assertions)
		p("    %d REPRODUCED (the returned schedule violates the exempted invariant too), %d DIVERGED, "+
			"%d COULD NOT SAY.", pc.Reproduced, pc.Diverged, pc.Undetermined)
		if !pc.Partitions() {
			p("    *** THE CENSUS DOES NOT PARTITION: %d + %d + %d != %d inspected. It has stopped counting",
				pc.Reproduced, pc.Diverged, pc.Undetermined, pc.Assertions)
			p("    *** something, so none of these figures is evidence.")
		}
		for _, name := range pc.DivergedNames {
			p("        DIVERGED: %s", name)
		}
		for _, name := range pc.UndeterminedNames {
			p("        COULD NOT SAY: %s", name)
		}
	}
	p("")

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

	writeLedgerSection(p, s)

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
	// T116-N1. Exemptions belong beside the violation count, not only in the
	// coverage table, so that "invariant violations 0" can never be read without
	// the number of checks that were switched off to get there.
	p("    invariant assertions    %d EXEMPTED BY A VECTOR (switched off on purpose; each one's reason is listed above)",
		exemptCount)
	// PRINTED WHETHER OR NOT ANYTHING IS WRONG (P-35). A guard that speaks only
	// when it fails cannot be told apart from a guard that never ran, and both
	// of the no-float guards were exactly that until T154. The counts are the
	// assertion: N files and T tokens were inspected, and each violation class
	// was 0. A run showing `0 files` here has checked nothing and is exit 2.
	// T166 ADDED THE PACKAGE COUNT AND THE PACKAGE LIST. The file count alone
	// read as healthy — "24 Go files" — on a repository where an entire second
	// package and every subdirectory in the module were outside the walked root.
	// A reader can only tell a full-module walk from a single-directory walk by
	// seeing the SET, so the set is printed.
	p("    no-float census         %d Go packages / %d Go files / %d tokens / %d import specs inspected under %s (recursive)",
		s.NoFloatCensus.PackagesScanned, s.NoFloatCensus.FilesScanned,
		s.NoFloatCensus.TokensScanned, s.NoFloatCensus.ImportsScanned, GuardedGoTreeRel)
	p("                            %d forbidden identifiers, %d floating-point or imaginary LITERALS, %d forbidden imports, %d unscannable files",
		len(s.NoFloatCensus.IdentifierViolations), len(s.NoFloatCensus.LiteralViolations),
		len(s.NoFloatCensus.ImportViolations), len(s.NoFloatCensus.ScanErrors))
	for _, dir := range s.NoFloatCensus.PackageDirs {
		p("                            covered: %s/%s", GuardedGoTreeRel, dir)
	}
	// THE ABSOLUTE ROOT, PRINTED BECAUSE "nexus" IS A RELATIVE PATH AND A
	// RELATIVE PATH CANNOT SAY WHICH CHECKOUT WAS GRADED.
	//
	// grade.go joins this census root onto opts.RepoRoot, which cmd/conformance
	// resolves with FindRepoRoot(".") — from the CALLER'S working directory, not
	// from the script's location. conformance.sh's own shell guards derive their
	// root from "$SCRIPT_DIR/..". The two therefore disagree whenever the script
	// is invoked by absolute path from a different checkout, and T166 MEASURED
	// that disagreement: running this worktree's conformance.sh with the CWD set
	// to the main checkout printed the WORKTREE's path in the shell guard line
	// and 56295 tokens — the MAIN checkout's count — in the census line, in one
	// run, with VERDICT: PASS and nothing to say the two legs had graded
	// different trees. That resolution defect belongs to T165 and is not fixed
	// here; what is fixed here is the SILENCE, because a guard that names one
	// tree and inspects another is the same class of defect T166 exists to close.
	p("                            census root walked: %s", s.NoFloatCensus.Root)

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
		// THE DIVERGENCE QUALIFIER [T397, closing T387's F-T387-1].
		//
		// The sentence above used to sit UNQUALIFIED over a corpus that, since
		// T360, contains captured vectors on which this port demonstrably does
		// NOT match the reference oracle — it REFUSES where the oracle ACCEPTS.
		// It was saved only by its own trailing "within the graded domain" and by
		// a census two hundred lines further up, which is precisely the
		// misreading G-19 exists to prevent: a reader who takes the top line at
		// face value concludes the port agrees with Fineract everywhere.
		//
		// IT IS PRINTED FROM THE LEDGER SUMMARY'S OWN FIGURES, not from a
		// constant, so it cannot drift away from the census it summarises; and
		// the ZERO case is printed too, because "there are no recorded
		// divergences" and "nobody looked" have to stay distinguishable — the
		// same reason every other empty state in this report is not silent.
		if d := s.recordedDivergences(); d > 0 {
			p("         IT EXCLUDES %d RECORDED DIVERGENCE(S) — see THE DIVERGENCE CENSUS above. On those", d)
			p("         captured vectors this port does NOT match the reference oracle: the oracle ACCEPTED")
			p("         a request this port REFUSES. Each is an OPEN disagreement held at the gate named on")
			p("         its row, and a green line there means only \"the disagreement is still exactly as")
			p("         recorded\" — never that it has been fixed, and never that the port is right.")
		} else if s.Ledger != nil {
			p("         NO DIVERGENCE IS RECORDED in this store, so the sentence above is not excluding any")
			p("         known port/oracle disagreement. That is a fact about the CORPUS, not a fact about")
			p("         the port: a disagreement nobody has captured is not a disagreement that is absent.")
		}
		p("         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.")
	case code == 1:
		p("VERDICT: FAIL (exit 1) — %d mismatched vector(s), %d invariant violation(s).",
			s.ParityFail+s.ContractFail+s.SelfTestFail, s.InvariantViolations)
	default:
		p("VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.")
	}
	p("")
}

// recordedDivergences returns how many DIVERGENCE-class vectors the ledger half
// loaded and graded, in either direction. [T397, for T387's F-T387-1]
//
// PASS AND FAIL ARE BOTH COUNTED, and that is the meaning of the figure rather
// than an oversight. The verdict line it qualifies claims "this port matches the
// reference oracle on the captured vectors"; a divergence vector is a captured
// vector on which it does NOT — whether the disagreement is still behaving
// exactly as recorded (PASS) or has moved (FAIL). Both are exclusions from that
// claim.
//
// IT READS THE LEDGER SUMMARY AND COMPOSES NOTHING. The ledger context renders
// its own divergence census (ledger/conformance/notgraded.go); this returns the
// same two fields that census prints, so the verdict qualifier and the census can
// never disagree about how many there are. A second, independently maintained
// count here is exactly the defect A2-34 found in the hand-written not-graded
// block.
//
// Nil ledger — self-test mode, a context filter, or a store with no ledger vector
// — returns 0. The caller distinguishes "zero because there are none" from "zero
// because the ledger half did not run" by testing s.Ledger itself, and the ledger
// section above has already printed which of those states this run is in.
func (s *Summary) recordedDivergences() int {
	if s.Ledger == nil {
		return 0
	}
	return s.Ledger.DivergencePass + s.Ledger.DivergenceFail
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

// writeRepoRootLines prints WHICH checkout was graded and HOW that was decided.
//
// Every branch prints something. There is no arm of this function that stays
// silent, because the failure it exists to expose — a run that graded a tree the
// reader did not expect — looked exactly like a healthy run until T165 measured
// it. Deterministic: no map iteration, no time, no set ordering (T90).
func writeRepoRootLines(p func(string, ...any), s *Summary) {
	res := s.RepoRootRes

	switch {
	case res.Root != "" && res.Source == RepoRootFromBuildAnchor:
		p("    repo root       %s", res.Root)
		p("                    resolved from the BUILD ANCHOR — the tree this binary was compiled from")
		p("                    anchor: %s", res.AnchorFile)
	case res.Root != "":
		// An explicit override. It is legitimate and it is also the one way left
		// to grade a tree other than the one the binary was built from, so the
		// anchor is printed next to it and any divergence is called out.
		p("    repo root       %s", res.Root)
		p("                    resolved from %s — an EXPLICIT OVERRIDE of the build anchor", res.Source)
		if res.AnchorRoot != "" {
			p("                    build anchor would have graded: %s", res.AnchorRoot)
			if res.AnchorRoot != res.Root {
				p("                    *** OVERRIDE DIVERGES FROM THE COMPILED BYTES: this run grades source that")
				p("                        is NOT what produced this binary. That is the caller's stated intent,")
				p("                        recorded here so no reader has to infer it. ***")
			}
		} else {
			p("                    build anchor unusable: %s", res.AnchorErr)
		}
	default:
		// Programmatic caller (the Go tests drive Run directly). Say so; do not
		// leave a blank where a provenance line belongs.
		if s.RepoRoot != "" {
			p("    repo root       %s", s.RepoRoot)
		} else {
			p("    repo root       (not recorded)")
		}
		p("                    resolution NOT RECORDED — this run was driven programmatically, not through")
		p("                    cmd/conformance, so nothing attests which rule chose the root.")
	}

	// THE CROSS-CHECK, PRINTED IN BOTH DIRECTIONS. `SAME` is as important as
	// `DIFFERENT`: it is the evidence that the check ran.
	switch {
	case res.CWD == "":
		p("                    cwd cross-check: the working directory could not be read (%s)", res.CWDErr)
	case res.Root == "":
		p("                    cwd cross-check: not performed (no recorded resolution)")
	case res.CWDRoot == "":
		p("                    cwd cross-check: cwd %s resolves to NO repository (%s)", res.CWD, res.CWDErr)
		p("                                     — pre-T165 this run would have REFUSED here instead of grading")
	case res.CWDRoot == res.Root:
		p("                    cwd cross-check: SAME — cwd %s resolves to the graded root", res.CWD)
	default:
		p("                    cwd cross-check: DIFFERENT — cwd %s resolves to", res.CWD)
		p("                                     %s", res.CWDRoot)
		p("                                     PRE-T165 THAT TREE, NOT THE ONE ABOVE, WOULD HAVE BEEN GRADED:")
		p("                                     its corpus, its contract.go digest, its no-float census and its")
		p("                                     capture_refs. The graded root is the build anchor and is correct;")
		p("                                     this line exists so the divergence is never silent again.")
	}
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

// writeLedgerSection prints the SECOND bounded context's own section, under its
// own comparator and its own counts.
//
// DEC-2 §5.2 requirement 6a is the reason every figure below is separate from
// the loanschedule figures above it, and the reason this function refuses to add
// them together anywhere: "the summary must report the ledger vector under its
// own comparator and its own count — NOT folded into `parity vectors PASS
// <B.parity>`."
//
// IT PRINTS ITS OWN LIMITS ON EVERY RUN, PASS OR FAIL (P-35, P-22). A ledger
// PASS is a much narrower claim than a reader would assume, and a section that
// stated its limits only when something went wrong would be indistinguishable
// from one that had none.
func writeLedgerSection(p func(string, ...any), s *Summary) {
	if s.SelfTestMode {
		// A DISTINCT LINE FOR A DISTINCT STATE, and the distinction is
		// load-bearing rather than cosmetic. -self-test grades the HARNESS by
		// replaying the loanschedule store through a generator that computes
		// nothing; there is no ledger replay and inventing one would put a
		// ledger implementation inside the harness that grades ledger
		// implementations. So the ledger half does not run.
		//
		// IT MUST NOT PRINT THE SAME BANNER AS AN EMPTY STORE. conformance.sh's
		// census gate reads the ledger figures and compares them for EQUALITY,
		// and the deflation case it exists to catch — every ledger vector
		// deleted — prints the empty-store banner. If a not-run run and an
		// empty-store run were indistinguishable in the report, the gate would
		// have to skip on both, and the deflation arm would be dead. This line
		// is what lets the gate skip exactly one of them and say which.
		p("--- LEDGER (tierA-gl-accounting) ---")
		p("    LEDGER NOT RUN IN SELF-TEST MODE — the ledger half grades a port, and -self-test grades")
		p("    the harness by replay. No ledger figure below is a measurement of anything, and none is")
		p("    printed. This is NOT the same state as a store with no ledger vector in it.")
		p("")
		return
	}
	if s.Ledger == nil && s.ContextFilter != "" && !ledgerconf.IsSchemaContext(s.ContextFilter) {
		// A THIRD DISTINCT STATE, for the same reason the self-test one is
		// distinct: the census gate must be able to tell "this run did not look"
		// from "there is nothing there", and only one of those two is the
		// deflation the pin exists to catch.
		p("--- LEDGER (tierA-gl-accounting) ---")
		p("    LEDGER NOT SELECTED — this run was filtered to context %q, so the ledger half was not",
			s.ContextFilter)
		p("    graded and no ledger figure is printed. Run without a filter to grade it. This is NOT the")
		p("    same state as a store with no ledger vector in it.")
		p("")
		return
	}
	if s.Ledger == nil {
		// NOT SILENT. "There are no ledger vectors" is a fact about the corpus
		// that a reader of a green run needs, and it is exactly the fact G-11's
		// closure notes were careful to keep saying: "Nothing grades the
		// ledger's money yet". A blank here would let that stop being said the
		// moment somebody stopped looking.
		p("--- LEDGER (tierA-gl-accounting) ---")
		p("    NO LEDGER VECTOR IS IN THIS STORE, so NOTHING in this run grades a GL account, a mapping,")
		p("    a financial activity or a journal entry. Every figure in the SUMMARY below is a")
		p("    loanschedule figure and says nothing whatever about the ledger.")
		p("")
		return
	}
	l := s.Ledger
	p("--- LEDGER (tierA-gl-accounting) — SECOND SCHEMA, SECOND COMPARATOR, SEPARATE COUNTS ---")
	p("    implementation          %s", l.ImplementationName)
	if l.ImplementationWrong != "" {
		p("    ⚠ THIS IS A DELIBERATELY WRONG IMPLEMENTATION, selected with -ledger-impl:")
		p("      %s", l.ImplementationWrong)
		p("      A RED below is the EXPECTED result and is not a defect in the port.")
	}
	for _, r := range l.Results {
		p("    %-46s %-14s %-22s %-14s %4d cells (%d money)",
			trunc(r.CaseID, 46), r.Class, trunc(r.Seam, 22), r.Outcome, r.GradedCells, r.MoneyCells)
		for _, d := range r.Detail {
			p("        %s", d)
		}
		for _, iv := range r.Invariants {
			// INDEPENDENT / DEPENDENT IS PRINTED ON EVERY LINE, not only when it
			// matters, because a reader counting green lines has no other way to
			// tell two assertions from one assertion counted twice. On a
			// one-against-N journal entry the leg-derived form of
			// splits_sum_to_whole IS the equation double_entry_balances asserts;
			// it becomes independent only where the recorded request carries its
			// own transaction amount.
			dep := "DEPENDENT"
			if iv.Independent {
				dep = "INDEPENDENT"
			}
			if iv.Status == ledgerconf.InvariantNotApplicable {
				dep = "—"
			}
			p("        INVARIANT %-24s %-4s (%d assertion(s), %s)  %s",
				iv.Name, iv.Status, iv.Assertions, dep, firstLine(iv.Detail))
		}
	}
	for _, le := range l.LoadErrors {
		p("    LEDGER FILE THAT COULD NOT BE READ: %s: %v", le.Path, le.Err)
	}
	for _, f := range l.Fatal {
		p("    LEDGER FATAL: %s", f)
	}
	p("    ledger parity           PASS %-4d FAIL %d", l.ParityPass, l.ParityFail)
	p("    ledger oracle-refusal   PASS %-4d FAIL %d   (an HTTP status and error code the ORACLE returned",
		l.RefusalPass, l.RefusalFail)
	p("                                              and a capture recorded — NOT a contract sentinel)")
	p("    ledger inadmissible     %d", l.Inadmissible)
	p("    ledger harness errors   %d", l.Errored)
	p("    ledger cells compared   %d graded, of which %d are MONEY cells in int64 minor units",
		l.GradedCells, l.MoneyCells)
	p("    ledger kills named      %d money, %d structural", l.MoneyKills, l.StructuralKills)
	p("    ledger invariants       %d violation(s), %d non-vacuous assertion(s) made, of which %d are",
		l.InvariantViolations, l.InvariantAssertions, l.IndependentAssertions)
	p("                            INDEPENDENT (able to go RED while every other invariant on the same")
	p("                            entry stays GREEN). A DEPENDENT hold is not a second piece of evidence.")
	p("    ledger exemptions       %d DECLARED (this schema ADMITS NONE; a declared exemption is",
		l.DeclaredExemptions)
	p("                                        INADMISSIBLE, so this figure is pinned at 0 by")
	p("                                        conformance.sh and both directions of drift are gated)")
	// PART TWO OF THE CITATION, CENSUSED ON EVERY RUN. [T243, from A2-34 F-3]
	// A2-34 found part two resolving BY FILE NAME on three of these citations --
	// a branch that reads ZERO bytes of the artefact and compares two fields of
	// one vector to each other -- and nothing in the report said so, because a
	// check that cannot fail reports "pass". The classes are printed whatever
	// they are; FILE-NAME-ONLY is pinned by identity in ledger admit.go and both
	// directions of drift refuse.
	p("    ledger citations        %d PART-TWO resolutions over the loaded corpus: %d ARTEFACT-BYTES,",
		len(l.Citations), l.CitationsByBytes)
	p("                            %d HTTP-SIDECAR, %d FILE-NAME-ONLY (pinned %d), %d UNRESOLVED.",
		l.CitationsBySide, l.CitationsNameOnly, ledgerconf.CitationNameOnlyPinCount(), l.CitationsUnres)
	p("                            FILE-NAME-ONLY reads NO byte of the artefact: it checks that the ref")
	p("                            this vector wrote contains the case id this vector wrote. It is not")
	p("                            evidence about the artefact, it is pinned by (case_id, field) in")
	p("                            ledger/conformance/admit.go, and a fourth is INADMISSIBLE.")
	for _, c := range l.Citations {
		if c.Mode == ledgerconf.CitationByNameOnly {
			p("                            FILE-NAME-ONLY: %s %s -> %s", c.VectorCaseID, c.Field, c.Ref)
		}
	}
	p("")

	// THE NOT-GRADED BLOCK IS NOT WRITTEN HERE ANY MORE. It used to be sixteen
	// lines of hand-written prose in this function, and A2-34 found both defects
	// that shape guarantees: it printed SIX of the EIGHT `in_graded_domain: false`
	// rows the registry declares (F-5, and one of the two it dropped had been
	// added by the very task that told the driver all of them were printed), and
	// one of the six it did print was measurably FALSE against the live oracle
	// (F-4 — "gl 18, 22, 16 have ZERO journal entries", where gl 16 has sixteen,
	// more than any other account, and is a promoted leg of three of the four
	// parity vectors printed as PASS a dozen lines above).
	//
	// The ledger context now renders its own coverage prose from its own
	// registry: the row set is derived, the slot names are decoded through the
	// ported Fineract enum, and each slot's account activity is MEASURED from the
	// promoted corpus at render time. This loop composes nothing — which is the
	// point, because anything composed here is a second place for the account of
	// the ledger's coverage to disagree with the ledger's own registry.
	for _, line := range l.NotGradedLines() {
		p("%s", line)
	}

	// THE ORACLE-DERIVED COLUMN CARVE-OUT [T429, G-22]. Printed EVERY run, pass
	// or fail, and printed as a NAMED ABSENCE when no declaration is loaded.
	//
	// It is rendered by the ledger context from its own declaration, and this
	// loop composes nothing, for the same reason the not-graded loop above
	// composes nothing: anything composed here is a second place for the account
	// of what the ledger does not compare to disagree with the ledger's own
	// record of it, and A2-34 F-4/F-5 is what that costs.
	for _, line := range l.OracleDerivedLines() {
		p("%s", line)
	}
}
