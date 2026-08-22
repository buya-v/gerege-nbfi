package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

// FINDING A2-19 F3 — A REFUSED VECTOR'S KILLS USED TO BACK A CAPABILITY.
//
// THE DEFECT. CounterfactualCoverage was handed every vector the run did not
// declare INADMISSIBLE, and a REFUSED vector is not inadmissible. So a vector the
// harness had just declined to grade — because its seam is blind, because a
// required capability is outside the graded domain, because the seam or the
// capability is not in the registry at all, or because the request itself is
// outside the graded domain — still had its named kills credited to whatever
// capability they named. The visible effect, measured by A2-19, is that adding a
// REFUSED vector took UNBACKED from 1 to 0 and the kill count from 103 to 104: a
// refusal made the coverage report QUIETER.
//
// WHY THAT INVERTS THE MEANING. The harness's own words for a refusal are "not a
// pass, not a failure" — it says no discriminating vector exists here, or the
// seam cannot see the behaviour. A vector that graded nothing cannot BACK
// anything. Crediting it means the one case where there is LESS evidence is the
// case where the UNBACKED warning disappears, which is the exact shape of defect
// this whole harness exists to make impossible.
//
// The tests below are ordered the way the work was done: measure the live blast
// radius first, then establish which refusal classes can carry kills at all, then
// prove the fix on a full end-to-end run.

// TestLiveStoreRefusedVectorBlastRadius is the MEASUREMENT, taken over the real
// committed store, of how much the defect was actually moving today.
//
// It is a census, not a boolean: it reports how many vectors it inspected, how
// many the harness refuses, how many kills those refusals carry, and which graded
// capabilities would lose all their backing if refused vectors stopped counting.
// A check that inspects zero items is an ERROR and not a pass (P-35), so the
// vector count is asserted before anything else is concluded from it.
//
// MEASURED ON THE COMMITTED STORE: 48 vectors, 0 refused, 0 kills carried by a
// refused vector, 0 capabilities backed only by a refusal. The live exposure of
// A2-19 F3 is therefore NIL TODAY, and this test is what establishes that rather
// than the fix implying it.
//
// It stays as a standing guard because a refused vector in the committed store is
// already exit 2 for the whole run, so "0 refused" is not a fact about one day —
// it is the only state the store is ever allowed to be green in.
func TestLiveStoreRefusedVectorBlastRadius(t *testing.T) {
	store := storeRoot(t)
	registry, err := LoadCapabilityRegistry(filepath.Join(store, "capabilities.json"))
	if err != nil {
		t.Fatalf("LoadCapabilityRegistry: %v", err)
	}
	vectors, loadErrs, err := LoadStore(store, "")
	if err != nil {
		t.Fatalf("LoadStore: %v", err)
	}
	for _, le := range loadErrs {
		t.Errorf("%s could not be loaded: %v", le.Path, le.Err)
	}
	if len(vectors) == 0 {
		t.Fatal("THIS CENSUS INSPECTED ZERO VECTORS, which is an ERROR and not a pass (P-35): a blast " +
			"radius measured over nothing is not a measurement")
	}

	var refused []string
	refusedKills := 0
	// coverageFromRefused is what a refused vector WOULD have contributed, computed
	// the pre-fix way: capability -> counterfactual ids. It is the blast radius.
	coverageFromRefused := map[string][]string{}
	for _, v := range vectors {
		verdict := registry.RefusalFor(v)
		if verdict.Gradeable {
			continue
		}
		refused = append(refused, string(v.Class)+" "+v.CaseID+" ("+string(verdict.Reason)+")")
		refusedKills += len(v.GradedAgainst)
		if v.Class != ClassParity {
			continue
		}
		for _, cf := range v.GradedAgainst {
			if !v.StructuralKillIsCompared(cf) {
				continue
			}
			if graded, defined := registry.IsGraded(cf.Capability); defined && graded {
				coverageFromRefused[cf.Capability] = append(coverageFromRefused[cf.Capability], cf.ID)
			}
		}
	}

	// Which graded capabilities are backed ONLY by refusals? Those are the ones
	// whose UNBACKED warning the defect would have silenced.
	backedOnlyByRefusal := []string{}
	_, uncoveredAfterFix := registry.CounterfactualCoverage(vectors)
	afterFixUnbacked := map[string]bool{}
	for _, name := range uncoveredAfterFix {
		afterFixUnbacked[name] = true
	}
	for name := range coverageFromRefused {
		if afterFixUnbacked[name] {
			backedOnlyByRefusal = append(backedOnlyByRefusal, name)
		}
	}
	sort.Strings(backedOnlyByRefusal)

	t.Logf("BLAST RADIUS, MEASURED: %d vectors inspected, %d graded capabilities (%v), "+
		"%d vectors refused %v, %d kills carried by refused vectors, "+
		"%d graded capabilities backed only by a refusal %v",
		len(vectors), len(registry.GradedCapabilities()), registry.GradedCapabilities(),
		len(refused), refused, refusedKills, len(backedOnlyByRefusal), backedOnlyByRefusal)

	if len(refused) > 0 {
		t.Errorf("the committed store contains %d REFUSED vector(s) %v. A refused vector is exit 2 for the "+
			"whole run, so this is a corpus defect in its own right; and until A2-22 their %d named kills "+
			"were being credited to the coverage report", len(refused), refused, refusedKills)
	}
	if len(backedOnlyByRefusal) > 0 {
		t.Errorf("THESE GRADED CAPABILITIES ARE BACKED ONLY BY REFUSED VECTORS: %v. A refusal grades "+
			"nothing, so these are unbacked in_graded_domain claims wearing a coverage line",
			backedOnlyByRefusal)
	}
}

