package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed origination vector store from the
// module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, OriginationContext)); err != nil {
		t.Fatalf("the origination vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, OriginationContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// origination corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/origination -coverprofile=/tmp/c.cov ./internal/apps/origination/conformance/...
//
// pointed at the origination port and run over THIS package reports which port
// code the golden-vector harness actually reaches. Without a store-driven test
// in the package, every port function reads 0.0% regardless of how many vectors
// exist, and the three status vectors look like they graded the name→stored
// string mapping while nothing measured that they reached
// StoredValue/String/LoanOriginatorStatusFromString.
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
		ContextFilter:      OriginationContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "origination-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, OriginationContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed origination corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed origination corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO origination vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed origination corpus does not pass origination-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// The name→stored-string mapping is what reaches StoredValue/String. Assert
	// the corpus carries all three LoanOriginatorStatus vocabulary values, so a
	// later deletion of one is a failing test rather than a silent return to
	// 0.0% conformance coverage of the status mapping. The oracle stores the enum
	// name itself (there is no integer ordinal column), so request.name must
	// equal expect.stored for a faithful port.
	wantNames := map[string]bool{"ACTIVE": false, "PENDING": false, "INACTIVE": false}
	for _, v := range vectors {
		if v.Oracle.Seam != SeamLoanOriginatorStatus {
			t.Errorf("%s grades seam %q, want the one seam %q", v.CaseID, v.Oracle.Seam, SeamLoanOriginatorStatus)
		}
		if v.Expect.Stored != v.Request.Name {
			t.Errorf("%s: expect.stored %q != request.name %q; LoanOriginatorStatus is a STRING enum",
				v.CaseID, v.Expect.Stored, v.Request.Name)
		}
		if _, ok := wantNames[v.Request.Name]; ok {
			wantNames[v.Request.Name] = true
		}
	}
	for name, seen := range wantNames {
		if !seen {
			t.Errorf("committed vectors omit the %s status: with none, conformance coverage of the "+
				"name→stored mapping silently loses that vocabulary member", name)
		}
	}
}
