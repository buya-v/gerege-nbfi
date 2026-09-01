// Package loanproduct is the Go port of Apache Fineract's loan-product
// configuration surface: the interest/amortization/repayment-frequency enums
// and the LoanProductRelatedDetail value object that carries them into a loan.
//
// # What this package is, and is not
//
// It is the CONFIGURATION MODEL. It owns the stored-value <-> enum tables and
// the loan-product related-detail aggregate the loan scheduler and the loan
// account read. It is NOT the schedule generator: that already exists, fully
// graded, in nexus/internal/apps/loanschedule (DEC-1), and this package is
// deliberately thin where the generator is already authoritative — it declares
// the enums the generator consumes, and nothing here recomputes an EMI.
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb. Every behavioural claim
// carries a file:line citation to that tree; claims that do not carry an
// UNVERIFIED marker. Oracle Database is a prohibited product in this program
// and appears nowhere in this stack; PostgreSQL is the only permitted database.
//
// # One trap this port is built around
//
// TRAP — DaysInYearType and DaysInMonthType do NOT store their ordinal. The
// oracle declares ACTUAL(1), DAYS_360(360), DAYS_364(364), DAYS_365(365) for
// years and ACTUAL(1), DAYS_30(30) for months
// [VERIFIED: DaysInYearType.java:25-29, DaysInMonthType.java:24-26], so the
// stored value and the ordinal agree only for the first member and diverge for
// every member after it. A port that uses a single `iota` constant block for
// either axis is silently wrong on DAYS_360/DAYS_364/DAYS_365/DAYS_30 — the
// most common non-trivial day-count conventions in the whole product surface.
// Both axes therefore carry an explicit StoredValue() table and a separately
// tested FromStoredValue() decoder, exactly as the ledger package does for
// Classification and Usage.
//
// # Deliberately NOT ported
//
// The annual-nominal-rate derivation is not reproduced here. In the oracle the
// per-period rate lives on LoanProductRelatedDetail while the annual rate is
// derived during product assembly and by the progressive schedule model, and
// that arithmetic is already owned and graded by loanschedule under DEC-1.
// This package exposes the per-period rate as the schedule generator expects
// it and adds no second derivation to keep a single source of truth for the
// rate mathematics.
package loanproduct
