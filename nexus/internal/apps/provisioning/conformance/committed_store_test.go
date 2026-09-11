package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed provisioning vector store from the
// module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, ProvisioningContext)); err != nil {
		t.Fatalf("the provisioning vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, ProvisioningContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// provisioning corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/provisioning -coverprofile=/tmp/c.cov ./internal/apps/provisioning/conformance/...
//
// pointed at the provisioning port and run over THIS package reports which port
// code the golden-vector harness actually reaches. Without a store-driven test
// in the package, every port function reads 0.0% regardless of how many vectors
// exist, and a reserve vector would look like it graded the arithmetic while
// nothing measured that it reached GenerateReserveEntries/PercentageOf.
//
// It is not a second opinion about the vectors: LoadStore, Admit and Run are
// the same functions the binary calls. It is the same grading, from the test
// target the coverage instrument needs.
func TestCommittedCorpusPassesTheReferenceImplementation(t *testing.T) {
	root := repoRoot(t)
	store := committedStoreRoot(t)

	pin, err := LoadPin(filepath.Join(root, ".softhouse", PinFileName))
	if err != nil {
		t.Fatalf("LoadPin: %v", err)
	}
	reg, err := LoadCapabilityRegistry(filepath.Join(root, ".softhouse", CapabilityFileName))
	if err != nil {
		t.Fatalf("LoadCapabilityRegistry: %v", err)
	}
	opts := Options{
		RepoRoot:           root,
		StoreRoot:          store,
		ContextFilter:      ProvisioningContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "provisioning-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, ProvisioningContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed provisioning corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed provisioning corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO provisioning vectors loaded, so this control would pass while reaching nothing")
	}
	for _, v := range vectors {
		if reasons := Admit(v, opts); len(reasons) > 0 {
			t.Errorf("%s is INADMISSIBLE: %s", v.CaseID, strings.Join(reasons, "; "))
		}
	}

	s, err := Run(context.Background(), opts)
	if err != nil {
		t.Fatalf("Run: %v", err)
	}
	if len(s.FatalReasons) != 0 {
		t.Fatalf("the committed corpus is fatal: %v", s.FatalReasons)
	}
	if s.VectorsLoaded == 0 {
		t.Fatal("VectorsLoaded is 0: the run graded nothing")
	}
	if bad := s.ParityFail + s.Refused + s.Inadmissible + s.Errored; bad != 0 {
		t.Fatalf("the committed provisioning corpus does not pass provisioning-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// Both seams are what distinguishes a category read from a reserve
	// computation, and each seam reaches different port code: the reserve seam is
	// what drives GenerateReserveEntries -> GenerateReserveEntriesWith ->
	// PercentageOf -> roundHalfAwayFromZero. Assert both observations are
	// committed, so a later deletion of one seam is a failing test rather than a
	// silent return to 0.0% coverage of that seam.
	categories := 0
	reserves := 0
	for _, v := range vectors {
		switch v.Oracle.Seam {
		case SeamProvisioningCategoryRead:
			categories++
		case SeamProvisioningEntryReserve:
			reserves++
		}
	}
	if categories < 1 {
		t.Fatalf("committed category-read vectors = %d, want at least one observation of the category aggregate: "+
			"with none, the conformance coverage of the category seam silently falls back to 0.0%%", categories)
	}
	if reserves < 1 {
		t.Fatalf("committed entry-reserve vectors = %d, want at least one observation of the reserve arithmetic: "+
			"with none, the conformance coverage of GenerateReserveEntries/PercentageOf silently falls back to 0.0%%", reserves)
	}

	// The multi-entry observation is the only shape that reaches the DISTINCT-KEY
	// branch of GenerateReserveEntriesWith: a request whose rows carry different
	// reserveKeys must produce several entries, so the map-insert path runs
	// rather than the sum path alone. Assert at least one such observation is
	// committed, so a later deletion is a failing test rather than a silent
	// return to 0.0% coverage of the distinct-key branch.
	multiEntry := 0
	for _, v := range vectors {
		if v.Oracle.Seam == SeamProvisioningEntryReserve && len(v.ExpectEntries) >= 2 {
			multiEntry++
		}
	}
	if multiEntry < 1 {
		t.Fatalf("committed multi-entry reserve vectors = %d, want the distinct-key observation: "+
			"with none, the conformance coverage of the distinct-key branch of GenerateReserveEntriesWith "+
			"silently falls back to 0.0%%", multiEntry)
	}
}
