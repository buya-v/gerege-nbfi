package conformance

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// FINDING T220-N1 — THE EXEMPTION MECHANISM HAD NO CORPUS-WIDE TRIPWIRE.
//
// The kill counts have corpus-wide tripwires (coverage_refusal_test.go). The
// EXEMPTION count did not, and admit.go asked an exemption only for a known
// invariant name and a non-empty reason — both satisfiable by prose. T220 raised
// it while APPROVING T116, and the reason it could still approve T116 is worth
// stating precisely: it proved that an exemption cannot hide a port divergence
// TODAY, and it proved that only because every cell the two committed exemptions
// read is a GRADED cell on those two vectors. A property of TODAY'S CORPUS is not
// a property of the mechanism.
//
// This file drives the mechanism, not the corpus. Every check below is DRIVEN RED
// on a deliberately-bad store copy first (P-22: a guard you have not seen fail is
// not a guard; this program has already found SIX guards that structurally could
// not fail), and the legitimate corpus is then shown GREEN.
//
// The pristine store is NEVER opened for writing: every fixture is built in a
// t.TempDir copy.

const (
	fambN104File = "T116-G8-FAMB-nonamortizing-mnt0pt01-104x600pct.json"
	fambN108File = "T116-G8-FAMB-nonamortizing-mnt0pt01-108x600pct.json"
	refuse01File = "REFUSE-01-actual-actual-ungraded.json"
)

// editVector decodes one vector file, hands the map to mutate, and writes it back.
//
// UseNumber throughout, and SetEscapeHTML(false): the store is MONEY, and a
// re-encoded amount that had gone through a float64 would be a non-negotiable
// violation even inside a temp directory. Every money cell in this store is a
// STRING anyway (MinorText), but the request block carries integers and the rule
// does not get to depend on that.
func editVector(t *testing.T, storeDir, name string, mutate func(t *testing.T, m map[string]any)) string {
	t.Helper()
	path := filepath.Join(storeDir, "loanschedule", name)
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile %s: %v", path, err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var m map[string]any
	if derr := dec.Decode(&m); derr != nil {
		t.Fatalf("decode %s: %v", path, derr)
	}
	mutate(t, m)
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	if eerr := enc.Encode(m); eerr != nil {
		t.Fatalf("encode %s: %v", path, eerr)
	}
	if werr := os.WriteFile(path, buf.Bytes(), 0o644); werr != nil {
		t.Fatalf("WriteFile %s: %v", path, werr)
	}
	if bytes.Equal(raw, buf.Bytes()) {
		t.Fatalf("the edit to %s changed NOTHING, so every assertion that depends on it is vacuous", name)
	}
	return path
}

// periodsOf returns the mutable expect.periods slice of a decoded vector.
func periodsOf(t *testing.T, m map[string]any) []any {
	t.Helper()
	expect, ok := m["expect"].(map[string]any)
	if !ok {
		t.Fatal("vector has no expect object")
	}
	periods, ok := expect["periods"].([]any)
	if !ok || len(periods) == 0 {
		t.Fatal("vector has no expect.periods, so a period-level fixture cannot be built")
	}
	return periods
}

// addExemption appends one exemption entry to a decoded vector.
func addExemption(t *testing.T, m map[string]any, invariant, reason string) {
	t.Helper()
	existing, _ := m["invariant_exemptions"].([]any)
	m["invariant_exemptions"] = append(existing, map[string]any{
		"invariant": invariant,
		"reason":    reason,
	})
}

// selfTestRun grades storeDir with the replay implementation built from the SAME
// directory, which is the hermetic mode the rest of this suite uses: no oracle,
// no port, and the implementation reproduces the store exactly, so any red is the
// harness's own verdict rather than a divergence.
func selfTestRun(t *testing.T, storeDir string) *Summary {
	t.Helper()
	impl, _, err := NewReplayImplementation(storeDir, "")
	if err != nil {
		t.Fatalf("NewReplayImplementation(%s): %v", storeDir, err)
	}
	return mustRun(t, Options{
		RepoRoot: repoRoot(t), StoreRoot: storeDir,
		Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
	})
}

// inadmissibleDetail returns the concatenated inadmissibility detail for one
// case_id, and fails if that vector was not declared INADMISSIBLE at all.
func inadmissibleDetail(t *testing.T, s *Summary, caseID string) string {
	t.Helper()
	for _, r := range s.Results {
		if r.CaseID != caseID {
			continue
		}
		if r.Outcome != OutcomeInadmissible {
			t.Fatalf("%s was %q, not INADMISSIBLE. THE GUARD DID NOT FIRE.\n%s",
				caseID, r.Outcome, render(s))
		}
		return strings.Join(r.Detail, "\n")
	}
	t.Fatalf("no result for %s at all\n%s", caseID, render(s))
	return ""
}

