package conformance

import (
	"fmt"
	"sort"
	"strconv"
	"sync"

	"github.com/gerege/nexus/internal/apps/branch"
)

// BranchEvaluator is what a branch implementation must be able to do for this
// harness to grade it: given a cashier-transaction cash movement (a txn-type
// stored id and an amount as exact decimal text), return the stored transaction
// type and the amount normalised to integer minor units. This is the pure,
// testable money path the branch slice ports.
type BranchEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]BranchEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a BranchEvaluator available under name.
func Register(name string, e BranchEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("branch conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e BranchEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (BranchEvaluator, bool) {
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

// goEvaluator is the port-backed cashier-transaction amount. It maps the txn-type
// stored id through branch.CashierTxnTypeFromID and normalises the amount through
// branch.MinorUnitsFromDecimalText, so a port whose enum table or exact-money
// parser diverges from the oracle's stored row produces a different cell.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() BranchEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	typ, ok := branch.CashierTxnTypeFromID(req.TxnType)
	if !ok {
		return Expect{}, fmt.Errorf("branch: request.txn_type %d is not a known cashier txn type", req.TxnType)
	}
	amt, err := branch.MinorUnitsFromDecimalText(req.TxnAmount, branch.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("branch: request.txn_amount %q: %w", req.TxnAmount, err)
	}
	return Expect{
		TxnTypeID:      typ.ID,
		TxnTypeValue:   typ.Value,
		TxnAmountMinor: strconv.FormatInt(int64(amt), 10),
	}, nil
}

// offByOneEvaluator is a DELIBERATELY WRONG implementation: it returns the
// transaction amount one minor unit high. It exists so a graded_against row can
// name an executable defect, exactly as the provisioning harness's wrong
// implementation does.
type offByOneEvaluator struct{ goEvaluator }

func (offByOneEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	n, perr := strconv.ParseInt(e.TxnAmountMinor, 10, 64)
	if perr != nil {
		return e, perr
	}
	e.TxnAmountMinor = strconv.FormatInt(n+1, 10)
	return e, nil
}

func init() {
	Register("branch-go", NewGoEvaluator())
	RegisterWrong("branch-wrong-off-by-one",
		"returns the transaction amount one minor unit high, so any amount cell goes red",
		offByOneEvaluator{})
}
