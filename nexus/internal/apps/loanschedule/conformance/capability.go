package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"sort"
)

// CapabilityRegistrySchema is the only registry schema this harness accepts.
const CapabilityRegistrySchema = "gerege.loanschedule.capabilities/v1"

// SeamStatus is what one capture seam does with one capability class.
//
// The whole point of naming four states rather than a boolean is that "the seam
// does not exercise this" has several materially different causes, and a reader
// deciding whether a capture can be trusted needs to know which one applies.
// Only StatusExercised permits grading; everything else, INCLUDING an absent
// entry, refuses. Default-deny is the rule, in both directions.
type SeamStatus string

const (
	// StatusExercised: the seam passes this input through to the calculation and
	// the capture can therefore tell a correct implementation from an incorrect
	// one on it.
	StatusExercised SeamStatus = "exercised"

	// StatusBlind: the seam structurally cannot exercise this capability — the
	// input is hard-wired null, dropped by an assembler, or has no setter — so
	// an implementation that honours it and one that ignores it score
	// IDENTICALLY on every capture from this seam. A capture from a blind seam
	// has zero discriminating power here, and grading against it is not a weak
	// test: it is a test that reports green for a defect, forever.
	StatusBlind SeamStatus = "blind"

	// StatusAliased: the seam delivers a DIFFERENT value into this slot — a
	// value from another configuration scope — so the capture is not merely
	// blind, it is actively misleading about which setting produced the answer.
	StatusAliased SeamStatus = "aliased"

	// StatusPartial: the seam reaches this capability, but only on a subset of
	// the cases a reader would assume, so a capture grades less than it appears
	// to. A partial capability needs a vector that pins the subset before it can
	// be graded, and until then it refuses.
	StatusPartial SeamStatus = "partial"
)

// Capability is one capability class: a named dimension of behaviour that a
// capture either can or cannot see.
type Capability struct {
	Name string `json:"name"`

	// Description says what the capability is, in a sentence.
	Description string `json:"description"`

	// InGradedDomain records whether this capability is inside the GRADED
	// DOMAIN today — that is, whether a promoted vector exists that can tell a
	// correct implementation from an incorrect one on it. It is separate from
	// per-seam status because the two questions are independent: a capability can
	// be exercised by a seam and still be ungraded (nothing promoted), and it
	// can be inside the contract domain while no seam can see it at all.
	InGradedDomain bool `json:"in_graded_domain"`

	// Evidence is the source citation or finding id behind the two flags above.
	Evidence string `json:"evidence"`
}

// Seam is one capture seam and its per-capability status map.
type Seam struct {
	Name        string                `json:"name"`
	Description string                `json:"description"`
	Status      map[string]SeamStatus `json:"status"`
}

// CapabilityRegistry is the data behind every refusal this harness issues on
// capability grounds.
//
// It is DATA, in .softhouse/vectors/capabilities.json, rather than a table in
// this file, and that is the design decision the whole scheme turns on. The Path
// A seam's blind spots have been discovered one at a time — charges first
// (T50-N2), then holiday and non-working-day adjustment (D-2), and separately
// installmentAmountInMultiplesOf and daysInYearCustomStrategy — and nobody has
// exhaustively audited every input that seam drops. So a third, fourth and fifth
// blind spot should be expected, and the cost of recording one must be as close
// to zero as possible: adding a row here immediately refuses every affected
// vector, WITHOUT any vector file changing, without a schema migration, and
// without a code change.
type CapabilityRegistry struct {
	Schema       string       `json:"schema"`
	Note         string       `json:"note"`
	DEC1Revision int          `json:"dec1_revision"`
	Capabilities []Capability `json:"capabilities"`
	Seams        []Seam       `json:"seams"`

	byName map[string]Capability
	bySeam map[string]Seam
}