// refusedVectorCases enumerates ONE construction per refusal class, so that "a
// refused vector backs nothing" is proved for every way a vector can be refused
// rather than for the one class that happened to be convenient. A2-19 could not
// close this; the five entries below are the closure.
//
// Every case carries a well-formed money kill on schedule.core — a capability
// that IS in_graded_domain and IS exercised by the seam — so in every one of them
// the pre-fix code credited coverage to a capability off a vector it had just
// refused to grade.
func refusedVectorCases(pin *Pin) []struct {
	name   string
	reason RefusalReason
	mutate func(*Vector)
} {
	return []struct {
		name   string
		reason RefusalReason
		mutate func(*Vector)
	}{
		{
			name:   "SEAM_BLIND",
			reason: ReasonSeamBlind,
			// charges is "blind" on path_a_embeddable: the seam hard-wires the charge
			// argument to null, so a port that honours charges and one that ignores
			// them score identically on every capture from it.
			mutate: func(v *Vector) {
				v.CapabilitiesRequired = []string{"schedule.core", "charges"}
			},
		},
		{
			name:   "UNGRADED_CAPABILITY",
			reason: ReasonUngradedCapability,
			// daycount.actual.actual IS exercised by path_a_embeddable and is NOT in
			// the graded domain, which is precisely the pair that produces this class.
			mutate: func(v *Vector) {
				v.CapabilitiesRequired = []string{"schedule.core", "daycount.actual.actual"}
			},
		},
		{
			name:   "UNKNOWN_CAPABILITY",
			reason: ReasonUnknownCapability,
			mutate: func(v *Vector) {
				v.CapabilitiesRequired = []string{"schedule.core", "no.such.capability"}
			},
		},
		{
			name:   "UNKNOWN_SEAM",
			reason: ReasonUnknownSeam,
			mutate: func(v *Vector) {
				v.Oracle.Seam = "a_seam_nobody_declared"
			},
		},
		{
			name:   "UNGRADED_REQUEST",
			reason: ReasonUngradedRequest,
			// The STRONGEST class of the five, and the one that makes this fix
			// unavoidable: the capability gate passes in full — every required
			// capability is exercised by the seam AND inside the graded domain — and
			// the vector is refused purely on a request field value. So EVERY kill
			// such a vector names was being credited, not merely some of them.
			mutate: func(v *Vector) {
				v.Request.RepaymentEvery = 2
			},
		},
	}
}

