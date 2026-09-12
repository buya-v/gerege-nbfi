package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	shared "github.com/gerege/nexus/internal/conformance"
)

// SchemaV1 is the only schema string this package accepts.
const SchemaV1 = "gerege.loan.vector/v1"

// LoanContext is the ONE bounded context this schema's machinery can say anything
// about, and it is the directory name that context's vectors live in.
const LoanContext = "loan"

// SeamLoanRepaymentAllocation is the capture seam this schema grades: the
// four-bucket greedy allocation of a repayment across penalty/fee/interest/
// principal, observed on the SEED-L03 repayment.
const SeamLoanRepaymentAllocation = "loan-repayment-allocation"

// SeamLoanScheduleInterest is the discriminating capture seam: the single-period
// interest of the discriminating loan SEED-L06, whose period-1 interest ties
// HALF_UP against HALF_EVEN.
const SeamLoanScheduleInterest = "loan-schedule-interest"

// SeamLoanDisbursement is the capture seam this schema grades: the net disbursal
// amount of the SEED-L06 disbursal.
const SeamLoanDisbursement = "loan-disbursement"

// SeamLoanStatus is the capture seam this schema grades: the persisted
// loan-status ordinal as the oracle's read-back serialises it. Fineract stores
// loan status in m_loan.loan_status_id with a NON-contiguous value table — the
// active band sits at 300 with transfer sub-states at 303/304 and the closed
// band carries three 6xx values — so a port that encodes the enum as an iota
// silently collapses states. Each vector decodes one observed stored value and
// pins the status_code the read-back emitted for it (plus the round-trip stored
// value), transcribed from a capture whose status.id/code pair is the
// observation.
const SeamLoanStatus = "loan-status"

// SeamLoanTransactionBalance is the capture seam this schema grades: the
// per-transaction outstandingLoanBalance column of the loan read-back, DERIVED
// row by row from the earlier postings by
// LoanBalanceService.updateLoanOutstandingBalances. The balances track
// PRINCIPAL only: a disbursement creates principal, a repayment recognises a
// principal portion, a non-monetary accrual is excluded from the balance
// stream and its row serialises NO balance cell, and an interest waiver
// (which recognises no principal portion) leaves the balance unmoved. A
// capture that observes this column therefore pins the running derivation, the
// null-not-zero absence of a balance cell on an accrual row, and the
// "a waiver does not move the outstanding balance" consequence in one go.
const SeamLoanTransactionBalance = "loan-transaction-balance"

// SeamLoanSummaryOutstanding is the capture seam this schema grades: the loan
// summary's total outstanding, DERIVED from the four outstanding buckets the
// oracle read back. Fineract persists total_outstanding_derived; the port's
// LoanSummary keeps the bucket decomposition and derives the total
// (derive-don't-store). A port that stores the total and reads it back, or sums
// the wrong buckets, returns a total that disagrees with the observed read-back.
const SeamLoanSummaryOutstanding = "loan-summary-outstanding"

// SeamLoanDelinquentDays is the capture seam this schema grades: the
// calendar-day delinquency derivation of a loan read-back. Fineract derives
// overdueDays as the day difference between the summary's overdueSinceDate and
// the business date (DateUtils.getDifferenceInDays == DAYS.between), and
// delinquentDays as overdueDays minus paused and grace days, floored at zero
// [delinquency.go:96,109]. The committed loan details pin both the overdue
// dates and the resulting counts at the business date 2026-09-01, so the seam
// is gradeable with no capture. The request carries the observed overdue-since
// date (ABSENT on a loan the read-back shows no overdue date for) and the
// business date, plus the paused-day count of any active delinquency pause and
// the product's graceOnArrearsAgeing; the expectation transcribes the observed
// pastDueDays / delinquentDays. A port that approximates a month as 30 days,
// that errors on an absent overdue date instead of returning zero, or that
// counts the days inside a pause as delinquent, disagrees with the read-back.
const SeamLoanDelinquentDays = "loan-delinquent-days"

// SeamLoanJournalEntryBatchBalance is the capture seam this schema grades: the
// debit and credit totals of a loan-produced journal-entry BATCH read back from
// the journal-entries endpoint. A loan disbursement GENERATES its postings, so
// the observation is a read-back, not a posting command; the batch carries more
// than one pair when a disbursement pair and a fee pair share one loan. The
// property is TWO things at once, and the second is invisible to the first:
//
//   - sum(debits) == sum(credits), exactly, in integer minor units, summed
//     independently over EVERY leg: a port that sums only the first pair, drops
//     a pair, or nets the two legs on one account produces totals that a
//     single-pair batch cannot tell apart; and
//   - WHICH account takes WHICH side in WHICH transaction
//     (expect.journal_entry_account_sides). A port that swaps the two legs of a
//     balanced pair moves equal amounts between the sides, so the totals are
//     UNCHANGED and the batch still balances while the posting is reversed. The
//     per-(transaction, account) side list is the cell that moves.
//
// The property is per-(transaction, account), not per-account globally:
// OHLGR-Fund-Source is CREDIT in the disbursement transaction L17 and DEBIT in
// the fee transaction L18.
const SeamLoanJournalEntryBatchBalance = "loan-journal-entry-batch-balance"

// SeamLoanScheduleAmortization is the capture seam this schema grades: the
// WHOLE-schedule principal amortization of a loan read-back, the property
// "principal amortizes to zero" asserted over every repayment period at once.
// No existing seam grades it: LN-L06 grades ONE period's INTEREST, and the
// loanschedule context's vectors grade the schedule GENERATOR at a different
// seam (they do not read a loan back). The request carries the disbursed
// principal and the observed per-period principalDue components raised to
// integer minor units; the expectation is the sum of every component and the
// final outstanding principal balance. The property holds exactly when the sum
// equals the disbursed principal and the final balance is zero. A port that
// truncates a per-period principal, drops the final adjustment row, or
// reconstructs a uniform per-period component leaves a residue and goes red.
// A port that places the remainder in the wrong PERIOD preserves both the sum
// and the final balance, so this seam does NOT grade placement; no committed
// capture exposes per-period placement on a loan read-back.
const SeamLoanScheduleAmortization = "loan-schedule-amortization"

// SeamLoanWriteOffFourBucket is the capture seam this schema grades: the
// four-bucket discharge a write-off posts. WriteOffOutstanding
// [writeoff.go:36] reads the per-instalment outstanding of every instalment
// whose obligations are NOT met and sums each of the four buckets
// (principal/interest/fee/penalty) across the schedule; the four returned
// buckets are the write-off transaction's portions, and they sum to its
// amount. The request carries the observed per-instalment schedule reduced to
// the four outstanding cells plus the obligationsMet flag; the expectation is
// the four portions the oracle wrote onto the write-off transaction and their
// total. A port that writes off only principal (or principal and interest),
// drops the fee or the penalty bucket, or swaps fee and penalty moves at least
// one portion. On the pinned loan-11 observation fee (10000) and penalty
// (5700) are both non-zero and DIFFERENT, so a swap cannot hide. The
// obligationsMet skip is NOT graded here: loan 11 has no instalment with
// obligations met, so a port that forgets the skip sums the same numbers and a
// drive for it would kill zero. A capture would need a loan with at least one
// fully-paid instalment, then written off.
const SeamLoanWriteOffFourBucket = "loan-writeoff-four-bucket"

// SeamLoanTransactionReversal is the capture seam this schema grades: the
// journal-entry side of the FIRST observed loan-transaction reversal. When the
// loan write-off reversed the loan's last accrual (transaction L46, the
// 2026-09-02 interest accrual on loan 11), Fineract ADDED one counter-leg per
// original leg with the same transaction id, account, amount and transaction
// date but the OPPOSITE side, and changed no original:
//
//	JournalEntryWritePlatformServiceJpaRepositoryImpl
//	  .createJournalEntryForReversedLoanTransaction (:359-378)
//
// The manual reversal path is DIFFERENT and must not be ported here
// (revertJournalEntry, :380-429): it posts its counter-entries on a FRESH
// generated transaction id and flags each original reversed = true, as the
// committed tierA-a2 observation shows (originals 45/46/47 flagged,
// counter-entries 50/51/52 on a fresh id). A porter who has read that path
// first will write the wrong loan reversal, which is exactly why this seam
// carries its own vector.
//
// request = the before-read-back legs of ONE loan transaction plus the reversed
// transaction's transaction date; expect = the full after-read-back leg list
// (the originals as they were, then the counter-legs), every leg graded on its
// transaction id, account, side, amount, transaction date and reversed flag. A
// port that DUPLICATES instead of reverses (same side), FLAGS and rewrites the
// originals, posts on a FRESH transaction id, or dates the counter-legs at the
// business date moves at least one graded cell, and the side cells see the
// duplication that the batch totals (both still 1156) cannot.
const SeamLoanTransactionReversal = "loan-transaction-reversal"

// SeamLoanWriteOffJournalEntries is the capture seam this schema grades: the
// five-leg journal entry the loan write-off ITSELF posts, the other half of the
// observation the writeoff-four-bucket seam grades. It ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForLoanWriteOffs
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1872-1976, pinned
// commit 426a23544]. For each of the five portion slots (principal, interest,
// fees, penalties, overpayment) whose portion is > 0 the processor adds the
// portion to a total and credits the slot's mapped GL account, MERGING portions
// that resolve to the SAME account (accountMap); it then posts ONE debit of the
// total to the losses-written-off account (or the write-off-reason mapping when
// one is set). The request carries the observed four portions and the product's
// slot->account mapping; the expectation is the ordered leg list the write-off
// posted. On the pinned loan-11 observation transaction L54 posts four credits
// (Loan-Portfolio 10000000, Interest-Receivable 661853, Fees-Receivable 10000,
// Penalties-Receivable 5700) then ONE debit (Losses-Written-Off 10677553), the
// credits summing to the debit exactly.
//
// WHAT THIS SEAM DOES NOT GRADE. The same-account MERGE is invisible here:
// product 3 maps the four credit slots to four DIFFERENT accounts, so a port
// that never merges posts the same five legs, and a drive for the merge would
// kill ZERO. Grading it needs a product that maps two portion slots to one
// account (e.g. fees and penalties receivable sharing an account). The
// zero-portion skip is likewise invisible: every portion on loan 11 is > 0, so
// a port that never skips a zero posts the same five legs; grading it needs a
// write-off with an all-zero slot. Overpayment and the write-off-reason mapping
// are absent from the observation (the request's overpayment slot is zero and
// the product carries no reason mapping), and the charged-off branch
// [AccrualBasedAccountingProcessorForLoan.java:1616] is not reached because
// loan 11 was not charged off.
const SeamLoanWriteOffJournalEntries = "loan-writeoff-journal-entries"

// SeamLoanChargeOffJournalEntries is the capture seam this schema grades: the
// journal entry a loan CHARGE-OFF itself posts in the branch with NO
// charge-off reason, the charged-off sibling of the write-off-journal seam. It
// ports AccrualBasedAccountingProcessorForLoan.createJournalEntriesForChargeOff
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:890-975, pinned commit
// 426a23544]. For each of the four portion slots (principal, interest, fees,
// penalties) whose portion is > 0 the processor credits the slot's receivable/
// portfolio account and debits an expense/income account (the FRAUD expense
// account for the principal when the loan is marked fraud, the ordinary
// charge-off expense account otherwise), MERGING portions that resolve to the
// SAME account on each side (accountMap); it then posts every credit in
// insertion order, followed by every debit in insertion order. The
// charge-off-REASON branch is NOT observed: the port REFUSES a reason mapping
// rather than guessing it.
//
// On the pinned observations transaction L19 (loan 7, non-fraud) posts two
// credits (portfolio 100000, interest/fee/penalty receivable MERGED to 14300)
// then three debits (charge-off expense 100000, charge-off interest 3000,
// charge-off fee+penalty MERGED to 11300); L44 (loan 15, fraud, same portions)
// moves the principal debit to the FRAUD expense account; L11 (loan 4) carries
// a penalty portion alone.
const SeamLoanChargeOffJournalEntries = "loan-chargeoff-journal-entries"

// SeamLoanChargedOffWriteOffJournalEntries is the capture seam this schema
// grades: the journal entry a WRITE-OFF posts on a loan that is ALREADY MARKED
// CHARGED OFF, the charged-off sibling of the write-off-journal seam. It ports
// AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForWriteOffsWhenLoanIsChargedOff [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1616-1694, pinned commit
// 426a23544]. For each of the five portion slots (principal, interest, fees,
// penalties, overpayment) whose portion is > 0 the processor CREDITS the
// charge-off expense/income account the earlier charge-off debited — the FRAUD
// expense account for the principal when the loan is marked fraud, the ordinary
// charge-off expense account otherwise — MERGING portions that resolve to the
// SAME account (accountMap is a LinkedHashMap); it then posts the credits in
// insertion order followed by ONE debit of the total to LOSSES_WRITTEN_OFF. The
// FUND_SOURCE debits populateCreditDebitMaps accumulates are NEVER posted: only
// the credit map is iterated.
//
// On the pinned observations transaction L16 (loan 4, non-fraud) credits the
// charge-off expense 100000, the charge-off interest account 3000 and the
// fee+penalty account 11300, then debits losses-written-off 114300; L37 (loan 9,
// fraud) credits the fraud expense 75000 and debits 75000; L27 (loan 7)
// credits 8357 and 147 then debits 8504. The account ids are THIS replay's
// product mappings, not an earlier replay's.
const SeamLoanChargedOffWriteOffJournalEntries = "loan-chargedoff-writeoff-journal-entries"

