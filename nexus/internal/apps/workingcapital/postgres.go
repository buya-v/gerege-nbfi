package workingcapital

import (
	"context"
	"fmt"
	"time"

	"github.com/gerege/nexus/internal/apps/loan"
	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL storage layer for the working-capital slice. It
// follows the same package rule as the ledger, investor and savings packages:
// no concrete pgx type is named here — a postgres.DB captured at construction
// carries every statement, so the import graph stays
// workingcapital -> internal/platform/postgres -> pgx/v5.

// wcMNTMinorDigits is MNT's minor unit (ISO 4217 numeric 496, 2 decimal digits),
// the precision every working-capital money column is stored at.
const wcMNTMinorDigits = 2

// money renders a loan.MinorUnits amount as an exact decimal string.
func money(m loan.MinorUnits) string { return postgres.MinorUnit(m).Format(wcMNTMinorDigits) }

// moneyFromText parses an exact decimal column into loan.MinorUnits.
func moneyFromText(text string) (loan.MinorUnits, error) {
	v, err := postgres.ParseMinorUnit(text, wcMNTMinorDigits)
	return loan.MinorUnits(v), err
}

func moneyPtr(p *string) (loan.MinorUnits, error) {
	if p == nil {
		return 0, nil
	}
	return moneyFromText(*p)
}

func datePtr(p *string) (time.Time, error) {
	if p == nil {
		return time.Time{}, nil
	}
	return time.Parse("2006-01-02", *p)
}

func int32Ptr(p *int32) int {
	if p == nil {
		return 0
	}
	return int(*p)
}

func int64Ptr(p *int64) int64 {
	if p == nil {
		return 0
	}
	return *p
}

func nullString(s string) any {
	if s == "" {
		return nil
	}
	return s
}

func nullDate(t time.Time) any {
	if t.IsZero() {
		return nil
	}
	return t
}

func nullInt64(v int64) any {
	if v == 0 {
		return nil
	}
	return v
}

func nullInt(v int) any {
	if v == 0 {
		return nil
	}
	return v
}

// wcProductDetailColumns is the single source of truth for the embedded
// WorkingCapitalLoanProductRelatedDetails columns on m_wc_loan. It serves the
// SELECT (read path) below; the INSERT spells the same seventeen columns out
// literally so the statement stays a single string literal a reader — and the
// I-3/I-4 guard — can read whole. The two must move together: a column added
// here without being added to the INSERT's column list will fail against the
// placeholder count in Insert. [T503/T525]
const wcProductDetailColumns = `currency_code, principal_amount, period_payment_rate,
repayment_every, repayment_frequency_enum, amortization_type, npv_day_count,
discount, discount_proposed, discount_approved,
delinquency_bucket_classification_id, breach_id, near_breach_id,
delinquency_grace_days, delinquency_start_type, breach_grace_days, breach_start_type`

// wcProductDetailArgs renders the embedded product-details columns as insert
// arguments, returning a full NULL row when the pointer is nil.
func wcProductDetailArgs(d *WorkingCapitalLoanProductRelatedDetails) []any {
	if d == nil {
		return []any{nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil}
	}
	return []any{
		nullString(d.CurrencyCode),
		money(d.Principal),
		money(d.PeriodPaymentRate),
		nullInt(d.RepaymentEvery),
		nullString(d.RepaymentFrequencyType.String()),
		nullString(d.AmortizationType.String()),
		nullInt(d.NpvDayCount),
		money(d.Discount),
		money(d.DiscountProposed),
		money(d.DiscountApproved),
		nullInt64(d.DelinquencyBucketID),
		nullInt64(d.BreachID),
		nullInt64(d.NearBreachID),
		nullInt(d.DelinquencyGraceDays),
		nullString(d.DelinquencyStartType.String()),
		nullInt(d.BreachGraceDays),
		nullString(d.BreachStartType.String()),
	}
}

// WorkingCapitalLoanRepository is the persistence surface for m_wc_loan.
type WorkingCapitalLoanRepository interface {
	Insert(ctx context.Context, l WorkingCapitalLoan) (int64, error)
	FindByID(ctx context.Context, id int64) (*WorkingCapitalLoan, error)
	FindByAccountNumber(ctx context.Context, accountNo string) (*WorkingCapitalLoan, error)
	UpdateStatus(ctx context.Context, id int64, status loan.LoanStatus) error
}

// PostgresWorkingCapitalLoanRepository persists m_wc_loan rows, including the
// embedded product-related-details columns.
type PostgresWorkingCapitalLoanRepository struct {
	db postgres.DB
}

// NewPostgresWorkingCapitalLoanRepository constructs the loan store.
func NewPostgresWorkingCapitalLoanRepository(db postgres.DB) *PostgresWorkingCapitalLoanRepository {
	return &PostgresWorkingCapitalLoanRepository{db: db}
}

// Insert writes an m_wc_loan row, returning its id. The balance, disbursement
// details, payment-allocation rules and transactions are not written here; use
// the dedicated child repositories afterwards.
func (r *PostgresWorkingCapitalLoanRepository) Insert(ctx context.Context, l WorkingCapitalLoan) (int64, error) {
	args := append([]any{
		nullString(l.AccountNumber),
		nullString(l.ExternalID),
		nullInt64(l.ClientID),
		nullInt64(l.FundID),
		l.LoanProductID,
		l.LoanStatus.StoredValue(),
		nullInt(l.LoanCounter),
		nullInt(l.LoanProductCounter),
		nullDate(l.SubmittedOnDate),
		nullDate(l.RejectedOnDate),
		nullDate(l.ApprovedOnDate),
		nullDate(l.ClosedOnDate),
		nullDate(l.ExpectedMaturityDate),
		nullDate(l.MaturedOnDate),
		money(l.ProposedPrincipal),
		money(l.ApprovedPrincipal),
		money(l.TotalPaymentVolume),
		l.ChargedOff,
		l.Fraud,
	}, wcProductDetailArgs(l.LoanProductRelatedDetails)...)

	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_wc_loan
(account_no, external_id, client_id, fund_id, product_id, loan_status_id,
 loan_counter, loan_product_counter,
 submittedon_date, rejectedon_date, approvedon_date, closedon_date,
 expected_maturedon_date, maturedon_date,
 principal_amount_proposed, approved_principal, total_payment_volume,
 is_charged_off, is_fraud,
 currency_code, principal_amount, period_payment_rate,
 repayment_every, repayment_frequency_enum, amortization_type, npv_day_count,
 discount, discount_proposed, discount_approved,
 delinquency_bucket_classification_id, breach_id, near_breach_id,
 delinquency_grace_days, delinquency_start_type, breach_grace_days, breach_start_type)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,
 $20,$21,$22,$23,$24,$25,$26,$27,$28,$29,$30,$31,$32,$33,$34,$35,$36)
RETURNING id`, args...)
	if err != nil {
		return 0, fmt.Errorf("workingcapital: insert loan: %w", err)
	}
	return id, nil
}

// FindByID resolves one loan (header + embedded product details) by id, or
// (nil, nil) on a miss. Balance and child collections are loaded separately.
func (r *PostgresWorkingCapitalLoanRepository) FindByID(ctx context.Context, id int64) (*WorkingCapitalLoan, error) {
	return r.findOne(ctx, `WHERE id = $1`, id)
}

// FindByAccountNumber resolves one loan by account_no, or (nil, nil) on a miss.
func (r *PostgresWorkingCapitalLoanRepository) FindByAccountNumber(ctx context.Context, accountNo string) (*WorkingCapitalLoan, error) {
	return r.findOne(ctx, `WHERE account_no = $1`, accountNo)
}

func (r *PostgresWorkingCapitalLoanRepository) findOne(ctx context.Context, where string, arg any) (*WorkingCapitalLoan, error) {
	var out *WorkingCapitalLoan
	err := postgres.QueryRows(ctx, r.db, `SELECT id, account_no, external_id,
client_id, fund_id, product_id, loan_status_id, loan_counter, loan_product_counter,
submittedon_date::text, rejectedon_date::text, approvedon_date::text,
closedon_date::text, expected_maturedon_date::text, maturedon_date::text,
principal_amount_proposed::text, approved_principal::text,
total_payment_volume::text, is_charged_off, is_fraud, `+wcProductDetailColumns+`
FROM m_wc_loan `+where, []any{arg}, func(s postgres.RowScanner) error {
		var l WorkingCapitalLoan
		var status int32
		var loanCounter, productCounter *int32
		var submitted, rejected, approved, closed, expected, matured *string
		var proposed, approvedPrincipal, paymentVolume *string
		var currencyCode, principalAmount, periodRate *string
		var repaymentEvery, npvDayCount *int32
		var repaymentFreq, amortization *string
		var discount, discountProposed, discountApproved *string
		var bucketID, breachID, nearBreachID *int64
		var delinquencyGrace, breachGrace *int32
		var delinquencyStart, breachStart *string
		if err := s.Scan(&l.ID, &l.AccountNumber, &l.ExternalID,
			&l.ClientID, &l.FundID, &l.LoanProductID, &status,
			&loanCounter, &productCounter,
			&submitted, &rejected, &approved, &closed, &expected, &matured,
			&proposed, &approvedPrincipal, &paymentVolume,
			&l.ChargedOff, &l.Fraud,
			&currencyCode, &principalAmount, &periodRate,
			&repaymentEvery, &repaymentFreq, &amortization, &npvDayCount,
			&discount, &discountProposed, &discountApproved,
			&bucketID, &breachID, &nearBreachID,
			&delinquencyGrace, &delinquencyStart, &breachGrace, &breachStart); err != nil {
			return err
		}
		st, ok := loan.LoanStatusFromStoredValue(status)
		if !ok {
			return fmt.Errorf("workingcapital: unknown loan_status_id %d", status)
		}
		l.LoanStatus = st
		l.LoanCounter = int32Ptr(loanCounter)
		l.LoanProductCounter = int32Ptr(productCounter)

		var err error
		if l.SubmittedOnDate, err = datePtr(submitted); err != nil {
			return err
		}
		if l.RejectedOnDate, err = datePtr(rejected); err != nil {
			return err
		}
		if l.ApprovedOnDate, err = datePtr(approved); err != nil {
			return err
		}
		if l.ClosedOnDate, err = datePtr(closed); err != nil {
			return err
		}
		if l.ExpectedMaturityDate, err = datePtr(expected); err != nil {
			return err
		}
		if l.MaturedOnDate, err = datePtr(matured); err != nil {
			return err
		}
		if l.ProposedPrincipal, err = moneyPtr(proposed); err != nil {
			return err
		}
		if l.ApprovedPrincipal, err = moneyPtr(approvedPrincipal); err != nil {
			return err
		}
		if l.TotalPaymentVolume, err = moneyPtr(paymentVolume); err != nil {
			return err
		}

		var d WorkingCapitalLoanProductRelatedDetails
		d.CurrencyCode = ""
		if currencyCode != nil {
			d.CurrencyCode = *currencyCode
		}
		if d.Principal, err = moneyPtr(principalAmount); err != nil {
			return err
		}
		if d.PeriodPaymentRate, err = moneyPtr(periodRate); err != nil {
			return err
		}
		d.RepaymentEvery = int32Ptr(repaymentEvery)
		d.NpvDayCount = int32Ptr(npvDayCount)
		if repaymentFreq != nil {
			f, ok := WorkingCapitalLoanPeriodFrequencyTypeFromString(*repaymentFreq)
			if !ok {
				return fmt.Errorf("workingcapital: unknown repayment_frequency_enum %q", *repaymentFreq)
			}
			d.RepaymentFrequencyType = f
		}
		if amortization != nil {
			a, ok := WorkingCapitalAmortizationTypeFromString(*amortization)
			if !ok {
				return fmt.Errorf("workingcapital: unknown amortization_type %q", *amortization)
			}
			d.AmortizationType = a
		}
		if d.Discount, err = moneyPtr(discount); err != nil {
			return err
		}
		if d.DiscountProposed, err = moneyPtr(discountProposed); err != nil {
			return err
		}
		if d.DiscountApproved, err = moneyPtr(discountApproved); err != nil {
			return err
		}
		d.DelinquencyBucketID = int64Ptr(bucketID)
		d.BreachID = int64Ptr(breachID)
		d.NearBreachID = int64Ptr(nearBreachID)
		d.DelinquencyGraceDays = int32Ptr(delinquencyGrace)
		d.BreachGraceDays = int32Ptr(breachGrace)
		if delinquencyStart != nil {
			st, ok := WorkingCapitalStartTypeFromString(*delinquencyStart)
			if !ok {
				return fmt.Errorf("workingcapital: unknown delinquency_start_type %q", *delinquencyStart)
			}
			d.DelinquencyStartType = st
		}
		if breachStart != nil {
			st, ok := WorkingCapitalStartTypeFromString(*breachStart)
			if !ok {
				return fmt.Errorf("workingcapital: unknown breach_start_type %q", *breachStart)
			}
			d.BreachStartType = st
		}
		if currencyCode != nil || repaymentFreq != nil || amortization != nil {
			l.LoanProductRelatedDetails = &d
		}
		out = &l
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("workingcapital: find loan: %w", err)
	}
	return out, nil
}

// UpdateStatus overwrites m_wc_loan.loan_status_id.
func (r *PostgresWorkingCapitalLoanRepository) UpdateStatus(ctx context.Context, id int64, status loan.LoanStatus) error {
	if _, err := r.db.Exec(ctx, `UPDATE m_wc_loan SET loan_status_id = $1 WHERE id = $2`,
		status.StoredValue(), id); err != nil {
		return fmt.Errorf("workingcapital: update loan status: %w", err)
	}
	return nil
}

// WorkingCapitalLoanBalanceRepository is the READ-ONLY persistence surface for
// m_wc_loan_balance. The Go module has no write path to this table: the row is
// Fineract's, written by its disbursement, balance-updater, charge, breach and
// amortization services during the strangler window. This port only ever reads
// it as an inbound read model and derives every outstanding/due figure from the
// raw totals it carries (see WorkingCapitalLoanBalance). [R1; T525]
type WorkingCapitalLoanBalanceRepository interface {
	FindByLoanID(ctx context.Context, loanID int64) (*WorkingCapitalLoanBalance, error)
}

// PostgresWorkingCapitalLoanBalanceRepository reads the one balance row per loan.
type PostgresWorkingCapitalLoanBalanceRepository struct {
	db postgres.DB
}

// NewPostgresWorkingCapitalLoanBalanceRepository constructs the balance read
// model.
func NewPostgresWorkingCapitalLoanBalanceRepository(db postgres.DB) *PostgresWorkingCapitalLoanBalanceRepository {
	return &PostgresWorkingCapitalLoanBalanceRepository{db: db}
}

// wcBalanceColumns is the READ path's column list for m_wc_loan_balance. The
// table has no write path in this port, so there is no INSERT/UPDATE statement
// to keep this list in step with; it names the thirteen raw charged/paid totals
// the read model decodes. [T525]
const wcBalanceColumns = `principal, principal_paid, principal_adjustment, fee,
fee_paid, penalty, penalty_paid, realized_income_from_discount_fee,
overpayment_amount, total_disbursement, total_discount_fee,
total_discount_fee_adjustment, breach_pastdue_amount`

// FindByLoanID resolves the balance for one loan, or (nil, nil) on a miss.
func (r *PostgresWorkingCapitalLoanBalanceRepository) FindByLoanID(ctx context.Context, loanID int64) (*WorkingCapitalLoanBalance, error) {
	var out *WorkingCapitalLoanBalance
	err := postgres.QueryRows(ctx, r.db, `SELECT `+wcBalanceColumns+`
FROM m_wc_loan_balance WHERE wc_loan_id = $1`, []any{loanID}, func(s postgres.RowScanner) error {
		var principal, principalPaid, principalAdjustment, fee, feePaid, penalty,
			penaltyPaid, realized, overpayment, disbursement, discountFee,
			discountAdjustment, breach string
		if err := s.Scan(&principal, &principalPaid, &principalAdjustment, &fee,
			&feePaid, &penalty, &penaltyPaid, &realized, &overpayment,
			&disbursement, &discountFee, &discountAdjustment, &breach); err != nil {
			return err
		}
		var b WorkingCapitalLoanBalance
		var err error
		if b.Principal, err = moneyFromText(principal); err != nil {
			return err
		}
		if b.PrincipalPaid, err = moneyFromText(principalPaid); err != nil {
			return err
		}
		if b.PrincipalAdjustment, err = moneyFromText(principalAdjustment); err != nil {
			return err
		}
		if b.Fee, err = moneyFromText(fee); err != nil {
			return err
		}
		if b.FeePaid, err = moneyFromText(feePaid); err != nil {
			return err
		}
		if b.Penalty, err = moneyFromText(penalty); err != nil {
			return err
		}
		if b.PenaltyPaid, err = moneyFromText(penaltyPaid); err != nil {
			return err
		}
		if b.RealizedIncomeFromDiscountFee, err = moneyFromText(realized); err != nil {
			return err
		}
		if b.OverpaymentAmount, err = moneyFromText(overpayment); err != nil {
			return err
		}
		if b.TotalDisbursement, err = moneyFromText(disbursement); err != nil {
			return err
		}
		if b.TotalDiscountFee, err = moneyFromText(discountFee); err != nil {
			return err
		}
		if b.TotalDiscountFeeAdjustment, err = moneyFromText(discountAdjustment); err != nil {
			return err
		}
		if b.BreachPastDueAmount, err = moneyFromText(breach); err != nil {
			return err
		}
		out = &b
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("workingcapital: find balance: %w", err)
	}
	return out, nil
}

// WorkingCapitalLoanDisbursementDetailsRepository is the persistence surface for
// m_wc_loan_disbursement_detail.
type WorkingCapitalLoanDisbursementDetailsRepository interface {
	Insert(ctx context.Context, d WorkingCapitalLoanDisbursementDetails) (int64, error)
	FindByLoanID(ctx context.Context, loanID int64) ([]WorkingCapitalLoanDisbursementDetails, error)
}

// PostgresWorkingCapitalLoanDisbursementDetailsRepository persists tranches.
type PostgresWorkingCapitalLoanDisbursementDetailsRepository struct {
	db postgres.DB
}

// NewPostgresWorkingCapitalLoanDisbursementDetailsRepository constructs the
// disbursement-details store.
func NewPostgresWorkingCapitalLoanDisbursementDetailsRepository(db postgres.DB) *PostgresWorkingCapitalLoanDisbursementDetailsRepository {
	return &PostgresWorkingCapitalLoanDisbursementDetailsRepository{db: db}
}

// Insert writes one disbursement-details row, returning its id.
func (r *PostgresWorkingCapitalLoanDisbursementDetailsRepository) Insert(ctx context.Context, d WorkingCapitalLoanDisbursementDetails) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_wc_loan_disbursement_detail
(wc_loan_id, expected_disburse_date, expected_amount, expected_maturity_date,
 actual_disburse_date, actual_amount, disbursedon_userid)
VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id`,
		d.LoanID,
		nullDate(d.ExpectedDisbursementDate),
		money(d.ExpectedAmount),
		nullDate(d.ExpectedMaturityDate),
		nullDate(d.ActualDisbursementDate),
		money(d.ActualAmount),
		nullInt64(d.DisbursedByUserID))
	if err != nil {
		return 0, fmt.Errorf("workingcapital: insert disbursement details: %w", err)
	}
	return id, nil
}

