package shares

import (
	"context"
	"fmt"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL storage layer for the shares slice. It follows
// the package rule used by the ledger package: no concrete pgx type is named
// here, and a postgres.DB captured at construction carries every statement. The
// import graph stays shares -> internal/platform/postgres -> pgx/v5.

// ShareProductRepository is the persistence surface for m_share_product and its
// market-price and charge child tables.
type ShareProductRepository interface {
	Insert(ctx context.Context, p ShareProduct) (int64, error)
	FindByID(ctx context.Context, id int64) (*ShareProduct, error)
	InsertMarketPrice(ctx context.Context, mp ShareProductMarketPrice) (int64, error)
	InsertCharge(ctx context.Context, c ShareProductCharge) (int64, error)
}

// PostgresShareProductRepository persists share-product rows.
type PostgresShareProductRepository struct {
	db postgres.DB
}

// NewPostgresShareProductRepository constructs the share-product store.
func NewPostgresShareProductRepository(db postgres.DB) *PostgresShareProductRepository {
	return &PostgresShareProductRepository{db: db}
}

// Insert writes a share-product row, returning its id.
func (r *PostgresShareProductRepository) Insert(ctx context.Context, p ShareProduct) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_share_product
			(name, short_name, external_id, description, currency_code, digits_after_decimal,
			 in_multiples_of, minimum_shares, nominal_shares, maximum_shares,
			 allow_dividend_calculation, lock_period_enum, minimum_active_period, accounting_type)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14) RETURNING id`,
		p.Name, p.ShortName, nullIfEmpty(p.ExternalID), p.Description, p.CurrencyCode,
		p.DigitsAfterDecimal, p.InMultiplesOf, p.MinimumShares, p.NominalShares,
		p.MaximumShares, p.AllowDividendCalculation, p.LockinPeriod, p.MinimumActivePeriod,
		p.AccountingType)
	if err != nil {
		return 0, fmt.Errorf("shares: insert share product: %w", err)
	}
	return id, nil
}

// FindByID resolves one share product with its market prices and charges, or
// (nil, nil) on a miss.
func (r *PostgresShareProductRepository) FindByID(ctx context.Context, id int64) (*ShareProduct, error) {
	var p *ShareProduct
	err := postgres.QueryRows(ctx, r.db, `SELECT id, name, short_name, external_id,
			description, currency_code, digits_after_decimal, in_multiples_of,
			minimum_shares, nominal_shares, maximum_shares, allow_dividend_calculation,
			lock_period_enum, minimum_active_period, accounting_type
		FROM m_share_product WHERE id = $1`, []any{id},
		func(s postgres.RowScanner) error {
			var sp ShareProduct
			var externalID *string
			if err := s.Scan(&sp.ID, &sp.Name, &sp.ShortName, &externalID, &sp.Description,
				&sp.CurrencyCode, &sp.DigitsAfterDecimal, &sp.InMultiplesOf, &sp.MinimumShares,
				&sp.NominalShares, &sp.MaximumShares, &sp.AllowDividendCalculation,
				&sp.LockinPeriod, &sp.MinimumActivePeriod, &sp.AccountingType); err != nil {
				return err
			}
			if externalID != nil {
				sp.ExternalID = *externalID
			}
			p = &sp
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("shares: find share product: %w", err)
	}
	if p == nil {
		return nil, nil
	}
	prices, err := r.findMarketPrices(ctx, id)
	if err != nil {
		return nil, err
	}
	charges, err := r.findCharges(ctx, id)
	if err != nil {
		return nil, err
	}
	p.MarketPrices = prices
	p.Charges = charges
	return p, nil
}

// InsertMarketPrice writes one market-price band.
func (r *PostgresShareProductRepository) InsertMarketPrice(ctx context.Context, mp ShareProductMarketPrice) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_share_product_market_price
			(product_id, from_date, to_date, share_value)
		VALUES ($1,$2,$3,$4) RETURNING id`,
		mp.ProductID, mp.FromDate, mp.ToDate, mp.ShareValue.FormatDecimal(MNTMinorDigits))
	if err != nil {
		return 0, fmt.Errorf("shares: insert market price: %w", err)
	}
	return id, nil
}

