package conformance

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// storeRoot resolves the committed vector store from this test's own file
// location, never from the working directory. `go test` runs with the package
// directory as cwd, so a relative path here is stable; the point of stating it
// is that a test that resolved the store from somewhere else would be grading a
// different corpus from the one conformance.sh grades (T165, one context over).
func storeRoot(t *testing.T) string {
	t.Helper()
	root, err := filepath.Abs(filepath.Join("..", "..", "..", "..", "..", ".softhouse", "vectors"))
	if err != nil {
		t.Fatalf("resolving the store root: %v", err)
	}
	if _, err := os.Stat(filepath.Join(root, "PIN-ledger.json")); err != nil {
		t.Fatalf("the ledger pin is not where this test expects it (%s): %v", root, err)
	}
	return root
}

func repoRoot(t *testing.T) string {
	t.Helper()
	root, err := filepath.Abs(filepath.Join("..", "..", "..", "..", ".."))
	if err != nil {
		t.Fatalf("resolving the repo root: %v", err)
	}
	return root
}

func loadCommitted(t *testing.T) ([]*Vector, Options) {
	t.Helper()
	store := storeRoot(t)
	vs, errs, err := LoadStore(store, "")
	if err != nil {
		t.Fatalf("LoadStore refuses the committed ledger corpus: %v", err)
	}
	if len(errs) != 0 {
		t.Fatalf("the committed ledger corpus has load errors: %v", errs)
	}
	// ANTI-VACUITY. Every sub-test below iterates this slice, and an empty slice
	// makes all of them pass over nothing — the single shape every vacuous guard
	// this program has found shares (P-35).
	if len(vs) == 0 {
		t.Fatal("ZERO ledger vectors loaded. Every assertion in this file iterates that slice, so an " +
			"empty corpus would make this whole file pass while checking nothing")
	}
	pin, err := LoadPin(filepath.Join(store, PinFileName))
	if err != nil {
		t.Fatalf("LoadPin: %v", err)
	}
	reg, err := LoadCapabilityRegistry(filepath.Join(store, CapabilityFileName))
	if err != nil {
		t.Fatalf("LoadCapabilityRegistry: %v", err)
	}
	return vs, Options{
		RepoRoot:  repoRoot(t),
		StoreRoot: store,
		Pin:       pin,
		Registry:  reg,
	}
}

