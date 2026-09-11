package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed cob vector store from the module
// layout, never from the working directory: `go test` runs with the package
// directory as cwd, so this is stable, and a test that resolved the store from
// anywhere else would grade a different corpus from the one conformance.sh
// grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, COBContext)); err != nil {
		t.Fatalf("the cob vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, COBContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed cob
// corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/cob -coverprofile=/tmp/c.cov ./internal/apps/cob/conformance/...
//
// pointed at the cob port and run over THIS package reports which port code the
// golden-vector harness actually reaches. Without a store-driven test in the
// package, every port function reads 0.0% regardless of how many vectors exist,
// and a step-order vector would look like it graded the rule while nothing
// measured that it reached cob.DefaultLoanConfig.
//
// It is not a second opinion about the vectors: LoadStore, Admit and Run are
// the same functions the binary calls. It is the same grading, from the test
// target the coverage instrument needs. It calls no port function directly, so
// it cannot manufacture coverage: remove the vectors and the coverage falls
// back to whatever the probes reach.
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
		ContextFilter:      COBContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "cob-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, COBContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed cob corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed cob corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO cob vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed cob corpus does not pass cob-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// The single graded seam is what reaches cob.DefaultLoanConfig: every vector
	// carries the step order the port seeds. Assert the committed corpus still
	// covers that seam and its capability, so a later deletion is a failing test
	// rather than a silent return to 0.0% conformance coverage of the ordering
	// rule.
	seamVectors := 0
	present := map[string]bool{}
	for _, v := range vectors {
		if v.Oracle.Seam == SeamCOBBusinessStepOrder {
			seamVectors++
		}
		for _, c := range v.CapabilitiesRequired {
			present[c] = true
		}
	}
	if seamVectors == 0 {
		t.Fatalf("committed %s vectors = 0: with none, the conformance coverage of "+
			"cob.DefaultLoanConfig silently falls back to 0.0%%", SeamCOBBusinessStepOrder)
	}
	for _, want := range committedCOBCapabilities {
		if !present[want] {
			t.Errorf("the committed cob corpus carries no vector exercising capability %q: "+
				"with none, the coverage of the ordering rule behind it silently falls back to 0.0%%", want)
		}
	}
}

// committedCOBCapabilities are the capability-registry names for what the
// committed cob corpus is expected to observe. The single entry is the
// business-step order rule; the test fails if the corpus loses every vector
// that exercises it.
var committedCOBCapabilities = []string{
	"business-step-order",
}
