package conformance

import (
	"fmt"
	"sort"
	"strings"
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

// goEvaluator grades the port's own vocabularies: it derives the stored ordinal
// directly from each constant's StoredValue(), and — for the display-name seam —
// it runs the port's own name derivation. No value is invented here.
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
	case VocabularyDisplayName:
		lf, ok := legalFormByName[req.LegalForm]
		if !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the LegalForm vocabulary", req.LegalForm)
		}
		c := parties.NewClient(0, req.GivenName, req.Patronymic, req.Ovog, req.Fullname, lf)
		return Expect{DisplayName: c.DisplayName}, nil
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

// iotaOrdinalEvaluator is a DELIBERATELY WRONG implementation: it writes each
// status as its Go enum constant's own declaration index (its iota ordinal)
// rather than the stored value the vocabulary pins. The statuses ARE declared in
// the Java lifecycle order -- INVALID, PENDING, ACTIVE, TRANSFER_IN_PROGRESS,
// TRANSFER_ON_HOLD, CLOSED, REJECTED, WITHDRAWN [ClientStatus.java:24-96] -- so
// an idiomatic Go enum built with iota lines up member-for-member with the
// source and int32(member) silently substitutes the DECLARATION POSITION for
// the 100/300/303/304/600/700/800 code. Every non-INVALID status in BOTH status
// tables (m_client.status_enum and m_group.status_enum) comes back one or two
// orders of magnitude too small. INVALID (0) and both LegalForm members (whose
// codes really are contiguous from 1) survive, which is exactly the footprint
// that makes the defect look like a rounding-normalisation bug on a status that
// 'really is' ordinal 2 for ACTIVE.
type iotaOrdinalEvaluator struct{}

func (iotaOrdinalEvaluator) Evaluate(req Request) (Expect, error) {
	switch Vocabulary(req.Vocabulary) {
	case VocabularyClientStatus:
		s, ok := clientStatusByName[req.Name]
		if !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the ClientStatus vocabulary", req.Name)
		}
		return Expect{Ordinal: int32(s)}, nil
	case VocabularyGroupingStatus:
		g, ok := groupingStatusByName[req.Name]
		if !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the GroupingTypeStatus vocabulary", req.Name)
		}
		return Expect{Ordinal: int32(g)}, nil
	}
	return goEvaluator{}.Evaluate(req)
}

// transferSwapEvaluator is a DELIBERATELY WRONG implementation: it transposes
// the two transfer sub-states, TRANSFER_IN_PROGRESS (303) and TRANSFER_ON_HOLD
// (304), in BOTH status tables. The Java enum declares the pair adjacently with
// one-digit codes that differ only in the last digit and whose memberships of
// the active band are identical [ClientStatus.java:36-45,
// GroupingTypeStatus.java:31-40]; a port that carries the transfer lifecycle as
// a two-step state machine and copies the pair across from a loan or centre
// transfer path can invert them without any compile error. It proves the 303/304
// vectors in each table are individually graded: the client swap catches CS-04
// and CS-05, the group swap catches GS-04 and GS-05, and the ACTIVE/PENDING swap
// alone never touches this band.
type transferSwapEvaluator struct{}

func (transferSwapEvaluator) Evaluate(req Request) (Expect, error) {
	switch Vocabulary(req.Vocabulary) {
	case VocabularyClientStatus, VocabularyGroupingStatus:
		switch req.Name {
		case "TRANSFER_IN_PROGRESS":
			return Expect{Ordinal: 304}, nil
		case "TRANSFER_ON_HOLD":
			return Expect{Ordinal: 303}, nil
		}
	}
	return goEvaluator{}.Evaluate(req)
}

// legalFormPersonAsUnsetEvaluator is a DELIBERATELY WRONG implementation: it
// encodes a PERSON legal form as the UNSET/NULL ordinal 0 because the
// display-name derivation treats a NULL legal_form_enum exactly as it treats a
// person [Client.java:383]. A port written against that derivation -- persons
// are the default, ENTITY is the stored exception -- reads the fallback as the
// persistence rule and never writes PERSON(1); m_client.legal_form_enum is
// nullable [LegalForm.java:24-58], so 0 is a value the column can hold and the
// row survives. It kills LF-01 (PERSON -> 1) and leaves ENTITY -> 2 green; the
// produced 0 is also outside the declared legal-form ordinal set {1,2}, so the
// ordinal_in_vocabulary invariant sees it even before the stored cell compares.
type legalFormPersonAsUnsetEvaluator struct{}

