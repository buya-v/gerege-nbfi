package conformance

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
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
// ITS OWN VECTOR RECORDED and honouring that vector's unrecorded_fields, must
// come back VIOLATED. Not "the reason does not contain a weasel word" — the
// property the report already claims for every exemption, asserted.
//
// DRIVEN RED. Each subtest below builds a store copy that is admissible on main's
// bytes and shows the run refusing it here. Measured on the PRE-T222 bytes (the
// admit.go loop that checked only the invariant name and a non-empty reason),
// every one of the three fixtures below graded clean:
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
// extra ungraded cell. The transcripts are reproduced in the T222 handoff.
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
			"HOLDS ON THE SCHEDULE THIS VECTOR ITSELF RECORDED",
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

	// SHAPE 2 — THE DANGEROUS PAIRING. An exemption whose invariant reads ONLY
	// cells the same vector's unrecorded_fields has withdrawn. unrecorded_fields
	// takes the cells out of the diff; the exemption takes out the invariant that
	// would have noticed; and the exemption's REASON — a sentence about what the
	// oracle does on this shape — then rests on numbers nobody recorded.
	t.Run("RED_the_dangerous_pairing_an_exemption_over_withdrawn_cells", func(t *testing.T) {
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
		// makes ungrounded is one T116 committed.
		c := InspectExemptions(vectors)
		if c.Declared != 4 {
			t.Fatalf("the fixture must not change the number of exemptions; declared %d", c.Declared)
		}
		if c.Ungrounded != 1 {
			t.Fatalf("expected exactly 1 ungrounded exemption, got %d: %v", c.Ungrounded, c.UngroundedNames)
		}

		s := selfTestRun(t, store)
		detail := inadmissibleDetail(t, s, "T116-G8-FAMB-N104")
		for _, want := range []string{
			"WITHDRAW EVERY CELL THAT INVARIANT READS",
			InvPrincipalAmortizes,
			"outstanding_principal_minor",
			"removes the cells from the cell diff AND removes the invariant that would",
		} {
			if !strings.Contains(detail, want) {
				t.Errorf("the refusal must say %q; it said:\n%s", want, detail)
			}
		}
		// It must NOT fire on the OTHER exemption of the same vector, whose cells
		// are all still recorded. A check that refuses the whole vector's
		// exemptions the moment one is bad would be over-broad and would teach the
		// next author to delete the mechanism.
		if strings.Contains(detail, InvPrincipalSum) {
			t.Errorf("the refusal also fired on %s, whose cells are recorded and which is genuinely "+
				"grounded:\n%s", InvPrincipalSum, detail)
		}
		out := render(s)
		if !strings.Contains(out,
			"UNGROUNDED: T116-G8-FAMB-N104 — "+InvPrincipalAmortizes+" [RESTS-ON-WITHDRAWN-CELLS]") {
			t.Errorf("the report does not name the pairing:\n%s", grepLines(out, "UNGROUNDED"))
		}
		t.Logf("refused: %s", firstLine(detail))
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
		out := render(s)
		if !strings.Contains(out, "4 GROUNDED (the recorded schedule VIOLATES the exempted invariant), 0 UNGROUNDED.") {
			t.Errorf("the report does not state the grounding result:\n%s", grepLines(out, "GROUNDED"))
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
// check trustworthy: the schedule an exemption is judged against is BYTE-FOR-BYTE
// the schedule the replay implementation answers with, because there is one
// builder. Two builders that disagreed about which cells are placeholders would be
// the T9-F1b shape all over again — one half of the harness policing a cell the
// other half resolves differently.
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
	checked, withPlaceholders := 0, 0
	for _, v := range vectors {
		if v.Expect.Kind != "schedule" {
			continue
		}
		req, cerr := v.Request.ContractRequest()
		if cerr != nil {
			t.Fatalf("%s: %v", v.CaseID, cerr)
		}
		_, ph, rerr := RecordedSchedule(v)
		if rerr != nil {
			t.Fatalf("%s: RecordedSchedule: %v", v.CaseID, rerr)
		}
		if got, want := ph.Count(), reporter.PlaceholderCells(req).Count(); got != want {
			t.Errorf("%s: RecordedSchedule reports %d placeholder cells, the replay reports %d",
				v.CaseID, got, want)
		}
		if ph.Count() > 0 {
			withPlaceholders++
		}
		checked++
	}
	if checked == 0 {
		t.Fatal("checked ZERO schedule vectors, so this test is vacuous")
	}
	// P-35 fixture bite: an all-zero agreement proves nothing about placeholders.
	if withPlaceholders == 0 {
		t.Fatal("not one vector in the store produces a placeholder cell, so the agreement asserted " +
			"above is 0 == 0 on every row")
	}
	t.Logf("%d schedule vectors agree, %d of them carrying placeholder cells", checked, withPlaceholders)
}
