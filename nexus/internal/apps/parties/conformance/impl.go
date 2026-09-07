package conformance

import (
	"fmt"
	"sort"
	"sync"

	"github.com/gerege/nexus/internal/apps/parties"
)

// PartiesEvaluator is what a parties implementation must be able to do for this
// harness to grade it: given an enum NAME within a vocabulary, return the integer
// ordinal Fineract persists for that name.
type PartiesEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]PartiesEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a PartiesEvaluator available under name.
func Register(name string, e PartiesEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("parties conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e PartiesEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (PartiesEvaluator, bool) {
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

// The NAME -> enum-constant transcriptions. The NAME is the stable identity; the
// ORDINAL is derived from each constant's StoredValue(), so a drift in the port's
// name -> ordinal mapping is exactly what the harness catches. No value is
// invented here — the names below are the enum members declared in the pinned
// Java source.
var clientStatusByName = map[string]parties.ClientStatus{
	"INVALID":              parties.ClientInvalid,
	"PENDING":              parties.ClientPending,
	"ACTIVE":               parties.ClientActive,
	"TRANSFER_IN_PROGRESS": parties.ClientTransferInProgress,
	"TRANSFER_ON_HOLD":     parties.ClientTransferOnHold,
	"CLOSED":               parties.ClientClosed,
	"REJECTED":             parties.ClientRejected,
	"WITHDRAWN":            parties.ClientWithdrawn,
}

var legalFormByName = map[string]parties.LegalForm{
	"PERSON": parties.LegalFormPerson,
	"ENTITY": parties.LegalFormEntity,
}

var groupingStatusByName = map[string]parties.GroupingTypeStatus{
	"INVALID":              parties.GroupingInvalid,
	"PENDING":              parties.GroupingPending,
	"ACTIVE":               parties.GroupingActive,
	"TRANSFER_IN_PROGRESS": parties.GroupingTransferInProgress,
	"TRANSFER_ON_HOLD":     parties.GroupingTransferOnHold,
	"CLOSED":               parties.GroupingClosed,
}

// goEvaluator grades the port's own enum vocabularies: it derives the stored
// ordinal directly from each constant's StoredValue(). No value is invented here.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() PartiesEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	switch Vocabulary(req.Vocabulary) {
	case VocabularyClientStatus:
		s, ok := clientStatusByName[req.Name]
		if !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the ClientStatus vocabulary", req.Name)
		}
		return Expect{Ordinal: s.StoredValue()}, nil
	case VocabularyLegalForm:
		l, ok := legalFormByName[req.Name]
		if !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the LegalForm vocabulary", req.Name)
		}
		return Expect{Ordinal: l.StoredValue()}, nil
	case VocabularyGroupingStatus:
		g, ok := groupingStatusByName[req.Name]
		if !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the GroupingTypeStatus vocabulary", req.Name)
		}
		return Expect{Ordinal: g.StoredValue()}, nil
	default:
		return Expect{}, fmt.Errorf("parties: unknown vocabulary %q", req.Vocabulary)
	}
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it swaps the client
// ACTIVE (300) and PENDING (100) ordinals, the exact adjacent-ordinal defect this
// context is built to catch. The two swapped vectors go red; every other vector
// stays green. It exists so a graded_against row can name an executable defect.
type wrongEvaluator struct{}

func (wrongEvaluator) Evaluate(req Request) (Expect, error) {
	if Vocabulary(req.Vocabulary) == VocabularyClientStatus {
		switch req.Name {
		case "ACTIVE":
			return Expect{Ordinal: 100}, nil
		case "PENDING":
			return Expect{Ordinal: 300}, nil
		}
	}
	return goEvaluator{}.Evaluate(req)
}

func init() {
	Register("parties-go", NewGoEvaluator())
	RegisterWrong("parties-wrong-swap-active-pending",
		"swaps the client ACTIVE (300) and PENDING (100) ordinals, so any vector asserting that mapping goes red",
		wrongEvaluator{})
}