// SeamLoanRepaymentJournalEntries is the capture seam this schema grades: the
// journal entry an ORDINARY repayment posts on a loan that is NOT charged off.
// It ports AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForLoanRepayments [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1695-1871, pinned commit
// 426a23544]. For each of the five portion slots (principal, interest, fees,
// penalties, overpayment) whose portion is > 0 the processor CREDITS the slot's
// mapped account — LOAN_PORTFOLIO, INTEREST_RECEIVABLE, FEES_RECEIVABLE,
// PENALTIES_RECEIVABLE and OVERPAYMENT respectively — MERGING portions that
// resolve to the SAME account (accountMap is a LinkedHashMap) into one credit at
// the first slot's position; it then posts ONE debit of the total to the
// RESOLVED fund source (the transaction paymentTypeId's payment-channel account
// when the product maps that channel, else the product's FUND_SOURCE). The
// credits come first and the debit is last.
//
// On the pinned observations transaction L66 (loan 14) credits the loan
// portfolio 250 and debits fund-source 4 250; L93 (loan 18) credits 250 and the
// fee receivable 20 then debits 270; L98 (loan 19) credits 250 and the
// overpayment account 250 then debits 500. All three loans are product 6 (LP1)
// and are NOT charged off. The account ids are THIS replay's product mapping,
// and the only channel mapping is paymentTypeId 1 -> 17, so the observed
// paymentType 11 (AUTOPAY) resolves to the product fund source 4.
const SeamLoanRepaymentJournalEntries = "loan-repayment-journal-entries"

// SeamLoanGoodwillCreditJournalEntries is the capture seam this schema grades:
// the journal entry a GOODWILL CREDIT posts on a loan that is NOT charged off,
// the goodwill-credit branch of
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForLoanRepayments
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1695-1871, pinned
// commit 426a23544]. The CREDIT side is an ordinary repayment's: for each of the
// five portion slots (principal, interest, fees, penalties, overpayment) whose
// portion is > 0 the processor CREDITS the slot's mapped account — LOAN_PORTFOLIO,
// INTEREST_RECEIVABLE, FEES_RECEIVABLE, PENALTIES_RECEIVABLE and OVERPAYMENT
// respectively — MERGING portions that resolve to the SAME account into one
// credit at the first slot's position. The DEBIT side is the goodwill arm's own
// table, posted AFTER every credit in insertion order: principal and overpayment
// debit GOODWILL_CREDIT, interest debits INCOME_FROM_GOODWILL_CREDIT_INTEREST,
// fees debit INCOME_FROM_GOODWILL_CREDIT_FEES and penalties debit
// INCOME_FROM_GOODWILL_CREDIT_PENALTY, merging debits that resolve to the same
// account. It is NOT a transfer: no fund source is posted.
//
// On the pinned observations L444 (loan 42) posts a 10.00 principal credit to
// account 6 and a 10.00 goodwill debit to account 20; L466 (loan 46) posts a
// 500.00 overpayment credit to account 13 and a 500.00 goodwill debit to account
// 20; L267 (loan 26) posts a 15.00 penalty credit to account 7 and a 15.00
// income-from-goodwill-credit-penalty debit to account 12. None of the three
// loans is charged off. The account ids DIFFER per capture — loans 42 and 46 are
// the chargeoff-p3-mnt replay and loan 26 is the accrual-activity-p1-mnt replay —
// so each vector carries its own product mapping. The charged-off goodwill arm
// is a different method and is not observed here; the port refuses a charged-off
// loan.
const SeamLoanGoodwillCreditJournalEntries = "loan-goodwill-credit-journal-entries"

// SeamLoanDisbursementJournalEntries is the capture seam this schema grades: the
// journal entry a loan DISBURSEMENT posts, the disbursement branch of
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForDisbursements
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1309-1345, pinned
// commit 426a23544]. It is the ONLY property this seam ports: the principal
// portion is amount MINUS overpayment — NOT the read-back transaction's
// principalPortion field, which every observed disbursement carries as 0. The
// principal portion DEBITs LOAN_PORTFOLIO when > 0, the overpayment portion
// DEBITs OVERPAYMENT when > 0, then the whole amount CREDITs the RESOLVED fund
// source once. The debits come first, in that order, and the credit last.
//
// The fund source is RESOLVED: a payment type with a payment-channel mapping
// uses that channel's account, otherwise the product's FUND_SOURCE. Every
// observed disbursement's payment type has NO channel mapping — each observed
// product maps only paymentType 1 — so each resolves to the product's
// fundSourceAccountId; the seam carries the resolved account, never resolving it
// itself.
//
// It is NOT a transfer. A loan-to-loan transfer (ASSET_TRANSFER) and an account
// transfer (LIABILITY_TRANSFER) are the processor's other branches and are NOT
// observed; the port takes no transfer flag, so the seam cannot express them.
// Every observed disbursement is unreversed and has overpayment 0; an
// overpayment portion > 0 is ported as the processor has it but is unobserved.
//
// The account ids DIFFER per capture: loan 16 is the merchant-refund-mnt replay,
// loan 20 the emi-calculation-p2-mnt replay and loan 1 the repayment-p1-mnt
// replay, so each vector carries its own product mapping and no account id is
// shared across them.
const SeamLoanDisbursementJournalEntries = "loan-disbursement-journal-entries"

// SeamLoanChargeAdjustmentJournalEntries is the capture seam this schema grades:
// the journal entry a CHARGE ADJUSTMENT posts on a loan. It ports
// AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForLoanChargeAdjustment and
// .createJournalEntriesForChargeOffLoanChargeAdjustment [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:997-1214, pinned commit
// 426a23544]. The credit side depends on the loan's charged-off state: NOT
// charged off, principal credits LOAN_PORTFOLIO, interest INTEREST_RECEIVABLE,
// fees FEES_RECEIVABLE, penalties PENALTIES_RECEIVABLE and overpayment
// OVERPAYMENT; charged off, principal, interest and fees all credit
// INCOME_FROM_CHARGE_OFF_FEES, penalties credit
// INCOME_FROM_CHARGE_OFF_PENALTY and overpayment credits OVERPAYMENT. Portions
// that resolve to the SAME account MERGE into one credit at the first slot's
// position (the processor's accountMap is a LinkedHashMap). It then posts
// exactly ONE DEBIT of the total, after every credit: INCOME_FROM_PENALTIES when
// the adjusted charge is a penalty, else INCOME_FROM_FEES.
//
// The Java resolves that debit account through
// AccountingProcessorHelper.createDebitJournalEntryForLoanCharges, which can
// honour a CHARGE-SPECIFIC override; this seam takes the PRODUCT accounts only
// and carries no charge id, so that override is REFUSED.
//
// Honest limit: in every observed product INCOME_FROM_FEES and
// INCOME_FROM_PENALTIES map to the SAME GL account (3 in charges-progressive-mnt,
// 9 in charges-cumulative-mnt), so these observations cannot discriminate the
// fee-vs-penalty debit choice. The port posts it as the Java has it; the vectors
// grade the credits, the merge and the single-debit total, not that choice.
//
// On the pinned observations L239 (loan 41, NOT charged off, product LP1)
// credits the portfolio 8 10.00 and debits the income 3 10.00; L213 (loan 36,
// NOT charged off, penalty charge) credits the penalty receivable 9 20.00 and
// debits 3 20.00; L232 (loan 40, CHARGED OFF) credits the charge-off fees 12
// 5.00 and debits 3 5.00; L38 (loan 7, NOT charged off) credits the portfolio 2
// 1.00 and the penalty receivable 7 2.00, then ONE debit 9 3.00. Account ids
// are THIS replay's product mapping.
const SeamLoanChargeAdjustmentJournalEntries = "loan-charge-adjustment-journal-entries"

// SeamLoanChargedOffRepaymentJournalEntries is the capture seam this schema
// grades: the journal entry a REPAYMENT posts on a loan ALREADY MARKED CHARGED
// OFF. It ports AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForRepaymentWhenLoanIsChargedOff [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1388-1615, dispatch :1369-1377,
// pinned commit 426a23544]. For every positive portion slot — principal,
// interest, fees, penalties — the processor CREDITS INCOME_FROM_RECOVERY,
// whatever the loan's fraud flag (this branch never reads it); a positive
// overpayment portion credits OVERPAYMENT. Portions that resolve to the SAME
// account MERGE into one credit at the first slot's position (creditBalances is
// a LinkedHashMap). It then posts ONE debit of the total to the RESOLVED fund
// source (the transaction paymentTypeId's payment-channel account when the
// product maps that channel, else the product FUND_SOURCE): every portion debits
// that same account, so the debit map merges them too. Credits come first, the
// single debit last.
//
// The method's merchant-issued-refund, payout-refund, goodwill-credit and else
// branches are NOT observed on a charged-off loan and are not expressible here:
// the port takes a REPAYMENT only, with no transaction-type parameter.
//
// On the pinned observations transaction L61 (loan 19, FRAUD, product
// LP1_INTEREST_FLAT) merges its 633 principal and 10 interest into ONE credit
// of 643 to the recovery account 17, then debits the fund source 1 643; L125
// (loan 37, product LP1) credits the recovery account 17 500 and debits the fund
// source 1 500. The account ids are THIS replay's product mapping: the only
// channel mapping is paymentTypeId 1 -> 18, so the observed paymentType 5
// resolves to the product fund source 1.
const SeamLoanChargedOffRepaymentJournalEntries = "loan-chargedoff-repayment-journal-entries"

// SeamLoanChargedOffMerchantRefundJournalEntries is the capture seam this schema
// grades: the journal entry a MERCHANT-ISSUED REFUND posts on a loan ALREADY
// MARKED CHARGED OFF and NOT fraud. It ports
// AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForRepaymentWhenLoanIsChargedOff [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1388-1615, dispatch :1369-1377,
// pinned commit 426a23544]. The merchant-issued-refund arm CREDITS the
// charge-off slots the earlier charge-off DEBITED: principal to
// CHARGE_OFF_EXPENSE, interest to INCOME_FROM_CHARGE_OFF_INTEREST, fees to
// INCOME_FROM_CHARGE_OFF_FEES, penalties to INCOME_FROM_CHARGE_OFF_PENALTY, and
// overpayment to OVERPAYMENT. Portions that resolve to the SAME account MERGE
// into one credit at the first slot's position. It then posts ONE debit of the
// total to the RESOLVED fund source (the transaction paymentTypeId's
// payment-channel account when the product maps that channel, else the product
// FUND_SOURCE): every portion debits that same account, so the debit map merges
// them too. Credits come first, the single debit last.
//
// The method's FRAUD split (principal to CHARGE_OFF_FRAUD_EXPENSE), its
// payout-refund and goodwill-credit arms and its else branch are NOT observed on
// a charged-off loan and are not expressible here: the port REFUSES a fraud loan
// rather than guessing the split.
//
// On the pinned observations transaction L475 (loan 48, product
// LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_FULL) credits
// the charge-off expense 18 800, the charge-off interest 16 18.49 and the
// overpayment 13 81.51, then debits the fund source 7 900; L477 (same loan)
// credits 18 883.10 and 16 16.90 then debits 7 900; L498 (loan 50, product
// LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ACCELERATE_MATURITY_CHARGE_OFF)
// credits 18 900 then debits 7 900. The account ids are THIS replay's product
// mapping, both products mapping fundSource 7, chargeOffExpense 18,
// incomeFromChargeOffInterest 16, incomeFromChargeOffFees 12,
// incomeFromChargeOffPenalty 12 and overpayment 13; the only channel mapping is
// paymentTypeId 1 -> 19, so the observed paymentType 4 (AUTOPAY) resolves to the
// product fund source 7.
const SeamLoanChargedOffMerchantRefundJournalEntries = "loan-chargedoff-merchant-refund-journal-entries"

// SeamLoanAccrualJournalEntries is the capture seam this schema grades: the
// journal entry an ACCRUAL or ACCRUAL_ADJUSTMENT transaction posts, the
// tax-free observed shape of AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForAccruals [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:2015-2087, dispatch :79-81,
// pinned commit 426a23544]. The interest group posts first when interest > 0:
// an accrual DEBITs INTEREST_RECEIVABLE then CREDITs INTEREST_ON_LOANS, an
// adjustment posts the same pair with the accounts swapped. Then, each only
// when its portion > 0, the fee group and the penalty group post through
// helper.createJournalEntriesForLoanCharges [AccountingProcessorHelper.java:
// 393-435], which CREDITs first and DEBITs second: accrual CREDIT
// INCOME_FROM_FEES / DEBIT FEES_RECEIVABLE and CREDIT INCOME_FROM_PENALTIES /
// DEBIT PENALTIES_RECEIVABLE; an adjustment swaps the sides. The fee and
// penalty groups are separate helper calls and never merge with each other.
//
// On the pinned observations loan-1 L2 (accrual, interest 0.33) posts a 33
// debit to account 7 then a 33 credit to 8; loan-11 L84 (accrual, interest
// 10.00, fee 10.00, penalty 15.00) posts the interest pair, then a fee credit
// 5 / debit 7 pair, then a penalty credit 5 / debit 7 pair — six legs, the two
// charge groups not merged despite sharing accounts 5 and 7; loan-15 L107
// (accrual adjustment, interest 2.79) posts a 279 debit to 8 then a 279 credit
// to 7; loan-19 L145 (accrual, penalty 15.00 alone) posts a 1500 credit to 5
// then a 1500 debit to 7. The account ids are THIS replay's product mapping
// (receivable interest/fee/penalty 7, interestOnLoan 8, incomeFromFee 5,
// incomeFromPenalty 5).
//
// The tax branch and the charge-specific GL mappings are NOT observed and are
// not expressible here: the port takes the resolved product accounts and no
// tax or charge input.
const SeamLoanAccrualJournalEntries = "loan-accrual-journal-entries"