// TestRefusedVectorCannotBackACapability is the RED/GREEN demonstration at the
// registry seam, one case per refusal class.
//
// DRIVEN RED ON THE UNFIXED CODE. Against main at cc33f7f, before
// CounterfactualCoverage consulted RefusalFor, all five subtests failed with
// "backs schedule.core with [A2-22-RED-KILL] even though the harness REFUSES it".
// The control below passed in the same run, which is what makes the five
// failures mean something: the assertion can distinguish the two populations, so
// it is not a control that cannot fail (P-22).
func TestRefusedVectorCannotBackACapability(t *testing.T) {
	root := repoRoot(t)
	store := storeRoot(t)
	pin, err := LoadPin(filepath.Join(store, "PIN.json"))
	if err != nil {
		t.Fatalf("LoadPin: %v", err)
	}
	registry, err := LoadCapabilityRegistry(filepath.Join(store, "capabilities.json"))
	if err != nil {
		t.Fatalf("LoadCapabilityRegistry: %v", err)
	}

	kill := Counterfactual{
		ID:          "A2-22-RED-KILL",
		Capability:  "schedule.core",
		Description: "computes interest as balance * rateFactor in one multiplication instead of the oracle's three separately rounded operations",
		Evidence:    "contract.go Period.InterestMinor; DEC-1 section 8 item 3b",
		MarginMinor: "1",
	}

	// THE CONTROL, FIRST AND UNCONDITIONALLY. If a gradeable vector carrying this
	// exact kill does NOT back schedule.core, every "backs nothing" result below
	// is vacuous — the assertion would be measuring a broken fixture rather than
	// the fix. A control that cannot fail is worse than none (P-22).
	control := parityShell(pin)
	control.CaseID = "A2-22-CONTROL"
	control.GradedAgainst = []Counterfactual{kill}
	if problems := Admit(control, pin, root); len(problems) > 0 {
		t.Fatalf("the control vector is inadmissible, so this whole test is vacuous: %v", problems)
	}
	if verdict := registry.RefusalFor(control); !verdict.Gradeable {
		t.Fatalf("the control vector is REFUSED (%s: %v), so it cannot serve as the positive case",
			verdict.Reason, verdict.Detail)
	}
	covered, uncovered := registry.CounterfactualCoverage([]*Vector{control})
	if len(covered["schedule.core"]) != 1 {
		t.Fatalf("CONTROL FAILED: a GRADEABLE vector naming %s must back schedule.core, got %v. "+
			"Without this the refusal assertions below prove nothing.", kill.ID, covered["schedule.core"])
	}
	if containsString(uncovered, "schedule.core") {
		t.Fatalf("CONTROL FAILED: schedule.core is backed by %v and still reported UNBACKED",
			covered["schedule.core"])
	}
	t.Logf("control: a gradeable vector naming %s backs schedule.core with %v, and schedule.core is not "+
		"reported unbacked — the assertion below can therefore fail", kill.ID, covered["schedule.core"])

	for _, tc := range refusedVectorCases(pin) {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			v := parityShell(pin)
			v.CaseID = "A2-22-REFUSED-" + tc.name
			v.GradedAgainst = []Counterfactual{kill}
			tc.mutate(v)

			// The vector must be REFUSED for the reason this case is named after,
			// and it must be otherwise well-formed. A vector refused for the wrong
			// reason, or one that is merely inadmissible, would not exercise the
			// path under test.
			verdict := registry.RefusalFor(v)
			if verdict.Gradeable {
				t.Fatalf("fixture is not refused at all, so this case tests nothing")
			}
			if verdict.Reason != tc.reason {
				t.Fatalf("fixture refused as %s, want %s (%v)", verdict.Reason, tc.reason, verdict.Detail)
			}

			covered, uncovered := registry.CounterfactualCoverage([]*Vector{v})
			if len(covered["schedule.core"]) != 0 {
				t.Errorf("A REFUSED VECTOR BACKED A CAPABILITY: %s is refused (%s) and still backs "+
					"schedule.core with %v. A refusal is not a pass and not a failure — it means the "+
					"vector graded NOTHING — so it cannot back anything (finding A2-19 F3).",
					v.CaseID, verdict.Reason, covered["schedule.core"])
			}
			if !containsString(uncovered, "schedule.core") {
				t.Errorf("A REFUSAL SILENCED AN UNBACKED WARNING: over a store whose only vector is the "+
					"refused %s, schedule.core must be reported UNBACKED, and it was not. The case with "+
					"LESS evidence must not be the quieter report.", v.CaseID)
			}
		})
	}
}

