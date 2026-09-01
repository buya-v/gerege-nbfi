package parties

import (
	"context"
	"fmt"
	"time"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL storage layer for the client-and-group slice.
// It honours the package import-graph rule — parties depends only on
// internal/platform/postgres, never on github.com/jackc/pgx/v5 directly.

// ClientRepository is the persistence surface for m_client.
type ClientRepository interface {
	Insert(ctx context.Context, c Client) (int64, error)
	FindByID(ctx context.Context, id int64) (*Client, error)
	FindByAccountNumber(ctx context.Context, accountNumber string) (*Client, error)
	FindByExternalID(ctx context.Context, externalID string) (*Client, error)
	UpdateStatus(ctx context.Context, id int64, status ClientStatus) error
}

// PostgresClientRepository persists m_client rows.
type PostgresClientRepository struct {
	db postgres.DB
}

// NewPostgresClientRepository constructs the client store.
func NewPostgresClientRepository(db postgres.DB) *PostgresClientRepository {
	return &PostgresClientRepository{db: db}
}

const clientColumns = `id, account_no, office_id, transfer_to_office_id, image_id,
status_enum, sub_status, activation_date, office_joining_date, firstname,
middlename, lastname, fullname, display_name, mobile_no, email_address,
is_staff, external_id, date_of_birth, gender_cv_id, staff_id,
closure_reason_cv_id, closedon_date, reject_reason_cv_id, rejectedon_date,
withdraw_reason_cv_id, withdrawn_on_date, reactivated_on_date, submittedon_date,
default_savings_product, default_savings_account, client_type_cv_id,
client_classification_cv_id, legal_form_enum, reopened_on_date,
proposed_transfer_date`

// Insert writes an m_client row, deriving id and display name. It returns the
// new id.
func (r *PostgresClientRepository) Insert(ctx context.Context, c Client) (int64, error) {
	if c.DisplayName == "" {
		c.DeriveDisplayName()
	}
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_client
(account_no, office_id, transfer_to_office_id, image_id, status_enum, sub_status,
 activation_date, office_joining_date, firstname, middlename, lastname, fullname,
 display_name, mobile_no, email_address, is_staff, external_id, date_of_birth,
 gender_cv_id, staff_id, closure_reason_cv_id, closedon_date, reject_reason_cv_id,
 rejectedon_date, withdraw_reason_cv_id, withdrawn_on_date, reactivated_on_date,
 submittedon_date, default_savings_product, default_savings_account, client_type_cv_id,
 client_classification_cv_id, legal_form_enum, reopened_on_date, proposed_transfer_date)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,
 $22,$23,$24,$25,$26,$27,$28,$29,$30,$31,$32,$33,$34,$35) RETURNING id`,
		nullStr(c.AccountNumber), nullInt(c.OfficeID), nullInt(c.TransferToOfficeID),
		nullInt(c.ImageID), c.Status.StoredValue(), nullInt(c.SubStatusID),
		nullTime(c.ActivationDate), nullTime(c.OfficeJoiningDate),
		nullStr(c.Firstname), nullStr(c.Middlename), nullStr(c.Lastname), nullStr(c.Fullname),
		c.DisplayName, nullStr(c.MobileNo), nullStr(c.EmailAddress), c.IsStaff,
		nullStr(c.ExternalID), nullTime(c.DateOfBirth), nullInt(c.GenderID), nullInt(c.StaffID),
		nullInt(c.ClosureReasonID), nullTime(c.ClosureDate), nullInt(c.RejectionReasonID),
		nullTime(c.RejectionDate), nullInt(c.WithdrawalReasonID), nullTime(c.WithdrawalDate),
		nullTime(c.ReactivateDate), nullTime(c.SubmittedOnDate), nullInt(c.SavingsProductID),
		nullInt(c.SavingsAccountID), nullInt(c.ClientTypeID), nullInt(c.ClientClassificationID),
		nullInt(int64(c.LegalForm.StoredValue())), nullTime(c.ReopenedDate), nullTime(c.ProposedTransferDate))
	if err != nil {
		return 0, fmt.Errorf("parties: insert client: %w", err)
	}
	return id, nil
}

// FindByID resolves one client by id, or (nil, nil) on a miss.
func (r *PostgresClientRepository) FindByID(ctx context.Context, id int64) (*Client, error) {
	return r.findOne(ctx, `SELECT `+clientColumns+` FROM m_client WHERE id = $1`, id)
}

// FindByAccountNumber resolves one client by account number, or (nil, nil).
func (r *PostgresClientRepository) FindByAccountNumber(ctx context.Context, accountNumber string) (*Client, error) {
	return r.findOne(ctx, `SELECT `+clientColumns+` FROM m_client WHERE account_no = $1`, accountNumber)
}

// FindByExternalID resolves one client by external id, or (nil, nil).
func (r *PostgresClientRepository) FindByExternalID(ctx context.Context, externalID string) (*Client, error) {
	return r.findOne(ctx, `SELECT `+clientColumns+` FROM m_client WHERE external_id = $1`, externalID)
}

func (r *PostgresClientRepository) findOne(ctx context.Context, query string, arg any) (*Client, error) {
	var out *Client
	err := postgres.QueryRows(ctx, r.db, query, []any{arg}, func(s postgres.RowScanner) error {
		c, err := scanClient(s)
		if err != nil {
			return err
		}
		out = &c
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("parties: find client: %w", err)
	}
	return out, nil
}

// UpdateStatus overwrites m_client.status_enum.
func (r *PostgresClientRepository) UpdateStatus(ctx context.Context, id int64, status ClientStatus) error {
	if _, err := r.db.Exec(ctx, `UPDATE m_client SET status_enum = $1 WHERE id = $2`, status.StoredValue(), id); err != nil {
		return fmt.Errorf("parties: update client status: %w", err)
	}
	return nil
}

func scanClient(s postgres.RowScanner) (Client, error) {
	var c Client
	var status int32
	var subStatus, imageID, transferOffice, genderID, staffID, closureReasonID,
		rejectReasonID, withdrawReasonID, savingsProductID, savingsAccountID,
		clientTypeID, clientClassificationID, legalForm *int64
	var activation, officeJoining, dob, closedOn, rejectedOn, withdrawnOn,
		reactivatedOn, submittedOn, reopenedOn, proposedTransfer *time.Time
	if err := s.Scan(
		&c.ID, &c.AccountNumber, &c.OfficeID, &transferOffice, &imageID,
		&status, &subStatus, &activation, &officeJoining, &c.Firstname,
		&c.Middlename, &c.Lastname, &c.Fullname, &c.DisplayName, &c.MobileNo,
		&c.EmailAddress, &c.IsStaff, &c.ExternalID, &dob, &genderID, &staffID,
		&closureReasonID, &closedOn, &rejectReasonID, &rejectedOn,
		&withdrawReasonID, &withdrawnOn, &reactivatedOn, &submittedOn,
		&savingsProductID, &savingsAccountID, &clientTypeID, &clientClassificationID,
		&legalForm, &reopenedOn, &proposedTransfer); err != nil {
		return Client{}, err
	}
	st, ok := ClientStatusFromStoredValue(status)
	if !ok {
		return Client{}, fmt.Errorf("parties: unknown client status_enum %d", status)
	}
	c.Status = st
	c.TransferToOfficeID = valInt(transferOffice)
	c.ImageID = valInt(imageID)
	c.SubStatusID = valInt(subStatus)
	c.ActivationDate = valTime(activation)
	c.OfficeJoiningDate = valTime(officeJoining)
	c.DateOfBirth = valTime(dob)
	c.GenderID = valInt(genderID)
	c.StaffID = valInt(staffID)
	c.ClosureReasonID = valInt(closureReasonID)
	c.ClosureDate = valTime(closedOn)
	c.RejectionReasonID = valInt(rejectReasonID)
	c.RejectionDate = valTime(rejectedOn)
	c.WithdrawalReasonID = valInt(withdrawReasonID)
	c.WithdrawalDate = valTime(withdrawnOn)
	c.ReactivateDate = valTime(reactivatedOn)
	c.SubmittedOnDate = valTime(submittedOn)
	c.SavingsProductID = valInt(savingsProductID)
	c.SavingsAccountID = valInt(savingsAccountID)
	c.ClientTypeID = valInt(clientTypeID)
	c.ClientClassificationID = valInt(clientClassificationID)
	c.LegalForm = LegalForm(valInt(legalForm))
	c.ReopenedDate = valTime(reopenedOn)
	c.ProposedTransferDate = valTime(proposedTransfer)
	return c, nil
}

// GroupRepository is the persistence surface for m_group.
type GroupRepository interface {
	Insert(ctx context.Context, g Group) (int64, error)
	FindByID(ctx context.Context, id int64) (*Group, error)
	FindByAccountNumber(ctx context.Context, accountNumber string) (*Group, error)
	UpdateStatus(ctx context.Context, id int64, status GroupingTypeStatus) error
}

// PostgresGroupRepository persists m_group rows.
type PostgresGroupRepository struct {
	db postgres.DB
}

// NewPostgresGroupRepository constructs the group store.
func NewPostgresGroupRepository(db postgres.DB) *PostgresGroupRepository {
	return &PostgresGroupRepository{db: db}
}

// Insert writes an m_group row, returning its id.
func (r *PostgresGroupRepository) Insert(ctx context.Context, g Group) (int64, error) {
	id, err := postgres.InsertReturningInt64(ctx, r.db, `INSERT INTO m_group
(external_id, status_enum, activation_date, office_id, staff_id, parent_id,
 level_id, display_name, hierarchy, closure_reason_cv_id, closedon_date,
 submittedon_date, account_no)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13) RETURNING id`,
		nullStr(g.ExternalID), g.Status.StoredValue(), nullTime(g.ActivationDate),
		nullInt(g.OfficeID), nullInt(g.StaffID), nullInt(g.ParentID), g.Level.ID,
		nullStr(g.Name), nullStr(g.Hierarchy), nullInt(g.ClosureReasonID),
		nullTime(g.ClosureDate), nullTime(g.SubmittedOnDate), nullStr(g.AccountNumber))
	if err != nil {
		return 0, fmt.Errorf("parties: insert group: %w", err)
	}
	return id, nil
}

// FindByID resolves one group by id, or (nil, nil) on a miss.
func (r *PostgresGroupRepository) FindByID(ctx context.Context, id int64) (*Group, error) {
	return r.findOne(ctx, `SELECT id, external_id, status_enum, activation_date,
