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
// /working-capital/near-breach. As of the pinned capture, m_wc_loan is EMPTY:
// every one of those read paths returns an empty list, so there is no loan row
// to transcribe and no breach/delinquency schedule arithmetic to observe. This
// harness therefore ships with ZERO vectors and, like every parity harness on
// this core, REFUSES (exit 2) rather than reporting a pass over zero work. A
// vector is added the moment the seed grows a working-capital loan.
//
// # Money representation
//
// No money cell is gradeable while m_wc_loan is empty. The slice's money cells
// (principal/outstanding in integer minor units, and the HALF_UP rounding the
// breach and delinquency schedule seams surface) are unreachable through the
// read-back this context currently exposes. No floating-point type appears on
// any money path here or in the package it grades.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/workingcapital/
// and does not touch a database. It needs a store pin (PIN-workingcapital.json)
// and a capability registry (capabilities-workingcapital.json). It reuses the
// shared no-float census, which scans the whole Go module.
package conformance