// TestRefusedVectorDoesNotSilenceUnbackedEndToEnd is the same proof through the
// whole harness — LoadStore, gradeVector, the summary and the rendered report —
// on a copy of the REAL store, because a fix that holds at one function call and
// not in the run that ships is not a fix.
//
// THE PERTURBATION IS ONE WORD. path_a_embeddable's status for monthend.reanchor
// goes "exercised" -> "blind", which is exactly the kind of discovery this
// registry exists to absorb: it is how the charges, holiday and working-day blind
// spots were each recorded. All 14 vectors requiring monthend.reanchor sit on that
// seam, so all 14 are refused at once and monthend.reanchor — still marked
// in_graded_domain — loses every backing vector.
//
// DRIVEN RED ON THE UNFIXED CODE, against main at cc33f7f:
//
//	UNBACKED in_graded_domain claims: (absent — monthend.reanchor read as backed)
//	counterfactuals named: 110 (103 money, 7 structural)
//
// GREEN after the fix:
//
//	UNBACKED in_graded_domain claims: monthend.reanchor
//	counterfactuals named: 48 (47 money, 1 structural); 62 more carried by refused vectors, credited nowhere
func TestRefusedVectorDoesNotSilenceUnbackedEndToEnd(t *testing.T) {
	root := repoRoot(t)
	pristine := storeRoot(t)
	blinded := copyStore(t, pristine)

	// perturb() replaces the FIRST occurrence, and path_a_embeddable is the first
	// seam block in capabilities.json. It fails loudly if the text is absent, so
	// this cannot silently become a no-op.
	perturb(t, filepath.Join(blinded, "capabilities.json"),
		"\"schedule.core\": \"exercised\",\n        \"monthend.reanchor\": \"exercised\",",
		"\"schedule.core\": \"exercised\",\n        \"monthend.reanchor\": \"blind\",")

	impl, n, err := NewReplayImplementation(blinded, "")
	if err != nil {
		t.Fatalf("NewReplayImplementation: %v", err)
	}
	if n == 0 {
		t.Fatal("the replay implementation learned no answers")
	}
	// SelfTestMode is false on purpose: the UNBACKED fatal reason is suppressed in
	// self-test mode, and the fatal reason is half of what is being proved. The
	// oracle probe is declared up because no vector in this run reaches an oracle
	// — every assertion below is about refusal bookkeeping, and the run's exit
	// code is 2 either way once 14 vectors are refused.
	s := mustRun(t, Options{
		RepoRoot: root, StoreRoot: blinded,
		Implementation: impl, ImplementationName: "replay", OracleProbe: "up",
	})

	// THE FIXTURE MUST BITE. If the perturbation refused nothing, everything below
	// is a check over zero items, which is an ERROR and not a pass (P-35).
	if s.Refused == 0 {
		t.Fatalf("the perturbation refused NO vector, so this proof inspects zero items and is vacuous\n%s",
			render(s))
	}
	t.Logf("perturbation refused %d vectors of %d", s.Refused, len(s.Results))

	if !containsString(s.UncoveredGradedCapabilities, "monthend.reanchor") {
		t.Errorf("A REFUSAL SILENCED AN UNBACKED WARNING. Every vector backing monthend.reanchor is "+
			"REFUSED on this store, monthend.reanchor is still marked in_graded_domain, and the run does "+
			"not report it UNBACKED. Reported unbacked: %v; reported coverage: %v",
			s.UncoveredGradedCapabilities, s.CounterfactualCoverage["monthend.reanchor"])
	}
	if got := s.CounterfactualCoverage["monthend.reanchor"]; len(got) != 0 {
		t.Errorf("refused vectors still back monthend.reanchor with %v", got)
	}

	// The fatal reason, not merely the field: the run must SAY the claim is
	// unbacked, in the sentence an operator reads.
	if !containsSubstring(s.FatalReasons, "MARKED in_graded_domain BUT NO PARITY VECTOR KILLS") {
		t.Errorf("the unbacked claim produced no fatal reason: %v", s.FatalReasons)
	}
	out := render(s)
	if !strings.Contains(out, "UNBACKED in_graded_domain claims: monthend.reanchor") {
		t.Errorf("the rendered report does not name monthend.reanchor as unbacked:\n%s", out)
	}

	// The kill count must shed exactly the refused vectors' kills, and the shed
	// count must be DISCLOSED rather than dropped. 14 refused vectors carry 62
	// kills (56 money, 6 structural) of the store's 113 (106 money, 7 structural).
	//
	// THESE THREE NUMBERS ARE CORPUS-WIDE TRIPWIRES AND THEY MOVED WITH T116.
	// 110 -> 113 and 103 -> 106 money kills, because T116 promoted three parity
	// vectors carrying one money counterfactual each (G-8 family B and its clean
	// boundary control); the credited count moved 48 -> 51 for the same reason,
	// none of the three being among the 14 the perturbation refuses. The refused
	// count (62) and the structural counts (7 and 1) are UNMOVED, which is what
	// says the change is additive and touched no existing vector.
	if s.RefusedCounterfactualsNamed != 62 {
		t.Errorf("kills carried by refused vectors: got %d, want 62", s.RefusedCounterfactualsNamed)
	}
	if s.CounterfactualsNamed != 51 || s.MoneyKills != 50 || s.StructuralKills != 1 {
		t.Errorf("credited kills: got %d (%d money, %d structural), want 51 (50 money, 1 structural)",
			s.CounterfactualsNamed, s.MoneyKills, s.StructuralKills)
	}
	if !strings.Contains(out, "kills carried by REFUSED vectors") {
		t.Errorf("the report does not disclose the kills it withheld:\n%s", out)
	}

	// AND THE PRISTINE STORE IS UNMOVED. The whole point of the bar is that this
	// fix changes nothing when nothing is refused.
	pristineImpl, _, perr := NewReplayImplementation(pristine, "")
	if perr != nil {
		t.Fatalf("NewReplayImplementation(pristine): %v", perr)
	}
	ps := mustRun(t, Options{
		RepoRoot: root, StoreRoot: pristine,
		Implementation: pristineImpl, ImplementationName: "replay", SelfTestMode: true,
	})
	if ps.Refused != 0 {
		t.Fatalf("the committed store refuses %d vectors; the no-change claim below cannot be made", ps.Refused)
	}
	if ps.RefusedCounterfactualsNamed != 0 {
		t.Errorf("kills carried by refused vectors on the committed store: got %d, want 0",
			ps.RefusedCounterfactualsNamed)
	}
	if ps.CounterfactualsNamed != 113 || ps.MoneyKills != 106 || ps.StructuralKills != 7 {
		t.Errorf("the committed store's kill count moved: got %d (%d money, %d structural), "+
			"want 113 (106 money, 7 structural)",
			ps.CounterfactualsNamed, ps.MoneyKills, ps.StructuralKills)
	}
	if len(ps.UncoveredGradedCapabilities) != 0 {
		t.Errorf("the committed store reports unbacked capabilities %v", ps.UncoveredGradedCapabilities)
	}
}

