package ledger

import (
	"context"
	"fmt"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL storage layer for slice A2. It implements the
// read surfaces that resolution needs behind the existing repository
// interfaces, so the in-memory stores can be swapped for these without touching
// the resolver.
//
// The import-graph rule is enforced here, not merely documented: this package
// depends on internal/platform/postgres (the one permitted driver seam) and
// never on github.com/jackc/pgx/v5 directly. PostgreSQL is the only permitted
// database; Go talks to it via pgx/v5.
//
// The repository interfaces in mapping.go, financialactivity.go and glaccount.go
// were written before this file existed and deliberately carry no
// context.Context: they model "which single GL account does this posting hit?",
// which is a pure question for the in-memory store. A pgx-backed implementation
// cannot answer it without a context, so each store here captures the context it
// was constructed with and uses it for every query. Construct a fresh store when
// request-scoped cancellation matters; for the read-only resolution queries A2
// issues, a constructor-supplied context is the correct unit of lifetime.

// PostgresMappingStore is a MappingRepository over acc_product_mapping, backed
// by PostgreSQL via the platform postgres package. It reproduces the single
// getSingleResult() semantics of the in-memory store in ONE place, so the two
// cannot drift.
type PostgresMappingStore struct {
	q   postgres.Querier
	ctx context.Context

	// NullPaymentTypePolicy decides how FindByPaymentType treats a nil payment
	// type. It belongs to the query layer, exactly as on InMemoryMappingStore.
	NullPaymentTypePolicy NullPaymentTypePolicy
}

// NewPostgresMappingStore constructs a MappingRepository that reads
// acc_product_mapping through q.
func NewPostgresMappingStore(ctx context.Context, q postgres.Querier) *PostgresMappingStore {
	return &PostgresMappingStore{q: q, ctx: ctx}
}

const accProductMappingColumns = `id, gl_account_id, product_id, product_type, financial_account_type, payment_type, charge_id, charge_off_reason_id, write_off_reason_id, capitalized_income_classification_id, buydown_fee_classification_id`

func (s *PostgresMappingStore) queryMappings(sql string, args ...any) ([]MappingRow, error) {
	var out []MappingRow
	err := postgres.QueryRows(s.ctx, s.q, sql, args, func(rs postgres.RowScanner) error {
		var row MappingRow
		if err := rs.Scan(
			&row.ID,
			&row.GLAccountID,
			&row.ProductID,
			&row.ProductType,
			&row.FinancialAccountType,
			&row.PaymentTypeID,
			&row.ChargeID,
			&row.ChargeOffReasonID,
			&row.WriteOffReasonID,
			&row.CapitalizedIncomeClassificationID,
			&row.BuydownFeeClassificationID,
		); err != nil {
			return err
		}
		out = append(out, row)
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("ledger: query acc_product_mapping: %w", err)
	}
	return out, nil
}

// FindCoreProductToFinAccountMapping reproduces the core-row query
// [ProductToGLAccountMappingRepository.java:38-40]: the key row plus all six
// discriminators NULL.
func (s *PostgresMappingStore) FindCoreProductToFinAccountMapping(productID int64, productType, financialAccountType int32) (*MappingRow, error) {
	rows, err := s.queryMappings(`SELECT `+accProductMappingColumns+`
		FROM acc_product_mapping
		WHERE product_id = $1 AND product_type = $2 AND financial_account_type = $3
		  AND payment_type IS NULL
		  AND charge_id IS NULL
		  AND charge_off_reason_id IS NULL
		  AND write_off_reason_id IS NULL
		  AND capitalized_income_classification_id IS NULL
		  AND buydown_fee_classification_id IS NULL`,
		productID, productType, financialAccountType)
	if err != nil {
		return nil, err
	}
	return single(rows)
}

// FindByPaymentType reproduces the derived payment-type query, which filters on
// FOUR columns only [ProductToGLAccountMappingRepository.java:30-31].
func (s *PostgresMappingStore) FindByPaymentType(productID int64, productType, financialAccountType int32, paymentTypeID *int64) (*MappingRow, error) {
	if paymentTypeID == nil && s.NullPaymentTypePolicy == NullPaymentTypeMatchesNothing {
		return nil, nil
	}
	rows, err := s.queryMappings(`SELECT `+accProductMappingColumns+`
		FROM acc_product_mapping
		WHERE product_id = $1 AND product_type = $2 AND financial_account_type = $3
		  AND payment_type IS NULL`,
		productID, productType, financialAccountType)
	if paymentTypeID != nil {
		rows, err = s.queryMappings(`SELECT `+accProductMappingColumns+`
			FROM acc_product_mapping
			WHERE product_id = $1 AND product_type = $2 AND financial_account_type = $3
			  AND payment_type = $4`,
			productID, productType, financialAccountType, *paymentTypeID)
	}
	if err != nil {
		return nil, err
	}
	return single(rows)
}

// FindByCharge reproduces the joined charge-id equality query
// [ProductToGLAccountMappingRepository.java:33-36]. A NULL charge matches
// nothing, because there is no joined charge row to compare.
func (s *PostgresMappingStore) FindByCharge(productID int64, productType, financialAccountType int32, chargeID *int64) (*MappingRow, error) {
	if chargeID == nil {
		return nil, nil
	}
	rows, err := s.queryMappings(`SELECT `+accProductMappingColumns+`
		FROM acc_product_mapping
		WHERE product_id = $1 AND product_type = $2 AND financial_account_type = $3
		  AND charge_id = $4`,
		productID, productType, financialAccountType, *chargeID)
	if err != nil {
		return nil, err
	}
	return single(rows)
}

// FindChargeOffReasonMapping reproduces the charge-off reason lookup, which keys
// on (product_id, product_type, charge_off_reason_id) and does NOT filter on
// financial_account_type [ProductToGLAccountMappingRepository.java:76-78].
func (s *PostgresMappingStore) FindChargeOffReasonMapping(productID int64, productType int32, chargeOffReasonID int64) (*MappingRow, error) {
	return s.findByReasonColumn("charge_off_reason_id", productID, productType, chargeOffReasonID)
}

// FindWriteOffReasonMapping reproduces ProductToGLAccountMappingRepository.java:109-111.
func (s *PostgresMappingStore) FindWriteOffReasonMapping(productID int64, productType int32, writeOffReasonID int64) (*MappingRow, error) {
	return s.findByReasonColumn("write_off_reason_id", productID, productType, writeOffReasonID)
}

// FindCapitalizedIncomeClassificationMapping reproduces ProductToGLAccountMappingRepository.java:105-107.
func (s *PostgresMappingStore) FindCapitalizedIncomeClassificationMapping(productID int64, productType int32, classificationID int64) (*MappingRow, error) {
	return s.findByReasonColumn("capitalized_income_classification_id", productID, productType, classificationID)
}

// FindBuydownFeeClassificationMapping reproduces ProductToGLAccountMappingRepository.java:101-103.
func (s *PostgresMappingStore) FindBuydownFeeClassificationMapping(productID int64, productType int32, classificationID int64) (*MappingRow, error) {
	return s.findByReasonColumn("buydown_fee_classification_id", productID, productType, classificationID)
}

// findByReasonColumn is the shared shape of the four reason/classification
// lookups: they all key on (product_id, product_type, <column>) and none of
// them filters on financial_account_type.
func (s *PostgresMappingStore) findByReasonColumn(column string, productID int64, productType int32, valueID int64) (*MappingRow, error) {
	rows, err := s.queryMappings(`SELECT `+accProductMappingColumns+`
		FROM acc_product_mapping
		WHERE product_id = $1 AND product_type = $2 AND `+column+` = $3`,
		productID, productType, valueID)
	if err != nil {
		return nil, err
	}
	return single(rows)
}

// PostgresFinancialActivityStore is a FinancialActivityRepository over
// acc_gl_financial_activity_account.
type PostgresFinancialActivityStore struct {
	q   postgres.Querier
	ctx context.Context
}

// NewPostgresFinancialActivityStore constructs a FinancialActivityRepository
// that reads acc_gl_financial_activity_account through q.
func NewPostgresFinancialActivityStore(ctx context.Context, q postgres.Querier) *PostgresFinancialActivityStore {
	return &PostgresFinancialActivityStore{q: q, ctx: ctx}
}

// FindByActivity reproduces
// FinancialActivityAccountRepository.findByFinancialActivityType
// [FinancialActivityAccountRepository.java:29-30], including the non-unique
// result refusal the write service relies on rather than pre-checking.
func (s *PostgresFinancialActivityStore) FindByActivity(a FinancialActivity) (*FinancialActivityAccountRow, error) {
	var rows []FinancialActivityAccountRow
	err := postgres.QueryRows(s.ctx, s.q, `SELECT id, gl_account_id, financial_activity_type
		FROM acc_gl_financial_activity_account
		WHERE financial_activity_type = $1`, []any{a.StoredValue()},
		func(rs postgres.RowScanner) error {
			var row FinancialActivityAccountRow
			var activityValue int32
			if err := rs.Scan(&row.ID, &row.GLAccountID, &activityValue); err != nil {
				return err
			}
			activity, ok := FinancialActivityFromValue(activityValue)
			if !ok {
				return fmt.Errorf("ledger: acc_gl_financial_activity_account row %d carries unknown financial_activity_type %d", row.ID, activityValue)
			}
			row.Activity = activity
			rows = append(rows, row)
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("ledger: query acc_gl_financial_activity_account: %w", err)
	}
	switch len(rows) {
	case 0:
		return nil, nil
	case 1:
		row := rows[0]
		return &row, nil
	default:
		return nil, newErr(ErrNonUniqueMappingResult, "",
			"More than one result was returned from Query.getSingleResult()")
	}
}

// GLAccountReadRepository is the PostgreSQL read surface for acc_gl_account.
//
// It returns an error where the in-memory GLAccountRepository returns a bool,
// because a database read can fail and that failure must propagate; the
// bool-only interface cannot represent it and remains the conformance /
// test-double surface consumed by the resolver.
type GLAccountReadRepository interface {
	AccountByID(id int64) (*GLAccount, error)
}

// PostgresGLAccountStore is a GLAccountReadRepository over acc_gl_account.
type PostgresGLAccountStore struct {
	q   postgres.Querier
	ctx context.Context
}

// NewPostgresGLAccountStore constructs a GLAccountReadRepository that reads
// acc_gl_account through q.
func NewPostgresGLAccountStore(ctx context.Context, q postgres.Querier) *PostgresGLAccountStore {
	return &PostgresGLAccountStore{q: q, ctx: ctx}
}

// AccountByID resolves one account id to the account itself, or (nil, nil) on a
// miss.
func (s *PostgresGLAccountStore) AccountByID(id int64) (*GLAccount, error) {
	var row GLAccount
	var parentID *int64
	var hierarchy, description *string
	var tagID *int64
	var classificationValue, usageValue int32
	found := false

	err := postgres.QueryRows(s.ctx, s.q, `SELECT id, name, parent_id, hierarchy, gl_code,
			disabled, manual_journal_entries_allowed, account_usage,
			classification_enum, tag_id, description
		FROM acc_gl_account
		WHERE id = $1`, []any{id},
		func(rs postgres.RowScanner) error {
			if err := rs.Scan(
				&row.ID,
				&row.Name,
				&parentID,
				&hierarchy,
				&row.GLCode,
				&row.Disabled,
				&row.ManualEntriesAllowed,
				&usageValue,
				&classificationValue,
				&tagID,
				&description,
			); err != nil {
				return err
			}
			found = true
			return nil
		})
	if err != nil {
		return nil, fmt.Errorf("ledger: query acc_gl_account: %w", err)
	}
	if !found {
		return nil, nil
	}

	classification, ok := ClassificationFromStoredValue(classificationValue)
	if !ok {
		return nil, fmt.Errorf("ledger: acc_gl_account row %d carries unknown classification_enum %d", row.ID, classificationValue)
	}
	usage, ok := UsageFromStoredValue(usageValue)
	if !ok {
		return nil, fmt.Errorf("ledger: acc_gl_account row %d carries unknown account_usage %d", row.ID, usageValue)
	}

	row.ParentID = parentID
	row.Classification = classification
	row.Usage = usage
	row.TagID = tagID
	if hierarchy != nil {
		row.Hierarchy = *hierarchy
	}
	if description != nil {
		row.Description = *description
	}
	return &row, nil
}

// Compile-time proof that the pgx-backed stores satisfy the interfaces they are
// meant to replace, so an accidental signature drift fails the build rather
// than the resolver.
var (
	_ MappingRepository           = (*PostgresMappingStore)(nil)
	_ FinancialActivityRepository = (*PostgresFinancialActivityStore)(nil)
	_ GLAccountReadRepository     = (*PostgresGLAccountStore)(nil)
)
