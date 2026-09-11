package conformance

import (
	"fmt"
	"math/big"
	"sort"
	"strconv"
	"sync"
	"time"

	"github.com/gerege/nexus/internal/apps/loan"
	shared "github.com/gerege/nexus/internal/conformance"
)

// LoanEvaluator is what a loan implementation must be able to do for this
// harness to grade it. The graded surface is the capture seams:
//
//   - seam loan-repayment-allocation: the four-bucket greedy allocation of a
//     repayment across a single instalment's outstanding buckets, graded by
//     loan.AllocatePayment;
//   - seam loan-schedule-interest: the single-period interest of the
//     discriminating loan, the one cell the MANIFEST records as its rounding
//     surface (HALF_UP vs HALF_EVEN);
//   - seam loan-disbursement: the net disbursal amount, graded by
//     loan.NetDisbursalAmount;
//   - seam loan-summary-outstanding: the summary total outstanding, DERIVED by
//     loan.LoanSummary.TotalOutstanding from the four outstanding buckets;
//   - seam loan-status: the persisted loan-status ordinal decoded by
//     loan.LoanStatusFromStoredValue and its code/round-trip stored value;
//   - seam loan-transaction-balance: the running outstandingLoanBalance column,
//     DERIVED row by row by loan.DeriveOutstandingBalances from the request's
//     posting stream.
type LoanEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]LoanEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a LoanEvaluator available under name.
func Register(name string, e LoanEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("loan conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e LoanEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (LoanEvaluator, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	e, ok := impls[name]
	return e, ok
}

// IsRegisteredWrong reports whether name is a known-wrong implementation.
func IsRegisteredWrong(name string) (string, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	d, ok := wrong[name]
	return d, ok
}

// RegisteredNames lists every registered implementation, wrong ones included.
func RegisteredNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

// CorrectImplementationNames lists the registered implementations that are NOT
// declared wrong.
func CorrectImplementationNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		if _, bad := wrong[n]; !bad {
			out = append(out, n)
		}
	}
	sort.Strings(out)
	return out
}

// mifosOrder is the repayment allocation order of the mifos-standard-strategy:
// penalties, then fees, then interest, then principal, each at the DUE due-type
// (the SEED-L03 repayment had no past-due or in-advance component, so the
// in-advance/past-due buckets are empty and irrelevant to the allocation).
var mifosOrder = []loan.PaymentAllocationType{
	loan.PaymentDuePenalty, loan.PaymentDueFee, loan.PaymentDueInterest, loan.PaymentDuePrincipal,
}

// parseMinorText parses a vector's monetary text field into integer minor units.
// The parse lives in nexus/internal/conformance; this wrapper adapts the shared
// int64 result to the loan MinorUnits type.
func parseMinorText(text string) (loan.MinorUnits, error) {
	n, err := shared.ParseMinorInt(text)
	if err != nil {
		return 0, err
	}
	return loan.MinorUnits(n), nil
}

// goEvaluator is the port-backed implementation.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() LoanEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	switch {
	case req.Repayment != nil:
		return goRepayment(*req.Repayment)
	case req.Schedule != nil:
		return goSchedule(*req.Schedule, roundHalfUp)
	case req.ScheduleAmortization != nil:
		return goScheduleAmortization(*req.ScheduleAmortization)
	case req.Disburse != nil:
		return goDisburse(*req.Disburse)
	case req.Summary != nil:
		return goSummary(*req.Summary)
	case req.Status != nil:
		return goStatus(*req.Status)
	case len(req.Transactions) > 0:
		return goTransactionBalance(req.Transactions)
	case len(req.JournalEntries) > 0:
		return goJournalEntryBatch(req.JournalEntries)
	case req.Delinquency != nil:
		return goDelinquency(*req.Delinquency)
	case req.WriteOff != nil:
		return goWriteOff(*req.WriteOff)
	case req.Reversal != nil:
		return goReversal(*req.Reversal)
	case req.WriteOffJournal != nil:
		return goWriteOffJournal(*req.WriteOffJournal)
	case req.ChargeOffJournal != nil:
		return goChargeOffJournal(*req.ChargeOffJournal)
	case req.ChargedOffWriteOffJournal != nil:
		return goChargedOffWriteOffJournal(*req.ChargedOffWriteOffJournal)
	case req.RepaymentJournal != nil:
		return goRepaymentJournal(*req.RepaymentJournal)
	case req.ChargedOffRepaymentJournal != nil:
		return goChargedOffRepaymentJournal(*req.ChargedOffRepaymentJournal)
	case req.ChargedOffMerchantRefundJournal != nil:
		return goChargedOffMerchantRefundJournal(*req.ChargedOffMerchantRefundJournal)
	case req.AccrualJournal != nil:
		return goAccrualJournal(*req.AccrualJournal)
	case req.ChargebackJournal != nil:
		return goChargebackJournal(*req.ChargebackJournal)
	case req.ChargeLifecycle != nil:
		return goChargeLifecycle(*req.ChargeLifecycle)
	case req.StatusTransition != nil:
		return goStatusTransition(*req.StatusTransition)
	default:
		return Expect{}, fmt.Errorf("loan: request must set exactly one of repayment, schedule, disburse, summary, status, transactions, journal_entries, schedule_amortization, delinquency, write_off, reversal, write_off_journal, charge_off_journal, charged_off_write_off_journal, repayment_journal, charged_off_repayment_journal, charged_off_merchant_refund_journal, accrual_journal, chargeback_journal, charge_lifecycle, status_transition")
	}
}

// transactionPostingType resolves a transaction-balance request row's type token
// (the code suffix of the observed transaction_type_enum) to the loan posting
// type the balance derivation switches on. It is a pure switch, not a lookup
// table, so no mutable package state exists to drift from the captures it pins.
func transactionPostingType(t string) (loan.LoanTransactionType, bool) {
	switch t {
	case "disbursement":
		return loan.TransactionDisbursement, true
	case "accrual":
		return loan.TransactionAccrual, true
	case "repayment":
		return loan.TransactionRepayment, true
	case "waiver":
		return loan.TransactionWaiveInterest, true
	}
	return 0, false
}

// goTransactionBalance derives the per-row outstandingLoanBalance column from
// the request's posting stream via loan.DeriveOutstandingBalances. A row the
// derivation leaves without a balance (an accrual) is serialised WITHOUT the
// balance cell — the oracle returns absent there, never zero.
func goTransactionBalance(rows []TransactionRow) (Expect, error) {
	postings := make([]loan.OutstandingBalancePosting, len(rows))
	for i, tr := range rows {
		typ, ok := transactionPostingType(tr.Type)
		if !ok {
			return Expect{}, fmt.Errorf("loan-transaction-balance: type %q is not transcribed", tr.Type)
		}
		amount, err := parseMinorText(tr.AmountMinor)
		if err != nil {
			return Expect{}, err
		}
		var pp loan.MinorUnits
		if tr.PrincipalMinor != "" {
			pp, err = parseMinorText(tr.PrincipalMinor)
			if err != nil {
				return Expect{}, err
			}
		}
		postings[i] = loan.OutstandingBalancePosting{Type: typ, Amount: amount, PrincipalPortion: pp}
	}
	derived, err := loan.DeriveOutstandingBalances(postings)
	if err != nil {
		return Expect{}, err
	}
	out := make([]TransactionBalanceRow, len(derived))
	for i, r := range derived {
		if !r.Serialized {
			out[i] = TransactionBalanceRow{Serialized: false}
			continue
		}
		out[i] = TransactionBalanceRow{
			Serialized:   true,
			BalanceMinor: strconv.FormatInt(int64(r.BalanceMinor), 10),
		}
	}
	return Expect{TransactionRows: out}, nil
}

// journalEntrySide resolves a journal-entry leg's observed entry_type value code
// to the loan side the batch derivation switches on. It is a pure switch, not a
// lookup table, so no mutable package state exists to drift from the captures it
// pins.
func journalEntrySide(t string) (loan.JournalEntrySide, bool) {
	switch t {
	case "DEBIT":
		return loan.JournalEntryDebit, true
	case "CREDIT":
		return loan.JournalEntryCredit, true
	}
	return loan.JournalEntrySideUnknown, false
}

// journalEntrySideCode renders a parsed side back in the observed code form for
// an account-side cell. It returns "" for the unknown side so a leg that somehow
// escaped journalEntrySide's refusal fails visibly rather than defaulting to a
// side the capture never showed.
func journalEntrySideCode(s loan.JournalEntrySide) string {
	switch s {
	case loan.JournalEntryDebit:
		return "DEBIT"
	case loan.JournalEntryCredit:
		return "CREDIT"
	}
	return ""
}

// flipJournalEntrySide reverses the two observed sides. It is the wrong-port
// operation the two totals cannot see when applied to BOTH legs of one balanced
// pair: each side keeps the same sum, so the batch still "balances".
func flipJournalEntrySide(s loan.JournalEntrySide) loan.JournalEntrySide {
	if s == loan.JournalEntryDebit {
		return loan.JournalEntryCredit
	}
	return loan.JournalEntryDebit
}

// goJournalEntryBatch derives the debit and credit totals of a loan-produced
// journal-entry batch by summing EVERY leg on its observed side, via
// loan.SumJournalEntryBatch. The totals are independent sums, never a netting
// of the two same-account legs and never a truncation after the first pair, so
// the two cells pin the multi-pair batch balance a single-pair read-back cannot.
func goJournalEntryBatch(legs []JournalEntryLeg) (Expect, error) {
	parsed := make([]loan.JournalEntryLeg, len(legs))
	for i, leg := range legs {
		side, ok := journalEntrySide(leg.EntryType)
		if !ok {
			return Expect{}, fmt.Errorf("loan-journal-entry-batch: entry_type %q is not transcribed", leg.EntryType)
		}
		amount, err := parseMinorText(leg.AmountMinor)
		if err != nil {
			return Expect{}, err
		}
		parsed[i] = loan.JournalEntryLeg{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			Side:          side,
			Amount:        amount,
		}
	}
	totals, err := loan.SumJournalEntryBatch(parsed)
	if err != nil {
		return Expect{}, err
	}
	sides, err := loan.JournalEntryAccountSides(parsed)
	if err != nil {
		return Expect{}, err
	}
	cells := make([]JournalEntryAccountSideCell, len(sides))
	for i, s := range sides {
		cells[i] = JournalEntryAccountSideCell{
			TransactionID: s.TransactionID,
			Account:       s.Account,
			EntryType:     s.Side,
		}
	}
	return Expect{
		JournalEntryDebitsMinor:  strconv.FormatInt(int64(totals.Debits), 10),
		JournalEntryCreditsMinor: strconv.FormatInt(int64(totals.Credits), 10),
		JournalEntryAccountSides: cells,
	}, nil
}

// goReversal ports the loan-transaction-reversal seam: it parses the before
// read-back legs of ONE loan transaction, runs the append-only reversal rule
// (loan.ReverseLoanTransactionJournalEntries), and renders the full
// after-read-back leg list — originals as they were, then the counter-legs.
// Every original is parsed from the request (its date is the reversed
// transaction's date) and every counter-leg comes from the port, so a defect in
// the rule is visible here and nowhere else.
func goReversal(r ReversalRequest) (Expect, error) {
	legs := make([]loan.JournalEntryLeg, len(r.JournalEntries))
	for i, leg := range r.JournalEntries {
		side, ok := journalEntrySide(leg.EntryType)
		if !ok {
			return Expect{}, fmt.Errorf("loan-transaction-reversal: entry_type %q is not transcribed", leg.EntryType)
		}
		amount, err := parseMinorText(leg.AmountMinor)
		if err != nil {
			return Expect{}, err
		}
		legs[i] = loan.JournalEntryLeg{
			TransactionID:   leg.TransactionID,
			Account:         leg.Account,
			Side:            side,
			Amount:          amount,
			TransactionDate: r.TransactionDate,
			Reversed:        false,
		}
	}
	out, err := loan.ReverseLoanTransactionJournalEntries(legs, r.TransactionDate)
	if err != nil {
		return Expect{}, err
	}
	cells := make([]ReversalLegCell, len(out))
	for i, leg := range out {
		cells[i] = ReversalLegCell{
			TransactionID:   leg.TransactionID,
			Account:         leg.Account,
			EntryType:       journalEntrySideCode(leg.Side),
			AmountMinor:     strconv.FormatInt(int64(leg.Amount), 10),
			TransactionDate: leg.TransactionDate,
			Reversed:        leg.Reversed,
		}
	}
	return Expect{ReversalLegs: cells}, nil
}

func goRepayment(r RepaymentRequest) (Expect, error) {
	penalty, err := parseMinorText(r.Outstanding.Penalty)
	if err != nil {
		return Expect{}, err
	}
	fee, err := parseMinorText(r.Outstanding.Fee)
	if err != nil {
		return Expect{}, err
	}
	interest, err := parseMinorText(r.Outstanding.Interest)
	if err != nil {
		return Expect{}, err
	}
	principal, err := parseMinorText(r.Outstanding.Principal)
	if err != nil {
		return Expect{}, err
	}
	amount, err := parseMinorText(r.AmountMinor)
	if err != nil {
		return Expect{}, err
	}
	outstanding := loan.Allocation{Penalty: penalty, Fee: fee, Interest: interest, Principal: principal}
	alloc, leftover := loan.AllocatePayment(outstanding, amount, mifosOrder)
	return Expect{
		Allocation: &AllocationMoney{
			Penalty:   strconv.FormatInt(int64(alloc.Penalty), 10),
			Fee:       strconv.FormatInt(int64(alloc.Fee), 10),
			Interest:  strconv.FormatInt(int64(alloc.Interest), 10),
			Principal: strconv.FormatInt(int64(alloc.Principal), 10),
		},
		LeftoverMinor: strconv.FormatInt(int64(leftover), 10),
	}, nil
}

func goSchedule(s ScheduleRequest, round func(numerator, denominator *big.Int) int64) (Expect, error) {
	principal, err := parseMinorText(s.PrincipalMinor)
	if err != nil {
		return Expect{}, err
	}
	interest := scheduleInterestMinor(int64(principal), s.RatePerAnnumPct, s.DaysInMonth, s.DaysInYear, round)
	return Expect{InterestMinor: strconv.FormatInt(interest, 10)}, nil
}

func goDisburse(d DisburseRequest) (Expect, error) {
	approved, err := parseMinorText(d.ApprovedPrincipalMinor)
	if err != nil {
		return Expect{}, err
	}
	charges, err := parseMinorText(d.ChargesDueAtDisbursementMinor)
	if err != nil {
		return Expect{}, err
	}
	net := loan.NetDisbursalAmount(approved, charges)
	return Expect{NetDisbursalMinor: strconv.FormatInt(int64(net), 10)}, nil
}

// goSummary derives the summary's total outstanding from the four outstanding
// buckets a capture's "summary" block read back, via
// loan.LoanSummary.TotalOutstanding. The buckets are the authority and the
// total is DERIVED from them (the derive-don't-store ruling: Fineract persists
// total_outstanding_derived, the port keeps the decomposition and derives the
// total).
func goSummary(s SummaryRequest) (Expect, error) {
	principal, err := parseMinorText(s.PrincipalOutstanding)
	if err != nil {
		return Expect{}, err
	}
	interest, err := parseMinorText(s.InterestOutstanding)
	if err != nil {
		return Expect{}, err
	}
	fee, err := parseMinorText(s.FeeOutstanding)
	if err != nil {
		return Expect{}, err
	}
	penalty, err := parseMinorText(s.PenaltyOutstanding)
	if err != nil {
		return Expect{}, err
	}
	total := loan.LoanSummary{
		PrincipalOutstanding:      principal,
		InterestOutstanding:       interest,
		FeeChargesOutstanding:     fee,
		PenaltyChargesOutstanding: penalty,
	}.TotalOutstanding()
	return Expect{SummaryTotalMinor: strconv.FormatInt(int64(total), 10)}, nil
}

// goStatus decodes a persisted m_loan.loan_status_id value and exposes the
// read-back the capture serialised: the enum's i18n code and the stored value
// the decoded status round-trips to (which must equal the request's stored
// value — that round trip is what pins the ordinal, not the Go enum's
// position).
func goStatus(s StatusRequest) (Expect, error) {
	st, ok := loan.LoanStatusFromStoredValue(s.StoredValue)
	if !ok {
		return Expect{}, fmt.Errorf("loan-status: stored value %d is not a legal loan status", s.StoredValue)
	}
	return Expect{StatusCode: st.Code(), StatusStoredValue: st.StoredValue()}, nil
}

// statusTransitionModeEvent dispatches the observed event through
// loan.NextStatus; statusTransitionModeBalance recomputes from the facts through
// loan.DetermineTransition. The two are the two halves of the oracle's
// DefaultLoanLifecycleStateMachine the committed transitions exercise.
const (
	statusTransitionModeEvent   = "event"
	statusTransitionModeBalance = "balance"
)

// statusTransitionFacts converts a request's observed fact snapshot into the
// loan.Facts the state machine reads. The five fields are predicates over the
// loan's balances, derived by the caller from the read-back; none is a balance
// value.
func statusTransitionFacts(s StatusTransitionRequest) loan.Facts {
	return loan.Facts{
		HasOutstanding:          s.HasOutstanding,
		RepaidInFull:            s.RepaidInFull,
		TotalOverpaidIsPositive: s.TotalOverpaidIsPositive,
		TotalOverpaidIsZero:     s.TotalOverpaidIsZero,
		AllChargesPaid:          s.AllChargesPaid,
	}
}

// statusTransitionExpect renders the status the state machine returned: the
// read-back code plus the stored value it round-trips to. Both are read off the
// enum the port itself decoded; no status field is assigned.
func statusTransitionExpect(st loan.LoanStatus) Expect {
	return Expect{NextStatusCode: st.Code(), NextStatusStoredValue: st.StoredValue()}
}

// loanEventFromName resolves the observed Fineract LoanEvent constant name to
// the port's event. loanEventName has no exported reverse, and the observed
// vocabulary is deliberately narrow — only the events the committed captures
// dispatch. It is a pure switch, not a lookup table, so no mutable package state
// exists to drift from the captures it pins.
func loanEventFromName(name string) (loan.LoanEvent, bool) {
	switch name {
	case "LOAN_CREATED":
		return loan.EventLoanCreated, true
	case "LOAN_APPROVED":
		return loan.EventLoanApproved, true
	case "LOAN_DISBURSED":
		return loan.EventLoanDisbursed, true
	case "WRITE_OFF_OUTSTANDING":
		return loan.EventWriteOffOutstanding, true
	}
	return 0, false
}

// goStatusTransition runs one observed lifecycle transition through the port.
// Mode "event" dispatches (from, event); mode "balance" recomputes the status
// from the fact snapshot. A transition the oracle leaves unmoved returns the
// unchanged status, exactly as NextStatus/DetermineTransition do.
func goStatusTransition(s StatusTransitionRequest) (Expect, error) {
	from, ok := loan.LoanStatusFromStoredValue(s.FromStoredValue)
	if !ok {
		return Expect{}, fmt.Errorf("loan-status-transition: stored value %d is not a legal loan status", s.FromStoredValue)
	}
	facts := statusTransitionFacts(s)
	switch s.Mode {
	case statusTransitionModeEvent:
		ev, ok := loanEventFromName(s.Event)
		if !ok {
			return Expect{}, fmt.Errorf("loan-status-transition: event %q is not an observed loan event", s.Event)
		}
		next, _ := loan.NextStatus(from, ev, facts)
		return statusTransitionExpect(next), nil
	case statusTransitionModeBalance:
		return statusTransitionExpect(loan.DetermineTransition(from, facts).Status), nil
	default:
		return Expect{}, fmt.Errorf("loan-status-transition: mode %q is neither %q nor %q", s.Mode, statusTransitionModeEvent, statusTransitionModeBalance)
	}
}

