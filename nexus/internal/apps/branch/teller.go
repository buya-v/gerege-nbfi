package branch

import "time"

// Teller is the m_tellers aggregate root: a cash office within a branch, tied
// to a debit and credit GL account and carrying a lifecycle status.
//
// [VERIFIED: Teller.java — office_id, debit_account_id, credit_account_id,
// name (unique), description, valid_from, valid_to, state; name length 100.]
type Teller struct {
	ID              int64
	OfficeID        int64
	DebitAccountID  *int64
	CreditAccountID *int64
	Name            string
	Description     string
	StartDate       time.Time
	EndDate         time.Time
	Status          TellerStatus
}

// OfficeIDFor returns the office id of a teller, mirroring the officeId()
// accessor Fineract's update path reads.
func (t Teller) OfficeIDFor() int64 { return t.OfficeID }
