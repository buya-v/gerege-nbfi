package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed investor vector store from the
// module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, InvestorContext)); err != nil {
		t.Fatalf("the investor vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, InvestorContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// investor corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -count=1 -coverpkg=./internal/apps/investor -coverprofile=/tmp/c.cov ./internal/apps/investor/conformance/...
//
// pointed at the investor port and run over THIS package reports which port code
// the golden-vector harness actually reaches. Without a store-driven test in the
// package, every port function reads 0.0% regardless of how many vectors exist,
// and the settlement vector would look like it graded the derived-total rule
// while nothing measured that it reached DeriveTotalOutstanding.
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
		ContextFilter:      InvestorContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "investor-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, InvestorContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed investor corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed investor corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO investor vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed investor corpus does not pass investor-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// The settlement observation is what reaches DeriveTotalOutstanding (the
	// derived total_outstanding_minor cell) and the transfer-details snapshot.
	// Assert both seams are committed, so a later deletion of one is a failing
	// test rather than a silent return to 0.0% conformance coverage of the
	// derived-total rule (P-35: a guard that inspects nothing is an error).
	reads := 0
	settlements := 0
	for _, v := range vectors {
		switch v.Oracle.Seam {
		case SeamExternalAssetOwnerTransferRead:
			reads++
		case SeamExternalAssetOwnerTransferSettlement:
			settlements++
		}
	}
	if reads < 1 {
		t.Fatalf("committed transfer-read vectors = %d, want at least the row and empty-page observations: "+
			"with none, the read seam is ungraded and the coverage instrument reaches nothing", reads)
	}
	if settlements < 1 {
		t.Fatalf("committed transfer-settlement vectors = %d, want the settled observation: "+
			"with none, DeriveTotalOutstanding silently falls back to 0.0%% conformance coverage", settlements)
	}
}