// TestExemptionMustBeGroundedInARecordedViolation is the mechanism guard.
//
// THE RULE, POSITIVELY (P-35): an exempted invariant, re-run against the schedule
// ITS OWN VECTOR RECORDED and honouring that vector's unrecorded_fields, is
// admissible when it comes back VIOLATED there, and INADMISSIBLE when the record
// REFUTES it — HOLD outright, or nothing to assert at all. Not "the reason does
// not contain a weasel word" — the property the report already claims for every
// exemption, asserted.
//
// AND WHEN THE RECORD IS SILENT — a cell the invariant reads was withdrawn by
// this vector's own unrecorded_fields — THE VERDICT IS
// UNDETERMINED-ON-THE-RECORD, WHICH IS REPORTED AND ADMITTED. T222 refused that
// case too; finding T225-F1 measured what it cost, and exemption.go's doctrine
// block carries the argument. "The record does not say" is not "the record says
// no", and concluding otherwise is finding T58-N2 one level up.
//
// DRIVEN RED. Each REFUSAL subtest below builds a store copy that is admissible on
// pre-T222 bytes and shows the run refusing it here. Measured on the PRE-T222
// bytes (the admit.go loop that checked only the invariant name and a non-empty
// reason), every fixture below graded clean:
//
//	decoration        T116-G8-FAMB-N104 outcome PASS; parity 46 PASS 0 FAIL,
//	                  contract-refusal 4, inadmissible 0, 7884 graded cells,
//	                  "invariant assertions 5 EXEMPTED BY A VECTOR",
//	                  VERDICT: SELF-TEST PASS (exit 0)
//	withdrawn cells   T116-G8-FAMB-N104 outcome PASS; parity 46 PASS 0 FAIL,
//	                  inadmissible 0, 7883 graded / 94 ungraded cells,
//	                  "4 EXEMPTED", VERDICT: SELF-TEST PASS (exit 0)
//	no schedule       REFUSE-01-actual-actual-ungraded outcome PASS;
//	                  contract-refusal 4 PASS, inadmissible 0, 7884 graded cells,
//	                  "4 EXEMPTED", VERDICT: SELF-TEST PASS (exit 0)
//
// — that is, the corpus's own headline numbers absorbed all three without a word,
// and in the withdrawn-cells case the ONLY trace anywhere in the output was one
// extra ungraded cell [VERIFIED: T222's transcripts, reproduced independently by
// T225 item 6 to the cell]. The withdrawn-cells row is why that case is now
// REPORTED rather than admitted silently: it must leave a mark in the output, and
// the subtest below fails if it does not.
func TestExemptionMustBeGroundedInARecordedViolation(t *testing.T) {
	pristine := storeRoot(t)

	// ANTI-VACUITY, FIRST AND UNCONDITIONALLY (P-64). Every refusal below would
	// look identical if the new check simply refused everything, and it would look
	// identical again if the committed corpus carried no exemption for it to
	// inspect. So: the committed store's exemptions exist, and every one of them
	// is GROUNDED.
	t.Run("the_committed_store_is_grounded_and_the_population_is_not_empty", func(t *testing.T) {
		vectors, loadErrs, err := LoadStore(pristine, "")
		if err != nil || len(loadErrs) != 0 {
			t.Fatalf("LoadStore(pristine): %v / %v", err, loadErrs)
		}
		c := InspectExemptions(vectors)
		if c.Declared == 0 {
			t.Fatal("the committed store declares ZERO exemptions, so this whole test inspects an empty " +
				"population and every assertion in it is vacuous")
		}
		if c.Ungrounded != 0 {
			t.Fatalf("the committed store carries %d UNGROUNDED exemption(s): %v",
				c.Ungrounded, c.UngroundedNames)
		}
		if c.Grounded != c.Declared {
			t.Fatalf("grounded %d != declared %d", c.Grounded, c.Declared)
		}
		t.Logf("inspected %d loaded vectors, %d exempting, %d exemptions, all GROUNDED",
			c.VectorsInspected, c.VectorsExempting, c.Declared)
	})

	// SHAPE 1 — THE DECORATION. An exemption on an invariant that would have held
	// anyway. This is not a hypothetical shape: T116 PROPOSED exactly this
	// exemption (balance_roll_forward on the family-B vectors) and dropped it BY
	// HAND after checking that the invariant holds unexempted. Nothing enforced
	// that judgement afterwards. This subtest is that judgement, mechanised.
	t.Run("RED_decoration_an_exemption_on_an_invariant_that_holds", func(t *testing.T) {
		store := copyStore(t, pristine)
		editVector(t, store, fambN104File, func(t *testing.T, m map[string]any) {
			addExemption(t, m, InvBalanceRollForward,
				"T222 fixture: prose that reads exactly like the two real exemptions beside it, on an "+
					"invariant that holds unexempted. This is the shape T116 dropped by hand.")
		})

		// The fixture must be otherwise well-formed, or the refusal below could be
		// any other admissibility defect wearing this test's name.
		vectors, loadErrs, lerr := LoadStore(store, "")
		if lerr != nil || len(loadErrs) != 0 {
			t.Fatalf("the fixture store does not even load: %v / %v", lerr, loadErrs)
		}
		c := InspectExemptions(vectors)
		if c.Declared != 5 {
			t.Fatalf("the fixture was meant to raise the declared exemptions to 5; it reads %d", c.Declared)
		}

		s := selfTestRun(t, store)
		detail := inadmissibleDetail(t, s, "T116-G8-FAMB-N104")
		for _, want := range []string{
			"HOLDS OUTRIGHT ON THE SCHEDULE THIS VECTOR ITSELF RECORDED",
			// "with no assertion withheld" is the half T225-F2 found missing: a
			// PARTIAL hold used to reach this same refusal, and the refusal then
			// described a schedule the invariant had not fully read.
			"with no assertion withheld",
			InvBalanceRollForward,
			"silences NOTHING",
		} {
			if !strings.Contains(detail, want) {
				t.Errorf("the refusal must say %q; it said:\n%s", want, detail)
			}
		}
		// The refusal must not be silent about WHY the invariant held: the
		// invariant's own sentence is quoted, so a reader can act without opening
		// the vector.
		if !strings.Contains(detail, "every outstanding balance asserted follows from the previous row") {
			t.Errorf("the refusal does not quote the invariant's own verdict:\n%s", detail)
		}
		if s.ExitCode() != 2 {
			t.Errorf("an inadmissible vector is exit 2; got %d", s.ExitCode())
		}
		// AND THE RUN MUST SAY SO IN THE REPORT, by name. A refusal a reader
		// cannot find in the output is the T164/A2-11 shape.
		out := render(s)
		if !strings.Contains(out, "UNGROUNDED: T116-G8-FAMB-N104 — "+InvBalanceRollForward+" [DECORATION]") {
			t.Errorf("the report does not name the decoration:\n%s", grepLines(out, "UNGROUNDED"))
		}
		t.Logf("refused: %s", firstLine(detail))
	})

	// SHAPE 2 — THE WITHDRAWN-CELLS PAIRING: REPORTED BY NAME, NOT REFUSED.
	//
	// T222 shipped this as an exit-2 refusal and T225's F-1 measured what that
	// costs: the SAME classification fires on an ordinary capture gap and takes a
	// legitimate vector, its cells and its named money kills out of the corpus.
	// The rule now separates "the record refutes the exemption" (DECORATION,
	// NOT-EVALUABLE — still refused) from "the record cannot say"
	// (UNDETERMINED-ON-THE-RECORD — admitted and named). See exemption.go's
	// doctrine block for the argument against extending T9-F1b here.
	//
	// DRIVEN RED, in the direction that is left: the CENSUS must move and the
	// report must NAME it. Before this classification existed, the whole trace of
	// this pairing in the run output was one extra ungraded cell, 93 -> 94
	// [VERIFIED: T222's own pre-bytes measurement, reproduced by T225 item 6].
	// The subtest fails if the pairing is silently folded into GROUNDED — which is
	// the one-line shortcut that would have re-created finding T220-N1.
	t.Run("REPORTED_the_withdrawn_cells_pairing_is_named_not_refused", func(t *testing.T) {
		store := copyStore(t, pristine)
		editVector(t, store, fambN104File, func(t *testing.T, m map[string]any) {
			periods := periodsOf(t, m)
			last, ok := periods[len(periods)-1].(map[string]any)
			if !ok {
				t.Fatal("the final period is not an object")
			}
			// "Marked unrecorded means EMPTY" (finding T9-F1a), so the cell is
			// blanked as well as withdrawn — otherwise admitPeriods refuses the
			// fixture for a different reason and this test proves nothing.
			last["unrecorded_fields"] = []any{"outstanding_principal_minor"}
			last["outstanding_principal_minor"] = ""
			last["outstanding_principal_major_text"] = ""
		})

		vectors, loadErrs, lerr := LoadStore(store, "")
		if lerr != nil || len(loadErrs) != 0 {
			t.Fatalf("the fixture store does not even load: %v / %v", lerr, loadErrs)
		}
		// The fixture withdraws a cell; it adds no exemption. The exemption it
		// makes undetermined is one T116 committed.
		c := InspectExemptions(vectors)
		if c.Declared != 4 {
			t.Fatalf("the fixture must not change the number of exemptions; declared %d", c.Declared)
		}
		if c.Undetermined != 1 {
			t.Fatalf("expected exactly 1 UNDETERMINED exemption, got %d (grounded %d, ungrounded %d %v). "+
				"If this reads 0 with grounded 4, the undetermined case has been folded back into "+
				"GROUNDED and the exempted-count evidence is inflated again (finding T220-N1)",
				c.Undetermined, c.Grounded, c.Ungrounded, c.UngroundedNames)
		}
		if c.Ungrounded != 0 {
			t.Fatalf("a capture gap must not make a vector inadmissible (finding T225-F1); ungrounded %d: %v",
				c.Ungrounded, c.UngroundedNames)
		}
		if c.Grounded+c.Undetermined+c.Ungrounded != c.Declared {
			t.Fatalf("the census does not partition the declarations: %d + %d + %d != %d",
				c.Grounded, c.Undetermined, c.Ungrounded, c.Declared)
		}

		s := selfTestRun(t, store)
		// ADMITTED. The vector keeps grading, and the run stays green.
		for _, r := range s.Results {
			if r.CaseID != "T116-G8-FAMB-N104" {
				continue
			}
			if r.Outcome != OutcomePass {
				t.Fatalf("the pairing made the vector %q; it must be admitted and reported\n%s",
					r.Outcome, strings.Join(r.Detail, "\n"))
			}
			if r.GradedCells == 0 {
				t.Errorf("the vector contributed 0 graded cells, so it was admitted in name only")
			}
		}
		if s.Inadmissible != 0 || s.ExitCode() != 0 {
			t.Fatalf("inadmissible %d, exit %d; want 0 and 0\n%s", s.Inadmissible, s.ExitCode(), render(s))
		}
		// NAMED. A guard that admits silently is not a guard.
		out := render(s)
		for _, want := range []string{
			"UNDETERMINED: T116-G8-FAMB-N104 — " + InvPrincipalAmortizes + " [UNDETERMINED-ON-THE-RECORD]",
			"THE RECORD COULD NOT SAY:",
			"outstanding_principal_minor",
			"3 GROUNDED (the recorded schedule VIOLATES the exempted invariant), 0 UNGROUNDED.",
			"1 UNDETERMINED-ON-THE-RECORD",
		} {
			if !strings.Contains(out, want) {
				t.Errorf("the report must say %q; the section reads:\n%s",
					want, grepLines(out, "GROUNDED")+"\n"+grepLines(out, "COULD NOT SAY"))
			}
		}
		// And it must NOT reclassify the OTHER exemption of the same vector, whose
		// cells are all still recorded and which is genuinely grounded.
		if strings.Contains(out, "UNDETERMINED: T116-G8-FAMB-N104 — "+InvPrincipalSum) {
			t.Errorf("%s was also called undetermined; its cells are all recorded:\n%s",
				InvPrincipalSum, grepLines(out, "UNDETERMINED"))
		}
		t.Logf("admitted and named: %s", grepLines(out, "UNDETERMINED"))
	})

	// FINDING T225-F1, THE ACCEPTANCE TEST. This is the vector T222's rule refused
	// and the reason this task exists, built from T225's probe fixture verbatim:
	// an ordinary capture gap — ONE repayment row's principal_minor never recorded
	// — on a vector whose exemption is committed, load-bearing and GROUNDED today.
	//
	// The two views of the same schedule disagree, which is the whole defect:
	//
	//	GROUNDING VIEW (recorded schedule + THIS VECTOR'S placeholders)  N/A
	//	PORT-MODE VIEW (same schedule, placeholders EMPTY)               VIOLATED
	//
	// A real port computes every cell and implements no PlaceholderReporter, so
	// grading runs the port-mode view — where the exemption is the ONLY thing
	// standing between this vector and a false RED. T222 refused it on the
	// grounding view and printed a remedy ("drop the exemption and let the harness
	// report the assertion as NOT RUN") that is false in exactly the mode that
	// matters. Both halves are asserted below.
	t.Run("T225_F1_a_capture_gap_under_a_grounded_exemption_is_ADMITTED", func(t *testing.T) {
		store := copyStore(t, pristine)
		editVector(t, store, fambN104File, func(t *testing.T, m map[string]any) {
			row, ok := periodsOf(t, m)[5].(map[string]any)
			if !ok || row["kind"] != "REPAYMENT" {
				t.Fatalf("period 5 is not a REPAYMENT row: %v", periodsOf(t, m)[5])
			}
			// "Marked unrecorded means EMPTY" (finding T9-F1a).
			row["unrecorded_fields"] = []any{"principal_minor"}
			row["principal_minor"] = ""
			row["principal_major_text"] = ""
		})

		vectors, loadErrs, lerr := LoadStore(store, "")
		if lerr != nil || len(loadErrs) != 0 {
			t.Fatalf("the fixture store does not even load: %v / %v", lerr, loadErrs)
		}
		var target *Vector
		for _, v := range vectors {
			if v.CaseID == "T116-G8-FAMB-N104" {
				target = v
			}
		}
		if target == nil {
			t.Fatal("fixture vector missing")
		}
		sched, ph, rerr := RecordedSchedule(target)
		if rerr != nil {
			t.Fatalf("RecordedSchedule: %v", rerr)
		}
		withPH := runInvariant(InvPrincipalSum, target, sched, ph)
		noPH := runInvariant(InvPrincipalSum, target, sched, PlaceholderCells{})
		t.Logf("GROUNDING VIEW (recorded schedule + this vector's placeholders): %s — %s",
			withPH.Status, firstLine(withPH.Detail))
		t.Logf("PORT-MODE VIEW (same schedule, placeholders empty):              %s — %s",
			noPH.Status, firstLine(noPH.Detail))
		// THE FIXTURE'S OWN ANTI-VACUITY. If the two views ever agree, this
		// subtest is asserting nothing about the defect it is named for.
		if withPH.Status == noPH.Status {
			t.Fatalf("the two views agree (%s), so this fixture no longer exhibits T225-F1", withPH.Status)
		}
		if noPH.Status != InvariantViolated {
			t.Fatalf("port-mode view is %s, want VIOLATED — the exemption would not be load-bearing "+
				"and the refusal would have cost nothing", noPH.Status)
		}

		// THE ACCEPTANCE. The whole run is clean: the vector is admitted, it still
		// grades its cells, the corpus is whole and the exit code is 0.
		s := selfTestRun(t, store)
		if s.Inadmissible != 0 {
			t.Fatalf("the capture gap made %d vector(s) INADMISSIBLE. THE T225-F1 REGRESSION IS BACK.\n%s",
				s.Inadmissible, render(s))
		}
		if s.ExitCode() != 0 {
			t.Fatalf("exit %d, want 0\n%s", s.ExitCode(), render(s))
		}
		if s.ParityPass != 46 {
			t.Errorf("parity vectors PASS %d, want 46 — the vector was dropped from the corpus",
				s.ParityPass)
		}
		if s.InvariantViolations != 0 {
			t.Errorf("invariant violations %d, want 0 — the exemption must still silence the one it "+
				"is grounded in", s.InvariantViolations)
		}
		for _, r := range s.Results {
			if r.CaseID == "T116-G8-FAMB-N104" {
				t.Logf("N104: outcome=%s graded=%d ungraded=%d", r.Outcome, r.GradedCells, r.UngradedCells)
				if r.Outcome != OutcomePass || r.GradedCells == 0 {
					t.Errorf("the vector must keep grading; outcome %s, %d graded cells",
						r.Outcome, r.GradedCells)
				}
			}
		}
		// AND IT IS REPORTED, not admitted silently.
		out := render(s)
		if !strings.Contains(out,
			"UNDETERMINED: T116-G8-FAMB-N104 — "+InvPrincipalSum+" [UNDETERMINED-ON-THE-RECORD]") {
			t.Errorf("the report does not name the undetermined exemption:\n%s",
				grepLines(out, "UNDETERMINED"))
		}
		// THE FALSE REMEDY IS GONE. Nothing in the run may tell an author that
		// dropping this exemption yields NOT RUN; in port mode it yields VIOLATED.
		if strings.Contains(out, "let the harness report the assertion as NOT RUN, which is what it is") {
			t.Errorf("the run still prints T222's false remedy:\n%s", grepLines(out, "NOT RUN, which is"))
		}
	})

	// FINDING T225-F2. A PARTIAL hold — the invariant held on every assertion it
	// could make, and one it could not — was classified DECORATION and refused,
	// while T222's own honesty note said such a case was "still GROUNDED and is
	// not reported". Both halves were wrong. It is UNDETERMINED-ON-THE-RECORD.
	t.Run("T225_F2_a_partial_hold_is_UNDETERMINED_not_a_decoration", func(t *testing.T) {
		store := copyStore(t, pristine)
		editVector(t, store, fambN108File, func(t *testing.T, m map[string]any) {
			row, ok := periodsOf(t, m)[5].(map[string]any)
			if !ok {
				t.Fatal("period 5 is not an object")
			}
			row["unrecorded_fields"] = []any{"principal_minor"}
			row["principal_minor"] = ""
			row["principal_major_text"] = ""
			addExemption(t, m, InvBalanceRollForward,
				"T230 fixture (from T225's probe): an exemption on an invariant that only PARTIALLY held "+
					"on the record, because one row's principal was never captured.")
		})
		vectors, loadErrs, lerr := LoadStore(store, "")
		if lerr != nil || len(loadErrs) != 0 {
			t.Fatalf("the fixture store does not even load: %v / %v", lerr, loadErrs)
		}
		var seen bool
		for _, v := range vectors {
			if v.CaseID != "T116-G8-FAMB-N108" {
				continue
			}
			sched, ph, _ := RecordedSchedule(v)
			res := runInvariant(InvBalanceRollForward, v, sched, ph)
			if res.Status != InvariantHold || len(res.NotAsserted) == 0 {
				t.Fatalf("the fixture did not produce a PARTIAL hold (status %s, %d unmade assertions), "+
					"so this subtest proves nothing", res.Status, len(res.NotAsserted))
			}
			for _, g := range CheckExemptionGrounding(v) {
				if g.Invariant != InvBalanceRollForward {
					continue
				}
				seen = true
				t.Logf("balance_roll_forward on the record: %s with %d assertion(s) NOT MADE -> %s",
					res.Status, len(res.NotAsserted), g.Status)
				if g.Status != ExemptionUndetermined {
					t.Errorf("a partial hold classified %s; want %s", g.Status, ExemptionUndetermined)
				}
			}
		}
		if !seen {
			t.Fatal("the fixture's exemption was never classified, so this subtest is vacuous")
		}
		s := selfTestRun(t, store)
		if s.Inadmissible != 0 || s.ExitCode() != 0 {
			t.Fatalf("a partial hold must not refuse the vector; inadmissible %d exit %d\n%s",
				s.Inadmissible, s.ExitCode(), render(s))
		}
		// T222's DECORATION refusal predicted "the invariant will hold, unexempted,
		// and the report will say so" on a schedule where it did NOT fully hold.
		// That prediction must not be reachable from a partial hold any more.
		if strings.Contains(render(s), "the invariant will hold, unexempted") {
			t.Errorf("the run still predicts an unexempted hold on a partially-withheld invariant")
		}
	})

	// SHAPE 3 — AN EXEMPTION WITH NO SCHEDULE UNDER IT. A contract-refusal vector
	// has no periods at all, so every invariant reports N/A there and an exemption
	// on one excuses nothing. It is the limiting case of the decoration.
	t.Run("RED_an_exemption_on_a_vector_with_no_schedule", func(t *testing.T) {
		store := copyStore(t, pristine)
		editVector(t, store, refuse01File, func(t *testing.T, m map[string]any) {
			addExemption(t, m, InvPrincipalAmortizes,
				"T222 fixture: an exemption on a vector that has no schedule to violate anything.")
		})
		s := selfTestRun(t, store)
		detail := inadmissibleDetail(t, s, "REFUSE-01-actual-actual-ungraded")
		for _, want := range []string{"no periods", "nothing to assert here", InvPrincipalAmortizes} {
			if !strings.Contains(detail, want) {
				t.Errorf("the refusal must say %q; it said:\n%s", want, detail)
			}
		}
		out := render(s)
		if !strings.Contains(out, "UNGROUNDED: REFUSE-01-actual-actual-ungraded — "+InvPrincipalAmortizes+" [NOT-EVALUABLE]") {
			t.Errorf("the report does not name it:\n%s", grepLines(out, "UNGROUNDED"))
		}
		t.Logf("refused: %s", firstLine(detail))
	})

	// GREEN. The legitimate corpus is unmoved by all of the above: same parity
	// count, same exemption count, nothing inadmissible, and the census says so.
	t.Run("GREEN_the_committed_corpus_is_unmoved", func(t *testing.T) {
		s := selfTestRun(t, pristine)
		if s.Inadmissible != 0 {
			t.Fatalf("the new check refuses %d committed vector(s):\n%s", s.Inadmissible, render(s))
		}
		if s.ExemptionCensus.Ungrounded != 0 {
			t.Fatalf("committed store reports ungrounded exemptions %v", s.ExemptionCensus.UngroundedNames)
		}
		if s.ExemptionCensus.Undetermined != 0 {
			t.Fatalf("committed store reports undetermined exemptions %v",
				s.ExemptionCensus.UndeterminedExemptions)
		}
		out := render(s)
		for _, want := range []string{
			"4 GROUNDED (the recorded schedule VIOLATES the exempted invariant), 0 UNGROUNDED.",
			"0 UNDETERMINED-ON-THE-RECORD",
		} {
			if !strings.Contains(out, want) {
				t.Errorf("the report does not state %q:\n%s", want, grepLines(out, "GROUNDED"))
			}
		}
	})
}

