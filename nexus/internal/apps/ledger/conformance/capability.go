package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"
)

// The ledger capability registry and the store pin.
//
// ---------------------------------------------------------------------------
// DEC-2 PRECONDITION P-6, DECIDED HERE, WITH THE ALTERNATIVE RECORDED
// ---------------------------------------------------------------------------
//
// P-6 asks where ledger capability rows live, given that
// `.softhouse/vectors/capabilities.json` declares the HARD CONSTANT schema id
// `gerege.loanschedule.capabilities/v1` and a SINGULAR `dec1_revision`. DEC-2
// §5.3 ranks it FIRST of the preconditions and says it "must not be improvised".
//
// DECISION: a SEPARATE store-root file, `.softhouse/vectors/capabilities-ledger.json`,
// carrying schema `gerege.ledger.capabilities/v1` and a `dec2_revision`.
//
// REASONS, in the order they weigh:
//
//  1. `dec1_revision` is a DEC-1 revision number. Appending ledger rows to a
//     file versioned by it would make an amendment of the LOANSCHEDULE contract
//     the thing that re-stamps the LEDGER context's capability data. That is
//     exactly the semantic error P-7 names one row down, arriving through a
//     different field.
//  2. The schema id is a hard constant naming the other context. A file whose
//     own schema string says `loanschedule` while half its rows are `ledger`
//     rows is a name that lies, and the first harness has already paid for one
//     of those (`LoanScheduleTreeRel`, renamed by T166 because "a name that lies
//     is how this hid").
//  3. It keeps this package free of any import of the loanschedule harness,
//     which is the boundary DEC-2 §5.2's adopted disposition rests on.
//
// REJECTED ALTERNATIVE, recorded because P-6 says it must not be improvised:
// append `ledger` rows to `capabilities.json`. It works today — the loader's
// strict decode would accept them, since the rows are a list — and it is one
// fewer file. It is rejected on (1) and (2) above. The cost of the rejection is
// one more entry in `storeRootNonVectorFiles` and one more loader; the cost of
// accepting it would have been a DEC-1 revision number governing DEC-2 data,
// which is not reversible by a later edit to a comment.
//
// WHAT §5.2's "SHARES THE CAPABILITY REGISTRY" MEANS UNDER THIS DECISION, since
// the two sentences can be read as conflicting and a reader deserves the
// resolution rather than the ambiguity: what is shared is the REGISTRY
// DISCIPLINE — capability status is DATA, `exercised` is the only status that
// permits grading, and an ABSENT entry REFUSES (default-deny, §4.10). Every one
// of those is implemented below. If the file itself were simply shared, P-6
// would not be a precondition at all; DEC-2 lists it precisely because the file
// is "named and versioned for one context".

// CapabilitySchemaV1 is the ledger capability file's schema string.
const CapabilitySchemaV1 = "gerege.ledger.capabilities/v1"

// CapabilityFileName is the store-root file this registry loads.
const CapabilityFileName = "capabilities-ledger.json"

// PinFileName is the store-root file the ledger pin loads.
const PinFileName = "PIN-ledger.json"

// PinSchemaV1 is the ledger pin file's schema string.
const PinSchemaV1 = "gerege.ledger.pin/v1"

// Pin is the ledger corpus's store-level comparability pin.
//
// IT CARRIES NO CONTRACT DIGEST, and DEC-2 §1.1 is why: this ADR "does not
// create or freeze a Go file, and could not", there is "no counterpart file for
// this context", and "no PIN digest appears in this document at all". A pin
// field for a digest that does not exist would be a slot inviting somebody to
// fill it with the wrong file.
type Pin struct {
	Schema         string `json:"schema"`
	Note           string `json:"_note"`
	DEC2Revision   int    `json:"dec2_revision"`
	FineractCommit string `json:"fineract_commit"`

	// InadmissibleProductIDs is G-10 option (c) as data.
	//
	// It is a list and not a hard-coded switch for the same reason
	// capabilities.json is data: a product that becomes admissible again — or a
	// sixth that becomes inadmissible — is one edit here and refuses or admits
	// every affected vector with no code change.
	InadmissibleProductIDs []int64 `json:"inadmissible_product_ids"`

	// TenantParams is the tenant configuration this corpus is graded under.
	//
	// R2a: a vector that DECLARES tenant_params is checked against this, and
	// refused on any mismatch. It lives on the pin (not hard-coded in Go) for
	// the same reason production_rounding lives on PIN.json: when the ratified
	// tenant changes, re-stamping the corpus is one edit here rather than a
	// source edit. The content is FIXED by R2a to the `gerege` tenant.
	TenantParams TenantParams `json:"tenant_params"`
}

