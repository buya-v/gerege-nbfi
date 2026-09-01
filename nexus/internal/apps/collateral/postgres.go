package collateral

import (
	"context"
	"fmt"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL storage layer for the collateral slice. It
// follows the package rule used by the ledger and investor packages: no
// concrete pgx type is named here, and a postgres.DB (Querier + Executor)
// captured at construction carries every statement. The import graph stays
// collateral -> internal/platform/postgres -> pgx/v5.

// CollateralProductRepository is the persistence surface for m_collateral_management.
type CollateralProductRepository interface {
	Upsert(ctx context.Context, p CollateralProduct) (int64, error)
	FindByID(ctx context.Context, id int64) (*CollateralProduct, error)
}

// PostgresCollateralProductRepository persists m_collateral_management rows.
type PostgresCollateralProductRepository struct {
	db postgres.DB
}

// NewPostgresCollateralProductRepository constructs the product store.
func NewPostgresCollateralProductRepository(db postgres.DB) *PostgresCollateralProductRepository {
	return &PostgresCollateralProductRepository{db: db}
}

// Upsert inserts a product, returning its id. When the supplied product already
// has an id it is returned unchanged, mirroring the aggregate id sentinel.
func (r *PostgresCollateralProductRepository) Upsert(ctx context.Context, p CollateralProduct) (int64, error) {
	if p.ID != 0 {
		return p.ID, nil
	}
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_collateral_management
(name, quality, base_price, unit_type, pct_to_base, currency)
VALUES ($1,$2,$3,$4,$5,$6) RETURNING id`,
		nullIfEmpty(p.Name), nullIfEmpty(p.Quality),
		p.BasePrice.FormatDecimal(DecimalScale), nullIfEmpty(p.UnitType),
		p.PctToBase.FormatDecimal(DecimalScale), nullIfEmpty(p.CurrencyCode))
	if err != nil {
		return 0, fmt.Errorf("collateral: upsert collateral product: %w", err)
	}
	return id, nil
}

// FindByID resolves one product by id, or (nil, nil) on a miss.
func (r *PostgresCollateralProductRepository) FindByID(ctx context.Context, id int64) (*CollateralProduct, error) {
	var out *CollateralProduct
	err := postgres.QueryRows(ctx, r.db, `SELECT id, name, quality, base_price::text,
unit_type, pct_to_base::text, currency
FROM m_collateral_management WHERE id = $1`, []any{id},
		func(s postgres.RowScanner) error {
			var p CollateralProduct
			var basePrice, pctToBase string
			var currency *string
			if err := s.Scan(&p.ID, &p.Name, &p.Quality, &basePrice, &p.UnitType, &pctToBase, &currency); err != nil {
				return err
			}
			var err error
			if p.BasePrice, err = ScaledIntFromText(basePrice, DecimalScale); err != nil {
				return err
			}
			if p.PctToBase, err = ScaledIntFromText(pctToBase, DecimalScale); err != nil {
				return err
			}
			if currency != nil {
				p.CurrencyCode = *currency
			}
			out = &p
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("collateral: find collateral product: %w", err)
	}
	return out, nil
}

// ClientCollateralRepository is the persistence surface for
// m_client_collateral_management.
type ClientCollateralRepository interface {
	Insert(ctx context.Context, c ClientCollateral) (int64, error)
	FindByID(ctx context.Context, id int64) (*ClientCollateral, error)
	FindByClientID(ctx context.Context, clientID int64) ([]ClientCollateral, error)
	UpdateQuantity(ctx context.Context, id int64, quantity ScaledInt) error
}

// PostgresClientCollateralRepository persists client collateral holdings.
type PostgresClientCollateralRepository struct {
	db postgres.DB
}

// NewPostgresClientCollateralRepository constructs the client-collateral store.
func NewPostgresClientCollateralRepository(db postgres.DB) *PostgresClientCollateralRepository {
	return &PostgresClientCollateralRepository{db: db}
}

// Insert writes a holding row, resolving the product id from the aggregate.
func (r *PostgresClientCollateralRepository) Insert(ctx context.Context, c ClientCollateral) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_client_collateral_management
(quantity, client_id, collateral_id) VALUES ($1,$2,$3) RETURNING id`,
		c.Quantity.FormatDecimal(DecimalScale), c.ClientID, c.Product.ID)
	if err != nil {
		return 0, fmt.Errorf("collateral: insert client collateral: %w", err)
	}
	return id, nil
}

