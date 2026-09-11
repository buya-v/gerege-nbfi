package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed parties vector store from the
// module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, PartiesContext)); err != nil {
		t.Fatalf("the parties vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, PartiesContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// parties corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/parties -coverprofile=/tmp/c.cov ./internal/apps/parties/conformance/...
//
// pointed at the parties port and run over THIS package reports which port code
// the golden-vector harness actually reaches. The map records the
// committed-store test as ABSENT before this file existed, so every port
// function read 0.0% from the graded corpus regardless of how many vectors
// exist, and an ordinals vector would look like it graded the rule while nothing
// measured that it reached ClientStatus.StoredValue or either sibling table.
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
		ContextFilter:      PartiesContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "parties-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, PartiesContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed parties corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed parties corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO parties vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed parties corpus does not pass parties-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// Each of the three enum vocabularies is graded through its own capture seam
	// and its own decode table. Assert every seam still carries at least one
	// committed vector, so deleting a vocabulary's vectors is a failing test
	// rather than a silent return to 0.0% graded coverage of that ordinal table.
	bySeam := map[string]int{}
	for _, v := range vectors {
		bySeam[v.Oracle.Seam]++
	}
	for _, seam := range []string{SeamClientStatus, SeamLegalForm, SeamGroupingStatus, SeamDisplayName} {
		if bySeam[seam] == 0 {
			t.Fatalf("no committed vector grades seam %q: with none, the conformance coverage of that "+
				"vocabulary silently falls back to 0.0%%", seam)
		}
	}
}