// FindByLoanID returns every tranche of one loan in id order.
func (r *PostgresWorkingCapitalLoanDisbursementDetailsRepository) FindByLoanID(ctx context.Context, loanID int64) ([]WorkingCapitalLoanDisbursementDetails, error) {
	var out []WorkingCapitalLoanDisbursementDetails
	err := postgres.QueryRows(ctx, r.db, `SELECT id, wc_loan_id,
expected_disburse_date::text, expected_amount::text, expected_maturity_date::text,
actual_disburse_date::text, actual_amount::text, disbursedon_userid
FROM m_wc_loan_disbursement_detail WHERE wc_loan_id = $1 ORDER BY id`, []any{loanID},
		func(s postgres.RowScanner) error {
			var d WorkingCapitalLoanDisbursementDetails
			var expectedDate, expectedMaturity, actualDate *string
			var expectedAmount, actualAmount string
			var disbursedBy *int64
			if err := s.Scan(&d.ID, &d.LoanID, &expectedDate, &expectedAmount,
				&expectedMaturity, &actualDate, &actualAmount, &disbursedBy); err != nil {
				return err
			}
			var err error
			if d.ExpectedDisbursementDate, err = datePtr(expectedDate); err != nil {
				return err
			}
			if d.ExpectedMaturityDate, err = datePtr(expectedMaturity); err != nil {
				return err
			}
			if d.ActualDisbursementDate, err = datePtr(actualDate); err != nil {
				return err
			}
			if d.ExpectedAmount, err = moneyFromText(expectedAmount); err != nil {
				return err
			}
			if d.ActualAmount, err = moneyFromText(actualAmount); err != nil {
				return err
			}
			d.DisbursedByUserID = int64Ptr(disbursedBy)
			out = append(out, d)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("workingcapital: find disbursement details: %w", err)
	}
	return out, nil
}

// WorkingCapitalLoanTransactionRepository is the persistence surface for
// m_wc_loan_transaction and its one-to-one allocation.
type WorkingCapitalLoanTransactionRepository interface {
	Insert(ctx context.Context, t WorkingCapitalLoanTransaction) (int64, error)
	FindByLoanID(ctx context.Context, loanID int64) ([]WorkingCapitalLoanTransaction, error)
}

// PostgresWorkingCapitalLoanTransactionRepository persists transactions and
// their allocations.
type PostgresWorkingCapitalLoanTransactionRepository struct {
	db postgres.DB
}

// NewPostgresWorkingCapitalLoanTransactionRepository constructs the transaction
// store.
func NewPostgresWorkingCapitalLoanTransactionRepository(db postgres.DB) *PostgresWorkingCapitalLoanTransactionRepository {
	return &PostgresWorkingCapitalLoanTransactionRepository{db: db}
}

// Insert writes the transaction row and its one allocation row.
func (r *PostgresWorkingCapitalLoanTransactionRepository) Insert(ctx context.Context, t WorkingCapitalLoanTransaction) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_wc_loan_transaction
(wc_loan_id, transaction_type_id, transaction_date, transaction_amount,
 is_reversed, reversal_external_id)
VALUES ($1,$2,$3,$4,$5,$6) RETURNING id`,
		t.LoanID,
		t.TransactionType.StoredValue(),
		t.TransactionDate,
		money(t.TransactionAmount),
		t.Reversed,
		nullString(t.ReversalExternalID))
	if err != nil {
		return 0, fmt.Errorf("workingcapital: insert transaction: %w", err)
	}

	if _, err := r.db.Exec(ctx, `INSERT INTO m_wc_loan_transaction_allocation
(wc_loan_transaction_id, principal_portion, fee_charges_portion,
 penalty_charges_portion, overpayment_portion)
VALUES ($1,$2,$3,$4,$5)`,
		id,
		money(t.Allocation.PrincipalPortion),
		money(t.Allocation.FeeChargesPortion),
		money(t.Allocation.PenaltyChargesPortion),
		money(t.Allocation.OverpaymentPortion)); err != nil {
		return 0, fmt.Errorf("workingcapital: insert transaction allocation: %w", err)
	}
	return id, nil
}

// FindByLoanID returns the transaction stream of one loan in id order, each
// with its allocation attached.
func (r *PostgresWorkingCapitalLoanTransactionRepository) FindByLoanID(ctx context.Context, loanID int64) ([]WorkingCapitalLoanTransaction, error) {
	var out []WorkingCapitalLoanTransaction
	err := postgres.QueryRows(ctx, r.db, `SELECT id, wc_loan_id, transaction_type_id,
transaction_date::text, transaction_amount::text, is_reversed, reversal_external_id
FROM m_wc_loan_transaction WHERE wc_loan_id = $1 ORDER BY id`, []any{loanID},
		func(s postgres.RowScanner) error {
			var t WorkingCapitalLoanTransaction
			var typeID int32
			var date, amount string
			var reversal *string
			if err := s.Scan(&t.ID, &t.LoanID, &typeID, &date, &amount,
				&t.Reversed, &reversal); err != nil {
				return err
			}
			tx, ok := loan.LoanTransactionTypeFromStoredValue(typeID)
			if !ok {
				return fmt.Errorf("workingcapital: unknown transaction_type_id %d", typeID)
			}
			t.TransactionType = tx
			if reversal != nil {
				t.ReversalExternalID = *reversal
			}
			var err error
			if t.TransactionDate, err = time.Parse("2006-01-02", date); err != nil {
				return err
			}
			if t.TransactionAmount, err = moneyFromText(amount); err != nil {
				return err
			}
			out = append(out, t)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("workingcapital: find transactions: %w", err)
	}
	for i := range out {
		if err := r.loadAllocation(ctx, &out[i]); err != nil {
			return nil, err
		}
	}
	return out, nil
}

func (r *PostgresWorkingCapitalLoanTransactionRepository) loadAllocation(ctx context.Context, t *WorkingCapitalLoanTransaction) error {
	err := postgres.QueryRows(ctx, r.db, `SELECT principal_portion::text,
fee_charges_portion::text, penalty_charges_portion::text, overpayment_portion::text
FROM m_wc_loan_transaction_allocation WHERE wc_loan_transaction_id = $1`,
		[]any{t.ID}, func(s postgres.RowScanner) error {
			var principal, fee, penalty, overpayment string
			if err := s.Scan(&principal, &fee, &penalty, &overpayment); err != nil {
				return err
			}
			var err error
			if t.Allocation.PrincipalPortion, err = moneyFromText(principal); err != nil {
				return err
			}
			if t.Allocation.FeeChargesPortion, err = moneyFromText(fee); err != nil {
				return err
			}
			if t.Allocation.PenaltyChargesPortion, err = moneyFromText(penalty); err != nil {
				return err
			}
			if t.Allocation.OverpaymentPortion, err = moneyFromText(overpayment); err != nil {
				return err
			}
			return nil
		})
	if err != nil {
		return fmt.Errorf("workingcapital: load transaction allocation: %w", err)
	}
	return nil
}

// WorkingCapitalLoanPaymentAllocationRuleRepository is the persistence surface
// for m_wc_loan_payment_allocation_rule.
type WorkingCapitalLoanPaymentAllocationRuleRepository interface {
	Upsert(ctx context.Context, rule WorkingCapitalLoanPaymentAllocationRule) (int64, error)
	FindByLoanID(ctx context.Context, loanID int64) ([]WorkingCapitalLoanPaymentAllocationRule, error)
}

// PostgresWorkingCapitalLoanPaymentAllocationRuleRepository persists the
// ordered allocation list per (loan, transaction type).
type PostgresWorkingCapitalLoanPaymentAllocationRuleRepository struct {
	db postgres.DB
}

// NewPostgresWorkingCapitalLoanPaymentAllocationRuleRepository constructs the
// allocation-rule store.
func NewPostgresWorkingCapitalLoanPaymentAllocationRuleRepository(db postgres.DB) *PostgresWorkingCapitalLoanPaymentAllocationRuleRepository {
	return &PostgresWorkingCapitalLoanPaymentAllocationRuleRepository{db: db}
}

// Upsert writes (or replaces) the allocation list for one rule key, returning
// its id.
func (r *PostgresWorkingCapitalLoanPaymentAllocationRuleRepository) Upsert(ctx context.Context, rule WorkingCapitalLoanPaymentAllocationRule) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_wc_loan_payment_allocation_rule
(wc_loan_id, transaction_type, allocation_types)
VALUES ($1,$2,$3)
ON CONFLICT (wc_loan_id, transaction_type) DO UPDATE SET
 allocation_types = EXCLUDED.allocation_types
RETURNING id`,
		rule.LoanID,
		rule.TransactionType,
		JoinAllocationTypes(rule.AllocationTypes))
	if err != nil {
		return 0, fmt.Errorf("workingcapital: upsert payment allocation rule: %w", err)
	}
	return id, nil
}

