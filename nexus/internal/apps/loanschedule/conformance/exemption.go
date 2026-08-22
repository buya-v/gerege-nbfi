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
// That single positive assertion distinguishes four outcomes by name. THE
// CLASSIFIER ASKS "DID A CELL THE INVARIANT READS GO UNRECORDED?" BEFORE IT ASKS
// ANYTHING ELSE, and that order is the whole of finding T225-F1 (see below):
//
//   - VIOLATED -> GROUNDED. The record shows the violation the reason describes.
//     Admissible. A violation is a violation even if some OTHER assertion of the
//     same invariant went unmade, so GROUNDED may carry a non-empty NotAsserted.
//   - anything else, with at least one assertion NOT MADE because this vector's
//     own unrecorded_fields withdrew a cell the invariant reads ->
//     UNDETERMINED-ON-THE-RECORD. The record neither shows the violation nor
//     refutes it. REPORTED BY NAME, NOT REFUSED.
//   - HOLD, nothing withdrawn -> DECORATION. The invariant holds outright on the
//     oracle's own numbers, with no assertion withheld, so the exemption silences
//     nothing on the record and only moves a count. Refused.
//   - N/A, nothing withdrawn -> NOT-EVALUABLE. No periods at all (a
//     contract-refusal vector), or no observed total for splits_sum_to_whole to
//     sum to. There is no violation in the record either way, and no port can
//     make it evaluable because the missing term comes from the VECTOR. Refused.
//
// WHICH OUTCOMES ARE REFUSED IN Admit, AND WHY THE OTHER ONE IS NOT.
//
// Admit's own doctrine is that an INADMISSIBLE vector is one the harness cannot
// make a statement about the implementation from, and the precedent T222 invoked
// is finding T9-F1b (admitDivergentCell): a structural kill naming a cell the
// same vector withdrew from grading is INADMISSIBLE, not a warning — because the
// store may not RECORD A CLAIM THAT IS NOT EVIDENCE. That precedent stands, and
// it still settles DECORATION and NOT-EVALUABLE: both are the exemption's claim
// REFUTED BY THE VECTOR'S OWN RECORD, decidable OFFLINE from the file alone, with
// no implementation and no run — the signature of an admissibility question
// rather than a grading one.
//
// It does NOT reach UNDETERMINED-ON-THE-RECORD, and T222 extending it there was
// the defect T225 measured (F-1). Three reasons, in order of weight:
//
//  1. T9-F1b refuses a SELF-CONTRADICTION INSIDE ONE FILE: the same vector says
//     "this cell diverges" and "this cell was never observed". An exemption paired
//     with a withdrawal is not that. The exemption's claim is about the ORACLE'S
//     BEHAVIOUR; the withdrawal is about what the capture TRANSCRIBED. Both can be
//     true at once, and neither contradicts the other. "The record does not say"
//     is not "the record says no".
//
//  2. CONCLUDING "UNGROUNDED" FROM "UNOBSERVED" IS FINDING T58-N2, ONE LEVEL UP.
//     T58-N2's whole ruling is that a cell nobody observed must be DECLARED and
//     NOT ASSERTED UPON, in either direction — the false GREEN (an invariant
//     agreeing with the stand-in it was handed) and the false RED alike.
//     invariants.go now obeys that. The grounding check did not: it read
//     "no observation" and returned a verdict AGAINST the exemption.
//
//  3. THE REFUSAL HAD NO CORRECT REMEDY, and prescribed a false one. Grounding
//     judged RecordedSchedule + THIS VECTOR'S placeholders; the exemption ACTS at
//     grading time on the schedule THE IMPLEMENTATION RETURNED, and a real port
//     computes every cell and implements no PlaceholderReporter, so grading runs
//     with placeholders EMPTY (registry.go's PlaceholderCells doc, grade.go's
//     invariant call). MEASURED on a store copy of T116-G8-FAMB-N104 with one
//     repayment row's principal_minor withdrawn: grounding view N/A, PORT-MODE
//     view VIOLATED. So the refusal's own printed advice — "drop the exemption and
//     let the harness report the assertion as NOT RUN, which is what it is" — was
//     true only in self-test replay mode and FALSE in the mode that matters: the
//     port supplies the cell, the invariant fires, and the run goes red for a
//     divergence that is not one. A guard whose prescribed remedy breaks the mode
//     it exists to protect must not be an exit-2 refusal.
//
// WHAT IS NOT WEAKENED. T220-N1's actual complaint was that the exempted COUNT is
// quoted as evidence about how much of the corpus is checked and could be inflated
// by an exemption that silences nothing. That is still enforced, three ways:
// an undetermined exemption is NOT counted as GROUNDED (ExemptionCensus separates
// them); it is NAMED in the run output every run, with the withdrawn cells; and
// the corpus-wide count pin in exemption_test.go pins the undetermined count at 0,
// so the first one to arrive is a deliberate edit a reviewer sees in the same
// commit as the vector that brought it. The claim-needs-evidence half of T9-F1b is
// properly closed by T222's own follow-up F-4 (require a capture citation on an
// exemption's reason), which applies to ALL FOUR committed exemptions — whose
// reasons are uncited prose today — and not only to the ones a capture gap made
// uncheckable.
//
// And the consequence of leaving a REFUTED exemption in the report only is still
// the T164/A2-11 shape: a number a reader trusts, kept honest by prose. That is
// why DECORATION and NOT-EVALUABLE remain exit 2.
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

	// ExemptionUndetermined: at least one assertion the invariant would have made
	// could NOT be made, because this vector's own unrecorded_fields withdrew a
	// cell it reads. The record therefore neither shows the violation the reason
	// describes nor refutes it.
	//
	// THIS IS REPORTED, NOT REFUSED (finding T225-F1; it replaces T222's
	// RESTS-ON-WITHDRAWN-CELLS, which refused). It covers both the invariant that
	// lost EVERY assertion — T222's "dangerous pairing", the shape whose reason
	// rests on numbers nobody recorded — and the one that lost SOME, which T222
	// misclassified as a DECORATION because it branched on Status alone. Neither
	// is evidence against the exemption; both are the capture being silent. See
	// the doctrine block above for why the T9-F1b refusal precedent does not
	// reach this outcome, and for what enforces T220-N1 instead.
	ExemptionUndetermined ExemptionGroundingStatus = "UNDETERMINED-ON-THE-RECORD"

	// ExemptionNotEvaluable: the invariant reports N/A with NOTHING withdrawn —
	// no periods at all, or no observed total to sum to. No implementation can
	// make it evaluable, because the missing term comes from the vector.
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
	// they read was withdrawn by this vector's unrecorded_fields.
	//
	// EXACTLY, because T222 documented this wrongly and T225 measured a
	// DECORATION carrying a non-empty one (finding T225-F2):
	//
	//	ExemptionUndetermined      ALWAYS non-empty — it is the classifier's
	//	                           own entry condition.
	//	ExemptionGrounded          MAY be non-empty: a recorded violation on one
	//	                           row and a withdrawn cell on another.
	//	ExemptionDecoration        ALWAYS empty, because the classifier tests
	//	ExemptionNotEvaluable      NotAsserted BEFORE it tests Status.
	//	ExemptionUnknownInvariant  ALWAYS empty — the invariant is never run.
	//	ExemptionScheduleUnreadable
	NotAsserted []string
}

