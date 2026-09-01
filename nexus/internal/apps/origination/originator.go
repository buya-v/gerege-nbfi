package origination

// LoanOriginator is the Go port of the loan-originator aggregate
// [VERIFIED: LoanOriginator.java:24-73]. It records who originated loans: an
// external identity, a display name, an ACTIVE/PENDING/INACTIVE status, and the
// originator/channel code-value references.
//
// The CodeValue references (originatorType, channelType) are kept as IDs; the
// code-value catalogue itself belongs to the infrastructure codes context, not
// here.
type LoanOriginator struct {
	ID         int64  // m_loan_originator.id
	ExternalID string // external_id (unique, required)
	Name       string // name

	Status LoanOriginatorStatus // status (EnumType.STRING)

	OriginatorTypeID int64 // originator_type_cv_id (0 = none)
	ChannelTypeID    int64 // channel_type_cv_id (0 = none)
}

// NewLoanOriginator ports the create factory: externalId, name, status,
// originatorType and channelType [VERIFIED: LoanOriginator.java:52-61]. Newly
// created originators are ACTIVE by default (the write path supplies ACTIVE
// unless a status is given) [VERIFIED: LoanOriginatorWritePlatformServiceImpl
// .java:106-108, LoanOriginatorHelper.java:129].
func NewLoanOriginator(externalID, name string, originatorTypeID, channelTypeID int64) LoanOriginator {
	return LoanOriginator{
		ExternalID:       externalID,
		Name:             name,
		Status:           OriginatorActive,
		OriginatorTypeID: originatorTypeID,
		ChannelTypeID:    channelTypeID,
	}
}

// Update ports LoanOriginator.update: it replaces name, status, originatorType
// and channelType [VERIFIED: LoanOriginator.java:63-68].
func (o *LoanOriginator) Update(name string, status LoanOriginatorStatus, originatorTypeID, channelTypeID int64) {
	o.Name = name
	o.Status = status
	o.OriginatorTypeID = originatorTypeID
	o.ChannelTypeID = channelTypeID
}
