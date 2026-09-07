package conformance

import (
	"fmt"
	"sort"
	"sync"

	"github.com/gerege/nexus/internal/apps/cob"
)

// COBEvaluator is what a cob implementation must be able to do for this harness
// to grade it: given a business-step name, return that step's order (1..6) in
// the LOAN_CLOSE_OF_BUSINESS job.
type COBEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]COBEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a COBEvaluator available under name.
func Register(name string, e COBEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("cob conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e COBEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (COBEvaluator, bool) {
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

// goEvaluator grades the port's own DefaultLoanConfig: it derives the step-name
// to step-order mapping directly from cob.DefaultLoanConfig(), so a drift in the
// port's seeded order is exactly what the harness catches. No value is invented
// here.
type goEvaluator struct {
	order map[string]int64
}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() COBEvaluator {
	g := goEvaluator{order: map[string]int64{}}
	for _, s := range cob.DefaultLoanConfig().BusinessSteps {
		g.order[s.StepName] = s.StepOrder
	}
	return g
}

func (g goEvaluator) Evaluate(req Request) (Expect, error) {
	o, ok := g.order[req.StepName]
	if !ok {
		return Expect{}, fmt.Errorf("cob: step %q is not in the default LOAN_CLOSE_OF_BUSINESS configuration", req.StepName)
	}
	return Expect{StepOrder: o}, nil
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it returns each step's
// order shifted by one, so every order-asserting vector goes red. It exists so a
// graded_against row can name an executable defect.
type wrongEvaluator struct{ goEvaluator }

func (w wrongEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	e.StepOrder++
	return e, nil
}

func init() {
	Register("cob-go", NewGoEvaluator())
	RegisterWrong("cob-wrong-shift-order",
		"shifts every business-step order by one, so any vector that asserts the order goes red",
		wrongEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
}
