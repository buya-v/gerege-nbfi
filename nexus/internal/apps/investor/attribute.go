package investor

// OutstandingInterestStrategy is the value of the OUTSTANDING_INTEREST_STRATEGY
// loan-product attribute that governs how much interest participates in an
// ownership transfer. Fineract defines exactly two values; the strategy is
// stored as an attribute key/value pair on m_external_asset_owner_loan_product_
// configurable_attributes rather than as a fixed column.
//
// [VERIFIED: ExternalAssetOwnerLoanProductAttribute.java — key
// "OUTSTANDING_INTEREST_STRATEGY"; values "TOTAL_OUTSTANDING" (due + not yet due
// + projected) and "PAYABLE_OUTSTANDING" (due + not yet due).]
type OutstandingInterestStrategy string

const (
	OutstandingInterestStrategyTotal              OutstandingInterestStrategy = "TOTAL_OUTSTANDING"
	OutstandingInterestStrategyPayableOutstanding OutstandingInterestStrategy = "PAYABLE_OUTSTANDING"
)

// StoredValue returns the exact value Fineract persists for a strategy.
func (s OutstandingInterestStrategy) StoredValue() string { return string(s) }

// OutstandingInterestStrategyKey is the attribute key under which the strategy
// is stored, shared by the persistence layer and any read-side lookup.
const OutstandingInterestStrategyKey = "OUTSTANDING_INTEREST_STRATEGY"

// LoanProductAttribute is one configured attribute row on a loan product:
// m_external_asset_owner_loan_product_configurable_attributes.
//
// [VERIFIED: ExternalAssetOwnerLoanProductAttributes.java — loan_product_id,
// attribute_key, attribute_value, all NOT NULL.]
type LoanProductAttribute struct {
	ID             int64
	LoanProductID  int64
	AttributeKey   string
	AttributeValue string
}

// OutstandingInterestStrategyFor returns the interest strategy carried by an
// attribute row when the row is the OUTSTANDING_INTEREST_STRATEGY key.
func OutstandingInterestStrategyFor(a LoanProductAttribute) (OutstandingInterestStrategy, bool) {
	if a.AttributeKey != OutstandingInterestStrategyKey {
		return "", false
	}
	switch OutstandingInterestStrategy(a.AttributeValue) {
	case OutstandingInterestStrategyTotal, OutstandingInterestStrategyPayableOutstanding:
		return OutstandingInterestStrategy(a.AttributeValue), true
	default:
		return "", false
	}
}