// Grounded reports whether this exemption silences a violation the record shows.
func (g ExemptionGrounding) Grounded() bool { return g.Status == ExemptionGrounded }

// Undetermined reports whether the record was SILENT about this exemption rather
// than supporting or refuting it. Such an exemption is reported, never refused.
func (g ExemptionGrounding) Undetermined() bool { return g.Status == ExemptionUndetermined }

// Inadmissible reports whether this verdict makes the whole vector INADMISSIBLE.
//
// It is phrased as the COMPLEMENT of the two admissible outcomes on purpose: a
// grounding status nobody has thought of yet is inadmissible by default and is
// then named by admitExemptions' default arm, rather than falling through some
// switch into a silent pass. A guard's unhandled case must be its loud case.
func (g ExemptionGrounding) Inadmissible() bool { return !g.Grounded() && !g.Undetermined() }

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
			// ORDER IS THE RULE (finding T225-F1). "The record could not say" is
			// tested BEFORE "the record said no", so a HOLD that withheld an
			// assertion is never mistaken for a HOLD that withheld none, and a
			// capture gap never produces a verdict AGAINST an exemption.
			switch {
			case res.Status == InvariantViolated:
				g.Status = ExemptionGrounded
			case len(res.NotAsserted) > 0:
				g.Status = ExemptionUndetermined
			case res.Status == InvariantHold:
				g.Status = ExemptionDecoration
			default:
				g.Status = ExemptionNotEvaluable
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

	problems = append(problems, refuseUngroundedExemptions(CheckExemptionGrounding(v))...)
	return problems
}

