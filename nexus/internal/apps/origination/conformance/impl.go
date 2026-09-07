package conformance

import (
	"fmt"
	"sort"
	"sync"

	"github.com/gerege/nexus/internal/apps/origination"
)

// OriginationEvaluator is what an origination implementation must be able to do
// for this harness to grade it: given a LoanOriginatorStatus enum name, return
// the stored string value (the EnumType.STRING the oracle persists).
type OriginationEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]OriginationEvaluator{}
	wrong  = map[string]string{}
)

// Register makes an OriginationEvaluator available under name.
func Register(name string, e OriginationEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("origination conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e OriginationEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (OriginationEvaluator, bool) {
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

// originatorStatusByName is the enum NAME -> LoanOriginatorStatus constant
// transcription. The NAME is the stable identity; the stored STRING is derived
// from the port's own StoredValue(), so a drift in the port's name->string
// mapping is exactly what the harness catches.
var originatorStatusByName = map[string]origination.LoanOriginatorStatus{
	"ACTIVE":   origination.OriginatorActive,
	"PENDING":  origination.OriginatorPending,
	"INACTIVE": origination.OriginatorInactive,
}

// goEvaluator grades the port's own LoanOriginatorStatus vocabulary: it derives
// the stored string directly from each constant's StoredValue(). No value is
// invented here.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() OriginationEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	s, ok := originatorStatusByName[req.Name]
	if !ok {
		return Expect{}, fmt.Errorf("origination: status %q is not in the LoanOriginatorStatus vocabulary", req.Name)
	}
	return Expect{Stored: s.StoredValue()}, nil
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it stores PENDING for
// ACTIVE and ACTIVE for PENDING, so the two swapped vectors go red while
// INACTIVE stays green. It exists so a graded_against row can name an executable
// defect.
type wrongEvaluator struct{}

func (wrongEvaluator) Evaluate(req Request) (Expect, error) {
	switch req.Name {
	case "ACTIVE":
		return Expect{Stored: "PENDING"}, nil
	case "PENDING":
		return Expect{Stored: "ACTIVE"}, nil
	default:
		s, ok := originatorStatusByName[req.Name]
		if !ok {
			return Expect{}, fmt.Errorf("origination: status %q is not in the LoanOriginatorStatus vocabulary", req.Name)
		}
		return Expect{Stored: s.StoredValue()}, nil
	}
}

func init() {
	Register("origination-go", NewGoEvaluator())
	RegisterWrong("origination-wrong-swap-status",
		"swaps ACTIVE and PENDING stored strings, so any vector asserting that mapping goes red",
		wrongEvaluator{})
}
