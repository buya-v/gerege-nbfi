package conformance

import (
	"fmt"
	"sort"
	"sync"
)

// WorkingCapitalEvaluator is what a working-capital implementation must be able
// to do for this harness to grade it. The graded surface is the list of
// working-capital loans (m_wc_loan). As of the pinned capture the table is
// empty, so the only observable result is an empty list; a loan-id request for
// a row that does not exist is an error, exactly as the port reads it.
type WorkingCapitalEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]WorkingCapitalEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a WorkingCapitalEvaluator available under name.
func Register(name string, e WorkingCapitalEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("workingcapital conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e WorkingCapitalEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (WorkingCapitalEvaluator, bool) {
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

// RegisteredNames lists every registered implementation.
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

// goEvaluator is the port-backed working-capital loan read. m_wc_loan is empty
// in the pinned capture, so it returns an empty list — the faithful transcription
// of what the oracle returned for GET /working-capital-loans.
type goEvaluator struct {
	loans []LoanExpect
}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() WorkingCapitalEvaluator {
	return goEvaluator{loans: []LoanExpect{}}
}

func (g goEvaluator) Evaluate(req Request) (Expect, error) {
	if req.LoanID > 0 {
		return Expect{}, fmt.Errorf("workingcapital: loan id %d not present in m_wc_loan (table is empty)", req.LoanID)
	}
	return Expect{Loans: g.loans, TotalElements: int64(len(g.loans))}, nil
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it invents a loan row
// that the empty m_wc_loan table cannot contain, so any list vector asserting
// the empty list goes red.
type wrongEvaluator struct{}

func (wrongEvaluator) Evaluate(req Request) (Expect, error) {
	if req.LoanID > 0 {
		return Expect{}, fmt.Errorf("workingcapital: loan id %d not present in m_wc_loan (table is empty)", req.LoanID)
	}
	return Expect{
		Loans:         []LoanExpect{{ID: "1", ExternalID: "SEED-WC-FAKE", Status: "ACTIVE"}},
		TotalElements: 1,
	}, nil
}

func init() {
	Register("workingcapital-go", NewGoEvaluator())
	RegisterWrong("workingcapital-wrong-phantom-loan",
		"invents a loan row the empty m_wc_loan table cannot contain, so any list vector asserting the empty list goes red",
		wrongEvaluator{})
}
