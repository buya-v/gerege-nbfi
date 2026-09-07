// Package conformance is the loanproduct context's golden-vector schema,
// comparator and grade machinery. It follows the parties harness (the
// vocabulary-parity harness) and is a separate schema on purpose rather than a
// widening of any existing one.
//
// # What this harness grades
//
// The loanproduct slice is the loan-product CONFIGURATION model: the
// stored-value <-> code <-> name tables for six enum vocabularies
// (amortization method, interest method, interest-calculation period, period
// frequency, days-in-month and days-in-year) plus the LoanProductRelatedDetail
// value object that carries principal and rate columns verbatim. The running
// reference oracle's loanproducts template read-back enumerates each vocabulary's
// option list with an integer id and an i18n code, so the gradeable, observable
// surface is the DECODE: given the stored id, return the round-trip stored value,
// the code, and the enum name.
//
// The discriminator is not a rounding tie — this surface carries no money it
// rounds (the schedule/EMI arithmetic that consumes these values is owned and
// graded by loanschedule under DEC-1). It is the day-count trap: DaysInYearType
// and DaysInMonthType persist the LITERAL DAY COUNT, not the ordinal
// (DaysInYear360 stores 360, DaysInYear364 stores 364, DaysInYear365 stores 365,
// DaysInMonth30 stores 30). A naive iota port is silently wrong on every
// non-trivial day-count convention, the same class of defect as a wrong enum
// ordinal.
//
// # What this harness cannot grade
//
// The loan schedule, interest/repayment-period arithmetic and every money
// rounding surface the schedule produces live in loanschedule, not here. The
// product's principal (numeric(19,6)) and annual-nominal-rate derivation are
// carried columns with no decode or rounding in this package, so there is no
// minor-unit money cell to pin and no HALF_UP/HALF_EVEN tie; the MANIFEST records
// "roundingSurface": "none".
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/loanproduct/ and
// does not touch a database. It needs a store pin (PIN-loanproduct.json) and a
// capability registry (capabilities-loanproduct.json). With no vectors it
// REFUSES (exit 2) rather than reporting a vacuous pass. It reuses the shared
// no-float census, which scans the whole Go module, so no floating-point type or
// literal may appear here.
package conformance
