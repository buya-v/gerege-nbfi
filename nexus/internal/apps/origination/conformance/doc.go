// Package conformance is the origination context's golden-vector schema,
// comparator and grade machinery. It follows the collateral harness (the
// smallest existing harness) and is a separate schema on purpose.
//
// # What this harness grades
//
// The origination slice owns the LoanOriginatorStatus vocabulary. It is a STRING
// enum: Fineract persists the enum NAME itself (ACTIVE/PENDING/INACTIVE), there
// is no integer ordinal column. A wrong name→string mapping (e.g. PENDING
// stored as ACTIVE) silently corrupts every originator written, with no crash.
// That is the same class of silent defect as the HALF_UP/HALF_EVEN ordinal, so
// the name→string mapping is worth pinning.
//
// The one graded seam is "origination-loan-originator-status": given a status
// NAME, the port returns the string value it stores. The truth comes from GET
// /loan-originators/template statusOptions on the running reference oracle,
// with the authoritative mapping declared in LoanOriginatorStatus.java.
//
// # Money representation
//
// There is none. This context carries no money token, no minor-unit parsing and
// no rounding logic. The only graded cell is the stored status string.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/origination/ and
// does not touch a database. It needs a store pin (PIN-origination.json) and a
// capability registry (capabilities-origination.json). With no vectors it
// REFUSES (exit 2). It reuses the shared no-float census, which scans the whole
// Go module.
package conformance
