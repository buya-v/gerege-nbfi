package conformance

import (
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
	// kills (56 money, 6 structural) of the store's 110 (103 money, 7 structural).
	if s.RefusedCounterfactualsNamed != 62 {
		t.Errorf("kills carried by refused vectors: got %d, want 62", s.RefusedCounterfactualsNamed)
	}
	if s.CounterfactualsNamed != 48 || s.MoneyKills != 47 || s.StructuralKills != 1 {
		t.Errorf("credited kills: got %d (%d money, %d structural), want 48 (47 money, 1 structural)",
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
	if ps.CounterfactualsNamed != 110 || ps.MoneyKills != 103 || ps.StructuralKills != 7 {
		t.Errorf("the committed store's kill count moved: got %d (%d money, %d structural), "+
			"want 110 (103 money, 7 structural)",
			ps.CounterfactualsNamed, ps.MoneyKills, ps.StructuralKills)
	}
	if len(ps.UncoveredGradedCapabilities) != 0 {
		t.Errorf("the committed store reports unbacked capabilities %v", ps.UncoveredGradedCapabilities)
	}
}
