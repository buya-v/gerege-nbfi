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
// oracle exposes exactly one rounding surface through its savings interest
// posting, two account-status stored values through its lifecycle command
// acknowledgements, and the money arithmetic of a deposit and of the posted
// interest through its account read-backs:
//
//   - seam "savings-daily-interest": the single-period daily-balance interest of
//     the discriminating savings account SEED-Savings-Product-Daily. 1000 MNT
//     at 0.1825 %/yr over a 365-day year gives 0.005 MNT of raw daily interest
//     (half a minor unit), which ties HALF_UP (0.01) against HALF_EVEN (0.00);
//     the oracle posted 0.01 (capture savings-account-daily-raw.json,
//     transaction id 5, amount 0.010000). This harness ports ONLY that single
//     cell — balance x rate x days / (100 x days_in_year) — never the whole
//     accrual/compounding/posting engine.
//   - seam "savings-account-status": the m_savings_account.status_enum stored
//     value the oracle's lifecycle command acknowledgements wrote back on the
//     same account. The oracle executed two lifecycle steps and each ack carries
//     the resulting status id: approve wrote 200 (code
//     savingsAccountStatusType.approved, capture savings-daily-approve-raw.json)
//     and activate wrote 300 (code savingsAccountStatusType.active, capture
//     savings-daily-activate-raw.json). The status enum is NOT the Go
//     declaration ordinal — ACTIVE is 300, not 2 — so each ack pins one
//     stored-value ordinal a port can silently corrupt. Only the two observed
//     steps are graded; no unobserved transition is extrapolated.
//   - seam "savings-deposit": what the observed DEPOSIT posting does to the
//     posted balance. The account read-backs record the opening 1000.00 MNT
//     deposit of each captured account (the account's first row, against a zero
//     opening balance) and the running balance straight after it, 1000.00. A
//     deposit that is not credited, that is debited, or that is folded from a
//     nonzero opening balance goes red.
//   - seam "savings-transactions": the running-balance fold over the captured
//     append-only streams — what a deposit and the posted interest do to the
//     posted balance row by row. The daily account's stream (deposit 1000.00,
//     then an interest posting of 0.01) pins running balances 1000.00 then
//     1000.01; the monthly account's stream (deposit 1000.00, then interest
//     postings of 0.15 and 0.16) pins 1000.00, 1000.15 then 1000.31. This
//     grades the deposit credit, the credit-and-accumulation of each interest
//     posting, and the row count of the fold — NOT the calculation behind the
//     posted amounts (below).
//
// # What this harness cannot grade
//
// The INTEREST CALCULATION behind the monthly-posting account's postings
// (SEED-Savings-Product, product id 1) is NOT graded: the two postings (0.15
// over 30 days, 0.16 over 31 days) are read back from
// savings-account-monthly-raw.json, but the day counts that produced them are
// not single transcribed fields of the capture — they are derived from the
// MANIFEST's prose — and promotion transcribes, never computes. Neither posting
// is a discriminating rounding surface (0.155 rounds to 0.16 under HALF_UP and
// HALF_EVEN alike). The monthly account's OBSERVED amounts and running balances
// are graded as a fold (savings-transactions seam); the interest-period posting
// cadence, compounding and the total-interest-earned derivation are OUTSIDE this
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
