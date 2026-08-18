package contract

import (
	"errors"
	"testing"
)

// TEMPORARY reviewer-only probe (T23). Deleted before commit.
func TestT23ErrorTaxonomy(t *testing.T) {
	if !errors.Is(ErrNoDiscriminatingVector, ErrUnsupportedConfiguration) {
		t.Error("ErrNoDiscriminatingVector does not wrap ErrUnsupportedConfiguration")
	}
	if errors.Is(ErrUnsupportedConfiguration, ErrNoDiscriminatingVector) {
		t.Error("ErrUnsupportedConfiguration wrongly Is ErrNoDiscriminatingVector")
	}
	if errors.Is(ErrNoDiscriminatingVector, ErrInvalidRequest) {
		t.Error("ErrNoDiscriminatingVector wrongly Is ErrInvalidRequest")
	}
	if errors.Is(ErrUnsupportedConfiguration, ErrInvalidRequest) {
		t.Error("ErrUnsupportedConfiguration wrongly Is ErrInvalidRequest")
	}
	// Distinguishable in the other direction: a caller that DOES care can
	// still separate the two.
	if !errors.Is(ErrNoDiscriminatingVector, ErrNoDiscriminatingVector) {
		t.Error("sentinel not Is itself")
	}
	t.Logf("ErrNoDiscriminatingVector = %q", ErrNoDiscriminatingVector.Error())
	t.Logf("unwrap = %v", errors.Unwrap(ErrNoDiscriminatingVector))
}
