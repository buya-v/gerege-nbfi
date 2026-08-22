package conformance

import (
	"fmt"
	"strings"
)

// THE EXEMPTION TRIPWIRE — finding T220-N1, raised against T116 while approving it.
//
// An `invariant_exemptions` entry switches a property invariant OFF for one
// vector. Until this file existed, admit.go asked exactly two things of one: that
// it names an invariant this harness knows, and that it carries a non-empty
// reason. Both are satisfiable by prose. NOTHING asked whether the exemption
// SILENCES ANYTHING, and nothing counted the exemptions corpus-wide, so two
// shapes were admissible with no check able to see either:
//
//	(1) A DECORATION. An exemption on an invariant that would have HELD anyway.
//	    It silences nothing, but it inflates the exempted count and teaches a
//	    reader that the corpus is more exempted than it is. T116 itself dropped a
//	    proposed THIRD exemption — balance_roll_forward on the two family-B
//	    vectors — precisely because it holds unexempted. That judgement was made
//	    by hand, by one author, once, and nothing enforced it afterwards.
//
//	(2) AN EXEMPTION PAIRED WITH unrecorded_fields WITHDRAWING THE SAME CELLS.
//	    This is the dangerous one. unrecorded_fields removes the cells from the
//	    cell diff; the exemption removes the invariant that would otherwise have
//	    noticed. Between them nothing reads those cells at all, and the report
//	    still prints a REASON that describes the ORACLE's behaviour — a claim
//	    about numbers this capture never recorded.
//
//	    T220 proved that an exemption cannot hide a port divergence TODAY, and
//	    proved it only because every cell the two committed exemptions read is a
//	    GRADED cell on those two vectors. That is a property of TODAY'S CORPUS,
//	    not of the mechanism. This file makes it a property of the mechanism.
//
// THE RULE, PHRASED POSITIVELY (P-35). The harness does not grep an exemption's
// reason for weasel words and it does not look for a bad shape. It asserts the
// property the report already claims for every exemption, in report.go's own
// words:
//
//	"It is admissible only for a shape where the REFERENCE ORACLE ITSELF violates
//	 the invariant and the implementation reproduces it."
//
// So: RE-RUN THE EXEMPTED INVARIANT AGAINST THE SCHEDULE THE CAPTURE RECORDED —
// the oracle's own output, honouring that same vector's unrecorded_fields — AND
// REQUIRE IT TO BE VIOLATED THERE. An exemption is admissible exactly when the
// thing it excuses is visible in the record.
//
// That single positive assertion refuses both shapes above and distinguishes
// them by name:
//
//   - VIOLATED   -> GROUNDED. The record shows the violation the reason describes.
//   - HOLD       -> DECORATION. The invariant holds on the oracle's own numbers,
//     so the exemption silences nothing and only moves a count.
//   - N/A, with cells NOT ASSERTED -> RESTS-ON-WITHDRAWN-CELLS. Shape (2), named.
//     The invariant reads only cells this vector's own unrecorded_fields
//     withdrew, so the exemption's claim about the oracle rests on numbers
//     nobody recorded.
//   - N/A, nothing withdrawn -> NOT-EVALUABLE. No periods at all (a
//     contract-refusal vector), or no observed total for splits_sum_to_whole to
//     sum to. There is no violation in the record either way.
//
// WHY THIS IS A REFUSAL IN Admit AND NOT A REPORT LINE.
//
// Admit's own doctrine is that an INADMISSIBLE vector is one the harness cannot
// make a statement about the implementation from, and the precedent that settles
// it is finding T9-F1b (admitDivergentCell): a structural kill naming a cell the
// same vector withdrew from grading is INADMISSIBLE, not a warning — because the
// store may not RECORD A CLAIM THAT IS NOT EVIDENCE. An exemption is a recorded
// claim of exactly that kind: "the oracle violates this invariant here". A
// decoration is that claim refuted by the vector's own record; a
// rests-on-withdrawn-cells exemption is that claim with no record behind it. Both
// are decidable OFFLINE, from the file alone, with no implementation and no run —
// which is the signature of an admissibility question rather than a grading one.
//
// And the consequence of leaving either in the report only is the T164/A2-11
// shape: a number a reader trusts, kept honest by prose. The exempted count is
// quoted as evidence about the corpus; a count that can be inflated by an
// exemption that silences nothing is not evidence.
//
// The COUNT is a different question and gets a different answer — see
// Summary.InvariantsExempted and TestExemptionCountIsPinnedCorpusWide. A hard cap
// in the binary would refuse legitimate corpus growth at RUN time; the corpus-wide
// pin belongs in the test suite beside the kill-count tripwires, where moving it
// is a deliberate edit a reviewer sees.