// FINDING A2-24 F2 — THE APPROVED CORROBORATION SEMANTICS HAD NO TEST AT ALL.
//
// A2-22 narrowed Summary.CorroborationsClaimed from the ADMISSIBLE population to
// the GRADED one; A2-24 adjudicated that narrowing and approved it. Then A2-24
// measured the thing that matters here: with the narrowing REVERTED,
// `go test ./... -count=1` is ALL GREEN. Nothing in the suite pinned the
// population, because THE COMMITTED STORE CARRIES ZERO
// provenance.corroborated_by ENTRIES — so both rules read 0 on it, for every
// possible pattern of refusals, and the semantics was held in place by nobody.
//
// WHY THE POPULATION IS THE GRADED ONE, stated here because a test that pins a
// number without its reason is a tripwire nobody dares move:
//
//   - It is NOT the kill argument. A counterfactual asserts DISCRIMINATION and
//     its antecedent is grading, so a refusal leaves it unrealised. A
//     corroboration asserts something about the RECORD — "a named second source
//     prints these columns for this row kind, and this vector's values agreed" —
//     it is validated offline at admission (admitCorroborations), and none of the
//     five RefusalFor reasons impugns it. A refused vector's corroboration is
//     STILL TRUE. On truth-conditions alone the wide population would win.
//   - The report scopes by POLARITY, not by truth. Hazard disclosures take the
//     widest population — RateFactorsRecorded and OverScaledCells accumulate in
//     gradeVector BEFORE any early return, so refused vectors still contribute
//     them. SUPPORT counts take the narrowest: GradedCells, CounterfactualsNamed,
//     MoneyKills, ParityPass. A corroboration exists only to make the corpus look
//     better attested and can never make it look worse, so it is support.
//   - The degenerate store settles it. Blind one seam and everything refuses; the
//     wide rule then prints "cells compared: 0" beside "corroboration claims: 51"
//     in the same report, which is the limiting case of the
//     confidence-nobody-measured that T17-F2 exists to prevent.
//
// THE STORE HAS TO BE BUILT, because the divergence does not exist on the
// committed corpus. This test injects ONE admissible corroboration into EVERY
// vector of a COPY (t.TempDir; the pristine store is never opened for writing)
// and then blinds monthend.reanchor, which refuses a block of vectors. The
// expectations below are DERIVED FROM THE RUN'S OWN OUTCOME RECORD rather than
// hard-coded, so T116-style corpus growth (43 -> 46 parity vectors this fire)
// moves them automatically and cannot silently defuse the guard.
//
// DRIVEN RED, on the pre-A2-22 bytes (the one-line revert that credits refused
// vectors' corroborations into CorroborationsClaimed):
//
//	corroborations credited to a run that compared nothing: got 51, want 37
//	    (37 graded + 14 refused, of 51 injected)
//	CorroborationsClaimed + RefusedCorroborationsClaimed = 65, want 51: the two
//	    counts OVERLAP instead of partitioning the corpus
//	the narrowing does not bite: 51 of 51 injected claims are credited even
//	    though 14 vectors were refused
//	the rendered report sentence is false: it says 51 claims were "made by GRADED
//	    vectors" when only 37 were, and that the 14 are "counted nowhere" when
//	    they are inside the 51
func TestCorroborationsAreScopedToTheGradedPopulation(t *testing.T) {
	root := repoRoot(t)
	blinded := copyStore(t, storeRoot(t))

	// FIXTURE BITE 1 (P-35): the injection must actually inject. An assertion over
	// zero corroborations passes under BOTH rules and is the vacuous guard this
	// whole file is about.
	injected := injectOneCorroborationIntoEveryVector(t, blinded)
	if injected == 0 {
		t.Fatal("injected ZERO corroborations: every assertion below would hold under both population " +
			"rules, so this test would be vacuous (P-35)")
	}

	// perturb() replaces the FIRST occurrence and fails loudly if the text is
	// absent, so this cannot silently become a no-op.
	perturb(t, filepath.Join(blinded, "capabilities.json"),
		"\"schedule.core\": \"exercised\",\n        \"monthend.reanchor\": \"exercised\",",
		"\"schedule.core\": \"exercised\",\n        \"monthend.reanchor\": \"blind\",")

	impl, n, err := NewReplayImplementation(blinded, "")
	if err != nil {
		t.Fatalf("NewReplayImplementation: %v", err)
	}
	if n == 0 {
		t.Fatal("the replay implementation learned no answers")
	}
	s := mustRun(t, Options{
		RepoRoot: root, StoreRoot: blinded,
		Implementation: impl, ImplementationName: "replay", OracleProbe: "up",
	})

	// FIXTURE BITE 2: without a refusal the two rules agree by construction.
	if s.Refused == 0 {
		t.Fatalf("the perturbation refused NO vector, so the narrowed and un-narrowed rules cannot "+
			"differ on this store and this test is vacuous\n%s", render(s))
	}
	// FIXTURE BITE 3: an inadmissible or errored vector would confound the
	// partition, since those populations are shed by other branches.
	if s.Inadmissible != 0 || s.Errored != 0 {
		var why []string
		for _, r := range s.Results {
			if r.Outcome == OutcomeInadmissible || r.Outcome == OutcomeError {
				why = append(why, fmt.Sprintf("%s (%s): %s", r.CaseID, r.Outcome, strings.Join(r.Detail, "; ")))
			}
		}
		t.Fatalf("the injection produced %d INADMISSIBLE and %d HARNESS-ERROR vectors, which would "+
			"confound the graded/refused partition: %v", s.Inadmissible, s.Errored, why)
	}
	// FIXTURE BITE 4: every loaded vector must carry exactly one claim, or
	// "injected" is not the corpus total and the partition check below is loose.
	if injected != len(s.Results) {
		t.Fatalf("injected %d corroborations but the run loaded %d vectors: the corpus total is not "+
			"1-per-vector and the partition assertion would not be exact", injected, len(s.Results))
	}

	// The expectation, derived from the run's OWN record of what it graded. This
	// is the population claim itself, written as an equation: the aggregate must
	// equal the count of vectors whose outcome was neither REFUSED nor
	// INADMISSIBLE.
	wantGraded := 0
	for _, r := range s.Results {
		switch r.Outcome {
		case OutcomeRefused, OutcomeInadmissible:
		default:
			wantGraded++
		}
	}
	t.Logf("store: %d vectors, %d injected claims, %d refused -> expect %d credited, %d shed",
		len(s.Results), injected, s.Refused, wantGraded, s.Refused)

	if s.CorroborationsClaimed != wantGraded {
		t.Errorf("corroborations credited to a run that compared nothing for them: got %d, want %d "+
			"(%d graded + %d refused, of %d injected). A corroboration is a SUPPORT number and this "+
			"report scopes support to what the run actually compared (A2-22, adjudicated A2-24).",
			s.CorroborationsClaimed, wantGraded, wantGraded, s.Refused, injected)
	}
	if s.RefusedCorroborationsClaimed != s.Refused {
		t.Errorf("claims shed by REFUSED vectors: got %d, want %d (one per refused vector). A shed "+
			"number that is not disclosed is a number nobody can audit.",
			s.RefusedCorroborationsClaimed, s.Refused)
	}
	if got := s.CorroborationsClaimed + s.RefusedCorroborationsClaimed; got != injected {
		t.Errorf("CorroborationsClaimed + RefusedCorroborationsClaimed = %d, want %d: the two counts "+
			"must PARTITION the corpus, not overlap it. Before A2-22 the refused branch counted and "+
			"then fell through into the credited one, so the shed count was a SUBSET of the credited "+
			"count and the report line describing them was false.", got, injected)
	}
	if s.CorroborationsClaimed >= injected {
		t.Errorf("the narrowing does not bite: %d of %d injected claims are credited even though %d "+
			"vectors were refused. On a store where a blinded seam refuses everything this rule would "+
			"print 0 cells compared beside %d corroboration claims.",
			s.CorroborationsClaimed, injected, s.Refused, injected)
	}

	// AND THE SENTENCE THE OPERATOR READS MUST BE TRUE OF THE NUMBERS IT PRINTS.
	// A revert that changes only grade.go ships a report line that lies, which is
	// itself evidence about which population the sentence wants.
	out := render(s)
	want := fmt.Sprintf("corroboration claims made by GRADED vectors: %d (a further %d are carried by "+
		"REFUSED vectors and %d by HARNESS-ERROR vectors, counted nowhere)",
		wantGraded, s.Refused, 0)
	if !strings.Contains(out, want) {
		t.Errorf("the rendered report does not carry the true sentence %q. Reported line(s):\n%s",
			want, grepLines(out, "corroboration claims made by"))
	}

	// AND THE COMMITTED STORE IS UNMOVED: with no corroboration anywhere and
	// nothing refused, both rules read 0 and this change is inert on the bar.
	pristineImpl, _, perr := NewReplayImplementation(storeRoot(t), "")
	if perr != nil {
		t.Fatalf("NewReplayImplementation(pristine): %v", perr)
	}
	ps := mustRun(t, Options{
		RepoRoot: root, StoreRoot: storeRoot(t),
		Implementation: pristineImpl, ImplementationName: "replay", SelfTestMode: true,
	})
	if ps.CorroborationsClaimed != 0 || ps.RefusedCorroborationsClaimed != 0 ||
		ps.ErroredCorroborationsClaimed != 0 {
		t.Errorf("the committed store now carries corroborations (%d credited, %d refused, %d errored). "+
			"That is not a failure of this rule, but the first such vector makes the choice LIVE, so "+
			"re-read the reasoning above rather than editing the number.",
			ps.CorroborationsClaimed, ps.RefusedCorroborationsClaimed, ps.ErroredCorroborationsClaimed)
	}
}

