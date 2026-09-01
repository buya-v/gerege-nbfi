// Package savings is the Go port of Apache Fineract's savings / deposits
// domain: the account status, transaction-type and deposit-type stored-value
// enums, the interest-rate chart model, and the SavingsAccount aggregate with
// its derived summary.
//
// # SHIPS DISABLED — this package must never be switched on without a user gate
//
// This context is ported under the development plan's Tier B activation rule
// [development_plan.md §8 row 1; CLAUDE.md "Deposit-taking ACTIVATION"]:
//
//   - Porting the savings / deposit code is IN SCOPE.
//   - ENABLING deposit-taking behaviour in any live environment is NOT in
//     scope. Activation is a hard `user` gate, because which licensed entity
//     operates a deployment decides the law that applies:
//   - NBFI (ББСБ): accepting deposits or opening deposit accounts is
//     PROHIBITED — Law on Non-Banking Financial Activities Art. 12.1.3 and
//     Art. 12.1.4 (no deposits via cheques, cards or promissory notes).
//     https://legalinfo.mn/mn/detail/103
//   - SCC (ХЗХ): a savings and credit cooperative may take savings from
//     members only, and lend to members only.
//
// The ratified tenant licence is NBFI [CLAUDE.md], so a deployment of this
// package exposes no deposit endpoint. The port therefore ships behind a
// config flag whose default is OFF (config.go), and no code path in this
// package returns a string that describes member savings as insured,
// protected, or guaranteed — SCC deposits are not covered by Mongolian deposit
// insurance, and the "never insured/protected/guaranteed" rule is a rejection
// on sight.
//
// # What this package is, and is not
//
// It is the ACCOUNT MODEL and the stored-value <-> enum tables plus the
// aggregate the write path reads. It is NOT the interest-posting arithmetic,
// the double-entry posting itself, or the persistence layer: those belong to
// later slices of this context and to tierA-gl-accounting (A1). This slice is
// a pure model, deliberately free of a database so it can be graded without
// one, matching the derive-don't-store ruling.
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb. Every behavioural claim
// carries a file:line citation to that tree. "The oracle" here always means
// the FINERACT REFERENCE IMPLEMENTATION; Oracle Database is a prohibited
// product in this program and appears nowhere in this stack.
//
// # One trap this port is built around
//
// TRAP — SavingsAccountStatusType and SavingsAccountTransactionType do NOT
// store their ordinal, and the savings status band is NOT contiguous. The
// status values are INVALID(0), SUBMITTED_AND_PENDING_APPROVAL(100),
// APPROVED(200), ACTIVE(300), TRANSFER_IN_PROGRESS(303), TRANSFER_ON_HOLD(304),
// WITHDRAWN_BY_APPLICANT(400), REJECTED(500), CLOSED(600),
// PRE_MATURE_CLOSURE(700), MATURED(800) [VERIFIED: SavingsAccountStatusType.java:24-35].
// A port that encodes these as an iota would collapse the transfer sub-states
// (303/304) and every band after 300. The transaction types are likewise
// non-contiguous (there is no 9 or 11, and 20/21 are the hold/release pair
// that does not move the account balance) [VERIFIED: SavingsAccountTransactionType.java:24-47].
// Both therefore carry an explicit StoredValue() table and a separately tested
// FromStoredValue() decoder, exactly as the ledger and loan packages do.
package savings
