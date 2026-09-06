package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"sort"
)

// The shared capability machinery: capability status is DATA, "exercised" is the
// only status that permits grading, and an ABSENT entry REFUSES (default-deny).
//
// Each context keeps its own CapabilityRegistry STRUCT (its tests build the
// indexed maps directly), but the refusal decision and the file loading are
// shared so the default-deny rule cannot drift between contexts.

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

// CapabilityVerdict is the result of the default-deny assessment.
type CapabilityVerdict struct {
	Gradeable bool
	Reason    string
	Detail    []string
}

const (
	// ReasonUnknownSeam: the seam is not in the registry.
	ReasonUnknownSeam = "unknown-seam"
	// ReasonUnknownCapability: a required capability is undefined, unaudited, or
	// the required list is empty.
	ReasonUnknownCapability = "unknown-capability"
	// ReasonSeamBlind: the seam is recorded as not exercising a required input.
	ReasonSeamBlind = "seam-blind"
	// ReasonUngraded: the capability is exercised but outside the graded domain.
	ReasonUngraded = "ungraded"
)

// CapabilityMaps is a loaded, indexed capability registry.
type CapabilityMaps struct {
	ByName map[string]Capability
	BySeam map[string]Seam
}

// capabilityFile is the on-disk shape the loader strictly decodes. It mirrors
// the exported fields of each context's CapabilityRegistry struct so that a
// registry file round-trips through the loader unchanged.
type capabilityFile struct {
	Schema       string       `json:"schema"`
	Note         string       `json:"note"`
	Capabilities []Capability `json:"capabilities"`
	Seams        []Seam       `json:"seams"`
}

// LoadCapabilityMaps reads a registry file and returns its indexed maps.
//
// A missing or malformed registry is a hard error and never a permissive
// default: a harness that graded everything because it could not find its own
// refusal rules would be the most expensive possible failure mode.
//
// label is the context name used in the error text so the reader knows which
// store's refusal rules failed to load.
func LoadCapabilityMaps(path, schema, label string) (CapabilityMaps, error) {
	var zero CapabilityMaps
	raw, err := os.ReadFile(path)
	if err != nil {
		return zero, fmt.Errorf("%s capability registry: %w", label, err)
	}
	if err := RejectFloatTokens(raw, label); err != nil {
		return zero, fmt.Errorf("%s capability registry %s: %w", label, path, err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var f capabilityFile
	if err := dec.Decode(&f); err != nil {
		return zero, fmt.Errorf("%s capability registry %s: decode: %w", label, path, err)
	}
	if f.Schema != schema {
		return zero, fmt.Errorf("%s capability registry %s: schema %q, want %q",
			label, path, f.Schema, schema)
	}
	m := CapabilityMaps{
		ByName: map[string]Capability{},
		BySeam: map[string]Seam{},
	}
	for _, c := range f.Capabilities {
		m.ByName[c.Name] = c
	}
	for _, s := range f.Seams {
		m.BySeam[s.Name] = s
	}
	return m, nil
}

// AssessCapability answers whether a vector's required capabilities can be
// graded against a capture from its seam, under default-deny: an unaudited input
// is assumed invisible, never assumed wired.
func AssessCapability(byName map[string]Capability, bySeam map[string]Seam, seamName string, required []string) CapabilityVerdict {
	seam, ok := bySeam[seamName]
	if !ok {
		return CapabilityVerdict{
			Reason: ReasonUnknownSeam,
			Detail: []string{fmt.Sprintf(
				"seam %q is not in the capability registry; the harness refuses rather than assume it sees anything",
				seamName)},
		}
	}
	if len(required) == 0 {
		return CapabilityVerdict{
			Reason: ReasonUnknownCapability,
			Detail: []string{"capabilities_required is empty: a vector must state what it exercises, " +
				"because a vector that exercises nothing grades nothing"},
		}
	}
	var unknown, blind, ungraded []string
	for _, name := range required {
		capDef, defined := byName[name]
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
		return CapabilityVerdict{Reason: ReasonUnknownCapability, Detail: unknown}
	case len(blind) > 0:
		return CapabilityVerdict{Reason: ReasonSeamBlind, Detail: blind}
	case len(ungraded) > 0:
		return CapabilityVerdict{Reason: ReasonUngraded, Detail: ungraded}
	}
	return CapabilityVerdict{Gradeable: true}
}