// TestExemptionGroundingStatesItsPopulation is the P-22/P-35 half: the check must
// say what it inspected, every run, and must say NIL-COVERAGE on the day it
// inspects nothing — in the shape guard_ledger_invariants uses.
//
// DRIVEN RED on the pre-T222 bytes trivially: no line of the report mentioned the
// exemption-grounding population at all, in any run, because the check did not
// exist. The assertion that carries real weight is the SECOND one: a corpus with
// no exemptions must not read like a corpus whose exemptions were all checked.
func TestExemptionGroundingStatesItsPopulation(t *testing.T) {
	pristine := storeRoot(t)

	t.Run("a_populated_corpus_states_the_population_it_inspected", func(t *testing.T) {
		out := render(selfTestRun(t, pristine))
		want := "INSPECTED 51 loaded vector(s); 2 of them exempt at least one invariant; " +
			"4 exemption declaration(s) examined."
		if !strings.Contains(out, want) {
			t.Errorf("the report must state the inspected population as %q; the section reads:\n%s",
				want, grepLines(out, "INSPECTED"))
		}
		if strings.Contains(out, "NIL-COVERAGE — no vector in this store exempts") {
			t.Errorf("a corpus with 4 exemptions printed the NIL-COVERAGE notice:\n%s",
				grepLines(out, "NIL-COVERAGE"))
		}
	})

	// THE EMPTY POPULATION. Strip both family-B vectors' exemptions and the check
	// has nothing to inspect. It must SAY so rather than print a clean-looking
	// zero — that is the whole NIL-COVERAGE idiom.
	//
	// It also proves the exemptions are LOAD-BEARING rather than decorative on the
	// committed corpus, which is the same claim shape 1 above refuses to let rot:
	// with them removed the run reports FOUR invariant violations and exit 1.
	t.Run("NIL_COVERAGE_when_no_vector_exempts_anything", func(t *testing.T) {
		store := copyStore(t, pristine)
		for _, name := range []string{fambN104File, fambN108File} {
			editVector(t, store, name, func(t *testing.T, m map[string]any) {
				m["invariant_exemptions"] = []any{}
			})
		}
		vectors, _, lerr := LoadStore(store, "")
		if lerr != nil {
			t.Fatalf("LoadStore: %v", lerr)
		}
		if c := InspectExemptions(vectors); c.Declared != 0 {
			t.Fatalf("the fixture still declares %d exemption(s)", c.Declared)
		}
		s := selfTestRun(t, store)
		out := render(s)
		if !strings.Contains(out, "NIL-COVERAGE — no vector in this store exempts any invariant, so the "+
			"exemption-grounding") {
			t.Errorf("an empty population did not produce the NIL-COVERAGE notice:\n%s",
				grepLines(out, "EXEMPTION GROUNDING"))
		}
		if !strings.Contains(out, "It inspected 51 loaded vector(s) to find that out.") {
			t.Errorf("the NIL-COVERAGE notice does not say how many vectors it opened to find out:\n%s",
				grepLines(out, "NIL-COVERAGE"))
		}
		// The load-bearing half: those four exemptions were silencing four real
		// violations, so removing them turns the run red. If this ever reads 0 the
		// committed exemptions have become decorations and shape 1 above should
		// have caught it.
		if s.InvariantViolations != 4 {
			t.Errorf("removing the 4 committed exemptions produced %d invariant violations, want 4: "+
				"an exemption that silences nothing is a decoration\n%s",
				s.InvariantViolations, grepLines(out, "invariant violations"))
		}
		if s.InvariantsExempted != 0 {
			t.Errorf("exempted count with no exemptions declared: got %d, want 0", s.InvariantsExempted)
		}
	})
}

