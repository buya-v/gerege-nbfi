package investor

import "time"

// ExternalAssetOwnerTransfer is the m_external_asset_owner_transfer aggregate
// root: one transfer of a loan's ownership from a previous owner to a new owner.
// It is the unit the transfer state machine advances through the
// ExternalTransferStatus vocabulary.
//
// [VERIFIED: ExternalAssetOwnerTransfer.java — owner_id, external_id, status,
// sub_status, purchase_price_ratio, settlement_date, effective_date_from,
// effective_date_to, loan_id, external_loan_id, external_group_id,
// previous_owner_id.]
type ExternalAssetOwnerTransfer struct {
	ID                 int64
	Owner              *ExternalAssetOwner
	PreviousOwner      *ExternalAssetOwner
	ExternalID         string
	Status             ExternalTransferStatus
	SubStatus          ExternalTransferSubStatus
	PurchasePriceRatio string
	SettlementDate     time.Time
	EffectiveDateFrom  time.Time
	EffectiveDateTo    time.Time
	LoanID             int64
	ExternalLoanID     string
	ExternalGroupID    string
	Details            ExternalAssetOwnerTransferDetails
}

// ExternalAssetOwnerTransferDetails is the one-to-one derived-balance snapshot
// attached to a transfer (m_external_asset_owner_transfer_details). It records
// the loan's outstanding decomposition at the moment the transfer was priced.
//
// [VERIFIED: ExternalAssetOwnerTransferDetails.java — the six *_derived columns,
// scale 6, precision 19, NOT NULL; setTotalOutstanding is DERIVED from the four
// component buckets via MathUtil.add.]
type ExternalAssetOwnerTransferDetails struct {
	PrincipalOutstanding      MinorUnits
	InterestOutstanding       MinorUnits
	FeeChargesOutstanding     MinorUnits
	PenaltyChargesOutstanding MinorUnits
	TotalOutstanding          MinorUnits
	TotalOverpaid             MinorUnits
}

// TotalOutstanding derives the snapshot total from the four component buckets,
// exactly mirroring ExternalAssetOwnerTransferDetails.updateTotalOutstanding
// [VERIFIED: ExternalAssetOwnerTransferDetails.java — MathUtil.add of principal,
// interest, fee charges, penalty charges]. It is never persisted independently.
func (d ExternalAssetOwnerTransferDetails) DeriveTotalOutstanding() MinorUnits {
	return d.PrincipalOutstanding + d.InterestOutstanding + d.FeeChargesOutstanding + d.PenaltyChargesOutstanding
}

// NormalizedTotalOutstanding returns the derived total when it differs from the
// stored total; the caller may use it to verify a round-trip. It exists to make
// the derive-don't-store rule explicit on read paths.
func (d ExternalAssetOwnerTransferDetails) NormalizedTotalOutstanding() MinorUnits {
	return d.DeriveTotalOutstanding()
}