// LoadPin reads the ledger pin.
func LoadPin(path string) (*Pin, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("ledger pin: %w", err)
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, fmt.Errorf("ledger pin %s: %w", path, err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var p Pin
	if err := dec.Decode(&p); err != nil {
		return nil, fmt.Errorf("ledger pin %s: decode: %w", path, err)
	}
	if p.Schema != PinSchemaV1 {
		return nil, fmt.Errorf("ledger pin %s: schema %q, want %q", path, p.Schema, PinSchemaV1)
	}
	if p.DEC2Revision <= 0 {
		return nil, fmt.Errorf("ledger pin %s: dec2_revision must be positive, got %d",
			path, p.DEC2Revision)
	}
	if p.FineractCommit == "" {
		return nil, fmt.Errorf("ledger pin %s: fineract_commit is empty", path)
	}
	// An ABSENT pin declaration is UNRECORDED, not fatal — the same rule this
	// mechanism applies to a vector. Nobody has yet established what the existing
	// corpus was captured under, and inventing a value here would make the
	// mismatch check compare the tree's own expectation against itself. A pin
	// that declares NOTHING disables the cross-check and says so; a pin that
	// declares SOMETHING must declare it completely.
	declared := p.TenantParams.RoundingMode != "" || p.TenantParams.Currency != "" ||
		p.TenantParams.Timezone != "" || p.TenantParams.Precision > 0
	if declared && (p.TenantParams.RoundingMode == "" || p.TenantParams.Currency == "" ||
		p.TenantParams.Timezone == "" || p.TenantParams.Precision <= 0 ||
		p.TenantParams.MinorUnits < 0) {
		return nil, fmt.Errorf("ledger pin %s: tenant_params is PARTIAL: %s — declare every field "+
			"or none. A partial declaration cannot be checked against and hides which half is "+
			"unknown", path, p.TenantParams)
	}
	return &p, nil
}

// Capability is one capability class and whether it is in the graded domain.
type Capability struct {
	Name           string `json:"name"`
	Description    string `json:"description"`
	InGradedDomain bool   `json:"in_graded_domain"`
	Evidence       string `json:"evidence"`

	// UnpostedSlots is the STRUCTURED half of a not-graded row's reason: the
	// product/slot pairs this corpus has never posted through.
	//
	// It exists because the prose half was where A2-34 F-4 lived. "gl 18, 22, 16
	// have ZERO journal entries" was a hand-maintained list of account ids
	// making a live-database claim, printed as a measured fact on every run, and
	// wrong on one of the three — in the direction that understated activity, on
	// the account this corpus exercises MOST. Recording the SLOT instead makes
	// the claim checkable: the slot name is derived from the ported enum at load
	// time and the account's activity is measured from the store at render time.
	// See notgraded.go for the full derivation and for what is still NOT
	// derivable.
	//
	// OPTIONAL. Most not-graded rows have no slot to name.
	UnpostedSlots []UnpostedSlot `json:"unposted_slots,omitempty"`
}

// Seam records which capabilities one capture seam structurally exercises.
type Seam struct {
	Name        string            `json:"name"`
	Description string            `json:"description"`
	Status      map[string]string `json:"status"`
}

// CapabilityRegistry is the loaded ledger capability file.
type CapabilityRegistry struct {
	Schema       string       `json:"schema"`
	DEC2Revision int          `json:"dec2_revision"`
	Note         string       `json:"_note"`
	Capabilities []Capability `json:"capabilities"`
	Seams        []Seam       `json:"seams"`
}

// LoadCapabilityRegistry reads the ledger capability file.
func LoadCapabilityRegistry(path string) (*CapabilityRegistry, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("ledger capability registry: %w", err)
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, fmt.Errorf("ledger capability registry %s: %w", path, err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var r CapabilityRegistry
	if err := dec.Decode(&r); err != nil {
		return nil, fmt.Errorf("ledger capability registry %s: decode: %w", path, err)
	}
	if r.Schema != CapabilitySchemaV1 {
		return nil, fmt.Errorf("ledger capability registry %s: schema %q, want %q",
			path, r.Schema, CapabilitySchemaV1)
	}
	if len(r.Capabilities) == 0 {
		return nil, fmt.Errorf("ledger capability registry %s: declares no capabilities. A registry "+
			"that lists nothing refuses nothing", path)
	}
	if len(r.Seams) == 0 {
		return nil, fmt.Errorf("ledger capability registry %s: declares no seams", path)
	}
	// UNPOSTED SLOTS ARE VALIDATED AT LOAD, so a slot code the oracle's own enum
	// does not define REFUSES THE RUN (exit 2) instead of reaching the report as
	// a name nobody checked. This is the gate that stands where A2-34 F-4's
	// hand-maintained account list used to stand.
	for _, c := range r.Capabilities {
		if len(c.UnpostedSlots) == 0 {
			continue
		}
		if c.InGradedDomain {
			return nil, fmt.Errorf(
				"ledger capability registry %s: capability %q is in_graded_domain TRUE and also "+
					"declares unposted_slots. A slot this corpus has never posted through cannot be "+
					"part of a capability the corpus grades; one of the two statements is wrong",
				path, c.Name)
		}
		for _, u := range c.UnpostedSlots {
			if err := u.validate(c.Name); err != nil {
				return nil, fmt.Errorf("ledger capability registry %s: %w", path, err)
			}
		}
	}
	return &r, nil
}

func (r *CapabilityRegistry) capability(name string) (Capability, bool) {
	for _, c := range r.Capabilities {
		if c.Name == name {
			return c, true
		}
	}
	return Capability{}, false
}

func (r *CapabilityRegistry) seam(name string) (Seam, bool) {
	for _, s := range r.Seams {
		if s.Name == name {
			return s, true
		}
	}
	return Seam{}, false
}

// Refusals returns every capability-grounded reason this vector may not be
// graded.
//
// DEFAULT-DENY IN BOTH DIRECTIONS, which is §4.10's rule and the first
// registry's hard-won discipline: an unknown capability refuses, a capability
// outside the graded domain refuses, an unknown seam refuses, and a seam whose
// status for a required capability is ABSENT refuses. "Absent" is the one that
// matters — an unaudited input is assumed invisible and never assumed wired.
func (r *CapabilityRegistry) Refusals(v *Vector) []string {
	var out []string
	seam, ok := r.seam(v.Oracle.Seam)
	if !ok {
		return []string{fmt.Sprintf(
			"oracle.seam %q is not a seam this registry declares (have: %s). ABSENT REFUSES",
			v.Oracle.Seam, strings.Join(r.seamNames(), ", "))}
	}
	for _, name := range v.CapabilitiesRequired {
		c, known := r.capability(name)
		if !known {
			out = append(out, fmt.Sprintf(
				"capabilities_required names %q, which this registry does not declare. ABSENT REFUSES: "+
					"an unaudited capability is assumed invisible, never assumed wired", name))
			continue
		}
		if !c.InGradedDomain {
			out = append(out, fmt.Sprintf(
				"capability %q is marked in_graded_domain FALSE: %s", name, c.Evidence))
			continue
		}
		status, present := seam.Status[name]
		if !present {
			out = append(out, fmt.Sprintf(
				"seam %q declares NO STATUS for capability %q. ABSENT REFUSES", seam.Name, name))
			continue
		}
		if status != "exercised" {
			out = append(out, fmt.Sprintf(
				"seam %q is %q for capability %q, and only \"exercised\" permits grading",
				seam.Name, status, name))
		}
	}
	return out
}

func (r *CapabilityRegistry) seamNames() []string {
	out := make([]string, 0, len(r.Seams))
	for _, s := range r.Seams {
		out = append(out, s.Name)
	}
	sort.Strings(out)
	return out
}

// GradedCapabilities lists the capabilities marked in_graded_domain.
func (r *CapabilityRegistry) GradedCapabilities() []string {
	var out []string
	for _, c := range r.Capabilities {
		if c.InGradedDomain {
			out = append(out, c.Name)
		}
	}
	sort.Strings(out)
	return out
}

// UncoveredGradedCapabilities returns the capabilities marked in_graded_domain
// that NO graded parity vector names a money-or-structural kill for.
//
// This is the first harness's coverage rule, ported deliberately: "in the graded
// domain" means a vector exists that can tell a correct implementation from an
// incorrect one, and a capability nothing kills for is a capability marked
// graded on nobody's authority.
func (r *CapabilityRegistry) UncoveredGradedCapabilities(graded []*Vector) []string {
	covered := map[string]bool{}
	for _, v := range graded {
		if len(v.GradedAgainst) == 0 {
			continue
		}
		for _, c := range v.CapabilitiesRequired {
			covered[c] = true
		}
	}
	var out []string
	for _, name := range r.GradedCapabilities() {
		if !covered[name] {
			out = append(out, name)
		}
	}
	return out
}
