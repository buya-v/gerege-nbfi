package parties

import (
	"fmt"
	"strings"
	"time"
)

// GroupingTypeStatus is m_group.status_enum — Fineract's GroupingTypeStatus
// [VERIFIED: GroupingTypeStatus.java:24-84]:
//
//	INVALID(0), PENDING(100), ACTIVE(300),
//	TRANSFER_IN_PROGRESS(303), TRANSFER_ON_HOLD(304), CLOSED(600)
type GroupingTypeStatus int32

const (
	GroupingInvalid GroupingTypeStatus = iota
	GroupingPending
	GroupingActive
	GroupingTransferInProgress
	GroupingTransferOnHold
	GroupingClosed
)

var groupingStoredValue = map[GroupingTypeStatus]int32{
	GroupingInvalid:            0,
	GroupingPending:            100,
	GroupingActive:             300,
	GroupingTransferInProgress: 303,
	GroupingTransferOnHold:     304,
	GroupingClosed:             600,
}

var groupingName = map[GroupingTypeStatus]string{
	GroupingInvalid:            "INVALID",
	GroupingPending:            "PENDING",
	GroupingActive:             "ACTIVE",
	GroupingTransferInProgress: "TRANSFER_IN_PROGRESS",
	GroupingTransferOnHold:     "TRANSFER_ON_HOLD",
	GroupingClosed:             "CLOSED",
}

var groupingFromStored = map[int32]GroupingTypeStatus{}

// StoredValue returns m_group.status_enum.
func (s GroupingTypeStatus) StoredValue() int32 {
	v, ok := groupingStoredValue[s]
	if !ok {
		panic(fmt.Sprintf("parties: unknown GroupingTypeStatus %d", int32(s)))
	}
	return v
}

func (s GroupingTypeStatus) String() string {
	if n, ok := groupingName[s]; ok {
		return n
	}
	return fmt.Sprintf("GroupingTypeStatus(%d)", int32(s))
}

// GroupingTypeStatusFromStoredValue decodes m_group.status_enum, returning
// ok=false for values outside the six legal states.
func GroupingTypeStatusFromStoredValue(v int32) (GroupingTypeStatus, bool) {
	s, ok := groupingFromStored[v]
	return s, ok
}

func (s GroupingTypeStatus) IsPending() bool            { return s == GroupingPending }
func (s GroupingTypeStatus) IsActive() bool             { return s == GroupingActive }
func (s GroupingTypeStatus) IsClosed() bool             { return s == GroupingClosed }
func (s GroupingTypeStatus) IsTransferInProgress() bool { return s == GroupingTransferInProgress }
func (s GroupingTypeStatus) IsTransferOnHold() bool     { return s == GroupingTransferOnHold }
func (s GroupingTypeStatus) IsUnderTransfer() bool {
	return s.IsTransferInProgress() || s.IsTransferOnHold()
}

func init() {
	for s, v := range groupingStoredValue {
		if _, dup := groupingFromStored[v]; dup {
			panic(fmt.Sprintf("parties: grouping status encode table is not injective at %d", v))
		}
		groupingFromStored[v] = s
	}
}

// GroupLevel is m_group_level — the catalogue entry naming a hierarchy level
// (Center, Group, ...) and its capabilities [VERIFIED: GroupLevel.java:14-81].
type GroupLevel struct {
	ID             int64
	ParentID       int64
	SuperParent    bool
	LevelName      string
	Recursable     bool
	CanHaveClients bool
}

// NewGroupLevel constructs a level with the capabilities explicit.
func NewGroupLevel(id, parentID int64, superParent bool, levelName string, recursable, canHaveClients bool) GroupLevel {
	return GroupLevel{
		ID: id, ParentID: parentID, SuperParent: superParent,
		LevelName: levelName, Recursable: recursable, CanHaveClients: canHaveClients,
	}
}

// IsCenter ports GroupLevel.isCenter: level name is "Center" (case-insensitive)
// [VERIFIED: GroupLevel.java:73-75].
func (l GroupLevel) IsCenter() bool { return strings.EqualFold(l.LevelName, "Center") }

// IsGroup ports GroupLevel.isGroup: level name is "Group" (case-insensitive)
// [VERIFIED: GroupLevel.java:77-79].
func (l GroupLevel) IsGroup() bool { return strings.EqualFold(l.LevelName, "Group") }

// IsIdentifiedByParentID ports GroupLevel.isIdentifiedByParentId
// [VERIFIED: GroupLevel.java:69-71].
func (l GroupLevel) IsIdentifiedByParentID(parentLevelID int64) bool {
	return l.ParentID == parentLevelID
}

// Group is the Go port of Fineract's Group aggregate [VERIFIED: Group.java:57-112],
// the m_group row. It covers a center and its child groups uniformly: a group
// whose GroupLevel.IsCenter() is true is a center.
type Group struct {
	ID              int64
	ExternalID      string
	Status          GroupingTypeStatus
	ActivationDate  time.Time
	OfficeID        int64
	StaffID         int64
	ParentID        int64
	Level           GroupLevel
	Name            string
	Hierarchy       string
	ClosureReasonID int64
	ClosureDate     time.Time
	SubmittedOnDate time.Time
	AccountNumber   string
}

// NewGroup ports Group.newGroup: a group defaults to PENDING unless active is
// requested, in which case it is ACTIVE with an activation date
// [VERIFIED: Group.java:121-134].
func NewGroup(officeID int64, parentID int64, level GroupLevel, name, externalID string, active bool, activationDate time.Time) Group {
	g := Group{
		OfficeID:   officeID,
		ParentID:   parentID,
		Level:      level,
		Name:       strings.TrimSpace(name),
		ExternalID: strings.TrimSpace(externalID),
		Status:     GroupingPending,
	}
	if active {
		g.Status = GroupingActive
		g.ActivationDate = activationDate
	}
	return g
}

func (g *Group) IsActive() bool     { return g.Status.IsActive() }
func (g *Group) IsPending() bool    { return g.Status.IsPending() }
func (g *Group) IsClosed() bool     { return g.Status.IsClosed() }
func (g *Group) IsNotActive() bool  { return !g.Status.IsActive() }
func (g *Group) IsNotPending() bool { return !g.Status.IsPending() }

// IsCenter reports whether this group's level is a center.
func (g *Group) IsCenter() bool { return g.Level.IsCenter() }