// SeamLoanChargebackJournalEntries is the capture seam this schema grades: the
// journal entry a loan CHARGEBACK posts on a loan that is NOT charged off, the
// chargeback sibling of the charge-off-journal seam. It ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForChargeback
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1215-1308, pinned
// commit 426a23544], in posting order: when the amount is > 0 CREDIT the
// resolved fund source (the transaction paymentTypeId's channel account, else
// the product FUND_SOURCE); when the overpayment portion is > 0 DEBIT
// OVERPAYMENT; when principalCredited > principalPaid DEBIT LOAN_PORTFOLIO the
// difference. The observed domain has no fee or penalty portion, no paid
// portion and no charged-off loan, so the port has no field for any of them and
// REFUSES an amount that is not principal + overpayment rather than guessing an
// unported branch.
//
// On the pinned observations transaction L69 (loan 14) carries principal 250
// and no overpayment (CREDIT fund-source 4 250, DEBIT loan-portfolio 10 250);
// L99 (loan 19) carries overpayment 250 and no principal (CREDIT 4 250, DEBIT
// overpayment 18 250); L109 (loan 21) carries 350 = overpayment 250 + principal
// 100, the overpayment debit 241 preceding the principal debit 242 (CREDIT 4
// 350, DEBIT 18 250, DEBIT 10 100). The chargeback was posted with
// paymentTypeId 2, which has no channel mapping, so the product FUND_SOURCE
// account 4 applies.
const SeamLoanChargebackJournalEntries = "loan-chargeback-journal-entries"

// SeamLoanBuyDownFeeJournalEntries is the capture seam this schema grades: the
// journal entry a BUY_DOWN_FEE transaction posts. It ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForBuyDownFee
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:530-551, pinned commit
// 426a23544]. When the amount is > 0 it posts two legs in order through
// helper.createJournalEntriesForLoan(debit, credit): DEBIT BUY_DOWN_EXPENSE when
// the loan product's merchantBuyDownFee is set, else the resolved FUND_SOURCE,
// then CREDIT DEFERRED_INCOME_LIABILITY, both with the amount.
//
// On the pinned observations L2 (loan 1, merchant product
// LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES) DEBITs buy-down
// expense account 23 5000 then CREDITs deferred-income-liability 22 5000; L781
// (loan 20, non-merchant product
// LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT) DEBITs
// fund-source account 5 5000 then CREDITs 22 5000. The only channel mapping is
// paymentTypeId 1 -> 17, and both transactions use paymentTypeId 5, so the
// product FUND_SOURCE 5 applies on the non-merchant side. A NON-merchant product
// has no buy-down expense account, so a merchant=true input whose mapping omits
// it is refused rather than falling back to the fund source.
const SeamLoanBuyDownFeeJournalEntries = "loan-buy-down-fee-journal-entries"

// SeamLoanCreditBalanceRefundJournalEntries is the capture seam this schema
// grades: the journal entry a CREDIT BALANCE REFUND posts, the refund sibling of
// the chargeback seam. It ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForLoanCreditBalanceRefund
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:2120-2155, dispatched
// from createJournalEntriesForCreditBalanceRefund :2113-2118, pinned commit
// 426a23544], in posting order: when the principal portion is > 0 DEBIT the
// account determineAccrualAccountForCBR selects — LOAN_PORTFOLIO while the loan
// is not charged off, CHARGE_OFF_EXPENSE once it is, and CHARGE_OFF_FRAUD_EXPENSE
// when it is also fraud; when the overpayment portion is > 0 DEBIT OVERPAYMENT
// (the charged-off and fraud flags never reach this slot); then ONE CREDIT of
// the total to the RESOLVED fund source (the transaction paymentTypeId's
// payment-channel account when the product maps that channel, else the product
// FUND_SOURCE). Unlike a repayment or chargeback the debits come first and the
// single credit is last.
//
// On the pinned observations transaction L5 (loan 1) carries overpayment 200 and
// no principal (DEBIT overpayment 16 200, CREDIT fund-source 4 200; the later
// ids 21-22 are a separate reversal pair and are not graded); L112 (loan 19)
// carries principal 10 and overpayment 190 (DEBIT 5 10, DEBIT 16 190, CREDIT 4
// 200); L175 (loan 28, CHARGED OFF, not fraud) carries principal 250 (DEBIT
// charge-off expense 15 250, CREDIT 4 250); L169 (loan 27, CHARGED OFF AND
// FRAUD) carries principal 250 (DEBIT charge-off fraud expense 11 250, CREDIT 4
// 250). The refunds were posted with paymentTypeId 6, which has no channel
// mapping (the only mapping is paymentTypeId 1 -> 19), so the product FUND_SOURCE
// account 4 applies.
const SeamLoanCreditBalanceRefundJournalEntries = "loan-credit-balance-refund-journal-entries"

// SeamLoanChargeLifecycle is the capture seam this schema grades: the
// money-mutation lifecycle of a single LoanCharge on loan 18. The fee
// (charge 14, amount 123.45) is created, partly paid 100.00, then fully paid;
// the penalty (charge 13, amount 67.89) is created and waived. Each step is
// graded through loan.UpdatePaidAmountBy, loan.Waive and
// loan.UpdateWaivedAmount.
const SeamLoanChargeLifecycle = "loan-charge-lifecycle"

// SeamLoanStatusTransition is the capture seam this schema grades: the loan
// lifecycle state machine the observed status transitions read back. Fineract's
// DefaultLoanLifecycleStateMachine answers two questions: NextStatus(from,
// event, facts) dispatches an event, and DetermineTransition(from, facts)
// recomputes the status from the balance facts for a loan already active or
// terminal. The committed captures observe submit->approve->disburse (SEED-L06),
// a loan repaid in full -> CLOSED_OBLIGATIONS_MET (loan 18) and a loan written
// off -> CLOSED_WRITTEN_OFF (loan 11). Each is graded through loan.NextStatus or
// loan.DetermineTransition.
const SeamLoanStatusTransition = "loan-status-transition"

// SchemaContexts returns the complete set of store contexts a vector bearing
// SchemaV1 may claim. A vector claiming any other context is INADMISSIBLE.
func SchemaContexts() []string { return []string{LoanContext} }

// IsSchemaContext reports whether ctx is one of SchemaContexts().
func IsSchemaContext(ctx string) bool {
	for _, c := range SchemaContexts() {
		if ctx == c {
			return true
		}
	}
	return false
}

// VectorClass is what a loan vector file claims to be.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit. Only this class counts toward the
	// loan parity tally.
	ClassParity VectorClass = "parity"
)

// ProvenanceKindOracleCapture is the only admissible provenance.kind for a
// parity vector.
const ProvenanceKindOracleCapture = shared.ProvenanceKindOracleCapture

// OracleStamp records where and against what the expectation was captured.
type OracleStamp struct {
	Seam           string `json:"seam"`
	FineractCommit string `json:"fineract_commit"`
}

// Provenance is where a parity vector's expected values came from: a committed
// oracle capture artefact, named by repo-relative path and content hash, and the
// case id within it that was transcribed.
type Provenance struct {
	Kind          string `json:"kind"`
	Note          string `json:"note"`
	CaptureRef    string `json:"capture_ref"`
	CaptureSHA256 string `json:"capture_sha256"`
	CaptureCaseID string `json:"capture_case_id"`
	Citation      string `json:"citation"`
}

// TenantParams is the tenant context a capture was taken under. The loan
// captures were taken under the gerege tenant: HALF_UP (ordinal 4), precision
// 19, currency MNT, 2 minor units, Asia/Ulaanbaatar.
type TenantParams = shared.TenantParams

// AllocationMoney is the four-bucket money breakdown of a repayment allocation,
// each bucket an integer STRING in minor units.
type AllocationMoney struct {
	Penalty   string `json:"penalty"`
	Fee       string `json:"fee"`
	Interest  string `json:"interest"`
	Principal string `json:"principal"`
}

// RepaymentRequest is the loan-repayment-allocation seam's input: the outstanding
// buckets the allocation runs against and the payment amount.
type RepaymentRequest struct {
	Outstanding AllocationMoney `json:"outstanding"`
	AmountMinor string          `json:"amount_minor"`
}

// ScheduleRequest is the loan-schedule-interest seam's input: the MANIFEST's
// discriminating input (principal, annual rate per cent, day conventions).
type ScheduleRequest struct {
	PrincipalMinor  string `json:"principal_minor"`
	RatePerAnnumPct int64  `json:"rate_per_annum_pct"`
	DaysInYear      int64  `json:"days_in_year"`
	DaysInMonth     int64  `json:"days_in_month"`
}

// ScheduleAmortizationRequest is the loan-schedule-amortization seam's input:
// the principal the oracle disbursed and the observed per-period principalDue
// components of a full repayment schedule, each an integer STRING in minor
// units. Period 0 of the capture is the disbursement row and carries no
// principalDue, so the components are exactly the repayment periods that do.
// A component carrying more than 2 decimal places of significance is a
// sub-minor residue: it is REFUSED by admission (G-19 / DEC-2 predicate G-08),
// never rounded and never vectored.
type ScheduleAmortizationRequest struct {
	PrincipalDisbursedMinor  string   `json:"principal_disbursed_minor"`
	PrincipalComponentsMinor []string `json:"principal_components_minor"`
}

// WriteOffInstallmentInput is one repayment-schedule instalment reduced to the
// cells loan.WriteOffOutstanding reads: its four outstanding buckets, each an
// integer STRING in minor units, and its obligationsMet flag. The flag is
// omitted when false (the committed loan-11 schedule has no fully-paid
// instalment), so a request with every obligationsMet false carries no flag
// token — the port's zero value is false and the instalment is written off.
type WriteOffInstallmentInput struct {
	PrincipalOutstandingMinor string `json:"principal_outstanding_minor"`
	InterestOutstandingMinor  string `json:"interest_outstanding_minor"`
	FeeOutstandingMinor       string `json:"fee_outstanding_minor"`
	PenaltyOutstandingMinor   string `json:"penalty_outstanding_minor"`
	ObligationsMet            bool   `json:"obligations_met,omitempty"`
}

// WriteOffRequest is the loan-writeoff-four-bucket seam's input: the observed
// repayment schedule as the per-instalment outstanding loan.WriteOffOutstanding
// consumes. Period 0 of a loan read-back is the disbursement row and carries no
// outstanding buckets, so the instalments are exactly the repayment periods.
type WriteOffRequest struct {
	Installments []WriteOffInstallmentInput `json:"installments"`
}

// ReversalRequest is the loan-transaction-reversal seam's input: the journal
// entries of ONE loan transaction as read back BEFORE it was reversed, reduced
// to the (transaction_id, account, entry_type, amount_minor) cells the reversal
// reads, plus the reversed transaction's transaction date. Every leg must share
// the one transaction id — the reversal operates on one transaction's entries.
type ReversalRequest struct {
	TransactionDate string            `json:"transaction_date"`
	JournalEntries  []JournalEntryLeg `json:"journal_entries"`
}

// ReversalLegCell is one leg of the loan-transaction-reversal seam's expected
// after-read-back list: the before legs as they were, then the counter-legs the
// reversal ADDED. TransactionDate and Reversed are the two cells the batch
// sum cannot see — a port that dates a counter-leg at the business date, or
// flags an original reversed, moves them while every side and amount stays put.
type ReversalLegCell struct {
	TransactionID   string `json:"transaction_id"`
	Account         string `json:"account"`
	EntryType       string `json:"entry_type"`
	AmountMinor     string `json:"amount_minor"`
	TransactionDate string `json:"transaction_date"`
	Reversed        bool   `json:"reversed"`
}

// WriteOffPortionsMoney is the per-slot money a write-off discharges, each slot
// an integer STRING in minor units. It is the request-side reduction of
// loan.WriteOffPortions: the five fields
// createJournalEntriesForLoanWriteOffs reads off the write-off transaction.
// Overpayment is omitted when zero (the committed loan-11 write-off carries no
// overpayment portion), so the port's zero value is used.
type WriteOffPortionsMoney struct {
	Principal   string `json:"principal"`
	Interest    string `json:"interest"`
	Fee         string `json:"fee"`
	Penalty     string `json:"penalty"`
	Overpayment string `json:"overpayment,omitempty"`
}

// WriteOffSlotAccounts is the product's write-off slot->account mapping, each
// account the GL code the oracle's GET /loanproducts/{id}.accountingMappings
// returns for that slot: loanPortfolioAccount, receivableInterestAccount,
// receivableFeeAccount, receivablePenaltyAccount,
// overpaymentLiabilityAccount and writeOffAccount. Overpayment is omitted when
// the product's overpayment slot is not exercised (every portion is zero).
type WriteOffSlotAccounts struct {
	LoanPortfolio       string `json:"loan_portfolio"`
	InterestReceivable  string `json:"interest_receivable"`
	FeesReceivable      string `json:"fees_receivable"`
	PenaltiesReceivable string `json:"penalties_receivable"`
	Overpayment         string `json:"overpayment,omitempty"`
	LossesWrittenOff    string `json:"losses_written_off"`
}

// WriteOffJournalRequest is the loan-writeoff-journal-entries seam's input: the
// observed write-off portions and the product's slot->account mapping, plus the
// transaction id the legs are posted under. The mapping is the product's
// accountingMappings read back from the reference server, never invented; a
// slot with a positive portion and no account is refused by the port.
type WriteOffJournalRequest struct {
	TransactionID string                `json:"transaction_id"`
	Portions      WriteOffPortionsMoney `json:"portions"`
	Accounts      WriteOffSlotAccounts  `json:"accounts"`
}

