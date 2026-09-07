// Package conformance is the savings context's golden-vector schema, comparator
// and grade machinery. It follows the provisioning harness (the third-generation
// harness) rather than the first-generation ledger/loanschedule harnesses, and it
// is a separate schema on purpose rather than a widening of any of them.
//
// # What this harness grades
//
// The savings slice owns the deposit/withdrawal balance arithmetic and the
// interest-period enum vocabulary, but the daily-balance interest ACCRUAL is not
// yet ported into the savings package (summary.go records the postings verbatim
// and the accrual engine is a separate future port). The running reference
// oracle, however, exposes exactly one rounding surface through its savings
// interest posting:
//
//   - seam "savings-daily-interest": the single-period daily-balance interest of
//     the discriminating savings account SEED-Savings-Product-Daily. 1000 MNT
//     at 0.1825 %/yr over a 365-day year gives 0.005 MNT of raw daily interest
//     (half a minor unit), which ties HALF_UP (0.01) against HALF_EVEN (0.00);
//     the oracle posted 0.01 (capture savings-account-daily-raw.json,
//     transaction id 5, amount 0.010000). This harness ports ONLY that single
//     cell — balance x rate x days / (100 x days_in_year) — never the whole
//     accrual/compounding/posting engine.
//
// # What this harness cannot grade
//
// The monthly-posting account (SEED-Savings-Product, product id 1) is captured
// but NOT graded: its two interest postings (0.15 over 30 days, 0.16 over 31
// days) are read back from savings-account-monthly-raw.json, but the day counts
// that produced them are not single transcribed fields of the capture — they are
// derived from the MANIFEST's prose — and promotion transcribes, never computes.
// Neither posting is a discriminating rounding surface (0.155 rounds to 0.16
// under HALF_UP and HALF_EVEN alike). The full interest-period posting cadence,
// compounding and the total-interest-earned derivation are OUTSIDE this
// harness's graded domain.
//
// # Money representation
//
// Savings money is integer MINOR UNITS: balances and interest are transcribed as
// integer strings of the minor-unit count, matching the savings MinorUnits type.
// An interest rate is the savings Percent convention — whole per cent scaled by
// 10^6 (micro-per-cent), so 0.1825 % is 182500. No floating-point type appears
// on any money path here or in the package it grades.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/savings/ and does
// not touch a database. It needs a store pin (PIN-savings.json) and a capability
// registry (capabilities-savings.json). With no vectors it REFUSES (exit 2)
// rather than reporting a vacuous pass. It reuses the shared no-float census,
// which scans the whole Go module.
package conformance
