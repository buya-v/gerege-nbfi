// Package conformance is the collateral context's golden-vector schema,
// comparator and grade machinery. It follows the provisioning harness (the
// third-generation harness) rather than the first-generation ledger/loanschedule
// harnesses, and it is a separate schema on purpose rather than a widening of
// any of them.
//
// # What this harness grades
//
// The collateral slice owns the four collateral aggregates and the pure
// valuation arithmetic (ClientCollateral.Total, ClientCollateral.TotalCollateral)
// that links a client's pledged collateral to a loan. The m_collateral_management
// product row and the m_loan_collateral row are read back verbatim, and the
// SINGLE-row client-collateral read-back
// (GET /clients/{clientId}/collaterals/{collateralId}) computes and returns the
// valuation: total = base_price * quantity and totalCollateral = total *
// (pct_to_base/100) on the read path
// (ClientCollateralManagementReadServiceImpl.getClientCollateralManagementData,
// javap-verified). The valuation arithmetic IS in the graded domain; a capture
// that records that computed read-back is transcribed, never guessed.
//
// What is observable and transcribed is the read of the aggregates the captures
// recorded:
//
//   - seam "collateral-product-read": the m_collateral_management row returned
//     by the product read-back (id, name, quality, base_price, unit_type,
//     pct_to_base, currency);
//   - seam "collateral-link-read": the m_loan_collateral row returned by the
//     loan-collateral read-back (id, type_cv_id). The classic loan-collateral
//     row stores only a LoanCollateral code value; value and description are
//     null and there is no quantity, which is exactly why the seam has no
//     rounding surface;
//   - seam "collateral-client-read": the client-collateral read-back, which the
//     oracle returned as an EMPTY content page for client 5 (content []) even
//     though its own write path stored holding id 2 under
//     m_client_collateral_management. The graded cell is page presence: a
//     conformant read reproduces the EMPTY page, so a read that answers the
//     client from the table the write populated fabricates a row the oracle
//     never returned;
//   - seam "collateral-valuation-read": the SINGLE-row client-collateral
//     read-back (client-collateral-single-raw.json, GET /clients/5/collaterals/2),
//     which the oracle returned WITH a computed valuation (total and
//     totalCollateral as JSON numbers, no stored column). The graded cells are
//     id, quantity and the two COMPUTED valuation fields total and
//     total_collateral, all scale-5 integer counts, so a port whose valuation
//     arithmetic differs from the oracle's read path goes red even when the
//     stored quantity matches.
//
// # Money representation
//
// Collateral money is scale-5 fixed-point (DECIMAL(19,5)/DECIMAL(20,5)), NOT
// minor units: base_price and pct_to_base are transcribed as integer strings of
// the scaled count, exactly as the port's ScaledInt represents them. No
// floating-point type appears on any money path here or in the package it grades.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/collateral/ and
// does not touch a database. It needs a store pin (PIN-collateral.json) and a
// capability registry (capabilities-collateral.json). With no vectors it
// REFUSES (exit 2) rather than reporting a vacuous pass. It reuses the shared
// no-float census, which scans the whole Go module.
package conformance