// ChargeOffPortionsMoney is the per-slot money a charge-off discharges, each
// slot an integer STRING in minor units. It is the request-side reduction of
// loan.ChargeOffPortions: the four fields createJournalEntriesForChargeOff
// reads off the charge-off transaction. There is no overpayment portion on a
// charge-off.
type ChargeOffPortionsMoney struct {
	Principal string `json:"principal"`
	Interest  string `json:"interest"`
	Fee       string `json:"fee"`
	Penalty   string `json:"penalty"`
}

// ChargeOffSlotAccounts is the product's charge-off slot->account mapping, each
// account the GL code the oracle's GET /loanproducts/{id}.accountingMappings
// returns for that slot. The four *_receivable slots are credited; the
// charge-off expense (or fraud expense, when the loan is marked fraud),
// income-from-charge-off-interest, income-from-charge-off-fees and
// income-from-charge-off-penalty slots are debited. ChargeOffReason is omitted
// on every observed product: it names the advanced mapping the loan slice has
// NOT observed, and the port REFUSES a non-empty value rather than guessing it.
type ChargeOffSlotAccounts struct {
	LoanPortfolio               string `json:"loan_portfolio"`
	InterestReceivable          string `json:"interest_receivable"`
	FeesReceivable              string `json:"fees_receivable"`
	PenaltiesReceivable         string `json:"penalties_receivable"`
	ChargeOffExpense            string `json:"charge_off_expense"`
	ChargeOffFraudExpense       string `json:"charge_off_fraud_expense"`
	IncomeFromChargeOffInterest string `json:"income_from_charge_off_interest"`
	IncomeFromChargeOffFees     string `json:"income_from_charge_off_fees"`
	IncomeFromChargeOffPenalty  string `json:"income_from_charge_off_penalty"`
	ChargeOffReason             string `json:"charge_off_reason,omitempty"`
}

// ChargeOffJournalRequest is the loan-chargeoff-journal-entries seam's input:
// the observed charge-off portions, whether the loan is marked fraud, and the
// product's slot->account mapping, plus the transaction id the legs are posted
// under. The mapping is the product's accountingMappings read back from the
// reference server, never invented; a slot with a positive portion and no
// account is refused by the port.
type ChargeOffJournalRequest struct {
	TransactionID string                 `json:"transaction_id"`
	Portions      ChargeOffPortionsMoney `json:"portions"`
	Fraud         bool                   `json:"fraud,omitempty"`
	Accounts      ChargeOffSlotAccounts  `json:"accounts"`
}

// ChargedOffWriteOffPortionsMoney is the per-slot money a write-off on a
// charged-off loan reverses, each slot an integer STRING in minor units. It is
// the request-side reduction of loan.ChargedOffWriteOffPortions: the five fields
// createJournalEntriesForWriteOffsWhenLoanIsChargedOff reads off the write-off
// transaction. Overpayment is optional (absent when the observed read-back
// omits it).
type ChargedOffWriteOffPortionsMoney struct {
	Principal   string `json:"principal"`
	Interest    string `json:"interest"`
	Fee         string `json:"fee"`
	Penalty     string `json:"penalty"`
	Overpayment string `json:"overpayment,omitempty"`
}

// ChargedOffWriteOffSlotAccounts is the product's charged-off write-off
// slot->account mapping, each account the GL code the oracle's
// GET /loanproducts/{id}.accountingMappings returns for that slot. The
// charge-off expense (or fraud expense, when the loan is marked fraud),
// income-from-charge-off-interest, income-from-charge-off-fees,
// income-from-charge-off-penalty and overpayment slots are CREDITED; the
// losses-written-off slot is DEBITed ONCE with the total. FundSource is the
// product's FUND_SOURCE slot, which the processor resolves as the paired debit
// of every portion and NEVER posts; it carries no posting and exists only so
// the wrong-mode drive can name the account its unposted debit map would use.
type ChargedOffWriteOffSlotAccounts struct {
	ChargeOffExpense            string `json:"charge_off_expense"`
	ChargeOffFraudExpense       string `json:"charge_off_fraud_expense"`
	IncomeFromChargeOffInterest string `json:"income_from_charge_off_interest"`
	IncomeFromChargeOffFees     string `json:"income_from_charge_off_fees"`
	IncomeFromChargeOffPenalty  string `json:"income_from_charge_off_penalty"`
	Overpayment                 string `json:"overpayment,omitempty"`
	LossesWrittenOff            string `json:"losses_written_off"`
	FundSource                  string `json:"fund_source"`
}

// ChargedOffWriteOffJournalRequest is the loan-chargedoff-writeoff-journal-entries
// seam's input: the observed write-off portions of a loan that is ALREADY MARKED
// CHARGED OFF, whether the loan is marked fraud, and the product's
// slot->account mapping, plus the transaction id the legs are posted under. The
// mapping is the product's accountingMappings read back from the reference
// server, never invented; a slot with a positive portion and no credit account
// is refused by the port.
type ChargedOffWriteOffJournalRequest struct {
	TransactionID string                          `json:"transaction_id"`
	Portions      ChargedOffWriteOffPortionsMoney `json:"portions"`
	Fraud         bool                            `json:"fraud,omitempty"`
	Accounts      ChargedOffWriteOffSlotAccounts  `json:"accounts"`
}

// RepaymentPortionsMoney is the per-slot money an ordinary repayment applies,
// each slot an integer STRING in minor units. It is the request-side reduction
// of loan.RepaymentPortions: the five fields
// createJournalEntriesForLoanRepayments reads off the repayment transaction.
// Overpayment is optional (absent when the observed read-back omits it).
type RepaymentPortionsMoney struct {
	Principal   string `json:"principal"`
	Interest    string `json:"interest"`
	Fee         string `json:"fee"`
	Penalty     string `json:"penalty"`
	Overpayment string `json:"overpayment,omitempty"`
}

// RepaymentSlotAccounts is the product's repayment slot->account mapping, each
// account the GL code the oracle's GET /loanproducts/{id}.accountingMappings
// returns for that slot, plus the RESOLVED fund source. The
// loan-portfolio, receivable-interest, receivable-fee, receivable-penalty and
// overpayment slots are CREDITED; the fund-source slot is DEBITed ONCE with the
// total. FundSource is the RESOLVED account: the payment-channel account when
// the transaction's paymentTypeId has one, else the product's FUND_SOURCE. The
// caller resolves the channel, so this seam carries only the resolved account.
type RepaymentSlotAccounts struct {
	LoanPortfolio      string `json:"loan_portfolio"`
	ReceivableInterest string `json:"receivable_interest"`
	ReceivableFee      string `json:"receivable_fee"`
	ReceivablePenalty  string `json:"receivable_penalty"`
	Overpayment        string `json:"overpayment,omitempty"`
	FundSource         string `json:"fund_source"`
}

// RepaymentJournalRequest is the loan-repayment-journal-entries seam's input:
// the observed portions of an ordinary repayment on a loan that is NOT charged
// off and the resolved slot->account mapping, plus the transaction id the legs
// are posted under. The mapping is the product's accountingMappings (with the
// fund source resolved through the payment channel) read back from the reference
// server, never invented; a slot with a positive portion and no mapped account
// is refused by the port.
type RepaymentJournalRequest struct {
	TransactionID string                 `json:"transaction_id"`
	Portions      RepaymentPortionsMoney `json:"portions"`
	Accounts      RepaymentSlotAccounts  `json:"accounts"`
}

// GoodwillCreditSlotAccounts is the product's goodwill-credit slot->account
// mapping: the five CREDIT slots an ordinary repayment also posts, the four
// GOODWILL-CREDIT DEBIT slots the debitAccountMapForGoodwillCredit resolves, the
// INCOME_FROM_RECOVERY credit slot the CHARGED-OFF arm posts the four
// non-overpayment portions to, and the RESOLVED fund source the wrong drive
// posts instead. The credit slots and the fund source are the same as
// RepaymentSlotAccounts; the debit slots are the goodwill arm's own table.
// FundSource is the RESOLVED account (the payment-channel account when the
// transaction's paymentTypeId has one, else the product's FUND_SOURCE); the
// correct port never posts it, but the registered wrong implementations express
// their defects by posting it, so the seam carries it. The slots a positive
// portion needs are required; a slot with a positive portion and no mapped
// account is refused by the port. IncomeFromRecovery is required only on a
// charged-off loan with a positive principal, interest, fee or penalty portion:
// the NOT-charged-off arm never reads it.
type GoodwillCreditSlotAccounts struct {
	LoanPortfolio                    string `json:"loan_portfolio"`
	ReceivableInterest               string `json:"receivable_interest"`
	ReceivableFee                    string `json:"receivable_fee"`
	ReceivablePenalty                string `json:"receivable_penalty"`
	IncomeFromRecovery               string `json:"income_from_recovery,omitempty"`
	Overpayment                      string `json:"overpayment,omitempty"`
	GoodwillCredit                   string `json:"goodwill_credit"`
	IncomeFromGoodwillCreditInterest string `json:"income_from_goodwill_credit_interest"`
	IncomeFromGoodwillCreditFees     string `json:"income_from_goodwill_credit_fees"`
	IncomeFromGoodwillCreditPenalty  string `json:"income_from_goodwill_credit_penalty"`
	FundSource                       string `json:"fund_source"`
}

// GoodwillCreditJournalRequest is the loan-goodwill-credit-journal-entries
// seam's input: the observed portions of a GOODWILL CREDIT transaction, the
// loan's charged-off state (which selects which accounts the credit side posts)
// and the slot->account mapping, plus the transaction id the legs are posted
// under. The mapping is the product's accountingMappings (with the fund source
// resolved through the payment channel) read back from the reference server,
// never invented; a slot with a positive portion and no mapped credit or debit
// account is refused by the port.
type GoodwillCreditJournalRequest struct {
	TransactionID string                     `json:"transaction_id"`
	Portions      RepaymentPortionsMoney     `json:"portions"`
	ChargedOff    bool                       `json:"charged_off,omitempty"`
	Accounts      GoodwillCreditSlotAccounts `json:"accounts"`
}

// DisbursementSlotAccounts is the product's disbursement slot->account mapping:
// the loan portfolio the principal portion DEBITs, the overpayment liability the
// overpayment portion DEBITs, and the RESOLVED fund source the whole amount
// CREDITs once. FundSource is the RESOLVED account — the payment-channel account
// when the transaction's paymentTypeId has one, else the product's FUND_SOURCE —
// so the seam carries only the resolved account and needs no payment-type lookup
// or product state.
//
// The overpayment account is required by the port only when the overpayment
// portion is positive; it is carried here from the product's OVERPAYMENT slot
// even when that portion is 0, because the product maps it and the caller reads
// it back rather than inventing it.
type DisbursementSlotAccounts struct {
	LoanPortfolio string `json:"loan_portfolio"`
	Overpayment   string `json:"overpayment,omitempty"`
	FundSource    string `json:"fund_source"`
}

// DisbursementJournalRequest is the loan-disbursement-journal-entries seam's
// input: the observed disbursement transaction's amount and overpayment in
// integer minor units, the resolved slot->account mapping and the transaction id
// the legs are posted under. The principal portion is NOT carried as an input —
// the port derives it as amount minus overpayment; the read-back
// principalPortion field is carried only in PrincipalPortion, and only so the
// registered wrong implementation can read it, so the correct port never sees
// it. The mapping is the product's accountingMappings (with the fund source
// resolved through the payment channel) read back from the reference server,
// never invented; a positive leg with no mapped account is refused by the port.
type DisbursementJournalRequest struct {
	TransactionID string `json:"transaction_id"`
	Amount        string `json:"amount"`
	Overpayment   string `json:"overpayment,omitempty"`
	// PrincipalPortion is the read-back transaction's principalPortion field, 0
	// on every observed disbursement. The CORRECT port must not read it: it is
	// the wrong drive's input, carried here so that drive can express the defect
	// without touching the port.
	PrincipalPortion string                   `json:"principal_portion,omitempty"`
	Accounts         DisbursementSlotAccounts `json:"accounts"`
}

// ChargeAdjustmentSlotAccounts is the product's charge-adjustment
// slot->account mapping: the five CREDIT slots of the NOT-charged-off arm (the
// receivables), the two charge-off income slots the charged-off arm credits
// instead, and the two income slots the single total debit selects between. A
// positive portion must have its slot mapped; a positive total must have the
// selected debit slot mapped, else the port refuses. Overpayment is shared by
// both arms.
type ChargeAdjustmentSlotAccounts struct {
	LoanPortfolio              string `json:"loan_portfolio"`
	ReceivableInterest         string `json:"receivable_interest"`
	ReceivableFee              string `json:"receivable_fee"`
	ReceivablePenalty          string `json:"receivable_penalty"`
	Overpayment                string `json:"overpayment,omitempty"`
	IncomeFromChargeOffFees    string `json:"income_from_charge_off_fees"`
	IncomeFromChargeOffPenalty string `json:"income_from_charge_off_penalty"`
	IncomeFromFees             string `json:"income_from_fees"`
	IncomeFromPenalties        string `json:"income_from_penalties"`
}

