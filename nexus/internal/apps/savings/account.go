package savings

// SavingsAccount is the Go port of the savings-account aggregate: the identity,
// status and product facts a deposit write path reads from and writes to.
//
// It is deliberately a pure model with no database dependency, matching the
// derive-don't-store ruling. The reference structure is
// SavingsAccount.java [fineract-savings/.../savings/domain/SavingsAccount.java],
// reduced here to the core fields a later persistence and posting slice needs:
// external identity, status, deposit type, currency, the derived summary, and
// the account-level interest-rate chart.
type SavingsAccount struct {
	// ID is the surrogate primary key m_savings_account.id. Zero means
	// not-yet-persisted, the same sentinel the oracle's AbstractPersistable
	// uses before the sequence assigns an id.
	ID int64

	// ExternalID is the client-visible identifier (m_savings_account.external_id).
	ExternalID string

	// Status is m_savings_account.status_enum.
	Status SavingsAccountStatusType

	// DepositType is the product's m_savings_product.deposit_type_enum.
	DepositType DepositAccountType

	// CurrencyCode is the ISO 4217 code of the account's monetary currency.
	CurrencyCode string

	// Summary is the derived account summary (totals and running balance).
	// It is always recomputed from its transactions, never a primary write
	// target.
	Summary SavingsAccountSummary

	// InterestRateChart is the account-level chart of interest-rate slabs.
	// It may be nil for accounts that inherit the product chart.
	InterestRateChart *DepositAccountInterestRateChart
}

// IsDisabled reports whether the aggregate may not take deposits under the
// runtime gate. A disabled Config means no deposit write path exists; this
// helper keeps that check adjacent to the account rather than scattered across
// a future service layer.
func (a SavingsAccount) IsDisabled() bool { return !a.Status.IsActive() }

// NewSavingsAccount assembles a savings account with the summary zeroed. The
// summary is derived and empty until the first posting is applied.
func NewSavingsAccount(externalID string, depositType DepositAccountType, currencyCode string) SavingsAccount {
	return SavingsAccount{
		ExternalID:   externalID,
		Status:       StatusInvalid,
		DepositType:  depositType,
		CurrencyCode: currencyCode,
	}
}