// FINDING A2-22 F3 / A2-24 F3, CLOSED — A HARNESS-ERROR VECTOR USED TO BACK A
// CAPABILITY.
//
// The graded population skipped only INADMISSIBLE and REFUSED, so a vector the
// harness could not complete AT ALL still credited its kills, its corroborations
// and its capability coverage. A2-24 recorded this as latent because the single
// assignment site for OutcomeError (Options.Implementation == nil) already makes
// the run fatal. It is latent for the EXIT CODE and live for the REPORT, and the
// report is what a reader takes away.
//
// DRIVEN RED, on the pre-A2-27 bytes, committed store, nil implementation:
//
//	results=51 errored=51 refused=0 inadmissible=0 gradedCells=0
//	CounterfactualsNamed=113 money=106 structural=7
//	uncovered=[]
//
// A run that compared ZERO cells claimed 113 kills and reported every
// in_graded_domain capability backed. That is the A2-19 F3 shape — less evidence,
// quieter report — reached through the other door.
func TestErroredVectorCannotBackACapability(t *testing.T) {
	root := repoRoot(t)

	// Corroborations are injected so the errored SHED count is a non-zero
	// positive assertion rather than 0-equals-0 (P-35). The store copy is a
	// t.TempDir; the pristine store is never opened for writing.
	store := copyStore(t, storeRoot(t))
	injected := injectOneCorroborationIntoEveryVector(t, store)
	if injected == 0 {
		t.Fatal("injected ZERO corroborations: the errored-shed assertion below would be 0 == 0 (P-35)")
	}

	// Implementation is deliberately nil. That is not a contrived state: it is
	// what cmd/conformance/impl_hook.go returns until a port is registered, and
	// Run has a FatalReason written for exactly it.
	s := mustRun(t, Options{
		RepoRoot: root, StoreRoot: store,
		ImplementationName: "none", OracleProbe: "up",
	})

	// FIXTURE BITE: prove the arm RAN and produced the population it is about
	// (P-64). Zero errored vectors would make every assertion below vacuous.
	if s.Errored == 0 {
		t.Fatalf("NO vector errored, so this test inspects zero items and is vacuous\n%s", render(s))
	}
	if s.Errored != len(s.Results) || injected != len(s.Results) {
		t.Fatalf("expected every one of the %d loaded vectors to error and to carry one injected claim; "+
			"got errored=%d injected=%d", len(s.Results), s.Errored, injected)
	}
	if s.GradedCells != 0 {
		t.Fatalf("a run with no implementation compared %d cells, which contradicts the premise of this "+
			"test", s.GradedCells)
	}

	if s.CounterfactualsNamed != 0 || s.MoneyKills != 0 || s.StructuralKills != 0 {
		t.Errorf("a run that compared ZERO cells credited %d kills (%d money, %d structural). A vector "+
			"the harness could not complete graded nothing, so it kills nothing — the strongest case of "+
			"the rule A2-22 applied to refusals.",
			s.CounterfactualsNamed, s.MoneyKills, s.StructuralKills)
	}
	if s.CorroborationsClaimed != 0 {
		t.Errorf("a run that compared ZERO cells credited %d corroboration claims, want 0",
			s.CorroborationsClaimed)
	}

	// SHED, NOT DROPPED. A number that silently disappears is a number nobody can
	// audit, so the withheld claims must be counted and printed.
	if s.ErroredCounterfactualsNamed == 0 {
		t.Errorf("the withheld kills were DROPPED rather than disclosed: ErroredCounterfactualsNamed " +
			"is 0 on a store whose vectors name kills")
	}
	if s.ErroredCorroborationsClaimed != injected {
		t.Errorf("claims shed by HARNESS-ERROR vectors: got %d, want %d (one per errored vector)",
			s.ErroredCorroborationsClaimed, injected)
	}
	// THE CORPUS-WIDE TRIPWIRE, and it MOVED WITH T116 (110 -> 113, 103 -> 106
	// money). Same three numbers as TestRefusedVectorDoesNotSilenceUnbackedEndToEnd
	// asserts for the pristine store, because this run sheds the whole corpus.
	if s.ErroredCounterfactualsNamed != 113 {
		t.Errorf("kills carried by HARNESS-ERROR vectors: got %d, want 113 (the whole committed corpus). "+
			"If a promotion moved the corpus, move this number and the 113 in "+
			"TestRefusedVectorDoesNotSilenceUnbackedEndToEnd together.", s.ErroredCounterfactualsNamed)
	}

	// AND THE RUN MUST SAY SO. An unbacked capability is what a reader acts on.
	if len(s.UncoveredGradedCapabilities) == 0 {
		t.Errorf("a run that compared nothing reports NO unbacked in_graded_domain capability, which " +
			"means the coverage report went QUIET on the case with the least evidence")
	}
	if !containsSubstring(s.FatalReasons, "MARKED in_graded_domain BUT NO PARITY VECTOR KILLS") {
		t.Errorf("no unbacked fatal reason on a run that graded nothing: %v", s.FatalReasons)
	}
	out := render(s)
	if !strings.Contains(out, "kills carried by HARNESS-ERROR vectors") {
		t.Errorf("the report does not disclose the kills it withheld from errored vectors:\n%s", out)
	}
	if s.ExitCode() != 2 {
		t.Errorf("a run with no implementation is exit 2 by construction; got %d", s.ExitCode())
	}
}

