package investor

// ExternalAssetOwner is the m_external_asset_owner aggregate root: a legal
// entity that can acquire ownership of a loan through an ExternalAssetOwnerTransfer.
// Its identity is an external id string; Fineract wraps it in an ExternalId
// value object whose database representation is the raw text.
//
// [VERIFIED: ExternalAssetOwner.java — @Table(name="m_external_asset_owner"),
// external_id NOT NULL UNIQUE length 100.]
type ExternalAssetOwner struct {
	ID         int64
	ExternalID string
}

// ExternalIDFor returns the stored external id for an owner, or an empty string
// when the owner is nil (a nil previous owner is legal on the first transfer).
func ExternalIDFor(o *ExternalAssetOwner) string {
	if o == nil {
		return ""
	}
	return o.ExternalID
}
