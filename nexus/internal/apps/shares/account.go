package shares

import "time"

// ShareAccount is the m_share_account aggregate root: one client's holding in a
// share product, carrying the four running share totals and the lifecycle dates.
//
// [VERIFIED: ShareAccount.java — account_no, external_id, client_id,
// product_id, status_enum, submitted_on_date, approved_date, activated_date,
// closed_date, total_approved_shares, total_pending_shares,
// total_redeemed_shares, total_issued_shares, savings_account_id, currency.]
type ShareAccount struct {
	ID                  int64
	AccountNo           string
	ExternalID          string
	ClientID            int64
	ProductID           int64
	Status              ShareAccountStatusType
	SubmittedDate       time.Time
	ApprovedDate        time.Time
	ActivatedDate       time.Time
	ClosedDate          time.Time
	TotalApprovedShares int64
	TotalPendingShares  int64
	TotalRedeemedShares int64
	TotalIssuedShares   int64
	SavingsAccountID    *int64
	CurrencyCode        string
}