// refuseUngroundedExemptions renders the refusal for every grounding verdict that
// makes a vector inadmissible.
//
// It takes the verdicts rather than the vector so that the default arm below — a
// status this function does not classify — is reachable from a test. An arm no
// test can execute is an arm nobody knows the behaviour of (P-22), and T225-F5
// found this one and SCHEDULE-UNREADABLE both undriven.
func refuseUngroundedExemptions(groundings []ExemptionGrounding) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	for _, g := range groundings {
		if !g.Inadmissible() {
			// GROUNDED is admissible; UNDETERMINED-ON-THE-RECORD is admissible and
			// REPORTED — the census names it, with the withdrawn cells, on every
			// run. See the doctrine block at the top of this file for why it is not
			// a refusal (finding T225-F1).
			continue
		}
		switch g.Status {
		case ExemptionUnknownInvariant:
			// Already reported above, in its own precise words. Reporting it twice
			// would be a derived echo of one defect.
			continue

		case ExemptionDecoration:
			bad("invariant_exemptions switches off %q, BUT THAT INVARIANT HOLDS OUTRIGHT ON THE SCHEDULE "+
				"THIS VECTOR ITSELF RECORDED, with no assertion withheld: %q. An exemption is admissible "+
				"only where the REFERENCE ORACLE GENUINELY VIOLATES the invariant; THIS CHECK ASSERTS "+
				"THAT CONJUNCT AND ONLY THAT ONE, offline, against the record — whether the PORT "+
				"reproduces the oracle's behaviour is a grading-time question this refusal says nothing "+
				"about. On the oracle conjunct the record is unambiguous here: its own recorded output "+
				"satisfies the invariant, so this exemption silences NOTHING ON THE RECORD. What it does "+
				"do is raise the corpus's exempted count, which this program quotes as evidence about how "+
				"much of the corpus is checked — a count inflated by an exemption that excuses nothing is "+
				"not evidence (finding T220-N1, shape 1). T116 dropped exactly such an exemption "+
				"(balance_roll_forward on this family) BY HAND; this is that judgement made mechanical. "+
				"Delete the exemption. (If you believe the oracle DOES violate this invariant here and "+
				"the capture simply did not record the cells that show it, say so by naming those cells "+
				"in that period's unrecorded_fields: a withdrawn cell makes this verdict "+
				"UNDETERMINED-ON-THE-RECORD, which is reported rather than refused)",
				g.Invariant, g.Detail)

		case ExemptionNotEvaluable:
			bad("invariant_exemptions switches off %q, but that invariant reports %q on the schedule this "+
				"vector recorded — with NOTHING withdrawn, so this is the invariant having nothing to "+
				"assert here rather than the capture being silent. There is no violation for the "+
				"exemption to excuse and no implementation can produce one, because the missing term "+
				"comes from the VECTOR and not from the schedule under grading. An exemption on an "+
				"invariant that never fires is a count with no check behind it (finding T220-N1). Delete it",
				g.Invariant, g.Detail)

		case ExemptionScheduleUnreadable:
			bad("invariant_exemptions switches off %q, and whether that exemption is grounded COULD NOT BE "+
				"DETERMINED: this vector's own expect.periods do not form a schedule (%s). An exemption "+
				"nothing could check is not an exemption that was checked. This is NOT the capture being "+
				"silent about a cell — that is UNDETERMINED-ON-THE-RECORD and is reported, not refused — "+
				"it is the recorded rows failing to parse at all, which the replay implementation refuses "+
				"to build from as well",
				g.Invariant, g.Detail)

		default:
			bad("invariant_exemptions for %q has grounding status %q, which refuseUngroundedExemptions "+
				"does not classify. A verdict this function cannot name is a defect in this function, "+
				"not a pass",
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

	// Declared, Grounded, Undetermined and Ungrounded count exemption ENTRIES,
	// not vectors, and they PARTITION Declared exactly.
	//
	// UNDETERMINED IS COUNTED APART FROM GROUNDED DELIBERATELY (finding T225-F1).
	// It would have been one line cheaper to fold it into Grounded and let the
	// vector through silently, and that would have re-created the exact defect
	// T220-N1 raised: a "GROUNDED" figure quoted as evidence about how much of the
	// corpus is checked, inflated by exemptions nothing checked. An undetermined
	// exemption is admissible and is NOT evidence, so it gets its own number.
	Declared     int
	Grounded     int
	Undetermined int
	Ungrounded   int

	// UngroundedNames renders each INADMISSIBLE exemption as
	// "<case_id> — <invariant> [<status>]", so the report names them rather than
	// only counting them.
	UngroundedNames []string

	// UndeterminedExemptions carries the same rendering for each undetermined
	// exemption, plus the assertions the record could not make. The cells are
	// carried because "undetermined" without WHICH CELL is exactly the kind of
	// number a reader has to take on trust.
	UndeterminedExemptions []UndeterminedExemption
}

// UndeterminedExemption is one exemption the record was silent about.
type UndeterminedExemption struct {
	// Name is "<case_id> — <invariant> [UNDETERMINED-ON-THE-RECORD]".
	Name string

	// NotAsserted are the invariant's own sentences for the assertions it could
	// not make, each naming the row and the withdrawn cell.
	NotAsserted []string
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
			name := fmt.Sprintf("%s — %s [%s]", v.CaseID, g.Invariant, g.Status)
			switch {
			case g.Grounded():
				c.Grounded++
			case g.Undetermined():
				c.Undetermined++
				c.UndeterminedExemptions = append(c.UndeterminedExemptions,
					UndeterminedExemption{Name: name, NotAsserted: g.NotAsserted})
			default:
				c.Ungrounded++
				c.UngroundedNames = append(c.UngroundedNames, name)
			}
		}
	}
	return c
}