// TestExemptionCountIsPinnedCorpusWide IS THE TRIPWIRE T220 ASKED FOR, and it is
// the cheap half of this task: one number, pinned, beside the kill counts.
//
// TODAY'S TRUTH, MEASURED IN THE LIVE ARTEFACT AND NOT INHERITED (P-63, P-69 — a
// measured claim has a shelf life shorter than one fire): 4 invariant assertions
// EXEMPTED BY A VECTOR, on 46 parity vectors, two exemptions each on the two T116
// family-B vectors. Re-derived here from the run rather than quoted from a
// handoff, and re-derived again from the store by a second route
// (InspectExemptions) so that a defect in the grading loop cannot move both.
//
// WHY A TEST AND NOT A HARD CAP IN THE BINARY. A cap inside Run would refuse
// legitimate corpus growth at RUN time, in a fire that has nothing to do with
// exemptions, and the fix would be to edit the cap under pressure. The kill
// counts are pinned in the test suite for the same reason (coverage_refusal_test)
// and the precedent is worth more than the marginal coverage: moving this number
// must be a deliberate edit a reviewer sees, in the same commit as the vector
// that moved it. What DOES gate the verdict is the grounding refusal above, which
// is in Admit and is exit 2.
//
// DRIVEN RED IN BOTH DIRECTIONS, because a tripwire that only fires on growth is
// half a tripwire: a vector edit that silently DROPS an exemption changes what the
// corpus checks just as much.
func TestExemptionCountIsPinnedCorpusWide(t *testing.T) {
	pristine := storeRoot(t)

	// THE PIN.
	s := selfTestRun(t, pristine)
	if s.InvariantsExempted != 4 {
		t.Errorf("INVARIANT ASSERTIONS EXEMPTED BY A VECTOR: got %d, want 4. This is a corpus-wide "+
			"tripwire (finding T220-N1). If a promotion legitimately moved it, move this number, the "+
			"census assertion below and the handoff's measured figure TOGETHER, and say in the commit "+
			"which vector exempts what and why the oracle violates it there.\n%s",
			s.InvariantsExempted, grepLines(render(s), "EXEMPTED"))
	}
	if s.ParityPass != 46 {
		t.Errorf("the exemption pin above is quoted as \"4 on 46 parity vectors\"; parity vectors read %d",
			s.ParityPass)
	}
	// The second route: counted from the STORE, not from the grading loop.
	vectors, loadErrs, err := LoadStore(pristine, "")
	if err != nil || len(loadErrs) != 0 {
		t.Fatalf("LoadStore(pristine): %v / %v", err, loadErrs)
	}
	c := InspectExemptions(vectors)
	if c.Declared != 4 || c.Grounded != 4 || c.VectorsExempting != 2 {
		t.Errorf("store census: %d declared / %d grounded / %d vectors exempting, want 4 / 4 / 2",
			c.Declared, c.Grounded, c.VectorsExempting)
	}
	// THE UNDETERMINED COUNT IS PINNED AT ZERO, for the same reason the exempted
	// count is pinned at 4 (finding T225-F1). UNDETERMINED-ON-THE-RECORD is
	// ADMITTED rather than refused, so nothing at RUN time stops the first one
	// arriving — this is the tripwire that makes its arrival a deliberate edit a
	// reviewer sees, in the same commit as the vector that brought it. An
	// undetermined exemption is not evidence: it is a check the corpus declares
	// switched off over a violation the capture never recorded.
	if c.Undetermined != 0 {
		t.Errorf("UNDETERMINED exemptions: got %d, want 0: %v. If a promotion legitimately brought one, "+
			"move this number and say in the commit which cell the capture could not record, why it "+
			"could not, and what still holds the exemption honest without it",
			c.Undetermined, c.UndeterminedExemptions)
	}
	if c.Grounded+c.Undetermined+c.Ungrounded != c.Declared {
		t.Errorf("the census does not partition the declarations: %d + %d + %d != %d",
			c.Grounded, c.Undetermined, c.Ungrounded, c.Declared)
	}
	// The two counts answer different questions over different populations
	// (graded vs loaded) and happen to agree today. Assert the agreement rather
	// than assume it: they diverge the moment an exempting vector is refused or
	// errors, and a reader of the report needs to know which number moved.
	if s.InvariantsExempted != c.Declared {
		t.Errorf("the run exercised %d exemptions but the store declares %d: a declared exemption that "+
			"is never exercised is invisible in the summary line", s.InvariantsExempted, c.Declared)
	}

	// RED, DOWNWARD: a vector edit that silently drops an exemption.
	t.Run("RED_the_pin_fires_when_an_exemption_is_dropped", func(t *testing.T) {
		store := copyStore(t, pristine)
		editVector(t, store, fambN104File, func(t *testing.T, m map[string]any) {
			ex, ok := m["invariant_exemptions"].([]any)
			if !ok || len(ex) != 2 {
				t.Fatalf("%s no longer carries 2 exemptions; this fixture would be vacuous", fambN104File)
			}
			m["invariant_exemptions"] = ex[:1]
		})
		got := selfTestRun(t, store)
		if got.InvariantsExempted != 3 {
			t.Fatalf("dropping one exemption should read 3; got %d", got.InvariantsExempted)
		}
		if got.InvariantsExempted == 4 {
			t.Fatal("THE PIN CANNOT FIRE DOWNWARD")
		}
		// And the run goes RED, because the dropped exemption was silencing a real
		// violation. That is the pin's whole point: the count is not decoration.
		if got.InvariantViolations != 1 {
			t.Errorf("dropping a GROUNDED exemption must surface the violation it silenced; "+
				"invariant violations read %d", got.InvariantViolations)
		}
		t.Logf("count moved 4 -> %d, invariant violations %d", got.InvariantsExempted, got.InvariantViolations)
	})

	// RED, UPWARD, AND THROUGH THE ONE DOOR THE GROUNDING CHECK LEAVES OPEN.
	//
	// With the grounding refusal in place a DECORATION can no longer inflate the
	// count — it is inadmissible. The remaining way the count can grow is a
	// GENUINELY GROUNDED exemption, which is exactly the event that should force a
	// human to look. So the fixture manufactures one honestly: break the
	// contiguity of one repayment window in a store copy, so that
	// monotonic_due_dates is REALLY violated on that vector's own recorded
	// schedule, and exempt it. The exemption is grounded, the vector is
	// admissible, the run is green — and the count moves to 5, which is the only
	// thing left to notice it.
	t.Run("RED_the_pin_fires_when_a_grounded_exemption_is_added", func(t *testing.T) {
		store := copyStore(t, pristine)
		editVector(t, store, fambN108File, func(t *testing.T, m map[string]any) {
			periods := periodsOf(t, m)
			row, ok := periods[3].(map[string]any)
			if !ok || row["kind"] != "REPAYMENT" {
				t.Fatalf("period 3 is not a REPAYMENT row: %v", periods[3])
			}
			// One day later than the previous row's due date: the window is still
			// well-formed (from < due), so the ONLY thing this breaks is
			// contiguity — [from, due) windows that leave a day accruing nowhere.
			row["from_date"] = map[string]any{
				"year": json.Number("2024"), "month": json.Number("3"), "day": json.Number("2"),
			}
			addExemption(t, m, InvMonotonicDueDates,
				"T222 fixture: a GENUINELY grounded exemption. The recorded schedule really does carry a "+
					"non-contiguous repayment window here, so the invariant really is violated and the "+
					"exemption really does silence it. It is admissible; the corpus-wide count is the "+
					"only thing that notices it arrived.")
		})

		got := selfTestRun(t, store)
		// The fixture must be ADMISSIBLE, or this proves nothing about the count.
		if got.Inadmissible != 0 {
			t.Fatalf("the grounded fixture was refused, so the count assertion below is not the thing "+
				"under test:\n%s", render(got))
		}
		if got.InvariantsExempted != 5 {
			t.Fatalf("adding one grounded exemption should read 5; got %d", got.InvariantsExempted)
		}
		if got.InvariantsExempted == 4 {
			t.Fatal("THE PIN CANNOT FIRE UPWARD")
		}
		if got.InvariantViolations != 0 {
			t.Errorf("the added exemption is supposed to SILENCE the violation it is grounded in; "+
				"violations read %d", got.InvariantViolations)
		}
		out := render(got)
		if !strings.Contains(out, "5 GROUNDED") {
			t.Errorf("the census does not report the fifth grounded exemption:\n%s",
				grepLines(out, "GROUNDED"))
		}
		t.Logf("count moved 4 -> %d with the run still green", got.InvariantsExempted)
	})
}

