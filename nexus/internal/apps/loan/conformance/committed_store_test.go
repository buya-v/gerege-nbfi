package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed loan vector store from the module
// layout, never from the working directory: `go test` runs with the package
// directory as cwd, so this is stable, and a test that resolved the store from
// anywhere else would grade a different corpus from the one conformance.sh
// grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, LoanContext)); err != nil {
		t.Fatalf("the loan vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, LoanContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed loan
// corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/loan -coverprofile=/tmp/loan.cov ./internal/apps/loan/conformance/...
//
// pointed at the loan port and run over THIS package reports which port code
// the golden-vector harness actually reaches. This package's other tests build
// hand-transcribed PROBES and grade them through gradeOne, so a port function
// that only a committed vector reaches reads 0.0% no matter how many vectors
// exist. Without a store-driven test, a vector can look like it graded a rule
// while nothing measured that it reached the code implementing it.
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
		ContextFilter:      LoanContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "loan-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, LoanContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed loan corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed loan corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO loan vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed loan corpus does not pass loan-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// Every committed seam the corpus carries must keep at least one vector: a
	// seam with none is how a rule silently returns to 0.0% coverage. This is
	// the same guard the savings committed-store test puts on the hold-release
	// seam, generalised to the loan seams.
	seams := map[string]bool{}
	for _, v := range vectors {
		seams[v.Oracle.Seam] = true
	}
	for _, want := range committedLoanSeams {
		if !seams[want] {
			t.Errorf("the committed loan corpus carries no vector for seam %q: "+
				"with none, the coverage of the rule behind it silently falls back to 0.0%%", want)
		}
	}
}

// committedLoanSeams are the capture seams the committed loan corpus is expected
// to carry. Each names a money rule the corpus is supposed to observe; the test
// fails if a seam loses every vector.
var committedLoanSeams = []string{
	SeamLoanRepaymentAllocation,
	SeamLoanScheduleInterest,
	SeamLoanDisbursement,
	SeamLoanStatus,
	SeamLoanTransactionBalance,
	SeamLoanSummaryOutstanding,
	SeamLoanJournalEntryBatchBalance,
	SeamLoanScheduleAmortization,
	SeamLoanDelinquentDays,
	SeamLoanWriteOffFourBucket,
	SeamLoanTransactionReversal,
	SeamLoanWriteOffJournalEntries,
	SeamLoanChargeOffJournalEntries,
	SeamLoanChargedOffWriteOffJournalEntries,
	SeamLoanRepaymentJournalEntries,
	SeamLoanGoodwillCreditJournalEntries,
	SeamLoanChargedOffRepaymentJournalEntries,
	SeamLoanChargedOffMerchantRefundJournalEntries,
	SeamLoanAccrualJournalEntries,
	SeamLoanChargebackJournalEntries,
	SeamLoanCreditBalanceRefundJournalEntries,
	SeamLoanCapitalizedIncomeAmortizationJournalEntries,
	SeamLoanBuyDownFeeJournalEntries,
	SeamLoanChargeLifecycle,
	SeamLoanStatusTransition,
}
