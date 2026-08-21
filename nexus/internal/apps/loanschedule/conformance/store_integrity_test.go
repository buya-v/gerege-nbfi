package conformance

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// THE DEFECT THESE GUARDS EXIST FOR (T110, from T104's F-T104-3 against T90).
//
// A vector store containing ONE file copied under a second name — same case_id,
// same context — was graded twice and reported, on main's bytes:
//
//	parity vectors  PASS 43   FAIL 0
//	cells compared  5623 graded, 86 ungraded
//	inadmissible    0        harness errors 0
//	VERDICT: PASS (exit 0)
//
// against 42 / 5576 for the same store without the copy. No warning, no refusal,
// no fatal reason. Those two numbers are what every RESUME.md, gate write-up and
// postmortem in this program quotes as its evidence of what has been proven
// against the reference oracle, so a store that silently double-counts inflates
// exactly the number the program is judged by.
//
// WHY EVERY ASSERTION BELOW GOES THROUGH LoadStore AND Run, AND NEVER THROUGH
// DuplicateCaseIDs DIRECTLY. This file must COMPILE ON MAIN, because a guard that
// only compiles against the fix cannot be driven red on the bytes that had the
// defect, and "it passes on the branch" is then indistinguishable from "the check
// never ran" (P-22). LoadStore and Run both exist on main with these exact
// signatures; the whole file is therefore a valid main test, and on main it fails.
func duplicateStore(t *testing.T, dupName string) (dir, original, duplicate string) {
	t.Helper()
	dir = copyStore(t, storeRoot(t))
	original = filepath.Join("loanschedule", "P-00-baseline-6x7pct.json")
	duplicate = filepath.Join("loanschedule", dupName)
	raw, err := os.ReadFile(filepath.Join(dir, original))
	if err != nil {
		t.Fatalf("ReadFile %s: %v", original, err)
	}
	// Anti-vacuity: if the file we are copying does not actually carry the
	// case_id we are about to claim it duplicates, this fixture proves nothing.
	if !strings.Contains(string(raw), `"case_id": "P-00"`) {
		t.Fatalf("%s no longer declares case_id P-00; this fixture would be vacuous", original)
	}
	if err := os.WriteFile(filepath.Join(dir, duplicate), raw, 0o644); err != nil {
		t.Fatalf("WriteFile %s: %v", duplicate, err)
	}
	return dir, original, duplicate
}

