package conformance

import "fmt"

// InvariantStatus is the outcome of one invariant assertion.
type InvariantStatus string

const (
	InvariantHeld          InvariantStatus = "HOLD"
	InvariantViolated      InvariantStatus = "VIOLATED"
	InvariantNotApplicable InvariantStatus = "N/A"
)

// InvariantResult is one invariant's verdict on one vector.
type InvariantResult struct {
	Name       string
	Status     InvariantStatus
	Assertions int
	Detail     string
}

// legalStoredValues is the declared stored-value set for each vocabulary,
// transcribed from the pinned Java source and corroborated by the template
// option lists. It is the vocabulary's contract: a stored value outside this set
// cannot have been produced by the oracle.
var legalStoredValues = map[string]map[int32]bool{
	string(VocabularyAmortizationMethod): {
		0: true, 1: true,
	},
	string(VocabularyInterestMethod): {
		0: true, 1: true,
	},
	string(VocabularyInterestCalcPeriod): {
		0: true, 1: true,
	},
	string(VocabularyPeriodFrequency): {
		0: true, 1: true, 2: true, 3: true, 4: true,
	},
	string(VocabularyDaysInMonth): {
		1: true, 30: true,
	},
	string(VocabularyDaysInYear): {
		1: true, 360: true, 364: true, 365: true,
	},
}

// AssertInvariants runs every gradeable loanproduct invariant against the result
// an implementation returned.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	return []InvariantResult{
		assertStoredInVocabulary(v, got),
		assertCodeConsistentWithStored(v, got),
	}
}

// assertStoredInVocabulary: the decoded stored value must be a member of the
// vocabulary's declared stored-value set. A value outside that set cannot have
// come from the oracle — it is silent configuration corruption.
func assertStoredInVocabulary(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "stored_in_vocabulary", Assertions: 1}
	set := legalStoredValues[v.Request.Vocabulary]
	if set == nil {
		r.Status = InvariantNotApplicable
		r.Detail = fmt.Sprintf("no declared stored-value set for vocabulary %q", v.Request.Vocabulary)
		return r
	}
	if set[got.Stored] {
		r.Status = InvariantHeld
		r.Detail = fmt.Sprintf("stored %d is in the %s vocabulary", got.Stored, v.Request.Vocabulary)
		return r
	}
	r.Status = InvariantViolated
	r.Detail = fmt.Sprintf("stored %d is not in the %s vocabulary", got.Stored, v.Request.Vocabulary)
	return r
}

// assertCodeConsistentWithStored: the code and name must be non-empty whenever
// the stored value is a member of the vocabulary. An empty code on a decode that
// succeeded is a port defect, not an oracle output.
func assertCodeConsistentWithStored(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "code_non_empty", Assertions: 1}
	if got.Code == "" || got.Name == "" {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("decoded code %q / name %q for stored %d is empty", got.Code, got.Name, got.Stored)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("decoded code %q / name %q for stored %d is non-empty", got.Code, got.Name, got.Stored)
	return r
}