// TestRecordedScheduleIsTheOneBuilder pins the property that makes the grounding
// check trustworthy: the schedule an exemption is judged against is CELL FOR CELL
// the schedule the replay implementation answers with, and the placeholder SETS
// are the same SETS — because there is one builder. Two builders that disagreed
// about which cells are placeholders, or about what the cells are, would be the
// T9-F1b shape all over again: one half of the harness policing a cell the other
// half resolves differently.
//
// FINDING T225-F3 — WHAT THIS TEST USED TO COMPARE. It compared ph.Count(), one
// integer, and NOTHING ELSE, while its own docstring and T222's handoff claimed
// "BYTE-FOR-BYTE" and "the two now cannot drift". T225 mutated it twice and both
// mutations PASSED:
//
//	M1  a second, DIVERGENT placeholder builder in NewReplayImplementation, with
//	    the same COUNT of placeholder cells on different cells
//	        --- PASS, while printing "47 schedule vectors agree"
//	M2  the replay answering a materially different schedule (final row's
//	    OutstandingPrincipalMinor forced to 0), placeholders untouched
//	        --- PASS
//
// The corpus makes the count comparison thinner still: the placeholder histogram
// over the store is map[0:46 1:1] [VERIFIED: T225's probe, re-measured by T230],
// so the old assertion was 0 == 0 on 46 rows and 1 == 1 on one. Both mutations are
// re-run against the version below in T230's handoff; both go RED, M1 naming the
// cell the two builders disagree about and M2 naming the row, the field and the
// two values.
func TestRecordedScheduleIsTheOneBuilder(t *testing.T) {
	pristine := storeRoot(t)
	vectors, loadErrs, err := LoadStore(pristine, "")
	if err != nil || len(loadErrs) != 0 {
		t.Fatalf("LoadStore: %v / %v", err, loadErrs)
	}
	impl, _, ierr := NewReplayImplementation(pristine, "")
	if ierr != nil {
		t.Fatalf("NewReplayImplementation: %v", ierr)
	}
	reporter, ok := impl.(PlaceholderReporter)
	if !ok {
		t.Fatal("the replay implementation no longer reports placeholders")
	}
	checked, withPlaceholders, cellsCompared, placeholderCells := 0, 0, 0, 0
	for _, v := range vectors {
		if v.Expect.Kind != "schedule" {
			continue
		}
		req, cerr := v.Request.ContractRequest()
		if cerr != nil {
			t.Fatalf("%s: %v", v.CaseID, cerr)
		}
		recorded, ph, rerr := RecordedSchedule(v)
		if rerr != nil {
			t.Fatalf("%s: RecordedSchedule: %v", v.CaseID, rerr)
		}
		answered, gerr := impl.Generate(context.Background(), req)
		if gerr != nil {
			t.Fatalf("%s: the replay refused a schedule vector: %v", v.CaseID, gerr)
		}

		// THE SCHEDULE, CELL BY CELL. Not reflect.DeepEqual: a mismatch has to
		// name the row and the field, because "the schedules differ" is exactly
		// the message that would send the next reader looking in the wrong place.
		if len(recorded.Periods) != len(answered.Periods) {
			t.Errorf("%s: RecordedSchedule built %d rows, the replay answered %d",
				v.CaseID, len(recorded.Periods), len(answered.Periods))
			continue
		}
		for i := range recorded.Periods {
			for _, cell := range scheduleCells(recorded.Periods[i], answered.Periods[i]) {
				cellsCompared++
				if cell.recorded != cell.answered {
					t.Errorf("%s row %d %s: RecordedSchedule says %s, the replay answers %s. "+
						"THE GROUNDING CHECK AND THE REPLAY ARE NO LONGER JUDGING THE SAME SCHEDULE",
						v.CaseID, i, cell.field, cell.recorded, cell.answered)
				}
			}
		}

		// THE PLACEHOLDER SET, NOT ITS SIZE. Equal counts on different cells is
		// M1, and it is the mutation the old assertion could not see.
		answeredPH := reporter.PlaceholderCells(req)
		for _, cell := range placeholderDiff(ph, answeredPH) {
			t.Errorf("%s: placeholder disagreement at row %d %s — RecordedSchedule says %v, "+
				"the replay says %v. One half of the harness would police a cell the other half "+
				"resolves differently (the T9-F1b shape)",
				v.CaseID, cell.period, cell.field, cell.inRecorded, cell.inAnswered)
		}
		placeholderCells += ph.Count()
		if ph.Count() > 0 {
			withPlaceholders++
		}
		checked++
	}
	if checked == 0 {
		t.Fatal("checked ZERO schedule vectors, so this test is vacuous")
	}
	if cellsCompared == 0 {
		t.Fatal("compared ZERO cells, so the schedule agreement asserted above is asserted of nothing")
	}
	// P-35 fixture bite: an all-empty agreement proves nothing about placeholders.
	if withPlaceholders == 0 || placeholderCells == 0 {
		t.Fatal("not one vector in the store produces a placeholder cell, so the placeholder-set " +
			"agreement asserted above is empty == empty on every row")
	}
	// THE ATTESTATION IS CONDITIONAL ON HAVING PASSED. Under T225's M1 the old
	// test printed "47 schedule vectors agree" WHILE THEY DID NOT AGREE — a guard
	// attesting the property it was failing to check. A log line that says "agree"
	// may only be emitted by a run that found agreement.
	if t.Failed() {
		return
	}
	t.Logf("%d schedule vectors agree on %d cells; %d of them carry placeholders, %d placeholder cell(s) "+
		"corpus-wide, sets compared as sets", checked, cellsCompared, withPlaceholders, placeholderCells)
}