func TestDuplicateCaseIDRefusesTheRun(t *testing.T) {
	root := repoRoot(t)
	pristine := storeRoot(t)

	// (0) THE CONTROL. Establishes that the store this test perturbs loads
	// cleanly and grades a non-zero amount of work. Without it, every refusal
	// below could be produced by a harness that refuses everything, and the guard
	// would be structurally incapable of distinguishing a working check from a
	// broken one.
	var baselineVectors int
	t.Run("control_unique_store_loads_and_grades", func(t *testing.T) {
		clean := copyStore(t, pristine)
		vectors, loadErrs, err := LoadStore(clean, "")
		if err != nil {
			t.Fatalf("a store with no duplicate case_id must load: %v", err)
		}
		if len(loadErrs) > 0 {
			t.Fatalf("unexpected load errors: %v", loadErrs)
		}
		if len(vectors) == 0 {
			t.Fatal("the control store loaded zero vectors; every assertion below would be vacuous")
		}
		baselineVectors = len(vectors)
		seen := map[string]string{}
		for _, v := range vectors {
			if prev, dup := seen[v.CaseID]; dup {
				t.Fatalf("the COMMITTED store already contains duplicate case_id %q (%s, %s)",
					v.CaseID, prev, v.Path)
			}
			seen[v.CaseID] = v.Path
		}
		impl, n, ierr := NewReplayImplementation(clean, "")
		if ierr != nil {
			t.Fatalf("NewReplayImplementation: %v", ierr)
		}
		if n == 0 {
			t.Fatal("the replay implementation learned no answers")
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: clean,
			Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
		})
		if s.GradedCells == 0 {
			t.Fatal("the control run graded zero cells; a later 'graded 0 cells' assertion would be vacuous")
		}
		if got := s.ExitCode(); got != 0 {
			t.Fatalf("control self-test over an unperturbed store: exit %d, want 0\n%s", got, render(s))
		}
		t.Logf("control: %d vectors, %d graded cells, exit 0", len(vectors), s.GradedCells)
	})

	// (1) LoadStore must REFUSE, and the refusal must name BOTH files. Naming one
	// would leave the reader hunting for the other, and naming neither would be a
	// refusal nobody can act on.
	t.Run("load_store_refuses_and_names_both_files", func(t *testing.T) {
		dir, original, duplicate := duplicateStore(t, "AAA-duplicate-caseid-of-P-00.json")
		vectors, _, err := LoadStore(dir, "")
		if err == nil {
			t.Fatalf("LoadStore accepted a store in which %s and %s both declare case_id P-00; "+
				"it loaded %d vectors and the run would have graded P-00 TWICE",
				original, duplicate, len(vectors))
		}
		msg := err.Error()
		for _, want := range []string{original, duplicate, "P-00", "REFUSED"} {
			if !strings.Contains(msg, want) {
				t.Errorf("the refusal must name %q; got: %s", want, msg)
			}
		}
		// It must not silently drop one instead.
		if len(vectors) != 0 {
			t.Errorf("a refused store must yield no vectors, got %d — a de-duplicated store is the "+
				"same lie told in the other direction", len(vectors))
		}
	})

	// (2) THE ONE THAT MATTERS: end to end, through Run, the run is refused
	// BEFORE grading. Asserting only "exit 2" would not distinguish a refusal
	// from grading the duplicate and then complaining, so this asserts that no
	// vector was graded and no cell was counted — the counts the program quotes.
	t.Run("run_refuses_before_any_vector_is_graded", func(t *testing.T) {
		dir, original, duplicate := duplicateStore(t, "AAA-duplicate-caseid-of-P-00.json")
		// The replay implementation is built from the PRISTINE store, exactly as
		// `-replay-store` does in production, so the refusal under test is the one
		// on StoreRoot and not an accident of the stand-in.
		impl, _, ierr := NewReplayImplementation(pristine, "")
		if ierr != nil {
			t.Fatalf("NewReplayImplementation: %v", ierr)
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: dir,
			Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
		})
		if got := s.ExitCode(); got != 2 {
			t.Fatalf("a duplicated store must be exit 2 (corpus unusable), got %d\n%s", got, render(s))
		}
		if len(s.Results) != 0 || s.GradedCells != 0 || s.ParityPass != 0 || s.SelfTestPass != 0 {
			t.Errorf("the refusal must fire BEFORE grading: got %d results, %d graded cells, "+
				"%d parity passes, %d self-test passes — the control graded %d vectors, so these "+
				"numbers were computed and could be quoted",
				len(s.Results), s.GradedCells, s.ParityPass, s.SelfTestPass, baselineVectors)
		}
		report := render(s)
		for _, want := range []string{original, duplicate, "DUPLICATE case_id"} {
			if !strings.Contains(report, want) {
				t.Errorf("the printed report must name %q; got:\n%s", want, report)
			}
		}
		if strings.Contains(report, "VERDICT: PASS") || strings.Contains(report, "SELF-TEST PASS") {
			t.Errorf("a duplicated store printed a PASS verdict:\n%s", report)
		}
	})

	// (3) The duplicate need not share a context directory. The report prints
	// CASE without CONTEXT, so two rows with one case_id in different directories
	// are indistinguishable to a reader and still add to the same headline totals.
	// A per-context check would let this through; the key is the case_id alone.
	t.Run("duplicate_across_context_directories_is_refused", func(t *testing.T) {
		dir := copyStore(t, pristine)
		original := filepath.Join("loanschedule", "P-00-baseline-6x7pct.json")
		raw, err := os.ReadFile(filepath.Join(dir, original))
		if err != nil {
			t.Fatalf("ReadFile: %v", err)
		}
		moved := strings.Replace(string(raw), `"context": "loanschedule"`, `"context": "`+SelfTestDir+`"`, 1)
		if moved == string(raw) {
			t.Fatalf("%s does not declare context loanschedule; this fixture would be vacuous", original)
		}
		duplicate := filepath.Join(SelfTestDir, "ZZZ-crossdir-duplicate-of-P-00.json")
		if err := os.WriteFile(filepath.Join(dir, duplicate), []byte(moved), 0o644); err != nil {
			t.Fatalf("WriteFile: %v", err)
		}
		_, _, err = LoadStore(dir, "")
		if err == nil {
			t.Fatalf("LoadStore accepted case_id P-00 declared by both %s and %s", original, duplicate)
		}
		for _, want := range []string{original, duplicate} {
			if !strings.Contains(err.Error(), want) {
				t.Errorf("the refusal must name %q; got: %s", want, err.Error())
			}
		}
	})

	// (4) The refusal is itself part of the harness's output, so it must be a
	// function of the store's contents and not of Go's map iteration order —
	// otherwise a reviewer diffing two runs of the refusal sees a spurious diff
	// and is trained to explain it away (the T90/T81 failure mode).
	t.Run("refusal_message_is_deterministic", func(t *testing.T) {
		dir := copyStore(t, pristine)
		// The three files to duplicate are DERIVED from the store, never named:
		// a hard-coded filename that has since been renamed turns this guard into
		// a t.Skip, which reads green and checks nothing (observed while writing
		// it — the first draft skipped on P-02-monthend-anchor.json).
		before, _, berr := LoadStore(dir, "")
		if berr != nil {
			t.Fatalf("the fixture store must load before it is perturbed: %v", berr)
		}
		if len(before) < 3 {
			t.Fatalf("need at least 3 vectors to build 3 duplicate groups, store has %d", len(before))
		}
		for _, v := range before[:3] {
			raw, rerr := os.ReadFile(filepath.Join(dir, v.Path))
			if rerr != nil {
				t.Fatalf("ReadFile %s: %v", v.Path, rerr)
			}
			dup := filepath.Join(filepath.Dir(v.Path), "DUP-"+filepath.Base(v.Path))
			if werr := os.WriteFile(filepath.Join(dir, dup), raw, 0o644); werr != nil {
				t.Fatalf("WriteFile: %v", werr)
			}
		}
		seen := map[string]int{}
		for i := 0; i < 50; i++ {
			_, _, err := LoadStore(dir, "")
			if err == nil {
				t.Fatal("three duplicated case_ids were accepted")
			}
			seen[err.Error()]++
		}
		if len(seen) != 1 {
			t.Errorf("the refusal message must be byte-identical across runs, got %d distinct messages",
				len(seen))
		}
		for msg := range seen {
			// Anti-vacuity: one distinct message is also what a message naming
			// NOTHING would produce, so assert it actually names all three groups.
			if n := strings.Count(msg, "is declared by 2 files"); n != 3 {
				t.Errorf("the refusal must name all 3 duplicated case_ids, it names %d: %s", n, msg)
			}
		}
	})
}
