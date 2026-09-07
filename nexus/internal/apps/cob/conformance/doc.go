// Package conformance is the cob context's golden-vector schema, comparator
// and grade machinery. It follows the collateral harness (the smallest existing
// harness) and is a separate schema on purpose.
//
// # What this harness grades
//
// The cob slice owns the Close-of-Business business-step ORDER for the loan COB
// job: the m_batch_business_steps rows are persisted by ordinal (step_order),
// and a wrong ordinal silently reorders the pipeline — charges before
// delinquency, accrual before arrears aging — with no crash. That is the same
// class of defect as the HALF_UP/HALF_EVEN rounding ordinal, so the order is
// worth pinning.
//
// The one graded seam is "cob-business-step-order": given a business-step name,
// the port returns that step's order (1..6) in the LOAN_CLOSE_OF_BUSINESS job.
// The truth comes from GET /jobs/LOAN_CLOSE_OF_BUSINESS/steps on the running
// reference oracle, corroborated by a read-only read-back of
// m_batch_business_steps.step_order.
//
// # Money representation
//
// There is none. This context carries no money token, no minor-unit parsing and
// no rounding logic. The only graded integer is the business-step order.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/cob/ and does
// not touch a database. It needs a store pin (PIN-cob.json) and a capability
// registry (capabilities-cob.json). With no vectors it REFUSES (exit 2). It
// reuses the shared no-float census, which scans the whole Go module.
package conformance
