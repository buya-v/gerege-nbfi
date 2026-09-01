package provisioning

import "fmt"

// CriteriaDefinition is one age band of a provisioning criteria: for a given
// provisioning category it maps a closed overdue-age interval [MinimumAge,
// MaximumAge] to a reserve percentage and a liability/expense GL account pair.
//
// [VERIFIED: ProvisioningCriteriaDefinition.java — @Table(name =
// "m_provisioning_criteria_definition"), min_age/max_age NOT NULL,
// provision_percentage NOT NULL, liability_account/expense_account NOT NULL.]
type CriteriaDefinition struct {
	ID               int64
	CategoryID       int64
	MinimumAge       int64
	MaximumAge       int64
	Percentage       Percent
	LiabilityAccount int64
	ExpenseAccount   int64
}

// Matches reports whether overdueInDays falls inside the closed age band,
// porting the SQL predicate the oracle's provisioning query applies:
//
//	pcd.min_age <= overdueInDays AND overdueInDays <= pcd.max_age
//
// [VERIFIED: ProvisioningEntriesReadPlatformServiceImpl.java:75-77 (the
// m_provisioning_criteria_definition join predicate).]
func (d CriteriaDefinition) Matches(overdueInDays int64) bool {
	return d.MinimumAge <= overdueInDays && overdueInDays <= d.MaximumAge
}

// Overlaps ports ProvisioningCriteriaDefinition.isOverlapping
// [VERIFIED: ProvisioningCriteriaDefinition.java:94-96 — minimumAge <=
// def.maximumAge && def.minimumAge <= maximumAge]. Two definitions overlap when
// their closed bands intersect; the write path rejects any criteria whose
// definitions overlap so a given overdue age maps to exactly one reserve rate.
func (d CriteriaDefinition) Overlaps(other CriteriaDefinition) bool {
	return d.MinimumAge <= other.MaximumAge && other.MinimumAge <= d.MaximumAge
}

// Criteria is the Go port of the m_provisioning_criteria aggregate: a named set
// of age-band definitions plus the loan products mapped to it.
// [VERIFIED: ProvisioningCriteria.java — @Table(name = "m_provisioning_criteria"),
// criteria_name unique NOT NULL, one-to-many provisioningCriteriaDefinition and
// loanProductMapping.]
type Criteria struct {
	ID             int64
	Name           string
	Definitions    []CriteriaDefinition
	LoanProductIDs []int64
}

// ReserveRate returns the single definition whose age band contains
// overdueInDays. ok is false when overdueInDays falls in a gap between bands,
// which is exactly the case the oracle's join drops (no row) rather than
// erroring. Callers treat !ok as "no provisioning entry for this loan".
func (c Criteria) ReserveRate(overdueInDays int64) (CriteriaDefinition, bool) {
	for _, d := range c.Definitions {
		if d.Matches(overdueInDays) {
			return d, true
		}
	}
	return CriteriaDefinition{}, false
}

// OverlappingPairs returns every pair of definitions (i, j, i < j) whose age
// bands overlap, porting the pairwise validation in
// ProvisioningCriteriaAssembler.validateRange
// [VERIFIED: ProvisioningCriteriaAssembler.java:78-88]. An empty result means
// the criteria is well-formed: no overdue age maps to two reserve rates.
func (c Criteria) OverlappingPairs() []DefinitionPair {
	var pairs []DefinitionPair
	for i := 0; i < len(c.Definitions); i++ {
		for j := i + 1; j < len(c.Definitions); j++ {
			if c.Definitions[i].Overlaps(c.Definitions[j]) {
				pairs = append(pairs, DefinitionPair{I: i, J: j})
			}
		}
	}
	return pairs
}

// DefinitionPair identifies a pair of overlapping definitions by slice index.
type DefinitionPair struct {
	I, J int
}

// ValidateRange returns an error describing the first overlap found, or nil if
// none. It mirrors ProvisioningCriteriaAssembler.validateRange, which throws
// ProvisioningCriteriaOverlappingDefinitionException on the first overlap.
func (c Criteria) ValidateRange() error {
	if pairs := c.OverlappingPairs(); len(pairs) > 0 {
		p := pairs[0]
		return fmt.Errorf("provisioning: criteria %q definitions %d and %d are overlapping (bands [%d,%d] and [%d,%d])",
			c.Name, p.I, p.J,
			c.Definitions[p.I].MinimumAge, c.Definitions[p.I].MaximumAge,
			c.Definitions[p.J].MinimumAge, c.Definitions[p.J].MaximumAge)
	}
	return nil
}
