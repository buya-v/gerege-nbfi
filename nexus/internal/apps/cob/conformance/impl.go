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

// orderMapFor builds the step-name-to-order lookup a seeded step list carries.
func orderMapFor(steps []cob.StepConfig) map[string]int64 {
	m := make(map[string]int64, len(steps))
	for _, s := range steps {
		m[s.StepName] = s.StepOrder
	}
	return m
}

// transposedDueOverdueEvaluator is a DELIBERATELY WRONG implementation: it
// seeds the two repayment checks in the reverse order (CHECK_LOAN_REPAYMENT_DUE
// at 4, CHECK_LOAN_REPAYMENT_OVERDUE at 3), while the other four steps keep
// their places. A shift is not the only whole-sequence way the order can be
// wrong: this is a local transposition of two neighbours, which the port's own
// default cannot argue away because the oracle inserted the DUE step before the
// OVERDUE step [VERIFIED: 0067_add_configurations_for_repayment_due_business_steps.xml
// step_name CHECK_LOAN_REPAYMENT_DUE step_order 3 at 59-60, then step_name
// CHECK_LOAN_REPAYMENT_OVERDUE step_order 4 at 64-65]. The two vectors that
// assert the transposed orders go red; the other four stay green (a signature a
// whole-sequence shift cannot produce).
type transposedDueOverdueEvaluator struct{ goEvaluator }

// skippedDelinquencyEvaluator is a DELIBERATELY WRONG implementation: the job's
// step list is seeded from every changelog part EXCEPT 0047, so
// LOAN_DELINQUENCY_CLASSIFICATION is absent and every later step runs one
// position early (its order compacted down). A porter that stopped at the 0022
// base and never applied the delinquency-classification part seeds exactly this
// list [VERIFIED: 0047_add_loan_delinquency_tags_business_step.xml step_name
// LOAN_DELINQUENCY_CLASSIFICATION step_order 2 at 28-29]. The vectors for the
// steps after the gap go red on their compacted order; the vector for the
// skipped step itself cannot be answered (its name is not in the job) and comes
// back as a HARNESS-ERROR rather than a fabricated order.
type skippedDelinquencyEvaluator struct{ goEvaluator }

func init() {
	Register("cob-go", NewGoEvaluator())
	RegisterWrong("cob-wrong-shift-order",
		"shifts every business-step order by one, so any vector that asserts the order goes red",
		wrongEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})

	steps := cob.DefaultLoanConfig().BusinessSteps
	transposed := orderMapFor(steps)
	transposed[cob.StepCheckLoanRepaymentDue] = 4
	transposed[cob.StepCheckLoanRepaymentOverdue] = 3
	RegisterWrong("cob-wrong-transpose-due-overdue",
		"seeds the two repayment checks transposed (DUE at 4, OVERDUE at 3) while every other "+
			"step keeps its order: a local swap, not a whole-sequence shift. The oracle inserted "+
			"DUE at 3 before OVERDUE at 4 [VERIFIED: 0067_add_configurations_for_repayment_due_"+
			"business_steps.xml:59-60,64-65], so the two vectors asserting those orders go red and "+
			"the other four stay green.",
		transposedDueOverdueEvaluator{goEvaluator: goEvaluator{order: transposed}})

	skipped := orderMapFor(steps)
	delete(skipped, cob.StepLoanDelinquencyClassification)
	for _, s := range steps {
		if s.StepOrder > 2 {
			skipped[s.StepName] = s.StepOrder - 1
		}
	}
	RegisterWrong("cob-wrong-skip-delinquency-classification",
		"omits LOAN_DELINQUENCY_CLASSIFICATION from the job's step list (seeded as if the porter "+
			"never applied changelog part 0047 [VERIFIED: 0047_add_loan_delinquency_tags_business_"+
			"step.xml:28-29 step_order 2]) and compacts every later order down by one. The vectors "+
			"for the four steps after the gap go red; the vector for the skipped step cannot be "+
			"answered from a list that does not contain it and returns an error, never a fabricated "+
			"order.",
		skippedDelinquencyEvaluator{goEvaluator: goEvaluator{order: skipped}})
}
