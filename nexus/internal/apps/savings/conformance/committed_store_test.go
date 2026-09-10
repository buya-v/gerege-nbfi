package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed savings vector store from the
// module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, SavingsContext)); err != nil {
		t.Fatalf("the savings vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, SavingsContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// savings corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/savings -coverprofile=/tmp/c.cov ./internal/apps/savings/conformance/...
//
// pointed at the savings port and run over THIS package reports which port code
// the golden-vector harness actually reaches. Without a store-driven test in
// the package, every port function reads 0.0% regardless of how many vectors
// exist, and a hold vector would look like it graded the rule while nothing
// measured that it reached HeldOf/AvailableOf/AccountBalanceOf.
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
		ContextFilter:      SavingsContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "savings-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, SavingsContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed savings corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed savings corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO savings vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed savings corpus does not pass savings-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// The hold/release observation is what reaches HeldOf, AvailableOf and
	// AccountBalanceOf. Assert both observed states are committed, so a later
	// deletion of one is a failing test rather than a silent return to 0.0%
	// conformance coverage of the holds rule.
	holds := 0
	for _, v := range vectors {
		if v.Oracle.Seam == SeamSavingsHoldRelease {
			holds++
		}
	}
	if holds < 2 {
		t.Fatalf("committed hold-release vectors = %d, want the after-hold and after-release observations: "+
			"with fewer than two, the conformance coverage of the holds rule silently falls back to 0.0%%", holds)
	}
}