// TestCommittedCorpusIsAdmissible is the anti-no-op control for every refusal
// test below: if Admit refused everything, they would all pass and look
// identical.
func TestCommittedCorpusIsAdmissible(t *testing.T) {
	vs, opts := loadCommitted(t)
	for _, v := range vs {
		if reasons := Admit(v, opts); len(reasons) > 0 {
			t.Errorf("%s is INADMISSIBLE: %s", v.CaseID, strings.Join(reasons, "; "))
		}
	}
	t.Logf("%d committed ledger vectors, all admissible", len(vs))
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// corpus against the port and demands every vector pass.
func TestCommittedCorpusPassesTheReferenceImplementation(t *testing.T) {
	_, opts := loadCommitted(t)
	opts.Implementation = NewGoPoster()
	opts.ImplementationName = "ledger-go"
	s := Run(opts)
	if s.ParityFail+s.RefusalFail+s.Inadmissible+s.Errored != 0 || len(s.Fatal) != 0 {
		t.Fatalf("the committed corpus does not pass: parityFail=%d refusalFail=%d inadmissible=%d "+
			"errored=%d fatal=%v", s.ParityFail, s.RefusalFail, s.Inadmissible, s.Errored, s.Fatal)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations on the committed corpus: %d", s.InvariantViolations)
	}
	// THE MONEY CELL COUNT IS ASSERTED POSITIVELY. DEC-2 §5.5: "a ledger corpus
	// whose money cells only ever kill structurally has graded no amount". A
	// corpus that stopped comparing money would keep every vector count above
	// and lose only this one.
	if s.MoneyCells == 0 {
		t.Fatal("ZERO money cells were compared. Every count above can be green over a corpus that " +
			"grades no amount at all, which is the exact state this context was in before A2-15")
	}
	// AND THE INDEPENDENT-ASSERTION COUNT. Two invariants printing HOLD is not
	// two checks unless at least one of them could have gone red on its own.
	if s.IndependentAssertions == 0 {
		t.Fatal("ZERO independent invariant assertions. Every invariant that held did so as a " +
			"restatement of another, which is one assertion counted twice")
	}
	t.Logf("parity %d, oracle-refusal %d, %d cells (%d money), %d invariant assertions (%d independent)",
		s.ParityPass, s.RefusalPass, s.GradedCells, s.MoneyCells,
		s.InvariantAssertions, s.IndependentAssertions)
}

// TestEveryWrongImplementationIsKilled is DEC-2 precondition P-10 as a test:
// every REGISTERED wrong implementation must actually be caught by the committed
// corpus.
//
// WITHOUT IT, `RegisterWrong` IS DECORATION. A wrong implementation nothing
// kills is the same thing as a `graded_against` row nothing executes — the
// defect P-10 was added to close — one level further in.
func TestEveryWrongImplementationIsKilled(t *testing.T) {
	_, base := loadCommitted(t)
	names := RegisteredNames()
	killed := 0
	for _, name := range names {
		if _, bad := IsRegisteredWrong(name); !bad {
			continue
		}
		impl, ok := Lookup(name)
		if !ok {
			t.Fatalf("%s is declared wrong and is not registered", name)
		}
		opts := base
		opts.Implementation = impl
		opts.ImplementationName = name
		s := Run(opts)
		if !s.ExitWorthy() {
			t.Errorf("WRONG IMPLEMENTATION %q SURVIVES THE COMMITTED CORPUS. Either the corpus does not "+
				"discriminate it, or it is not actually wrong. Both are defects and neither may be left "+
				"as a registered-but-unkilled name", name)
			continue
		}
		killed++
	}
	if killed == 0 {
		t.Fatal("no wrong implementation was even attempted, so this test asserted nothing")
	}
	t.Logf("%d registered wrong implementations, all %d killed by the committed corpus", killed, killed)
}

// TestExemptionsAreRefused is the default-deny that this schema rests on.
func TestExemptionsAreRefused(t *testing.T) {
	vs, opts := loadCommitted(t)
	v := *vs[0]
	v.InvariantExemptions = []Exemption{{
		Invariant: "double_entry_balances",
		Reason:    "a reason long enough to satisfy any prose check, which is exactly the point",
	}}
	reasons := Admit(&v, opts)
	if len(reasons) == 0 {
		t.Fatal("a declared invariant_exemptions entry was ADMITTED. This schema has no grounding " +
			"classifier, so admitting one switches an invariant off with nothing checking that the " +
			"thing it excuses is visible in the record")
	}
	if !containsSubstring(reasons, "THIS SCHEMA ADMITS NONE") {
		t.Fatalf("refused, but not for the exemption: %s", strings.Join(reasons, "; "))
	}
}

// TestGlAccountTypeMayNotBeGraded locks the two halves of the glAccountType
// decision: the exclusion list is CLOSED to that one cell, and a vector that
// excludes it must say why in its own note.
func TestGlAccountTypeMayNotBeGraded(t *testing.T) {
	vs, opts := loadCommitted(t)

	t.Run("a_widened_exclusion_list_is_refused", func(t *testing.T) {
		v := *vs[0]
		legs := append([]ExpectLeg(nil), v.Expect.Legs...)
		if len(legs) == 0 {
			t.Skip("this vector asserts no legs")
		}
		legs[0].ExcludedFields = []string{"amount_minor"}
		v.Expect.Legs = legs
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "the only cell this schema permits") {
			t.Fatalf("excluding a money cell was not refused: %v", reasons)
		}
	})

	t.Run("an_exclusion_without_the_reason_in_the_note_is_refused", func(t *testing.T) {
		v := *vs[0]
		if !excludesType(&v) {
			t.Skip("this vector excludes nothing")
		}
		v.Note = "a note that says nothing about why a cell was excluded"
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "does not mention glAccountType") {
			t.Fatalf("a silent exclusion was admitted: %v", reasons)
		}
	})

	t.Run("no_committed_vector_names_it_as_a_divergent_cell", func(t *testing.T) {
		for _, v := range vs {
			for _, cf := range v.GradedAgainst {
				for _, c := range cf.DivergentCells {
					if c == "gl_account_type" {
						t.Errorf("%s names gl_account_type as a divergent cell; DEC-2 §5.2 requirement 7 "+
							"forbids it, because a red on an unstable cell demonstrates that the corpus "+
							"is not reproducible", v.CaseID)
					}
				}
			}
		}
	})
}