// LoadCapabilityRegistry reads the registry.
//
// A missing or malformed registry is a hard error and never a permissive
// default: a harness that graded everything because it could not find its own
// refusal rules would be the most expensive possible failure mode.
func LoadCapabilityRegistry(path string) (*CapabilityRegistry, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("capability registry: %w", err)
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, fmt.Errorf("capability registry: %w", err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	var r CapabilityRegistry
	if err := dec.Decode(&r); err != nil {
		return nil, fmt.Errorf("capability registry: %w", err)
	}
	if r.Schema != CapabilityRegistrySchema {
		return nil, fmt.Errorf("capability registry: schema %q, want %q", r.Schema, CapabilityRegistrySchema)
	}
	r.byName = make(map[string]Capability, len(r.Capabilities))
	for _, c := range r.Capabilities {
		if c.Name == "" {
			return nil, fmt.Errorf("capability registry: a capability has no name")
		}
		if _, dup := r.byName[c.Name]; dup {
			return nil, fmt.Errorf("capability registry: duplicate capability %q", c.Name)
		}
		r.byName[c.Name] = c
	}
	r.bySeam = make(map[string]Seam, len(r.Seams))
	for _, s := range r.Seams {
		if s.Name == "" {
			return nil, fmt.Errorf("capability registry: a seam has no name")
		}
		if _, dup := r.bySeam[s.Name]; dup {
			return nil, fmt.Errorf("capability registry: duplicate seam %q", s.Name)
		}
		// SORTED (T90). This loop returns on the FIRST bad entry, so ranging the
		// map directly meant that a seam with two defective capability entries
		// reported one of them at random: two runs of one binary on one
		// capabilities.json, two different fatal reasons, and a reader diffing
		// them would see a registry error appear to change. Which registries are
		// rejected does not depend on the order — every path here returns an
		// error — so this fixes WHICH defect is named first, and nothing else.
		for _, capName := range sortedKeys(s.Status) {
			st := s.Status[capName]
			if _, ok := r.byName[capName]; !ok {
				return nil, fmt.Errorf("capability registry: seam %q references unknown capability %q", s.Name, capName)
			}
			switch st {
			case StatusExercised, StatusBlind, StatusAliased, StatusPartial:
			default:
				return nil, fmt.Errorf("capability registry: seam %q capability %q has unknown status %q",
					s.Name, capName, st)
			}
		}
		r.bySeam[s.Name] = s
	}
	return &r, nil
}

// CapabilityVerdict is the registry's answer for one vector.
type CapabilityVerdict struct {
	// Gradeable is true only when every required capability is both exercised by
	// the seam and inside the graded domain.
	Gradeable bool

	// Reason is the machine-readable refusal reason when Gradeable is false.
	Reason RefusalReason

	// Detail explains the refusal in the report, naming the capability, the
	// status and the evidence, so a reader never has to open the registry to
	// understand why a vector was refused.
	Detail []string
}

// RefusalReason distinguishes the kinds of refusal, because they retire
// differently: a seam-blind vector is retired by RE-CAPTURING on another seam,
// an ungraded capability by PROMOTING a vector, and an ungraded request value by
// WIDENING the graded domain.
type RefusalReason string

const (
	ReasonNone RefusalReason = ""

	// ReasonUnknownSeam: the vector's seam is not in the registry.
	ReasonUnknownSeam RefusalReason = "UNKNOWN_SEAM"

	// ReasonUnknownCapability: the vector requires a capability the registry does
	// not define, or the registry has no status for it on this seam.
	ReasonUnknownCapability RefusalReason = "UNKNOWN_CAPABILITY"

	// ReasonSeamBlind: the capture seam structurally cannot exercise a required
	// capability, so grading against this capture would be broken by
	// construction.
	ReasonSeamBlind RefusalReason = "SEAM_BLIND"

	// ReasonUngradedCapability: the capability is outside the graded domain.
	ReasonUngradedCapability RefusalReason = "UNGRADED_CAPABILITY"

	// ReasonUngradedRequest: a request FIELD VALUE is outside the graded domain
	// listed on contract.GenerateRequest.
	ReasonUngradedRequest RefusalReason = "UNGRADED_REQUEST"
)

// IsGraded reports whether a capability is currently inside the graded domain.
// It is the single data-driven answer used everywhere; nothing in this harness
// hard-codes a capability's status, so admitting DayCountActualActual (or any
// other arm) is one edit to capabilities.json.
func (r *CapabilityRegistry) IsGraded(name string) (graded, defined bool) {
	c, ok := r.byName[name]
	if !ok {
		return false, false
	}
	return c.InGradedDomain, true
}

// GradedCapabilities lists the capabilities currently inside the graded domain.
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

// CounterfactualCoverage answers, for every capability inside the graded domain,
// whether some ADMISSIBLE PARITY vector names a wrong implementation it kills.
//
// This is the honest form of "in the graded domain". A capability marked graded
// with no vector killing a named candidate defect for it is an unbacked claim, and
// it is exactly the situation the whole program exists to prevent: a port that
// passes its corpus and is wrong. The check is expressed over named
// counterfactuals rather than over capture pairs because pair difference is the
// wrong filter — see the Counterfactual doc comment and finding T55-N1.
//
// Returned maps are capability -> the counterfactual ids covering it, and the
// sorted list of graded capabilities with no coverage at all.
//
// A REFUSED VECTOR BACKS NOTHING (finding A2-19 F3), and this function decides
// that for itself rather than trusting the caller to have filtered. That is the
// whole shape of the defect it fixes: Run handed in every vector it had not
// declared INADMISSIBLE, a refused vector is not inadmissible, and so kills from
// vectors the harness had just declined to grade were credited as coverage. The
// measured effect was that adding a refused vector took UNBACKED from 1 to 0 —
// the case with LESS evidence produced the QUIETER report.
//
// Deciding it here rather than at the call site is deliberate. Coverage is the
// number a reader trusts, the caller-side filter is what failed, and a second
// caller (a future report, a tool, a test) would have had to rediscover the rule.
// Re-asking is idempotent: a caller that has already dropped its refused vectors
// gets exactly the same answer.
//
// ADMISSIBILITY IS STILL THE CALLER'S JOB. It needs the pin and the repo root,
// which this registry does not have, and it is a different question — an
// inadmissible file is not a vector at all. Run filters it before calling.
func (r *CapabilityRegistry) CounterfactualCoverage(vectors []*Vector) (map[string][]string, []string) {
	covered := map[string][]string{}
	for _, v := range vectors {
		if v.Class != ClassParity {
			continue
		}
		if verdict := r.RefusalFor(v); !verdict.Gradeable {
			// "Not a pass, not a failure": the seam is blind to something this case
			// needs, a required capability is outside the graded domain, the seam or
			// a capability is not in the registry at all, or the request itself is
			// outside the graded domain. In every one of those five cases the vector
			// separated no implementation from any other, so it kills nothing — and
			// a kill that catches nothing must not back a capability and must not
			// print as killing anything. Same rule as the withdrawn structural cell
			// below, reached by a different route.
			continue
		}
		for _, cf := range v.GradedAgainst {
			// FINDING T9-F1b: a structural kill whose every divergent cell has
			// been withdrawn from grading covers NOTHING and must not print as
			// killing anything. See Vector.StructuralKillIsCompared.
			if !v.StructuralKillIsCompared(cf) {
				continue
			}
			if graded, defined := r.IsGraded(cf.Capability); defined && graded {
				// The kind is carried into the coverage listing, because "this
				// capability is covered" reads very differently when every
				// counterfactual covering it is a zero-margin structural kill —
				// a real kill, but not one that grades an AMOUNT (finding D-4).
				id := cf.ID
				if cf.Kind == CounterfactualStructural {
					id += " [structural]"
				}
				covered[cf.Capability] = append(covered[cf.Capability], id)
			}
		}
	}
	var uncovered []string
	for _, name := range r.GradedCapabilities() {
		if len(covered[name]) == 0 {
			uncovered = append(uncovered, name)
		}
	}
	for k := range covered {
		sort.Strings(covered[k])
	}
	return covered, uncovered
}

// RefusalFor is THE refusal predicate for a whole vector: does this harness
// decline to grade it, and on what ground.
//
// It exists because there were two answers to that question and only one of them
// was ever consulted twice. gradeVector asked Assess and then GradedDomain,
// inline, and decided the OUTCOME; every other reader of "is this vector
// refused?" — the coverage report above all — had to re-derive it or, as the
// coverage report did, not derive it at all (finding A2-19 F3). One predicate,
// one answer, and a caller that cannot accidentally consult half of it.
//
// It deliberately does NOT re-check admissibility. That needs the pin and the
// repo root, and it is a different question: an inadmissible file is not a vector
// at all, whereas a refused vector is a well-formed vector this corpus cannot
// grade. Callers filter inadmissible separately, as Run does.
//
// The order matches gradeVector's normative precedence: the capability
// obstruction is reported before the request one, because a seam that cannot see
// something is a stronger obstruction than a value nobody has promoted a vector
// for, and the two must not disagree about which comes first depending on who
// asked.
func (r *CapabilityRegistry) RefusalFor(v *Vector) CapabilityVerdict {
	if verdict := r.Assess(v.Oracle.Seam, v.CapabilitiesRequired); !verdict.Gradeable {
		return verdict
	}
	if v.Expect.Kind == "schedule" {
		if ok, why := GradedDomain(v); !ok {
			return CapabilityVerdict{Reason: ReasonUngradedRequest, Detail: why}
		}
	}
	return CapabilityVerdict{Gradeable: true}
}

// Assess answers whether a vector's required capabilities can be graded against
// a capture from its seam.
//
// Precedence mirrors the contract's normative error precedence: the STRONGEST
// obstruction is reported first, so two readers of the same report reach the same
// conclusion about what has to happen next. A seam that cannot see the capability
// at all is a stronger obstruction than a capability nobody has promoted a vector
// for, because the former cannot be fixed by promoting anything.
func (r *CapabilityRegistry) Assess(seamName string, required []string) CapabilityVerdict {
	seam, ok := r.bySeam[seamName]
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
		return CapabilityVerdict{Reason: ReasonUnknownCapability, Detail: unknown}
	case len(blind) > 0:
		return CapabilityVerdict{Reason: ReasonSeamBlind, Detail: blind}
	case len(ungraded) > 0:
		return CapabilityVerdict{Reason: ReasonUngradedCapability, Detail: ungraded}
	}
	return CapabilityVerdict{Gradeable: true}
}
