package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed branch vector store from the
// module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, BranchContext)); err != nil {
		t.Fatalf("the branch vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, BranchContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// branch corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/branch -coverprofile=/tmp/c.cov ./internal/apps/branch/conformance/...
//
// pointed at the branch port and run over THIS package reports which port code
// the golden-vector harness actually reaches. Without a store-driven test in
// the package, every port function reads 0.0% regardless of how many vectors
// exist, and a money vector would look like it graded the rule while nothing
// measured that it reached CashierTxnTypeFromID / MinorUnitsFromDecimalText /
// FoldCashierSummary.
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
		ContextFilter:      BranchContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "branch-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, BranchContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed branch corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed branch corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO branch vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed branch corpus does not pass branch-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// The cashier-transaction movement observation is what reaches
	// CashierTxnTypeFromID and MinorUnitsFromDecimalText. Assert at least one
	// committed movement vector, so a later deletion is a failing test rather
	// than a silent return to 0.0% conformance coverage of the exact-money path.
	movements := 0
	// The cashier-summary observation is what reaches FoldCashierSummary and
	// NetCash. Assert at least one committed summary vector, so a later deletion
	// is a failing test rather than a silent return to 0.0% coverage of the fold.
	summaries := 0
	// The teller-status observation is what reaches TellerStatus.StoredValue.
	// Assert at least one committed teller-status vector, so a later deletion is
	// a failing test rather than a silent return to 0.0% coverage of the stored
	// state mapping.
	tellerStatuses := 0
	for _, v := range vectors {
		switch v.Oracle.Seam {
		case SeamCashierTxnAmount:
			movements++
		case SeamCashierSummary:
			summaries++
		case SeamTellerStatus:
			tellerStatuses++
		}
	}
	if movements < 1 {
		t.Fatalf("committed cashier-txn-amount vectors = %d, want the movement observations: "+
			"with none, the conformance coverage of CashierTxnTypeFromID/MinorUnitsFromDecimalText silently falls back to 0.0%%", movements)
	}
	if summaries < 1 {
		t.Fatalf("committed cashier-summary vectors = %d, want the summary observations: "+
			"with none, the conformance coverage of FoldCashierSummary/NetCash silently falls back to 0.0%%", summaries)
	}
	if tellerStatuses < 1 {
		t.Fatalf("committed teller-status vectors = %d, want the stored-state observation: "+
			"with none, the conformance coverage of TellerStatus.StoredValue silently falls back to 0.0%%", tellerStatuses)
	}
}
