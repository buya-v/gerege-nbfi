package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed collateral vector store from the
// module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, CollateralContext)); err != nil {
		t.Fatalf("the collateral vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, CollateralContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// collateral corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/collateral -coverprofile=/tmp/c.cov ./internal/apps/collateral/conformance/...
//
// pointed at the collateral port and run over THIS package reports which port
// code the golden-vector harness actually reaches. Without a store-driven test
// in the package, every port function reads 0.0% regardless of how many vectors
// exist, and a valuation vector would look like it graded the arithmetic while
// nothing measured that it reached Total/TotalCollateral.
//
// It is not a second opinion about the vectors: LoadStore, Admit and Run are the
// same functions the binary calls. It is the same grading, from the test target
// the coverage instrument needs.
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
		ContextFilter:      CollateralContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "collateral-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, CollateralContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed collateral corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed collateral corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO collateral vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed collateral corpus does not pass collateral-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// Count the committed observations per seam. The valuation seam is the one
	// that reaches the port's money arithmetic (ClientCollateral.Total /
	// TotalCollateral); a corpus that lost its valuation vectors would still pass
	// every assertion above while the conformance coverage of the valuation rule
	// silently fell back to 0.0%. Pin each seam so a deletion is a failing test.
	product, link, client, valuation := 0, 0, 0, 0
	for _, v := range vectors {
		switch v.Oracle.Seam {
		case SeamCollateralProductRead:
			product++
		case SeamCollateralLinkRead:
			link++
		case SeamClientCollateralRead:
			client++
		case SeamClientCollateralValuationRead:
			valuation++
		}
	}
	if valuation < 2 {
		t.Fatalf("committed valuation vectors = %d, want at least the seed (CL-04) and non-round (CL-06) observations: "+
			"with fewer, the conformance coverage of Total/TotalCollateral silently falls back to 0.0%%", valuation)
	}
	if product < 2 {
		t.Fatalf("committed product vectors = %d, want at least the seed (CL-01) and non-round (CL-05) reads", product)
	}
	if link < 1 {
		t.Fatalf("committed link vectors = %d, want at least CL-02", link)
	}
	if client < 1 {
		t.Fatalf("committed client-collateral vectors = %d, want at least CL-03", client)
	}
}
