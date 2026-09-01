package origination

import (
	"context"
	"fmt"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL storage layer for the loan-origination slice. It
// follows the same package rule as the other Tier B contexts: no concrete pgx
// type is named here — a postgres.DB captured at construction carries every
// statement, so the import graph stays
// origination -> internal/platform/postgres -> pgx/v5.
//
// The linking rule set (active-originator, submitted-status, duplicate and
// delete guards) lives in reconcile.go and is enforced by the service layer;
// these repositories are the CRUD surface that layer composes.

func nullString(s string) any {
	if s == "" {
		return nil
	}
	return s
}

func nullInt64(v int64) any {
	if v == 0 {
		return nil
	}
	return v
}

// LoanOriginatorRepository is the persistence surface for m_loan_originator.
type LoanOriginatorRepository interface {
	Insert(ctx context.Context, o LoanOriginator) (int64, error)
	FindByID(ctx context.Context, id int64) (*LoanOriginator, error)
	FindByExternalID(ctx context.Context, externalID string) (*LoanOriginator, error)
	Update(ctx context.Context, o LoanOriginator) error
	Delete(ctx context.Context, id int64) error
}

// PostgresLoanOriginatorRepository persists m_loan_originator rows. The audit
// columns (created_on_utc, created_by, last_modified_on_utc, last_modified_by)
// are infrastructure-owned and deliberately not written here.
type PostgresLoanOriginatorRepository struct {
	db postgres.DB
}

// NewPostgresLoanOriginatorRepository constructs the originator store.
func NewPostgresLoanOriginatorRepository(db postgres.DB) *PostgresLoanOriginatorRepository {
	return &PostgresLoanOriginatorRepository{db: db}
}

// Insert writes an m_loan_originator row, returning its id.
func (r *PostgresLoanOriginatorRepository) Insert(ctx context.Context, o LoanOriginator) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_loan_originator
(external_id, name, status, originator_type_cv_id, channel_type_cv_id)
VALUES ($1,$2,$3,$4,$5) RETURNING id`,
		o.ExternalID, nullString(o.Name), o.Status.StoredValue(),
		nullInt64(o.OriginatorTypeID), nullInt64(o.ChannelTypeID))
	if err != nil {
		return 0, fmt.Errorf("origination: insert originator: %w", err)
	}
	return id, nil
}

// FindByID resolves one originator by id, or (nil, nil) on a miss.
func (r *PostgresLoanOriginatorRepository) FindByID(ctx context.Context, id int64) (*LoanOriginator, error) {
	return r.findOne(ctx, `SELECT id, external_id, name, status,
originator_type_cv_id, channel_type_cv_id FROM m_loan_originator WHERE id = $1`, id)
}

// FindByExternalID resolves one originator by external_id, or (nil, nil) on a miss.
func (r *PostgresLoanOriginatorRepository) FindByExternalID(ctx context.Context, externalID string) (*LoanOriginator, error) {
	return r.findOne(ctx, `SELECT id, external_id, name, status,
originator_type_cv_id, channel_type_cv_id FROM m_loan_originator WHERE external_id = $1`, externalID)
}

func (r *PostgresLoanOriginatorRepository) findOne(ctx context.Context, query string, arg any) (*LoanOriginator, error) {
	var out *LoanOriginator
	err := postgres.QueryRows(ctx, r.db, query, []any{arg}, func(s postgres.RowScanner) error {
		var o LoanOriginator
		var status string
		var originatorType, channelType *int64
		if err := s.Scan(&o.ID, &o.ExternalID, &o.Name, &status, &originatorType, &channelType); err != nil {
			return err
		}
		st, ok := LoanOriginatorStatusFromString(status)
		if !ok {
			return fmt.Errorf("origination: unknown originator status %q", status)
		}
		o.Status = st
		o.OriginatorTypeID = int64Value(originatorType)
		o.ChannelTypeID = int64Value(channelType)
		out = &o
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("origination: find originator: %w", err)
	}
	return out, nil
}

// Update replaces name, status, originatorType and channelType for one
// originator, mirroring LoanOriginator.update.
func (r *PostgresLoanOriginatorRepository) Update(ctx context.Context, o LoanOriginator) error {
	if _, err := r.db.Exec(ctx, `UPDATE m_loan_originator SET name = $1, status = $2,
originator_type_cv_id = $3, channel_type_cv_id = $4 WHERE id = $5`,
		nullString(o.Name), o.Status.StoredValue(),
		nullInt64(o.OriginatorTypeID), nullInt64(o.ChannelTypeID), o.ID); err != nil {
		return fmt.Errorf("origination: update originator: %w", err)
	}
	return nil
}

// Delete removes one originator row.
func (r *PostgresLoanOriginatorRepository) Delete(ctx context.Context, id int64) error {
	if _, err := r.db.Exec(ctx, `DELETE FROM m_loan_originator WHERE id = $1`, id); err != nil {
		return fmt.Errorf("origination: delete originator: %w", err)
	}
	return nil
}

// LoanOriginatorMappingRepository is the persistence surface for
// m_loan_originator_mapping.
type LoanOriginatorMappingRepository interface {
	Insert(ctx context.Context, m LoanOriginatorMapping) (int64, error)
	FindByLoanID(ctx context.Context, loanID int64) ([]LoanOriginatorMapping, error)
	FindByOriginatorID(ctx context.Context, originatorID int64) ([]LoanOriginatorMapping, error)
	Delete(ctx context.Context, loanID, originatorID int64) error
}

// PostgresLoanOriginatorMappingRepository persists amortising-loan mappings.
type PostgresLoanOriginatorMappingRepository struct {
	db postgres.DB
}

// NewPostgresLoanOriginatorMappingRepository constructs the mapping store.
func NewPostgresLoanOriginatorMappingRepository(db postgres.DB) *PostgresLoanOriginatorMappingRepository {
	return &PostgresLoanOriginatorMappingRepository{db: db}
}

// Insert writes one mapping row, returning its id.
func (r *PostgresLoanOriginatorMappingRepository) Insert(ctx context.Context, m LoanOriginatorMapping) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_loan_originator_mapping
(loan_id, originator_id) VALUES ($1,$2) RETURNING id`, m.LoanID, m.OriginatorID)
	if err != nil {
		return 0, fmt.Errorf("origination: insert loan originator mapping: %w", err)
	}
	return id, nil
}