// scheduleInterestMinor ports the single-period interest of the MANIFEST's
// discriminating loan: interest = round(principal * ratePct * daysInMonth,
// 100 * daysInYear), the HALF_UP instance of
// interest = principal * (ratePct/100) * (daysInMonth/daysInYear).
//
// The loan slice does NOT own schedule generation (the loanschedule context
// does); this is the ONE cell the MANIFEST records as the loan context's
// discriminating rounding surface, not a port of the whole amortisation.
// The numerator is computed in big.Int so the rounding is exact for any
// captured magnitude, not merely the seed's.
func scheduleInterestMinor(principal, ratePct, daysInMonth, daysInYear int64, round func(numerator, denominator *big.Int) int64) int64 {
	num := new(big.Int).Mul(big.NewInt(principal), big.NewInt(ratePct))
	num.Mul(num, big.NewInt(daysInMonth))
	den := new(big.Int).Mul(big.NewInt(100), big.NewInt(daysInYear))
	return round(num, den)
}

// roundHalfUp rounds a non-negative ratio to the nearest integer, half away
// from zero (the tenant's HALF_UP rounding mode, ordinal 4).
func roundHalfUp(num, den *big.Int) int64 {
	q, r := new(big.Int).QuoRem(num, den, new(big.Int))
	if new(big.Int).Lsh(r, 1).Cmp(den) >= 0 {
		q.Add(q, big.NewInt(1))
	}
	return q.Int64()
}

// roundHalfEven rounds a non-negative ratio to the nearest integer, half to
// even (banker's rounding). It exists ONLY to make the discriminating cell go
// red: the oracle posted 1000.51 under HALF_UP where HALF_EVEN would have
// posted 1000.50.
func roundHalfEven(num, den *big.Int) int64 {
	q, r := new(big.Int).QuoRem(num, den, new(big.Int))
	twice := new(big.Int).Lsh(r, 1)
	switch cmp := twice.Cmp(den); {
	case cmp > 0:
		q.Add(q, big.NewInt(1))
	case cmp == 0 && q.Bit(0) == 1:
		q.Add(q, big.NewInt(1))
	}
	return q.Int64()
}

// parsePrincipalComponents parses a vector's per-period principal component
// strings into integer minor units. A component carrying sub-minor significance
// (a decimal point) is refused by ParseMinorInt, never rounded: G-19 / DEC-2
// predicate G-08 refuse a residue rather than vector one.
func parsePrincipalComponents(texts []string) ([]loan.MinorUnits, error) {
	out := make([]loan.MinorUnits, len(texts))
	for i, s := range texts {
		v, err := parseMinorText(s)
		if err != nil {
			return nil, fmt.Errorf("principal_components_minor[%d]: %w", i, err)
		}
		out[i] = v
	}
	return out, nil
}

// goScheduleAmortization ports the whole-schedule principal-amortization seam:
// it sums the observed per-period principal components and derives the final
// outstanding principal balance by rolling the disbursed principal down by each
// component in period order (derive-don't-store, I-3).
func goScheduleAmortization(r ScheduleAmortizationRequest) (Expect, error) {
	disbursed, err := parseMinorText(r.PrincipalDisbursedMinor)
	if err != nil {
		return Expect{}, err
	}
	components, err := parsePrincipalComponents(r.PrincipalComponentsMinor)
	if err != nil {
		return Expect{}, err
	}
	am := loan.DerivePrincipalAmortization(disbursed, components)
	return Expect{
		PrincipalSumMinor:          strconv.FormatInt(int64(am.PrincipalSum), 10),
		FinalPrincipalBalanceMinor: strconv.FormatInt(int64(am.FinalBalance), 10),
	}, nil
}

// civilDateLayout is the calendar-date wire form every delinquency request
// carries. A bare calendar date has no clock and no offset, so parsing it never
// hard-codes a time-zone offset: the day-count is taken over the civil dates
// themselves.
const civilDateLayout = "2006-01-02"

// goDelinquency ports the loan-delinquent-days seam through the port's own
// arithmetic: loan.OverdueDays derives the calendar-day difference between the
// overdue-since date and the business date (floored at zero), and
// loan.DelinquentDays subtracts the requested paused and grace days (both zero
// on every committed row that carries no pause and no grace, so the two cells
// agree there). An ABSENT overdue-since date means the read-back showed no
// overdue date, and both counts are zero — never an error and never a
// days-since-epoch value.
func goDelinquency(r DelinquencyRequest) (Expect, error) {
	business, err := time.Parse(civilDateLayout, r.BusinessDate)
	if err != nil {
		return Expect{}, fmt.Errorf("loan-delinquent-days: business_date %q is not a civil date: %w", r.BusinessDate, err)
	}
	var overdue int64
	if r.OverdueSinceDate != "" {
		since, err := time.Parse(civilDateLayout, r.OverdueSinceDate)
		if err != nil {
			return Expect{}, fmt.Errorf("loan-delinquent-days: overdue_since_date %q is not a civil date: %w", r.OverdueSinceDate, err)
		}
		overdue = loan.OverdueDays(since, business)
	}
	delinquent := loan.DelinquentDays(overdue, r.PausedDays, r.GraceDays)
	return Expect{
		OverdueDays:    strconv.FormatInt(overdue, 10),
		DelinquentDays: strconv.FormatInt(delinquent, 10),
	}, nil
}

// goWriteOff ports the loan-writeoff-four-bucket seam: it reduces the observed
// repayment schedule to loan.WriteOffInstallment rows and runs the port's own
// loan.WriteOffOutstanding, which sums each of the four outstanding buckets
// across every instalment whose obligations are NOT met. The four returned
// buckets are the write-off transaction's portions; their sum is its amount.
// Every cell is an integer STRING in minor units — no float enters the path.
func goWriteOff(r WriteOffRequest) (Expect, error) {
	installments, err := writeOffInstallmentsFromRequest(r)
	if err != nil {
		return Expect{}, err
	}
	return writeOffExpect(loan.WriteOffOutstanding(installments)), nil
}

// writeOffInstallmentsFromRequest reduces the observed per-instalment schedule
// to the port's input rows. Every monetary cell is an integer STRING in minor
// units, so no float enters the path.
func writeOffInstallmentsFromRequest(r WriteOffRequest) ([]loan.WriteOffInstallment, error) {
	installments := make([]loan.WriteOffInstallment, len(r.Installments))
	for i, in := range r.Installments {
		principal, err := parseMinorText(in.PrincipalOutstandingMinor)
		if err != nil {
			return nil, err
		}
		interest, err := parseMinorText(in.InterestOutstandingMinor)
		if err != nil {
			return nil, err
		}
		fee, err := parseMinorText(in.FeeOutstandingMinor)
		if err != nil {
			return nil, err
		}
		penalty, err := parseMinorText(in.PenaltyOutstandingMinor)
		if err != nil {
			return nil, err
		}
		installments[i] = loan.WriteOffInstallment{
			PrincipalOutstanding: principal,
			InterestOutstanding:  interest,
			FeeOutstanding:       fee,
			PenaltyOutstanding:   penalty,
			ObligationsMet:       in.ObligationsMet,
		}
	}
	return installments, nil
}

// writeOffExpect renders a write-off allocation as the seam's expected cells:
// the four discharged portions and their sum, the write-off amount.
func writeOffExpect(alloc loan.Allocation) Expect {
	return Expect{
		WriteOffAllocation: &AllocationMoney{
			Principal: strconv.FormatInt(int64(alloc.Principal), 10),
			Interest:  strconv.FormatInt(int64(alloc.Interest), 10),
			Fee:       strconv.FormatInt(int64(alloc.Fee), 10),
			Penalty:   strconv.FormatInt(int64(alloc.Penalty), 10),
		},
		WriteOffTotalMinor: strconv.FormatInt(int64(alloc.Total()), 10),
	}
}

// writeOffWrongMode selects which deliberately-wrong discharge to run. Every
// mode delegates every non-write-off request to the correct port, so each drive
// goes red ONLY on the write-off vector (vector isolation).
type writeOffWrongMode int

const (
	// wrongWriteOffPrincipalOnly discharges only the principal bucket, as a
	// port that reads the write-off as a pure principal charge-off does. On the
	// pinned loan-11 schedule it reads 10000000/0/0/0 and 6618553 short.
	wrongWriteOffPrincipalOnly writeOffWrongMode = iota
	// wrongWriteOffPrincipalAndInterest discharges the principal and interest
	// buckets but drops both charge buckets, the fee/penalty blind spot.
	wrongWriteOffPrincipalAndInterest
	// wrongWriteOffDropsFee discharges principal, interest and penalty but not
	// the fee bucket, so the pinned fee 10000 falls out of the total.
	wrongWriteOffDropsFee
	// wrongWriteOffDropsPenalty discharges principal, interest and fee but not
	// the penalty bucket, so the pinned penalty 5700 falls out of the total.
	wrongWriteOffDropsPenalty
	// wrongWriteOffSwapsFeeAndPenalty discharges all four buckets but assigns
	// the fee outstanding to the penalty portion and vice versa. The total is
	// unchanged (10000000+661853+10000+5700 = 10677553), so only the two
	// bucket cells move — the swap the distinct fee (10000) and penalty (5700)
	// exist to catch.
	wrongWriteOffSwapsFeeAndPenalty
)

// wrongWriteOffEvaluator is a DELIBERATELY WRONG implementation of the
// loan-writeoff-four-bucket seam, parameterised by which discharge defect it
// commits.
type wrongWriteOffEvaluator struct {
	goEvaluator
	mode writeOffWrongMode
}

