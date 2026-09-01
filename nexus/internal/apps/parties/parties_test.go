package parties

import (
	"testing"
	"time"
)

func TestDeriveDisplayName(t *testing.T) {
	for _, c := range []struct {
		name                          string
		first, middle, last, fullname string
		legalForm                     LegalForm
		want                          string
	}{
		{"fullname wins over parts", "Ada", "L", "Byron", "Augusta Ada King", LegalFormPerson, "Augusta Ada King"},
		{"person space-joins present parts", "Ada", "Lovelace", "King", "", LegalFormPerson, "Ada Lovelace King"},
		{"person skips blank parts", "Ada", "", "King", "", LegalFormPerson, "Ada King"},
		{"unset legal form treated as person", "Ada", "", "King", "", LegalFormUnset, "Ada King"},
		{"entity yields empty display name", "", "", "", "", LegalFormEntity, ""},
		{"entity fullname still wins", "", "", "", "Acme Corp", LegalFormEntity, "Acme Corp"},
	} {
		t.Run(c.name, func(t *testing.T) {
			client := NewClient(1, c.first, c.middle, c.last, c.fullname, c.legalForm)
			if client.DisplayName != c.want {
				t.Errorf("DisplayName = %q, want %q", client.DisplayName, c.want)
			}
		})
	}
}

func TestClientStatusStoredValues(t *testing.T) {
	want := map[ClientStatus]int32{
		ClientInvalid:            0,
		ClientPending:            100,
		ClientActive:             300,
		ClientTransferInProgress: 303,
		ClientTransferOnHold:     304,
		ClientClosed:             600,
		ClientRejected:           700,
		ClientWithdrawn:          800,
	}
	for s, v := range want {
		if got := s.StoredValue(); got != v {
			t.Errorf("ClientStatus(%s).StoredValue() = %d, want %d", s, got, v)
		}
		back, ok := ClientStatusFromStoredValue(v)
		if !ok || back != s {
			t.Errorf("ClientStatusFromStoredValue(%d) = (%v, %v), want %s", v, back, ok, s)
		}
	}
	if _, ok := ClientStatusFromStoredValue(999); ok {
		t.Errorf("ClientStatusFromStoredValue(999) ok=true, want false")
	}
}

func TestClientStatusPredicates(t *testing.T) {
	if !ClientActive.IsActive() {
		t.Errorf("ClientActive.IsActive() = false")
	}
	if ClientTransferInProgress.IsUnderTransfer() && ClientTransferOnHold.IsUnderTransfer() {
		// both transfer sub-states report under-transfer
	} else {
		t.Errorf("transfer sub-states should report IsUnderTransfer")
	}
	if !ClientRejected.IsRejected() || !ClientWithdrawn.IsWithdrawn() || !ClientClosed.IsClosed() {
		t.Errorf("terminal status predicates incorrect")
	}
}

func TestLegalForm(t *testing.T) {
	if !LegalFormPerson.IsPerson() || LegalFormPerson.IsEntity() {
		t.Errorf("LegalFormPerson misclassified")
	}
	if !LegalFormEntity.IsEntity() || LegalFormEntity.IsPerson() {
		t.Errorf("LegalFormEntity misclassified")
	}
	if !LegalFormUnset.IsUnset() {
		t.Errorf("LegalFormUnset.IsUnset() = false")
	}
	if lf, ok := LegalFormFromStoredValue(2); !ok || lf != LegalFormEntity {
		t.Errorf("LegalFormFromStoredValue(2) = (%v, %v), want ENTITY", lf, ok)
	}
}

func TestGroupingTypeStatusStoredValues(t *testing.T) {
	want := map[GroupingTypeStatus]int32{
		GroupingInvalid:            0,
		GroupingPending:            100,
		GroupingActive:             300,
		GroupingTransferInProgress: 303,
		GroupingTransferOnHold:     304,
		GroupingClosed:             600,
	}
	for s, v := range want {
		if got := s.StoredValue(); got != v {
			t.Errorf("GroupingTypeStatus(%s).StoredValue() = %d, want %d", s, got, v)
		}
		back, ok := GroupingTypeStatusFromStoredValue(v)
		if !ok || back != s {
			t.Errorf("GroupingTypeStatusFromStoredValue(%d) = (%v, %v), want %s", v, back, ok, s)
		}
	}
}

func TestGroupLevelClassification(t *testing.T) {
	if !NewGroupLevel(1, 0, true, "Center", true, false).IsCenter() {
		t.Errorf("level named Center should IsCenter")
	}
	if NewGroupLevel(1, 0, true, "center", true, false).IsGroup() {
		t.Errorf("level named center should not IsGroup")
	}
	if !NewGroupLevel(2, 1, false, "Group", false, true).IsGroup() {
		t.Errorf("level named Group should IsGroup")
	}
}

func TestNewGroupDefaults(t *testing.T) {
	g := NewGroup(1, 0, NewGroupLevel(1, 0, true, "Center", true, false), "  Alpha  ", " ext ", false, time.Time{})
	if !g.IsPending() {
		t.Errorf("new group should default to PENDING, got %s", g.Status)
	}
	if g.Name != "Alpha" || g.ExternalID != "ext" {
		t.Errorf("name/externalId not trimmed: %q / %q", g.Name, g.ExternalID)
	}
}
