package conformance

import "fmt"

// ProvenanceKindOracleCapture is the only provenance.kind a parity vector may
// carry. A vector claiming any other kind is refused at admission.
const ProvenanceKindOracleCapture = "oracle-capture"

// TenantParams is the tenant configuration a vector was captured under.
//
// The reference oracle's arithmetic reads its tenant context, so a capture taken
// under a different tenant is not a parity observation of the implementation
// under test. These six fields are that record; the content is FIXED: it names
// the tenant, its rounding mode and ordinal, its money precision and currency,
// and its timezone. A vector with the field ABSENT is UNRECORDED (graded but
// flagged); a vector with it PRESENT is checked against the store pin and
// refused on any mismatch.
type TenantParams struct {
	RoundingMode    string `json:"rounding_mode"`
	RoundingOrdinal int    `json:"rounding_ordinal"`
	Precision       int    `json:"precision"`
	Currency        string `json:"currency"`
	MinorUnits      int    `json:"minor_units"`
	Timezone        string `json:"timezone"`
}

// String renders the six tenant fields in a stable, one-line shape for refusal
// and census messages that must name both sides.
func (tp TenantParams) String() string {
	return fmt.Sprintf("{rounding_mode %s, rounding_ordinal %d, precision %d, currency %s, minor_units %d, timezone %s}",
		tp.RoundingMode, tp.RoundingOrdinal, tp.Precision, tp.Currency, tp.MinorUnits, tp.Timezone)
}
