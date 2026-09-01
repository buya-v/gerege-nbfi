package parties

import "fmt"

// LegalForm distinguishes a person from an entity, stored in
// m_client.legal_form_enum [VERIFIED: LegalForm.java:24-58]:
//
//	PERSON(1), ENTITY(2)
//
// The zero value (LegalFormUnset) represents a NULL column: Fineract's
// legal_form_enum is nullable and an unset legal form is treated as a person by
// the display-name derivation [VERIFIED: Client.java:383].
type LegalForm int32

const (
	LegalFormUnset LegalForm = 0
	LegalFormPerson LegalForm = 1
	LegalFormEntity LegalForm = 2
)

var legalFormName = map[LegalForm]string{
	LegalFormUnset:  "UNSET",
	LegalFormPerson: "PERSON",
	LegalFormEntity: "ENTITY",
}

// StoredValue returns m_client.legal_form_enum. The zero value is the sentinel
// a persistence layer maps to NULL.
func (l LegalForm) StoredValue() int32 { return int32(l) }

func (l LegalForm) String() string {
	if n, ok := legalFormName[l]; ok {
		return n
	}
	return fmt.Sprintf("LegalForm(%d)", int32(l))
}

// LegalFormFromStoredValue decodes m_client.legal_form_enum, returning
// LegalFormUnset for NULL/0 and ok=false for any other unknown value.
func LegalFormFromStoredValue(v int32) (LegalForm, bool) {
	switch v {
	case 0:
		return LegalFormUnset, true
	case 1:
		return LegalFormPerson, true
	case 2:
		return LegalFormEntity, true
	default:
		return 0, false
	}
}

// IsPerson reports PERSON [VERIFIED: LegalForm.java:47-49].
func (l LegalForm) IsPerson() bool { return l == LegalFormPerson }

// IsEntity reports ENTITY [VERIFIED: LegalForm.java:51-53].
func (l LegalForm) IsEntity() bool { return l == LegalFormEntity }

// IsUnset reports the NULL/unset legal form.
func (l LegalForm) IsUnset() bool { return l == LegalFormUnset }
