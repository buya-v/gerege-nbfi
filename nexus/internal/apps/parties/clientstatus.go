package parties

import "fmt"

// ClientStatus is m_client.status_enum — Fineract's ClientStatus
// [VERIFIED: ClientStatus.java:24-96]:
//
//	INVALID(0)
//	PENDING(100)
//	ACTIVE(300)
//	TRANSFER_IN_PROGRESS(303)
//	TRANSFER_ON_HOLD(304)
//	CLOSED(600)
//	REJECTED(700)
//	WITHDRAWN(800)
//
// The stored values are NOT contiguous (the active band is around 300 with
// transfer sub-states at 303/304, and rejected/withdrawn sit in the 7xx/8xx
// band), so the explicit table below is the contract rather than an iota.
type ClientStatus int32

const (
	ClientInvalid ClientStatus = iota
	ClientPending
	ClientActive
	ClientTransferInProgress
	ClientTransferOnHold
	ClientClosed
	ClientRejected
	ClientWithdrawn
)

var clientStatusStoredValue = map[ClientStatus]int32{
	ClientInvalid:            0,
	ClientPending:            100,
	ClientActive:             300,
	ClientTransferInProgress: 303,
	ClientTransferOnHold:     304,
	ClientClosed:             600,
	ClientRejected:           700,
	ClientWithdrawn:          800,
}

var clientStatusName = map[ClientStatus]string{
	ClientInvalid:            "INVALID",
	ClientPending:            "PENDING",
	ClientActive:             "ACTIVE",
	ClientTransferInProgress: "TRANSFER_IN_PROGRESS",
	ClientTransferOnHold:     "TRANSFER_ON_HOLD",
	ClientClosed:             "CLOSED",
	ClientRejected:           "REJECTED",
	ClientWithdrawn:          "WITHDRAWN",
}

var clientStatusFromStored = map[int32]ClientStatus{}

// StoredValue returns m_client.status_enum.
func (s ClientStatus) StoredValue() int32 {
	v, ok := clientStatusStoredValue[s]
	if !ok {
		panic(fmt.Sprintf("parties: unknown ClientStatus %d", int32(s)))
	}
	return v
}

func (s ClientStatus) String() string {
	if n, ok := clientStatusName[s]; ok {
		return n
	}
	return fmt.Sprintf("ClientStatus(%d)", int32(s))
}

// ClientStatusFromStoredValue decodes m_client.status_enum. ok is false outside
// the eight legal values, matching ClientStatus.fromInt's INVALID fallback
// [VERIFIED: ClientStatus.java:35-49].
func ClientStatusFromStoredValue(v int32) (ClientStatus, bool) {
	s, ok := clientStatusFromStored[v]
	return s, ok
}

func (s ClientStatus) IsPending() bool            { return s == ClientPending }
func (s ClientStatus) IsActive() bool             { return s == ClientActive }
func (s ClientStatus) IsClosed() bool             { return s == ClientClosed }
func (s ClientStatus) IsRejected() bool           { return s == ClientRejected }
func (s ClientStatus) IsWithdrawn() bool          { return s == ClientWithdrawn }
func (s ClientStatus) IsTransferInProgress() bool { return s == ClientTransferInProgress }
func (s ClientStatus) IsTransferOnHold() bool     { return s == ClientTransferOnHold }

// IsUnderTransfer is the union of the two transfer states
// [VERIFIED: ClientStatus.java:92-94].
func (s ClientStatus) IsUnderTransfer() bool { return s.IsTransferInProgress() || s.IsTransferOnHold() }

func init() {
	for s, v := range clientStatusStoredValue {
		if _, dup := clientStatusFromStored[v]; dup {
			panic(fmt.Sprintf("parties: client status encode table is not injective at %d", v))
		}
		clientStatusFromStored[v] = s
	}
}
