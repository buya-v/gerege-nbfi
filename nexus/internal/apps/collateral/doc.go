// Package collateral is the Go port of Fineract's collateral-management domain
// (tierB-collateral). It models the four collateral tables and the pure
// valuation arithmetic that links a client's pledged collateral to a loan:
//
//   - CollateralProduct  (m_collateral_management)        — the product catalogue
//     (name, quality, base price, unit type, percentage-to-base, currency);
//   - ClientCollateral   (m_client_collateral_management) — a client's holding
//     quantity of a product;
//   - LoanCollateralLink (m_loan_collateral_management)   — the quantity of a
//     holding tied to one loan, with a released flag and optional transaction;
//   - LoanCollateral     (m_loan_collateral)              — the classic
//     type/value/description collateral attached to a loan.
//
// # money representation
//
// Fineract stores the management-side decimal columns (base_price, pct_to_base,
// quantity) as DECIMAL(19,5)/DECIMAL(20,5) and the classic loan-collateral
// value as DECIMAL(19,6). The port represents every one of these as a ScaledInt:
// an integer count scaled by 10^scale, with the scale carried at the
// encode/decode boundary rather than on the type. The management side uses
// scale 5 (DecimalScale) and the loan-collateral value uses scale 6
// (CollateralValueScale). No floating-point type appears on any money path.
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb. Behavioural claims carry
// file:line citations to that tree.
package collateral
