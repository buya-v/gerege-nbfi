package branch

import (
	"context"
	"fmt"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL storage layer for the branch/teller slice. It
// follows the package rule used by the ledger package: no concrete pgx type is
// named here, and a postgres.DB captured at construction carries every
// statement. The import graph stays branch -> internal/platform/postgres -> pgx/v5.

// TellerRepository is the persistence surface for m_tellers.
type TellerRepository interface {
	Insert(ctx context.Context, t Teller) (int64, error)
	FindByID(ctx context.Context, id int64) (*Teller, error)
	FindByOffice(ctx context.Context, officeID int64) ([]Teller, error)
}

// PostgresTellerRepository persists m_tellers rows.
type PostgresTellerRepository struct {
	db postgres.DB
}

// NewPostgresTellerRepository constructs the teller persistence surface.
func NewPostgresTellerRepository(db postgres.DB) *PostgresTellerRepository {
	return &PostgresTellerRepository{db: db}
}

// Insert writes a teller row, returning its id.
func (r *PostgresTellerRepository) Insert(ctx context.Context, t Teller) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_tellers
			(office_id, debit_account_id, credit_account_id, name, description,
			 valid_from, valid_to, state)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id`,
		t.OfficeID, t.DebitAccountID, t.CreditAccountID, t.Name, t.Description,
		t.StartDate, t.EndDate, t.Status.StoredValue())
	if err != nil {
		return 0, fmt.Errorf("branch: insert teller: %w", err)
	}
	return id, nil
}

// FindByID resolves one teller by id, or (nil, nil) on a miss.
func (r *PostgresTellerRepository) FindByID(ctx context.Context, id int64) (*Teller, error) {
	tellers, err := r.find(ctx, `WHERE id = $1`, id)
	if err != nil {
		return nil, err
	}
	if len(tellers) == 0 {
		return nil, nil
	}
	t := tellers[0]
	return &t, nil
}

// FindByOffice returns every teller attached to an office.
func (r *PostgresTellerRepository) FindByOffice(ctx context.Context, officeID int64) ([]Teller, error) {
	return r.find(ctx, `WHERE office_id = $1 ORDER BY id`, officeID)
}

func (r *PostgresTellerRepository) find(ctx context.Context, where string, args ...any) ([]Teller, error) {
	var out []Teller
	err := postgres.QueryRows(ctx, r.db, `SELECT id, office_id, debit_account_id,
			credit_account_id, name, description, valid_from::text, valid_to::text, state
		FROM m_tellers `+where, args,
		func(s postgres.RowScanner) error {
			var t Teller
			var status int32
			if err := s.Scan(&t.ID, &t.OfficeID, &t.DebitAccountID, &t.CreditAccountID,
				&t.Name, &t.Description, &t.StartDate, &t.EndDate, &status); err != nil {
				return err
			}
			t.Status = TellerStatusFromInt(status)
			out = append(out, t)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("branch: find tellers: %w", err)
	}
	return out, nil
}

// CashierRepository is the persistence surface for m_cashiers.
type CashierRepository interface {
	Insert(ctx context.Context, c Cashier) (int64, error)
	FindByTeller(ctx context.Context, tellerID int64) ([]Cashier, error)
}

// PostgresCashierRepository persists m_cashiers rows.
type PostgresCashierRepository struct {
	db postgres.DB
}

// NewPostgresCashierRepository constructs the cashier persistence surface.
func NewPostgresCashierRepository(db postgres.DB) *PostgresCashierRepository {
	return &PostgresCashierRepository{db: db}
}

// Insert writes a cashier row, returning its id.
func (r *PostgresCashierRepository) Insert(ctx context.Context, c Cashier) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_cashiers
			(staff_id, teller_id, description, start_date, end_date, full_day, start_time, end_time)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id`,
		c.StaffID, c.TellerID, c.Description, c.StartDate, c.EndDate, c.IsFullDay,
		nullIfEmpty(c.StartTime), nullIfEmpty(c.EndTime))
	if err != nil {
		return 0, fmt.Errorf("branch: insert cashier: %w", err)
	}
	return id, nil
}

