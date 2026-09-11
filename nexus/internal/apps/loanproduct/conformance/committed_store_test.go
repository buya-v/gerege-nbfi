package conformance

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// committedStoreRoot resolves the committed loanproduct vector store from the
// module layout, never from the working directory: `go test` runs with the
// package directory as cwd, so this is stable, and a test that resolved the
// store from anywhere else would grade a different corpus from the one
// conformance.sh grades.
func committedStoreRoot(t *testing.T) string {
	t.Helper()
	store := filepath.Join(repoRoot(t), ".softhouse", "vectors")
	if _, err := os.Stat(filepath.Join(store, LoanProductContext)); err != nil {
		t.Fatalf("the loanproduct vector directory is not where this test expects it (%s): %v",
			filepath.Join(store, LoanProductContext), err)
	}
	return store
}

// TestCommittedCorpusPassesTheReferenceImplementation grades the committed
// loanproduct corpus through the port inside `go test`, not only through the
// cmd/conformance binary. That is what makes Go's coverage instrument live:
//
//	go test -coverpkg=./internal/apps/loanproduct -coverprofile=/tmp/c.cov ./internal/apps/loanproduct/conformance/...
//
// pointed at the loanproduct port and run over THIS package reports which port
// code the golden-vector harness actually reaches. This package's other tests
// build hand-transcribed PROBES and grade them through gradeOne, so a port
// function that only a committed vector reaches reads 0.0% no matter how many
// vectors exist. Without a store-driven test, a vocabulary vector could look
// like it graded the decode while nothing measured that it reached
// AmortizationMethodFromStoredValue / PeriodFrequencyTypeFromStoredValue /
// DaysInYearTypeFromStoredValue and their StoredValue/Code/String methods.
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
		ContextFilter:      LoanProductContext,
		Pin:                pin,
		Registry:           reg,
		Implementation:     NewGoEvaluator(),
		ImplementationName: "loanproduct-go",
	}

	// ANTI-VACUITY. Every assertion below iterates the committed vectors, and an
	// empty corpus makes all of them pass over nothing (P-35).
	vectors, loadErrs, err := LoadStore(store, LoanProductContext)
	if err != nil {
		t.Fatalf("LoadStore refuses the committed loanproduct corpus: %v", err)
	}
	if len(loadErrs) != 0 {
		t.Fatalf("the committed loanproduct corpus has load errors: %v", loadErrs)
	}
	if len(vectors) == 0 {
		t.Fatal("ZERO loanproduct vectors loaded, so this control would pass while reaching nothing")
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
		t.Fatalf("the committed loanproduct corpus does not pass loanproduct-go: parity_fail=%d refused=%d inadmissible=%d errored=%d",
			s.ParityFail, s.Refused, s.Inadmissible, s.Errored)
	}
	if s.InvariantViolations != 0 {
		t.Fatalf("invariant violations = %d, want 0", s.InvariantViolations)
	}

	// Each of the six enum vocabularies is a decode rule this context grades, and
	// the observation that reaches each one is a vector whose declared capability
	// set names it. This is the same guard the savings, loan and charges
	// committed-store tests put on their dimensions, stated over the capability
	// dimension because loanproduct has one capture seam and six vocabularies: a
	// vocabulary whose last observing vector is deleted silently returns to 0.0%
	// coverage, so the deletion must instead be a failing test.
	present := map[string]bool{}
	for _, v := range vectors {
		for _, c := range v.CapabilitiesRequired {
			present[c] = true
		}
	}
	for _, want := range committedLoanProductVocabularies {
		if !present[want] {
			t.Errorf("the committed loanproduct corpus carries no vector exercising capability %q: "+
				"with none, the coverage of the decode behind it silently falls back to 0.0%%", want)
		}
	}
}

// committedLoanProductVocabularies are the capability-registry names for the six
// enum vocabularies the committed loanproduct corpus is expected to observe.
// The test fails if the corpus loses every vector that exercises one, because
// the decode behind it would then read 0.0% with nothing to say so.
var committedLoanProductVocabularies = []string{
	string(VocabularyAmortizationMethod),
	string(VocabularyInterestMethod),
	string(VocabularyInterestCalcPeriod),
	string(VocabularyPeriodFrequency),
	string(VocabularyDaysInMonth),
	string(VocabularyDaysInYear),
}