// scheduleCell is one cell of one row, rendered, from both builders.
type scheduleCell struct {
	field              string
	recorded, answered string
}

// scheduleCells renders EVERY cell of one row from both schedules.
//
// Every cell, not the money ones: the first observed defect in DEC-1 lived in the
// cells a three-scalar check never looked at (diffSchedule's own doc comment), and
// a builder that drifted on a row KIND or a due date would be just as invisible.
// Money is rendered with %d off the int64 — no float, no formatting library.
func scheduleCells(recorded, answered contract.Period) []scheduleCell {
	return []scheduleCell{
		{"kind", periodKindName(recorded.Kind), periodKindName(answered.Kind)},
		{FieldInstallmentNumber,
			fmt.Sprintf("%d", recorded.InstallmentNumber), fmt.Sprintf("%d", answered.InstallmentNumber)},
		{FieldFromDate, civil(recorded.FromDate), civil(answered.FromDate)},
		{FieldDueDate, civil(recorded.DueDate), civil(answered.DueDate)},
		{FieldPrincipalMinor,
			fmt.Sprintf("%d", recorded.PrincipalMinor), fmt.Sprintf("%d", answered.PrincipalMinor)},
		{FieldInterestMinor,
			fmt.Sprintf("%d", recorded.InterestMinor), fmt.Sprintf("%d", answered.InterestMinor)},
		{FieldOutstandingPrincipalMinor,
			fmt.Sprintf("%d", recorded.OutstandingPrincipalMinor),
			fmt.Sprintf("%d", answered.OutstandingPrincipalMinor)},
	}
}

