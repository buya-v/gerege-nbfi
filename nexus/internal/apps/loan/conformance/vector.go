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