// TestCellVocabularyIsDerivedFromTheComparator is DEC-2 precondition P-4.
func TestCellVocabularyIsDerivedFromTheComparator(t *testing.T) {
	fields := CellFields()
	if len(fields) == 0 {
		t.Fatal("the comparator emitted no cell names, so the vocabulary is empty and IsCellField " +
			"would refuse every divergent_cells entry")
	}
	for _, want := range []string{
		"leg_count", "legs[].gl_account_id", "legs[].gl_account_code", "legs[].entry_side",
		"legs[].amount_minor", "total_debits_minor", "total_credits_minor",
		"refusal.http_status", "refusal.code", "refusal.message",
	} {
		if !IsCellField(want) {
			t.Errorf("the comparator does not emit %q, so no vector can name it", want)
		}
	}
	if IsCellField("gl_account_type") {
		t.Error("the comparator emits gl_account_type. It must not: the cell is unstable across " +
			"captures (A2-26) and this schema excludes it")
	}
	// A cell nothing compares must be refusable, or the whitelist means nothing
	// (T9-F1b).
	if IsCellField("office_running_balance") {
		t.Error("the comparator emits office_running_balance. GATE G-12 is open on that column and " +
			"A2-29 measured it to be a second source of truth; nothing may grade it")
	}
	t.Logf("cell vocabulary (%d): %s", len(fields), strings.Join(fields, ", "))
}

// TestContextAllowlist is DEC-2 precondition P-9 for the second schema.
func TestContextAllowlist(t *testing.T) {
	vs, opts := loadCommitted(t)
	v := *vs[0]
	v.Ctx = "loanschedule"
	v.Path = filepath.Join("loanschedule", filepath.Base(v.Path))
	if reasons := Admit(&v, opts); !containsSubstring(reasons, "not a context THIS SCHEMA grades") {
		t.Fatalf("a ledger vector claiming the loanschedule context was admitted: %v", reasons)
	}
	if IsSchemaContext("loanschedule") || IsSchemaContext("_selftest") {
		t.Fatal("this schema claims a context belonging to the other one")
	}
}

// TestInadmissibleProductsAreRefused is G-10 option (c).
func TestInadmissibleProductsAreRefused(t *testing.T) {
	vs, opts := loadCommitted(t)
	if len(opts.Pin.InadmissibleProductIDs) == 0 {
		t.Fatal("the pin denylists no product, so this test asserts nothing")
	}
	v := *vs[0]
	v.Request.ProductID = opts.Pin.InadmissibleProductIDs[0]
	v.Request.ProductType = "LOAN"
	v.Request.AccountingRule = "CASH_BASED"
	v.Request.SlotFamily = "CashLoanSlot"
	if reasons := Admit(&v, opts); !containsSubstring(reasons, "INADMISSIBLE PRODUCT denylist") {
		t.Fatalf("a vector taken from a denylisted product was admitted: %v", reasons)
	}
}

// TestCitationsMustResolve is T233's three-part rule, applied to this schema.
func TestCitationsMustResolve(t *testing.T) {
	vs, opts := loadCommitted(t)

	t.Run("a_dangling_capture_ref_is_refused", func(t *testing.T) {
		v := *vs[0]
		v.Provenance.CaptureRef = ".softhouse/capture/tierA-a2/out/NO-SUCH-ARTEFACT.json"
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "does not resolve under the graded") {
			t.Fatalf("a dangling citation was admitted: %v", reasons)
		}
	})

	t.Run("a_wrong_digest_is_refused", func(t *testing.T) {
		v := *vs[0]
		v.Provenance.CaptureSHA256 = strings.Repeat("0", 64)
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "has changed since the vector") {
			t.Fatalf("a citation whose digest does not match was admitted: %v", reasons)
		}
	})

	t.Run("an_empty_rerun_invariant_is_refused", func(t *testing.T) {
		v := *vs[0]
		v.Provenance.RerunInvariant = "   "
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "rerun_invariant is empty") {
			t.Fatalf("a citation with no re-run sentence was admitted: %v", reasons)
		}
	})
}