// FindByID resolves one holding by id, or (nil, nil) on a miss.
func (r *PostgresClientCollateralRepository) FindByID(ctx context.Context, id int64) (*ClientCollateral, error) {
	var out *ClientCollateral
	err := postgres.QueryRows(ctx, r.db, `SELECT id, quantity::text, client_id, collateral_id
FROM m_client_collateral_management WHERE id = $1`, []any{id},
		func(s postgres.RowScanner) error {
			var c ClientCollateral
			var quantity string
			if err := s.Scan(&c.ID, &quantity, &c.ClientID, &c.Product.ID); err != nil {
				return err
			}
			var err error
			if c.Quantity, err = ScaledIntFromText(quantity, DecimalScale); err != nil {
				return err
			}
			out = &c
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("collateral: find client collateral: %w", err)
	}
	return out, nil
}

// FindByClientID returns every holding for one client, in id order.
func (r *PostgresClientCollateralRepository) FindByClientID(ctx context.Context, clientID int64) ([]ClientCollateral, error) {
	var out []ClientCollateral
	err := postgres.QueryRows(ctx, r.db, `SELECT id, quantity::text, client_id, collateral_id
FROM m_client_collateral_management WHERE client_id = $1 ORDER BY id`, []any{clientID},
		func(s postgres.RowScanner) error {
			var c ClientCollateral
			var quantity string
			if err := s.Scan(&c.ID, &quantity, &c.ClientID, &c.Product.ID); err != nil {
				return err
			}
			var err error
			if c.Quantity, err = ScaledIntFromText(quantity, DecimalScale); err != nil {
				return err
			}
			out = append(out, c)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("collateral: find client collaterals: %w", err)
	}
	return out, nil
}

// UpdateQuantity overwrites a holding's quantity.
func (r *PostgresClientCollateralRepository) UpdateQuantity(ctx context.Context, id int64, quantity ScaledInt) error {
	if _, err := r.db.Exec(ctx, `UPDATE m_client_collateral_management SET quantity = $1 WHERE id = $2`,
		quantity.FormatDecimal(DecimalScale), id); err != nil {
		return fmt.Errorf("collateral: update client collateral quantity: %w", err)
	}
	return nil
}

// LoanCollateralLinkRepository is the persistence surface for
// m_loan_collateral_management.
type LoanCollateralLinkRepository interface {
	Insert(ctx context.Context, l LoanCollateralLink) (int64, error)
	FindByID(ctx context.Context, id int64) (*LoanCollateralLink, error)
	FindByLoanID(ctx context.Context, loanID int64) ([]LoanCollateralLink, error)
	MarkReleased(ctx context.Context, id int64) error
}

// PostgresLoanCollateralLinkRepository persists loan-collateral links.
type PostgresLoanCollateralLinkRepository struct {
	db postgres.DB
}

// NewPostgresLoanCollateralLinkRepository constructs the link store.
func NewPostgresLoanCollateralLinkRepository(db postgres.DB) *PostgresLoanCollateralLinkRepository {
	return &PostgresLoanCollateralLinkRepository{db: db}
}

// Insert writes a link row, treating transaction_id 0 as NULL.
func (r *PostgresLoanCollateralLinkRepository) Insert(ctx context.Context, l LoanCollateralLink) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_loan_collateral_management
(quantity, transaction_id, loan_id, is_released, client_collateral_id)
VALUES ($1,$2,$3,$4,$5) RETURNING id`,
		l.Quantity.FormatDecimal(DecimalScale), nullIfZero(l.TransactionID), l.LoanID, l.IsReleased, l.ClientCollateralID)
	if err != nil {
		return 0, fmt.Errorf("collateral: insert loan collateral link: %w", err)
	}
	return id, nil
}

// FindByID resolves one link by id, or (nil, nil) on a miss.
func (r *PostgresLoanCollateralLinkRepository) FindByID(ctx context.Context, id int64) (*LoanCollateralLink, error) {
	var out *LoanCollateralLink
	err := postgres.QueryRows(ctx, r.db, `SELECT id, loan_id, transaction_id,
is_released, client_collateral_id, quantity::text
FROM m_loan_collateral_management WHERE id = $1`, []any{id},
		func(s postgres.RowScanner) error {
			var l LoanCollateralLink
			var txnID *int64
			var quantity string
			if err := s.Scan(&l.ID, &l.LoanID, &txnID, &l.IsReleased, &l.ClientCollateralID, &quantity); err != nil {
				return err
			}
			if txnID != nil {
				l.TransactionID = *txnID
			}
			var err error
			if l.Quantity, err = ScaledIntFromText(quantity, DecimalScale); err != nil {
				return err
			}
			out = &l
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("collateral: find loan collateral link: %w", err)
	}
	return out, nil
}

// FindByLoanID returns every link tied to one loan, in id order.
func (r *PostgresLoanCollateralLinkRepository) FindByLoanID(ctx context.Context, loanID int64) ([]LoanCollateralLink, error) {
	var out []LoanCollateralLink
	err := postgres.QueryRows(ctx, r.db, `SELECT id, loan_id, transaction_id,
is_released, client_collateral_id, quantity::text
FROM m_loan_collateral_management WHERE loan_id = $1 ORDER BY id`, []any{loanID},
		func(s postgres.RowScanner) error {
			var l LoanCollateralLink
			var txnID *int64
			var quantity string
			if err := s.Scan(&l.ID, &l.LoanID, &txnID, &l.IsReleased, &l.ClientCollateralID, &quantity); err != nil {
				return err
			}
			if txnID != nil {
				l.TransactionID = *txnID
			}
			var err error
			if l.Quantity, err = ScaledIntFromText(quantity, DecimalScale); err != nil {
				return err
			}
			out = append(out, l)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("collateral: find loan collateral links: %w", err)
	}
	return out, nil
}

// MarkReleased sets a link's is_released flag.
func (r *PostgresLoanCollateralLinkRepository) MarkReleased(ctx context.Context, id int64) error {
	if _, err := r.db.Exec(ctx, `UPDATE m_loan_collateral_management SET is_released = true WHERE id = $1`, id); err != nil {
		return fmt.Errorf("collateral: mark loan collateral link released: %w", err)
	}
	return nil
}

// LoanCollateralRepository is the persistence surface for m_loan_collateral.
type LoanCollateralRepository interface {
	Insert(ctx context.Context, c LoanCollateral) (int64, error)
	FindByID(ctx context.Context, id int64) (*LoanCollateral, error)
	FindByLoanID(ctx context.Context, loanID int64) ([]LoanCollateral, error)
	Update(ctx context.Context, c LoanCollateral) error
}

// PostgresLoanCollateralRepository persists classic loan collateral rows.
type PostgresLoanCollateralRepository struct {
	db postgres.DB
}

// NewPostgresLoanCollateralRepository constructs the loan-collateral store.
func NewPostgresLoanCollateralRepository(db postgres.DB) *PostgresLoanCollateralRepository {
	return &PostgresLoanCollateralRepository{db: db}
}

// Insert writes a loan-collateral row, returning its id.
func (r *PostgresLoanCollateralRepository) Insert(ctx context.Context, c LoanCollateral) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_loan_collateral
(loan_id, type_cv_id, value, description) VALUES ($1,$2,$3,$4) RETURNING id`,
		c.LoanID, c.TypeID, c.Value.FormatDecimal(CollateralValueScale), nullIfEmpty(c.Description))
	if err != nil {
		return 0, fmt.Errorf("collateral: insert loan collateral: %w", err)
	}
	return id, nil
}

