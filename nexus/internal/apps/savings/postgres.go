package savings

import (
	"context"
	"fmt"
	"time"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL storage layer for the savings slice. It follows
// the same package rule as the ledger and investor packages: no concrete pgx
// type is named here — a postgres.DB captured at construction carries every
// statement, so the import graph stays
// savings -> internal/platform/postgres -> pgx/v5.
//
// This layer persists the account identity and the derived summary/transaction
// read models. It never turns on deposit-taking: the runtime gate (Config) is
// read and enforced by the service layer, not by these repositories.

// AccountRepository is the persistence surface for m_savings_account.
type AccountRepository interface {
	Insert(ctx context.Context, a SavingsAccount) (int64, error)
	FindByID(ctx context.Context, id int64) (*SavingsAccount, error)
	FindByExternalID(ctx context.Context, externalID string) (*SavingsAccount, error)
	UpdateStatus(ctx context.Context, id int64, status SavingsAccountStatusType) error
}

// PostgresAccountRepository persists m_savings_account rows.
type PostgresAccountRepository struct {
	db postgres.DB
}

// NewPostgresAccountRepository constructs the account store.
func NewPostgresAccountRepository(db postgres.DB) *PostgresAccountRepository {
	return &PostgresAccountRepository{db: db}
}

// Insert writes an m_savings_account row, returning its id. The derived summary
// is deliberately not written here; call SummaryRepository.Upsert afterwards.
func (r *PostgresAccountRepository) Insert(ctx context.Context, a SavingsAccount) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_savings_account
(external_id, status_enum, currency_code, currency_digits)
VALUES ($1,$2,$3,$4) RETURNING id`,
		nullStr(a.ExternalID), a.Status.StoredValue(), nullStr(a.CurrencyCode), MNTMinorDigits)
	if err != nil {
		return 0, fmt.Errorf("savings: insert account: %w", err)
	}
	return id, nil
}

// FindByID resolves one account by id, or (nil, nil) on a miss.
func (r *PostgresAccountRepository) FindByID(ctx context.Context, id int64) (*SavingsAccount, error) {
	return r.findOne(ctx, `SELECT id, external_id, status_enum, currency_code
FROM m_savings_account WHERE id = $1`, id)
}

// FindByExternalID resolves one account by external_id, or (nil, nil) on a miss.
func (r *PostgresAccountRepository) FindByExternalID(ctx context.Context, externalID string) (*SavingsAccount, error) {
	return r.findOne(ctx, `SELECT id, external_id, status_enum, currency_code
FROM m_savings_account WHERE external_id = $1`, externalID)
}

func (r *PostgresAccountRepository) findOne(ctx context.Context, query string, arg any) (*SavingsAccount, error) {
	var out *SavingsAccount
	err := postgres.QueryRows(ctx, r.db, query, []any{arg}, func(s postgres.RowScanner) error {
		var a SavingsAccount
		var status int32
		if err := s.Scan(&a.ID, &a.ExternalID, &status, &a.CurrencyCode); err != nil {
			return err
		}
		st, ok := SavingsAccountStatusTypeFromStoredValue(status)
		if !ok {
			return fmt.Errorf("savings: unknown account status_enum %d", status)
		}
		a.Status = st
		out = &a
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("savings: find account: %w", err)
	}
	return out, nil
}

// UpdateStatus overwrites m_savings_account.status_enum.
func (r *PostgresAccountRepository) UpdateStatus(ctx context.Context, id int64, status SavingsAccountStatusType) error {
	if _, err := r.db.Exec(ctx, `UPDATE m_savings_account SET status_enum = $1 WHERE id = $2`,
		status.StoredValue(), id); err != nil {
		return fmt.Errorf("savings: update account status: %w", err)
	}
	return nil
}

// SummaryRepository is the persistence surface for m_savings_account_summary.
type SummaryRepository interface {
	Upsert(ctx context.Context, accountID int64, summary SavingsAccountSummary) error
	FindByAccountID(ctx context.Context, accountID int64) (*SavingsAccountSummary, error)
}

// PostgresSummaryRepository persists the derived summary block.
type PostgresSummaryRepository struct {
	db postgres.DB
}

// NewPostgresSummaryRepository constructs the summary store.
func NewPostgresSummaryRepository(db postgres.DB) *PostgresSummaryRepository {
	return &PostgresSummaryRepository{db: db}
}

// Upsert writes the derived summary for one account, replacing it if present.
func (r *PostgresSummaryRepository) Upsert(ctx context.Context, accountID int64, summary SavingsAccountSummary) error {
	if _, err := r.db.Exec(ctx, `INSERT INTO m_savings_account_summary
(savings_account_id, total_deposits_derived, total_withdrawals_derived,
 total_interest_earned_derived, total_interest_posted_derived,
 total_withdrawal_fees_derived, total_fees_charge_derived,
 total_penalty_charge_derived, total_annual_fees_derived,
 total_fee_charges_waived_derived, total_penalty_charges_waived_derived,
 total_overdraft_interest_derived, total_withhold_tax_derived,
 account_balance_derived)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
ON CONFLICT (savings_account_id) DO UPDATE SET
 total_deposits_derived = EXCLUDED.total_deposits_derived,
 total_withdrawals_derived = EXCLUDED.total_withdrawals_derived,
 total_interest_earned_derived = EXCLUDED.total_interest_earned_derived,
 total_interest_posted_derived = EXCLUDED.total_interest_posted_derived,
 total_withdrawal_fees_derived = EXCLUDED.total_withdrawal_fees_derived,
 total_fees_charge_derived = EXCLUDED.total_fees_charge_derived,
 total_penalty_charge_derived = EXCLUDED.total_penalty_charge_derived,
 total_annual_fees_derived = EXCLUDED.total_annual_fees_derived,
 total_fee_charges_waived_derived = EXCLUDED.total_fee_charges_waived_derived,
 total_penalty_charges_waived_derived = EXCLUDED.total_penalty_charges_waived_derived,
 total_overdraft_interest_derived = EXCLUDED.total_overdraft_interest_derived,
 total_withhold_tax_derived = EXCLUDED.total_withhold_tax_derived,
 account_balance_derived = EXCLUDED.account_balance_derived`,
		accountID,
		summary.TotalDeposits.FormatDecimal(MNTMinorDigits),
		summary.TotalWithdrawals.FormatDecimal(MNTMinorDigits),
		summary.TotalInterestEarned.FormatDecimal(MNTMinorDigits),
		summary.TotalInterestPosted.FormatDecimal(MNTMinorDigits),
		summary.TotalWithdrawalFees.FormatDecimal(MNTMinorDigits),
		summary.TotalFeeCharge.FormatDecimal(MNTMinorDigits),
		summary.TotalPenaltyCharge.FormatDecimal(MNTMinorDigits),
		summary.TotalAnnualFees.FormatDecimal(MNTMinorDigits),
		summary.TotalFeeChargesWaived.FormatDecimal(MNTMinorDigits),
		summary.TotalPenaltyChargesWaived.FormatDecimal(MNTMinorDigits),
		summary.TotalOverdraftInterestDerived.FormatDecimal(MNTMinorDigits),
		summary.TotalWithholdTax.FormatDecimal(MNTMinorDigits),
		summary.AccountBalance.FormatDecimal(MNTMinorDigits)); err != nil {
		return fmt.Errorf("savings: upsert summary: %w", err)
	}
	return nil
}

// FindByAccountID resolves the derived summary for one account, or (nil, nil).
func (r *PostgresSummaryRepository) FindByAccountID(ctx context.Context, accountID int64) (*SavingsAccountSummary, error) {
	var out *SavingsAccountSummary
	err := postgres.QueryRows(ctx, r.db, `SELECT total_deposits_derived::text,
total_withdrawals_derived::text, total_interest_earned_derived::text,
total_interest_posted_derived::text, total_withdrawal_fees_derived::text,
total_fees_charge_derived::text, total_penalty_charge_derived::text,
total_annual_fees_derived::text, total_fee_charges_waived_derived::text,
total_penalty_charges_waived_derived::text, total_overdraft_interest_derived::text,
total_withhold_tax_derived::text, account_balance_derived::text
FROM m_savings_account_summary WHERE savings_account_id = $1`, []any{accountID},
		func(s postgres.RowScanner) error {
			var deposits, withdrawals, interestEarned, interestPosted, withdrawalFees,
				feeCharge, penaltyCharge, annualFees, feeWaived, penaltyWaived,
				overdraftInterest, withholdTax, balance string
			if err := s.Scan(&deposits, &withdrawals, &interestEarned, &interestPosted,
				&withdrawalFees, &feeCharge, &penaltyCharge, &annualFees, &feeWaived,
				&penaltyWaived, &overdraftInterest, &withholdTax, &balance); err != nil {
				return err
			}
			summary, err := decodeSummary(deposits, withdrawals, interestEarned,
				interestPosted, withdrawalFees, feeCharge, penaltyCharge, annualFees,
				feeWaived, penaltyWaived, overdraftInterest, withholdTax, balance)
			if err != nil {
				return err
			}
			out = &summary
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("savings: find summary: %w", err)
	}
	return out, nil
}

// TransactionRepository is the persistence surface for
// m_savings_account_transaction.
type TransactionRepository interface {
	Insert(ctx context.Context, t SavingsAccountTransaction) (int64, error)
	FindByAccountID(ctx context.Context, accountID int64) ([]SavingsAccountTransaction, error)
}

// PostgresTransactionRepository persists savings-account transactions.
type PostgresTransactionRepository struct {
	db postgres.DB
}

// NewPostgresTransactionRepository constructs the transaction store.
func NewPostgresTransactionRepository(db postgres.DB) *PostgresTransactionRepository {
	return &PostgresTransactionRepository{db: db}
}

// Insert writes one transaction, returning its id. The entry classification is
// derived from the transaction type (it is not a stored column in the oracle).
func (r *PostgresTransactionRepository) Insert(ctx context.Context, t SavingsAccountTransaction) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_savings_account_transaction
(savings_account_id, transaction_type_enum, amount, running_balance_derived)
VALUES ($1,$2,$3,$4) RETURNING id`,
		t.AccountID, t.Type.StoredValue(),
		t.Amount.FormatDecimal(MNTMinorDigits),
		t.RunningBalance.FormatDecimal(MNTMinorDigits))
	if err != nil {
		return 0, fmt.Errorf("savings: insert transaction: %w", err)
	}
	return id, nil
}

