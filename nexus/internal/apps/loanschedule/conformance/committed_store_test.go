package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/gerege/nexus/internal/apps/loanschedule"
)

// committedStoreRoot resolves the committed loanschedule vector store from the
// module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades. It reuses storeRoot, the package's one resolution rule,
// and only asserts the context directory is really there.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := storeRoot(t)
	if _, err := os.Stat(filepath.Join(store, LoanScheduleContext)); err != nil {
		t.Fatalf("the loanschedule vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, LoanScheduleContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// loanschedule corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/loanschedule -coverprofile=/tmp/c.cov ./internal/apps/loanschedule/conformance/...
//
// pointed at the port and run over THIS package reports which port code the
// golden-vector harness actually reaches. This harness is the oldest context and
// did not grow from the savings template, so it is shaped differently:
//
//   - Admit takes (vector, pin, repoRoot) rather than an Options value
//     (admit.go:103);
//   - the registered implementations are contract.ScheduleGenerators in
//     registry.go, and the reference is the port itself, built by
//     loanschedule.New() and registered as "loanschedule-go" in
//     cmd/conformance/impl_hook.go — which a test binary does not run, so this
//     test constructs the same implementation the binary registers;
//   - Run is grade.go:380, and the corpus's verdict is the report's
//     "LOAN SCHEDULE N mismatch" line, not savings' parity_fail=N.
//
// Before this test the package imported no port at all, so every port function
// read 0.0% from conformance no matter how many vectors existed. It is not a
// second opinion about the vectors: LoadStore, Admit and Run are the same
// functions the binary calls. It calls no port function to grade a rule — the
// only port symbol it touches is the constructor the binary itself calls — so
// it cannot manufacture coverage: remove the vectors and the coverage falls
// back to whatever the package's other tests reach.
func TestCommittedCorpusPassesTheReferenceImplementation(t *testing.T) {
	root := repoRoot(t)
	store := committedStoreRoot(t)

	pin, err := LoadPin(filepath.Join(store, "PIN.json"))
	if err != nil {
		t.Fatalf("LoadPin: %v", err)
	}

	// "up" is the harness input Run requires before it will grade a parity
	// vector (grade.go:478); it is the same value the package's own in-process
	// tests pass. This test is a coverage control, not a live oracle probe.
	opts := Options{
		RepoRoot:           root,
		StoreRoot:          store,
		ContextFilter:      LoanScheduleContext,
		Implementation:     loanschedule.New(),
		ImplementationName: "loanschedule-go",
		OracleProbe:        "up",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, LoanScheduleContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed loanschedule corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed loanschedule corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO loanschedule vectors loaded, so this control would pass while reaching nothing")
	}
	for _, v := range vectors {
		if reasons := Admit(v, pin, root); len(reasons) > 0 {
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
	if s.ParityPass == 0 {
		t.Fatal("ParityPass is 0: the run graded no oracle-observed vector")
	}
	// contrast with savings' parity_fail=N: this harness's counters are
	// parity/contract-refusal/self-test, and a wrong port is named by the
	// report's "LOAN SCHEDULE N mismatch" verdict line rather than parity_fail.
	if bad := s.ParityFail + s.ContractFail + s.SelfTestFail + s.Refused + s.Inadmissible + s.Errored; bad != 0 {
		t.Fatalf("the committed loanschedule corpus does not pass loanschedule-go: parity_fail=%d contract_fail=%d "+
			"self_test_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.ContractFail, s.SelfTestFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}
	if s.GradedCells == 0 {
		t.Fatal("GradedCells is 0: the run compared nothing, so its parity pass is vacuous")
	}

	// The parity population is the vector-driven part of the measurement, so
	// every class-PARITY vector in the store must have been graded and passed.
	// A later deletion of a vector is then a failing test rather than a silent
	// return to 0.0% coverage of the rule it exercised.
	parity := 0
	for _, v := range vectors {
		if v.Class == ClassParity {
			parity++
		}
	}
	if parity == 0 {
		t.Fatal("the committed corpus holds ZERO parity vectors, so nothing here grades an oracle observation")
	}
	if s.ParityPass != parity {
		t.Fatalf("parity vectors loaded = %d but ParityPass = %d: a parity vector was dropped or did not pass",
			parity, s.ParityPass)
	}
}