func (w wrongWriteOffEvaluator) Evaluate(req Request) (Expect, error) {
	if req.WriteOff != nil {
		return wrongWriteOff(*req.WriteOff, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongWriteOff runs the correct discharge and then applies one defect, so each
// drive differs from the port on exactly the cells its defect moves.
func wrongWriteOff(r WriteOffRequest, mode writeOffWrongMode) (Expect, error) {
	installments, err := writeOffInstallmentsFromRequest(r)
	if err != nil {
		return Expect{}, err
	}
	return writeOffExpect(defectWriteOff(loan.WriteOffOutstanding(installments), mode)), nil
}

// defectWriteOff applies a write-off discharge defect to a correct allocation.
func defectWriteOff(a loan.Allocation, mode writeOffWrongMode) loan.Allocation {
	switch mode {
	case wrongWriteOffPrincipalOnly:
		return loan.Allocation{Principal: a.Principal}
	case wrongWriteOffPrincipalAndInterest:
		return loan.Allocation{Principal: a.Principal, Interest: a.Interest}
	case wrongWriteOffDropsFee:
		return loan.Allocation{Principal: a.Principal, Interest: a.Interest, Penalty: a.Penalty}
	case wrongWriteOffDropsPenalty:
		return loan.Allocation{Principal: a.Principal, Interest: a.Interest, Fee: a.Fee}
	case wrongWriteOffSwapsFeeAndPenalty:
		return loan.Allocation{Principal: a.Principal, Interest: a.Interest, Fee: a.Penalty, Penalty: a.Fee}
	}
	return a
}

// goWriteOffJournal ports the loan-writeoff-journal-entries seam: it reduces the
// request's five portions and slot->account mapping to loan.WriteOffPortions and
// loan.WriteOffAccountMapping and runs the port's own
// loan.CreateWriteOffJournalEntryLegs. Every monetary cell is an integer minor
// unit; the mapping is the product's observed accountingMappings, never
// invented.
func goWriteOffJournal(r WriteOffJournalRequest) (Expect, error) {
	portions, err := writeOffPortionsFromRequest(r.Portions)
	if err != nil {
		return Expect{}, err
	}
	legs, err := loan.CreateWriteOffJournalEntryLegs(r.TransactionID, portions, loan.WriteOffAccountMapping{
		LoanPortfolio:       r.Accounts.LoanPortfolio,
		InterestReceivable:  r.Accounts.InterestReceivable,
		FeesReceivable:      r.Accounts.FeesReceivable,
		PenaltiesReceivable: r.Accounts.PenaltiesReceivable,
		Overpayment:         r.Accounts.Overpayment,
		LossesWrittenOff:    r.Accounts.LossesWrittenOff,
	})
	if err != nil {
		return Expect{}, err
	}
	return writeOffJournalLegsExpect(legs), nil
}

// writeOffPortionsFromRequest reduces the request's per-slot money strings to
// the port's integer-minor-unit portions. Overpayment is optional (absent on
// the committed loan-11 write-off, so omitted); every other slot is required.
func writeOffPortionsFromRequest(p WriteOffPortionsMoney) (loan.WriteOffPortions, error) {
	var out loan.WriteOffPortions
	var err error
	if out.Principal, err = parseMinorText(p.Principal); err != nil {
		return loan.WriteOffPortions{}, err
	}
	if out.Interest, err = parseMinorText(p.Interest); err != nil {
		return loan.WriteOffPortions{}, err
	}
	if out.Fee, err = parseMinorText(p.Fee); err != nil {
		return loan.WriteOffPortions{}, err
	}
	if out.Penalty, err = parseMinorText(p.Penalty); err != nil {
		return loan.WriteOffPortions{}, err
	}
	if p.Overpayment != "" {
		if out.Overpayment, err = parseMinorText(p.Overpayment); err != nil {
			return loan.WriteOffPortions{}, err
		}
	}
	return out, nil
}

// writeOffJournalLegsExpect renders the port's ordered legs as the seam's
// ordered leg cells. Every money cell is an integer STRING in minor units; a
// leg whose side is somehow unknown renders an empty entry_type rather than
// defaulting to a side the capture never showed.
func writeOffJournalLegsExpect(legs []loan.JournalEntryLeg) Expect {
	out := make([]JournalEntryLeg, len(legs))
	for i, leg := range legs {
		out[i] = JournalEntryLeg{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			EntryType:     journalEntrySideCode(leg.Side),
			AmountMinor:   strconv.FormatInt(int64(leg.Amount), 10),
		}
	}
	if out == nil {
		out = []JournalEntryLeg{}
	}
	return Expect{WriteOffJournalLegs: out}
}

// goChargeOffJournal ports the loan-chargeoff-journal-entries seam: it reduces
// the request's four portions, fraud flag and slot->account mapping to
// loan.ChargeOffPortions and loan.ChargeOffAccountMapping and runs the port's
// own loan.CreateChargeOffJournalEntryLegs. Every monetary cell is an integer
// minor unit; the mapping is the product's observed accountingMappings, never
// invented. The charge-off-reason branch is not observed, so the port refuses a
// non-empty reason mapping.
func goChargeOffJournal(r ChargeOffJournalRequest) (Expect, error) {
	portions, err := chargeOffPortionsFromRequest(r.Portions)
	if err != nil {
		return Expect{}, err
	}
	legs, err := loan.CreateChargeOffJournalEntryLegs(r.TransactionID, portions, r.Fraud, loan.ChargeOffAccountMapping{
		LoanPortfolio:               r.Accounts.LoanPortfolio,
		InterestReceivable:          r.Accounts.InterestReceivable,
		FeesReceivable:              r.Accounts.FeesReceivable,
		PenaltiesReceivable:         r.Accounts.PenaltiesReceivable,
		ChargeOffExpense:            r.Accounts.ChargeOffExpense,
		ChargeOffFraudExpense:       r.Accounts.ChargeOffFraudExpense,
		IncomeFromChargeOffInterest: r.Accounts.IncomeFromChargeOffInterest,
		IncomeFromChargeOffFees:     r.Accounts.IncomeFromChargeOffFees,
		IncomeFromChargeOffPenalty:  r.Accounts.IncomeFromChargeOffPenalty,
		ChargeOffReason:             r.Accounts.ChargeOffReason,
	})
	if err != nil {
		return Expect{}, err
	}
	return chargeOffJournalLegsExpect(legs), nil
}

// chargeOffPortionsFromRequest reduces the request's per-slot money strings to
// the port's integer-minor-unit portions. Every slot is required; an omitted
// slot is zero.
func chargeOffPortionsFromRequest(p ChargeOffPortionsMoney) (loan.ChargeOffPortions, error) {
	var out loan.ChargeOffPortions
	var err error
	if out.Principal, err = parseMinorText(p.Principal); err != nil {
		return loan.ChargeOffPortions{}, err
	}
	if out.Interest, err = parseMinorText(p.Interest); err != nil {
		return loan.ChargeOffPortions{}, err
	}
	if out.Fee, err = parseMinorText(p.Fee); err != nil {
		return loan.ChargeOffPortions{}, err
	}
	if out.Penalty, err = parseMinorText(p.Penalty); err != nil {
		return loan.ChargeOffPortions{}, err
	}
	return out, nil
}

// chargeOffJournalLegsExpect renders the port's ordered legs as the seam's
// ordered leg cells. Every money cell is an integer STRING in minor units; a
// leg whose side is somehow unknown renders an empty entry_type rather than
// defaulting to a side the capture never showed.
func chargeOffJournalLegsExpect(legs []loan.JournalEntryLeg) Expect {
	out := make([]JournalEntryLeg, len(legs))
	for i, leg := range legs {
		out[i] = JournalEntryLeg{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			EntryType:     journalEntrySideCode(leg.Side),
			AmountMinor:   strconv.FormatInt(int64(leg.Amount), 10),
		}
	}
	if out == nil {
		out = []JournalEntryLeg{}
	}
	return Expect{ChargeOffJournalLegs: out}
}

// goChargedOffWriteOffJournal ports the
// loan-chargedoff-writeoff-journal-entries seam: it reduces the request's five
// portions, fraud flag and slot->account mapping to
// loan.ChargedOffWriteOffPortions and loan.ChargedOffWriteOffAccountMapping and
// runs the port's own loan.CreateChargedOffWriteOffJournalEntryLegs. Every
// monetary cell is an integer minor unit; the mapping is the product's observed
// accountingMappings, never invented. The fund-source slot the processor
// resolves but never posts is deliberately not carried into the port.
func goChargedOffWriteOffJournal(r ChargedOffWriteOffJournalRequest) (Expect, error) {
	portions, err := chargedOffWriteOffPortionsFromRequest(r.Portions)
	if err != nil {
		return Expect{}, err
	}
	legs, err := loan.CreateChargedOffWriteOffJournalEntryLegs(r.TransactionID, portions, r.Fraud, loan.ChargedOffWriteOffAccountMapping{
		ChargeOffExpense:            r.Accounts.ChargeOffExpense,
		ChargeOffFraudExpense:       r.Accounts.ChargeOffFraudExpense,
		IncomeFromChargeOffInterest: r.Accounts.IncomeFromChargeOffInterest,
		IncomeFromChargeOffFees:     r.Accounts.IncomeFromChargeOffFees,
		IncomeFromChargeOffPenalty:  r.Accounts.IncomeFromChargeOffPenalty,
		Overpayment:                 r.Accounts.Overpayment,
		LossesWrittenOff:            r.Accounts.LossesWrittenOff,
	})
	if err != nil {
		return Expect{}, err
	}
	return chargedOffWriteOffJournalLegsExpect(legs), nil
}

// chargedOffWriteOffPortionsFromRequest reduces the request's per-slot money
// strings to the port's integer-minor-unit portions. Overpayment is optional
// (absent on every observed charged-off write-off, so omitted); every other slot
// is required.
func chargedOffWriteOffPortionsFromRequest(p ChargedOffWriteOffPortionsMoney) (loan.ChargedOffWriteOffPortions, error) {
	var out loan.ChargedOffWriteOffPortions
	var err error
	if out.Principal, err = parseMinorText(p.Principal); err != nil {
		return loan.ChargedOffWriteOffPortions{}, err
	}
	if out.Interest, err = parseMinorText(p.Interest); err != nil {
		return loan.ChargedOffWriteOffPortions{}, err
	}
	if out.Fee, err = parseMinorText(p.Fee); err != nil {
		return loan.ChargedOffWriteOffPortions{}, err
	}
	if out.Penalty, err = parseMinorText(p.Penalty); err != nil {
		return loan.ChargedOffWriteOffPortions{}, err
	}
	if p.Overpayment != "" {
		if out.Overpayment, err = parseMinorText(p.Overpayment); err != nil {
			return loan.ChargedOffWriteOffPortions{}, err
		}
	}
	return out, nil
}

// chargedOffWriteOffJournalLegsExpect renders the port's ordered legs as the
// seam's ordered leg cells. Every money cell is an integer STRING in minor
// units; a leg whose side is somehow unknown renders an empty entry_type rather
// than defaulting to a side the capture never showed.
func chargedOffWriteOffJournalLegsExpect(legs []loan.JournalEntryLeg) Expect {
	out := make([]JournalEntryLeg, len(legs))
	for i, leg := range legs {
		out[i] = JournalEntryLeg{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			EntryType:     journalEntrySideCode(leg.Side),
			AmountMinor:   strconv.FormatInt(int64(leg.Amount), 10),
		}
	}
	if out == nil {
		out = []JournalEntryLeg{}
	}
	return Expect{ChargedOffWriteOffJournalLegs: out}
}

// goRepaymentJournal ports the loan-repayment-journal-entries seam: it reduces
// the request's five portions and resolved slot->account mapping to
// loan.RepaymentPortions and loan.RepaymentAccountMapping and runs the port's
// own loan.CreateRepaymentJournalEntryLegs. Every monetary cell is an integer
// minor unit; the mapping is the product's observed accountingMappings with the
// fund source resolved through the payment channel, never invented.
func goRepaymentJournal(r RepaymentJournalRequest) (Expect, error) {
	portions, err := repaymentPortionsFromRequest(r.Portions)
	if err != nil {
		return Expect{}, err
	}
	legs, err := loan.CreateRepaymentJournalEntryLegs(r.TransactionID, portions, loan.RepaymentAccountMapping{
		LoanPortfolio:      r.Accounts.LoanPortfolio,
		ReceivableInterest: r.Accounts.ReceivableInterest,
		ReceivableFee:      r.Accounts.ReceivableFee,
		ReceivablePenalty:  r.Accounts.ReceivablePenalty,
		Overpayment:        r.Accounts.Overpayment,
		FundSource:         r.Accounts.FundSource,
	})
	if err != nil {
		return Expect{}, err
	}
	return repaymentJournalLegsExpect(legs), nil
}

// repaymentPortionsFromRequest reduces the request's per-slot money strings to
// the port's integer-minor-unit portions. Overpayment is optional (absent on
// every observed repayment whose read-back omits it); every other slot is
// required.
func repaymentPortionsFromRequest(p RepaymentPortionsMoney) (loan.RepaymentPortions, error) {
	var out loan.RepaymentPortions
	var err error
	if out.Principal, err = parseMinorText(p.Principal); err != nil {
		return loan.RepaymentPortions{}, err
	}
	if out.Interest, err = parseMinorText(p.Interest); err != nil {
		return loan.RepaymentPortions{}, err
	}
	if out.Fee, err = parseMinorText(p.Fee); err != nil {
		return loan.RepaymentPortions{}, err
	}
	if out.Penalty, err = parseMinorText(p.Penalty); err != nil {
		return loan.RepaymentPortions{}, err
	}
	if p.Overpayment != "" {
		if out.Overpayment, err = parseMinorText(p.Overpayment); err != nil {
			return loan.RepaymentPortions{}, err
		}
	}
	return out, nil
}

// repaymentJournalLegsExpect renders the port's ordered legs as the seam's
// ordered leg cells. Every money cell is an integer STRING in minor units; a leg
// whose side is somehow unknown renders an empty entry_type rather than
// defaulting to a side the capture never showed.
func repaymentJournalLegsExpect(legs []loan.JournalEntryLeg) Expect {
	out := make([]JournalEntryLeg, len(legs))
	for i, leg := range legs {
		out[i] = JournalEntryLeg{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			EntryType:     journalEntrySideCode(leg.Side),
			AmountMinor:   strconv.FormatInt(int64(leg.Amount), 10),
		}
	}
	if out == nil {
		out = []JournalEntryLeg{}
	}
	return Expect{RepaymentJournalLegs: out}
}

// goChargedOffRepaymentJournal ports the loan-chargedoff-repayment-journal-entries
// seam: it reduces the request's five portions and resolved slot->account
// mapping to loan.RepaymentPortions and loan.ChargedOffRepaymentAccountMapping
// and runs the port's own loan.CreateChargedOffRepaymentJournalEntryLegs. Every
// monetary cell is an integer minor unit; the mapping is the product's observed
// accountingMappings with the fund source resolved through the payment channel,
// never invented.
func goChargedOffRepaymentJournal(r ChargedOffRepaymentJournalRequest) (Expect, error) {
	portions, err := repaymentPortionsFromRequest(r.Portions)
	if err != nil {
		return Expect{}, err
	}
	legs, err := loan.CreateChargedOffRepaymentJournalEntryLegs(r.TransactionID, portions, loan.ChargedOffRepaymentAccountMapping{
		IncomeFromRecovery: r.Accounts.IncomeFromRecovery,
		Overpayment:        r.Accounts.Overpayment,
		FundSource:         r.Accounts.FundSource,
	})
	if err != nil {
		return Expect{}, err
	}
	return chargedOffRepaymentJournalLegsExpect(legs), nil
}

// chargedOffRepaymentJournalLegsExpect renders the port's ordered legs as the
// seam's ordered leg cells. Every money cell is an integer STRING in minor
// units; a leg whose side is somehow unknown renders an empty entry_type rather
// than defaulting to a side the capture never showed.
func chargedOffRepaymentJournalLegsExpect(legs []loan.JournalEntryLeg) Expect {
	out := make([]JournalEntryLeg, len(legs))
	for i, leg := range legs {
		out[i] = JournalEntryLeg{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			EntryType:     journalEntrySideCode(leg.Side),
			AmountMinor:   strconv.FormatInt(int64(leg.Amount), 10),
		}
	}
	if out == nil {
		out = []JournalEntryLeg{}
	}
	return Expect{ChargedOffRepaymentJournalLegs: out}
}

// goChargedOffMerchantRefundJournal ports the
// loan-chargedoff-merchant-refund-journal-entries seam: it reduces the request's
// five portions, the loan's fraud flag, the transaction kind and resolved
// slot->account mapping to loan.RepaymentPortions and
// loan.ChargedOffMerchantRefundAccountMapping and runs the port's own
// loan.CreateChargedOffMerchantRefundJournalEntryLegs. Every monetary cell is an
// integer minor unit; the mapping is the product's observed accountingMappings
// with the fund source resolved through the payment channel, never invented. The
// kind maps "merchant_issued_refund" (and an empty kind, the pre-existing
// default) to TransactionMerchantIssuedRefund and "payout_refund" to
// TransactionPayoutRefund; anything else is refused by the port.
func goChargedOffMerchantRefundJournal(r ChargedOffMerchantRefundJournalRequest) (Expect, error) {
	transactionType, err := chargedOffRefundTransactionType(r.Kind)
	if err != nil {
		return Expect{}, err
	}
	portions, err := repaymentPortionsFromRequest(r.Portions)
	if err != nil {
		return Expect{}, err
	}
	legs, err := loan.CreateChargedOffMerchantRefundJournalEntryLegs(r.TransactionID, transactionType, portions, r.Fraud, loan.ChargedOffMerchantRefundAccountMapping{
		ChargeOffExpense:            r.Accounts.ChargeOffExpense,
		ChargeOffFraudExpense:       r.Accounts.ChargeOffFraudExpense,
		IncomeFromChargeOffInterest: r.Accounts.IncomeFromChargeOffInterest,
		IncomeFromChargeOffFees:     r.Accounts.IncomeFromChargeOffFees,
		IncomeFromChargeOffPenalty:  r.Accounts.IncomeFromChargeOffPenalty,
		Overpayment:                 r.Accounts.Overpayment,
		FundSource:                  r.Accounts.FundSource,
	})
	if err != nil {
		return Expect{}, err
	}
	return chargedOffMerchantRefundJournalLegsExpect(legs), nil
}

// chargedOffRefundTransactionType maps the seam's request kind to the port's
// transaction type: an empty kind defaults to a merchant-issued refund so the
// pre-existing vectors stay valid, "payout_refund" names the payout arm, and
// every other kind is refused because the method's goodwill-credit arm has a
// different account table and is out of this seam.
func chargedOffRefundTransactionType(kind string) (loan.LoanTransactionType, error) {
	switch kind {
	case "", "merchant_issued_refund":
		return loan.TransactionMerchantIssuedRefund, nil
	case "payout_refund":
		return loan.TransactionPayoutRefund, nil
	default:
		return loan.TransactionInvalid, fmt.Errorf(
			"loan: charged-off refund journal entries accept only the kind merchant_issued_refund or payout_refund, got %q", kind)
	}
}

// chargedOffMerchantRefundJournalLegsExpect renders the port's ordered legs as
// the seam's ordered leg cells. Every money cell is an integer STRING in minor
// units; a leg whose side is somehow unknown renders an empty entry_type rather
// than defaulting to a side the capture never showed.
func chargedOffMerchantRefundJournalLegsExpect(legs []loan.JournalEntryLeg) Expect {
	out := make([]JournalEntryLeg, len(legs))
	for i, leg := range legs {
		out[i] = JournalEntryLeg{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			EntryType:     journalEntrySideCode(leg.Side),
			AmountMinor:   strconv.FormatInt(int64(leg.Amount), 10),
		}
	}
	if out == nil {
		out = []JournalEntryLeg{}
	}
	return Expect{ChargedOffMerchantRefundJournalLegs: out}
}

// goAccrualJournal ports the loan-accrual-journal-entries seam: it reduces the
// request's three portions and resolved slot->account mapping to
// loan.AccrualPortions and loan.AccrualAccountMapping and runs the port's own
// loan.CreateAccrualJournalEntryLegs with the adjustment flag. Every monetary
// cell is an integer minor unit; the mapping is the product's observed
// accountingMappings, never invented.
func goAccrualJournal(r AccrualJournalRequest) (Expect, error) {
	var portions loan.AccrualPortions
	var err error
	if portions.Interest, err = parseMinorText(r.Portions.Interest); err != nil {
		return Expect{}, err
	}
	if portions.Fee, err = parseMinorText(r.Portions.Fee); err != nil {
		return Expect{}, err
	}
	if portions.Penalty, err = parseMinorText(r.Portions.Penalty); err != nil {
		return Expect{}, err
	}
	legs, err := loan.CreateAccrualJournalEntryLegs(r.TransactionID, r.Adjustment, portions, loan.AccrualAccountMapping{
		ReceivableInterest: r.Accounts.ReceivableInterest,
		ReceivableFee:      r.Accounts.ReceivableFee,
		ReceivablePenalty:  r.Accounts.ReceivablePenalty,
		InterestOnLoans:    r.Accounts.InterestOnLoans,
		IncomeFromFee:      r.Accounts.IncomeFromFee,
		IncomeFromPenalty:  r.Accounts.IncomeFromPenalty,
	})
	if err != nil {
		return Expect{}, err
	}
	return accrualJournalLegsExpect(legs), nil
}

// accrualJournalLegsExpect renders the port's ordered legs as the seam's
// ordered leg cells. Every money cell is an integer STRING in minor units; a
// leg whose side is somehow unknown renders an empty entry_type rather than
// defaulting to a side the capture never showed.
func accrualJournalLegsExpect(legs []loan.JournalEntryLeg) Expect {
	out := make([]JournalEntryLeg, len(legs))
	for i, leg := range legs {
		out[i] = JournalEntryLeg{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			EntryType:     journalEntrySideCode(leg.Side),
			AmountMinor:   strconv.FormatInt(int64(leg.Amount), 10),
		}
	}
	if out == nil {
		out = []JournalEntryLeg{}
	}
	return Expect{AccrualJournalLegs: out}
}

// goChargebackJournal ports the loan-chargeback-journal-entries seam: it reduces
// the request's amount, principal, fee, penalty and overpayment portions, the
// charged-off flag and resolved slot->account mapping to loan.MinorUnits and
// loan.ChargebackAccountMapping and runs the port's own
// loan.CreateChargebackJournalEntryLegs. Every monetary cell is an integer minor
// unit; the mapping is the product's (or the payment channel's) observed
// accountingMappings, never invented. The observed identity amount = principal +
// fee + penalty + overpayment is enforced by the port, and the unobserved
// paid branches and charged-off fraud branch cannot be expressed. An omitted
// optional fee or penalty portion defaults to zero, so the three pinned
// principal/overpayment-only vectors keep their meaning.
func goChargebackJournal(r ChargebackJournalRequest) (Expect, error) {
	amount, err := parseMinorText(r.Amount)
	if err != nil {
		return Expect{}, err
	}
	principal, err := parseMinorText(minorTextOrZero(r.Portions.Principal))
	if err != nil {
		return Expect{}, err
	}
	fee, err := parseMinorText(minorTextOrZero(r.Portions.Fee))
	if err != nil {
		return Expect{}, err
	}
	penalty, err := parseMinorText(minorTextOrZero(r.Portions.Penalty))
	if err != nil {
		return Expect{}, err
	}
	overpayment, err := parseMinorText(minorTextOrZero(r.Portions.Overpayment))
	if err != nil {
		return Expect{}, err
	}
	legs, err := loan.CreateChargebackJournalEntryLegs(r.TransactionID, amount, principal, fee, penalty, overpayment, r.ChargedOff, r.Fraud, loan.ChargebackAccountMapping{
		FundSource:                 r.Accounts.FundSource,
		LoanPortfolio:              r.Accounts.LoanPortfolio,
		Overpayment:                r.Accounts.Overpayment,
		FeesReceivable:             r.Accounts.FeesReceivable,
		PenaltiesReceivable:        r.Accounts.PenaltiesReceivable,
		ChargeOffExpense:           r.Accounts.ChargeOffExpense,
		IncomeFromChargeOffFees:    r.Accounts.IncomeFromChargeOffFees,
		IncomeFromChargeOffPenalty: r.Accounts.IncomeFromChargeOffPenalty,
	})
	if err != nil {
		return Expect{}, err
	}
	return chargebackJournalLegsExpect(legs), nil
}

// chargebackJournalLegsExpect renders the port's ordered legs as the seam's
// ordered leg cells. Every money cell is an integer STRING in minor units; a
// leg whose side is somehow unknown renders an empty entry_type rather than
// defaulting to a side the capture never showed.
func chargebackJournalLegsExpect(legs []loan.JournalEntryLeg) Expect {
	out := make([]JournalEntryLeg, len(legs))
	for i, leg := range legs {
		out[i] = JournalEntryLeg{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			EntryType:     journalEntrySideCode(leg.Side),
			AmountMinor:   strconv.FormatInt(int64(leg.Amount), 10),
		}
	}
	if out == nil {
		out = []JournalEntryLeg{}
	}
	return Expect{ChargebackJournalLegs: out}
}

// goChargeLifecycle ports the loan-charge-lifecycle seam: it builds a
// LoanCharge of the observed amount and penalty flag, applies the ordered
// operations through the port's own money mutations, and captures the state
// after creation and after every operation. A "pay" operation runs
// UpdatePaidAmountBy; a "waive" operation runs Waive. After every operation the
// schedule/reprocess reconcile UpdateWaivedAmount runs on the charge — the path
// the oracle invokes on every charge — which is a no-op in every observed state
// and therefore never moves a cell. Every monetary cell is an integer minor
// unit; nothing is parsed as a float.
func goChargeLifecycle(c ChargeLifecycleRequest) (Expect, error) {
	amount, err := parseMinorText(c.AmountMinor)
	if err != nil {
		return Expect{}, err
	}
	charge := loan.LoanCharge{
		Amount:            amount,
		AmountOutstanding: amount,
		Penalty:           c.Penalty,
		Active:            true,
	}
	if err := assertChargeOutstandingConserved(charge); err != nil {
		return Expect{}, err
	}
	states := []ChargeLifecycleState{chargeLifecycleState(charge)}
	for _, op := range c.Operations {
		switch op.Op {
		case "pay":
			increment, err := parseMinorText(op.AmountMinor)
			if err != nil {
				return Expect{}, err
			}
			charge.UpdatePaidAmountBy(increment)
		case "waive":
			charge.Waive()
		default:
			return Expect{}, fmt.Errorf("loan: charge-lifecycle operation %q is neither pay nor waive", op.Op)
		}
		charge.UpdateWaivedAmount()
		if err := assertChargeOutstandingConserved(charge); err != nil {
			return Expect{}, err
		}
		states = append(states, chargeLifecycleState(charge))
	}
	return Expect{ChargeStates: states}, nil
}

// assertChargeOutstandingConserved grades the seam's one property directly
// through the port's own derivation: the authoritative AmountOutstanding field
// must equal loan.LoanCharge.CalculateOutstanding (amount minus paid minus
// waived minus written off) in every observed state. On the committed captures
// written-off is always zero, so this is exactly amount minus paid minus waived.
func assertChargeOutstandingConserved(c loan.LoanCharge) error {
	if got, want := c.AmountOutstanding, c.CalculateOutstanding(); got != want {
		return fmt.Errorf("loan: charge outstanding %d != CalculateOutstanding (amount - paid - waived) %d", got, want)
	}
	return nil
}

// chargeLifecycleState renders one LoanCharge's observed cells as the seam's
// state: amountPaid, amountWaived and amountOutstanding as integer minor-unit
// strings plus the paid/waived flags.
func chargeLifecycleState(c loan.LoanCharge) ChargeLifecycleState {
	return chargeLifecycleStateFromOutstanding(c, c.AmountOutstanding)
}

// chargeLifecycleStateFromOutstanding renders the same observed cells but takes
// the outstanding explicitly. The caller passes a value the port DERIVED (its
// own CalculateOutstanding on a charge whose inputs were changed), so no
// balance-named field is ever assigned in this package — the value is in
// flight, exactly like the correct renderer above.
func chargeLifecycleStateFromOutstanding(c loan.LoanCharge, outstanding loan.MinorUnits) ChargeLifecycleState {
	return ChargeLifecycleState{
		PaidMinor:        strconv.FormatInt(int64(c.AmountPaid), 10),
		WaivedMinor:      strconv.FormatInt(int64(c.AmountWaived), 10),
		OutstandingMinor: strconv.FormatInt(int64(outstanding), 10),
		Paid:             c.Paid,
		Waived:           c.Waived,
	}
}

// chargeLifecycleWrongMode selects which deliberately-wrong charge-lifecycle
// reading to run. Each is a port a reasonable reader might write, and each is
// discriminated by the committed loan-18 observation. Every mode changes the
// charge's INPUTS or the OPERATIONS it applies and then reads the outstanding
// off the port's own derivation; no balance-named field is assigned in this
// package.
type chargeLifecycleWrongMode int

const (
	// wrongChargePartialMarksPaid flips the paid flag as soon as any amount is
	// paid, before outstanding reaches zero. The port still moves amountPaid to
	// 10000 and derives outstanding 2345; only the flag flips early. The pinned
	// fee's partial step (amountPaid 10000, outstanding 2345, paid false) then
	// reads paid true.
	wrongChargePartialMarksPaid chargeLifecycleWrongMode = iota
	// wrongChargeWaiverLeavesOutstanding records amountWaived through the port's
	// own Waive, then re-derives outstanding from a view with the waived input
	// dropped, so the pinned penalty (waived 6789, outstanding 0) reads
	// outstanding 6789 while the waived cell and flag stay observed.
	wrongChargeWaiverLeavesOutstanding
	// wrongChargeWaiverCountsAsPaid applies a waiver as a PAYMENT: the "waive"
	// operation runs UpdatePaidAmountBy(outstanding) instead of Waive, routing
	// the amount into amountPaid and the paid flag, so the pinned penalty (paid
	// false, waived true) reads amountPaid 6789, amountWaived 0, paid true,
	// waived false.
	wrongChargeWaiverCountsAsPaid
	// wrongChargeOutstandingIgnoresWaived re-derives every state's outstanding
	// from a view with the waived input dropped (amount minus paid only), so the
	// pinned waived penalty (outstanding 0) reads outstanding 6789.
	wrongChargeOutstandingIgnoresWaived
)

// wrongChargeLifecycleEvaluator is a DELIBERATELY WRONG implementation of the
// loan-charge-lifecycle seam, parameterised by which lifecycle defect it
// commits. On any request that is not a charge lifecycle it delegates to the
// correct port, so each drive goes red ONLY on this seam's vectors and stays
// green everywhere else (vector isolation).
type wrongChargeLifecycleEvaluator struct {
	goEvaluator
	mode chargeLifecycleWrongMode
}

func (w wrongChargeLifecycleEvaluator) Evaluate(req Request) (Expect, error) {
	if req.ChargeLifecycle != nil {
		return wrongChargeLifecycle(*req.ChargeLifecycle, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongChargeLifecycle runs the lifecycle through deliberately-wrong behaviour.
// Each mode changes the charge's INPUTS or the OPERATIONS it applies and then
// renders the outstanding through the port's own derivation (the field a port
// mutation left, or CalculateOutstanding on a view whose inputs were changed) —
// the balance is never assigned here.
func wrongChargeLifecycle(c ChargeLifecycleRequest, mode chargeLifecycleWrongMode) (Expect, error) {
	amount, err := parseMinorText(c.AmountMinor)
	if err != nil {
		return Expect{}, err
	}
	charge := loan.LoanCharge{
		Amount:            amount,
		AmountOutstanding: amount,
		Penalty:           c.Penalty,
		Active:            true,
	}
	states := []ChargeLifecycleState{chargeLifecycleWrongState(charge, mode)}
	for _, op := range c.Operations {
		switch op.Op {
		case "pay":
			increment, err := parseMinorText(op.AmountMinor)
			if err != nil {
				return Expect{}, err
			}
			charge.UpdatePaidAmountBy(increment)
			if mode == wrongChargePartialMarksPaid && charge.AmountPaid > 0 {
				// The defect: the paid flag flips on the first payment. The
				// paid amount and outstanding remain the port's own.
				charge.Paid = true
			}
		case "waive":
			if mode == wrongChargeWaiverCountsAsPaid {
				// The defect: a waiver is applied as a payment, so the port
				// routes the amount into amountPaid and derives the rest.
				increment := charge.AmountOutstanding
				charge.UpdatePaidAmountBy(increment)
			} else {
				charge.Waive()
			}
		default:
			return Expect{}, fmt.Errorf("loan: charge-lifecycle operation %q is neither pay nor waive", op.Op)
		}
		charge.UpdateWaivedAmount()
		states = append(states, chargeLifecycleWrongState(charge, mode))
	}
	return Expect{ChargeStates: states}, nil
}

// chargeLifecycleWrongState renders one charge for a wrong drive. The two
// modes whose defect is that the outstanding ignores the waiver drop the
// waived input on a view charge and re-derive the outstanding through the
// port's own CalculateOutstanding (amount - paid - waived = amount - paid); the
// waived cell and the flags still come from the charge the operations ran on.
// Every other mode renders the charge's own port-derived state.
func chargeLifecycleWrongState(c loan.LoanCharge, mode chargeLifecycleWrongMode) ChargeLifecycleState {
	if mode == wrongChargeOutstandingIgnoresWaived ||
		(mode == wrongChargeWaiverLeavesOutstanding && c.AmountWaived > 0) {
		view := loan.LoanCharge{
			Amount:           c.Amount,
			AmountPaid:       c.AmountPaid,
			AmountWrittenOff: c.AmountWrittenOff,
		}
		return chargeLifecycleStateFromOutstanding(c, view.CalculateOutstanding())
	}
	return chargeLifecycleState(c)
}

// writeOffJournalWrongMode selects which deliberately-wrong write-off posting
// to run. Each is a port a reasonable reader might write, and each is
// discriminated by the committed L54 observation.
type writeOffJournalWrongMode int

const (
	// wrongWriteOffJournalOneDebitPerPortion posts one debit per discharged
	// portion instead of ONE debit of the total. The whole batch still balances
	// (each side sums to 10677553) and every account is right, but the leg
	// count grows from five to eight and the debit count from one to four, so
	// only the ordered leg cells see the extra debits.
	wrongWriteOffJournalOneDebitPerPortion writeOffJournalWrongMode = iota
	// wrongWriteOffJournalDebitsPrincipalOnly posts all four credits but debits
	// only the principal portion (10000000), so the credits sum to 10677553
	// while the debit reads 10000000 and the batch no longer balances.
	wrongWriteOffJournalDebitsPrincipalOnly
	// wrongWriteOffJournalDebitsLoanPortfolio debits the loan-portfolio slot
	// instead of the losses-written-off slot. Every amount and side is right
	// and the batch still balances; only the debit's ACCOUNT cell moves.
	wrongWriteOffJournalDebitsLoanPortfolio
	// wrongWriteOffJournalSwapsFeeAndPenalty credits the fee portion to the
	// penalties-receivable account and the penalty portion to the fee account,
	// so the fee (10000) and penalty (5700) account cells move while every total
	// holds; the distinct non-zero portions mean the swap cannot hide.
	wrongWriteOffJournalSwapsFeeAndPenalty
)

// wrongWriteOffJournalEvaluator is a DELIBERATELY WRONG implementation of the
// loan-writeoff-journal-entries seam, parameterised by which posting defect it
// commits. On any request that is not a write-off journal it delegates to the
// correct port, so each drive goes red ONLY on this seam's vector and stays
// green everywhere else (vector isolation).
type wrongWriteOffJournalEvaluator struct {
	goEvaluator
	mode writeOffJournalWrongMode
}

func (w wrongWriteOffJournalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.WriteOffJournal != nil {
		return wrongWriteOffJournal(*req.WriteOffJournal, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongWriteOffJournal runs the correct posting and then applies exactly one
// defect, so each drive differs from the port on exactly the cells its defect
// moves.
func wrongWriteOffJournal(r WriteOffJournalRequest, mode writeOffJournalWrongMode) (Expect, error) {
	// Input-level defects perturb the observed mapping the port reads.
	switch mode {
	case wrongWriteOffJournalDebitsLoanPortfolio:
		r.Accounts.LossesWrittenOff = r.Accounts.LoanPortfolio
	case wrongWriteOffJournalSwapsFeeAndPenalty:
		r.Accounts.FeesReceivable, r.Accounts.PenaltiesReceivable = r.Accounts.PenaltiesReceivable, r.Accounts.FeesReceivable
	}
	expect, err := goWriteOffJournal(r)
	if err != nil {
		return Expect{}, err
	}
	switch mode {
	case wrongWriteOffJournalOneDebitPerPortion:
		expect = oneDebitPerPortion(expect)
	case wrongWriteOffJournalDebitsPrincipalOnly:
		principal, err := parseMinorText(r.Portions.Principal)
		if err != nil {
			return Expect{}, err
		}
		legs := expect.WriteOffJournalLegs
		if n := len(legs); n > 0 {
			legs[n-1].AmountMinor = strconv.FormatInt(int64(principal), 10)
		}
	}
	return expect, nil
}

// oneDebitPerPortion rewrites the correct leg list (credits then one debit) as
// one debit per credit, after the credits, so the batch balances but carries a
// debit for every portion.
func oneDebitPerPortion(e Expect) Expect {
	var credits, debits []JournalEntryLeg
	for _, leg := range e.WriteOffJournalLegs {
		if leg.EntryType == "CREDIT" {
			credits = append(credits, leg)
			debits = append(debits, JournalEntryLeg{
				TransactionID: leg.TransactionID,
				Account:       leg.Account,
				EntryType:     "DEBIT",
				AmountMinor:   leg.AmountMinor,
			})
		}
	}
	e.WriteOffJournalLegs = append(credits, debits...)
	if e.WriteOffJournalLegs == nil {
		e.WriteOffJournalLegs = []JournalEntryLeg{}
	}
	return e
}

// chargeOffJournalWrongMode selects which deliberately-wrong charge-off posting
// to run. Each is a port a reasonable reader might write, and each is
// discriminated by the committed observations.
type chargeOffJournalWrongMode int

const (
	// wrongChargeOffJournalIgnoresFraud debits the principal portion to the
	// ordinary CHARGE_OFF_EXPENSE account even when the loan is marked fraud,
	// as a port that never reads the fraud flag does. On the pinned loan-7 and
	// loan-4 (non-fraud) observations it posts the observed legs; on the fraud
	// loan-15 observation the principal debit moves from the fraud expense
	// account (13) to the ordinary charge-off expense account (14), so only
	// that account cell moves.
	wrongChargeOffJournalIgnoresFraud chargeOffJournalWrongMode = iota
)

// wrongChargeOffJournalEvaluator is a DELIBERATELY WRONG implementation of the
// loan-chargeoff-journal-entries seam, parameterised by which posting defect it
// commits. On any request that is not a charge-off journal it delegates to the
// correct port, so each drive goes red ONLY on this seam's vectors and stays
// green everywhere else (vector isolation).
type wrongChargeOffJournalEvaluator struct {
	goEvaluator
	mode chargeOffJournalWrongMode
}

func (w wrongChargeOffJournalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.ChargeOffJournal != nil {
		return wrongChargeOffJournal(*req.ChargeOffJournal, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongChargeOffJournal runs the correct posting and then applies exactly one
// defect, so the drive differs from the port on exactly the cells its defect
// moves.
func wrongChargeOffJournal(r ChargeOffJournalRequest, mode chargeOffJournalWrongMode) (Expect, error) {
	switch mode {
	case wrongChargeOffJournalIgnoresFraud:
		r.Accounts.ChargeOffFraudExpense = r.Accounts.ChargeOffExpense
	}
	return goChargeOffJournal(r)
}

// chargedOffWriteOffJournalWrongMode selects which deliberately-wrong
// charged-off-write-off posting to run. Each is a port a reasonable reader might
// write, and it is discriminated by the committed observations.
type chargedOffWriteOffJournalWrongMode int

const (
	// wrongChargedOffWriteOffDebitsFundSource posts the per-portion FUND_SOURCE
	// debits populateCreditDebitMaps accumulates instead of the one
	// LOSSES_WRITTEN_OFF debit the oracle posts, as a port that iterates both
	// maps does. The credits are unchanged; the ONE losses-written-off debit is
	// replaced by one debit per credit to the fund-source account, so the leg
	// count grows by (credits - 1), the last leg's account moves from
	// losses-written-off to fund-source, and the batch no longer balances when
	// the fund source differs from the merged credit accounts. It is the mirror
	// of the unposted debit map the oracle deliberately ignores.
	wrongChargedOffWriteOffDebitsFundSource chargedOffWriteOffJournalWrongMode = iota
)

// wrongChargedOffWriteOffJournalEvaluator is a DELIBERATELY WRONG implementation
// of the loan-chargedoff-writeoff-journal-entries seam, parameterised by which
// posting defect it commits. On any request that is not a charged-off write-off
// journal it delegates to the correct port, so the drive goes red ONLY on this
// seam's vector and stays green everywhere else (vector isolation).
type wrongChargedOffWriteOffJournalEvaluator struct {
	goEvaluator
	mode chargedOffWriteOffJournalWrongMode
}

func (w wrongChargedOffWriteOffJournalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.ChargedOffWriteOffJournal != nil {
		return wrongChargedOffWriteOffJournal(*req.ChargedOffWriteOffJournal, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongChargedOffWriteOffJournal runs the correct posting and then applies
// exactly one defect, so the drive differs from the port on exactly the cells
// its defect moves.
func wrongChargedOffWriteOffJournal(r ChargedOffWriteOffJournalRequest, mode chargedOffWriteOffJournalWrongMode) (Expect, error) {
	expect, err := goChargedOffWriteOffJournal(r)
	if err != nil {
		return Expect{}, err
	}
	switch mode {
	case wrongChargedOffWriteOffDebitsFundSource:
		// Replace the single losses-written-off debit with one fund-source debit
		// per credit, after the credits, so the batch carries the unposted debit
		// map's per-portion legs instead of the oracle's one total debit.
		fund := r.Accounts.FundSource
		if fund == "" {
			fund = r.Accounts.LossesWrittenOff
		}
		var credits, debits []JournalEntryLeg
		for _, leg := range expect.ChargedOffWriteOffJournalLegs {
			if leg.EntryType == "CREDIT" {
				credits = append(credits, leg)
				debits = append(debits, JournalEntryLeg{
					TransactionID: leg.TransactionID,
					Account:       fund,
					EntryType:     "DEBIT",
					AmountMinor:   leg.AmountMinor,
				})
			}
		}
		expect.ChargedOffWriteOffJournalLegs = append(credits, debits...)
		if expect.ChargedOffWriteOffJournalLegs == nil {
			expect.ChargedOffWriteOffJournalLegs = []JournalEntryLeg{}
		}
	}
	return expect, nil
}

// chargedOffRepaymentJournalWrongMode selects which deliberately-wrong
// charged-off-repayment posting to run. Each is a port a reasonable reader might
// write, and it is discriminated by the committed observations.
type chargedOffRepaymentJournalWrongMode int

const (
	// wrongChargedOffRepaymentJournalsOrdinary posts the repayment through the
	// ORDINARY repayment port instead of the charged-off branch, as a port that
	// forgets the loan is marked charged off does. The principal credit moves to
	// LOAN_PORTFOLIO and the interest credit to INTEREST_RECEIVABLE instead of
	// both merging into INCOME_FROM_RECOVERY, so the credits' accounts and count
	// (and the recovery credit's amount, split back apart) differ while every
	// side and the single fund-source debit stay observed. On the principal-only
	// loan-37 observation only the principal credit's account moves; on the
	// principal+interest loan-19 observation the ONE merged recovery credit
	// becomes TWO credits.
	wrongChargedOffRepaymentJournalsOrdinary chargedOffRepaymentJournalWrongMode = iota
)

// wrongChargedOffRepaymentJournalEvaluator is a DELIBERATELY WRONG
// implementation of the loan-chargedoff-repayment-journal-entries seam,
// parameterised by which posting defect it commits. On any request that is not a
// charged-off repayment journal it delegates to the correct port, so the drive
// goes red ONLY on this seam's vectors and stays green everywhere else (vector
// isolation).
type wrongChargedOffRepaymentJournalEvaluator struct {
	goEvaluator
	mode chargedOffRepaymentJournalWrongMode
}

func (w wrongChargedOffRepaymentJournalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.ChargedOffRepaymentJournal != nil {
		return wrongChargedOffRepaymentJournal(*req.ChargedOffRepaymentJournal, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongChargedOffRepaymentJournal runs the deliberately-wrong posting selected
// by mode. It never calls the correct charged-off port, so the drive differs
// from the port on exactly the cells its defect moves.
func wrongChargedOffRepaymentJournal(r ChargedOffRepaymentJournalRequest, mode chargedOffRepaymentJournalWrongMode) (Expect, error) {
	switch mode {
	case wrongChargedOffRepaymentJournalsOrdinary:
		// Post the same portions through the ordinary repayment port: the
		// principal credits the loan portfolio, the interest the interest
		// receivable, and the merged recovery credit never forms.
		ordinary, err := goRepaymentJournal(RepaymentJournalRequest{
			TransactionID: r.TransactionID,
			Portions:      r.Portions,
			Accounts: RepaymentSlotAccounts{
				LoanPortfolio:      r.Accounts.LoanPortfolio,
				ReceivableInterest: r.Accounts.ReceivableInterest,
				FundSource:         r.Accounts.FundSource,
			},
		})
		if err != nil {
			return Expect{}, err
		}
		out := ordinary.RepaymentJournalLegs
		if out == nil {
			out = []JournalEntryLeg{}
		}
		return Expect{ChargedOffRepaymentJournalLegs: out}, nil
	default:
		return Expect{}, fmt.Errorf("loan: unknown charged-off repayment wrong mode %d", mode)
	}
}

// merchantRefundJournalWrongMode selects which deliberately-wrong
// merchant-issued-refund posting to run.
type merchantRefundJournalWrongMode int

const (
	// wrongMerchantRefundJournalAsRecovery posts the merchant-issued refund
	// through the charged-off REPAYMENT layout instead of the merchant-refund
	// arm, as a port that reuses the repayment branch for every refund does: the
	// principal credit moves from CHARGE_OFF_EXPENSE to INCOME_FROM_RECOVERY and
	// the interest credit from INCOME_FROM_CHARGE_OFF_INTEREST to
	// INCOME_FROM_RECOVERY, so two credits collapse into ONE on the
	// principal+interest observation while the overpayment credit and the single
	// fund-source debit stay observed. On the principal-only observation the
	// single principal credit's account moves.
	wrongMerchantRefundJournalAsRecovery merchantRefundJournalWrongMode = iota
	// wrongMerchantRefundJournalFraudIgnored posts a refund on a FRAUD loan as
	// if the loan were not fraud: the principal credit lands on
	// CHARGE_OFF_EXPENSE instead of CHARGE_OFF_FRAUD_EXPENSE while every other
	// leg stays observed. It is correct on a non-fraud observation, so the drive
	// goes red ONLY on a fraud vector and stays green on the non-fraud ones.
	wrongMerchantRefundJournalFraudIgnored
)

// wrongMerchantRefundJournalEvaluator is a DELIBERATELY WRONG implementation of
// the loan-chargedoff-merchant-refund-journal-entries seam. On any request that
// is not a charged-off merchant refund it delegates to the correct port, so the
// drive goes red ONLY on this seam's vectors and stays green everywhere else
// (vector isolation).
type wrongMerchantRefundJournalEvaluator struct {
	goEvaluator
	mode merchantRefundJournalWrongMode
}

func (w wrongMerchantRefundJournalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.ChargedOffMerchantRefundJournal != nil {
		return wrongMerchantRefundJournal(*req.ChargedOffMerchantRefundJournal, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongMerchantRefundJournal runs the deliberately-wrong posting selected by
// mode. It never calls the correct merchant-refund port, so the drive differs
// from the port on exactly the cells its defect moves.
func wrongMerchantRefundJournal(r ChargedOffMerchantRefundJournalRequest, mode merchantRefundJournalWrongMode) (Expect, error) {
	switch mode {
	case wrongMerchantRefundJournalAsRecovery:
		// Post the same portions through the charged-off repayment port: every
		// principal, interest, fee and penalty portion credits
		// income-from-recovery (merged), the overpayment credits its own account
		// and the total debits the fund source once.
		portions, err := repaymentPortionsFromRequest(r.Portions)
		if err != nil {
			return Expect{}, err
		}
		legs, err := loan.CreateChargedOffRepaymentJournalEntryLegs(r.TransactionID, portions, loan.ChargedOffRepaymentAccountMapping{
			IncomeFromRecovery: r.Accounts.IncomeFromRecovery,
			Overpayment:        r.Accounts.Overpayment,
			FundSource:         r.Accounts.FundSource,
		})
		if err != nil {
			return Expect{}, err
		}
		return chargedOffMerchantRefundJournalLegsExpect(legs), nil
	case wrongMerchantRefundJournalFraudIgnored:
		// Post the same portions through the correct refund port but with the
		// fraud flag forced false: the principal credit lands on the ordinary
		// charge-off expense account, so on a fraud observation the principal
		// leg's account moves and every other leg stays observed.
		portions, err := repaymentPortionsFromRequest(r.Portions)
		if err != nil {
			return Expect{}, err
		}
		legs, err := loan.CreateChargedOffMerchantRefundJournalEntryLegs(r.TransactionID, loan.TransactionMerchantIssuedRefund, portions, false, loan.ChargedOffMerchantRefundAccountMapping{
			ChargeOffExpense:            r.Accounts.ChargeOffExpense,
			ChargeOffFraudExpense:       r.Accounts.ChargeOffFraudExpense,
			IncomeFromChargeOffInterest: r.Accounts.IncomeFromChargeOffInterest,
			IncomeFromChargeOffFees:     r.Accounts.IncomeFromChargeOffFees,
			IncomeFromChargeOffPenalty:  r.Accounts.IncomeFromChargeOffPenalty,
			Overpayment:                 r.Accounts.Overpayment,
			FundSource:                  r.Accounts.FundSource,
		})
		if err != nil {
			return Expect{}, err
		}
		return chargedOffMerchantRefundJournalLegsExpect(legs), nil
	default:
		return Expect{}, fmt.Errorf("loan: unknown charged-off merchant refund wrong mode %d", mode)
	}
}

// accrualJournalWrongMode selects which deliberately-wrong accrual posting to
// run. Each is a port a reasonable reader might write, and it is discriminated
// by the committed observations.
type accrualJournalWrongMode int

const (
	// wrongAccrualJournalAdjustmentNotReversed posts an ACCRUAL_ADJUSTMENT
	// through the accrual branch, as a port that forgets to swap the sides for
	// an adjustment does. On the loan-15 L107 observation the interest pair
	// keeps the accrual sides (DEBIT the receivable 7, CREDIT the interest
	// income 8) instead of the reversed pair (DEBIT 8, CREDIT 7), so both legs
	// move while every count, amount and every non-adjustment vector stays
	// observed.
	wrongAccrualJournalAdjustmentNotReversed accrualJournalWrongMode = iota
)

// wrongAccrualJournalEvaluator is a DELIBERATELY WRONG implementation of the
// loan-accrual-journal-entries seam, parameterised by which posting defect it
// commits. On any request that is not an accrual journal it delegates to the
// correct port, so the drive goes red ONLY on this seam's vectors and stays
// green everywhere else (vector isolation).
type wrongAccrualJournalEvaluator struct {
	goEvaluator
	mode accrualJournalWrongMode
}

func (w wrongAccrualJournalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.AccrualJournal != nil {
		return wrongAccrualJournal(*req.AccrualJournal, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongAccrualJournal runs the deliberately-wrong posting selected by mode. The
// adjustment-not-reversed defect drops the flag before the posting, so an
// adjustment is posted with the accrual's (unswapped) sides.
func wrongAccrualJournal(r AccrualJournalRequest, mode accrualJournalWrongMode) (Expect, error) {
	switch mode {
	case wrongAccrualJournalAdjustmentNotReversed:
		r.Adjustment = false
		return goAccrualJournal(r)
	default:
		return Expect{}, fmt.Errorf("loan: unknown accrual wrong mode %d", mode)
	}
}

// repaymentJournalWrongMode selects which deliberately-wrong repayment posting
// to run. Each is a port a reasonable reader might write, and it is
// discriminated by the committed observations.
type repaymentJournalWrongMode int

const (
	// wrongRepaymentJournalDebitsFundSourcePerPortion posts one FUND_SOURCE debit
	// per credited portion instead of the one total FUND_SOURCE debit the oracle
	// posts, as a port that emits a debit for every credit does. The credits are
	// unchanged; the single total debit is replaced by one debit per credit, so
	// the leg count grows by (credits - 1) and the batch carries more than one
	// debit leg. On the principal-only loan-14 observation one credit and one
	// debit coincide, so only the multi-credit observations (loan 18 and loan 19)
	// discriminate it.
	wrongRepaymentJournalDebitsFundSourcePerPortion repaymentJournalWrongMode = iota
)

// wrongRepaymentJournalEvaluator is a DELIBERATELY WRONG implementation of the
// loan-repayment-journal-entries seam, parameterised by which posting defect it
// commits. On any request that is not a repayment journal it delegates to the
// correct port, so the drive goes red ONLY on this seam's vector and stays green
// everywhere else (vector isolation).
type wrongRepaymentJournalEvaluator struct {
	goEvaluator
	mode repaymentJournalWrongMode
}

func (w wrongRepaymentJournalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.RepaymentJournal != nil {
		return wrongRepaymentJournal(*req.RepaymentJournal, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongRepaymentJournal runs the correct posting and then applies exactly one
// defect, so the drive differs from the port on exactly the cells its defect
// moves.
func wrongRepaymentJournal(r RepaymentJournalRequest, mode repaymentJournalWrongMode) (Expect, error) {
	expect, err := goRepaymentJournal(r)
	if err != nil {
		return Expect{}, err
	}
	switch mode {
	case wrongRepaymentJournalDebitsFundSourcePerPortion:
		// Replace the single fund-source debit with one fund-source debit per
		// credit, after the credits, so the batch carries a per-portion debit
		// instead of the oracle's one total debit.
		fund := r.Accounts.FundSource
		var credits, debits []JournalEntryLeg
		for _, leg := range expect.RepaymentJournalLegs {
			if leg.EntryType == "CREDIT" {
				credits = append(credits, leg)
				debits = append(debits, JournalEntryLeg{
					TransactionID: leg.TransactionID,
					Account:       fund,
					EntryType:     "DEBIT",
					AmountMinor:   leg.AmountMinor,
				})
			}
		}
		expect.RepaymentJournalLegs = append(credits, debits...)
		if expect.RepaymentJournalLegs == nil {
			expect.RepaymentJournalLegs = []JournalEntryLeg{}
		}
	}
	return expect, nil
}

// chargebackJournalWrongMode selects which deliberately-wrong chargeback posting
// to run. Each is a port a reasonable reader might write, and each is
// discriminated by the committed observations.
type chargebackJournalWrongMode int

const (
	// wrongChargebackJournalOverpaymentToPortfolio debits the overpayment
	// portion to the LOAN_PORTFOLIO account instead of the OVERPAYMENT account,
	// as a port that reuses one debit account for every non-principal portion
	// does. On the pinned loan-14 (principal only) observation it posts the
	// observed legs; on loan-19 (overpayment only) the overpayment debit moves
	// from account 18 to account 10; on loan-21 (overpayment 250 + principal
	// 100) both debits name account 10, so the account cell of the first debit
	// moves while every amount and side stays observed.
	wrongChargebackJournalOverpaymentToPortfolio chargebackJournalWrongMode = iota
	// wrongChargebackJournalIgnoresChargeOff posts every portion to the
	// not-charged-off portfolio/receivable accounts, as a port that never reads
	// the loan's charged-off flag does. On a charged-off loan the principal
	// debit moves from CHARGE_OFF_EXPENSE to LOAN_PORTFOLIO and the fee/penalty
	// debits from the charge-off income accounts to the receivables; the
	// not-charged-off observations are unaffected.
	wrongChargebackJournalIgnoresChargeOff
)

// wrongChargebackJournalEvaluator is a DELIBERATELY WRONG implementation of the
// loan-chargeback-journal-entries seam, parameterised by which posting defect it
// commits. On any request that is not a chargeback journal it delegates to the
// correct port, so each drive goes red ONLY on this seam's vectors and stays
// green everywhere else (vector isolation).
type wrongChargebackJournalEvaluator struct {
	goEvaluator
	mode chargebackJournalWrongMode
}

func (w wrongChargebackJournalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.ChargebackJournal != nil {
		return wrongChargebackJournal(*req.ChargebackJournal, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongChargebackJournal runs the correct posting and then applies exactly one
// defect, so the drive differs from the port on exactly the cells its defect
// moves.
func wrongChargebackJournal(r ChargebackJournalRequest, mode chargebackJournalWrongMode) (Expect, error) {
	switch mode {
	case wrongChargebackJournalOverpaymentToPortfolio:
		r.Accounts.Overpayment = r.Accounts.LoanPortfolio
	case wrongChargebackJournalIgnoresChargeOff:
		r.ChargedOff = false
	}
	return goChargebackJournal(r)
}

// amortizationWrongMode selects which deliberately-wrong whole-schedule
// principal reconstruction to run. Each mode rebuilds the per-period components
// from the disbursed principal or from a prefix of the observed components and
// then runs the same derivation — exactly what a port does when it re-derives
// the schedule instead of transcribing its per-period principal back.
type amortizationWrongMode int

const (
	// wrongAmortizationDropsFinalComponent reconstructs the schedule without the
	// LAST repayment period's principal component, as a port does when it reads
	// only the pre-adjustment rows. On the pinned loan-5 schedule the sum falls
	// 348748 minor units short and the final balance is left at exactly 348748.
	wrongAmortizationDropsFinalComponent amortizationWrongMode = iota
	// wrongAmortizationUniformTruncated recomputes every period as
	// floor(disbursed/periods), so the sub-minor remainder of an uneven division
	// is never placed anywhere. On the pinned loan-5 schedule (4185009 minor
	// units over 12 periods) the remainder is 9 minor units: the sum reads
	// 4185000 and the final balance is left at 9.
	wrongAmortizationUniformTruncated
	// wrongAmortizationUniformRoundedUp recomputes every period as
	// ceil(disbursed/periods), over-amortising by the rounded-up excess. On the
	// pinned loan-5 schedule the sum reads 4185012 and the final balance goes
	// negative at -3.
	wrongAmortizationUniformRoundedUp
)

// wrongScheduleAmortizationEvaluator is a DELIBERATELY WRONG implementation of
// the whole-schedule principal-amortization seam, parameterised by which
// reconstruction defect it commits. On any request that is not a schedule
// amortization it delegates to the correct port, so each drive goes red ONLY on
// this seam's vector and stays green everywhere else (vector isolation).
type wrongScheduleAmortizationEvaluator struct {
	goEvaluator
	mode amortizationWrongMode
}

func (w wrongScheduleAmortizationEvaluator) Evaluate(req Request) (Expect, error) {
	if req.ScheduleAmortization != nil {
		return wrongScheduleAmortization(*req.ScheduleAmortization, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongScheduleAmortization rebuilds the per-period components with one defect
// and derives the sum and final balance from the rebuilt sequence.
func wrongScheduleAmortization(r ScheduleAmortizationRequest, mode amortizationWrongMode) (Expect, error) {
	disbursed, err := parseMinorText(r.PrincipalDisbursedMinor)
	if err != nil {
		return Expect{}, err
	}
	components, err := parsePrincipalComponents(r.PrincipalComponentsMinor)
	if err != nil {
		return Expect{}, err
	}
	var rebuilt []loan.MinorUnits
	switch mode {
	case wrongAmortizationDropsFinalComponent:
		if len(components) > 0 {
			rebuilt = components[:len(components)-1]
		}
	case wrongAmortizationUniformTruncated:
		rebuilt = uniformPrincipalComponents(disbursed, len(components), false)
	case wrongAmortizationUniformRoundedUp:
		rebuilt = uniformPrincipalComponents(disbursed, len(components), true)
	}
	am := loan.DerivePrincipalAmortization(disbursed, rebuilt)
	return Expect{
		PrincipalSumMinor:          strconv.FormatInt(int64(am.PrincipalSum), 10),
		FinalPrincipalBalanceMinor: strconv.FormatInt(int64(am.FinalBalance), 10),
	}, nil
}

// uniformPrincipalComponents returns n copies of a uniform per-period principal
// derived from the disbursed amount: floor(disbursed/n), or ceil(disbursed/n)
// when roundUp is set. Neither places the division remainder, so the derived
// sum reconciles to the disbursed principal only when the division is exact.
func uniformPrincipalComponents(disbursed loan.MinorUnits, n int, roundUp bool) []loan.MinorUnits {
	if n <= 0 {
		return nil
	}
	per := disbursed / loan.MinorUnits(n)
	if roundUp && per*loan.MinorUnits(n) != disbursed {
		per++
	}
	out := make([]loan.MinorUnits, n)
	for i := range out {
		out[i] = per
	}
	return out
}

// delinquencyWrongMode selects which deliberately-wrong day-count to run. Both
// modes delegate every non-delinquency request to the correct port, so each
// drive goes red ONLY on the delinquent-days seam (vector isolation).
type delinquencyWrongMode int

const (
	// wrongDelinquencyThirtyDayMonth approximates every month as 30 days: it
	// counts whole calendar months between the overdue-since date and the
	// business date and multiplies by 30. The committed rows are the 1st of
	// June, July and August 2026 read at 2026-09-01, so this shortcut reads
	// 90 / 60 / 30 where the oracle read 92 / 62 / 31 — it treats months of
	// unequal length as interchangeable.
	wrongDelinquencyThirtyDayMonth delinquencyWrongMode = iota
	// wrongDelinquencyAbsentNonZero treats an ABSENT overdue-since date as an
	// elapsed-since-epoch day count instead of zero, the port that serialises a
	// number where the oracle returns zero. The present-date rows are
	// unaffected.
	wrongDelinquencyAbsentNonZero
	// wrongDelinquencyPauseIgnored ignores the delinquency pause and counts the
	// days inside it as delinquent: it calls DelinquentDays with zero paused
	// days, so a row whose pause covers days between the overdue-since date and
	// the business date reads a larger count than the oracle. A row whose pause
	// starts ON the business date has zero paused days and is unaffected.
	wrongDelinquencyPauseIgnored
)

// wrongDelinquencyEvaluator is a DELIBERATELY WRONG implementation of the
// loan-delinquent-days seam, parameterised by which day-count defect it commits.
type wrongDelinquencyEvaluator struct {
	goEvaluator
	mode delinquencyWrongMode
}

func (w wrongDelinquencyEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Delinquency != nil {
		return wrongDelinquency(*req.Delinquency, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongDelinquency computes the two day-count cells with one defect and returns
// them, so the drive differs from the port on exactly the cells the committed
// rows pin.
func wrongDelinquency(r DelinquencyRequest, mode delinquencyWrongMode) (Expect, error) {
	business, err := time.Parse(civilDateLayout, r.BusinessDate)
	if err != nil {
		return Expect{}, fmt.Errorf("loan-delinquent-days: business_date %q is not a civil date: %w", r.BusinessDate, err)
	}
	if r.OverdueSinceDate == "" {
		switch mode {
		case wrongDelinquencyAbsentNonZero:
			// Days since the Unix epoch, the value a port that falls back to a
			// zero time.Time (or a raw epoch) would emit where the oracle
			// returns zero.
			days := loan.OverdueDays(time.Unix(0, 0).UTC(), business)
			s := strconv.FormatInt(days, 10)
			return Expect{OverdueDays: s, DelinquentDays: s}, nil
		default:
			return goDelinquency(r)
		}
	}
	since, err := time.Parse(civilDateLayout, r.OverdueSinceDate)
	if err != nil {
		return Expect{}, fmt.Errorf("loan-delinquent-days: overdue_since_date %q is not a civil date: %w", r.OverdueSinceDate, err)
	}
	if mode == wrongDelinquencyThirtyDayMonth {
		months := int64(business.Year()*12+int(business.Month())) -
			int64(since.Year()*12+int(since.Month()))
		days := months * 30
		if days < 0 {
			days = 0
		}
		s := strconv.FormatInt(days, 10)
		return Expect{OverdueDays: s, DelinquentDays: s}, nil
	}
	if mode == wrongDelinquencyPauseIgnored {
		// The pause is dropped: DelinquentDays is called with zero paused days,
		// so the days a resumed loan spent paused are counted as delinquent.
		overdue := loan.OverdueDays(since, business)
		delinquent := loan.DelinquentDays(overdue, 0, r.GraceDays)
		return Expect{
			OverdueDays:    strconv.FormatInt(overdue, 10),
			DelinquentDays: strconv.FormatInt(delinquent, 10),
		}, nil
	}
	return goDelinquency(r)
}

// wrongEvaluator is a DELIBERATELY WRONG implementation: it rounds the
// discriminating schedule-interest cell with HALF_EVEN instead of HALF_UP, so a
// vector that asserts that cell goes red (100050 minor vs the oracle's 100051).
type wrongEvaluator struct{ goEvaluator }

func (w wrongEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Schedule != nil {
		return goSchedule(*req.Schedule, roundHalfEven)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongSummaryEvaluator is a DELIBERATELY WRONG implementation of the summary
// seam: it derives total_outstanding from the PRINCIPAL and FEE buckets only,
// treating the interest and penalty outstanding buckets as already recovered
// income. While those buckets are empty the error is invisible, but on the
// pinned SEED-L03 post-repayment read-back the interest bucket holds 5618.53,
// so the derived total comes out 5618.53 short and the vector goes red.
type wrongSummaryEvaluator struct{ goEvaluator }

func (w wrongSummaryEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Summary != nil {
		return wrongSummary(*req.Summary)
	}
	return w.goEvaluator.Evaluate(req)
}

func wrongSummary(s SummaryRequest) (Expect, error) {
	principal, err := parseMinorText(s.PrincipalOutstanding)
	if err != nil {
		return Expect{}, err
	}
	fee, err := parseMinorText(s.FeeOutstanding)
	if err != nil {
		return Expect{}, err
	}
	total := principal + fee
	return Expect{SummaryTotalMinor: strconv.FormatInt(int64(total), 10)}, nil
}

// wrongStatusTransitionMode selects which deliberately-wrong lifecycle rule a
// wrongStatusTransitionEvaluator applies.
type wrongStatusTransitionMode int

const (
	// wrongTransitionIgnoresRepaidInFull is the RepaidInFull arm of the balance
	// re-derivation wired to the wrong fact: it behaves as if a loan whose
	// outstanding has reached zero still has outstanding, so an active loan
	// repaid in full stays ACTIVE instead of closing as obligations met.
	wrongTransitionIgnoresRepaidInFull wrongStatusTransitionMode = iota
	// wrongTransitionWriteOffClosesObligationsMet maps the write-off event to
	// CLOSED_OBLIGATIONS_MET instead of CLOSED_WRITTEN_OFF, losing the write-off
	// distinction.
	wrongTransitionWriteOffClosesObligationsMet
	// wrongTransitionApproveSkipsToActive jumps straight from
	// SUBMITTED_AND_PENDING_APPROVAL to ACTIVE on approval, as if approval also
	// disbursed.
	wrongTransitionApproveSkipsToActive
)

// wrongStatusTransitionEvaluator is a DELIBERATELY WRONG implementation of the
// loan-status-transition seam: it perturbs one observed transition according to
// its mode. Three vectors pin three defects the task calls out: the
// repaid-in-full balance transition ignored, the write-off event closing as
// obligations met, and approval skipping to active.
type wrongStatusTransitionEvaluator struct {
	goEvaluator
	mode wrongStatusTransitionMode
}

func (w wrongStatusTransitionEvaluator) Evaluate(req Request) (Expect, error) {
	if req.StatusTransition == nil {
		return w.goEvaluator.Evaluate(req)
	}
	corrected := *req.StatusTransition
	switch w.mode {
	case wrongTransitionIgnoresRepaidInFull:
		if corrected.Mode == statusTransitionModeBalance && corrected.RepaidInFull && !corrected.HasOutstanding {
			corrected.RepaidInFull = false
		}
		return goStatusTransition(corrected)
	case wrongTransitionWriteOffClosesObligationsMet:
		if corrected.Mode == statusTransitionModeEvent && corrected.Event == "WRITE_OFF_OUTSTANDING" {
			return Expect{
				NextStatusCode:        loan.StatusClosedObligationsMet.Code(),
				NextStatusStoredValue: loan.StatusClosedObligationsMet.StoredValue(),
			}, nil
		}
		return goStatusTransition(corrected)
	case wrongTransitionApproveSkipsToActive:
		if corrected.Mode == statusTransitionModeEvent && corrected.Event == "LOAN_APPROVED" {
			return Expect{
				NextStatusCode:        loan.StatusActive.Code(),
				NextStatusStoredValue: loan.StatusActive.StoredValue(),
			}, nil
		}
		return goStatusTransition(corrected)
	}
	return goStatusTransition(corrected)
}

// wrongStatusEvaluator is a DELIBERATELY WRONG implementation of the status
// seam: it decodes the stored value through the real table but then RE-ENCODES
// the resulting enum as its contiguous Go ordinal when it is persisted, exactly
// the iota collapse loan/status.go warns about (ACTIVE is stored 300, but the
// enum's ordinal is 3). The round-trip stored_value cell of every status vector
// therefore goes red (300 vs 3).
type wrongStatusEvaluator struct{ goEvaluator }

func (w wrongStatusEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Status != nil {
		st, ok := loan.LoanStatusFromStoredValue(req.Status.StoredValue)
		if !ok {
			return Expect{}, fmt.Errorf("loan-status: stored value %d is not a legal loan status", req.Status.StoredValue)
		}
		return Expect{StatusCode: st.Code(), StatusStoredValue: int32(st)}, nil
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongSummaryDropsPrincipalEvaluator is a DELIBERATELY WRONG implementation of
// the summary seam: it derives total_outstanding from the fee, interest and
// penalty buckets only, dropping the principal bucket as if the outstanding
// principal had already been repaid. Its pinning case is the principal-only
// SEED-L05 read-back, whose entire total lives in the principal bucket and so
// comes out as zero; on every interest-bearing read-back the derived total is
// short by the whole outstanding principal.
type wrongSummaryDropsPrincipalEvaluator struct{ goEvaluator }

func (w wrongSummaryDropsPrincipalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Summary != nil {
		return wrongSummaryDropsPrincipal(*req.Summary)
	}
	return w.goEvaluator.Evaluate(req)
}

func wrongSummaryDropsPrincipal(s SummaryRequest) (Expect, error) {
	interest, err := parseMinorText(s.InterestOutstanding)
	if err != nil {
		return Expect{}, err
	}
	fee, err := parseMinorText(s.FeeOutstanding)
	if err != nil {
		return Expect{}, err
	}
	penalty, err := parseMinorText(s.PenaltyOutstanding)
	if err != nil {
		return Expect{}, err
	}
	total := interest + fee + penalty
	return Expect{SummaryTotalMinor: strconv.FormatInt(int64(total), 10)}, nil
}

// wrongSummaryDropsFeeEvaluator is a DELIBERATELY WRONG implementation of the
// summary seam: it derives total_outstanding from the principal, interest and
// penalty buckets only, dropping the FEE bucket as if the outstanding fee had
// already been repaid. It exists because every summary vector that predates
// F-2026-09-09 carries fee = 0, where dropping the term changes nothing; its
// pinning case is the fee-bearing OHLGT-L03 read-back (fee 100.000000), whose
// total comes out 10000 minor units short.
type wrongSummaryDropsFeeEvaluator struct{ goEvaluator }

func (w wrongSummaryDropsFeeEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Summary != nil {
		return wrongSummaryDropsFee(*req.Summary)
	}
	return w.goEvaluator.Evaluate(req)
}

func wrongSummaryDropsFee(s SummaryRequest) (Expect, error) {
	principal, err := parseMinorText(s.PrincipalOutstanding)
	if err != nil {
		return Expect{}, err
	}
	interest, err := parseMinorText(s.InterestOutstanding)
	if err != nil {
		return Expect{}, err
	}
	penalty, err := parseMinorText(s.PenaltyOutstanding)
	if err != nil {
		return Expect{}, err
	}
	total := principal + interest + penalty
	return Expect{SummaryTotalMinor: strconv.FormatInt(int64(total), 10)}, nil
}

// wrongSummaryDropsPenaltyEvaluator is a DELIBERATELY WRONG implementation of
// the summary seam: it derives total_outstanding from the principal, interest
// and fee buckets only, dropping the PENALTY bucket. Its pinning cases are the
// two penalty-bearing read-backs: OHLGT-L03 (penalty 57.000000) and OHGLR-L01
// (penalty 57.000000, fee zero, so the PENALTY term alone is missing).
type wrongSummaryDropsPenaltyEvaluator struct{ goEvaluator }

func (w wrongSummaryDropsPenaltyEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Summary != nil {
		return wrongSummaryDropsPenalty(*req.Summary)
	}
	return w.goEvaluator.Evaluate(req)
}

func wrongSummaryDropsPenalty(s SummaryRequest) (Expect, error) {
	principal, err := parseMinorText(s.PrincipalOutstanding)
	if err != nil {
		return Expect{}, err
	}
	interest, err := parseMinorText(s.InterestOutstanding)
	if err != nil {
		return Expect{}, err
	}
	fee, err := parseMinorText(s.FeeOutstanding)
	if err != nil {
		return Expect{}, err
	}
	total := principal + interest + fee
	return Expect{SummaryTotalMinor: strconv.FormatInt(int64(total), 10)}, nil
}

// mifosOrderNoPrincipal is the repayment allocation order a port would produce
// by transcribing the mifos-standard-strategy but dropping the principal leg:
// penalties, fees, then interest — the loan never amortises because no repayment
// is ever allocated to principal.
var mifosOrderNoPrincipal = []loan.PaymentAllocationType{
	loan.PaymentDuePenalty, loan.PaymentDueFee, loan.PaymentDueInterest,
}

// mifosOrderNoFee is the repayment allocation order a port would produce by
// transcribing the mifos-standard-strategy but dropping the FEE leg: penalties,
// then interest, then principal. On a repayment whose fee bucket is zero it is
// indistinguishable from the correct order; on the fee-bearing OHLGT-L03 (loan
// 12) repayment the 100.00 fee is never allocated, so the allocation reports
// fee=0 and the whole 100.00 instead falls through to principal.
var mifosOrderNoFee = []loan.PaymentAllocationType{
	loan.PaymentDuePenalty, loan.PaymentDueInterest, loan.PaymentDuePrincipal,
}

// mifosOrderNoPenalty is the repayment allocation order a port would produce by
// transcribing the mifos-standard-strategy but dropping the PENALTY leg: fees,
// then interest, then principal. On a repayment whose penalty bucket is zero it
// is indistinguishable from the correct order; on the penalty-bearing OHLGT-L03
// (loan 12) repayment the 57.00 penalty is never allocated, so the allocation
// reports penalty=0 and the whole 57.00 instead falls through to principal.
var mifosOrderNoPenalty = []loan.PaymentAllocationType{
	loan.PaymentDueFee, loan.PaymentDueInterest, loan.PaymentDuePrincipal,
}

// wrongRepaymentEvaluator is a DELIBERATELY WRONG implementation of the
// repayment-allocation seam: its allocation order omits the principal bucket, so
// every repayment is recognised wholly against charges and interest and the loan
// never amortises. On the pinned SEED-L03 repayment the instalment's 7884.88 of
// principal is never allocated: the allocation reports principal=0 and the whole
// 7884.88 falls through to the leftover, and the vector goes red on both cells.
type wrongRepaymentEvaluator struct{ goEvaluator }

func (w wrongRepaymentEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Repayment != nil {
		return wrongRepayment(*req.Repayment, mifosOrderNoPrincipal)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongRepaymentDropsFeeEvaluator is a DELIBERATELY WRONG implementation of the
// repayment-allocation seam: its allocation order omits the fee bucket, so a
// repayment never pays a fee and the fee amount is recognised against interest
// and principal instead. It is invisible to every repayment vector whose fee
// bucket is zero (all of them before OHLGT-L03); on the fee-bearing OHLGT-L03
// repayment the 100.00 fee reads 0 and principal reads 100.00 long.
type wrongRepaymentDropsFeeEvaluator struct{ goEvaluator }

func (w wrongRepaymentDropsFeeEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Repayment != nil {
		return wrongRepayment(*req.Repayment, mifosOrderNoFee)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongRepaymentDropsPenaltyEvaluator is a DELIBERATELY WRONG implementation of
// the repayment-allocation seam: its allocation order omits the penalty bucket,
// so a repayment never pays a penalty and the penalty amount is recognised
// against interest and principal instead. It is invisible to every repayment
// vector whose penalty bucket is zero (all of them before OHLGT-L03); on the
// penalty-bearing OHLGT-L03 repayment the 57.00 penalty reads 0 and principal
// reads 57.00 long.
type wrongRepaymentDropsPenaltyEvaluator struct{ goEvaluator }

func (w wrongRepaymentDropsPenaltyEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Repayment != nil {
		return wrongRepayment(*req.Repayment, mifosOrderNoPenalty)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongRepayment runs the greedy allocation with the given (deliberately
// defective) bucket order and serialises the result as the seam's expectation.
func wrongRepayment(r RepaymentRequest, order []loan.PaymentAllocationType) (Expect, error) {
	penalty, err := parseMinorText(r.Outstanding.Penalty)
	if err != nil {
		return Expect{}, err
	}
	fee, err := parseMinorText(r.Outstanding.Fee)
	if err != nil {
		return Expect{}, err
	}
	interest, err := parseMinorText(r.Outstanding.Interest)
	if err != nil {
		return Expect{}, err
	}
	principal, err := parseMinorText(r.Outstanding.Principal)
	if err != nil {
		return Expect{}, err
	}
	amount, err := parseMinorText(r.AmountMinor)
	if err != nil {
		return Expect{}, err
	}
	outstanding := loan.Allocation{Penalty: penalty, Fee: fee, Interest: interest, Principal: principal}
	alloc, leftover := loan.AllocatePayment(outstanding, amount, order)
	return Expect{
		Allocation: &AllocationMoney{
			Penalty:   strconv.FormatInt(int64(alloc.Penalty), 10),
			Fee:       strconv.FormatInt(int64(alloc.Fee), 10),
			Interest:  strconv.FormatInt(int64(alloc.Interest), 10),
			Principal: strconv.FormatInt(int64(alloc.Principal), 10),
		},
		LeftoverMinor: strconv.FormatInt(int64(leftover), 10),
	}, nil
}

// txnBalanceWrongMode is which deliberately-wrong balance derivation to run.
type txnBalanceWrongMode int

const (
	// wrongWaiverMovesPrincipal subtracts the FULL amount of an interest
	// waiver from the running balance, as a port does when it mistakes the
	// waived interest for settled principal (the P1 defect: a waiver does not
	// move the outstanding balance).
	wrongWaiverMovesPrincipal txnBalanceWrongMode = iota
	// wrongAccrualSerializesZero emits a serialised zero balance cell on an
	// accrual row where the oracle leaves the balance ABSENT (the P2 defect:
	// null is not zero).
	wrongAccrualSerializesZero
	// wrongRepaymentSubtractsAmount subtracts the FULL amount of a repayment
	// from the running balance, folding the interest portion into the
	// principal as if the balance tracked payments rather than principal (the
	// P3 derive-drift defect).
	wrongRepaymentSubtractsAmount
)

// wrongTransactionBalanceEvaluator is a DELIBERATELY WRONG implementation of
// the transaction-balance seam, parameterised by which of the three pinned
// balance defects it commits. On any request that is not a transaction stream
// it delegates to the correct port, so each drive goes red ONLY on the vectors
// that observe its defect and stays green everywhere else (vector isolation).
type wrongTransactionBalanceEvaluator struct {
	goEvaluator
	mode txnBalanceWrongMode
}

func (w wrongTransactionBalanceEvaluator) Evaluate(req Request) (Expect, error) {
	if len(req.Transactions) > 0 {
		return wrongTransactionBalance(req.Transactions, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongTransactionBalance runs the defective derivation. The running balance
// tracks principal; each wrong mode changes exactly one leg of that
// derivation.
func wrongTransactionBalance(rows []TransactionRow, mode txnBalanceWrongMode) (Expect, error) {
	type posting struct {
		typ       loan.LoanTransactionType
		amount    loan.MinorUnits
		principal loan.MinorUnits
	}
	postings := make([]posting, len(rows))
	for i, tr := range rows {
		typ, ok := transactionPostingType(tr.Type)
		if !ok {
			return Expect{}, fmt.Errorf("loan-transaction-balance: type %q is not transcribed", tr.Type)
		}
		amount, err := parseMinorText(tr.AmountMinor)
		if err != nil {
			return Expect{}, err
		}
		var pp loan.MinorUnits
		if tr.PrincipalMinor != "" {
			pp, err = parseMinorText(tr.PrincipalMinor)
			if err != nil {
				return Expect{}, err
			}
		}
		postings[i] = posting{typ: typ, amount: amount, principal: pp}
	}

	var running loan.MinorUnits
	out := make([]TransactionBalanceRow, len(postings))
	for i, p := range postings {
		switch p.typ {
		case loan.TransactionAccrual:
			if mode == wrongAccrualSerializesZero {
				// A zero default for the missing balance cell.
				out[i] = TransactionBalanceRow{Serialized: true, BalanceMinor: "0"}
				continue
			}
			// Non-monetary: excluded from the balance stream.
			out[i] = TransactionBalanceRow{Serialized: false}
			continue
		case loan.TransactionDisbursement:
			running += p.amount
		case loan.TransactionWaiveInterest:
			deduct := p.principal
			if mode == wrongWaiverMovesPrincipal {
				deduct = p.amount
			}
			running -= deduct
		case loan.TransactionRepayment:
			deduct := p.principal
			if mode == wrongRepaymentSubtractsAmount {
				deduct = p.amount
			}
			running -= deduct
		default:
			return Expect{}, fmt.Errorf("loan-transaction-balance: type %q is not transcribed", p.typ)
		}
		if running < 0 {
			running = 0
		}
		out[i] = TransactionBalanceRow{Serialized: true, BalanceMinor: strconv.FormatInt(int64(running), 10)}
	}
	return Expect{TransactionRows: out}, nil
}

// journalBatchWrongMode selects which deliberately-wrong batch reconstruction
// to run.
type journalBatchWrongMode int

const (
	// wrongBatchFirstPairOnly sums only the legs of the FIRST transaction id, as
	// if a batch were one pair. On the pinned two-pair OHLGR-L01 read-back the
	// fee pair is never seen, so both totals read 100000.00 instead of 100100.00.
	wrongBatchFirstPairOnly journalBatchWrongMode = iota
	// wrongBatchDropsSecondPair sums every transaction id but the LAST, as if the
	// fee pair were not part of the disbursement's batch. On the pinned read-back
	// the dropped pair is the fee pair (L18), so both totals read 100000.00.
	wrongBatchDropsSecondPair
	// wrongBatchNetsAccount nets the two legs on each GL account before summing,
	// so OHLGR-Fund-Source contributes 100000.00 - 100.00 = 99900.00 to one side.
	// The two totals stay EQUAL (the difference is preserved) while the money
	// actually posted moves, which only a per-side comparison can see.
	wrongBatchNetsAccount
	// wrongBatchSwapsFirstPairSides reverses the two legs of the first
	// transaction id's pair, crediting the account that was debited and debiting
	// the account that was credited. Both totals are UNCHANGED — a balanced
	// pair swapped is still balanced — so the two total cells cannot see it.
	// What moves is WHICH account takes WHICH side, the per-(transaction,
	// account) cell this drive exists to isolate.
	wrongBatchSwapsFirstPairSides
	// wrongBatchRoutesFeeThroughDisbursementAccounts posts every leg of a later
	// transaction id through the FIRST transaction id's account mapping: the fee
	// pair is routed to the disbursement's accounts instead of its own. Sides
	// and amounts are untouched, so BOTH totals stay observed and every leg
	// keeps its side; only WHICH GL account a fee leg names moves. It is the
	// mapping defect the totals, the side swap and the truncation drives all
	// miss, because a batch that posts a fee to the loan portfolio instead of to
	// income still balances exactly.
	wrongBatchRoutesFeeThroughDisbursementAccounts
	// wrongBatchCollapsesCreditsToOneAccount merges, per transaction, every
	// credit leg into ONE credit to that transaction's first credit account,
	// leaving the debit total untouched. On the five-leg repayment L53 the four
	// bucket credits (Loan-Portfolio 91203.12, Interest-Receivable 6618.53,
	// Fees-Receivable 100.00, Penalties-Receivable 57.00) collapse to a single
	// Loan-Portfolio credit of 97978.65: both totals STILL BALANCE and equal the
	// observed 9797865, and only the accounts the credits name move — the
	// collapse the two total cells cannot see and the per-(transaction, account)
	// side list exists to catch.
	wrongBatchCollapsesCreditsToOneAccount
	// wrongBatchPairsLegsTwoAtATime walks, per transaction, the legs two at a
	// time and DROPS any trailing unpaired leg, as logic that assumes every
	// posting is a leg-PAIR does. The five-leg L53 batch is ODD, so the fifth
	// leg (the single debit) is dropped: the debit total reads zero while the
	// four credits still sum to the whole 9797865. No existing drive is an
	// odd-count defect; the pair-based drives drop a whole transaction instead.
	wrongBatchPairsLegsTwoAtATime
	// wrongBatchDebitFromFirstTwoCredits posts the debit as the sum of only the
	// FIRST TWO credit legs instead of all four, so the repayment's debit reads
	// 9120312+661853=9782165 instead of 9797865 while every leg and the credit
	// total stay observed. It is the partial-debit defect the collapse and
	// odd-count drives are blind to.
	wrongBatchDebitFromFirstTwoCredits
	// wrongBatchRoutesAccrualIncomeToFirstAccount routes every CREDIT leg of a
	// single transaction that carries MORE THAN ONE PAIR to that transaction's
	// FIRST income account, as an accrual port with one income account for all
	// charge families does. It is the intra-transaction analogue of
	// wrongBatchRoutesFeeThroughDisbursementAccounts: the disbursement mapping
	// defect keys on the transaction BOUNDARY, so it is inert on a batch whose
	// two families share one transaction id, and this drive is the only one that
	// sees the accrual. On L25 the interest pair (interest-receivable debit /
	// Interest-On-Loans credit, 92115) and the fee pair (fees-receivable debit /
	// Income-From-Fees credit, 10000) keep every leg, side and both totals at
	// the observed 102115, and only the fee credit's account moves; on L09 (each
	// transaction a clean one-debit/one-credit pair) and on the five-leg L53
	// repayment (one debit, four credits) it is inert, so each vector it reddens
	// is the accrual shape alone.
	wrongBatchRoutesAccrualIncomeToFirstAccount
)

// wrongJournalEntryBatchEvaluator is a DELIBERATELY WRONG implementation of the
// journal-entry-batch seam, parameterised by which reconstruction defect it
// commits. On any request that is not a journal-entry batch it delegates to the
// correct port, so each drive goes red ONLY on this seam's vectors and stays
// green everywhere else (vector isolation).
type wrongJournalEntryBatchEvaluator struct {
	goEvaluator
	mode journalBatchWrongMode
}

func (w wrongJournalEntryBatchEvaluator) Evaluate(req Request) (Expect, error) {
	if len(req.JournalEntries) > 0 {
		return wrongJournalEntryBatch(req.JournalEntries, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongJournalEntryBatch runs the defective reconstruction. Each mode changes
// exactly one leg of the correct "sum every leg on its side" derivation.
func wrongJournalEntryBatch(legs []JournalEntryLeg, mode journalBatchWrongMode) (Expect, error) {
	type parsedLeg struct {
		txn    string
		acct   string
		side   loan.JournalEntrySide
		amount loan.MinorUnits
	}
	parsed := make([]parsedLeg, len(legs))
	var order []string
	seenTxn := map[string]bool{}
	for i, l := range legs {
		side, ok := journalEntrySide(l.EntryType)
		if !ok {
			return Expect{}, fmt.Errorf("loan-journal-entry-batch: entry_type %q is not transcribed", l.EntryType)
		}
		amount, err := parseMinorText(l.AmountMinor)
		if err != nil {
			return Expect{}, err
		}
		parsed[i] = parsedLeg{txn: l.TransactionID, acct: l.Account, side: side, amount: amount}
		if !seenTxn[l.TransactionID] {
			seenTxn[l.TransactionID] = true
			order = append(order, l.TransactionID)
		}
	}

	// The pair swap is the one defect the two total cells cannot see: reversing
	// both legs of a balanced pair keeps each side's sum. Applying it only for
	// its named mode keeps every other drive isolated to its own defect, so the
	// swap drive is the ONLY one of the five that moves the side cells.
	if mode == wrongBatchSwapsFirstPairSides {
		first := order[0]
		for i := range parsed {
			if parsed[i].txn == first {
				parsed[i].side = flipJournalEntrySide(parsed[i].side)
			}
		}
	}

	// The account-mapping defect is the one the side cells' SIDE term cannot
	// see and the side SWAP cannot either: the fee pair's own accounts are
	// replaced by the disbursement transaction's accounts for the same side,
	// leaving every leg's side and amount untouched. Both totals still equal the
	// observed sums and the side list still reads DEBIT/CREDIT exactly as
	// observed; only the account a fee leg names moves.
	if mode == wrongBatchRoutesFeeThroughDisbursementAccounts {
		first := order[0]
		bySide := map[loan.JournalEntrySide]string{}
		for _, l := range parsed {
			if l.txn != first {
				continue
			}
			if _, ok := bySide[l.side]; !ok {
				bySide[l.side] = l.acct
			}
		}
		for i := range parsed {
			if parsed[i].txn == first {
				continue
			}
			if acct, ok := bySide[parsed[i].side]; ok {
				parsed[i].acct = acct
			}
		}
	}

	// The accrual-income defect is the intra-transaction analogue of the account
	// mapping above. Where a single transaction carries MORE THAN ONE PAIR — an
	// accrual posting one receivable/income pair per charge family — a port with
	// a single income account for all families routes EVERY credit of that
	// transaction to the FIRST income account it saw. The ≥2 debits and ≥2
	// credits that identify such a transaction are exactly what keeps this drive
	// inert on a disbursement batch (each transaction is a one-debit/one-credit
	// pair) and on the five-leg repayment (one debit, four credits), so it reddens
	// the accrual shape and nothing else.
	if mode == wrongBatchRoutesAccrualIncomeToFirstAccount {
		for _, txn := range order {
			debits, credits := 0, 0
			firstCreditAcct := ""
			for _, l := range parsed {
				if l.txn != txn {
					continue
				}
				switch l.side {
				case loan.JournalEntryDebit:
					debits++
				case loan.JournalEntryCredit:
					credits++
					if firstCreditAcct == "" {
						firstCreditAcct = l.acct
					}
				}
			}
			if debits < 2 || credits < 2 || firstCreditAcct == "" {
				continue
			}
			for i := range parsed {
				if parsed[i].txn == txn && parsed[i].side == loan.JournalEntryCredit {
					parsed[i].acct = firstCreditAcct
				}
			}
		}
	}

	// The odd-count and credit-collapse defects rebuild the POSTED leg list
	// itself; every other mode posts the parsed legs unchanged. The rebuilds
	// are per-transaction, so the two-pair LN-L09 batch (each transaction a
	// clean pair, one credit) passes both drives untouched and each new drive
	// reddens only the five-leg repayment posting it targets.
	posted := parsed
	switch mode {
	case wrongBatchCollapsesCreditsToOneAccount:
		var out []parsedLeg
		for _, txn := range order {
			var firstAcct string
			var sum loan.MinorUnits
			credits := 0
			for _, l := range parsed {
				if l.txn != txn {
					continue
				}
				if l.side == loan.JournalEntryCredit {
					if credits == 0 {
						firstAcct = l.acct
					}
					sum += l.amount
					credits++
					continue
				}
				out = append(out, l)
			}
			if credits > 0 {
				out = append(out, parsedLeg{txn: txn, acct: firstAcct, side: loan.JournalEntryCredit, amount: sum})
			}
		}
		posted = out
	case wrongBatchPairsLegsTwoAtATime:
		var out []parsedLeg
		for _, txn := range order {
			var group []parsedLeg
			for _, l := range parsed {
				if l.txn == txn {
					group = append(group, l)
				}
			}
			for i := 0; i+1 < len(group); i += 2 {
				out = append(out, group[i], group[i+1])
			}
		}
		posted = out
	}

	var debits, credits loan.MinorUnits
	add := func(l parsedLeg) {
		if l.side == loan.JournalEntryDebit {
			debits += l.amount
		} else {
			credits += l.amount
		}
	}
	switch mode {
	case wrongBatchFirstPairOnly:
		first := order[0]
		for _, l := range posted {
			if l.txn == first {
				add(l)
			}
		}
	case wrongBatchDropsSecondPair:
		last := order[len(order)-1]
		for _, l := range posted {
			if l.txn != last {
				add(l)
			}
		}
	case wrongBatchNetsAccount:
		type key struct {
			acct string
			side loan.JournalEntrySide
		}
		totals := map[key]loan.MinorUnits{}
		var accounts []string
		seenAcct := map[string]bool{}
		for _, l := range posted {
			totals[key{l.acct, l.side}] += l.amount
			if !seenAcct[l.acct] {
				seenAcct[l.acct] = true
				accounts = append(accounts, l.acct)
			}
		}
		for _, acct := range accounts {
			d := totals[key{acct, loan.JournalEntryDebit}]
			c := totals[key{acct, loan.JournalEntryCredit}]
			switch {
			case d > c:
				debits += d - c
			case c > d:
				credits += c - d
			}
		}
	case wrongBatchDebitFromFirstTwoCredits:
		// Every leg and the credit total stay observed; the debit is posted as
		// the sum of the first two credits, as if only the first two allocation
		// buckets settled into cash.
		seenCredits := 0
		for _, l := range posted {
			if l.side != loan.JournalEntryCredit {
				continue
			}
			credits += l.amount
			if seenCredits < 2 {
				debits += l.amount
				seenCredits++
			}
		}
	default:
		// wrongBatchSwapsFirstPairSides, wrongBatchRoutesFeeThroughDisbursementAccounts,
		// wrongBatchRoutesAccrualIncomeToFirstAccount and the zero value sum every
		// leg on its (possibly remapped/flipped) side: none of these defects
		// changes any amount, so both totals stay observed.
		for _, l := range posted {
			add(l)
		}
	}

	sides := make([]JournalEntryAccountSideCell, len(posted))
	for i, l := range posted {
		sides[i] = JournalEntryAccountSideCell{
			TransactionID: l.txn,
			Account:       l.acct,
			EntryType:     journalEntrySideCode(l.side),
		}
	}
	return Expect{
		JournalEntryDebitsMinor:  strconv.FormatInt(int64(debits), 10),
		JournalEntryCreditsMinor: strconv.FormatInt(int64(credits), 10),
		JournalEntryAccountSides: sides,
	}, nil
}

// writeOffBusinessDateText is the write-off's business date (2026-09-03), the
// date a port that reads the reversal as "post the mirror at today's business
// date" stamps on the counter-legs. It is deliberately NOT the reversed
// transaction's own date (2026-09-02). Only the business-date drive uses it.
const writeOffBusinessDateText = "2026-09-03"

// reversalWrongMode selects which deliberately-wrong loan-transaction-reversal
// a drive commits. Each is a port a reasonable reader might write, and each is
// discriminated by the committed L46 vector.
type reversalWrongMode int

const (
	// wrongReversalDuplicatesInsteadOfReverses APPENDS a second copy of each leg
	// on the SAME side instead of the opposite side. The transaction still has
	// equal debit and credit totals (1156 = 1156), so a batch-sum port cannot
	// see it; only the per-leg side cells can.
	wrongReversalDuplicatesInsteadOfReverses reversalWrongMode = iota
	// wrongReversalFlagsOriginalsReversed posts the mirrors correctly but also
	// flags each ORIGINAL reversed = true — the manual-reversal semantics
	// applied to the loan path. Only a vector that grades each original's
	// `reversed` flag can see it.
	wrongReversalFlagsOriginalsReversed
	// wrongReversalFreshTransactionID posts the mirrors on a FRESH transaction
	// id (the manual path's other behaviour) instead of on the reversed
	// transaction's own id.
	wrongReversalFreshTransactionID
	// wrongReversalBusinessDate dates the counter-legs at the business date the
	// reversal was requested (2026-09-03) instead of the reversed transaction's
	// date (2026-09-02).
	wrongReversalBusinessDate
)

// wrongReversalEvaluator is a DELIBERATELY WRONG implementation of the
// loan-transaction-reversal seam, parameterised by which reversal defect it
// commits. On any request that is not a reversal it delegates to the correct
// port, so each drive goes red ONLY on this seam's vector and stays green
// everywhere else (vector isolation).
type wrongReversalEvaluator struct {
	goEvaluator
	mode reversalWrongMode
}

func (w wrongReversalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Reversal != nil {
		return wrongReversal(*req.Reversal, w.mode)
	}
	return w.goEvaluator.Evaluate(req)
}

// wrongReversal runs the correct append-only reversal and then applies exactly
// one defect to the result, so each drive differs from the port on exactly the
// cells its defect moves.
func wrongReversal(r ReversalRequest, mode reversalWrongMode) (Expect, error) {
	got, err := goReversal(r)
	if err != nil {
		return Expect{}, err
	}
	legs := got.ReversalLegs
	n := len(r.JournalEntries)
	switch mode {
	case wrongReversalDuplicatesInsteadOfReverses:
		for i := 0; i < n; i++ {
			legs[n+i].EntryType = legs[i].EntryType
		}
	case wrongReversalFlagsOriginalsReversed:
		for i := 0; i < n; i++ {
			legs[i].Reversed = true
		}
	case wrongReversalFreshTransactionID:
		for i := 0; i < n; i++ {
			legs[n+i].TransactionID = legs[i].TransactionID + "-REV"
		}
	case wrongReversalBusinessDate:
		for i := 0; i < n; i++ {
			legs[n+i].TransactionDate = writeOffBusinessDateText
		}
	}
	return Expect{ReversalLegs: legs}, nil
}

func init() {
	Register("loan-go", NewGoEvaluator())
	RegisterWrong("loan-wrong-half-even-schedule-interest",
		"rounds the discriminating schedule-interest cell with HALF_EVEN instead of HALF_UP, "+
			"so the pinned 1000.51 observation reads 1000.50 and the vector goes red",
		wrongEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("loan-wrong-summary-interest-not-outstanding",
		"derives total_outstanding from the principal and fee buckets only, treating the interest "+
			"and penalty outstanding buckets as recovered, so the pinned SEED-L03 total (97733.65) "+
			"reads 5618.53 short and the vector goes red",
		wrongSummaryEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("loan-wrong-status-iota-ordinal",
		"re-encodes a decoded loan status as its contiguous Go enum ordinal instead of its "+
			"non-contiguous stored value (ACTIVE 3, not 300), so the round-trip stored_value "+
			"cell of every status vector goes red",
		wrongStatusEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("loan-wrong-summary-drops-principal",
		"derives total_outstanding from the fee, interest and penalty buckets only, dropping the "+
			"principal bucket as if the outstanding principal were already repaid, so the pinned "+
			"principal-only SEED-L05 total (41850.09) reads 0 and the vector goes red",
		wrongSummaryDropsPrincipalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("loan-wrong-summary-drops-fee",
		"derives total_outstanding from the principal, interest and penalty buckets only, dropping the "+
			"fee bucket as if the outstanding fee had already been repaid, so the pinned fee-bearing "+
			"OHLGT-L03 total (106775.53) reads 100.00 short and the vector goes red",
		wrongSummaryDropsFeeEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("loan-wrong-summary-drops-penalty",
		"derives total_outstanding from the principal, interest and fee buckets only, dropping the "+
			"penalty bucket, so the pinned penalty-bearing OHLGT-L03 total (106775.53) reads 57.00 "+
			"short and the OHGLR-L01 vector (fee 0, penalty 57.00) goes red on the penalty term alone",
		wrongSummaryDropsPenaltyEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("loan-wrong-repayment-omits-principal",
		"allocates a repayment across penalties, fees and interest but never the principal bucket, "+
			"so the pinned SEED-L03 repayment reports principal=0 and the whole 7884.88 instalment "+
			"principal falls through to the leftover, and the vector goes red on both cells",
		wrongRepaymentEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("loan-wrong-allocation-drops-fee",
		"allocates a repayment across penalties, interest and principal but never the fee bucket, so a "+
			"fee-bearing repayment reports fee=0 and the whole fee falls through to principal; invisible "+
			"to every repayment vector whose fee bucket is zero, it goes red on the pinned OHLGT-L03 "+
			"allocation (fee 100.00 reads 0)",
		wrongRepaymentDropsFeeEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("loan-wrong-allocation-drops-penalty",
		"allocates a repayment across fees, interest and principal but never the penalty bucket, so a "+
			"penalty-bearing repayment reports penalty=0 and the whole penalty falls through to principal; "+
			"invisible to every repayment vector whose penalty bucket is zero, it goes red on the pinned "+
			"OHLGT-L03 allocation (penalty 57.00 reads 0)",
		wrongRepaymentDropsPenaltyEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("loan-wrong-transaction-balance-waiver-moves-principal",
		"subtracts the full amount of an interest waiver from the outstanding balance, as if the "+
			"waived interest settled principal, so the pinned post-waiver read-back (balance unmoved "+
			"at 100000.00) reads 1000.00 short and the vector goes red",
		wrongTransactionBalanceEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWaiverMovesPrincipal})
	RegisterWrong("loan-wrong-transaction-balance-accrual-zero",
		"emits a serialised zero balance on an accrual row where the oracle leaves the balance "+
			"ABSENT, so every transaction-balance vector's accrual row goes red on the serialisation cell",
		wrongTransactionBalanceEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongAccrualSerializesZero})
	RegisterWrong("loan-wrong-transaction-balance-folds-repayment-interest",
		"subtracts the full amount of a repayment from the outstanding balance, folding the interest "+
			"portion into principal, so the pinned SEED-L03 post-repayment balance (92115.12) reads "+
			"8884.88-portion short and the vector goes red",
		wrongTransactionBalanceEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongRepaymentSubtractsAmount})
	RegisterWrong("loan-wrong-journal-entry-batch-first-pair-only",
		"sums only the FIRST transaction id's legs of a loan-produced journal-entry batch, as if a "+
			"batch were one pair, so the pinned two-pair OHLGR-L01 read-back reads 100000.00/100000.00 "+
			"instead of 100100.00/100100.00 and both total cells go red",
		wrongJournalEntryBatchEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongBatchFirstPairOnly})
	RegisterWrong("loan-wrong-journal-entry-batch-drops-fee-pair",
		"sums every transaction id of a loan-produced journal-entry batch but the LAST, dropping the "+
			"fee pair (L18) from the pinned two-pair OHLGR-L01 read-back, so both totals read 100000.00 "+
			"instead of 100100.00 and both total cells go red",
		wrongJournalEntryBatchEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongBatchDropsSecondPair})
	RegisterWrong("loan-wrong-journal-entry-batch-nets-account",
		"nets the two legs on each GL account before summing, so the pinned OHLGR-Fund-Source legs "+
			"(debit 100.00, credit 100000.00) contribute a single 99900.00 position; both totals stay "+
			"EQUAL at 100000.00 but differ from the observed 100100.00, so the two per-side cells go red",
		wrongJournalEntryBatchEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongBatchNetsAccount})
	RegisterWrong("loan-wrong-journal-entry-batch-swaps-first-pair-sides",
		"reverses both legs of the FIRST transaction id's pair, crediting OHLGR-Loan-Portfolio and "+
			"debiting OHLGR-Fund-Source; a balanced pair swapped is still balanced, so both totals stay "+
			"EQUAL at the observed 100100.00 and only the per-(transaction, account) side cells go red — "+
			"the defect the two total cells cannot see",
		wrongJournalEntryBatchEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongBatchSwapsFirstPairSides})
	RegisterWrong("loan-wrong-journal-entry-batch-maps-fee-to-disbursement-accounts",
		"routes every leg of a LATER transaction id through the FIRST transaction id's account "+
			"mapping, so the pinned fee pair L18 posts DEBIT OHLGR-Loan-Portfolio / CREDIT "+
			"OHLGR-Fund-Source instead of its own DEBIT OHLGR-Fund-Source / CREDIT "+
			"OHLGR-Income-From-Fees; all four sides and both totals stay exactly at the observed "+
			"100100.00/100100.00, so only the per-(transaction, account) side cells move — a fee "+
			"posted to the loan portfolio instead of to income, and every total still balances",
		wrongJournalEntryBatchEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongBatchRoutesFeeThroughDisbursementAccounts})
	RegisterWrong("loan-wrong-journal-entry-batch-collapses-credits-to-one-account",
		"merges the four allocation-bucket credits of the five-leg L53 repayment into ONE "+
			"OHLGR-Loan-Portfolio credit of 97978.65; both totals still BALANCE at the observed "+
			"9797865, so only the per-(transaction, account) side list goes red — the four "+
			"distinct bucket accounts are gone while every total stays right",
		wrongJournalEntryBatchEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongBatchCollapsesCreditsToOneAccount})
	RegisterWrong("loan-wrong-journal-entry-batch-pairs-legs-two-at-a-time",
		"walks the odd five-leg L53 repayment two legs at a time and DROPS the trailing unpaired "+
			"leg (the single DEBIT OHLGR-Fund-Source), as logic that assumes every posting is a "+
			"leg-PAIR does; the debit total reads 0 while the four credits still sum to 9797865, "+
			"so the debit cell goes red on an ODD leg count where no pair-based drive can reach",
		wrongJournalEntryBatchEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongBatchPairsLegsTwoAtATime})
	RegisterWrong("loan-wrong-journal-entry-batch-debit-from-first-two-credits",
		"posts the debit as the sum of only the FIRST TWO credit legs (9120312+661853=9782165) "+
			"instead of all four (9797865), so the debit cell reads 9782165 while every leg and "+
			"the credit total stay observed — a partial debit the collapse and odd-count drives "+
			"are blind to",
		wrongJournalEntryBatchEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongBatchDebitFromFirstTwoCredits})
	RegisterWrong("loan-wrong-journal-entry-batch-routes-accrual-income-to-one-account",
		"routes every CREDIT leg of a single transaction carrying MORE THAN ONE PAIR to that "+
			"transaction's FIRST income account, as an accrual port with one income account for "+
			"all charge families does; on the pinned L25 accrual (interest pair 92115 + fee pair "+
			"10000) and L30 accrual (interest pair 84151 + penalty pair 5700) every leg, every "+
			"side and both totals stay exactly at the observed 102115/102115 and 89851/89851, so "+
			"only the per-(transaction, account) side cells move — one charge family's income "+
			"posted to another family's income account, and every total still balances. It is "+
			"inert on the multi-pair LN-L09 batch (each transaction a one-debit/one-credit pair) "+
			"and on the five-leg L53 repayment (one debit, four credits), which is why the "+
			"transaction-boundary mapping drive cannot see the accrual",
		wrongJournalEntryBatchEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongBatchRoutesAccrualIncomeToFirstAccount})
	RegisterWrong("loan-wrong-schedule-amortization-drops-final-component",
		"reconstructs the whole repayment schedule without the LAST period's principal "+
			"component, as a port does when it reads only the pre-adjustment rows, so the pinned "+
			"loan-5 schedule's sum falls 348748 minor units short and the final outstanding "+
			"principal balance is left at 348748 instead of 0",
		wrongScheduleAmortizationEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongAmortizationDropsFinalComponent})
	RegisterWrong("loan-wrong-schedule-amortization-uniform-truncated",
		"recomputes every period's principal as floor(disbursed/periods) and never places the "+
			"division remainder, so the pinned loan-5 schedule (4185009 minor units over 12 "+
			"periods) sums to 4185000 and leaves a final balance of 9 rather than 0 — the "+
			"truncation residue the whole-schedule property exists to catch",
		wrongScheduleAmortizationEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongAmortizationUniformTruncated})
	RegisterWrong("loan-wrong-schedule-amortization-uniform-rounded-up",
		"recomputes every period's principal as ceil(disbursed/periods), over-amortising by the "+
			"rounded-up excess, so the pinned loan-5 schedule sums to 4185012 and the final "+
			"outstanding principal balance goes negative at -3 instead of 0",
		wrongScheduleAmortizationEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongAmortizationUniformRoundedUp})
	RegisterWrong("loan-wrong-delinquency-thirty-day-month",
		"approximates every month as 30 days, counting whole calendar months between the "+
			"overdue-since date and the business date, so the pinned rows (June/July/August 1 -> "+
			"2026-09-01) read 90/60/30 where the oracle read 92/62/31; it treats months of unequal "+
			"length as interchangeable and goes red on every non-zero delinquent-days vector",
		wrongDelinquencyEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongDelinquencyThirtyDayMonth})
	RegisterWrong("loan-wrong-delinquency-absent-nonzero",
		"treats an ABSENT overdue-since date as an elapsed-since-epoch day count instead of "+
			"zero, so the pinned absent-date read-backs (loan 3 and loan L06 at 2026-09-01) read a "+
			"non-zero day count where the oracle read 0 and the vector goes red",
		wrongDelinquencyEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongDelinquencyAbsentNonZero})
	RegisterWrong("loan-wrong-delinquency-pause-ignored",
		"ignores the delinquency pause and counts the days inside it as delinquent, calling "+
			"DelinquentDays with zero paused days, so the pinned paused rows read 61-3=58 and "+
			"4-3=1 where the oracle read 44 and 0; a pause that starts ON the business date has "+
			"zero paused days and is unaffected",
		wrongDelinquencyEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongDelinquencyPauseIgnored})
	RegisterWrong("loan-wrong-writeoff-principal-only",
		"discharges only the principal bucket of a write-off, as a port that reads the write-off "+
			"as a pure principal charge-off does, so the pinned loan-11 write-off reports "+
			"interest/fee/penalty 0 and a total of 10000000 where the oracle discharged all four "+
			"buckets to 10677553; it goes red on the three dropped buckets and the amount",
		wrongWriteOffEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWriteOffPrincipalOnly})
	RegisterWrong("loan-wrong-writeoff-principal-and-interest",
		"discharges the principal and interest buckets of a write-off but drops both charge "+
			"buckets, so the pinned loan-11 write-off reports fee 0 and penalty 0 and a total of "+
			"10661853 instead of the observed 10677553 — the blind spot that lets the two "+
			"non-zero, distinct charge buckets fall out",
		wrongWriteOffEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWriteOffPrincipalAndInterest})
	RegisterWrong("loan-wrong-writeoff-drops-fee",
		"discharges principal, interest and penalty of a write-off but not the fee bucket, so the "+
			"pinned loan-11 write-off reports fee 0 and a total 10000 minor units short of the "+
			"observed 10677553 while the penalty bucket stays right",
		wrongWriteOffEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWriteOffDropsFee})
	RegisterWrong("loan-wrong-writeoff-drops-penalty",
		"discharges principal, interest and fee of a write-off but not the penalty bucket, so the "+
			"pinned loan-11 write-off reports penalty 0 and a total 5700 minor units short of the "+
			"observed 10677553 while the fee bucket stays right",
		wrongWriteOffEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWriteOffDropsPenalty})
	RegisterWrong("loan-wrong-writeoff-swaps-fee-and-penalty",
		"discharges all four buckets of a write-off but posts the fee outstanding into the penalty "+
			"portion and the penalty outstanding into the fee portion; the total stays exactly the "+
			"observed 10677553, so only the fee and penalty bucket cells move — the swap the "+
			"observed distinct fee (10000) and penalty (5700) exist to catch",
		wrongWriteOffEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWriteOffSwapsFeeAndPenalty})
	RegisterWrong("loan-wrong-reversal-duplicates-instead-of-reverses",
		"appends a second copy of every L46 leg on the SAME side instead of the opposite side, "+
			"as a port that reads a reversal as a re-post does; the transaction's debit and credit "+
			"totals still both read 1156, so only the per-leg side cells see the duplicate where a "+
			"batch sum cannot",
		wrongReversalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongReversalDuplicatesInsteadOfReverses})
	RegisterWrong("loan-wrong-reversal-flags-originals",
		"posts the two L46 counter-legs correctly but also flags each ORIGINAL reversed = true, "+
			"borrowing the manual revertJournalEntry semantics (which flags the originals); the "+
			"loan reversal changes no original, so only a vector grading each original's reversed "+
			"flag sees it",
		wrongReversalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongReversalFlagsOriginalsReversed})
	RegisterWrong("loan-wrong-reversal-fresh-transaction-id",
		"posts the two L46 counter-legs on a FRESH transaction id (L46-REV) instead of the "+
			"reversed transaction's own id, the manual revertJournalEntry path's other semantics; "+
			"every side, account, amount and date stays right and only the transaction-id cells move",
		wrongReversalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongReversalFreshTransactionID})
	RegisterWrong("loan-wrong-reversal-business-date",
		"dates the two L46 counter-legs at the business date the reversal was requested "+
			"(2026-09-03) instead of the reversed transaction's own date (2026-09-02); every side, "+
			"account, amount and transaction id stays right and only the counter-leg date cells move",
		wrongReversalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongReversalBusinessDate})
	RegisterWrong("loan-wrong-writeoff-journal-one-debit-per-portion",
		"posts one debit per discharged portion instead of ONE debit of the total, so the pinned "+
			"loan-11 L54 batch carries four debits (10000000/661853/10000/5700) after the four "+
			"credits; every account and side is right and each side still sums to 10677553, but the "+
			"leg count grows five to eight and only the ordered leg cells see the extra debits",
		wrongWriteOffJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWriteOffJournalOneDebitPerPortion})
	RegisterWrong("loan-wrong-writeoff-journal-debits-principal-only",
		"posts the four credits of a write-off but debits only the principal portion, so the pinned "+
			"loan-11 L54 batch credits 10677553 while the single debit reads 10000000 and the batch "+
			"no longer balances",
		wrongWriteOffJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWriteOffJournalDebitsPrincipalOnly})
	RegisterWrong("loan-wrong-writeoff-journal-debits-loan-portfolio",
		"debits the loan-portfolio account instead of the losses-written-off account, so the pinned "+
			"loan-11 L54 debit moves from OHLGR-50010 Losses-Written-Off to OHLGR-10010 "+
			"Loan-Portfolio while every amount, side and total stays observed — the account cell the "+
			"batch totals cannot see",
		wrongWriteOffJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWriteOffJournalDebitsLoanPortfolio})
	RegisterWrong("loan-wrong-writeoff-journal-swaps-fee-and-penalty",
		"credits the fee portion to the penalties-receivable account and the penalty portion to the "+
			"fee account; the pinned distinct fee (10000) and penalty (5700) both stay non-zero and "+
			"every total is unchanged, so only the two account cells move — the swap they exist to catch",
		wrongWriteOffJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongWriteOffJournalSwapsFeeAndPenalty})
	RegisterWrong("loan-wrong-chargeoff-journal-ignores-fraud",
		"debits the principal portion of a charge-off to the ordinary charge-off expense account even "+
			"when the loan is marked fraud, as a port that never reads the fraud flag does; the "+
			"pinned fraud loan-15 L44 principal debit moves from the fraud expense account (13) to "+
			"the ordinary charge-off expense account (14) while the non-fraud observations are "+
			"unaffected — the fraud flag's effect on the account cell",
		wrongChargeOffJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongChargeOffJournalIgnoresFraud})
	RegisterWrong("loan-wrong-chargedoff-writeoff-debits-fund-source",
		"posts the per-portion FUND_SOURCE debits populateCreditDebitMaps accumulates instead of the "+
			"one LOSSES_WRITTEN_OFF debit the oracle posts, as a port that iterates the debit map too "+
			"does; the credits are unchanged but the single losses-written-off debit becomes one "+
			"fund-source debit per credit, so the leg count grows, the last leg's account moves, and "+
			"the batch no longer balances — the debit map the oracle deliberately never posts",
		wrongChargedOffWriteOffJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongChargedOffWriteOffDebitsFundSource})
	RegisterWrong("loan-wrong-repayment-journal-one-debit-per-portion",
		"posts one FUND_SOURCE debit per credited portion instead of the one total FUND_SOURCE debit "+
			"the oracle posts, as a port that emits a debit for every credit does; the credits are "+
			"unchanged but the single total debit becomes one fund-source debit per credit, so the leg "+
			"count grows by (credits - 1) and the one-debit invariant fails on the multi-credit "+
			"observations (loan 18 and loan 19) while the principal-only loan 14 is unaffected",
		wrongRepaymentJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongRepaymentJournalDebitsFundSourcePerPortion})
	RegisterWrong("loan-wrong-chargedoff-repayment-to-portfolio",
		"posts a repayment on a loan marked charged off through the ORDINARY repayment port instead "+
			"of the charged-off branch, as a port that forgets the loan is charged off does; the "+
			"principal credit moves from income-from-recovery to the loan portfolio and the interest "+
			"credit to the interest receivable, so the ONE merged recovery credit splits into per-slot "+
			"credits and the account and count cells move while every side, amount and the single "+
			"fund-source debit stay observed — on loan-37 (principal only) only the account moves, on "+
			"loan-19 (principal+interest) the merged recovery credit becomes two",
		wrongChargedOffRepaymentJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongChargedOffRepaymentJournalsOrdinary})
	RegisterWrong("loan-wrong-chargedoff-merchant-refund-as-recovery",
		"posts a MERCHANT-ISSUED REFUND on a loan marked charged off through the charged-off "+
			"REPAYMENT layout instead of the merchant-refund arm, as a port that reuses the repayment "+
			"branch for every refund does; the principal credit moves from charge-off expense (18) to "+
			"income-from-recovery (17) and the interest credit from income-from-charge-off-interest (16) "+
			"to income-from-recovery (17), so on loan-48 L475 (principal+interest+overpayment) the two "+
			"move credits COLLAPSE into ONE recovery credit and the leg count drops by one, and on "+
			"loan-50 L498 (principal only) the one principal credit's account moves — while the "+
			"overpayment credit, every side, every amount and the single fund-source debit stay observed",
		wrongMerchantRefundJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongMerchantRefundJournalAsRecovery})
	RegisterWrong("loan-wrong-chargedoff-refund-fraud-ignored",
		"credits the principal portion of a charged-off refund to the ordinary charge-off expense "+
			"account even when the loan is marked fraud, as a port that never reads the fraud flag "+
			"does; on the pinned fraud observations loan-16 L48 (merchant-issued) and loan-17 L52 "+
			"(payout) the principal credit moves from the fraud charge-off expense account (13) to "+
			"the ordinary charge-off expense account (14) while every other leg, side, amount and "+
			"the single fund-source debit stay observed, and the non-fraud observations (loan-9 "+
			"payout and the existing merchant-issued vectors) are unaffected",
		wrongMerchantRefundJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongMerchantRefundJournalFraudIgnored})
	RegisterWrong("loan-wrong-accrual-journal-adjustment-not-reversed",
		"posts an ACCRUAL_ADJUSTMENT transaction through the accrual branch, as a port that forgets to "+
			"swap the two sides for an adjustment does; on the pinned loan-15 L107 observation (interest "+
			"279, adjustment) the interest pair keeps the accrual sides — DEBIT interest-receivable 7 and "+
			"CREDIT interest-on-loans 8 — instead of the reversed pair DEBIT 8 / CREDIT 7, so both legs' "+
			"account and side cells move while the count and every amount stay observed and every "+
			"non-adjustment vector (loans 1, 11 and 19) is unaffected",
		wrongAccrualJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongAccrualJournalAdjustmentNotReversed})
	RegisterWrong("loan-wrong-chargeback-journal-overpayment-to-portfolio",
		"debits the overpayment portion of a chargeback to the loan-portfolio account instead of the "+
			"overpayment account, as a port that reuses one debit account for every non-principal "+
			"portion does; on the pinned loan-19 (overpayment 250 alone) the debit moves from account "+
			"18 to account 10 and on loan-21 (overpayment 250 + principal 100) both debits name account "+
			"10, so the first debit's account cell moves while every side, amount and total stays "+
			"observed — and loan-14 (principal only) is unaffected",
		wrongChargebackJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongChargebackJournalOverpaymentToPortfolio})
	RegisterWrong("loan-wrong-chargeback-ignores-charge-off",
		"posts a chargeback on a charged-off loan through the not-charged-off portfolio/receivable "+
			"accounts, as a port that never reads the loan's charged-off flag does; on the pinned "+
			"charged-off loan-16 (principal 250) the principal debit moves from CHARGE_OFF_EXPENSE 16 "+
			"to LOAN_PORTFOLIO 5, and on loan-17 / loan-18 the fee / penalty debits move from the "+
			"charge-off income account 14 to the receivable account 10 as well, so the account cells "+
			"move while every side, amount and count stays observed — and the not-charged-off "+
			"observations (loans 11, 12 and the three existing vectors) are unaffected",
		wrongChargebackJournalEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongChargebackJournalIgnoresChargeOff})
	RegisterWrong("loan-wrong-charge-partial-marks-paid",
		"flips the paid flag as soon as any amount is paid, before outstanding reaches zero, so the "+
			"pinned fee's partial step (amountPaid 10000, outstanding 2345, paid false) reads paid "+
			"true while the amounts are unchanged",
		wrongChargeLifecycleEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongChargePartialMarksPaid})
	RegisterWrong("loan-wrong-charge-waiver-leaves-outstanding",
		"records the waived amount but leaves the charge's outstanding reduced by paid only, so the "+
			"pinned waived penalty (amountWaived 6789, outstanding 0) reads outstanding 6789 while "+
			"the waived cell and flag are correct",
		wrongChargeLifecycleEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongChargeWaiverLeavesOutstanding})
	RegisterWrong("loan-wrong-charge-waiver-counts-as-paid",
		"routes a waiver into amountPaid and the paid flag instead of amountWaived and the waived "+
			"flag, so the pinned penalty (paid false, waived true) reads amountPaid 6789, "+
			"amountWaived 0, paid true, waived false",
		wrongChargeLifecycleEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongChargeWaiverCountsAsPaid})
	RegisterWrong("loan-wrong-charge-outstanding-ignores-waived",
		"derives a charge's outstanding as amount minus paid only, never subtracting the waived "+
			"amount, so the pinned waived penalty (outstanding 0) reads outstanding 6789 while "+
			"every paid cell and flag is correct",
		wrongChargeLifecycleEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongChargeOutstandingIgnoresWaived})
	RegisterWrong("loan-wrong-status-transition-ignores-repaid-in-full",
		"drops the RepaidInFull arm of the balance re-derivation, behaving as if a loan whose "+
			"outstanding has reached zero still has outstanding, so the pinned repaid-in-full "+
			"transition (active, obligations satisfied) stays ACTIVE instead of closing as "+
			"CLOSED_OBLIGATIONS_MET",
		wrongStatusTransitionEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongTransitionIgnoresRepaidInFull})
	RegisterWrong("loan-wrong-status-transition-writeoff-closes-obligations-met",
		"maps the WRITE_OFF_OUTSTANDING event to CLOSED_OBLIGATIONS_MET instead of "+
			"CLOSED_WRITTEN_OFF, so the pinned write-off transition records the discharge as a "+
			"normal repayment close and the closed-state distinction is lost",
		wrongStatusTransitionEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongTransitionWriteOffClosesObligationsMet})
	RegisterWrong("loan-wrong-status-transition-approve-skips-to-active",
		"jumps straight from SUBMITTED_AND_PENDING_APPROVAL to ACTIVE on approval, as if approval "+
			"also disbursed, so the pinned approve transition reads ACTIVE instead of APPROVED",
		wrongStatusTransitionEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), mode: wrongTransitionApproveSkipsToActive})
}
