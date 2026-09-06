package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"sort"
)

// The charges capability registry and store pin, on the ledger harness's
// discipline: capability status is DATA, "exercised" is the only status that
// permits grading, and an ABSENT entry REFUSES (default-deny). A separate
// store-root file is used rather than appending to the loanschedule registry,
// because that file is named and versioned for one context.

// CapabilitySchemaV1 is the charges capability file's schema string.
const CapabilitySchemaV1 = "gerege.charges.capabilities/v1"

// CapabilityFileName is the store-root file this registry loads.
const CapabilityFileName = "capabilities-charges.json"

// PinFileName is the store-root file the charges pin loads.
const PinFileName = "PIN-charges.json"

// PinSchemaV1 is the charges pin file's schema string.
const PinSchemaV1 = "gerege.charges.pin/v1"

// Pin is the charges corpus's store-level comparability pin. It pins the
// Fineract commit a vector's oracle observation was taken from and the tenant
// context the capture was taken under; there is no contract digest because the
// charges slice freezes no contract file.
type Pin struct {
	Schema         string       `json:"schema"`
	Note           string       `json:"_note"`
	FineractCommit string       `json:"fineract_commit"`
	TenantParams   TenantParams `json:"tenant_params"`
}

// LoadPin reads the charges pin.
func LoadPin(path string) (*Pin, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("charges pin: %w", err)
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, fmt.Errorf("charges pin %s: %w", path, err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var p Pin
	if err := dec.Decode(&p); err != nil {
		return nil, fmt.Errorf("charges pin %s: decode: %w", path, err)
	}
	if p.Schema != PinSchemaV1 {
		return nil, fmt.Errorf("charges pin %s: schema %q, want %q", path, p.Schema, PinSchemaV1)
	}
	if p.FineractCommit == "" {
		return nil, fmt.Errorf("charges pin %s: fineract_commit is empty", path)
	}
	if p.TenantParams == (TenantParams{}) {
		return nil, fmt.Errorf("charges pin %s: tenant_params is empty", path)
	}
	return &p, nil
}

// SeamStatus records what a capture seam can see of one capability.
type SeamStatus string

const (
	StatusExercised SeamStatus = "exercised"
	StatusBlind     SeamStatus = "blind"
	StatusAliased   SeamStatus = "aliased"
	StatusPartial   SeamStatus = "partial"
)

// Capability is one named dimension of behaviour a capture either can or cannot
// see.
type Capability struct {
	Name           string `json:"name"`
	Description    string `json:"description"`
	InGradedDomain bool   `json:"in_graded_domain"`
	Evidence       string `json:"evidence"`
}

// Seam is one capture seam and its per-capability status map.
type Seam struct {
	Name        string                `json:"name"`
	Description string                `json:"description"`
	Status      map[string]SeamStatus `json:"status"`
}

// CapabilityRegistry is the data behind every refusal this harness issues on
// capability grounds. It is DATA rather than a table in this file, so recording
// a newly discovered blind spot refuses every affected vector without a code
// change or a schema migration.
type CapabilityRegistry struct {
	Schema       string       `json:"schema"`
	Note         string       `json:"note"`
	Capabilities []Capability `json:"capabilities"`
	Seams        []Seam       `json:"seams"`

	byName map[string]Capability
	bySeam map[string]Seam
}

// LoadCapabilityRegistry reads the registry. A missing or malformed registry is
// a hard error and never a permissive default: a harness that graded everything
// because it could not find its own refusal rules would be the most expensive
// possible failure mode.
func LoadCapabilityRegistry(path string) (*CapabilityRegistry, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("charges capability registry: %w", err)
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, fmt.Errorf("charges capability registry %s: %w", path, err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var r CapabilityRegistry
	if err := dec.Decode(&r); err != nil {
		return nil, fmt.Errorf("charges capability registry %s: decode: %w", path, err)
	}
	if r.Schema != CapabilitySchemaV1 {
		return nil, fmt.Errorf("charges capability registry %s: schema %q, want %q",
			path, r.Schema, CapabilitySchemaV1)
	}
	r.byName = map[string]Capability{}
	for _, c := range r.Capabilities {
		r.byName[c.Name] = c
	}
	r.bySeam = map[string]Seam{}
	for _, s := range r.Seams {
		r.bySeam[s.Name] = s
	}
	return &r, nil
}

// CapabilityVerdict is the result of Assess.
type CapabilityVerdict struct {
	Gradeable bool
	Reason    string
	Detail    []string
}

const (
	reasonUnknownSeam       = "unknown-seam"
	reasonUnknownCapability = "unknown-capability"
	reasonSeamBlind         = "seam-blind"
	reasonUngraded          = "ungraded"
)

// Assess answers whether a vector's required capabilities can be graded against
// a capture from its seam, under default-deny: an unaudited input is assumed
// invisible, never assumed wired.
func (r *CapabilityRegistry) Assess(seamName string, required []string) CapabilityVerdict {
	seam, ok := r.bySeam[seamName]
	if !ok {
		return CapabilityVerdict{
			Reason: reasonUnknownSeam,
			Detail: []string{fmt.Sprintf(
				"seam %q is not in the capability registry; the harness refuses rather than assume it sees anything",
				seamName)},
		}
	}
	if len(required) == 0 {
		return CapabilityVerdict{
			Reason: reasonUnknownCapability,
			Detail: []string{"capabilities_required is empty: a vector must state what it exercises, " +
				"because a vector that exercises nothing grades nothing"},
		}
	}
	var unknown, blind, ungraded []string
	for _, name := range required {
		capDef, defined := r.byName[name]
		if !defined {
			unknown = append(unknown, fmt.Sprintf("capability %q is not defined in the registry", name))
			continue
		}
		st, has := seam.Status[name]
		if !has {
			unknown = append(unknown, fmt.Sprintf(
				"seam %q has no recorded status for capability %q (default-deny: an unaudited input is "+
					"assumed invisible, never assumed wired)", seamName, name))
			continue
		}
		if st != StatusExercised {
			blind = append(blind, fmt.Sprintf(
				"capability %q is %q on seam %q — %s", name, st, seamName, capDef.Evidence))
			continue
		}
		if !capDef.InGradedDomain {
			ungraded = append(ungraded, fmt.Sprintf(
				"capability %q is exercised by seam %q but is OUTSIDE the graded domain — %s",
				name, seamName, capDef.Evidence))
		}
	}
	sort.Strings(unknown)
	sort.Strings(blind)
	sort.Strings(ungraded)
	switch {
	case len(unknown) > 0:
		return CapabilityVerdict{Reason: reasonUnknownCapability, Detail: unknown}
	case len(blind) > 0:
		return CapabilityVerdict{Reason: reasonSeamBlind, Detail: blind}
	case len(ungraded) > 0:
		return CapabilityVerdict{Reason: reasonUngraded, Detail: ungraded}
	}
	return CapabilityVerdict{Gradeable: true}
}
