package conformance

import (
	shared "github.com/gerege/nexus/internal/conformance"
)

// The charges capability registry and store pin, on the shared default-deny
// discipline: capability status is DATA, "exercised" is the only status that
// permits grading, and an ABSENT entry REFUSES. The registry shape and the
// refusal decision live in nexus/internal/conformance; this file keeps the
// charges-specific schema string, file names and the local struct (so the
// package's tests can build the indexed maps directly).

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
type Pin = shared.Pin

// LoadPin reads the charges pin.
func LoadPin(path string) (*Pin, error) {
	return shared.LoadPin(path, PinSchemaV1, "charges")
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
// capability grounds. The indexed maps are the only state Assess reads.
type CapabilityRegistry struct {
	byName map[string]Capability
	bySeam map[string]Seam
}

// LoadCapabilityRegistry reads the registry. A missing or malformed registry is
// a hard error and never a permissive default.
func LoadCapabilityRegistry(path string) (*CapabilityRegistry, error) {
	m, err := shared.LoadCapabilityMaps(path, CapabilitySchemaV1, "charges")
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