// injectOneCorroborationIntoEveryVector adds one ADMISSIBLE corroboration to
// every vector's provenance, in place, in a COPY of the store. It returns how
// many it wrote, so the caller can assert the fixture bit.
//
// The committed store carries ZERO corroborated_by entries, which is why the
// divergence between the two population rules has to be constructed rather than
// looked up. Numbers are decoded with UseNumber so no money or rate literal ever
// passes through a float on the round trip — the store is money, and a re-encoded
// amount that went through a float64 would be a non-negotiable violation even in
// a temp directory.
func injectOneCorroborationIntoEveryVector(t *testing.T, storeDir string) int {
	t.Helper()
	count := 0
	err := filepath.Walk(storeDir, func(path string, info os.FileInfo, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if info.IsDir() || filepath.Ext(path) != ".json" {
			return nil
		}
		switch filepath.Base(path) {
		case "PIN.json", "capabilities.json":
			return nil
		}
		raw, rerr := os.ReadFile(path)
		if rerr != nil {
			return rerr
		}
		dec := json.NewDecoder(bytes.NewReader(raw))
		dec.UseNumber()
		var m map[string]any
		if derr := dec.Decode(&m); derr != nil {
			return derr
		}
		prov, ok := m["provenance"].(map[string]any)
		if !ok {
			return fmt.Errorf("%s has no provenance object, so the injection would silently skip it and "+
				"the injected total would not equal the vector count", filepath.Base(path))
		}
		// embeddable-readme-ci-stdout attests principal and interest on a
		// REPAYMENT row; admitCorroborations refuses anything wider (T17-F2).
		prov["corroborated_by"] = []any{map[string]any{
			"source":   "embeddable-readme-ci-stdout",
			"row_kind": "REPAYMENT",
			"columns":  []any{"principal", "interest"},
			"note":     "injected by TestCorroborationsAreScopedToTheGradedPopulation",
		}}
		var buf bytes.Buffer
		enc := json.NewEncoder(&buf)
		enc.SetEscapeHTML(false)
		enc.SetIndent("", "  ")
		if eerr := enc.Encode(m); eerr != nil {
			return eerr
		}
		if werr := os.WriteFile(path, buf.Bytes(), 0o644); werr != nil {
			return werr
		}
		count++
		return nil
	})
	if err != nil {
		t.Fatalf("injectOneCorroborationIntoEveryVector: %v", err)
	}
	return count
}

// grepLines returns the lines of out containing needle, for an error message that
// shows what WAS printed rather than only what was expected.
func grepLines(out, needle string) string {
	var hits []string
	for _, line := range strings.Split(out, "\n") {
		if strings.Contains(line, needle) {
			hits = append(hits, strings.TrimSpace(line))
		}
	}
	if len(hits) == 0 {
		return "(no line contains " + needle + ")"
	}
	return strings.Join(hits, "\n")
}
