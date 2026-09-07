package conformance

import (
	shared "github.com/gerege/nexus/internal/conformance"
)

// The working-capital capability registry and store pin, on the shared
// default-deny discipline: capability status is DATA, "exercised" is the only
// status that permits grading, and an ABSENT entry REFUSES.

// CapabilitySchemaV1 is the working-capital capability file's schema string.
const CapabilitySchemaV1 = "gerege.workingcapital.capabilities/v1"

// CapabilityFileName is the store-root file this registry loads.
const CapabilityFileName = "capabilities-workingcapital.json"

// PinFileName is the store-root file the working-capital pin loads.
const PinFileName = "PIN-workingcapital.json"

// PinSchemaV1 is the working-capital pin file's schema string.
const PinSchemaV1 = "gerege.workingcapital.pin/v1"

// Pin is the working-capital corpus's store-level comparability pin.
type Pin = shared.Pin

// LoadPin reads the working-capital pin.
func LoadPin(path string) (*Pin, error) {
	return shared.LoadPin(path, PinSchemaV1, "workingcapital")
}

// SeamStatus records what a capture seam can see of one capability.
type SeamStatus = shared.SeamStatus

const (
	StatusExercised = shared.StatusExercised
	StatusBlind     = shared.StatusBlind
	StatusAliased   = shared.StatusAliased
	StatusPartial   = shared.StatusPartial
)

// Capability is one named dimension of behaviour a capture either can or cannot
// see.
type Capability = shared.Capability

// Seam is one capture seam and its per-capability status map.
type Seam = shared.Seam

// CapabilityVerdict is the result of Assess.
type CapabilityVerdict = shared.CapabilityVerdict

// CapabilityRegistry is the data behind every refusal this harness issues on
// capability grounds.
type CapabilityRegistry struct {
	byName map[string]Capability
	bySeam map[string]Seam
}

// LoadCapabilityRegistry reads the registry. A missing or malformed registry is
// a hard error and never a permissive default.
func LoadCapabilityRegistry(path string) (*CapabilityRegistry, error) {
	m, err := shared.LoadCapabilityMaps(path, CapabilitySchemaV1, "workingcapital")
	if err != nil {
		return nil, err
	}
	return &CapabilityRegistry{byName: m.ByName, bySeam: m.BySeam}, nil
}

// Assess answers whether a vector's required capabilities can be graded against
// a capture from its seam, under default-deny.
func (r *CapabilityRegistry) Assess(seamName string, required []string) CapabilityVerdict {
	return shared.AssessCapability(r.byName, r.bySeam, seamName, required)
}