// FindByTeller returns every cashier assigned to a teller.
func (r *PostgresCashierRepository) FindByTeller(ctx context.Context, tellerID int64) ([]Cashier, error) {
	var out []Cashier
	err := postgres.QueryRows(ctx, r.db, `SELECT id, staff_id, teller_id, description,
			start_date::text, end_date::text, full_day, start_time, end_time
		FROM m_cashiers WHERE teller_id = $1 ORDER BY id`, []any{tellerID},
		func(s postgres.RowScanner) error {
			var c Cashier
			var startTime, endTime *string
			if err := s.Scan(&c.ID, &c.StaffID, &c.TellerID, &c.Description,
				&c.StartDate, &c.EndDate, &c.IsFullDay, &startTime, &endTime); err != nil {
				return err
			}
			if startTime != nil {
				c.StartTime = *startTime
			}
			if endTime != nil {
				c.EndTime = *endTime
			}
			out = append(out, c)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("branch: find cashiers: %w", err)
	}
	return out, nil
}

// CashierTransactionRepository is the persistence surface for m_cashier_transactions.
type CashierTransactionRepository interface {
	Insert(ctx context.Context, t CashierTransaction) (int64, error)
	FindByCashier(ctx context.Context, cashierID int64) ([]CashierTransaction, error)
}

// PostgresCashierTransactionRepository persists m_cashier_transactions rows.
type PostgresCashierTransactionRepository struct {
	db postgres.DB
}

// NewPostgresCashierTransactionRepository constructs the cashier-transaction store.
func NewPostgresCashierTransactionRepository(db postgres.DB) *PostgresCashierTransactionRepository {
	return &PostgresCashierTransactionRepository{db: db}
}

// Insert writes a cashier transaction, returning its id. The amount is written
// as exact decimal text from integer minor units.
func (r *PostgresCashierTransactionRepository) Insert(ctx context.Context, t CashierTransaction) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_cashier_transactions
			(cashier_id, txn_type, txn_date, txn_amount, txn_note, entity_type, entity_id, currency_code)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id`,
		t.CashierID, t.TxnType.ID, t.TxnDate, t.TxnAmount.FormatDecimal(MNTMinorDigits),
		t.TxnNote, t.EntityType, t.EntityID, t.CurrencyCode)
	if err != nil {
		return 0, fmt.Errorf("branch: insert cashier transaction: %w", err)
	}
	return id, nil
}

// FindByCashier returns every till movement a cashier performed.
func (r *PostgresCashierTransactionRepository) FindByCashier(ctx context.Context, cashierID int64) ([]CashierTransaction, error) {
	var out []CashierTransaction
	err := postgres.QueryRows(ctx, r.db, `SELECT id, cashier_id, txn_type, txn_date::text,
			txn_amount::text, txn_note, entity_type, entity_id, currency_code
		FROM m_cashier_transactions WHERE cashier_id = $1 ORDER BY id`, []any{cashierID},
		func(s postgres.RowScanner) error {
			var t CashierTransaction
			var txnTypeID int32
			var amount string
			if err := s.Scan(&t.ID, &t.CashierID, &txnTypeID, &t.TxnDate, &amount,
				&t.TxnNote, &t.EntityType, &t.EntityID, &t.CurrencyCode); err != nil {
				return err
			}
			typ, ok := CashierTxnTypeFromID(txnTypeID)
			if !ok {
				return fmt.Errorf("branch: m_cashier_transactions row %d carries unknown txn_type %d", t.ID, txnTypeID)
			}
			t.TxnType = typ
			amt, err := MinorUnitsFromDecimalText(amount, MNTMinorDigits)
			if err != nil {
				return fmt.Errorf("branch: m_cashier_transactions row %d amount %q: %w", t.ID, amount, err)
			}
			t.TxnAmount = amt
			out = append(out, t)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("branch: find cashier transactions: %w", err)
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
	_ TellerRepository             = (*PostgresTellerRepository)(nil)
	_ CashierRepository            = (*PostgresCashierRepository)(nil)
	_ CashierTransactionRepository = (*PostgresCashierTransactionRepository)(nil)
)
