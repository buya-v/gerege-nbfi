// Package ledger is the Go port of Apache Fineract's slice A2: the GL account
// model, product-to-account mapping resolution, and financial activity
// accounts.
//
// # What this package is, and is not
//
// It is the ACCOUNT MODEL and the RESOLUTION RULE — "given a product, an
// accounting placeholder and (maybe) a payment type or a charge, which single
// GL account does the posting hit?". It is NOT the ledger write path: journal
// entries, reversals and balances belong to slice A1, which reads this package.
//
// Every behavioural claim below is either re-derived from the pinned reference
// oracle (Apache Fineract at /Users/buv/fineract, commit
// 426a23544e8426a38ae43ae404670a0a7e85b9eb) with a file:line citation, or
// graded against captured oracle bytes under .softhouse/capture/tierA-a2/.
// Claims that are neither carry an explicit UNVERIFIED marker.
//
// "The oracle" in this package always means the FINERACT REFERENCE
// IMPLEMENTATION. Oracle Database is a prohibited product in this program and
// appears nowhere in this stack; PostgreSQL is the only permitted database.
//
// # Four measured traps this port is built around
//
// TRAP 1 — PortfolioProductType.fromInt PERMUTES 3/4/5 relative to getValue().
// In the oracle, fromInt follows DECLARATION order while every persistence site
// writes getValue(), and the two disagree in a 3-cycle 3 -> 5 -> 4 -> 3
// [VERIFIED: PortfolioProductType.java:25-31 declares LOAN(1) SAVING(2)
// CLIENT(5) PROVISIONING(3) SHARES(4) WORKING_CAPITAL_LOAN(6); :51-59 switches
// 3->CLIENT, 4->PROVISIONING, 5->SHARES]. A port with ONE integer<->enum map
// used in both directions is silently wrong for PROVISIONING, SHARES and CLIENT
// and silently RIGHT for LOAN, SAVING and WORKING_CAPITAL_LOAN — the worst
// possible distribution, because the products a first test exercises are
// exactly the three that work. See producttype.go: the two directions are two
// separately-tested functions, and the oracle's defective decoder is carried
// under a name that cannot be mistaken for the inverse.
//
// TRAP 2 — CashAccountsForLoan and AccrualAccountsForLoan COLLIDE, and the
// name<->code relation is NOT A FUNCTION IN EITHER DIRECTION across the pair
// [VERIFIED: AccountingConstants.java:37-62 and :95-122, re-read by this
// worker]. Code 22 is CLASSIFICATION_INCOME under cash and
// INCOME_FROM_CAPITALIZATION under accrual; code 24 is INCOME_FROM_DISCOUNT_FEE
// (an INCOME member) under cash and BUY_DOWN_EXPENSE (an EXPENSE member) under
// accrual, so a cross-map at 24 posts to the WRONG SIDE, not merely the wrong
// account; code 25 is FEES_RECEIVABLE under cash and INCOME_FROM_BUY_DOWN under
// accrual, while the NAME FeesReceivable is code 25 under cash and code 8 under
// accrual. Keying on the code cross-maps AND keying on the name cross-maps:
// THERE IS NO SINGLE KEYING THAT IS SAFE. See slots.go — five separate Go
// types, one per (family, accounting rule), each with its own constant space
// and no conversion between them.
//
// TRAP 3 — acc_gl_journal_entry stores NO classification. Its columns are
// office_id, payment_details_id, account_id, currency_code, reversal_id,
// transaction_id, the four *_transaction_id columns, reversed, manual_entry,
// entry_date, type_enum, amount, description, entity_type_enum, entity_id,
// ref_num, submitted_on_date — and account_id is the only route to a
// classification [VERIFIED: JournalEntry.java:38-107, re-read by this worker].
// NOTE THE TRAP INSIDE THE TRAP: type_enum is DEBIT/CREDIT, a DIFFERENT AXIS
// from ASSET/LIABILITY/EQUITY/INCOME/EXPENSE. This package never calls a
// classification field "type" without qualification: it is Classification, and
// the debit/credit axis is EntrySide.
//
// Classification is mutable on the account (GLAccount.update handles
// GLAccountJsonInputParams.TYPE [VERIFIED: GLAccount.java:99-113, TYPE at :108])
// and the update path's only posted-history guard is keyed on USAGE, never on
// TYPE [VERIFIED: GLAccountWritePlatformServiceJpaRepositoryImpl.java:153-159 —
// changesOnly.containsKey(USAGE) && glAccount.isHeaderAccount(); the same
// journal-entries-exist query IS applied on delete at :201-205, so it was
// available and simply not applied to classification]. Fineract does guard the
// operationally visible change (validateForAttachedProduct at :177-187 refuses
// to DISABLE a mapped account) and leaves the semantically destructive one
// open. So a posted entry RETROACTIVELY RE-RENDERS under a retyped account: an
// append-only ledger displaying mutated history. This package therefore offers
// PostedAccountSnapshot (glaccount.go) so that A1 CAN carry the classification
// on the entry. Whether A1 does is A1's diff, not this one.
//
// TRAP 4 — Fineract's money columns are DECIMAL(19,6): SIX decimals against
// MNT's minor unit of 2 [VERIFIED: JournalEntry.java:91
// @Column(name = "amount", scale = 6, precision = 19, nullable = false);
// confirmed at the database in capture A2-150-db-final-state.txt, which reports
// acc_gl_journal_entry.amount as numeric(19,6)]. Fineract can therefore hold
// SUB-MINOR-UNIT RESIDUE in a money column while this project requires integer
// minor units. THE TRUNCATION RULE APPLIED HERE IS: NONE — see money.go. This
// package REFUSES a money text carrying a non-zero digit beyond the currency's
// minor unit, because NO VECTOR PROVES ANY TRUNCATION RULE and inventing one
// would silently move money. The rule is stated, not silent, and the evidence
// for and against it is written out in money.go's doc comment.
//
// # Deliberately NOT ported
//
// m_trial_balance. Its closing_balance is a WRITTEN, STORED, UNSIGNED sum
// wearing a balance's name, populated at INSERT from the unsigned SUM(je.amount)
// projection [VERIFIED: UpdateTrialBalanceDetailsTasklet.java:81 reading
// JournalEntryRepository.java:61]. That is in direct tension with this
// project's non-negotiable "balances are derived, never written". It is a
// reporting cache, it belongs to slice A3, and this package provides no
// balance store of any kind. Balances are derived by A1/A3 from the entries.
package ledger
