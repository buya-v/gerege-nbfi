package conformance

import (
	"fmt"
	"sort"
	"sync"
)

// LoanProductEvaluator is what a loanproduct implementation must be able to do
// for this harness to grade it: given a stored enum value within a vocabulary,
// return the round-trip stored value, i18n code and enum name the port decodes
// it to.
type LoanProductEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]LoanProductEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a LoanProductEvaluator available under name.
func Register(name string, e LoanProductEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("loanproduct conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e LoanProductEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (LoanProductEvaluator, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	e, ok := impls[name]
	return e, ok
}

// IsRegisteredWrong reports whether name is a known-wrong implementation.
func IsRegisteredWrong(name string) (string, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	d, ok := wrong[name]
	return d, ok
}

// RegisteredNames lists every registered implementation, wrong ones included.
func RegisteredNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

// CorrectImplementationNames lists the registered implementations that are NOT
// declared wrong.
func CorrectImplementationNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		if _, bad := wrong[n]; !bad {
			out = append(out, n)
		}
	}
	sort.Strings(out)
	return out
}

// goEvaluator grades the port's own enum vocabularies: it decodes the stored
// value through the port's FromStoredValue and returns the port's own
// StoredValue()/Code()/String(). No value is invented here.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() LoanProductEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	e, ok := decodeVocabulary(req.Vocabulary, req.Stored)
	if !ok {
		return Expect{}, fmt.Errorf("loanproduct: stored %d does not decode in vocabulary %q", req.Stored, req.Vocabulary)
	}
	return e, nil
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it swaps the days-in-year
// DAYS_360 (stored 360) and DAYS_365 (stored 365) codes and names, the exact
// adjacent-member defect the day-count trap exists to catch. The two swapped
// vectors go red; every other vector stays green. It exists so a graded_against
// row can name an executable defect.
type wrongEvaluator struct{}

func (wrongEvaluator) Evaluate(req Request) (Expect, error) {
	if Vocabulary(req.Vocabulary) == VocabularyDaysInYear {
		switch req.Stored {
		case 360:
			return Expect{Stored: 360, Code: "DaysInYearType.days365", Name: "DAYS_365"}, nil
		case 365:
			return Expect{Stored: 365, Code: "DaysInYearType.days360", Name: "DAYS_360"}, nil
		}
	}
	return goEvaluator{}.Evaluate(req)
}

func init() {
	Register("loanproduct-go", NewGoEvaluator())
	RegisterWrong("loanproduct-wrong-swap-days360-365",
		"swaps the days-in-year DAYS_360 (360) and DAYS_365 (365) codes/names, so any vector asserting that mapping goes red",
		wrongEvaluator{})
}