// InsertCharge writes one product-charge link.
func (r *PostgresShareProductRepository) InsertCharge(ctx context.Context, c ShareProductCharge) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_share_product_charge
			(product_id, charge_id) VALUES ($1,$2) RETURNING id`, c.ProductID, c.ChargeID)
	if err != nil {
		return 0, fmt.Errorf("shares: insert share product charge: %w", err)
	}
	return id, nil
}

func (r *PostgresShareProductRepository) findMarketPrices(ctx context.Context, productID int64) ([]ShareProductMarketPrice, error) {
	var out []ShareProductMarketPrice
	err := postgres.QueryRows(ctx, r.db, `SELECT id, product_id, from_date::text, to_date::text, share_value::text
		FROM m_share_product_market_price WHERE product_id = $1 ORDER BY id`, []any{productID},
		func(s postgres.RowScanner) error {
			var mp ShareProductMarketPrice
			var value string
			if err := s.Scan(&mp.ID, &mp.ProductID, &mp.FromDate, &mp.ToDate, &value); err != nil {
				return err
			}
			v, err := MinorUnitsFromDecimalText(value, MNTMinorDigits)
			if err != nil {
				return fmt.Errorf("shares: market price %d share_value %q: %w", mp.ID, value, err)
			}
			mp.ShareValue = v
			out = append(out, mp)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("shares: find market prices: %w", err)
	}
	return out, nil
}

func (r *PostgresShareProductRepository) findCharges(ctx context.Context, productID int64) ([]ShareProductCharge, error) {
	var out []ShareProductCharge
	err := postgres.QueryRows(ctx, r.db, `SELECT id, product_id, charge_id
		FROM m_share_product_charge WHERE product_id = $1 ORDER BY id`, []any{productID},
		func(s postgres.RowScanner) error {
			var c ShareProductCharge
			if err := s.Scan(&c.ID, &c.ProductID, &c.ChargeID); err != nil {
				return err
			}
			out = append(out, c)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("shares: find share product charges: %w", err)
	}
	return out, nil
}

// ShareAccountRepository is the persistence surface for m_share_account.
type ShareAccountRepository interface {
	Insert(ctx context.Context, a ShareAccount) (int64, error)
	FindByID(ctx context.Context, id int64) (*ShareAccount, error)
}

// PostgresShareAccountRepository persists share-account rows.
type PostgresShareAccountRepository struct {
	db postgres.DB
}

// NewPostgresShareAccountRepository constructs the share-account store.
func NewPostgresShareAccountRepository(db postgres.DB) *PostgresShareAccountRepository {
	return &PostgresShareAccountRepository{db: db}
}

// Insert writes a share-account row, returning its id.
func (r *PostgresShareAccountRepository) Insert(ctx context.Context, a ShareAccount) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_share_account
			(account_no, external_id, client_id, product_id, status_enum,
			 submitted_on_date, approved_date, activated_date, closed_date,
			 total_approved_shares, total_pending_shares, total_redeemed_shares,
			 total_issued_shares, savings_account_id, currency)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15) RETURNING id`,
		a.AccountNo, nullIfEmpty(a.ExternalID), a.ClientID, a.ProductID, a.Status.StoredValue(),
		a.SubmittedDate, a.ApprovedDate, a.ActivatedDate, a.ClosedDate,
		a.TotalApprovedShares, a.TotalPendingShares, a.TotalRedeemedShares,
		a.TotalIssuedShares, a.SavingsAccountID, a.CurrencyCode)
	if err != nil {
		return 0, fmt.Errorf("shares: insert share account: %w", err)
	}
	return id, nil
}

