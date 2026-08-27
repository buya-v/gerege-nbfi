package conformance

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	ledgerconf "github.com/gerege/nexus/internal/apps/ledger/conformance"
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

// crossContextDuplicateStore copies the store and plants a second declaration of
// case_id P-00 in a DIFFERENT context directory (_selftest), so the duplicate is
// invisible to any check scoped to one context — and to any check that applies
// -context before it counts.
func crossContextDuplicateStore(t *testing.T, pristine string) (dir, original, duplicate string) {
	t.Helper()
	dir = copyStore(t, pristine)
	original = filepath.Join("loanschedule", "P-00-baseline-6x7pct.json")
	raw, err := os.ReadFile(filepath.Join(dir, original))
	if err != nil {
		t.Fatalf("ReadFile: %v", err)
	}
	moved := strings.Replace(string(raw), `"context": "loanschedule"`, `"context": "`+SelfTestDir+`"`, 1)
	if moved == string(raw) {
		t.Fatalf("%s does not declare context loanschedule; this fixture would be vacuous", original)
	}
	if !strings.Contains(moved, `"case_id": "P-00"`) {
		t.Fatalf("%s no longer declares case_id P-00; this fixture would be vacuous", original)
	}
	duplicate = filepath.Join(SelfTestDir, "ZZZ-crossdir-duplicate-of-P-00.json")
	if err := os.WriteFile(filepath.Join(dir, duplicate), []byte(moved), 0o644); err != nil {
		t.Fatalf("WriteFile: %v", err)
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
		dir, original, duplicate := crossContextDuplicateStore(t, pristine)
		_, _, err := LoadStore(dir, "")
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

	// (5) THE FILTER NARROWS WHAT IS GRADED, NOT WHAT IS CHECKED (T123, closing
	// T119's F-T119-1).
	//
	// T110 documented its key as "the case_id ALONE, store-wide" and sub-test (3)
	// above proves that for an UNFILTERED run. It was not true under -context:
	// LoadStore applied contextFilter before it collected, so the census only ever
	// saw the contexts being graded. Measured on T110's own bytes, with the same
	// cross-context duplicate this sub-test plants:
	//
	//	no filter              -> exit 2, refused, 1 DUPLICATE line
	//	-context=loanschedule  -> exit 0, parity vectors PASS 42, 0 DUPLICATE lines
	//
	// A store defect visible from one angle and not another is the worse kind: the
	// run that hides it is the one somebody quotes, and no reader of that run's
	// report has anything to be suspicious of.
	t.Run("duplicate_outside_the_context_filter_is_still_refused", func(t *testing.T) {
		dir, original, duplicate := crossContextDuplicateStore(t, pristine)

		// Anti-vacuity: the filter must genuinely EXCLUDE the directory the
		// duplicate was planted in. If -context=loanschedule did not narrow the
		// store, this would be sub-test (3) wearing a different name.
		if got := filepath.Dir(duplicate); got == "loanschedule" {
			t.Fatalf("the duplicate was planted in %q, inside the filter; nothing here would be tested", got)
		}
		clean := copyStore(t, pristine)
		filtered, _, ferr := LoadStore(clean, "loanschedule")
		if ferr != nil {
			t.Fatalf("the clean store must load under -context=loanschedule: %v", ferr)
		}
		unfiltered, _, uerr := LoadStore(clean, "")
		if uerr != nil {
			t.Fatalf("the clean store must load unfiltered: %v", uerr)
		}
		if len(filtered) == 0 {
			t.Fatal("-context=loanschedule loaded zero vectors; every assertion below would be vacuous")
		}
		if len(filtered) >= len(unfiltered) {
			t.Fatalf("-context=loanschedule did not narrow the store (%d of %d vectors), so the "+
				"duplicate is not outside the filter and this sub-test proves nothing",
				len(filtered), len(unfiltered))
		}

		vectors, _, err := LoadStore(dir, "loanschedule")
		if err == nil {
			t.Fatalf("LoadStore with -context=loanschedule accepted a store in which %s and %s both "+
				"declare case_id P-00: it loaded %d vectors and reported a clean run. The census must "+
				"be taken over the whole store, before the filter", original, duplicate, len(vectors))
		}
		for _, want := range []string{original, duplicate, "P-00", "REFUSED"} {
			if !strings.Contains(err.Error(), want) {
				t.Errorf("the filtered refusal must name %q; got: %s", want, err.Error())
			}
		}
		if len(vectors) != 0 {
			t.Errorf("a refused store must yield no vectors, got %d", len(vectors))
		}

		// End to end through Run, with the filter set: refused before grading.
		impl, _, ierr := NewReplayImplementation(pristine, "")
		if ierr != nil {
			t.Fatalf("NewReplayImplementation: %v", ierr)
		}
		s := mustRun(t, Options{
			RepoRoot: root, StoreRoot: dir, ContextFilter: "loanschedule",
			Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
		})
		if got := s.ExitCode(); got != 2 {
			t.Fatalf("a filtered run over a cross-context duplicate must be exit 2, got %d\n%s",
				got, render(s))
		}
		if len(s.Results) != 0 || s.GradedCells != 0 || s.ParityPass != 0 || s.SelfTestPass != 0 {
			t.Errorf("the filtered refusal must fire BEFORE grading: got %d results, %d graded cells, "+
				"%d parity passes, %d self-test passes — the control graded %d vectors, so these "+
				"numbers were computed and could be quoted",
				len(s.Results), s.GradedCells, s.ParityPass, s.SelfTestPass, baselineVectors)
		}
		// Anti-vacuity: exit 2 has many causes. Assert this run reached it for THIS
		// reason, named in the report, rather than for any of the other eight.
		report := render(s)
		for _, want := range []string{original, duplicate, "DUPLICATE case_id"} {
			if !strings.Contains(report, want) {
				t.Errorf("the filtered report must name %q; got:\n%s", want, report)
			}
		}
	})

	// (6) THE OUTER SORT IN LoadStore IS COVERED (T123, closing T119's F-T119-2).
	//
	// The comment on that sort used to say it ran before the duplicate check "so
	// that the refusal itself names its files in a deterministic order". T119's
	// mutation M5 deleted the sort entirely and sub-test (4) still passed 50/50,
	// which means the stated reason was not the operative one — the refusal's
	// ordering comes from sortedKeys and sort.Strings inside DuplicateCaseIDs.
	// The reason has been corrected in the source. This sub-test supplies what was
	// missing: a test that the sort's REAL job — putting the report's rows in
	// (context, case_id) order rather than in os.ReadDir's on-disk order — is done.
	//
	// The fixture is built so the two orders DISAGREE: the file that sorts FIRST by
	// filename carries the case_id that sorts LAST. Deleting the sort therefore
	// turns this red, where deleting it turned nothing red before.
	t.Run("ordering_is_by_context_then_case_id", func(t *testing.T) {
		const (
			ctxDirName = "loanschedule"
			firstFile  = "aaa-ordering-probe.json" // first on disk, LAST by case_id
			lastFile   = "zzz-ordering-probe.json" // last on disk, FIRST by case_id
			firstCase  = "AAA-ordering-probe"      // expected row 0, from lastFile
			lastCase   = "ZZZ-ordering-probe"      // expected row 1, from firstFile
		)
		// Two REAL vectors from the committed store, so the fixture cannot drift
		// away from what the loader actually accepts. Both must declare the same
		// context, or the first sort key decides and case_id is never consulted.
		before, _, berr := LoadStore(pristine, "")
		if berr != nil {
			t.Fatalf("the committed store must load: %v", berr)
		}
		var src []*Vector
		for _, v := range before {
			if v.Context == ctxDirName {
				src = append(src, v)
			}
			if len(src) == 2 {
				break
			}
		}
		if len(src) < 2 {
			t.Fatalf("need 2 vectors declaring context %q to build the fixture, found %d",
				ctxDirName, len(src))
		}

		dir := t.TempDir()
		ctxDir := filepath.Join(dir, ctxDirName)
		if err := os.MkdirAll(ctxDir, 0o755); err != nil {
			t.Fatalf("MkdirAll: %v", err)
		}
		write := func(v *Vector, name, newCase string) {
			raw, err := os.ReadFile(filepath.Join(pristine, v.Path))
			if err != nil {
				t.Fatalf("ReadFile %s: %v", v.Path, err)
			}
			from := `"case_id": "` + v.CaseID + `"`
			to := `"case_id": "` + newCase + `"`
			out := strings.Replace(string(raw), from, to, 1)
			if out == string(raw) {
				t.Fatalf("%s does not render its case_id as %s; the fixture would be vacuous",
					v.Path, from)
			}
			if err := os.WriteFile(filepath.Join(ctxDir, name), []byte(out), 0o644); err != nil {
				t.Fatalf("WriteFile %s: %v", name, err)
			}
		}
		write(src[0], firstFile, lastCase)
		write(src[1], lastFile, firstCase)

		// Anti-vacuity: assert the two orders really do disagree on this platform.
		// If os.ReadDir ever stopped returning entries in filename order, an
		// unsorted LoadStore might return the right answer by accident and this
		// guard would pass while checking nothing.
		onDisk, err := os.ReadDir(ctxDir)
		if err != nil {
			t.Fatalf("ReadDir: %v", err)
		}
		if len(onDisk) != 2 || onDisk[0].Name() != firstFile || onDisk[1].Name() != lastFile {
			t.Fatalf("the fixture is not discriminating: os.ReadDir returned %v, want [%s %s]",
				onDisk, firstFile, lastFile)
		}

		got, loadErrs, err := LoadStore(dir, "")
		if err != nil {
			t.Fatalf("the ordering fixture must load: %v", err)
		}
		if len(loadErrs) > 0 {
			t.Fatalf("unexpected load errors: %v", loadErrs)
		}
		if len(got) != 2 {
			t.Fatalf("expected 2 vectors, got %d", len(got))
		}
		if got[0].CaseID != firstCase || got[1].CaseID != lastCase {
			t.Errorf("LoadStore must order rows by (context, case_id), not by filename: got [%s %s] "+
				"from files [%s %s], want [%s %s]. On-disk order is the REVERSE of case_id order in "+
				"this fixture, so this is what an unsorted loader returns",
				got[0].CaseID, got[1].CaseID, got[0].Path, got[1].Path, firstCase, lastCase)
		}
	})
}

// TestStoreFileCensus drives every mode of the enumerator disagreement RED in
// process, so a later rewrite of LoadStore cannot reopen one silently.
//
// THE DEFECT (T120, closing T143's M-5). The shell float guard enumerates the
// store with `find -name '*.json' -type f` — recursive, case-sensitive, no
// symlink following — and LoadStore reads ONE LEVEL DEEP matching the suffix
// bytewise. The two disagree about what the store contains, and before T154
// NOTHING COMPARED THEIR COUNTS. Measured on the pre-fix harness with the
// committed corpus otherwise intact, every row exit 0 with no warning:
//
//	symlinked extra context holding a float   42 parity / 5576 cells
//	a vector one directory too deep           42 parity / 5576 cells
//	T154-UPPER.JSON holding a float           42 parity / 5576 cells
//	P-00 and p-00 both present                43 parity / 5623 cells
//	NFC and NFD spellings of one case_id      44 parity / 5670 cells
//
// The last two are the dangerous pair: they do not hide a defect, they INFLATE
// the two numbers this program quotes as its evidence of coverage.
//
// EVERY SUB-TEST ASSERTS THE REFUSAL'S OWN WORDS, not merely that an error came
// back. A store defect refused for an unrelated reason is a check that has
// quietly stopped being the check it claims to be.
func TestStoreFileCensus(t *testing.T) {
	pristine := storeRoot(t)

	// ANTI-VACUITY, first and unconditionally: the committed store must pass the
	// census. Without this row every refusal below could be the census refusing
	// everything, and the suite would look identical.
	t.Run("the_committed_store_is_accounted_for", func(t *testing.T) {
		vectors, loadErrs, err := LoadStore(pristine, "")
		if err != nil {
			t.Fatalf("the committed store must pass the census: %v", err)
		}
		if len(loadErrs) != 0 {
			t.Fatalf("unexpected load errors: %v", loadErrs)
		}
		// A2-15: the committed store now carries a SECOND SCHEMA's vectors, whose
		// loader lives in nexus/internal/apps/ledger/conformance. LoadStore hands
		// those files over rather than loading them, so this direct call has to
		// supply what LoadStore itself supplies -- otherwise the sub-test asserts
		// that the census refuses a store the harness accepts, which is a check
		// measuring the test's own omission.
		//
		// THE PATHS ARE DERIVED, NOT LISTED. LedgerFilePaths walks the store and
		// answers "which files declare the ledger schema", so a ledger vector
		// added or removed later needs no edit here. A hard-coded list would go
		// stale on the next promotion and would go stale SILENTLY, since a
		// missing entry reads as a census refusal rather than as a stale test.
		ledgerPaths, lerr := ledgerconf.LedgerFilePaths(pristine)
		if lerr != nil {
			t.Fatalf("the ledger half of the committed store could not be enumerated: %v", lerr)
		}
		if err := StoreFileCensus(pristine, vectors, nil, ledgerPaths...); err != nil {
			t.Fatalf("StoreFileCensus refuses the committed store: %v", err)
		}
		// ANTI-VACUITY ON THE HAND-OVER ITSELF. If LedgerFilePaths ever returned
		// nothing, the line above would degrade into the pre-A2-15 call and pass
		// only because the ledger vectors had vanished -- the deflation shape this
		// program keeps paying for. The committed store carries ledger vectors, so
		// an empty answer here is an ERROR.
		if len(ledgerPaths) == 0 {
			t.Fatal("LedgerFilePaths found NO ledger vector in the committed store. Either the ledger " +
				"corpus has been deleted, or the schema probe has stopped recognising it; both make the " +
				"census call above pass for the wrong reason")
		}
		t.Logf("the census accounts for every .json under %s across %d loaded vectors and %d handed to "+
			"the ledger schema", pristine, len(vectors), len(ledgerPaths))
	})

	// A refusal, its required words, and the fixture that produces it.
	refuses := func(t *testing.T, mutate func(t *testing.T, dir string), wants ...string) {
		t.Helper()
		dir := copyStore(t, pristine)
		mutate(t, dir)
		_, _, err := LoadStore(dir, "")
		if err == nil {
			t.Fatal("LoadStore ACCEPTED the store. Before T154 this is exactly what happened, and the run " +
				"then reported a parity count over a set of files that is not the set on disk")
		}
		for _, w := range wants {
			if !strings.Contains(err.Error(), w) {
				t.Errorf("the refusal must say %q; it said: %v", w, err)
			}
		}
		t.Logf("refused: %v", err)
	}

	write := func(t *testing.T, path, body string) {
		t.Helper()
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			t.Fatalf("MkdirAll: %v", err)
		}
		if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
			t.Fatalf("WriteFile %s: %v", path, err)
		}
	}
	// A real vector re-cased, so the fixture cannot drift from what the loader
	// actually accepts.
	recased := func(t *testing.T, dir, destRel, newCaseID string) {
		t.Helper()
		src := filepath.Join(dir, "loanschedule", "P-00-baseline-6x7pct.json")
		raw, err := os.ReadFile(src)
		if err != nil {
			t.Fatalf("ReadFile: %v", err)
		}
		out := strings.Replace(string(raw), `"case_id": "P-00"`, `"case_id": "`+newCaseID+`"`, 1)
		if out == string(raw) {
			t.Fatal(`P-00-baseline-6x7pct.json no longer renders its case_id as "case_id": "P-00"; ` +
				"this fixture would be vacuous")
		}
		write(t, filepath.Join(dir, destRel), out)
	}

	t.Run("F1_a_symlinked_context_directory", func(t *testing.T) {
		refuses(t, func(t *testing.T, dir string) {
			outside := t.TempDir()
			write(t, filepath.Join(outside, "HIDDEN.json"), "{\n  \"n\": 3.6\n}\n")
			if err := os.Symlink(outside, filepath.Join(dir, "extra")); err != nil {
				t.Fatalf("Symlink: %v", err)
			}
		}, "SYMLINK", "extra")
	})

	t.Run("F2_a_subdirectory_of_a_context_directory", func(t *testing.T) {
		refuses(t, func(t *testing.T, dir string) {
			recased(t, dir, filepath.Join("loanschedule", "sub", "NESTED.json"), "T154-NESTED")
		}, "directory INSIDE a context directory", "loanschedule/sub")
	})

	t.Run("F3_an_uppercase_JSON_extension", func(t *testing.T) {
		refuses(t, func(t *testing.T, dir string) {
			write(t, filepath.Join(dir, "loanschedule", "T154-UPPER.JSON"), "{\n  \"n\": 3.6\n}\n")
		}, "DID NOT LOAD", "T154-UPPER.JSON")
	})

	t.Run("F4_case_only_case_id_variants", func(t *testing.T) {
		refuses(t, func(t *testing.T, dir string) {
			recased(t, dir, filepath.Join("loanschedule", "T154-lowercase-p00.json"), "p-00")
		}, "differing only in letter case", `"P-00"`, `"p-00"`)
	})

	t.Run("F5_NFC_and_NFD_spellings_of_one_case_id", func(t *testing.T) {
		refuses(t, func(t *testing.T, dir string) {
			// U+00E9 as one code point, and e + U+0301 as two. Two distinct
			// case_ids that render identically in the report.
			recased(t, dir, filepath.Join("loanschedule", "T154-nfc.json"), "P-NFC-é")
			recased(t, dir, filepath.Join("loanschedule", "T154-nfd.json"), "P-NFC-é")
		}, "[A-Za-z0-9._-]+", "T154-nfc.json", "T154-nfd.json")
	})

	t.Run("M5_a_json_at_the_store_root", func(t *testing.T) {
		// NO FLOAT IN IT. The point of this row is structural: the shell guard
		// has nothing to find here even when it is working, so a refusal can
		// only be the census's.
		refuses(t, func(t *testing.T, dir string) {
			write(t, filepath.Join(dir, "T154-ROOT-CLEAN.json"), "{\n  \"n\": 6\n}\n")
		}, "STORE ROOT", "never float-checked by Go", "T154-ROOT-CLEAN.json")
	})

	t.Run("an_allowlisted_root_file_is_float_checked", func(t *testing.T) {
		// BELT AND BRACES, AND SAID SO. LoadPin and LoadCapabilityRegistry
		// already call RejectFloatTokens, so this is not the closure of M-5 —
		// but they are called from Run, and this check runs under LoadStore
		// alone, which is how every test in this package reaches the store.
		refuses(t, func(t *testing.T, dir string) {
			path := filepath.Join(dir, "PIN.json")
			raw, err := os.ReadFile(path)
			if err != nil {
				t.Fatalf("ReadFile: %v", err)
			}
			out := strings.Replace(string(raw), `"significant_digits": 19`, `"significant_digits": 19.0`, 1)
			if out == string(raw) {
				t.Fatal("PIN.json no longer renders significant_digits as an integer 19; fixture vacuous")
			}
			write(t, path, out)
		}, "FLOAT TOKEN", "PIN.json")
	})

	t.Run("a_census_over_no_files_is_an_error", func(t *testing.T) {
		if err := StoreFileCensus(t.TempDir(), nil, nil); err == nil {
			t.Fatal("the census returned no error over an EMPTY store root: a census that inspects " +
				"nothing accounts for everything, which is the vacuous pass this check exists not to be")
		}
	})

	// A2-23 — THE STORE-SHAPE HALF OF A2-20's FIX.
	//
	// A2-20 closed the VECTOR-ADMISSION half of this defect: a FILE declaring an
	// unknown context is refused at Admit (admit.go:139, the
	// "not a context this harness grades" message). A2-20 measured, and left
	// standing as a residual, that `mkdir .softhouse/vectors/ledger/` WITH
	// NOTHING IN IT still gave exit 0, VERDICT PASS: nothing ever reaches Admit
	// for an empty directory, because LoadStore's own loop over that directory's
	// entries (vector.go's LoadStore) produces zero iterations when os.ReadDir
	// returns zero files, so no vector is loaded, no LoadError is recorded, and
	// the directory itself is unaccounted for anywhere the harness looks.
	//
	// The four sub-tests below drive that gap RED on four different SHAPES —
	// three of them new (empty, dotfile-only, README-only) and the fourth
	// (nested empty) already covered by a PRE-EXISTING rule, which the
	// sub-test's own name and assertion say plainly. A fifth is the P-72
	// negative control: a KNOWN context directory that happens to be empty must
	// NOT be refused, or the census would make it impossible to promote the
	// first vector of a brand-new context. A sixth drives a TYPE this task's
	// rule was not built around — a directory name differing from a known
	// context only by letter case.
	t.Run("A2-23_unknown_empty_top_level_directory_is_refused", func(t *testing.T) {
		refuses(t, func(t *testing.T, dir string) {
			if err := os.MkdirAll(filepath.Join(dir, "A2-23-unknown-empty"), 0o755); err != nil {
				t.Fatalf("MkdirAll: %v", err)
			}
		}, "STORE ROOT", "A2-23-unknown-empty", "not a context ANY schema grades")
	})

	t.Run("A2-23_unknown_directory_holding_only_a_dotfile_is_refused", func(t *testing.T) {
		refuses(t, func(t *testing.T, dir string) {
			write(t, filepath.Join(dir, "A2-23-unknown-dotfile", ".gitkeep"), "")
		}, "STORE ROOT", "A2-23-unknown-dotfile", "not a context ANY schema grades")
	})

	t.Run("A2-23_unknown_directory_holding_only_a_README_is_refused", func(t *testing.T) {
		refuses(t, func(t *testing.T, dir string) {
			write(t, filepath.Join(dir, "A2-23-unknown-readme", "README.md"), "# not a vector\n")
		}, "STORE ROOT", "A2-23-unknown-readme", "not a context ANY schema grades")
	})

	// THIS SHAPE WAS ALREADY COVERED BEFORE A2-23, AND THIS SUB-TEST SAYS SO
	// RATHER THAN CLAIMING CREDIT FOR IT. A nested EMPTY directory inside a
	// KNOWN context directory is caught by the PRE-EXISTING "directory INSIDE a
	// context directory" rule (T154/T120), which fires on the WalkDir directory
	// NODE itself and is unconditional on the directory's contents — so it was
	// never blind to emptiness the way the top-level check was. Included to
	// discharge the P-76 duty to drive a shape not built around this task's own
	// rule; the assertion below is the OLD nested-directory message, not the
	// new unknown-context-directory one, which is how the sub-test proves the
	// rule did not need to change for this shape.
	t.Run("A2-23_nested_empty_directory_was_already_refused_by_a_pre_existing_rule", func(t *testing.T) {
		refuses(t, func(t *testing.T, dir string) {
			if err := os.MkdirAll(filepath.Join(dir, "loanschedule", "A2-23-nested-empty"), 0o755); err != nil {
				t.Fatalf("MkdirAll: %v", err)
			}
		}, "directory INSIDE a context directory", "loanschedule/A2-23-nested-empty")
	})

	// THE NEGATIVE CONTROL (P-72): a KNOWN context directory that happens to be
	// EMPTY must NOT be refused by the new check — only an UNKNOWN name is a
	// defect. Without this row, the three RED sub-tests above could be passing
	// because the census now refuses every empty directory, known or not, and
	// that would make the corpus impossible to grow into: promoting the first
	// vector of a brand-new context always starts from an empty directory.
	t.Run("A2-23_a_known_context_directory_left_empty_is_not_flagged_as_unknown", func(t *testing.T) {
		dir := copyStore(t, pristine)
		if err := os.RemoveAll(filepath.Join(dir, "ledger")); err != nil {
			t.Fatalf("RemoveAll: %v", err)
		}
		if err := os.MkdirAll(filepath.Join(dir, "ledger"), 0o755); err != nil {
			t.Fatalf("MkdirAll: %v", err)
		}
		if _, _, err := LoadStore(dir, ""); err != nil {
			t.Fatalf("LoadStore refused a store whose only defect is an EMPTY KNOWN context "+
				"directory, which is not a defect the new check exists to report: %v", err)
		}
	})

	// A P-76 TYPE PROBE: a directory named "LEDGER" (uppercase) is a case-only
	// variant of the real context "ledger" and must still be refused as
	// UNKNOWN, matching the exact-case rule storeRootNonVectorFiles already
	// states for root-level FILES ("on a case-insensitive filesystem the two
	// names address one file, and on a case-sensitive one they address two").
	// Built from scratch (t.TempDir, not copyStore) rather than alongside a
	// real "ledger" directory, because MEASURED LIVE on this host (macOS,
	// default APFS) `mkdir .softhouse/vectors/LEDGER` alongside an existing
	// `ledger/` fails outright with "File exists" — the filesystem itself is
	// case-insensitive and will not hold both names as distinct entries, so a
	// fixture that tried to create both would never reach the code under test.
	// A second .json is planted in a genuinely-known context purely so the
	// census's own anti-vacuity floor ("a census over no files is an error",
	// tested above) does not fire first and mask the assertion this sub-test
	// exists to make.
	t.Run("A2-23_case_variant_of_a_known_context_name_is_still_unknown", func(t *testing.T) {
		dir := t.TempDir()
		write(t, filepath.Join(dir, "loanschedule", "A2-23-seenjson-anchor.json"), "{}")
		write(t, filepath.Join(dir, "LEDGER", "README.md"), "# not a vector\n")
		if _, _, err := LoadStore(dir, ""); err == nil {
			t.Fatal("LoadStore accepted a store whose only ledger-shaped directory is \"LEDGER\" " +
				"(uppercase): the known-context check must be exact-case, matching the exact-case " +
				"rule this file already states for root-level files")
		}
	})
}

