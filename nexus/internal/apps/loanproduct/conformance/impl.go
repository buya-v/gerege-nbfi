package conformance

import (
	"fmt"
	"sort"
	"strings"
	"sync"

	"github.com/gerege/nexus/internal/apps/loanproduct"
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

// iotaOrdinalEvaluator is a DELIBERATELY WRONG implementation: it decodes the
// stored value through the port's own FromStoredValue and then re-encodes the
// member as its contiguous Go ordinal (int32(member)) instead of the stored
// value. For every enum in this context the Go ordinal is NOT the stored value
// — PeriodFrequencyType declares INVALID first so the zero value is the sentinel
// and each real member sits one past its stored id, and DaysInMonthType and
// DaysInYearType store the literal day count (30/360/364/365) rather than any
// ordinal. A member whose ordinal happens to equal its stored value — ACTUAL,
// ordinal 1 and stored 1 in both day-count vocabularies — survives, which is
// why a corpus built only from ACTUAL would report this port GREEN.
type iotaOrdinalEvaluator struct{}

func (iotaOrdinalEvaluator) Evaluate(req Request) (Expect, error) {
	switch Vocabulary(req.Vocabulary) {
	case VocabularyPeriodFrequency:
		f, ok := loanproduct.PeriodFrequencyTypeFromStoredValue(req.Stored)
		if !ok {
			return Expect{}, fmt.Errorf("loanproduct: stored %d does not decode in %q", req.Stored, req.Vocabulary)
		}
		return Expect{Stored: int32(f), Code: f.Code(), Name: f.String()}, nil
	case VocabularyDaysInMonth:
		d, ok := loanproduct.DaysInMonthTypeFromStoredValue(req.Stored)
		if !ok {
			return Expect{}, fmt.Errorf("loanproduct: stored %d does not decode in %q", req.Stored, req.Vocabulary)
		}
		return Expect{Stored: int32(d), Code: d.Code(), Name: d.String()}, nil
	case VocabularyDaysInYear:
		d, ok := loanproduct.DaysInYearTypeFromStoredValue(req.Stored)
		if !ok {
			return Expect{}, fmt.Errorf("loanproduct: stored %d does not decode in %q", req.Stored, req.Vocabulary)
		}
		return Expect{Stored: int32(d), Code: d.Code(), Name: d.String()}, nil
	}
	return goEvaluator{}.Evaluate(req)
}

// dimSiblingNameEvaluator is a DELIBERATELY WRONG implementation: it names the
// days-in-month DAYS_30 member "DAYS_360". The two day-count vocabularies are
// siblings in the same template read-back, DaysInMonthType.java declares its
// 30-day member with the i18n code "DaysInMonthType.days360" (a string that
// carries no "30" anywhere), and the parallel member in DaysInYearType is
// literally named DAYS_360 — so a porter who transcribes the name from the code
// writes DAYS_360 onto the 30-day member. Stored (30) and code stay
// byte-identical to a correct port; only the name cell diverges.
type dimSiblingNameEvaluator struct{}

func (dimSiblingNameEvaluator) Evaluate(req Request) (Expect, error) {
	if Vocabulary(req.Vocabulary) == VocabularyDaysInMonth && req.Stored == 30 {
		return Expect{Stored: 30, Code: "DaysInMonthType.days360", Name: "DAYS_360"}, nil
	}
	return goEvaluator{}.Evaluate(req)
}

// freqFieldQualifiedCodeEvaluator is a DELIBERATELY WRONG implementation: it
// returns the shared period-frequency codes qualified by the interest-period
// field, "interestPeriodFrequencyType.months" where the template's option list
// carries "periodFrequencyType.months". The one enum is nested TWICE in the
// product payload — under interestPeriodFrequencyType and under
// repaymentPeriodFrequencyType — and LoanProductRelatedDetail reads the raw
// integer out of whichever field and decodes it through the same fromInt, so a
// porter who models one enum per field and keys its i18n strings by the field
// it was read under writes exactly this. Stored and name are untouched; the
// code cell of every period-frequency vector is corrupted.
type freqFieldQualifiedCodeEvaluator struct{}

func (freqFieldQualifiedCodeEvaluator) Evaluate(req Request) (Expect, error) {
	if Vocabulary(req.Vocabulary) == VocabularyPeriodFrequency {
		f, ok := loanproduct.PeriodFrequencyTypeFromStoredValue(req.Stored)
		if !ok {
			return Expect{}, fmt.Errorf("loanproduct: stored %d does not decode in %q", req.Stored, req.Vocabulary)
		}
		code := "interestPeriodFrequencyType." + strings.TrimPrefix(f.Code(), "periodFrequencyType.")
		return Expect{Stored: f.StoredValue(), Code: code, Name: f.String()}, nil
	}
	return goEvaluator{}.Evaluate(req)
}

func init() {
	Register("loanproduct-go", NewGoEvaluator())
	RegisterWrong("loanproduct-wrong-swap-days360-365",
		"swaps the days-in-year DAYS_360 (360) and DAYS_365 (365) codes/names, so any vector asserting that mapping goes red",
		wrongEvaluator{})
	RegisterWrong("loanproduct-wrong-iota-ordinals",
		"decodes the stored value and re-encodes the member as its contiguous Go ordinal int32(member) instead of "+
			"the stored value the column persists. Every member whose Go ordinal differs from its stored value is "+
			"corrupt: PeriodFrequencyType declares INVALID first (zero value = sentinel) so DAYS..WHOLE_TERM sit one "+
			"past their stored 0..4, and DaysInMonthType/DaysInYearType store the literal day count 30/360/364/365, "+
			"not an ordinal at all [VERIFIED: PeriodFrequencyType.java:27-32, DaysInMonthType.java:24-26, "+
			"DaysInYearType.java:25-29]. Only ACTUAL (Go ordinal 1 == stored 1) survives, so a corpus that stopped "+
			"at ACTUAL would grade it GREEN. Dies on LP-freq-months, LP-freq-years, LP-freq-whole-term, LP-dim-days360, "+
			"LP-diy-days360, LP-diy-days364 and LP-diy-days365",
		iotaOrdinalEvaluator{})
	RegisterWrong("loanproduct-wrong-dim-sibling-name",
		"names the days-in-month 30-day member DAYS_360. DaysInMonthType.java declares that member with the i18n code "+
			"'DaysInMonthType.days360' — a string with no '30' in it — and DaysInYearType.java's parallel member is "+
			"literally named DAYS_360, so a porter who transcribes the NAME from the sibling code string writes this. "+
			"Stored (30) and code are byte-identical to a correct port; the name cell of LP-dim-days360 alone dies",
		dimSiblingNameEvaluator{})
	RegisterWrong("loanproduct-wrong-freq-field-qualified-code",
		"qualifies the shared period-frequency codes with the interest-period field name: 'interestPeriodFrequencyType.months' "+
			"where the template's option list carries 'periodFrequencyType.months'. The enum is nested twice in the product "+
			"payload — under interestPeriodFrequencyType and repaymentPeriodFrequencyType — and both read through the same "+
			"PeriodFrequencyType.fromInt, so a porter who models one enum per field and keys its i18n strings by the field it "+
			"was read under writes exactly this. Stored and name are untouched; only the code cell of LP-freq-months, "+
			"LP-freq-years and LP-freq-whole-term dies",
		freqFieldQualifiedCodeEvaluator{})
}