// FindByID resolves one loan-collateral by id, or (nil, nil) on a miss.
func (r *PostgresLoanCollateralRepository) FindByID(ctx context.Context, id int64) (*LoanCollateral, error) {
	var out *LoanCollateral
	err := postgres.QueryRows(ctx, r.db, `SELECT id, loan_id, type_cv_id, value::text, description
FROM m_loan_collateral WHERE id = $1`, []any{id},
		func(s postgres.RowScanner) error {
			var c LoanCollateral
			var value, description string
			if err := s.Scan(&c.ID, &c.LoanID, &c.TypeID, &value, &description); err != nil {
				return err
			}
			var err error
			if c.Value, err = ScaledIntFromText(value, CollateralValueScale); err != nil {
				return err
			}
			c.Description = description
			out = &c
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("collateral: find loan collateral: %w", err)
	}
	return out, nil
}

// FindByLoanID returns every loan-collateral tied to one loan, in id order.
func (r *PostgresLoanCollateralRepository) FindByLoanID(ctx context.Context, loanID int64) ([]LoanCollateral, error) {
	var out []LoanCollateral
	err := postgres.QueryRows(ctx, r.db, `SELECT id, loan_id, type_cv_id, value::text, description
FROM m_loan_collateral WHERE loan_id = $1 ORDER BY id`, []any{loanID},
		func(s postgres.RowScanner) error {
			var c LoanCollateral
			var value, description string
			if err := s.Scan(&c.ID, &c.LoanID, &c.TypeID, &value, &description); err != nil {
				return err
			}
			var err error
			if c.Value, err = ScaledIntFromText(value, CollateralValueScale); err != nil {
				return err
			}
			c.Description = description
			out = append(out, c)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("collateral: find loan collaterals: %w", err)
	}
	return out, nil
}

// Update overwrites type, value and description on an existing row.
func (r *PostgresLoanCollateralRepository) Update(ctx context.Context, c LoanCollateral) error {
	if _, err := r.db.Exec(ctx, `UPDATE m_loan_collateral
SET type_cv_id = $1, value = $2, description = $3 WHERE id = $4`,
		c.TypeID, c.Value.FormatDecimal(CollateralValueScale), nullIfEmpty(c.Description), c.ID); err != nil {
		return fmt.Errorf("collateral: update loan collateral: %w", err)
	}
	return nil
}

func nullIfZero(v int64) any {
	if v == 0 {
		return nil
	}
	return v
}

func nullIfEmpty(s string) any {
	if s == "" {
		return nil
	}
	return s
}

// Compile-time proof that the pgx-backed stores satisfy their interfaces.
var (
	_ CollateralProductRepository  = (*PostgresCollateralProductRepository)(nil)
	_ ClientCollateralRepository   = (*PostgresClientCollateralRepository)(nil)
	_ LoanCollateralLinkRepository = (*PostgresLoanCollateralLinkRepository)(nil)
	_ LoanCollateralRepository     = (*PostgresLoanCollateralRepository)(nil)
)