// THE DEFECT THIS GUARDS (A2-19 finding F1; reproduced independently by the
// driver, and a third time by A2-20 before a line of the fix was written).
//
// `context` used to be constrained only to be NON-EMPTY (admit.go:115) and to
// EQUAL ITS OWN DIRECTORY NAME (admit.go:119-120). No allowlist existed, and both
// constraints are satisfied by a file copy. Copy any promoted loanschedule parity
// vector into a new `ledger/` directory, change `case_id` and `context` and
// nothing else, and the harness on main's bytes reported:
//
//	DRIVER-F1-PROBE   parity   path_a_e...   PASS   47 cells
//	parity vectors    PASS 44   FAIL 0
//	cells compared    5711 graded
//	VERDICT: PASS (exit 0) — 44 parity vectors match the pinned reference oracle
//
// against 43 / 5664 for the same store without the copy. "43 parity vectors,
// 5664 cells" is what "the Go port matches the reference oracle" MEANS in this
// program — it is the number every parity claim rests on — and it was inflatable
// by `cp` plus two string edits.
//
// The inflation is the smaller half. The fake vector sat in `ledger/` while
// grading a LOAN SCHEDULE, so the report read as GL/ledger coverage that does not
// exist: precisely the claim DEC-2 is being written to make honestly.
//
// WHY THIS TEST GOES THROUGH Run AND NOT THROUGH Admit ALONE. The defect was
// never "Admit returned the wrong slice"; it was "the headline number moved". A
// unit assertion on Admit cannot see 44, and 44 is the thing that had to stop
// happening. The sub-tests below therefore assert on the SUMMARY: the parity
// count, the graded-cell count and the exit code.
func TestUnknownContextIsInadmissible(t *testing.T) {
	root := repoRoot(t)
	pristine := storeRoot(t)

	// The probe is built the way the driver built it: read a real promoted parity
	// vector and change exactly two fields. Every step is anti-vacuity checked,
	// because a replacement that silently matched nothing would leave this test
	// planting a duplicate (which a different guard catches) and reporting green
	// for the wrong reason.
	source := filepath.Join("loanschedule", "P-00-baseline-6x7pct.json")
	raw, err := os.ReadFile(filepath.Join(pristine, source))
	if err != nil {
		t.Fatalf("ReadFile %s: %v", source, err)
	}
	withID := strings.Replace(string(raw), `"case_id": "P-00"`, `"case_id": "DRIVER-F1-PROBE"`, 1)
	if withID == string(raw) {
		t.Fatalf("%s no longer declares case_id P-00; this fixture would plant a duplicate instead "+
			"of an unknown context, and would prove nothing about the context guard", source)
	}
	probe := strings.Replace(withID, `"context": "loanschedule"`, `"context": "ledger"`, 1)
	if probe == withID {
		t.Fatalf("%s no longer declares context loanschedule; this fixture would be vacuous", source)
	}
	// Exactly two lines differ from the original. If a future edit to the source
	// vector makes this fixture differ in more, the refusal under test could be
	// attributable to something other than the context.
	if n := countDifferingLines(string(raw), probe); n != 2 {
		t.Fatalf("the probe must differ from %s in exactly the 2 lines case_id and context, it "+
			"differs in %d; the refusal would not be attributable to the context alone", source, n)
	}
	if !IsSchemaContext("loanschedule") || IsSchemaContext("ledger") {
		t.Fatalf("SchemaContexts() must contain loanschedule and must NOT contain ledger, it is %v; "+
			"every assertion below depends on that", SchemaContexts())
	}

	impl, _, ierr := NewReplayImplementation(pristine, "")
	if ierr != nil {
		t.Fatalf("NewReplayImplementation: %v", ierr)
	}
	runOn := func(t *testing.T, dir string) *Summary {
		t.Helper()
		return mustRun(t, Options{
			RepoRoot: root, StoreRoot: dir,
			Implementation: impl, ImplementationName: "replay", SelfTestMode: true,
		})
	}

	// (0) THE CONTROL. Establishes the numbers the perturbed runs are compared
	// against, from the store rather than from a literal — a hard-coded 43 in a
	// test goes stale the day a vector is promoted, and a stale expectation is
	// repaired by editing the number, which is how a guard stops guarding.
	clean := copyStore(t, pristine)
	control := runOn(t, clean)
	if got := control.ExitCode(); got != 0 {
		t.Fatalf("the pristine store must grade clean before it is perturbed, got exit %d\n%s",
			got, render(control))
	}
	if control.ParityPass == 0 || control.GradedCells == 0 {
		t.Fatalf("the control graded %d parity vectors over %d cells; with zero of either, no "+
			"assertion below could distinguish a working guard from a harness that grades nothing",
			control.ParityPass, control.GradedCells)
	}

	// (1) THE DRIVER'S PROBE, IN ITS PARITY FORM. This is the exact reproduction:
	// a loanschedule parity vector filed as `ledger`.
	t.Run("a_parity_vector_copied_into_an_unknown_context_is_refused", func(t *testing.T) {
		dir := copyStore(t, pristine)
		if err := os.MkdirAll(filepath.Join(dir, "ledger"), 0o755); err != nil {
			t.Fatalf("MkdirAll: %v", err)
		}
		planted := filepath.Join("ledger", "DRIVER-F1-PROBE.json")
		if err := os.WriteFile(filepath.Join(dir, planted), []byte(probe), 0o644); err != nil {
			t.Fatalf("WriteFile: %v", err)
		}

		s := runOn(t, dir)
		if got := s.ExitCode(); got != 2 {
			t.Fatalf("a vector declaring an unknown context must make the run UNUSABLE (exit 2), "+
				"got exit %d\n%s", got, render(s))
		}
		if s.Inadmissible != 1 {
			t.Errorf("want exactly 1 inadmissible vector, got %d", s.Inadmissible)
		}
		// THE POINT OF THE WHOLE TEST: the headline number must not move.
		if s.ParityPass != control.ParityPass {
			t.Errorf("the parity count moved from %d to %d — the copied vector was counted, which "+
				"is the defect (measured on main: 43 -> 44)", control.ParityPass, s.ParityPass)
		}
		if s.GradedCells != control.GradedCells {
			t.Errorf("the graded-cell count moved from %d to %d — the copied vector was graded, "+
				"which is the defect (measured on main: 5664 -> 5711)",
				control.GradedCells, s.GradedCells)
		}
		report := render(s)
		if strings.Contains(report, "VERDICT: PASS") {
			t.Errorf("a store containing a mislabelled context printed a PASS verdict:\n%s", report)
		}
		for _, want := range []string{planted, "is not a context this harness grades", "INADMISSIBLE"} {
			if !strings.Contains(report, want) {
				t.Errorf("the report must name %q; got:\n%s", want, report)
			}
		}
	})

	// (2) THE SAME COPY, FILED WHERE IT BELONGS, IS ADMITTED — so the refusal in
	// (1) is attributable to the CONTEXT and to nothing else about the file.
	//
	// Without this control, (1) is also what a harness that refused every planted
	// file would produce, and the guard would be structurally incapable of telling
	// a context check from a paranoid one.
	t.Run("the_same_bytes_in_the_right_context_are_admitted", func(t *testing.T) {
		dir := copyStore(t, pristine)
		planted := filepath.Join("loanschedule", "DRIVER-F1-PROBE.json")
		if err := os.WriteFile(filepath.Join(dir, planted), []byte(withID), 0o644); err != nil {
			t.Fatalf("WriteFile: %v", err)
		}
		s := runOn(t, dir)
		if got := s.ExitCode(); got != 0 {
			t.Fatalf("the same vector in its own context must still grade, got exit %d\n%s",
				got, render(s))
		}
		if s.ParityPass != control.ParityPass+1 {
			t.Fatalf("the copy in loanschedule/ must be graded as a 44th parity vector "+
				"(%d+1), got %d — if it is not admissible here, sub-test (1) proves nothing about "+
				"the context", control.ParityPass, s.ParityPass)
		}
	})

	// (3) THE CONTRACT-REFUSAL FORM, WHICH IS WHY THE CHECK IS AT ADMISSION AND
	// NOT AT THE COMPARATOR.
	//
	// A contract-refusal vector consults no oracle comparator at all — its
	// expectation is derived from the frozen contract's own doc comments. So a
	// refusal phrased as "the comparator for this class does not exist for this
	// context" would let this form straight through. Measured on main: admitted,
	// PASS, exit 0, contract-refusal 4 -> 5 and cells 5664 -> 5665.
	t.Run("a_contract_refusal_vector_in_an_unknown_context_is_refused_too", func(t *testing.T) {
		dir := copyStore(t, pristine)
		refSource := filepath.Join("loanschedule", "REFUSE-01-actual-actual-ungraded.json")
		refRaw, rerr := os.ReadFile(filepath.Join(pristine, refSource))
		if rerr != nil {
			t.Fatalf("ReadFile %s: %v", refSource, rerr)
		}
		refProbe := strings.Replace(string(refRaw),
			`"case_id": "REFUSE-01-actual-actual-ungraded"`, `"case_id": "DRIVER-F1-PROBE-REFUSAL"`, 1)
		refProbe = strings.Replace(refProbe, `"context": "loanschedule"`, `"context": "ledger"`, 1)
		if n := countDifferingLines(string(refRaw), refProbe); n != 2 {
			t.Fatalf("the contract-refusal probe must differ in exactly 2 lines, it differs in %d", n)
		}
		if err := os.MkdirAll(filepath.Join(dir, "ledger"), 0o755); err != nil {
			t.Fatalf("MkdirAll: %v", err)
		}
		planted := filepath.Join("ledger", "DRIVER-F1-PROBE-REFUSAL.json")
		if err := os.WriteFile(filepath.Join(dir, planted), []byte(refProbe), 0o644); err != nil {
			t.Fatalf("WriteFile: %v", err)
		}
		s := runOn(t, dir)
		if got := s.ExitCode(); got != 2 {
			t.Fatalf("a contract-refusal vector in an unknown context must be exit 2, got %d\n%s",
				got, render(s))
		}
		if s.ContractPass != control.ContractPass {
			t.Errorf("the contract-refusal count moved from %d to %d (measured on main: 4 -> 5)",
				control.ContractPass, s.ContractPass)
		}
		if s.GradedCells != control.GradedCells {
			t.Errorf("the graded-cell count moved from %d to %d (measured on main: 5664 -> 5665)",
				control.GradedCells, s.GradedCells)
		}
	})

	// (4) THE EMPTY-CONTEXT MESSAGE IS NOT DOUBLED. A vector with no context at
	// all has ONE defect and must report one, not that defect plus a derived echo
	// of it — a refusal that lists two problems for one cause trains its reader to
	// discount refusals.
	t.Run("an_empty_context_reports_one_defect_not_two", func(t *testing.T) {
		pin, perr := LoadPin(filepath.Join(pristine, "PIN.json"))
		if perr != nil {
			t.Fatalf("LoadPin: %v", perr)
		}
		v := &Vector{Schema: VectorSchemaV1, CaseID: "X", Context: "", Class: ClassParity,
			DEC1Revision: pin.DEC1Revision, Path: filepath.Join("loanschedule", "X.json")}
		problems := Admit(v, pin, root)
		if !containsSubstring(problems, "context is empty") {
			t.Errorf("an empty context must be named as such, got %v", problems)
		}
		if containsSubstring(problems, "is not a context this harness grades") {
			t.Errorf("an empty context must not ALSO be reported as an unknown context, got %v",
				problems)
		}
	})
}

// countDifferingLines is the fixtures' anti-vacuity measure: how many lines of a
// and b are not equal, treating a length difference as a difference on every
// extra line. It exists so a fixture can assert it perturbed EXACTLY what it
// meant to perturb.
func countDifferingLines(a, b string) int {
	la, lb := strings.Split(a, "\n"), strings.Split(b, "\n")
	n := 0
	for i := 0; i < len(la) || i < len(lb); i++ {
		var x, y string
		if i < len(la) {
			x = la[i]
		}
		if i < len(lb) {
			y = lb[i]
		}
		if x != y {
			n++
		}
	}
	return n
}
