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

// legalOrdinals is the declared ordinal set for each vocabulary, transcribed
// from the pinned Java source. It is the vocabulary's contract: an ordinal
// outside this set cannot have been produced by the oracle.
var legalOrdinals = map[string]map[int32]bool{
	string(VocabularyClientStatus): {
		0: true, 100: true, 300: true, 303: true, 304: true, 600: true, 700: true, 800: true,
	},
	string(VocabularyLegalForm): {
		1: true, 2: true,
	},
	string(VocabularyGroupingStatus): {
		0: true, 100: true, 300: true, 303: true, 304: true, 600: true,
	},
}

// AssertInvariants runs every gradeable parties invariant against the result an
// implementation returned. The single invariant asserts the one property every
// enum carries: the produced ordinal is a member of the vocabulary's declared
// ordinal set.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	return []InvariantResult{assertOrdinalInVocabulary(v, got)}
}

// assertOrdinalInVocabulary: Fineract persists these enums as ORDINALS, and each
// vocabulary declares a fixed set. An ordinal outside that set cannot have come
// from the oracle — it is silent data corruption, not a crash.
func assertOrdinalInVocabulary(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "ordinal_in_vocabulary", Assertions: 1}
	set := legalOrdinals[v.Request.Vocabulary]
	if set == nil {
		r.Status = InvariantNotApplicable
		r.Detail = fmt.Sprintf("no declared ordinal set for vocabulary %q", v.Request.Vocabulary)
		return r
	}
	if set[got.Ordinal] {
		r.Status = InvariantHeld
		r.Detail = fmt.Sprintf("ordinal %d is in the %s vocabulary", got.Ordinal, v.Request.Vocabulary)
		return r
	}
	r.Status = InvariantViolated
	r.Detail = fmt.Sprintf("ordinal %d is not in the %s vocabulary", got.Ordinal, v.Request.Vocabulary)
	return r
}