func (legalFormPersonAsUnsetEvaluator) Evaluate(req Request) (Expect, error) {
	if Vocabulary(req.Vocabulary) == VocabularyLegalForm && req.Name == "PERSON" {
		return Expect{Ordinal: 0}, nil
	}
	return goEvaluator{}.Evaluate(req)
}

// joinNonBlank joins the present parts with single spaces, skipping blank ones —
// Fineract's StringBuilder logic [Client.java:464-479] applied to the request's
// three semantic slots in wire order.
func joinNonBlank(parts ...string) string {
	var kept []string
	for _, p := range parts {
		if strings.TrimSpace(p) != "" {
			kept = append(kept, p)
		}
	}
	return strings.Join(kept, " ")
}

// ovogFirstDisplayEvaluator is a DELIBERATELY WRONG implementation: for a PERSON
// with no fullname it joins the three parts in ovog -> given -> patronymic order
// (Fineract's lastname -> firstname -> middlename) instead of Fineract's
// firstname -> middlename -> lastname. Blanks are still skipped, the fullname
// arm still wins, and an entity still yields no name, so only the two person
// vectors move: DN-02 (P1, three parts) and DN-03 (P2, blank middle). DN-01
// (fullname) and DN-04 (entity) stay green. This is the shape a port adopts when
// it reads CLAUDE.md's canonical "ovog, patronymic, given name" ordering as the
// join order instead of Fineract's physical column order.
type ovogFirstDisplayEvaluator struct{}

func (ovogFirstDisplayEvaluator) Evaluate(req Request) (Expect, error) {
	if Vocabulary(req.Vocabulary) == VocabularyDisplayName {
		lf, ok := legalFormByName[req.LegalForm]
		if !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the LegalForm vocabulary", req.LegalForm)
		}
		if strings.TrimSpace(req.Fullname) != "" {
			return Expect{DisplayName: req.Fullname}, nil
		}
		if lf.IsEntity() {
			return Expect{DisplayName: ""}, nil
		}
		return Expect{DisplayName: joinNonBlank(req.Ovog, req.GivenName, req.Patronymic)}, nil
	}
	return goEvaluator{}.Evaluate(req)
}

// noBlankSkipDisplayEvaluator is a DELIBERATELY WRONG implementation: it keeps
// Fineract's part order and both outer arms but joins all three slots
// unconditionally, so an absent middlename leaves the double space
// "Синтетик  Давхардалгүй". Only DN-03 (P2) moves; DN-02's three present parts
// join identically.
type noBlankSkipDisplayEvaluator struct{}

func (noBlankSkipDisplayEvaluator) Evaluate(req Request) (Expect, error) {
	if Vocabulary(req.Vocabulary) == VocabularyDisplayName {
		lf, ok := legalFormByName[req.LegalForm]
		if !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the LegalForm vocabulary", req.LegalForm)
		}
		if strings.TrimSpace(req.Fullname) != "" {
			return Expect{DisplayName: req.Fullname}, nil
		}
		if lf.IsEntity() {
			return Expect{DisplayName: ""}, nil
		}
		return Expect{DisplayName: strings.Join([]string{req.GivenName, req.Patronymic, req.Ovog}, " ")}, nil
	}
	return goEvaluator{}.Evaluate(req)
}

// entityJoinsPartsDisplayEvaluator is a DELIBERATELY WRONG implementation: it
// derives persons correctly but joins an ENTITY's present parts instead of
// yielding no name. Only DN-04 (E1) moves; the two persons and the fullname
// vector stay green.
type entityJoinsPartsDisplayEvaluator struct{}

func (entityJoinsPartsDisplayEvaluator) Evaluate(req Request) (Expect, error) {
	if Vocabulary(req.Vocabulary) == VocabularyDisplayName {
		if _, ok := legalFormByName[req.LegalForm]; !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the LegalForm vocabulary", req.LegalForm)
		}
		if strings.TrimSpace(req.Fullname) != "" {
			return Expect{DisplayName: req.Fullname}, nil
		}
		return Expect{DisplayName: joinNonBlank(req.GivenName, req.Patronymic, req.Ovog)}, nil
	}
	return goEvaluator{}.Evaluate(req)
}

// partsOverFullnameDisplayEvaluator is a DELIBERATELY WRONG implementation: the
// three-field port drops Fineract's fullname-wins arm and derives every person
// from the parts alone. Only DN-01 (arm 1, a person whose only name is fullname)
// moves; its three parts are empty, so the join yields "". Persons with parts
// and the entity are unaffected.
type partsOverFullnameDisplayEvaluator struct{}