// FindByLoanID returns every rule of one loan in id order.
func (r *PostgresWorkingCapitalLoanPaymentAllocationRuleRepository) FindByLoanID(ctx context.Context, loanID int64) ([]WorkingCapitalLoanPaymentAllocationRule, error) {
	var out []WorkingCapitalLoanPaymentAllocationRule
	err := postgres.QueryRows(ctx, r.db, `SELECT id, wc_loan_id, transaction_type,
allocation_types
FROM m_wc_loan_payment_allocation_rule WHERE wc_loan_id = $1 ORDER BY id`,
		[]any{loanID}, func(s postgres.RowScanner) error {
			var rule WorkingCapitalLoanPaymentAllocationRule
			var allocationTypes string
			if err := s.Scan(&rule.ID, &rule.LoanID, &rule.TransactionType, &allocationTypes); err != nil {
				return err
			}
			types, err := SplitAllocationTypes(allocationTypes)
			if err != nil {
				return err
			}
			rule.AllocationTypes = types
			out = append(out, rule)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("workingcapital: find payment allocation rules: %w", err)
	}
	return out, nil
}

// Compile-time proof that the pgx-backed stores satisfy their interfaces.
var (
	_ WorkingCapitalLoanRepository                      = (*PostgresWorkingCapitalLoanRepository)(nil)
	_ WorkingCapitalLoanBalanceRepository               = (*PostgresWorkingCapitalLoanBalanceRepository)(nil)
	_ WorkingCapitalLoanDisbursementDetailsRepository   = (*PostgresWorkingCapitalLoanDisbursementDetailsRepository)(nil)
	_ WorkingCapitalLoanTransactionRepository           = (*PostgresWorkingCapitalLoanTransactionRepository)(nil)
	_ WorkingCapitalLoanPaymentAllocationRuleRepository = (*PostgresWorkingCapitalLoanPaymentAllocationRuleRepository)(nil)
)
