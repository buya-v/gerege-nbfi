package investor

import (
	"context"
	"fmt"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL storage layer for the investor slice. It follows
// the package rule used by the ledger package: no concrete pgx type is named
// here, and a postgres.DB (Querier + Executor) captured at construction carries
// every statement. The import graph stays
// investor -> internal/platform/postgres -> pgx/v5.

// OwnerRepository is the persistence surface for m_external_asset_owner.
type OwnerRepository interface {
	Upsert(ctx context.Context, owner ExternalAssetOwner) (int64, error)
	FindByExternalID(ctx context.Context, externalID string) (*ExternalAssetOwner, error)
}

// PostgresOwnerRepository persists m_external_asset_owner rows.
type PostgresOwnerRepository struct {
	db postgres.DB
}

// NewPostgresOwnerRepository constructs the owner persistence surface.
func NewPostgresOwnerRepository(db postgres.DB) *PostgresOwnerRepository {
	return &PostgresOwnerRepository{db: db}
}

// Upsert inserts an owner keyed by external_id, returning its id. On conflict
// on external_id it returns the existing id without error.
func (r *PostgresOwnerRepository) Upsert(ctx context.Context, owner ExternalAssetOwner) (int64, error) {
	if owner.ID != 0 {
		return owner.ID, nil
	}
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_external_asset_owner (external_id) VALUES ($1)
ON CONFLICT (external_id) DO UPDATE SET external_id = EXCLUDED.external_id
RETURNING id`, owner.ExternalID)
	if err != nil {
		return 0, fmt.Errorf("investor: upsert external asset owner: %w", err)
	}
	return id, nil
}

// FindByExternalID resolves one owner by external_id, or (nil, nil) on a miss.
func (r *PostgresOwnerRepository) FindByExternalID(ctx context.Context, externalID string) (*ExternalAssetOwner, error) {
	var out *ExternalAssetOwner
	err := postgres.QueryRows(ctx, r.db, `SELECT id, external_id
FROM m_external_asset_owner WHERE external_id = $1`, []any{externalID},
		func(s postgres.RowScanner) error {
			var o ExternalAssetOwner
			if err := s.Scan(&o.ID, &o.ExternalID); err != nil {
				return err
			}
			out = &o
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("investor: find external asset owner: %w", err)
	}
	return out, nil
}

// TransferRepository is the persistence surface for m_external_asset_owner_transfer
// and its one-to-one details table.
type TransferRepository interface {
	Insert(ctx context.Context, t ExternalAssetOwnerTransfer) (int64, error)
	FindByID(ctx context.Context, id int64) (*ExternalAssetOwnerTransfer, error)
	FindByLoanID(ctx context.Context, loanID int64) ([]ExternalAssetOwnerTransfer, error)
}

// PostgresTransferRepository persists transfer + details rows.
type PostgresTransferRepository struct {
	db postgres.DB
}

// NewPostgresTransferRepository constructs the transfer persistence surface.
func NewPostgresTransferRepository(db postgres.DB) *PostgresTransferRepository {
	return &PostgresTransferRepository{db: db}
}

// Insert writes the transfer row and its details row, resolving the owner and
// previous-owner ids through the supplied aggregates.
func (r *PostgresTransferRepository) Insert(ctx context.Context, t ExternalAssetOwnerTransfer) (int64, error) {
	var ownerID *int64
	if t.Owner != nil {
		ownerID = &t.Owner.ID
	}
	var prevID *int64
	if t.PreviousOwner != nil {
		prevID = &t.PreviousOwner.ID
	}

	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_external_asset_owner_transfer
(owner_id, previous_owner_id, external_id, status, sub_status, purchase_price_ratio,
 settlement_date, effective_date_from, effective_date_to, loan_id, external_loan_id, external_group_id)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
RETURNING id`,
		ownerID, prevID, t.ExternalID, t.Status.StoredValue(), t.SubStatus.StoredValue(),
		t.PurchasePriceRatio, t.SettlementDate, t.EffectiveDateFrom, t.EffectiveDateTo,
		t.LoanID, nullIfEmpty(t.ExternalLoanID), nullIfEmpty(t.ExternalGroupID))
	if err != nil {
		return 0, fmt.Errorf("investor: insert transfer: %w", err)
	}

	if _, err := r.db.Exec(ctx, `INSERT INTO m_external_asset_owner_transfer_details
(asset_owner_transfer_id, principal_outstanding_derived, interest_outstanding_derived,
 fee_charges_outstanding_derived, penalty_charges_outstanding_derived,
 total_outstanding_derived, total_overpaid_derived)
VALUES ($1,$2,$3,$4,$5,$6,$7)`,
		id,
		t.Details.PrincipalOutstanding.FormatDecimal(MNTMinorDigits),
		t.Details.InterestOutstanding.FormatDecimal(MNTMinorDigits),
		t.Details.FeeChargesOutstanding.FormatDecimal(MNTMinorDigits),
		t.Details.PenaltyChargesOutstanding.FormatDecimal(MNTMinorDigits),
		t.Details.TotalOutstanding.FormatDecimal(MNTMinorDigits),
		t.Details.TotalOverpaid.FormatDecimal(MNTMinorDigits)); err != nil {
		return 0, fmt.Errorf("investor: insert transfer details: %w", err)
	}
	return id, nil
}