// FindByAccountID returns the transaction stream of one account in id order.
func (r *PostgresTransactionRepository) FindByAccountID(ctx context.Context, accountID int64) ([]SavingsAccountTransaction, error) {
	var out []SavingsAccountTransaction
	err := postgres.QueryRows(ctx, r.db, `SELECT id, savings_account_id,
transaction_type_enum, amount::text, running_balance_derived::text
FROM m_savings_account_transaction WHERE savings_account_id = $1 ORDER BY id`,
		[]any{accountID}, func(s postgres.RowScanner) error {
			var t SavingsAccountTransaction
			var typeEnum int32
			var amount, balance string
			if err := s.Scan(&t.ID, &t.AccountID, &typeEnum, &amount, &balance); err != nil {
				return err
			}
			tx, ok := SavingsAccountTransactionTypeFromStoredValue(typeEnum)
			if !ok {
				return fmt.Errorf("savings: unknown transaction_type_enum %d", typeEnum)
			}
			var err error
			if t.Amount, err = MinorUnitsFromDecimalText(amount, MNTMinorDigits); err != nil {
				return err
			}
			if t.RunningBalance, err = MinorUnitsFromDecimalText(balance, MNTMinorDigits); err != nil {
				return err
			}
			t.Type = tx
			t.Entry = tx.EntryType()
			out = append(out, t)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("savings: find transactions: %w", err)
	}
	return out, nil
}

func decodeSummary(fields ...string) (SavingsAccountSummary, error) {
	var s SavingsAccountSummary
	if len(fields) != 13 {
		return s, fmt.Errorf("savings: decode summary: expected 13 fields, got %d", len(fields))
	}
	dec := func(text string) (MinorUnits, error) {
		return MinorUnitsFromDecimalText(text, MNTMinorDigits)
	}
	var err error
	if s.TotalDeposits, err = dec(fields[0]); err != nil {
		return s, err
	}
	if s.TotalWithdrawals, err = dec(fields[1]); err != nil {
		return s, err
	}
	if s.TotalInterestEarned, err = dec(fields[2]); err != nil {
		return s, err
	}
	if s.TotalInterestPosted, err = dec(fields[3]); err != nil {
		return s, err
	}
	if s.TotalWithdrawalFees, err = dec(fields[4]); err != nil {
		return s, err
	}
	if s.TotalFeeCharge, err = dec(fields[5]); err != nil {
		return s, err
	}
	if s.TotalPenaltyCharge, err = dec(fields[6]); err != nil {
		return s, err
	}
	if s.TotalAnnualFees, err = dec(fields[7]); err != nil {
		return s, err
	}
	if s.TotalFeeChargesWaived, err = dec(fields[8]); err != nil {
		return s, err
	}
	if s.TotalPenaltyChargesWaived, err = dec(fields[9]); err != nil {
		return s, err
	}
	if s.TotalOverdraftInterestDerived, err = dec(fields[10]); err != nil {
		return s, err
	}
	if s.TotalWithholdTax, err = dec(fields[11]); err != nil {
		return s, err
	}
	if s.AccountBalance, err = dec(fields[12]); err != nil {
		return s, err
	}
	return s, nil
}

func nullStr(s string) any {
	if s == "" {
		return nil
	}
	return s
}

func nullTime(t time.Time) any {
	if t.IsZero() {
		return nil
	}
	return t
}

// Compile-time proof that the pgx-backed stores satisfy their interfaces.
var (
	_ AccountRepository     = (*PostgresAccountRepository)(nil)
	_ SummaryRepository     = (*PostgresSummaryRepository)(nil)
	_ TransactionRepository = (*PostgresTransactionRepository)(nil)
)