// TestPartTwoOfTheCitationCanFail is T243, closing A2-34's F-3.
//
// A2-34's charge was that part two RESOLVES TAUTOLOGICALLY: on LDG-01/02/03 the
// capture_case_id occurs only in the artefact's own file name, which the
// citation itself supplied, so the check "passes without demonstrating
// anything". The decision recorded in admit.go is to KEEP part two and pin its
// weakest branch. That decision is only honest if part two can be made to FAIL,
// in both of the two directions it now gates, and if the argument for keeping it
// is itself demonstrated rather than asserted. All three are asserted here.
func TestPartTwoOfTheCitationCanFail(t *testing.T) {
	vs, opts := loadCommitted(t)

	// The measurement the whole decision rests on, re-derived here so it cannot
	// go stale silently: exactly the pinned population resolves by name alone,
	// and it is not the whole corpus.
	var nameOnly, total int
	for _, v := range vs {
		for _, cr := range CitationResolutions(v, opts.RepoRoot) {
			total++
			if cr.Mode == CitationByNameOnly {
				nameOnly++
			}
		}
	}
	if total == 0 {
		t.Fatal("zero citations classified, so every assertion below is vacuous")
	}
	if nameOnly != CitationNameOnlyPinCount() {
		t.Fatalf("%d citations resolve FILE-NAME-ONLY and admit.go pins %d",
			nameOnly, CitationNameOnlyPinCount())
	}
	if nameOnly == total {
		t.Fatalf("all %d citations resolve by file name, so the classification separates nothing", total)
	}

	// DIRECTION 1 — INFLATION. A name-only citation that is not on the pin is
	// INADMISSIBLE. The vector is unchanged except for its case_id, so the only
	// thing that differs from the admitted control is pin membership.
	t.Run("an_unpinned_file_name_only_citation_is_refused", func(t *testing.T) {
		var subject *Vector
		for _, v := range vs {
			for _, cr := range CitationResolutions(v, opts.RepoRoot) {
				if cr.Mode == CitationByNameOnly && cr.Field == "provenance.capture_ref" {
					subject = v
				}
			}
		}
		if subject == nil {
			t.Skip("no file-name-only citation in the corpus; nothing to assert")
		}
		if reasons := Admit(subject, opts); len(reasons) != 0 {
			t.Fatalf("CONTROL: the pinned vector is not admitted, so the test below proves "+
				"nothing about the pin: %v", reasons)
		}
		v := *subject
		v.CaseID = "LDG-99-NOT-ON-THE-PIN"
		if reasons := Admit(&v, opts); !containsSubstring(reasons, "BY FILE NAME ONLY") {
			t.Fatalf("an unpinned file-name-only citation was admitted: %v", reasons)
		}
	})

	// DIRECTION 2 — DEFLATION. A pin that no longer describes the corpus is a
	// sentence nothing checks, and it is reported.
	t.Run("a_stale_pin_is_reported", func(t *testing.T) {
		loaded := map[string]bool{}
		var res []CitationResolution
		for _, v := range vs {
			loaded[v.CaseID] = true
			for _, cr := range CitationResolutions(v, opts.RepoRoot) {
				res = append(res, cr)
			}
		}
		if stale := StaleCitationPins(res, loaded); len(stale) != 0 {
			t.Fatalf("CONTROL: the committed corpus already has stale pins: %v", stale)
		}
		// Now claim the same citations resolved a STRONGER way. Every pinned row
		// must be reported, or the deflation arm is decoration.
		strong := make([]CitationResolution, 0, len(res))
		for _, cr := range res {
			if cr.Mode == CitationByNameOnly {
				cr.Mode = CitationBySidecar
			}
			strong = append(strong, cr)
		}
		stale := StaleCitationPins(strong, loaded)
		if len(stale) != CitationNameOnlyPinCount() {
			t.Fatalf("%d stale pins reported, wanted %d", len(stale), CitationNameOnlyPinCount())
		}
	})

	// THE ARGUMENT FOR KEEPING PART TWO, DEMONSTRATED RATHER THAN ASSERTED.
	// Point a citation at a DIFFERENT artefact and give it that artefact's
	// CORRECT sha256. The digest check is fully satisfied. Only part two
	// notices, so "the sha256 makes part two redundant" is false.
	t.Run("a_mis_cited_artefact_with_a_correct_digest_is_caught_only_by_part_two", func(t *testing.T) {
		var subject *Vector
		for _, v := range vs {
			if v.Provenance.CaptureRef != "" {
				subject = v
				break
			}
		}
		if subject == nil {
			t.Fatal("no vector carries a capture_ref")
		}
		// A real artefact from the same capture directory that is NOT this
		// vector's, chosen by walking the store's own citations.
		var otherRef string
		for _, v := range vs {
			if v.Provenance.CaptureRef != "" && v.Provenance.CaptureRef != subject.Provenance.CaptureRef &&
				!strings.Contains(v.Provenance.CaptureRef, subject.Provenance.CaptureCaseID) {
				otherRef = v.Provenance.CaptureRef
				break
			}
		}
		if otherRef == "" {
			t.Fatal("no second artefact to mis-cite")
		}
		raw, err := os.ReadFile(filepath.Join(opts.RepoRoot, otherRef))
		if err != nil {
			t.Fatalf("reading %s: %v", otherRef, err)
		}
		sum := sha256.Sum256(raw)
		v := *subject
		v.Provenance.CaptureRef = otherRef
		v.Provenance.CaptureSHA256 = hex.EncodeToString(sum[:])
		reasons := Admit(&v, opts)
		if containsSubstring(reasons, "has changed since the vector") {
			t.Fatalf("the digest check fired, so this case does not isolate part two: %v", reasons)
		}
		if !containsSubstring(reasons, "occurs neither in the bytes of") {
			t.Fatalf("a citation naming the WRONG artefact with the RIGHT digest was admitted, so "+
				"part two IS redundant and the decision in admit.go is wrong: %v", reasons)
		}
	})
}

