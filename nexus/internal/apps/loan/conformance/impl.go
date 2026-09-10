package conformance

import (
	"fmt"
	"math/big"
	"sort"
	"strconv"
	"sync"

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
	default:
		return Expect{}, fmt.Errorf("loan: request must set exactly one of repayment, schedule, disburse, summary, status, transactions, journal_entries")
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

// wrongRepaymentEvaluator is a DELIBERATELY WRONG implementation of the
// repayment-allocation seam: its allocation order omits the principal bucket, so
// every repayment is recognised wholly against charges and interest and the loan
// never amortises. On the pinned SEED-L03 repayment the instalment's 7884.88 of
// principal is never allocated: the allocation reports principal=0 and the whole
// 7884.88 falls through to the leftover, and the vector goes red on both cells.
type wrongRepaymentEvaluator struct{ goEvaluator }

func (w wrongRepaymentEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Repayment != nil {
		return wrongRepayment(*req.Repayment)
	}
	return w.goEvaluator.Evaluate(req)
}

func wrongRepayment(r RepaymentRequest) (Expect, error) {
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
	alloc, leftover := loan.AllocatePayment(outstanding, amount, mifosOrderNoPrincipal)
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
		for _, l := range parsed {
			if l.txn == first {
				add(l)
			}
		}
	case wrongBatchDropsSecondPair:
		last := order[len(order)-1]
		for _, l := range parsed {
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
		for _, l := range parsed {
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
	default:
		// wrongBatchSwapsFirstPairSides (and the zero value) sum every leg on
		// its (possibly flipped) side: the totals are unchanged by the swap.
		for _, l := range parsed {
			add(l)
		}
	}

	sides := make([]JournalEntryAccountSideCell, len(parsed))
	for i, l := range parsed {
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
}