// ExemptionGroundingStatus is the verdict on one `invariant_exemptions` entry.
type ExemptionGroundingStatus string

const (
	// ExemptionGrounded: the schedule the capture recorded VIOLATES the exempted
	// invariant. The exemption silences a check that would otherwise have fired,
	// which is the only thing an exemption is for.
	ExemptionGrounded ExemptionGroundingStatus = "GROUNDED"

	// ExemptionDecoration: the invariant HOLDS on the oracle's own recorded
	// schedule. Shape (1).
	ExemptionDecoration ExemptionGroundingStatus = "DECORATION"

	// ExemptionRestsOnWithdrawnCells: the invariant reads only cells this
	// vector's own unrecorded_fields withdrew, so it could not be evaluated
	// against the record at all. Shape (2), the dangerous pairing.
	ExemptionRestsOnWithdrawnCells ExemptionGroundingStatus = "RESTS-ON-WITHDRAWN-CELLS"

	// ExemptionNotEvaluable: the invariant reports N/A for a reason that is not a
	// withdrawn cell — no periods at all, or no observed total to sum to.
	ExemptionNotEvaluable ExemptionGroundingStatus = "NOT-EVALUABLE"

	// ExemptionUnknownInvariant: the entry names no invariant this harness runs,
	// so there is nothing to re-run and nothing it could be silencing.
	ExemptionUnknownInvariant ExemptionGroundingStatus = "UNKNOWN-INVARIANT"

	// ExemptionScheduleUnreadable: the vector's own expect.periods could not be
	// turned into a schedule. Reported rather than swallowed: an exemption whose
	// grounding could not be evaluated is not an exemption that was checked.
	ExemptionScheduleUnreadable ExemptionGroundingStatus = "SCHEDULE-UNREADABLE"
)

// ExemptionGrounding is the verdict on one exemption, with the invariant's own
// sentence about the recorded schedule carried along so the refusal can quote it.
type ExemptionGrounding struct {
	Invariant string
	Status    ExemptionGroundingStatus

	// Observed is what the exempted invariant reported when re-run against the
	// schedule the capture recorded. Empty when it could not be run at all.
	Observed InvariantStatus

	// Detail is the invariant's own detail sentence for Observed.
	Detail string

	// NotAsserted are the assertions the invariant could not make because a cell
	// they read was withdrawn by this vector's unrecorded_fields. Non-empty
	// exactly on ExemptionRestsOnWithdrawnCells.
	NotAsserted []string
}

// Grounded reports whether this exemption silences a violation the record shows.
func (g ExemptionGrounding) Grounded() bool { return g.Status == ExemptionGrounded }

// CheckExemptionGrounding re-runs every invariant this vector exempts against the
// schedule the capture recorded, and classifies each exemption.
//
// It is pure, offline and implementation-free: it reads the vector and nothing
// else. Admit turns a non-GROUNDED verdict into a refusal; Run counts the
// population it inspected so the report can state it (a check that stops checking
// says so, in writing).
func CheckExemptionGrounding(v *Vector) []ExemptionGrounding {
	if len(v.InvariantExemptions) == 0 {
		return nil
	}
	sched, ph, err := RecordedSchedule(v)
	out := make([]ExemptionGrounding, 0, len(v.InvariantExemptions))
	for _, ex := range v.InvariantExemptions {
		g := ExemptionGrounding{Invariant: ex.Invariant}
		switch {
		case !knownInvariant(ex.Invariant):
			g.Status = ExemptionUnknownInvariant
		case err != nil:
			g.Status = ExemptionScheduleUnreadable
			g.Detail = err.Error()
		default:
			res := runInvariant(ex.Invariant, v, sched, ph)
			g.Observed = res.Status
			g.Detail = res.Detail
			g.NotAsserted = res.NotAsserted
			switch res.Status {
			case InvariantViolated:
				g.Status = ExemptionGrounded
			case InvariantHold:
				g.Status = ExemptionDecoration
			default:
				if len(res.NotAsserted) > 0 {
					g.Status = ExemptionRestsOnWithdrawnCells
				} else {
					g.Status = ExemptionNotEvaluable
				}
			}
		}
		out = append(out, g)
	}
	return out
}

