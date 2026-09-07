// Package conformance is the working-capital context's golden-vector schema,
// comparator and grade machinery. It follows the collateral/investor harnesses
// (a read seam over a transcribed aggregate) rather than the loan/loanschedule
// harnesses, and it is a separate schema on purpose.
//
// # What this harness grades
//
// The working-capital slice owns the m_wc_* tables (m_wc_loan, the
// working-capital loan product, the breach schedule and the delinquency-range
// schedule). The running reference oracle exposes those read paths under
// /working-capital-loans, /working-capital-loan-products and
// /working-capital/near-breach. The graded seam is the loan-list read
// (GET /working-capital-loans): one seeded loan row (id 1, external id
// SEED-WC-L01, status active) transcribed from loans-list-raw.json under tenant
// gerege. The product-list and near-breach reads are captured but carry no
// gradeable cell this harness transcribes, so they do not promote a vector.
//
// # Money representation
//
// The loan-list read grades id, external_id and status — no money cell. The
// working-capital package's own money paths (WorkingCapitalLoanBalance and the
// repayment allocation) operate on loan.MinorUnits as integer minor units and
// only add or subtract; no division, percentage or apportionment appears, so
// the slice has no rounding surface. No floating-point type appears on any
// money path here or in the package it grades.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/workingcapital/
// and does not touch a database. It needs a store pin (PIN-workingcapital.json)
// and a capability registry (capabilities-workingcapital.json). It reuses the
// shared no-float census, which scans the whole Go module.
package conformance