// TestParityVectorMustNameAMoneyKill is DEC-2 §5.2 requirement 7, revision 4's
// conjunction.
func TestParityVectorMustNameAMoneyKill(t *testing.T) {
	vs, opts := loadCommitted(t)
	var parity *Vector
	for _, v := range vs {
		if v.Class == ClassParity {
			parity = v
			break
		}
	}
	if parity == nil {
		t.Fatal("no parity vector in the corpus, so this test asserts nothing")
	}
	v := *parity
	var structuralOnly []Counterfactual
	for _, cf := range v.GradedAgainst {
		if cf.Kind == "structural" {
			structuralOnly = append(structuralOnly, cf)
		}
	}
	if len(structuralOnly) == 0 {
		t.Skip("this vector names no structural kill to reduce to")
	}
	v.GradedAgainst = structuralOnly
	if reasons := Admit(&v, opts); !containsSubstring(reasons, "names no MONEY kill") {
		t.Fatalf("a parity vector whose kills are all structural was admitted: %v", reasons)
	}
}

// TestFloatTokensAreRefused is the raw-token scan, this schema's own copy.
func TestFloatTokensAreRefused(t *testing.T) {
	if err := RejectFloatTokens([]byte(`{"amount_minor": 100000.25}`)); err == nil {
		t.Fatal("a float token was accepted in a ledger vector")
	}
	if err := RejectFloatTokens([]byte(`{"amount_minor": "10000025"}`)); err != nil {
		t.Fatalf("an integer minor-unit STRING was refused: %v", err)
	}
}

// TestSplitsSumToWholeIsNotAlwaysARestatementOfDoubleEntry is the vacuity check
// this task nearly shipped without.
//
// On a journal entry with one leg on one side and N on the other, the
// leg-derived form of I-2 is character-for-character the equation I-1 asserts.
// Both print HOLD, and a reader counts two checks where there is one. The corpus
// must therefore contain at least one vector on which I-2 is INDEPENDENT.
func TestSplitsSumToWholeIsNotAlwaysARestatementOfDoubleEntry(t *testing.T) {
	_, opts := loadCommitted(t)
	opts.Implementation = NewGoPoster()
	opts.ImplementationName = "ledger-go"
	s := Run(opts)
	independent := 0
	for _, r := range s.Results {
		for _, iv := range r.Invariants {
			if iv.Name == "splits_sum_to_whole" && iv.Independent && iv.Assertions > 0 {
				independent++
			}
		}
	}
	if independent == 0 {
		t.Fatal("NO vector asserts splits_sum_to_whole INDEPENDENTLY of double_entry_balances. On a " +
			"one-against-N entry the two are the same equation, so a corpus without an independent " +
			"assertion reports two green invariant lines and has checked one thing")
	}
	t.Logf("%d vectors assert splits_sum_to_whole independently of double_entry_balances", independent)
}

func containsSubstring(reasons []string, needle string) bool {
	for _, r := range reasons {
		if strings.Contains(r, needle) {
			return true
		}
	}
	return false
}

func excludesType(v *Vector) bool {
	for _, l := range v.Expect.Legs {
		for _, f := range l.ExcludedFields {
			if f == "gl_account_type" {
				return true
			}
		}
	}
	return false
}