office_id, staff_id, parent_id, level_id, display_name, hierarchy,
closure_reason_cv_id, closedon_date, submittedon_date, account_no
FROM m_group WHERE id = $1`, id)
}

// FindByAccountNumber resolves one group by account number, or (nil, nil).
func (r *PostgresGroupRepository) FindByAccountNumber(ctx context.Context, accountNumber string) (*Group, error) {
	return r.findOne(ctx, `SELECT id, external_id, status_enum, activation_date,
office_id, staff_id, parent_id, level_id, display_name, hierarchy,
closure_reason_cv_id, closedon_date, submittedon_date, account_no
FROM m_group WHERE account_no = $1`, accountNumber)
}

func (r *PostgresGroupRepository) findOne(ctx context.Context, query string, arg any) (*Group, error) {
	var out *Group
	err := postgres.QueryRows(ctx, r.db, query, []any{arg}, func(s postgres.RowScanner) error {
		var g Group
		var status int32
		var activation, closedOn, submittedOn *time.Time
		var staffID, parentID, closureReasonID *int64
		if err := s.Scan(&g.ID, &g.ExternalID, &status, &activation, &g.OfficeID,
			&staffID, &parentID, &g.Level.ID, &g.Name, &g.Hierarchy,
			&closureReasonID, &closedOn, &submittedOn, &g.AccountNumber); err != nil {
			return err
		}
		st, ok := GroupingTypeStatusFromStoredValue(status)
		if !ok {
			return fmt.Errorf("parties: unknown group status_enum %d", status)
		}
		g.Status = st
		g.ActivationDate = valTime(activation)
		g.StaffID = valInt(staffID)
		g.ParentID = valInt(parentID)
		g.ClosureReasonID = valInt(closureReasonID)
		g.ClosureDate = valTime(closedOn)
		g.SubmittedOnDate = valTime(submittedOn)
		out = &g
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("parties: find group: %w", err)
	}
	return out, nil
}

// UpdateStatus overwrites m_group.status_enum.
func (r *PostgresGroupRepository) UpdateStatus(ctx context.Context, id int64, status GroupingTypeStatus) error {
	if _, err := r.db.Exec(ctx, `UPDATE m_group SET status_enum = $1 WHERE id = $2`, status.StoredValue(), id); err != nil {
		return fmt.Errorf("parties: update group status: %w", err)
	}
	return nil
}

// GroupLevelRepository is the persistence surface for m_group_level.
type GroupLevelRepository interface {
	List(ctx context.Context) ([]GroupLevel, error)
}

// PostgresGroupLevelRepository persists m_group_level rows.
type PostgresGroupLevelRepository struct {
	db postgres.DB
}

// NewPostgresGroupLevelRepository constructs the level store.
func NewPostgresGroupLevelRepository(db postgres.DB) *PostgresGroupLevelRepository {
	return &PostgresGroupLevelRepository{db: db}
}

// List returns the level catalogue in id order.
func (r *PostgresGroupLevelRepository) List(ctx context.Context) ([]GroupLevel, error) {
	var out []GroupLevel
	err := postgres.QueryRows(ctx, r.db, `SELECT id, parent_id, super_parent,
level_name, recursable, can_have_clients FROM m_group_level ORDER BY id`, nil,
		func(s postgres.RowScanner) error {
			var l GroupLevel
			var parentID *int64
			if err := s.Scan(&l.ID, &parentID, &l.SuperParent, &l.LevelName,
				&l.Recursable, &l.CanHaveClients); err != nil {
				return err
			}
			l.ParentID = valInt(parentID)
			out = append(out, l)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("parties: list group levels: %w", err)
	}
	return out, nil
}

func nullInt(v int64) any {
	if v == 0 {
		return nil
	}
	return v
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

func valInt(p *int64) int64 {
	if p == nil {
		return 0
	}
	return *p
}

func valTime(p *time.Time) time.Time {
	if p == nil {
		return time.Time{}
	}
	return *p
}

// Compile-time proof that the pgx-backed stores satisfy their interfaces.
var (
	_ ClientRepository     = (*PostgresClientRepository)(nil)
	_ GroupRepository      = (*PostgresGroupRepository)(nil)
	_ GroupLevelRepository = (*PostgresGroupLevelRepository)(nil)
)