// FindByLoanID returns every mapping of one loan in id order.
func (r *PostgresLoanOriginatorMappingRepository) FindByLoanID(ctx context.Context, loanID int64) ([]LoanOriginatorMapping, error) {
	return r.find(ctx, `WHERE loan_id = $1`, loanID)
}

// FindByOriginatorID returns every mapping referencing one originator.
func (r *PostgresLoanOriginatorMappingRepository) FindByOriginatorID(ctx context.Context, originatorID int64) ([]LoanOriginatorMapping, error) {
	return r.find(ctx, `WHERE originator_id = $1`, originatorID)
}

func (r *PostgresLoanOriginatorMappingRepository) find(ctx context.Context, where string, arg int64) ([]LoanOriginatorMapping, error) {
	var out []LoanOriginatorMapping
	err := postgres.QueryRows(ctx, r.db, `SELECT id, loan_id, originator_id
FROM m_loan_originator_mapping `+where+` ORDER BY id`, []any{arg}, func(s postgres.RowScanner) error {
		var m LoanOriginatorMapping
		if err := s.Scan(&m.ID, &m.LoanID, &m.OriginatorID); err != nil {
			return err
		}
		out = append(out, m)
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("origination: find loan originator mappings: %w", err)
	}
	return out, nil
}

// Delete removes the mapping for one (loan, originator) pair.
func (r *PostgresLoanOriginatorMappingRepository) Delete(ctx context.Context, loanID, originatorID int64) error {
	if _, err := r.db.Exec(ctx, `DELETE FROM m_loan_originator_mapping
WHERE loan_id = $1 AND originator_id = $2`, loanID, originatorID); err != nil {
		return fmt.Errorf("origination: delete loan originator mapping: %w", err)
	}
	return nil
}

// WorkingCapitalLoanOriginatorMappingRepository is the persistence surface for
// m_wc_loan_originator_mapping.
type WorkingCapitalLoanOriginatorMappingRepository interface {
	Insert(ctx context.Context, m WorkingCapitalLoanOriginatorMapping) (int64, error)
	FindByLoanID(ctx context.Context, loanID int64) ([]WorkingCapitalLoanOriginatorMapping, error)
	FindByOriginatorID(ctx context.Context, originatorID int64) ([]WorkingCapitalLoanOriginatorMapping, error)
	Delete(ctx context.Context, loanID, originatorID int64) error
}

// PostgresWorkingCapitalLoanOriginatorMappingRepository persists working-capital
// mappings.
type PostgresWorkingCapitalLoanOriginatorMappingRepository struct {
	db postgres.DB
}

// NewPostgresWorkingCapitalLoanOriginatorMappingRepository constructs the
// working-capital mapping store.
func NewPostgresWorkingCapitalLoanOriginatorMappingRepository(db postgres.DB) *PostgresWorkingCapitalLoanOriginatorMappingRepository {
	return &PostgresWorkingCapitalLoanOriginatorMappingRepository{db: db}
}

// Insert writes one mapping row, returning its id.
func (r *PostgresWorkingCapitalLoanOriginatorMappingRepository) Insert(ctx context.Context, m WorkingCapitalLoanOriginatorMapping) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_wc_loan_originator_mapping
(loan_id, originator_id) VALUES ($1,$2) RETURNING id`, m.LoanID, m.OriginatorID)
	if err != nil {
		return 0, fmt.Errorf("origination: insert working-capital loan originator mapping: %w", err)
	}
	return id, nil
}

// FindByLoanID returns every mapping of one working-capital loan in id order.
func (r *PostgresWorkingCapitalLoanOriginatorMappingRepository) FindByLoanID(ctx context.Context, loanID int64) ([]WorkingCapitalLoanOriginatorMapping, error) {
	return r.find(ctx, `WHERE loan_id = $1`, loanID)
}

// FindByOriginatorID returns every mapping referencing one originator.
func (r *PostgresWorkingCapitalLoanOriginatorMappingRepository) FindByOriginatorID(ctx context.Context, originatorID int64) ([]WorkingCapitalLoanOriginatorMapping, error) {
	return r.find(ctx, `WHERE originator_id = $1`, originatorID)
}

func (r *PostgresWorkingCapitalLoanOriginatorMappingRepository) find(ctx context.Context, where string, arg int64) ([]WorkingCapitalLoanOriginatorMapping, error) {
	var out []WorkingCapitalLoanOriginatorMapping
	err := postgres.QueryRows(ctx, r.db, `SELECT id, loan_id, originator_id
FROM m_wc_loan_originator_mapping `+where+` ORDER BY id`, []any{arg}, func(s postgres.RowScanner) error {
		var m WorkingCapitalLoanOriginatorMapping
		if err := s.Scan(&m.ID, &m.LoanID, &m.OriginatorID); err != nil {
			return err
		}
		out = append(out, m)
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("origination: find working-capital loan originator mappings: %w", err)
	}
	return out, nil
}

// Delete removes the mapping for one (working-capital loan, originator) pair.
func (r *PostgresWorkingCapitalLoanOriginatorMappingRepository) Delete(ctx context.Context, loanID, originatorID int64) error {
	if _, err := r.db.Exec(ctx, `DELETE FROM m_wc_loan_originator_mapping
WHERE loan_id = $1 AND originator_id = $2`, loanID, originatorID); err != nil {
		return fmt.Errorf("origination: delete working-capital loan originator mapping: %w", err)
	}
	return nil
}

func int64Value(p *int64) int64 {
	if p == nil {
		return 0
	}
	return *p
}

// Compile-time proof that the pgx-backed stores satisfy their interfaces.
var (
	_ LoanOriginatorRepository                      = (*PostgresLoanOriginatorRepository)(nil)
	_ LoanOriginatorMappingRepository               = (*PostgresLoanOriginatorMappingRepository)(nil)
	_ WorkingCapitalLoanOriginatorMappingRepository = (*PostgresWorkingCapitalLoanOriginatorMappingRepository)(nil)
)
