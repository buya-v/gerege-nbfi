package parties

import (
	"strings"
	"time"
)

// Client is the Go port of Fineract's Client aggregate [VERIFIED:
// Client.java:57-112], the m_client row. Optional fields are represented by
// their zero value ("" or 0) and marshalled to NULL at the persistence
// boundary, mirroring the nullable JPA columns.
type Client struct {
	ID                     int64
	AccountNumber          string
	OfficeID               int64
	TransferToOfficeID     int64
	ImageID                int64
	Status                 ClientStatus
	SubStatusID            int64
	ActivationDate         time.Time
	OfficeJoiningDate      time.Time
	Firstname              string
	Middlename             string
	Lastname               string
	Fullname               string
	DisplayName            string
	MobileNo               string
	EmailAddress           string
	IsStaff                bool
	ExternalID             string
	DateOfBirth            time.Time
	GenderID               int64
	StaffID                int64
	ClosureReasonID        int64
	ClosureDate            time.Time
	RejectionReasonID      int64
	RejectionDate          time.Time
	WithdrawalReasonID     int64
	WithdrawalDate         time.Time
	ReactivateDate         time.Time
	SubmittedOnDate        time.Time
	SavingsProductID       int64
	SavingsAccountID       int64
	ClientTypeID           int64
	ClientClassificationID int64
	LegalForm              LegalForm
	ReopenedDate           time.Time
	ProposedTransferDate   time.Time
}

// NewClient constructs a client from its identity fields, deriving the
// display name, mirroring Client.newClient's call to deriveDisplayName
// [VERIFIED: Client.java:187-198].
func NewClient(officeID int64, firstname, middlename, lastname, fullname string, legalForm LegalForm) Client {
	c := Client{
		OfficeID:   officeID,
		Firstname:  firstname,
		Middlename: middlename,
		Lastname:   lastname,
		Fullname:   fullname,
		LegalForm:  legalForm,
		Status:     ClientPending,
	}
	c.DeriveDisplayName()
	return c
}

// DeriveDisplayName ports Client.deriveDisplayName [VERIFIED:
// Client.java:378-398]:
//
//   - a non-blank fullname wins outright;
//   - otherwise, when the legal form is unset or PERSON, firstname, middlename
//     and lastname are space-joined (blank parts skipped);
//   - an ENTITY contributes no name parts and yields an empty display name.
func (c *Client) DeriveDisplayName() {
	if strings.TrimSpace(c.Fullname) != "" {
		c.DisplayName = c.Fullname
		return
	}
	if !c.LegalForm.IsEntity() {
		var parts []string
		for _, part := range []string{c.Firstname, c.Middlename, c.Lastname} {
			if strings.TrimSpace(part) != "" {
				parts = append(parts, part)
			}
		}
		c.DisplayName = strings.Join(parts, " ")
		return
	}
	c.DisplayName = ""
}

// IsActive is the Client.isActive predicate [VERIFIED: Client.java:614-616].
func (c *Client) IsActive() bool { return c.Status.IsActive() }

// IsClosed is the Client.isClosed predicate [VERIFIED: Client.java:618-620].
func (c *Client) IsClosed() bool { return c.Status.IsClosed() }

// IsNotActive ports Client.isNotActive [VERIFIED: Client.java:604-606].
func (c *Client) IsNotActive() bool { return !c.Status.IsActive() }