// placeholderCellDiff is one cell the two placeholder sets disagree about.
type placeholderCellDiff struct {
	period                 int
	field                  string
	inRecorded, inAnswered bool
}

// placeholderDiff compares two placeholder sets AS SETS, in both directions, so a
// cell present in one and absent from the other is named whichever way round it
// is and whatever the two counts happen to be.
func placeholderDiff(a, b PlaceholderCells) []placeholderCellDiff {
	var out []placeholderCellDiff
	seen := map[int]map[string]bool{}
	note := func(period int, field string) {
		if seen[period] == nil {
			seen[period] = map[string]bool{}
		}
		if seen[period][field] {
			return
		}
		seen[period][field] = true
		if a.Has(period, field) != b.Has(period, field) {
			out = append(out, placeholderCellDiff{
				period: period, field: field,
				inRecorded: a.Has(period, field), inAnswered: b.Has(period, field),
			})
		}
	}
	for period, row := range a {
		for field := range row {
			note(period, field)
		}
	}
	for period, row := range b {
		for field := range row {
			note(period, field)
		}
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].period != out[j].period {
			return out[i].period < out[j].period
		}
		return out[i].field < out[j].field
	})
	return out
}

// FINDING T225-F5 — SCHEDULE-UNREADABLE HAD NO TEST, AND NOR DID THE default: ARM.
//
// T225 grepped exemption_test.go for both and found zero hits, then drove
// SCHEDULE-UNREADABLE red by hand and reported it REACHABLE AND CORRECT. So these
// are missing tests, not dead branches, and the branches stay.
func TestExemptionGroundingRefusesAnUnreadableSchedule(t *testing.T) {
	store := copyStore(t, storeRoot(t))
	editVector(t, store, fambN104File, func(t *testing.T, m map[string]any) {
		periodsOf(t, m)[5].(map[string]any)["kind"] = "NOT_A_KIND"
	})
	vectors, loadErrs, err := LoadStore(store, "")
	if err != nil || len(loadErrs) != 0 {
		t.Fatalf("the fixture store does not load: %v / %v", err, loadErrs)
	}
	var checked int
	for _, v := range vectors {
		if v.CaseID != "T116-G8-FAMB-N104" {
			continue
		}
		for _, g := range CheckExemptionGrounding(v) {
			checked++
			if g.Status != ExemptionScheduleUnreadable {
				t.Errorf("%s classified %s, want %s", g.Invariant, g.Status, ExemptionScheduleUnreadable)
			}
			if len(g.NotAsserted) != 0 {
				t.Errorf("%s: SCHEDULE-UNREADABLE must carry no unmade assertions (the invariant never "+
					"ran); it carries %v", g.Invariant, g.NotAsserted)
			}
			if !g.Inadmissible() {
				t.Errorf("%s: an exemption nothing could check must be inadmissible", g.Invariant)
			}
		}
		problems := admitExemptions(v)
		if len(problems) != 2 {
			t.Fatalf("expected both exemptions refused, got %d problem(s): %v", len(problems), problems)
		}
		joined := strings.Join(problems, "\n")
		for _, want := range []string{
			"COULD NOT BE DETERMINED",
			"do not form a schedule",
			`"NOT_A_KIND" is not one of DISBURSEMENT, DOWN_PAYMENT, REPAYMENT`,
			// It must not be confused with the capture-gap case, which is admitted.
			"that is UNDETERMINED-ON-THE-RECORD and is reported, not refused",
		} {
			if !strings.Contains(joined, want) {
				t.Errorf("the refusal must say %q; it said:\n%s", want, joined)
			}
		}
		t.Logf("refused: %s", firstLine(problems[0]))
	}
	if checked != 2 {
		t.Fatalf("classified %d exemption(s); the fixture vector carries 2, so this test is not "+
			"exercising what it names", checked)
	}
}