// FindByID resolves one transfer (with its details) by id, or (nil, nil) on a miss.
func (r *PostgresTransferRepository) FindByID(ctx context.Context, id int64) (*ExternalAssetOwnerTransfer, error) {
	transfers, err := r.find(ctx, `WHERE id = $1`, id)
	if err != nil {
		return nil, err
	}
	if len(transfers) == 0 {
		return nil, nil
	}
	t := transfers[0]
	if err := r.loadDetails(ctx, &t); err != nil {
		return nil, err
	}
	return &t, nil
}

// FindByLoanID returns every transfer that ever touched a given loan, in id order.
func (r *PostgresTransferRepository) FindByLoanID(ctx context.Context, loanID int64) ([]ExternalAssetOwnerTransfer, error) {
	return r.find(ctx, `WHERE loan_id = $1 ORDER BY id`, loanID)
}

func (r *PostgresTransferRepository) find(ctx context.Context, where string, args ...any) ([]ExternalAssetOwnerTransfer, error) {
	var out []ExternalAssetOwnerTransfer
	err := postgres.QueryRows(ctx, r.db, `SELECT id, owner_id, previous_owner_id, external_id,
status, sub_status, purchase_price_ratio, settlement_date::text,
effective_date_from::text, effective_date_to::text, loan_id, external_loan_id, external_group_id
FROM m_external_asset_owner_transfer `+where, args,
		func(s postgres.RowScanner) error {
			var t ExternalAssetOwnerTransfer
			var statusText, subStatusText string
			var ownerID, prevID *int64
			var extLoanID, extGroupID *string
			if err := s.Scan(&t.ID, &ownerID, &prevID, &t.ExternalID,
				&statusText, &subStatusText, &t.PurchasePriceRatio, &t.SettlementDate,
				&t.EffectiveDateFrom, &t.EffectiveDateTo, &t.LoanID, &extLoanID,
				&extGroupID); err != nil {
				return err
			}
			t.Status = ExternalTransferStatus(statusText)
			t.SubStatus = ExternalTransferSubStatus(subStatusText)
			if ownerID != nil {
				t.Owner = &ExternalAssetOwner{ID: *ownerID}
			}
			if prevID != nil {
				t.PreviousOwner = &ExternalAssetOwner{ID: *prevID}
			}
			if extLoanID != nil {
				t.ExternalLoanID = *extLoanID
			}
			if extGroupID != nil {
				t.ExternalGroupID = *extGroupID
			}
			out = append(out, t)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("investor: find transfers: %w", err)
	}
	return out, nil
}

func (r *PostgresTransferRepository) loadDetails(ctx context.Context, t *ExternalAssetOwnerTransfer) error {
	err := postgres.QueryRows(ctx, r.db, `SELECT principal_outstanding_derived::text,
interest_outstanding_derived::text, fee_charges_outstanding_derived::text,
penalty_charges_outstanding_derived::text, total_outstanding_derived::text,
total_overpaid_derived::text
FROM m_external_asset_owner_transfer_details WHERE asset_owner_transfer_id = $1`,
		[]any{t.ID}, func(s postgres.RowScanner) error {
			var principal, interest, fee, penalty, total, overpaid string
			if err := s.Scan(&principal, &interest, &fee, &penalty, &total, &overpaid); err != nil {
				return err
			}
			var d ExternalAssetOwnerTransferDetails
			var err error
			if d.PrincipalOutstanding, err = MinorUnitsFromDecimalText(principal, MNTMinorDigits); err != nil {
				return err
			}
			if d.InterestOutstanding, err = MinorUnitsFromDecimalText(interest, MNTMinorDigits); err != nil {
				return err
			}
			if d.FeeChargesOutstanding, err = MinorUnitsFromDecimalText(fee, MNTMinorDigits); err != nil {
				return err
			}
			if d.PenaltyChargesOutstanding, err = MinorUnitsFromDecimalText(penalty, MNTMinorDigits); err != nil {
				return err
			}
			if d.TotalOutstanding, err = MinorUnitsFromDecimalText(total, MNTMinorDigits); err != nil {
				return err
			}
			if d.TotalOverpaid, err = MinorUnitsFromDecimalText(overpaid, MNTMinorDigits); err != nil {
				return err
			}
			t.Details = d
			return nil
		})
	if err != nil {
		return fmt.Errorf("investor: load transfer details: %w", err)
	}
	return nil
}

// LoanProductAttributeRepository persists
// m_external_asset_owner_loan_product_configurable_attributes.
type LoanProductAttributeRepository interface {
	Upsert(ctx context.Context, a LoanProductAttribute) (int64, error)
	FindByProduct(ctx context.Context, loanProductID int64) ([]LoanProductAttribute, error)
}

// PostgresLoanProductAttributeRepository persists loan-product attributes.
type PostgresLoanProductAttributeRepository struct {
	db postgres.DB
}

// NewPostgresLoanProductAttributeRepository constructs the attribute store.
func NewPostgresLoanProductAttributeRepository(db postgres.DB) *PostgresLoanProductAttributeRepository {
	return &PostgresLoanProductAttributeRepository{db: db}
}

// Upsert inserts a loan-product attribute, returning its id.
func (r *PostgresLoanProductAttributeRepository) Upsert(ctx context.Context, a LoanProductAttribute) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_external_asset_owner_loan_product_configurable_attributes
(loan_product_id, attribute_key, attribute_value)
VALUES ($1,$2,$3) RETURNING id`, a.LoanProductID, a.AttributeKey, a.AttributeValue)
	if err != nil {
		return 0, fmt.Errorf("investor: upsert loan product attribute: %w", err)
	}
	return id, nil
}

// FindByProduct returns every attribute configured on one loan product.
func (r *PostgresLoanProductAttributeRepository) FindByProduct(ctx context.Context, loanProductID int64) ([]LoanProductAttribute, error) {
	var out []LoanProductAttribute
	err := postgres.QueryRows(ctx, r.db, `SELECT id, loan_product_id, attribute_key, attribute_value
FROM m_external_asset_owner_loan_product_configurable_attributes
WHERE loan_product_id = $1`, []any{loanProductID},
		func(s postgres.RowScanner) error {
			var a LoanProductAttribute
			if err := s.Scan(&a.ID, &a.LoanProductID, &a.AttributeKey, &a.AttributeValue); err != nil {
				return err
			}
			out = append(out, a)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("investor: find loan product attributes: %w", err)
	}
	return out, nil
}

func nullIfEmpty(s string) any {
	if s == "" {
		return nil
	}
	return s
}

// Compile-time proof that the pgx-backed stores satisfy their interfaces.
var (
	_ OwnerRepository                = (*PostgresOwnerRepository)(nil)
	_ TransferRepository             = (*PostgresTransferRepository)(nil)
	_ LoanProductAttributeRepository = (*PostgresLoanProductAttributeRepository)(nil)
)