func (partsOverFullnameDisplayEvaluator) Evaluate(req Request) (Expect, error) {
	if Vocabulary(req.Vocabulary) == VocabularyDisplayName {
		lf, ok := legalFormByName[req.LegalForm]
		if !ok {
			return Expect{}, fmt.Errorf("parties: %q is not in the LegalForm vocabulary", req.LegalForm)
		}
		if lf.IsEntity() {
			return Expect{DisplayName: ""}, nil
		}
		return Expect{DisplayName: joinNonBlank(req.GivenName, req.Patronymic, req.Ovog)}, nil
	}
	return goEvaluator{}.Evaluate(req)
}

func init() {
	Register("parties-go", NewGoEvaluator())
	RegisterWrong("parties-wrong-swap-active-pending",
		"swaps the client ACTIVE (300) and PENDING (100) ordinals, so any vector asserting that mapping goes red",
		wrongEvaluator{})
	RegisterWrong("parties-wrong-iota-ordinals",
		"writes both status tables as int32(constant) on an iota enum whose members line up with the Java "+
			"declaration order [ClientStatus.java:24-96, GroupingTypeStatus.java:24-84], so PENDING persists as 1 not 100, "+
			"ACTIVE as 2 not 300, TRANSFER_IN_PROGRESS as 3 not 303, TRANSFER_ON_HOLD as 4 not 304, CLOSED as 5 not 600, "+
			"REJECTED as 6 not 700 and WITHDRAWN as 7 not 800 -- INVALID(0) is the only member that survives, and the "+
			"two LegalForm members survive because their codes genuinely are contiguous from 1. Dies on every non-INVALID "+
			"CS and GS vector (CS-02..CS-08, GS-02..GS-06) in both status vocabularies, in the stored ordinal cell, with "+
			"the out-of-vocabulary ordinals also flagged by ordinal_in_vocabulary",
		iotaOrdinalEvaluator{})
	RegisterWrong("parties-wrong-transfer-states-swapped",
		"transposes TRANSFER_IN_PROGRESS (303) and TRANSFER_ON_HOLD (304) in m_client.status_enum and "+
			"m_group.status_enum alike -- the Java enum declares the two transfer members adjacently with codes that differ "+
			"only in the last digit [ClientStatus.java:36-45, GroupingTypeStatus.java:31-40], and a port that ports the "+
			"transfer lifecycle as one two-step state machine instead of two tables copies the pair across inverted. Dies on "+
			"CS-04, CS-05, GS-04 and GS-05 only, in the stored ordinal cell",
		transferSwapEvaluator{})
	RegisterWrong("parties-wrong-legalform-person-as-unset",
		"encodes a PERSON as the unset/NULL legal form ordinal 0 because the display-name derivation treats a NULL "+
			"legal_form_enum as a person [Client.java:383] and m_client.legal_form_enum is nullable [LegalForm.java:24-58]; "+
			"the port reads that fallback as the persistence rule and never writes PERSON(1). Dies on LF-01 (PERSON -> 1) "+
			"alone, where the returned 0 is also outside the declared legal-form ordinal set {1,2}",
		legalFormPersonAsUnsetEvaluator{})
	RegisterWrong("parties-wrong-display-ovog-first",
		"joins the three name parts ovog -> given -> patronymic instead of Fineract's firstname -> middlename -> lastname, "+
			"so a PERSON without a fullname gets the parts in the reverse family order. Dies on DN-02 and DN-03 only; the "+
			"fullname arm (DN-01) and the entity arm (DN-04) are untouched",
		ovogFirstDisplayEvaluator{})
	RegisterWrong("parties-wrong-display-no-blank-skip",
		"joins all three name slots without skipping blanks, so an absent middlename leaves a double space "+
			"(\"Синтетик  Давхардалгүй\" instead of \"Синтетик Давхардалгүй\"). Dies on DN-03 only; DN-02's three present "+
			"parts join identically",
		noBlankSkipDisplayEvaluator{})
	RegisterWrong("parties-wrong-display-entity-joins-parts",
		"joins an ENTITY's present name parts instead of yielding no display name. Dies on DN-04 only",
		entityJoinsPartsDisplayEvaluator{})
	RegisterWrong("parties-wrong-display-parts-over-fullname",
		"drops Fineract's fullname-wins arm and derives a person from the three parts alone, so a client whose only name "+
			"is fullname (DN-01) gets the empty string. Dies on DN-01 only",
		partsOverFullnameDisplayEvaluator{})
}