// admitExemptions is the admissibility half: the same two cheap checks admit.go
// always made, plus the grounding assertion above.
func admitExemptions(v *Vector) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	for _, ex := range v.InvariantExemptions {
		if !knownInvariant(ex.Invariant) {
			bad("invariant_exemptions names unknown invariant %q", ex.Invariant)
		}
		if strings.TrimSpace(ex.Reason) == "" {
			bad("invariant_exemptions for %q carries no reason", ex.Invariant)
		}
	}

	for _, g := range CheckExemptionGrounding(v) {
		if g.Grounded() {
			continue
		}
		switch g.Status {
		case ExemptionUnknownInvariant:
			// Already reported above, in its own precise words. Reporting it twice
			// would be a derived echo of one defect.
			continue

		case ExemptionDecoration:
			bad("invariant_exemptions switches off %q, BUT THAT INVARIANT HOLDS ON THE SCHEDULE THIS "+
				"VECTOR ITSELF RECORDED: %q. An exemption is admissible only where the REFERENCE ORACLE "+
				"GENUINELY VIOLATES the invariant and the port reproduces it; here the oracle's own "+
				"recorded output satisfies it, so this exemption silences NOTHING. What it does do is "+
				"raise the corpus's exempted count, which this program quotes as evidence about how much "+
				"of the corpus is checked — a count inflated by an exemption that excuses nothing is not "+
				"evidence (finding T220-N1, shape 1). T116 dropped exactly such an exemption "+
				"(balance_roll_forward on this family) BY HAND; this is that judgement made mechanical. "+
				"Delete the exemption: the invariant will hold, unexempted, and the report will say so",
				g.Invariant, g.Detail)

		case ExemptionRestsOnWithdrawnCells:
			bad("invariant_exemptions switches off %q, AND THIS VECTOR'S OWN unrecorded_fields WITHDRAW "+
				"EVERY CELL THAT INVARIANT READS, so it could not have been asserted here at all: %q. "+
				"That pairing removes the cells from the cell diff AND removes the invariant that would "+
				"have noticed, and it leaves the exemption's REASON — a sentence about what the oracle "+
				"does on this shape — resting on numbers this capture never recorded. The unmade "+
				"assertions are: %s. Either record the cells and let the invariant arbitrate, or drop the "+
				"exemption and let the harness report the assertion as NOT RUN, which is what it is "+
				"(finding T220-N1, shape 2: the dangerous pairing)",
				g.Invariant, g.Detail, strings.Join(g.NotAsserted, "; "))

		case ExemptionNotEvaluable:
			bad("invariant_exemptions switches off %q, but that invariant reports %q on the schedule this "+
				"vector recorded — it has nothing to assert here, so there is no violation for the "+
				"exemption to excuse. An exemption on an invariant that never fires is a count with no "+
				"check behind it (finding T220-N1). Delete it",
				g.Invariant, g.Detail)

		case ExemptionScheduleUnreadable:
			bad("invariant_exemptions switches off %q, and whether that exemption is grounded COULD NOT BE "+
				"DETERMINED: this vector's own expect.periods do not form a schedule (%s). An exemption "+
				"nothing could check is not an exemption that was checked",
				g.Invariant, g.Detail)

		default:
			bad("invariant_exemptions for %q has grounding status %q, which admitExemptions does not "+
				"classify. A verdict this function cannot name is a defect in this function, not a pass",
				g.Invariant, g.Status)
		}
	}
	return problems
}

// ExemptionCensus is WHAT THE GROUNDING CHECK INSPECTED on this run, printed by
// the report whether or not anything is wrong.
//
// P-22 and P-35: a guard that speaks only when it fires cannot be told apart from
// a guard that never ran, and this program has already found SIX guards that
// structurally could not fail. So the population is stated in the run output, in
// the shape guard_ledger_invariants uses — including the NIL-COVERAGE notice for
// the day the corpus carries no exemption at all and this check therefore
// inspects an empty population.
type ExemptionCensus struct {
	// VectorsInspected is every vector LOADED from the store, which is exactly
	// the population Admit runs over. Not "graded": an exemption is a property of
	// the file, so a refused or errored vector's exemption is still inspected.
	VectorsInspected int

	// VectorsExempting is how many of those declare at least one exemption.
	VectorsExempting int

	// Declared, Grounded and Ungrounded count exemption ENTRIES, not vectors.
	Declared   int
	Grounded   int
	Ungrounded int

	// UngroundedNames renders each ungrounded exemption as
	// "<case_id> — <invariant> [<status>]", so the report names them rather than
	// only counting them.
	UngroundedNames []string
}

// InspectExemptions builds the census over the loaded vectors.
func InspectExemptions(vectors []*Vector) ExemptionCensus {
	c := ExemptionCensus{VectorsInspected: len(vectors)}
	for _, v := range vectors {
		groundings := CheckExemptionGrounding(v)
		if len(groundings) == 0 {
			continue
		}
		c.VectorsExempting++
		for _, g := range groundings {
			c.Declared++
			if g.Grounded() {
				c.Grounded++
				continue
			}
			c.Ungrounded++
			c.UngroundedNames = append(c.UngroundedNames,
				fmt.Sprintf("%s — %s [%s]", v.CaseID, g.Invariant, g.Status))
		}
	}
	return c
}