// ChargeAdjustmentJournalRequest is the
// loan-charge-adjustment-journal-entries seam's input: the observed portions of
// a CHARGE ADJUSTMENT transaction, the loan's charged-off state, whether the
// adjusted charge is a penalty (which selects the single debit account) and the
// product's slot->account mapping, plus the transaction id the legs are posted
// under. The mapping is the product's accountingMappings read back from the
// reference server, never invented, and carries no charge id: a charge-specific
// debit override is not modelled.
type ChargeAdjustmentJournalRequest struct {
	TransactionID string                       `json:"transaction_id"`
	Portions      RepaymentPortionsMoney       `json:"portions"`
	ChargedOff    bool                         `json:"charged_off,omitempty"`
	PenaltyCharge bool                         `json:"penalty_charge,omitempty"`
	Accounts      ChargeAdjustmentSlotAccounts `json:"accounts"`
}

// ChargedOffRepaymentSlotAccounts is the slot->account mapping of a repayment on
// a loan MARKED CHARGED OFF. IncomeFromRecovery is the recovery account every
// positive principal, interest, fee and penalty portion credits (regardless of
// the loan's fraud flag); Overpayment is the account a positive overpayment
// portion credits; FundSource is the RESOLVED account the single total debit
// posts to (the transaction paymentTypeId's payment-channel account when the
// product maps that channel, else the product FUND_SOURCE).
//
// The ordinary loan-portfolio and interest-receivable slots are carried too, not
// because the charged-off port reads them — it never does — but because the
// registered wrong implementation expresses the ordinary-posting defect by
// reposting the same repayment through the ORDINARY port, which needs them. A
// correct charged-off port reads only income_from_recovery, overpayment and
// fund_source.
type ChargedOffRepaymentSlotAccounts struct {
	IncomeFromRecovery string `json:"income_from_recovery"`
	LoanPortfolio      string `json:"loan_portfolio"`
	ReceivableInterest string `json:"receivable_interest"`
	Overpayment        string `json:"overpayment,omitempty"`
	FundSource         string `json:"fund_source"`
}

// ChargedOffRepaymentJournalRequest is the
// loan-chargedoff-repayment-journal-entries seam's input: the observed portions
// of a REPAYMENT on a loan already marked charged off and the resolved
// slot->account mapping, plus the transaction id the legs are posted under.
// There is no transaction-type field: the port takes a repayment only. The
// mapping is the product's accountingMappings (with the fund source resolved
// through the payment channel) read back from the reference server, never
// invented; a slot with a positive portion and no mapped account is refused by
// the port.
type ChargedOffRepaymentJournalRequest struct {
	TransactionID string                          `json:"transaction_id"`
	Portions      RepaymentPortionsMoney          `json:"portions"`
	Accounts      ChargedOffRepaymentSlotAccounts `json:"accounts"`
}

// SeamLoanInterestPaymentWaiverJournalEntries is the capture seam this schema
// grades: the journal entry an INTEREST_PAYMENT_WAIVER transaction posts. It
// ports AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForInterestPaymentWaiverOrInterestRefund for the waiver
// type [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:793-889, pinned
// commit 426a23544]. For each of the five portion slots (principal, interest,
// fees, penalties, overpayment) whose portion is > 0 the processor CREDITS the
// slot's account — LOAN_PORTFOLIO, INTEREST_RECEIVABLE, FEES_RECEIVABLE,
// PENALTIES_RECEIVABLE and OVERPAYMENT respectively while the loan is NOT
// charged off, but the charge-off income account
// INCOME_FROM_CHARGE_OFF_INTEREST for principal, interest, fees AND penalties
// once it is, with overpayment unchanged — MERGING portions that resolve to the
// SAME account (accountMap is a LinkedHashMap) into one credit at the first
// slot's position; it then posts ONE debit of the total to INTEREST_ON_LOANS.
// The credits come first and the single debit is last.
//
// On the pinned observations transaction L4 (loan 2) credits the loan portfolio
// 1000 and the interest+fee receivable MERGED to 3000 then debits 4000; L23
// (loan 7) credits portfolio 100000, receivable 4000 and overpayment 6000 then
// debits 110000; L42 (loan 11, CHARGED OFF) merges principal 25000 and interest
// 1000 into ONE charge-off income credit of 26000 then debits 26000; L76 (loan
// 13, CHARGED OFF) credits charge-off income 4656 and debits 4656. The
// interest-refund arm shares the method but is NOT observed here.
const SeamLoanInterestPaymentWaiverJournalEntries = "loan-interest-payment-waiver-journal-entries"

// InterestPaymentWaiverPortionsMoney is the per-slot money an
// interest-payment waiver applies, each slot an integer STRING in minor units.
// It is the request-side reduction of loan.RepaymentPortions: the five fields
// createJournalEntriesForInterestPaymentWaiverOrInterestRefund reads off the
// waiver transaction. Overpayment is optional (absent when the observed
// read-back omits it).
type InterestPaymentWaiverPortionsMoney struct {
	Principal   string `json:"principal"`
	Interest    string `json:"interest"`
	Fee         string `json:"fee"`
	Penalty     string `json:"penalty"`
	Overpayment string `json:"overpayment,omitempty"`
}

// InterestPaymentWaiverSlotAccounts is the product's interest-payment-waiver
// slot->account mapping, each account the GL code the oracle's
// GET /loanproducts/{id}.accountingMappings returns for that slot. The
// loan-portfolio, receivable-interest, receivable-fee, receivable-penalty and
// overpayment slots are CREDITED while the loan is NOT charged off; when it IS
// charged off the four principal/interest/fee/penalty slots all credit
// income_from_charge_off_interest instead, and overpayment still credits
// overpayment. The interest-on-loan slot is DEBITed ONCE with the total in both
// branches.
type InterestPaymentWaiverSlotAccounts struct {
	LoanPortfolio               string `json:"loan_portfolio"`
	ReceivableInterest          string `json:"receivable_interest"`
	ReceivableFee               string `json:"receivable_fee"`
	ReceivablePenalty           string `json:"receivable_penalty"`
	Overpayment                 string `json:"overpayment,omitempty"`
	InterestOnLoan              string `json:"interest_on_loan"`
	IncomeFromChargeOffInterest string `json:"income_from_charge_off_interest"`
}

// InterestPaymentWaiverJournalRequest is the
// loan-interest-payment-waiver-journal-entries seam's input: the observed
// portions of an INTEREST_PAYMENT_WAIVER transaction, the loan's charged-off
// state and the product's slot->account mapping, plus the transaction id the
// legs are posted under. The mapping is the product's accountingMappings read
// back from the reference server, never invented; a slot with a positive portion
// and no mapped credit account is refused by the port.
type InterestPaymentWaiverJournalRequest struct {
	TransactionID string                             `json:"transaction_id"`
	Portions      InterestPaymentWaiverPortionsMoney `json:"portions"`
	ChargedOff    bool                               `json:"charged_off,omitempty"`
	Accounts      InterestPaymentWaiverSlotAccounts  `json:"accounts"`
}

// SeamLoanCapitalizedIncomeAmortizationJournalEntries is the capture seam this
// schema grades: the journal entry a CAPITALIZED_INCOME_AMORTIZATION transaction
// posts. It ports AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForCapitalizedIncomeAmortization, dispatching on the
// loan's charged-off state to
// createJournalEntriesForLoanCapitalizedIncomeAmortization or
// createJournalEntriesForChargeOffLoanCapitalizedIncomeAmortization [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:308-502, pinned commit 426a23544].
// For each positive portion (interest, fees) it DEBITS
// DEFERRED_INCOME_LIABILITY and CREDITS ONE income account: INCOME_FROM_CAPITALIZATION
// while the loan is neither charged off nor written off, LOSSES_WRITTEN_OFF once
// it is written off, CHARGE_OFF_EXPENSE once it is charged off (non-fraud), or
// CHARGE_OFF_FRAUD_EXPENSE once it is charged off and fraud. The two portions
// resolve to the SAME credit account and the SAME deferred-income-liability
// account, so the processor MERGES them into ONE credit and ONE debit (its
// accountMap is a LinkedHashMap); credits come first, the debit last.
//
// On the pinned observations L5 (loan 1, neither) credits income from
// capitalization (account 6) 10000 and debits deferred income liability (23)
// 10000; L131 (loan 21, WRITTEN OFF) credits losses written off (13) 10000 and
// debits 23 10000; L784 (loan 30, CHARGED OFF, no charge-off reason) credits
// charge-off expense (14) 1648 and debits 23 1648; L332 (loan 25, CHARGED OFF
// and FRAUD, no charge-off reason) credits charge-off fraud expense (12) 1667
// and debits 23 1667. The capitalized-income
// CLASSIFICATION branch and the charge-off-REASON branch share the Java method
// but are NOT observed, and the request carries no input for them.
const SeamLoanCapitalizedIncomeAmortizationJournalEntries = "loan-capitalized-income-amortization-journal-entries"

// CapitalizedIncomeAmortizationPortionsMoney is the money a
// CAPITALIZED_INCOME_AMORTIZATION transaction amortizes, each slot an integer
// STRING in minor units. It is the request-side reduction of the transaction's
// interestPortion and feeChargesPortion. Fee is optional (absent when the
// observed read-back omits it).
type CapitalizedIncomeAmortizationPortionsMoney struct {
	Interest string `json:"interest"`
	Fee      string `json:"fee,omitempty"`
}

// CapitalizedIncomeAmortizationSlotAccounts is the product's
// capitalized-income-amortization slot->account mapping, each account the GL code
// the oracle's GET /loanproducts/{id}.accountingMappings returns for that slot.
// DeferredIncomeLiability is DEBITed ONCE with the sum of both portions.
// IncomeFromCapitalization is CREDITED when the loan is neither charged off nor
// written off, WriteOff (LOSSES_WRITTEN_OFF) when it is written off,
// ChargeOffExpense when it is charged off (non-fraud) and ChargeOffFraudExpense
// when it is charged off and fraud.
type CapitalizedIncomeAmortizationSlotAccounts struct {
	IncomeFromCapitalization string `json:"income_from_capitalization"`
	DeferredIncomeLiability  string `json:"deferred_income_liability"`
	ChargeOffExpense         string `json:"charge_off_expense,omitempty"`
	ChargeOffFraudExpense    string `json:"charge_off_fraud_expense,omitempty"`
	WriteOff                 string `json:"write_off,omitempty"`
}

// CapitalizedIncomeAmortizationJournalRequest is the
// loan-capitalized-income-amortization-journal-entries seam's input: the
// observed interest and fee portions of a CAPITALIZED_INCOME_AMORTIZATION
// transaction, the loan's charged-off / fraud / written-off state and the
// product's slot->account mapping, plus the transaction id the legs are posted
// under. The mapping is the product's accountingMappings read back from the
// reference server, never invented; a positive portion with no mapped credit or
// deferred-income-liability account is refused by the port, as is the impossible
// charged_off && written_off state.
type CapitalizedIncomeAmortizationJournalRequest struct {
	TransactionID string                                     `json:"transaction_id"`
	Portions      CapitalizedIncomeAmortizationPortionsMoney `json:"portions"`
	ChargedOff    bool                                       `json:"charged_off,omitempty"`
	Fraud         bool                                       `json:"fraud,omitempty"`
	WrittenOff    bool                                       `json:"written_off,omitempty"`
	Accounts      CapitalizedIncomeAmortizationSlotAccounts  `json:"accounts"`
}

// ChargedOffMerchantRefundSlotAccounts is the slot->account mapping of a
// MERCHANT-ISSUED REFUND or a PAYOUT REFUND on a loan MARKED CHARGED OFF. Each
// positive portion CREDITS its own charge-off slot: principal
// ChargeOffFraudExpense when the loan is fraud else ChargeOffExpense, interest
// IncomeFromChargeOffInterest, fees IncomeFromChargeOffFees, penalties
// IncomeFromChargeOffPenalty, overpayment Overpayment. FundSource is the RESOLVED
// account the single total debit posts to (the transaction paymentTypeId's
// payment-channel account when the product maps that channel, else the product
// FUND_SOURCE).
//
// IncomeFromRecovery is carried too, not because the refund port reads it — it
// never does — but because the registered wrong implementation expresses the
// wrong-as-repayment defect by reposting the same portions through the
// charged-off REPAYMENT layout, which credits every principal, interest, fee and
// penalty portion to income_from_recovery. A correct refund port reads only the
// principal slot selected by fraud, overpayment and fund_source.
type ChargedOffMerchantRefundSlotAccounts struct {
	ChargeOffExpense            string `json:"charge_off_expense"`
	ChargeOffFraudExpense       string `json:"charge_off_fraud_expense,omitempty"`
	IncomeFromChargeOffInterest string `json:"income_from_charge_off_interest"`
	IncomeFromChargeOffFees     string `json:"income_from_charge_off_fees"`
	IncomeFromChargeOffPenalty  string `json:"income_from_charge_off_penalty"`
	Overpayment                 string `json:"overpayment,omitempty"`
	IncomeFromRecovery          string `json:"income_from_recovery"`
	FundSource                  string `json:"fund_source"`
}

// ChargedOffMerchantRefundJournalRequest is the
// loan-chargedoff-merchant-refund-journal-entries seam's input: the observed
// portions of a MERCHANT-ISSUED REFUND or a PAYOUT REFUND on a loan already
// marked charged off, the loan's fraud flag and the resolved slot->account
// mapping, plus the transaction kind and the transaction id the legs are posted
// under. Kind selects which refund arm the request is, "merchant_issued_refund"
// or "payout_refund"; an empty Kind defaults to "merchant_issued_refund" so the
// pre-existing merchant-issued-refund vectors stay valid. The two arms post
// identical legs. The mapping is the product's accountingMappings (with the fund
// source resolved through the payment channel) read back from the reference
// server, never invented; a slot with a positive portion and no mapped account
// is refused by the port, and an unknown kind is refused rather than guessed.
type ChargedOffMerchantRefundJournalRequest struct {
	TransactionID string                               `json:"transaction_id"`
	Kind          string                               `json:"kind,omitempty"`
	Portions      RepaymentPortionsMoney               `json:"portions"`
	Fraud         bool                                 `json:"fraud"`
	Accounts      ChargedOffMerchantRefundSlotAccounts `json:"accounts"`
}

