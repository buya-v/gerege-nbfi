package conformance

import (
	shared "github.com/gerege/nexus/internal/conformance"
)

// CapabilitySchemaV1 is the branch capability file's schema string.
const CapabilitySchemaV1 = "gerege.branch.capabilities/v1"

// CapabilityFileName is the store-root file this registry loads.
const CapabilityFileName = "capabilities-branch.json"

// PinFileName is the store-root file the branch pin loads.
const PinFileName = "PIN-branch.json"

// PinSchemaV1 is the branch pin file's schema string.
const PinSchemaV1 = "gerege.branch.pin/v1"

// Pin is the branch corpus's store-level comparability pin.
type Pin = shared.Pin

// LoadPin reads the branch pin.
func LoadPin(path string) (*Pin, error) {
	return shared.LoadPin(path, PinSchemaV1, "branch")
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

const (
	reasonUnknownSeam       = shared.ReasonUnknownSeam
	reasonUnknownCapability = shared.ReasonUnknownCapability
	reasonSeamBlind         = shared.ReasonSeamBlind
	reasonUngraded          = shared.ReasonUngraded
)

// CapabilityRegistry is the data behind every refusal this harness issues on
// capability grounds.
type CapabilityRegistry struct {
	byName map[string]Capability
	bySeam map[string]Seam
}

// LoadCapabilityRegistry reads the registry.
func LoadCapabilityRegistry(path string) (*CapabilityRegistry, error) {
	m, err := shared.LoadCapabilityMaps(path, CapabilitySchemaV1, "branch")
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