// FindByID resolves one share account, or (nil, nil) on a miss.
func (r *PostgresShareAccountRepository) FindByID(ctx context.Context, id int64) (*ShareAccount, error) {
	var out *ShareAccount
	err := postgres.QueryRows(ctx, r.db, `SELECT id, account_no, external_id, client_id,
			product_id, status_enum, submitted_on_date::text, approved_date::text,
			activated_date::text, closed_date::text, total_approved_shares,
			total_pending_shares, total_redeemed_shares, total_issued_shares,
			savings_account_id, currency
		FROM m_share_account WHERE id = $1`, []any{id},
		func(s postgres.RowScanner) error {
			var a ShareAccount
			var status int32
			var externalID *string
			if err := s.Scan(&a.ID, &a.AccountNo, &externalID, &a.ClientID, &a.ProductID,
				&status, &a.SubmittedDate, &a.ApprovedDate, &a.ActivatedDate, &a.ClosedDate,
				&a.TotalApprovedShares, &a.TotalPendingShares, &a.TotalRedeemedShares,
				&a.TotalIssuedShares, &a.SavingsAccountID, &a.CurrencyCode); err != nil {
				return err
			}
			a.Status = ShareAccountStatusFromInt(status)
			if externalID != nil {
				a.ExternalID = *externalID
			}
			out = &a
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("shares: find share account: %w", err)
	}
	return out, nil
}

// ShareAccountTransactionRepository is the persistence surface for
// m_share_account_transactions.
type ShareAccountTransactionRepository interface {
	Insert(ctx context.Context, t ShareAccountTransaction) (int64, error)
	FindByAccount(ctx context.Context, accountID int64) ([]ShareAccountTransaction, error)
}

// PostgresShareAccountTransactionRepository persists share-account transactions.
type PostgresShareAccountTransactionRepository struct {
	db postgres.DB
}

// NewPostgresShareAccountTransactionRepository constructs the transaction store.
func NewPostgresShareAccountTransactionRepository(db postgres.DB) *PostgresShareAccountTransactionRepository {
	return &PostgresShareAccountTransactionRepository{db: db}
}

// Insert writes one share-account transaction.
func (r *PostgresShareAccountTransactionRepository) Insert(ctx context.Context, t ShareAccountTransaction) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_share_account_transactions
			(account_id, transaction_date, total_shares, transaction_type_enum,
			 amount, status_enum, charge_amount, charge_id)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id`,
		t.AccountID, t.TransactionDate, t.TotalShares, t.Type.StoredValue(),
		t.Amount.FormatDecimal(MNTMinorDigits), t.Status.StoredValue(),
		t.ChargeAmount.FormatDecimal(MNTMinorDigits), t.ChargeID)
	if err != nil {
		return 0, fmt.Errorf("shares: insert share account transaction: %w", err)
	}
	return id, nil
}

// FindByAccount returns every transaction on one account.
func (r *PostgresShareAccountTransactionRepository) FindByAccount(ctx context.Context, accountID int64) ([]ShareAccountTransaction, error) {
	var out []ShareAccountTransaction
	err := postgres.QueryRows(ctx, r.db, `SELECT id, account_id, transaction_date::text,
			total_shares, transaction_type_enum, amount::text, status_enum,
			charge_amount::text, charge_id
		FROM m_share_account_transactions WHERE account_id = $1 ORDER BY id`, []any{accountID},
		func(s postgres.RowScanner) error {
			var t ShareAccountTransaction
			var txnType, status int32
			var amount, chargeAmount string
			if err := s.Scan(&t.ID, &t.AccountID, &t.TransactionDate, &t.TotalShares,
				&txnType, &amount, &status, &chargeAmount, &t.ChargeID); err != nil {
				return err
			}
			t.Type = ShareAccountTransactionTypeFromInt(txnType)
			t.Status = PurchaseStatusFromInt(status)
			amt, err := MinorUnitsFromDecimalText(amount, MNTMinorDigits)
			if err != nil {
				return fmt.Errorf("shares: transaction %d amount %q: %w", t.ID, amount, err)
			}
			t.Amount = amt
			chg, err := MinorUnitsFromDecimalText(chargeAmount, MNTMinorDigits)
			if err != nil {
				return fmt.Errorf("shares: transaction %d charge_amount %q: %w", t.ID, chargeAmount, err)
			}
			t.ChargeAmount = chg
			out = append(out, t)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("shares: find share account transactions: %w", err)
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
	_ ShareProductRepository            = (*PostgresShareProductRepository)(nil)
	_ ShareAccountRepository            = (*PostgresShareAccountRepository)(nil)
	_ ShareAccountTransactionRepository = (*PostgresShareAccountTransactionRepository)(nil)
)
