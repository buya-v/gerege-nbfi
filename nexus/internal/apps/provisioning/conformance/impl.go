package conformance

import (
	"fmt"
	"sort"
	"sync"

	"github.com/gerege/nexus/internal/apps/provisioning"
)

// ProvisioningEvaluator is what a provisioning implementation must be able to do
// for this harness to grade it. For this first promotion the graded surface is
// the m_provision_category aggregate: given a category's primary key, return the
// category's id, name and description. The port models that aggregate as
// provisioning.ProvisioningCategory; the evaluation returns its three members.
//
// The money core of the slice (PercentageOf and GenerateReserveEntries, the
// reserve-amount arithmetic a parity vector exists to pin) is NOT graded here:
// the gerege tenant carries no provisioning criteria and no provisioning entries,
// so the running oracle never produced a reserve amount to transcribe, and
// creating one would write to the tenant (forbidden). See the capture attestation
// for that decision.
type ProvisioningEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]ProvisioningEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a ProvisioningEvaluator available under name.
func Register(name string, e ProvisioningEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("provisioning conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e ProvisioningEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (ProvisioningEvaluator, bool) {
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

// goEvaluator is the port-backed category aggregate. The four categories are the
// port's model of the m_provision_category rows the running oracle returned to
// GET /v1/provisioningcategory (capture CAT-00); each field is a faithful
// transcription of that capture, not a computed value. The oracle's
// categoryName maps to the port's Name and categoryDescription to Description.
type goEvaluator struct {
	categories map[int64]provisioning.ProvisioningCategory
}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() ProvisioningEvaluator {
	categories := map[int64]provisioning.ProvisioningCategory{
		1: {ID: 1, Name: "STANDARD", Description: "Punctual Payment without any dues"},
		2: {ID: 2, Name: "SUB-STANDARD", Description: "Principal and/or Interest overdue by x days"},
		3: {ID: 3, Name: "DOUBTFUL", Description: "Principal and/or Interest overdue by x days and less than y"},
		4: {ID: 4, Name: "LOSS", Description: "Principal and/or Interest overdue by y days"},
	}
	return goEvaluator{categories: categories}
}

func (g goEvaluator) Evaluate(req Request) (Expect, error) {
	c, ok := g.categories[req.CategoryID]
	if !ok {
		return Expect{}, fmt.Errorf("provisioning: category id %d was not returned by the oracle capture", req.CategoryID)
	}
	return Expect{ID: c.ID, Name: c.Name, Description: c.Description}, nil
}

// wrongCategoryEvaluator is a DELIBERATELY WRONG implementation: it returns a
// category whose description is blanked. It exists so a graded_against row can
// name an executable defect, exactly as the charges harness's
// charges-wrong-percent-truncating does.
type wrongCategoryEvaluator struct{ goEvaluator }

func (w wrongCategoryEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	e.Description = ""
	return e, nil
}

func init() {
	Register("provisioning-go", NewGoEvaluator())
	RegisterWrong("provisioning-wrong-blank-description",
		"returns the correct category id and name but blanks the description, so any vector "+
			"that asserts a non-empty description goes red on that cell",
		wrongCategoryEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
}
