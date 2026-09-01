package branch

import "time"

// Cashier is the m_cashiers aggregate: a staff member assigned to a teller for
// a date range, with an optional full-day flag or an explicit start/end time.
//
// [VERIFIED: Cashier.java — staff_id, teller_id, description, start_date,
// end_date, full_day, start_time, end_time; unique (staff_id, teller_id).]
type Cashier struct {
	ID          int64
	StaffID     int64
	TellerID    int64
	Description string
	StartDate   time.Time
	EndDate     time.Time
	IsFullDay   bool
	StartTime   string
	EndTime     string
}