// AccrualPortionsMoney is the per-slot money an accrual or accrual-adjustment
// transaction accrues, each slot an integer STRING in minor units. It is the
// request-side reduction of loan.AccrualPortions: the three fields
// createJournalEntriesForAccruals reads off the transaction (interestPortion,
// feeChargesPortion, penaltyChargesPortion). There is no principal or
// overpayment field because the observed accrual posts neither.
type AccrualPortionsMoney struct {
	Interest string `json:"interest"`
	Fee      string `json:"fee"`
	Penalty  string `json:"penalty"`
}

// AccrualSlotAccounts is the product's accrual slot->account mapping, each
// account the GL code the oracle's GET /loanproducts/{id}.accountingMappings
// returns for that slot. The receivable slots are the DEBIT side of an accrual
// and the CREDIT side of an adjustment; the income slots the reverse. The port
// takes them resolved: no tax or per-charge mapping is carried.
type AccrualSlotAccounts struct {
	ReceivableInterest string `json:"receivable_interest"`
	ReceivableFee      string `json:"receivable_fee"`
	ReceivablePenalty  string `json:"receivable_penalty"`
	InterestOnLoans    string `json:"interest_on_loans"`
	IncomeFromFee      string `json:"income_from_fee"`
	IncomeFromPenalty  string `json:"income_from_penalty"`
}

// AccrualJournalRequest is the loan-accrual-journal-entries seam's input: the
// observed portions of an ACCRUAL or ACCRUAL_ADJUSTMENT transaction and the
// resolved slot->account mapping, plus the transaction id the legs are posted
// under and whether the transaction is an adjustment. The mapping is the
// product's accountingMappings read back from the reference server, never
// invented; a slot with a positive portion and no mapped account is refused by
// the port.
type AccrualJournalRequest struct {
	TransactionID string               `json:"transaction_id"`
	Adjustment    bool                 `json:"adjustment,omitempty"`
	Portions      AccrualPortionsMoney `json:"portions"`
	Accounts      AccrualSlotAccounts  `json:"accounts"`
}

// ChargebackPortionsMoney is the money a chargeback transaction credited, per
// ledger slot, each an integer STRING in minor units. The observed domain has
// four credited slots: principal, fee, penalty and overpayment. There is no
// field for a paid portion, so a caller cannot express the unobserved
// "paid > credited" credit branches of createJournalEntriesForChargeback to this
// seam.
type ChargebackPortionsMoney struct {
	Principal   string `json:"principal"`
	Fee         string `json:"fee,omitempty"`
	Penalty     string `json:"penalty,omitempty"`
	Overpayment string `json:"overpayment"`
}

// ChargebackSlotAccounts is the RESOLVED slot->account mapping a chargeback's
// postings use. Three slots are unconditional: the fund source that the amount
// credits (the transaction paymentTypeId's payment-channel account when it has
// one, else the product FUND_SOURCE), the overpayment account the overpayment
// portion debits, and the loan-portfolio account the principal difference
// debits while the loan is NOT charged off. The charged-off slots are the
// principal CHARGE_OFF_EXPENSE, fee INCOME_FROM_CHARGE_OFF_FEES and penalty
// INCOME_FROM_CHARGE_OFF_PENALTY accounts, and the not-charged-off receivable
// slots are FEES_RECEIVABLE and PENALTIES_RECEIVABLE. Every account is the
// product's accountingMappings read back from the reference server (or the
// channel mapping), never invented; a positive slot with no account is refused
// by the port.
type ChargebackSlotAccounts struct {
	FundSource                 string `json:"fund_source"`
	LoanPortfolio              string `json:"loan_portfolio"`
	Overpayment                string `json:"overpayment"`
	FeesReceivable             string `json:"fees_receivable,omitempty"`
	PenaltiesReceivable        string `json:"penalties_receivable,omitempty"`
	ChargeOffExpense           string `json:"charge_off_expense,omitempty"`
	IncomeFromChargeOffFees    string `json:"income_from_charge_off_fees,omitempty"`
	IncomeFromChargeOffPenalty string `json:"income_from_charge_off_penalty,omitempty"`
}

// ChargebackJournalRequest is the loan-chargeback-journal-entries seam's input:
// the chargeback transaction's amount, its principal, fee, penalty and
// overpayment portions, the loan's charged-off flag (a charged-off loan debits
// the charge-off expense / charge-off income accounts), and the resolved
// slot->account mapping, plus the transaction id the legs are posted under. The
// observed identity amount = principal + fee + penalty + overpayment is
// enforced by the port: a mismatch is an unported portion, refused rather than
// posted. The unobserved paid portions and the charged-off-and-fraud
// combination have no input, so the port cannot express them.
type ChargebackJournalRequest struct {
	TransactionID string                  `json:"transaction_id"`
	Amount        string                  `json:"amount"`
	Portions      ChargebackPortionsMoney `json:"portions"`
	ChargedOff    bool                    `json:"charged_off,omitempty"`
	Fraud         bool                    `json:"fraud,omitempty"`
	Accounts      ChargebackSlotAccounts  `json:"accounts"`
}

// BuyDownFeeSlotAccounts is the resolved slot->account mapping for a buy-down
// fee, each an integer STRING account id. FundSource is already resolved through
// the transaction's payment channel (the product FUND_SOURCE when the channel
// map has no entry); BuyDownExpense is present only on a merchant product (a
// NON-merchant product has no buy-down expense account).
type BuyDownFeeSlotAccounts struct {
	FundSource              string `json:"fund_source"`
	BuyDownExpense          string `json:"buy_down_expense,omitempty"`
	DeferredIncomeLiability string `json:"deferred_income_liability"`
}

// BuyDownFeeJournalRequest is the loan-buy-down-fee-journal-entries seam's
// input: the buy-down-fee transaction's amount, the loan product's
// merchantBuyDownFee fact (which selects the debit account), and the resolved
// slot->account mapping, plus the transaction id the legs are posted under. The
// port refuses a negative amount and a positive amount whose selected debit
// account or deferred-income account is unmapped; because a NON-merchant product
// carries no buy-down expense account, a merchant=true request with no
// buy_down_expense is refused rather than guessed.
type BuyDownFeeJournalRequest struct {
	TransactionID string                 `json:"transaction_id"`
	Amount        string                 `json:"amount"`
	Merchant      bool                   `json:"merchant,omitempty"`
	Accounts      BuyDownFeeSlotAccounts `json:"accounts"`
}

// CreditBalanceRefundPortionsMoney is the two money portions a credit-balance
// refund posts, each an integer STRING in minor units: the principal debited to
// the portfolio or charge-off account and the overpayment debited to
// OVERPAYMENT. The refund has no fee, penalty or interest portion in the
// observed domain, so the port has no field for one.
type CreditBalanceRefundPortionsMoney struct {
	Principal   string `json:"principal"`
	Overpayment string `json:"overpayment"`
}

// CreditBalanceRefundSlotAccounts is the resolved slot->account mapping for a
// credit-balance refund, each an integer STRING account id. FundSource is
// already resolved through the transaction's payment channel (the product
// FUND_SOURCE when the channel map has no entry); ChargeOffExpense and
// ChargeOffFraudExpense are read only when the loan is charged off (and, for
// the latter, also fraud).
type CreditBalanceRefundSlotAccounts struct {
	FundSource            string `json:"fund_source"`
	LoanPortfolio         string `json:"loan_portfolio"`
	Overpayment           string `json:"overpayment"`
	ChargeOffExpense      string `json:"charge_off_expense,omitempty"`
	ChargeOffFraudExpense string `json:"charge_off_fraud_expense,omitempty"`
}

// CreditBalanceRefundJournalRequest is the
// loan-credit-balance-refund-journal-entries seam's input: the refund
// transaction's principal and overpayment portions, the loan's charged-off and
// fraud facts (both select the principal debit account), and the resolved
// slot->account mapping, plus the transaction id the legs are posted under. The
// port refuses a negative portion and a positive portion whose slot maps to no
// account; there is no field for a fee, penalty or interest portion because no
// observation carries one.
type CreditBalanceRefundJournalRequest struct {
	TransactionID string                           `json:"transaction_id"`
	Portions      CreditBalanceRefundPortionsMoney `json:"portions"`
	ChargedOff    bool                             `json:"charged_off,omitempty"`
	Fraud         bool                             `json:"fraud,omitempty"`
	Accounts      CreditBalanceRefundSlotAccounts  `json:"accounts"`
}

// DisburseRequest is the loan-disbursement seam's input: approved principal and
// charges due at disbursement.
type DisburseRequest struct {
	ApprovedPrincipalMinor        string `json:"approved_principal_minor"`
	ChargesDueAtDisbursementMinor string `json:"charges_due_at_disbursement_minor"`
}

// SummaryRequest is the loan-summary-outstanding seam's input: the four
// outstanding buckets of a loan summary read-back, each an integer STRING in
// minor units, transcribed from the capture's "summary" block.
type SummaryRequest struct {
	PrincipalOutstanding string `json:"principal_outstanding_minor"`
	InterestOutstanding  string `json:"interest_outstanding_minor"`
	FeeOutstanding       string `json:"fee_outstanding_minor"`
	PenaltyOutstanding   string `json:"penalty_outstanding_minor"`
}

// DelinquencyRequest is the loan-delinquent-days seam's input: the summary's
// overdueSinceDate and the business date the read-back was taken at, both civil
// dates in "YYYY-MM-DD" form, plus the two non-date day counts the port's
// DelinquentDays subtracts. OverdueSinceDate is OMITTED when the read-back
// carries no overdue date for the loan (the oracle then reports zero overdue
// days, not an error). BusinessDate is required: without it the day difference
// is undefined. PausedDays is the number of days the loan spent inside an active
// delinquency pause between the overdue-since date and the business date, and
// GraceDays is the loan product's graceOnArrearsAgeing; both are non-negative
// integer day counts, zero on a loan with no pause and no grace. The dates are
// plain calendar dates with no clock and no offset, so no time-zone offset is
// hard-coded anywhere in the path.
type DelinquencyRequest struct {
	OverdueSinceDate string `json:"overdue_since_date,omitempty"`
	BusinessDate     string `json:"business_date"`
	PausedDays       int64  `json:"paused_days"`
	GraceDays        int64  `json:"grace_days"`
}

// StatusRequest is the loan-status seam's input: the persisted
// m_loan.loan_status_id value (Fineract's status.id) whose read-back the vector
// pins.
type StatusRequest struct {
	StoredValue int32 `json:"stored_value"`
}

// StatusTransitionRequest is the loan-status-transition seam's input: the status
// the loan is observed in, the event or balance snapshot the state machine is
// asked to act on, and the outstanding facts the snapshot carries. Mode "event"
// dispatches through loan.NextStatus(from, event, facts); mode "balance"
// recomputes through loan.DetermineTransition(from, facts). Event is the
// Fineract LoanEvent constant name the oracle dispatches (e.g.
// "WRITE_OFF_OUTSTANDING"); it is required for mode "event" and must be empty
// for mode "balance". The five fact fields are the loan.Facts snapshot — the
// observed state of the loan's balances, never a balance value — and are the
// input DetermineTransition branches on; an event-mode request reads none of
// them.
type StatusTransitionRequest struct {
	Mode                    string `json:"mode"`
	FromStoredValue         int32  `json:"from_stored_value"`
	Event                   string `json:"event,omitempty"`
	HasOutstanding          bool   `json:"has_outstanding,omitempty"`
	RepaidInFull            bool   `json:"repaid_in_full,omitempty"`
	TotalOverpaidIsPositive bool   `json:"total_overpaid_is_positive,omitempty"`
	TotalOverpaidIsZero     bool   `json:"total_overpaid_is_zero,omitempty"`
	AllChargesPaid          bool   `json:"all_charges_paid,omitempty"`
}

// ChargeLifecycleOperation is one operation applied to a LoanCharge in the
// charge-lifecycle seam. Op is "pay" or "waive". For "pay", AmountMinor is
// the integer minor-unit amount to pay; for "waive" it is ignored.
type ChargeLifecycleOperation struct {
	Op          string `json:"op"`
	AmountMinor string `json:"amount_minor,omitempty"`
}

// ChargeLifecycleRequest is the loan-charge-lifecycle seam's input: the
// charge's amount, whether it is a penalty, and the ordered operations taken
// from the observed transactions.
type ChargeLifecycleRequest struct {
	AmountMinor string                     `json:"amount_minor"`
	Penalty     bool                       `json:"penalty"`
	Operations  []ChargeLifecycleOperation `json:"operations"`
}

// ChargeLifecycleState is the expected state of a LoanCharge after one
// operation (or after creation, at index 0). All money fields are integer
// strings in minor units.
type ChargeLifecycleState struct {
	PaidMinor        string `json:"paid_minor"`
	WaivedMinor      string `json:"waived_minor"`
	OutstandingMinor string `json:"outstanding_minor"`
	Paid             bool   `json:"paid"`
	Waived           bool   `json:"waived"`
}

// TransactionRow is one row of the loan-transaction-balance seam's input: a
// transaction read-back row reduced to the cells the balance derivation reads.
// Type is the row's Fineract transaction_type_enum in code-suffix form —
// "disbursement", "accrual", "repayment" or "waiver", the four type codes the
// committed captures observe on the balance path. AmountMinor is the row's full
// amount; PrincipalMinor is the row's principalPortion, which the read-back
// leaves ABSENT on the observed disbursement, accrual and waiver rows and is
// therefore omitted (zero) there.
type TransactionRow struct {
	Type           string `json:"type"`
	AmountMinor    string `json:"amount_minor"`
	PrincipalMinor string `json:"principal_minor,omitempty"`
}