// The default: arm — a grounding status refuseUngroundedExemptions does not
// classify. It is unreachable through CheckExemptionGrounding by construction,
// which is exactly why the function takes the verdicts as an argument: an arm no
// test can execute is an arm nobody knows the behaviour of (P-22), and the one
// thing it must NOT do is fall through into a silent pass.
func TestUnclassifiedGroundingStatusIsRefusedNotPassed(t *testing.T) {
	invented := ExemptionGrounding{
		Invariant: InvPrincipalSum,
		Status:    ExemptionGroundingStatus("A-STATUS-FROM-THE-FUTURE"),
	}
	if invented.Grounded() || invented.Undetermined() {
		t.Fatal("an invented status must be neither grounded nor undetermined, or this test is vacuous")
	}
	if !invented.Inadmissible() {
		t.Fatal("an unclassified grounding status must be INADMISSIBLE by default: a verdict nobody has " +
			"thought about must not be a pass")
	}
	problems := refuseUngroundedExemptions([]ExemptionGrounding{invented})
	if len(problems) != 1 {
		t.Fatalf("the default arm produced %d problem(s), want 1: %v", len(problems), problems)
	}
	for _, want := range []string{
		"A-STATUS-FROM-THE-FUTURE",
		"does not classify",
		"not a pass",
		InvPrincipalSum,
	} {
		if !strings.Contains(problems[0], want) {
			t.Errorf("the default arm must say %q; it said:\n%s", want, problems[0])
		}
	}
	// And the two admissible statuses must NOT reach it.
	for _, ok := range []ExemptionGroundingStatus{ExemptionGrounded, ExemptionUndetermined} {
		if got := refuseUngroundedExemptions([]ExemptionGrounding{
			{Invariant: InvPrincipalSum, Status: ok}}); len(got) != 0 {
			t.Errorf("%s produced a refusal: %v", ok, got)
		}
	}
	t.Logf("default arm: %s", problems[0])
}
