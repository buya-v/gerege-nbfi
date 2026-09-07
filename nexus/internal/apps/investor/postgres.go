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
//
// # NO DERIVED BALANCE IS WRITTEN OR READ BACK BY ANY STATEMENT IN THIS FILE
//
// m_external_asset_owner_transfer_details is Fineract's one-to-one snapshot of
// a loan's outstanding decomposition at the moment a transfer is priced. Its
// only domain columns are six NOT NULL *_derived balances Fineract folds from
// the loan summary (ExternalAssetOwnerTransferDetails.java:46-61), and the Go
// model repeats the rule those names break: total outstanding "is DERIVED from
// the four component buckets, never stored independently" (doc.go). DEC-2 §4.4
// I-3 and §7 refuse the m_trial_balance shape — a written, stored sum wearing a
// balance's name — and the repaired savings store states the rule this file
// obeys verbatim: "no INSERT here names a balance column ... no SELECT here
// reads one back into a field, because a decoded balance is a number this port
// did not derive, arriving through the SELECT instead of the INSERT and trusted
// just the same" (savings/postgres.go:33-37).
//
// Concretely:
//   - there is NO write to m_external_asset_owner_transfer_details at all (see
//     Insert). The adopted schema gives its *_derived columns no default
//     (0007_add_external_asset_owner_transfer_details.xml), so no details
//     INSERT that omits them stays valid; the write path is dropped, not
//     trimmed.
//   - there is NO SELECT in this file that reads a balance column back into a
//     field. FindByID / FindByLoanID return the transfer with Details left zero
//     (see FindByID); the read half of the old write+decode loop is gone with
//     the write half.
//
// Do not "restore" either half: a stored balance is still a written balance,
// and a decoded balance is still trusted without derivation. A caller that
// needs the outstanding decomposition derives it from the loan's own balances
// (total outstanding from the four buckets via DeriveTotalOutstanding,
// transfer.go:51).

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

// TransferRepository is the persistence surface for
// m_external_asset_owner_transfer. It has no details write path: the one-to-one
// details row is the derived-balance snapshot this port refuses to persist
// (see Insert).
type TransferRepository interface {
	Insert(ctx context.Context, t ExternalAssetOwnerTransfer) (int64, error)
	FindByID(ctx context.Context, id int64) (*ExternalAssetOwnerTransfer, error)
	FindByLoanID(ctx context.Context, loanID int64) ([]ExternalAssetOwnerTransfer, error)
}

// PostgresTransferRepository persists transfer rows. The one-to-one details row
// is deliberately not written (see Insert).
type PostgresTransferRepository struct {
	db postgres.DB
}

// NewPostgresTransferRepository constructs the transfer persistence surface.
func NewPostgresTransferRepository(db postgres.DB) *PostgresTransferRepository {
	return &PostgresTransferRepository{db: db}
}

// Insert writes the transfer row and returns its id, resolving the owner and
// previous-owner ids through the supplied aggregates.
//
// There is deliberately NO write to m_external_asset_owner_transfer_details
// here. That one-to-one table is Fineract's point-in-time snapshot of the
// loan's outstanding decomposition, folded from the loan summary when a
// transfer is priced (LoanAccountOwnerTransferServiceImpl.
// createAssetOwnerTransferDetails; the six *_derived columns, NOT NULL, at
// ExternalAssetOwnerTransferDetails.java:46-61). DEC-2 §4.4 I-3 and §7 refuse
// the m_trial_balance shape — a written, stored sum wearing a balance's name —
// and the repaired savings store states the rule this port now obeys: "no
// INSERT here names a balance column" (savings/postgres.go:33). Adopting
// Fineract's schema is not adopting its write paths.
//
// The adopted schema's create-table changelog makes every one of those columns
// NOT NULL with no default (0007_add_external_asset_owner_transfer_details.xml),
// so there is no details INSERT that omits them and remains valid: the write
// path is dropped, not trimmed to a facts-only row. The snapshot a caller
// attaches to ExternalAssetOwnerTransfer.Details is an in-memory aggregate —
// total outstanding derived from the four buckets by DeriveTotalOutstanding
// (transfer.go:51) — and is never persisted by this port.
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
	return id, nil
}

// FindByID resolves one transfer by id, or (nil, nil) on a miss.
//
// It does not rehydrate m_external_asset_owner_transfer_details into
// ExternalAssetOwnerTransfer.Details. This port never writes that table (see
// Insert), so there is no stored snapshot of its own to reload, and decoding
// the *_derived columns the oracle wrote there would reintroduce — on the read
// side — the derived balance the write path refuses: "a decoded balance is a
// number this port did not derive, arriving through the SELECT instead of the
// INSERT and trusted just the same" (savings/postgres.go:35-37). A caller that
// needs the loan's outstanding decomposition must derive it from the loan's own
// balances (DeriveTotalOutstanding folds the four buckets, transfer.go:51);
// the returned transfer carries a zero Details.
func (r *PostgresTransferRepository) FindByID(ctx context.Context, id int64) (*ExternalAssetOwnerTransfer, error) {
	transfers, err := r.find(ctx, `WHERE id = $1`, id)
	if err != nil {
		return nil, err
	}
	if len(transfers) == 0 {
		return nil, nil
	}
	t := transfers[0]
	return &t, nil
}

// FindByLoanID returns every transfer that ever touched a given loan, in id
// order. As with FindByID, Details is left zero: this port neither writes nor
// reads back the derived-balance details snapshot.
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