// JournalEntryLeg is one row of the journal-entry-batch-balance seam's input: a
// journal-entry read-back row reduced to the cells the batch derivation reads.
// TransactionID is the transaction the oracle grouped the leg under (a batch
// with more than one distinct id holds more than one pair). Account is the GL
// account the leg touched, and is what a port that nets same-account legs would
// key on. EntryType is the observed side in code-suffix form — "DEBIT" or
// "CREDIT". AmountMinor is the leg amount, an integer STRING in minor units.
type JournalEntryLeg struct {
	TransactionID string `json:"transaction_id"`
	Account       string `json:"account"`
	EntryType     string `json:"entry_type"`
	AmountMinor   string `json:"amount_minor"`
}

// JournalEntryAccountSideCell is the journal-entry-batch-balance seam's expected
// side for one (transaction_id, account) pair of the request batch. It carries
// the side in its OBSERVED code form ("DEBIT"/"CREDIT") and is the cell a
// swapped-pair port moves while the two totals stay equal.
type JournalEntryAccountSideCell struct {
	TransactionID string `json:"transaction_id"`
	Account       string `json:"account"`
	EntryType     string `json:"entry_type"`
}

// Request is the input the implementation is graded on. It is the union of the
// seams; a vector sets exactly one of the sub-requests.
type Request struct {
	Repayment      *RepaymentRequest `json:"repayment,omitempty"`
	Schedule       *ScheduleRequest  `json:"schedule,omitempty"`
	Disburse       *DisburseRequest  `json:"disburse,omitempty"`
	Summary        *SummaryRequest   `json:"summary,omitempty"`
	Status         *StatusRequest    `json:"status,omitempty"`
	Transactions   []TransactionRow  `json:"transactions,omitempty"`
	JournalEntries []JournalEntryLeg `json:"journal_entries,omitempty"`
	// ScheduleAmortization is the whole-schedule principal-amortization seam's
	// input: the disbursed principal and the observed per-period principalDue
	// components.
	ScheduleAmortization *ScheduleAmortizationRequest `json:"schedule_amortization,omitempty"`
	// Delinquency is the loan-delinquent-days seam's input: the observed
	// overdue-since date and the business date.
	Delinquency *DelinquencyRequest `json:"delinquency,omitempty"`
	// WriteOff is the loan-writeoff-four-bucket seam's input: the observed
	// per-instalment schedule write-off arithmetic consumes.
	WriteOff *WriteOffRequest `json:"write_off,omitempty"`
	// Reversal is the loan-transaction-reversal seam's input: the before
	// read-back legs of one loan transaction and its transaction date.
	Reversal *ReversalRequest `json:"reversal,omitempty"`
	// WriteOffJournal is the loan-writeoff-journal-entries seam's input: the
	// write-off transaction's portions and the product's slot->account mapping.
	WriteOffJournal *WriteOffJournalRequest `json:"write_off_journal,omitempty"`
	// ChargeOffJournal is the loan-chargeoff-journal-entries seam's input: the
	// charge-off transaction's four portions, the loan's fraud flag and the
	// product's slot->account mapping.
	ChargeOffJournal *ChargeOffJournalRequest `json:"charge_off_journal,omitempty"`
	// ChargedOffWriteOffJournal is the
	// loan-chargedoff-writeoff-journal-entries seam's input: the write-off
	// transaction's five portions on a loan already marked charged off, the
	// loan's fraud flag and the product's slot->account mapping.
	ChargedOffWriteOffJournal *ChargedOffWriteOffJournalRequest `json:"charged_off_write_off_journal,omitempty"`
	// RepaymentJournal is the loan-repayment-journal-entries seam's input: the
	// ordinary repayment transaction's five portions on a loan that is NOT
	// charged off and the resolved slot->account mapping (the fund source already
	// resolved through the payment channel).
	RepaymentJournal *RepaymentJournalRequest `json:"repayment_journal,omitempty"`
	// GoodwillCreditJournal is the loan-goodwill-credit-journal-entries seam's
	// input: a GOODWILL CREDIT transaction's five portions on a loan that is NOT
	// charged off, the loan's charged-off state and the slot->account mapping
	// (its five credit slots, its four goodwill debit slots and the resolved fund
	// source the wrong drive debits).
	GoodwillCreditJournal *GoodwillCreditJournalRequest `json:"goodwill_credit_journal,omitempty"`
	// DisbursementJournal is the loan-disbursement-journal-entries seam's input:
	// an observed disbursement transaction's amount and overpayment and the
	// resolved slot->account mapping (the fund source already resolved through the
	// payment channel). The read-back principalPortion is carried only for the
	// registered wrong drive; the correct port derives the principal as amount
	// minus overpayment and never reads it.
	DisbursementJournal *DisbursementJournalRequest `json:"disbursement_journal,omitempty"`
	// ChargeAdjustmentJournal is the loan-charge-adjustment-journal-entries
	// seam's input: a CHARGE ADJUSTMENT transaction's five portions, the loan's
	// charged-off state (which moves the credit side to the charge-off income
	// table), whether the adjusted charge is a penalty (which selects the single
	// debit income account) and the product's slot->account mapping.
	ChargeAdjustmentJournal *ChargeAdjustmentJournalRequest `json:"charge_adjustment_journal,omitempty"`
	// ChargedOffRepaymentJournal is the
	// loan-chargedoff-repayment-journal-entries seam's input: a REPAYMENT
	// transaction's five portions on a loan already marked charged off and the
	// resolved slot->account mapping (the fund source already resolved through
	// the payment channel). There is no transaction-type field.
	ChargedOffRepaymentJournal *ChargedOffRepaymentJournalRequest `json:"charged_off_repayment_journal,omitempty"`
	// InterestPaymentWaiverJournal is the
	// loan-interest-payment-waiver-journal-entries seam's input: an
	// INTEREST_PAYMENT_WAIVER transaction's five portions, the loan's charged-off
	// state and the product's slot->account mapping.
	InterestPaymentWaiverJournal *InterestPaymentWaiverJournalRequest `json:"interest_payment_waiver_journal,omitempty"`
	// CapitalizedIncomeAmortizationJournal is the
	// loan-capitalized-income-amortization-journal-entries seam's input: a
	// CAPITALIZED_INCOME_AMORTIZATION transaction's interest and fee portions, the
	// loan's charged-off / fraud / written-off state and the product's
	// slot->account mapping.
	CapitalizedIncomeAmortizationJournal *CapitalizedIncomeAmortizationJournalRequest `json:"capitalized_income_amortization_journal,omitempty"`
	// ChargedOffMerchantRefundJournal is the
	// loan-chargedoff-merchant-refund-journal-entries seam's input: a
	// MERCHANT-ISSUED REFUND transaction's five portions on a loan already marked
	// charged off and NOT fraud, the fraud flag (which this seam pins false) and
	// the resolved slot->account mapping (the fund source already resolved through
	// the payment channel).
	ChargedOffMerchantRefundJournal *ChargedOffMerchantRefundJournalRequest `json:"charged_off_merchant_refund_journal,omitempty"`
	// AccrualJournal is the loan-accrual-journal-entries seam's input: an
	// ACCRUAL or ACCRUAL_ADJUSTMENT transaction's three portions and the
	// product's resolved slot->account mapping, with the adjustment flag.
	AccrualJournal *AccrualJournalRequest `json:"accrual_journal,omitempty"`
	// ChargebackJournal is the loan-chargeback-journal-entries seam's input: the
	// chargeback transaction's amount and four portions, the loan's charged-off
	// and fraud facts, and the resolved slot->account mapping.
	ChargebackJournal *ChargebackJournalRequest `json:"chargeback_journal,omitempty"`
	// BuyDownFeeJournal is the loan-buy-down-fee-journal-entries seam's input: the
	// buy-down-fee transaction's amount, the loan product's merchantBuyDownFee
	// fact, and the resolved slot->account mapping.
	BuyDownFeeJournal *BuyDownFeeJournalRequest `json:"buy_down_fee_journal,omitempty"`
	// CreditBalanceRefundJournal is the
	// loan-credit-balance-refund-journal-entries seam's input: the refund
	// transaction's principal and overpayment portions, the loan's charged-off
	// and fraud facts, and the resolved slot->account mapping.
	CreditBalanceRefundJournal *CreditBalanceRefundJournalRequest `json:"credit_balance_refund_journal,omitempty"`
	// ChargeLifecycle is the loan-charge-lifecycle seam's input: the charge's
	// amount, penalty flag, and the ordered operations observed.
	ChargeLifecycle *ChargeLifecycleRequest `json:"charge_lifecycle,omitempty"`
	// StatusTransition is the loan-status-transition seam's input: the observed
	// status, the event or balance snapshot, and the fact snapshot.
	StatusTransition *StatusTransitionRequest `json:"status_transition,omitempty"`
}

