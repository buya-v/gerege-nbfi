package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// moduleRoot walks up from the test package to the go.mod directory (nexus/).
func moduleRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("could not locate go.mod")
		}
		dir = parent
	}
}

// repoRoot is the directory that contains the nexus/ module.
func repoRoot(t *testing.T) string {
	return filepath.Dir(moduleRoot(t))
}

// committedStoreRoot resolves the committed working-capital vector store from
// the module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, WorkingCapitalContext)); err != nil {
		t.Fatalf("the workingcapital vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, WorkingCapitalContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// working-capital corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/workingcapital -coverprofile=/tmp/c.cov \
//	    ./internal/apps/workingcapital/conformance/...
//
// pointed at the workingcapital port and run over THIS package reports which
// port code the golden-vector harness actually reaches. Without a store-driven
// test in the package, every port function reads 0.0% regardless of how many
// vectors exist, and the six committed vectors look like they graded the
// balance read-back while nothing measured that they reached
// TotalPrincipalDue/PrincipalOutstanding/TotalOutstanding/UnrealizedIncomeFromDiscountFee.
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
		ContextFilter:      WorkingCapitalContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "workingcapital-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, WorkingCapitalContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed workingcapital corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed workingcapital corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO workingcapital vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed workingcapital corpus does not pass workingcapital-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// The balance read-back is what reaches the derive-don't-store balance
	// getters (PrincipalOutstanding, TotalOutstanding, UnrealizedIncomeFromDiscountFee,
	// ...). Assert both seams are committed, so a later deletion of either is a
	// failing test rather than a silent return to 0.0% conformance coverage.
	list, detail := 0, 0
	for _, v := range vectors {
		switch v.Oracle.Seam {
		case SeamWorkingCapitalLoansList:
			list++
		case SeamWorkingCapitalLoansDetail:
			detail++
		}
	}
	if list < 1 {
		t.Fatalf("committed loans-list vectors = %d, want at least the seeded list observation: "+
			"with none, the conformance coverage of the list row read silently falls back to 0.0%%", list)
	}
	if detail < 1 {
		t.Fatalf("committed loans-detail vectors = %d, want at least the seeded balance read-back: "+
			"with none, the conformance coverage of the derive-don't-store balance getters silently falls back to 0.0%%", detail)
	}

	// The discount-nonzero observation (OHWCCAP-DISCNONZERO-L01) is the only
	// committed capture that exercises the discount arithmetic at a NONZERO
	// discount: principal = disbursed + totalDiscountFee (103753 = 100000 + 3753).
	// The balance getters stay covered by the other detail vectors, so deleting it
	// would not by itself drop a function to 0.0%; what it would silently lose is
	// the only graded cell with totalDiscountFee != 0. Assert it is committed so
	// its deletion is a failing test rather than a quiet regression to grading the
	// discount at zero everywhere.
	discountNonzero := 0
	for _, v := range vectors {
		if strings.Contains(v.Provenance.CaptureRef, "wc-discount-nonzero") {
			discountNonzero++
		}
	}
	if discountNonzero < 1 {
		t.Fatalf("committed discount-nonzero vectors = %d, want the nonzero-discount observation "+
			"(capture .softhouse/capture/wc-discount-nonzero/): with none, every graded discount cell is zero", discountNonzero)
	}
}