// Expect is what the oracle produced for the request. For the repayment seam it
// is the allocated buckets and the leftover; for the schedule seam the
// single-period interest; for the disbursement seam the net disbursal amount;
// for the summary seam the derived total outstanding; for the status seam the
// status_code the read-back emitted plus the round-trip stored value; for the
// transaction-balance seam one per-row verdict for each request row. Every
// money field is an integer STRING in minor units.
type Expect struct {
	Allocation        *AllocationMoney `json:"allocation,omitempty"`
	LeftoverMinor     string           `json:"leftover_minor,omitempty"`
	InterestMinor     string           `json:"interest_minor,omitempty"`
	NetDisbursalMinor string           `json:"net_disbursal_minor,omitempty"`
	// SummaryTotalMinor is total_outstanding, derived from the four request
	// buckets, in integer minor-unit STRING form.
	SummaryTotalMinor string `json:"summary_total_minor,omitempty"`
	// StatusCode is the capture's status.code for the request's stored value.
	StatusCode string `json:"status_code,omitempty"`
	// StatusStoredValue is the stored value the decoded status round-trips back
	// to: m_loan.loan_status_id of the enum the port derived from the request's
	// stored value. It must equal request.status.stored_value.
	StatusStoredValue int32 `json:"status_stored_value,omitempty"`
	// TransactionRows is the transaction-balance seam's per-row verdicts, one
	// entry per request.transactions row in order.
	TransactionRows []TransactionBalanceRow `json:"transaction_rows,omitempty"`
	// JournalEntryDebitsMinor and JournalEntryCreditsMinor are the
	// journal-entry-batch seam's two derived totals, each an integer STRING in
	// minor units, summed independently over every leg of the batch.
	JournalEntryDebitsMinor  string `json:"journal_entry_debits_minor,omitempty"`
	JournalEntryCreditsMinor string `json:"journal_entry_credits_minor,omitempty"`
	// JournalEntryAccountSides is the journal-entry-batch seam's per-leg side
	// expectation, one entry per request.journal_entries leg: WHICH account
	// takes WHICH side in WHICH transaction. It is required, and it is the cell
	// a swapped-pair port moves while both totals stay equal.
	JournalEntryAccountSides []JournalEntryAccountSideCell `json:"journal_entry_account_sides,omitempty"`
	// PrincipalSumMinor is the loan-schedule-amortization seam's derived sum of
	// the per-period principal components, an integer STRING in minor units.
	PrincipalSumMinor string `json:"principal_sum_minor,omitempty"`
	// FinalPrincipalBalanceMinor is the loan-schedule-amortization seam's final
	// outstanding principal balance after the schedule is repaid, an integer
	// STRING in minor units. The property "principal amortizes to zero" holds
	// exactly when this is "0".
	FinalPrincipalBalanceMinor string `json:"final_principal_balance_minor,omitempty"`
	// OverdueDays is the loan-delinquent-days seam's derived calendar-day
	// difference between the overdue-since date and the business date, floored
	// at zero, as an integer STRING. It is "0" when the request omits the
	// overdue-since date.
	OverdueDays string `json:"overdue_days,omitempty"`
	// DelinquentDays is the loan-delinquent-days seam's derived delinquent-day
	// count (overdueDays minus paused and grace days, floored at zero), as an
	// integer STRING. The committed corpus observes pause 0 / grace 0, so it
	// equals OverdueDays on every row transcribed.
	DelinquentDays string `json:"delinquent_days,omitempty"`
	// WriteOffAllocation is the loan-writeoff-four-bucket seam's four discharged
	// portions — the write-off transaction's principalPortion, interestPortion,
	// feeChargesPortion and penaltyChargesPortion — each an integer STRING in
	// minor units.
	WriteOffAllocation *AllocationMoney `json:"write_off_allocation,omitempty"`
	// WriteOffTotalMinor is the write-off transaction's amount, an integer
	// STRING in minor units. The four portions sum to it exactly; the sum is
	// the invariant this seam exists to grade.
	WriteOffTotalMinor string `json:"write_off_total_minor,omitempty"`
	// ReversalLegs is the loan-transaction-reversal seam's full after-read-back
	// leg list: the request's original legs unchanged and in order, then one
	// counter-leg per original with the same transaction id, account, amount
	// and transaction date but the OPPOSITE side. Every leg is graded on all
	// six cells; the originals' Reversed flag and the counter-legs' transaction
	// date are the cells the batch totals cannot see.
	ReversalLegs []ReversalLegCell `json:"reversal_legs,omitempty"`
	// WriteOffJournalLegs is the loan-writeoff-journal-entries seam's ordered
	// leg list the write-off posted: one credit per discharged slot (merged by
	// account) in portion order, then ONE debit of the total to the
	// losses-written-off account. Every leg is graded on its transaction id,
	// account, side and amount; the debit's account and the credit/debit split
	// are what discriminate a debit-per-portion or wrong-account port.
	WriteOffJournalLegs []JournalEntryLeg `json:"write_off_journal_legs,omitempty"`
	// ChargeOffJournalLegs is the loan-chargeoff-journal-entries seam's ordered
	// leg list the charge-off posted: one credit per discharged slot (merged by
	// account) in portion order, then every debit in insertion order (merged by
	// account). Every leg is graded on its transaction id, account, side and
	// amount; the principal debit's account (fraud vs ordinary expense) and the
	// credit/debit split are what discriminate a fraud-ignoring or
	// debit-per-portion port.
	ChargeOffJournalLegs []JournalEntryLeg `json:"charge_off_journal_legs,omitempty"`
	// ChargedOffWriteOffJournalLegs is the loan-chargedoff-writeoff-journal-entries
	// seam's ordered leg list the charged-off write-off posted: one credit per
	// reversed slot (merged by account) in portion order, then ONE debit of the
	// total to the losses-written-off account. Every leg is graded on its
	// transaction id, account, side and amount; the principal credit's account
	// (fraud vs ordinary charge-off expense) and the single debit's account and
	// count are what discriminate a fraud-ignoring or fund-source-debiting port.
	ChargedOffWriteOffJournalLegs []JournalEntryLeg `json:"charged_off_write_off_journal_legs,omitempty"`
	// RepaymentJournalLegs is the loan-repayment-journal-entries seam's ordered
	// leg list the ordinary repayment posted: one credit per non-zero portion
	// (merged by account) in portion order, then ONE debit of the total to the
	// resolved fund source. Every leg is graded on its transaction id, account,
	// side and amount; the merged credits' accounts and order, the single debit's
	// account, and the one-debit count are what discriminate a
	// debit-per-portion port.
	RepaymentJournalLegs []JournalEntryLeg `json:"repayment_journal_legs,omitempty"`
	// GoodwillCreditJournalLegs is the loan-goodwill-credit-journal-entries
	// seam's ordered leg list a goodwill credit posted: one credit per non-zero
	// portion (merged by account) in portion order, then one goodwill debit per
	// distinct debit account (merged by account) in the goodwill table's slot
	// order. Every leg is graded on its transaction id, account, side and amount;
	// a port that debits the resolved fund source (a transfer) or the wrong
	// goodwill slot moves an account, and a port that debits per credit moves the
	// count on a multi-credit transaction.
	GoodwillCreditJournalLegs []JournalEntryLeg `json:"goodwill_credit_journal_legs,omitempty"`
	// DisbursementJournalLegs is the loan-disbursement-journal-entries seam's
	// ordered leg list a disbursement posted: a DEBIT LOAN_PORTFOLIO for the
	// principal portion (amount minus overpayment) when > 0, a DEBIT OVERPAYMENT
	// for the overpayment portion when > 0, then ONE CREDIT of the whole amount to
	// the resolved fund source. Every leg is graded on its transaction id,
	// account, side and amount; a port that debits the principal from the
	// read-back principalPortion (0 on every observation) posts NO portfolio debit
	// and moves the count, which is the drive this seam discriminates.
	DisbursementJournalLegs []JournalEntryLeg `json:"disbursement_journal_legs,omitempty"`
	// ChargeAdjustmentJournalLegs is the
	// loan-charge-adjustment-journal-entries seam's ordered leg list a charge
	// adjustment posted: one credit per non-zero portion (merged by account) in
	// portion order — the receivables on a NOT-charged-off loan, the charge-off
	// income table on a charged-off loan — then ONE debit of the total to
	// INCOME_FROM_PENALTIES when the adjusted charge is a penalty, else
	// INCOME_FROM_FEES. Every leg is graded on its transaction id, account, side
	// and amount; a port that posts the not-charged-off credits on a charged-off
	// loan moves the credit accounts, and a port that splits the single debit
	// moves the count.
	ChargeAdjustmentJournalLegs []JournalEntryLeg `json:"charge_adjustment_journal_legs,omitempty"`
	// ChargedOffRepaymentJournalLegs is the
	// loan-chargedoff-repayment-journal-entries seam's ordered leg list a
	// charged-off loan's repayment posted: one credit to INCOME_FROM_RECOVERY
	// MERGING every positive principal, interest, fee and penalty portion (plus a
	// separate overpayment credit when that portion is positive), then ONE debit
	// of the total to the resolved fund source. Every leg is graded on its
	// transaction id, account, side and amount; a port that posts the repayment
	// like an ordinary one moves the credits to the portfolio/receivable accounts
	// and, when two portions merged into one recovery credit, splits them back
	// apart — the account, count and order cells.
	ChargedOffRepaymentJournalLegs []JournalEntryLeg `json:"charged_off_repayment_journal_legs,omitempty"`
	// InterestPaymentWaiverJournalLegs is the
	// loan-interest-payment-waiver-journal-entries seam's ordered leg list an
	// interest-payment waiver posted: one credit per non-zero portion (merged by
	// account) in portion order, then ONE debit of the total to INTEREST_ON_LOANS.
	// Every leg is graded on its transaction id, account, side and amount; the
	// charged-off account switch (the four portfolio/receivable credits collapsing
	// onto one charge-off income account) and the credit/debit split are what
	// discriminate an ignore-charge-off or debit-per-portion port.
	InterestPaymentWaiverJournalLegs []JournalEntryLeg `json:"interest_payment_waiver_journal_legs,omitempty"`
	// CapitalizedIncomeAmortizationJournalLegs is the
	// loan-capitalized-income-amortization-journal-entries seam's ordered leg list
	// a capitalized-income amortization posted: ONE credit of the interest+fee
	// total to the dispatch's income account (income from capitalization, losses
	// written off, charge-off expense or charge-off fraud expense), then ONE debit
	// of the same total to deferred income liability. Every leg is graded on its
	// transaction id, account, side and amount; the loan-state account switch is
	// what discriminates a port that ignores the loan's state.
	CapitalizedIncomeAmortizationJournalLegs []JournalEntryLeg `json:"capitalized_income_amortization_journal_legs,omitempty"`
	// ChargedOffMerchantRefundJournalLegs is the
	// loan-chargedoff-merchant-refund-journal-entries seam's ordered leg list a
	// merchant-issued refund posted on a charged-off loan: one credit per positive
	// portion to its OWN charge-off slot, MERGING portions that resolve to the
	// same account, then ONE debit of the total to the resolved fund source. Every
	// leg is graded on its transaction id, account, side and amount; a port that
	// posts the refund like a charged-off REPAYMENT moves every principal,
	// interest, fee and penalty credit to INCOME_FROM_RECOVERY — the account and
	// count cells.
	ChargedOffMerchantRefundJournalLegs []JournalEntryLeg `json:"charged_off_merchant_refund_journal_legs,omitempty"`
	// AccrualJournalLegs is the loan-accrual-journal-entries seam's ordered leg
	// list an accrual or accrual-adjustment transaction posted: the interest
	// pair (debit first), then the fee pair and the penalty pair (credit first),
	// each only when its portion is positive and each its own pair. Every leg is
	// graded on its transaction id, account, side and amount; the side of a
	// swapped adjustment interest pair, and the fact that the fee and penalty
	// groups never merge, are what discriminate a wrong port.
	AccrualJournalLegs []JournalEntryLeg `json:"accrual_journal_legs,omitempty"`
	// ChargebackJournalLegs is the loan-chargeback-journal-entries seam's ordered
	// leg list the chargeback posted: the amount credit to the fund source, then
	// the overpayment debit, then the principal debit, then the fee debit, then
	// the penalty debit, in posting order; a charged-off loan debits the
	// charge-off expense and charge-off income accounts instead of the portfolio
	// and receivables. Every leg is graded on its transaction id, account, side
	// and amount; the overpayment debit's account, the two-debit order and the
	// charge-off account switch are what discriminate a wrong port.
	ChargebackJournalLegs []JournalEntryLeg `json:"chargeback_journal_legs,omitempty"`
	// BuyDownFeeJournalLegs is the loan-buy-down-fee-journal-entries seam's
	// ordered leg list a buy-down fee posted: ONE debit of the amount to the
	// selected account (buy-down expense on a merchant product, else the resolved
	// fund source), then ONE credit of the amount to deferred income liability.
	// Every leg is graded on its transaction id, account, side and amount; the
	// merchant-selected debit account is what discriminates a port that ignores
	// the merchantBuyDownFee fact.
	BuyDownFeeJournalLegs []JournalEntryLeg `json:"buy_down_fee_journal_legs,omitempty"`
	// CreditBalanceRefundJournalLegs is the
	// loan-credit-balance-refund-journal-entries seam's ordered leg list the
	// refund posted: the principal debit (to the portfolio account, or the
	// charge-off / charge-off-fraud account as the loan's facts select), then the
	// overpayment debit, then the single total credit to the fund source. Every
	// leg is graded on its transaction id, account, side and amount; the
	// principal account switch and the single total credit are what discriminate
	// a wrong port.
	CreditBalanceRefundJournalLegs []JournalEntryLeg `json:"credit_balance_refund_journal_legs,omitempty"`
	// ChargeStates is the loan-charge-lifecycle seam's ordered list of expected
	// states: the created state at index 0, then one state per operation in
	// request.charge_lifecycle.operations, in order.
	ChargeStates []ChargeLifecycleState `json:"charge_states,omitempty"`
	// NextStatusCode is the loan-status-transition seam's expected read-back
	// code for the status the state machine returned (e.g.
	// "loanStatusType.closed.obligations.met").
	NextStatusCode string `json:"next_status_code,omitempty"`
	// NextStatusStoredValue is the stored value the decoded next status
	// round-trips back to (m_loan.loan_status_id), so a port that returns a
	// right-looking code off a wrong ordinal is still caught.
	NextStatusStoredValue int32 `json:"next_status_stored_value,omitempty"`
}

// TransactionBalanceRow is the transaction-balance seam's verdict for one
// transaction row: does the read-back serialise an outstandingLoanBalance cell
// on the row, and what is its derived value. A non-monetary posting (an
// accrual) serialises NO cell — the oracle returns absent, never zero.
type TransactionBalanceRow struct {
	Serialized bool `json:"serialized"`
	// BalanceMinor is the derived balance when Serialized is true. It is empty
	// (absent) on a row the read-back leaves without a balance cell.
	BalanceMinor string `json:"balance_minor,omitempty"`
}

// Vector is one loan golden vector.
type Vector struct {
	Schema       string        `json:"schema"`
	CaseID       string        `json:"case_id"`
	Title        string        `json:"title"`
	Class        VectorClass   `json:"class"`
	Context      string        `json:"context"`
	Note         string        `json:"_note"`
	Oracle       OracleStamp   `json:"oracle"`
	Provenance   Provenance    `json:"provenance"`
	TenantParams *TenantParams `json:"tenant_params"`
	Request      Request       `json:"request"`
	Expect       Expect        `json:"expect"`
	// CapabilitiesRequired states what this vector exercises, for the capability
	// registry's default-deny check.
	CapabilitiesRequired []string `json:"capabilities_required"`
	// GradedAgainst names the registered implementations this vector grades.
	GradedAgainst []string `json:"graded_against"`

	// Path is the store-relative path, set by LoadVector and never decoded.
	Path string `json:"-"`
}

// LoadError is one file that could not be read as a loan vector.
type LoadError = shared.LoadError

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
func RejectFloatTokens(raw []byte) error { return shared.RejectFloatTokens(raw, "loan") }

// DeclaresLoanSchema reports whether raw is a JSON object whose top-level
// "schema" member is exactly SchemaV1.
func DeclaresLoanSchema(raw []byte) bool { return shared.DeclaresSchema(raw, SchemaV1) }

// FileDeclaresLoanSchema is DeclaresLoanSchema over a path.
func FileDeclaresLoanSchema(absPath string) bool {
	return shared.FileDeclaresSchema(absPath, SchemaV1)
}

// LoanFilePaths walks the store root and returns the store-relative paths of
// every file that declares the loan schema, sorted. The paths are DERIVED, not
// listed, so a loan vector added or removed later needs no edit in the caller
// (the loanschedule store census).
func LoanFilePaths(storeRoot string) ([]string, error) {
	return shared.SchemaFilePaths(storeRoot, SchemaV1)
}

// LoadVector reads and strictly decodes one loan vector file: a raw float scan
// first, then a typed decode with unknown fields disallowed.
func LoadVector(absPath, relPath string) (*Vector, error) {
	raw, err := os.ReadFile(absPath)
	if err != nil {
		return nil, err
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var v Vector
	if err := dec.Decode(&v); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	if dec.More() {
		return nil, fmt.Errorf("decode: trailing content after the vector object")
	}
	v.Path = relPath
	return &v, nil
}

var loanID = shared.VectorIdentity[Vector]{
	Context: func(v *Vector) string { return v.Context },
	CaseID:  func(v *Vector) string { return v.CaseID },
	Path:    func(v *Vector) string { return v.Path },
}

// LoadStore walks the store root and loads every loan-schema .json under it.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	return shared.LoadStore[Vector](storeRoot, contextFilter, SchemaV1, "loan", loanID, LoadVector)
}

// DuplicateCaseIDs refuses a loan population carrying one case_id twice.
func DuplicateCaseIDs(vs []*Vector) error {
	return shared.DuplicateCaseIDs[Vector](vs, loanID, "loan")
}

func sortVectors(vs []*Vector) { shared.SortVectors[Vector](vs, loanID) }
