package conformance

import (
	"fmt"
	"math/big"
	"sort"
	"strconv"
	"sync"

	savingspkg "github.com/gerege/nexus/internal/apps/savings"
	shared "github.com/gerege/nexus/internal/conformance"
)

// SavingsEvaluator is what a savings implementation must be able to do for this
// harness to grade it. The graded surface is the capture seams:
//
//   - seam savings-daily-interest: the single-period daily-balance interest of
//     the discriminating savings account, the one cell the MANIFEST records as
//     its rounding surface (HALF_UP vs HALF_EVEN).
//   - seam savings-account-status: the m_savings_account.status_enum stored
//     value Fineract wrote back after a lifecycle command (approve -> 200,
//     activate -> 300), the enum-ordinal cell a port can silently corrupt.
//   - seams savings-deposit and savings-transactions: the running balance a
//     posted transaction stream derives, asserted against the read-back's
//     recorded running_balance values.
type SavingsEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]SavingsEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a SavingsEvaluator available under name.
func Register(name string, e SavingsEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("savings conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e SavingsEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (SavingsEvaluator, bool) {
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

// parseMinorText parses a vector's monetary text field into integer minor units.
func parseMinorText(text string) (int64, error) {
	return shared.ParseMinorInt(text)
}

// goEvaluator is the port-backed implementation.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() SavingsEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	switch {
	case req.DailyInterest != nil:
		return goDailyInterest(*req.DailyInterest, roundHalfUp)
	case req.AccountStatus != nil:
		return goAccountStatus(*req.AccountStatus)
	case req.Stream != nil:
		return goTransactionStream(*req.Stream)
	case req.HoldRelease != nil:
		return goHoldRelease(*req.HoldRelease)
	case req.HoldNetRunningBalance != nil:
		return goHoldNetRunningBalance(*req.HoldNetRunningBalance)
	default:
		return Expect{}, fmt.Errorf("savings: request must set exactly one seam sub-request")
	}
}

// evalStreamRows decodes every row of an observed append-only posting stream
// and folds it to per-row running balances with the savings package's own fold,
// in row order. decode is the stored-value-to-type mapping the implementation
// under test applies — the correct evaluator uses the savings package's decode,
// and each DELIBERATELY WRONG evaluator passes a corrupt mapping in its place.
// The posted rows of both captured accounts are unreversed, so the correct
// derived balances are exactly the values the oracle's read-back recorded next
// to each row.
func evalStreamRows(r TransactionStreamRequest, decode func(stored int32) (savingspkg.SavingsAccountTransactionType, bool)) (Expect, error) {
	rows := make([]savingspkg.SavingsAccountTransaction, 0, len(r.Transactions))
	for i, row := range r.Transactions {
		t, ok := decode(row.TypeStoredValue)
		if !ok {
			return Expect{}, fmt.Errorf("savings: row %d: transaction type stored value %d is not a savings transaction type", i, row.TypeStoredValue)
		}
		amount, err := parseMinorText(row.AmountMinor)
		if err != nil {
			return Expect{}, fmt.Errorf("savings: row %d amount: %v", i, err)
		}
		rows = append(rows, savingspkg.SavingsAccountTransaction{
			Type:   t,
			Amount: savingspkg.MinorUnits(amount),
		})
	}
	balances := savingspkg.RunningBalancesOf(rows)
	out := make([]string, 0, len(balances))
	for _, b := range balances {
		out = append(out, strconv.FormatInt(int64(b), 10))
	}
	return Expect{RunningBalances: out}, nil
}

// savingsDecode is the correct stored-value decode.
func savingsDecode(stored int32) (savingspkg.SavingsAccountTransactionType, bool) {
	return savingspkg.SavingsAccountTransactionTypeFromStoredValue(stored)
}

func goTransactionStream(r TransactionStreamRequest) (Expect, error) {
	return evalStreamRows(r, savingsDecode)
}

func goDailyInterest(r DailyInterestRequest, round func(numerator, denominator *big.Int) int64) (Expect, error) {
	balance, err := parseMinorText(r.BalanceMinor)
	if err != nil {
		return Expect{}, err
	}
	interest := dailyInterestMinor(balance, r.RatePerAnnumMicroPct, r.Days, r.DaysInYear, round)
	return Expect{InterestMinor: strconv.FormatInt(interest, 10)}, nil
}

// goAccountStatus returns the m_savings_account.status_enum stored value of the
// savings package enum reached by an observed lifecycle step. The values are NOT
// the Go declaration ordinals: the savings enum is the explicit stored-value
// table of accountstatus.go (APPROVED is 200, ACTIVE is 300, ...), and the
// vector's expected cell is the stored value the oracle's command
// acknowledgement wrote back. Only the two steps the oracle was observed
// executing are answered.
func goAccountStatus(r AccountStatusRequest) (Expect, error) {
	st, ok := savingsStatusForStep(r.Step)
	if !ok {
		return Expect{}, fmt.Errorf("savings: lifecycle step %q is not an observed step (approve, activate)", r.Step)
	}
	return Expect{StatusID: st.StoredValue()}, nil
}

func savingsStatusForStep(step string) (savingspkg.SavingsAccountStatusType, bool) {
	switch step {
	case "approve":
		return savingspkg.StatusApproved, true
	case "activate":
		return savingspkg.StatusActive, true
	}
	return savingspkg.StatusInvalid, false
}

// dailyInterestMinor ports the single-period daily-balance interest of the
// MANIFEST's discriminating savings account:
//
//	interest = round(balance * ratePct * days, 100 * daysInYear)
//
// with the result in integer MINOR UNITS (2 digits). The rate is the savings
// Percent convention — whole per cent scaled by 10^6 (micro-per-cent), so the
// whole-per-cent rate is rateMicroPct / 1e6 — and the balance is already minor
// units, so:
//
//	interestMinor = round(balanceMinor * rateMicroPct * days, 1e8 * daysInYear)
//
// For the discriminating cell (balanceMinor 100000, rateMicroPct 182500, 1 day,
// 365-day year) the numerator is 18,250,000,000 and the denominator is
// 36,500,000,000 — exactly one half minor unit — so HALF_UP posts 1 (0.01) and
// HALF_EVEN posts 0 (0.00). The oracle posted 0.01.
//
// The savings slice does NOT own the accrual engine (the accrual is a separate
// future port); this is the ONE cell the MANIFEST records as the savings
// context's discriminating rounding surface, not a port of the whole accrual.
// The numerator is computed in big.Int so the rounding is exact for any captured
// magnitude, not merely the seed's.
func dailyInterestMinor(balanceMinor, rateMicroPct, days, daysInYear int64, round func(numerator, denominator *big.Int) int64) int64 {
	num := new(big.Int).Mul(big.NewInt(balanceMinor), big.NewInt(rateMicroPct))
	num.Mul(num, big.NewInt(days))
	// denominator = 10^6 (micro-per-cent) * 100 (per cent) * daysInYear, written
	// as an integer literal so the no-float census never sees an exponent form.
	den := new(big.Int).Mul(big.NewInt(100000000), big.NewInt(daysInYear))
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
// red: the oracle posted 0.01 under HALF_UP where HALF_EVEN would have posted
// 0.00.
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
// discriminating daily-interest cell with HALF_EVEN instead of HALF_UP, so a
// vector that asserts that cell goes red (0 minor vs the oracle's 1).
type wrongEvaluator struct{ goEvaluator }

func (w wrongEvaluator) Evaluate(req Request) (Expect, error) {
	if req.DailyInterest != nil {
		return goDailyInterest(*req.DailyInterest, roundHalfEven)
	}
	return w.goEvaluator.Evaluate(req)
}

// statusWrongEvaluator is a DELIBERATELY WRONG implementation: it encodes the
// account status enum as the Go DECLARATION ordinal (iota) instead of the
// Fineract stored value, so APPROVED reads 2 and ACTIVE reads 3 rather than 200
// and 300. A port that makes this mistake silently writes corrupt status_enum
// values; the two account-status vectors go red against it.
type statusWrongEvaluator struct{ goEvaluator }

func (w statusWrongEvaluator) Evaluate(req Request) (Expect, error) {
	if req.AccountStatus != nil {
		st, ok := savingsStatusForStep(req.AccountStatus.Step)
		if !ok {
			return Expect{}, fmt.Errorf("savings: lifecycle step %q is not an observed step (approve, activate)", req.AccountStatus.Step)
		}
		return Expect{StatusID: int32(st)}, nil
	}
	return w.goEvaluator.Evaluate(req)
}

// depositNotCreditedEvaluator is a DELIBERATELY WRONG implementation: its
// stored-value decode maps a DEPOSIT row to a balance-neutral type, so a
// deposit does NOT credit the posted balance. This is the port of a savings
// classification that drops the deposit from the running-balance fold (a
// deposit posting whose type does not move the balance). The deposit seam's
// vector and the transaction-stream vectors go red against it (the opening
// deposit leaves the balance at 0 instead of 1000.00).
type depositNotCreditedEvaluator struct{ goEvaluator }

func (w depositNotCreditedEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Stream != nil {
		return evalStreamRows(*req.Stream, func(stored int32) (savingspkg.SavingsAccountTransactionType, bool) {
			if stored == savingspkg.TxnDeposit.StoredValue() {
				// A balance-neutral type: the deposit is folded but credits nothing.
				return savingspkg.TxnAccrual, true
			}
			return savingsDecode(stored)
		})
	}
	return w.goEvaluator.Evaluate(req)
}

// interestPostingDebitsEvaluator is a DELIBERATELY WRONG implementation: its
// stored-value decode maps an INTEREST_POSTING row to a DEBIT type, so an
// interest posting REDUCES the posted balance instead of crediting it — the
// sign error of a port that posts interest on the wrong side of the fold. The
// transaction-stream vectors (which carry interest postings) go red against it;
// the deposit-only seam vector does not (it carries no posting row).
type interestPostingDebitsEvaluator struct{ goEvaluator }

func (w interestPostingDebitsEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Stream != nil {
		return evalStreamRows(*req.Stream, func(stored int32) (savingspkg.SavingsAccountTransactionType, bool) {
			if stored == savingspkg.TxnInterestPosting.StoredValue() {
				return savingspkg.TxnWithdrawal, true
			}
			return savingsDecode(stored)
		})
	}
	return w.goEvaluator.Evaluate(req)
}

// runningBalanceBeforeEvaluator is a DELIBERATELY WRONG implementation: it
// derives each row's running balance as the balance BEFORE that row's posting
// instead of after it — the off-by-one of a port that records the running
// balance_derived column from the pre-posting state. Every row of a
// transaction-stream vector goes red (the opening deposit reads 0 instead of
// 1000.00).
type runningBalanceBeforeEvaluator struct{ goEvaluator }

func (w runningBalanceBeforeEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Stream != nil {
		after, err := evalStreamRows(*req.Stream, savingsDecode)
		if err != nil {
			return Expect{}, err
		}
		out := make([]string, len(after.RunningBalances))
		for i := range after.RunningBalances {
			if i == 0 {
				out[i] = "0"
				continue
			}
			out[i] = after.RunningBalances[i-1]
		}
		return Expect{RunningBalances: out}, nil
	}
	return w.goEvaluator.Evaluate(req)
}

// buildHoldReleaseRows decodes the observed hold/release stream into the
// savings package's own transaction rows, carrying the two id facts the hold
// algebra needs (the row id and the hold's release id). decode is the
// stored-value mapping the implementation under test applies; the correct
// evaluator uses savingsDecode, and the deliberately wrong evaluators pass a
// corrupt mapping in its place.
func buildHoldReleaseRows(stream []HoldReleaseRow, decode func(stored int32) (savingspkg.SavingsAccountTransactionType, bool)) ([]savingspkg.SavingsAccountTransaction, error) {
	rows := make([]savingspkg.SavingsAccountTransaction, 0, len(stream))
	for i, row := range stream {
		t, ok := decode(row.TypeStoredValue)
		if !ok {
			return nil, fmt.Errorf("savings: hold row %d: transaction type stored value %d is not a savings transaction type", i, row.TypeStoredValue)
		}
		amount, err := parseMinorText(row.AmountMinor)
		if err != nil {
			return nil, fmt.Errorf("savings: hold row %d amount: %v", i, err)
		}
		rows = append(rows, savingspkg.SavingsAccountTransaction{
			ID:                    row.ID,
			Type:                  t,
			Amount:                savingspkg.MinorUnits(amount),
			ReleaseIDOfHoldAmount: row.ReleaseIDOfHoldAmount,
		})
	}
	return rows, nil
}

// goHoldRelease evaluates the savings-hold-release seam with the port's own
// derivations, all three from the same observed append-only stream:
//
//	account_balance = AccountBalanceOf(rows)  // the hold contributes NOTHING
//	held            = HeldOf(rows)            // the outstanding hold, by id pairing
//	available       = AvailableOf(rows)       // balance less held
//
// The derivation splits the three cells deliberately: if the hold were folded
// into the posted balance, this evaluator would report 863.02 as the balance
// and 725.73 as available on the after-hold stream, against the oracle's
// 1000.31 and 863.02.
func goHoldRelease(r HoldReleaseRequest) (Expect, error) {
	rows, err := buildHoldReleaseRows(r.Transactions, savingsDecode)
	if err != nil {
		return Expect{}, err
	}
	balance := savingspkg.AccountBalanceOf(rows)
	held, err := savingspkg.HeldOf(rows)
	if err != nil {
		return Expect{}, fmt.Errorf("savings: held amount: %v", err)
	}
	available, err := savingspkg.AvailableOf(rows)
	if err != nil {
		return Expect{}, fmt.Errorf("savings: available amount: %v", err)
	}
	return Expect{
		AccountBalanceMinor: strconv.FormatInt(int64(balance), 10),
		HeldMinor:           strconv.FormatInt(int64(held), 10),
		AvailableMinor:      strconv.FormatInt(int64(available), 10),
	}, nil
}

// goHoldNetRunningBalance evaluates the savings-hold-net-running-balance seam
// with the port's own derivations, from the same observed append-only stream
// the request carries IN THE ORACLE'S TRANSACTION ORDER:
//
//	hold_net_running_balances = HoldNetRunningBalancesOf(0, rows)  // the stored
//	                                                               // running_balance_derived chain
//	account_balance           = AccountBalanceOf(rows)             // the posted balance
//
// The two are graded in the SAME vector because they are the two halves of the
// one property: the stored chain moves DOWN by the hold and back UP by its
// release, while the posted balance does not move at all. The chain starts from
// a zero opening balance, as the oracle's full recompute does.
//
// The request's row order is the observation. HoldNetRunningBalancesOf folds in
// the order given, and the capture's chain is transaction-date order
// (1, 3, 2, 6, 7), not id order, so a request that listed the rows in id order
// would fold a different chain (1000.16 then 1000.31) and read the 0.16 posting
// before the 0.15 one. Nothing here re-sorts: re-sorting would be a guess that
// discards the observation.
//
// The void-row branch is NOT reachable from this seam's observation: the
// captured account has no void row, so every RunningBalance is Valid. A
// non-valid cell would mean a request carried a reversed/reversal row, which
// admission (admitHoldReleaseStream) refuses because the capture has none; the
// evaluator reports it rather than inventing a value.
func goHoldNetRunningBalance(r HoldNetRunningBalanceRequest) (Expect, error) {
	rows, err := buildHoldReleaseRows(r.Transactions, savingsDecode)
	if err != nil {
		return Expect{}, err
	}
	chain := savingspkg.HoldNetRunningBalancesOf(0, rows)
	out := make([]string, 0, len(chain))
	for i, rb := range chain {
		if !rb.Valid {
			return Expect{}, fmt.Errorf(
				"savings: hold-net running balance row %d states NO balance (a void row); this seam's capture has no void row", i)
		}
		out = append(out, strconv.FormatInt(int64(rb.Value), 10))
	}
	balance := savingspkg.AccountBalanceOf(rows)
	return Expect{
		HoldNetRunningBalances: out,
		AccountBalanceMinor:    strconv.FormatInt(int64(balance), 10),
	}, nil
}

// holdNetEvaluator is a DELIBERATELY WRONG hold-net evaluator: it derives the
// stored chain from rows its decode has corrupted, while keeping the posted
// balance correct. Each concrete defect lives in the decode or the row order,
// so the SAME vector kills every one of them; the four drives are separated
// because a port can make any one of them without making the others.
type holdNetEvaluator struct {
	goEvaluator
	decode func(stored int32) (savingspkg.SavingsAccountTransactionType, bool)
	// sortByID folds the chain in id order instead of the observed transaction
	// order, the inverse of the transposition the capture records.
	sortByID bool
}

func (w holdNetEvaluator) Evaluate(req Request) (Expect, error) {
	if req.HoldNetRunningBalance != nil {
		stream := req.HoldNetRunningBalance.Transactions
		if w.sortByID {
			stream = append([]HoldReleaseRow(nil), stream...)
			sort.SliceStable(stream, func(i, j int) bool { return stream[i].ID < stream[j].ID })
		}
		rows, err := buildHoldReleaseRows(stream, w.decode)
		if err != nil {
			return Expect{}, err
		}
		chain := savingspkg.HoldNetRunningBalancesOf(0, rows)
		out := make([]string, 0, len(chain))
		for i, rb := range chain {
			if !rb.Valid {
				return Expect{}, fmt.Errorf("savings: wrong hold-net implementation: row %d has no balance", i)
			}
			out = append(out, strconv.FormatInt(int64(rb.Value), 10))
		}
		balance := savingspkg.AccountBalanceOf(rows)
		return Expect{
			HoldNetRunningBalances: out,
			AccountBalanceMinor:    strconv.FormatInt(int64(balance), 10),
		}, nil
	}
	return w.goEvaluator.Evaluate(req)
}

// holdNetBalanceNeutral maps the given stored values to a balance-neutral type,
// so a row of that type is folded but moves nothing.
func holdNetBalanceNeutral(storeds ...int32) func(int32) (savingspkg.SavingsAccountTransactionType, bool) {
	set := make(map[int32]bool, len(storeds))
	for _, s := range storeds {
		set[s] = true
	}
	return func(stored int32) (savingspkg.SavingsAccountTransactionType, bool) {
		if set[stored] {
			return savingspkg.TxnAccrual, true
		}
		return savingsDecode(stored)
	}
}

// holdNetHoldIsCredit maps AMOUNT_HOLD to a CREDIT type, so the chain ADDS the
// held amount instead of subtracting it — the sign error of a port that reads
// "a hold is a posting" as "the hold credits the running balance". On this
// vector the hold row reads 100031 + 13729 = 113760 minor units where the
// oracle stores 86302.
func holdNetHoldIsCredit() func(int32) (savingspkg.SavingsAccountTransactionType, bool) {
	return func(stored int32) (savingspkg.SavingsAccountTransactionType, bool) {
		if stored == savingspkg.TxnAmountHold.StoredValue() {
			return savingspkg.TxnDeposit, true
		}
		return savingsDecode(stored)
	}
}

// holdFoldRawBalance is the posted-balance fold of the NATURAL MISTAKE: it
// classifies each row by its RAW entry type instead of the oracle's folded
// classification. AMOUNT_HOLD carries raw entry DEBIT and AMOUNT_RELEASE raw
// entry CREDIT, so this fold subtracts the hold from the posted balance (and
// adds the release back) — exactly the pre-T515 defect the savings package's
// Effect()/IsDebit() documentation records. It exists only to drive the
// hold/release vectors red; it is not the port's own derivation.
func holdFoldRawBalance(rows []savingspkg.SavingsAccountTransaction) savingspkg.MinorUnits {
	var total savingspkg.MinorUnits
	for _, t := range rows {
		amount := t.Amount
		if amount < 0 {
			amount = -amount
		}
		switch {
		case t.Type.IsDebitEntryType():
			total -= amount
		case t.Type.IsCreditEntryType():
			total += amount
		}
	}
	return total
}

// holdFoldedIntoBalanceEvaluator is a DELIBERATELY WRONG implementation: it
// folds the hold into the POSTED balance by classifying rows with their raw
// entry type, the natural mistake CLAUDE.md line 14 forbids. HeldOf and
// AvailableOf stay the port's own, so on the after-hold vector it reports
// account_balance 863.02 (the oracle's AVAILABLE, not its balance), held 137.29
// and available 725.73 — two cells red. On the after-release vector the hold and
// release cancel and it accidentally passes: that is precisely why the
// after-hold state is the observation that grades the rule.
type holdFoldedIntoBalanceEvaluator struct{ goEvaluator }

func (w holdFoldedIntoBalanceEvaluator) Evaluate(req Request) (Expect, error) {
	if req.HoldRelease != nil {
		rows, err := buildHoldReleaseRows(req.HoldRelease.Transactions, savingsDecode)
		if err != nil {
			return Expect{}, err
		}
		balance := holdFoldRawBalance(rows)
		held, err := savingspkg.HeldOf(rows)
		if err != nil {
			return Expect{}, fmt.Errorf("savings: held amount: %v", err)
		}
		return Expect{
			AccountBalanceMinor: strconv.FormatInt(int64(balance), 10),
			HeldMinor:           strconv.FormatInt(int64(held), 10),
			AvailableMinor:      strconv.FormatInt(int64(balance-held), 10),
		}, nil
	}
	return w.goEvaluator.Evaluate(req)
}

// holdIgnoredEvaluator is a DELIBERATELY WRONG implementation: its stored-value
// decode maps both AMOUNT_HOLD and AMOUNT_RELEASE rows to a balance-neutral
// type, so the hold is invisible to every derivation — the posted balance is
// right by accident, but held is 0 and available never falls. The after-hold
// vector goes red (held 0 vs 137.29, available 1000.31 vs 863.02); the
// after-release vector passes, which is again the point of capturing the held
// state.
type holdIgnoredEvaluator struct{ goEvaluator }

func (w holdIgnoredEvaluator) Evaluate(req Request) (Expect, error) {
	if req.HoldRelease != nil {
		rows, err := buildHoldReleaseRows(req.HoldRelease.Transactions, func(stored int32) (savingspkg.SavingsAccountTransactionType, bool) {
			switch stored {
			case savingspkg.TxnAmountHold.StoredValue(), savingspkg.TxnAmountRelease.StoredValue():
				return savingspkg.TxnAccrual, true
			}
			return savingsDecode(stored)
		})
		if err != nil {
			return Expect{}, err
		}
		balance := savingspkg.AccountBalanceOf(rows)
		held, err := savingspkg.HeldOf(rows)
		if err != nil {
			return Expect{}, fmt.Errorf("savings: held amount: %v", err)
		}
		available, err := savingspkg.AvailableOf(rows)
		if err != nil {
			return Expect{}, fmt.Errorf("savings: available amount: %v", err)
		}
		return Expect{
			AccountBalanceMinor: strconv.FormatInt(int64(balance), 10),
			HeldMinor:           strconv.FormatInt(int64(held), 10),
			AvailableMinor:      strconv.FormatInt(int64(available), 10),
		}, nil
	}
	return w.goEvaluator.Evaluate(req)
}

func init() {
	Register("savings-go", NewGoEvaluator())
	RegisterWrong("savings-wrong-half-even-daily-interest",
		"rounds the discriminating daily-interest cell with HALF_EVEN instead of HALF_UP, "+
			"so the pinned 0.01 observation reads 0.00 and the vector goes red",
		wrongEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("savings-wrong-iota-status-ordinal",
		"encodes the account status enum as the Go declaration ordinal (iota) instead of the "+
			"Fineract stored value, so APPROVED reads 2 and ACTIVE reads 3 rather than 200 and 300",
		statusWrongEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("savings-wrong-deposit-not-credited",
		"decodes a DEPOSIT row to a balance-neutral type, so the opening deposit of 1000.00 "+
			"leaves the posted balance at 0 instead of crediting 1000.00",
		depositNotCreditedEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("savings-wrong-interest-posting-debits",
		"decodes an INTEREST_POSTING row to a DEBIT type, so an interest posting reduces "+
			"the posted balance instead of crediting it",
		interestPostingDebitsEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("savings-wrong-running-balance-before",
		"derives each row's running balance as the balance BEFORE that row instead of after it",
		runningBalanceBeforeEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("savings-wrong-hold-folded-into-balance",
		"classifies a hold by its raw entry type, so AMOUNT_HOLD subtracts from the POSTED "+
			"balance instead of altering available only: on the after-hold vector the balance "+
			"reads 863.02 (the oracle's AVAILABLE) and available reads 725.73",
		holdFoldedIntoBalanceEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("savings-wrong-hold-ignored",
		"decodes AMOUNT_HOLD and AMOUNT_RELEASE to a balance-neutral type, so the hold is "+
			"invisible: the balance is right by accident but held stays 0 and available never "+
			"falls by the held amount",
		holdIgnoredEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("savings-wrong-hold-net-ignores-holds",
		"folds the stored running_balance_derived chain as if the hold were balance-neutral, "+
			"the careful porter's reading of \"holds alter available only\": the hold row reads "+
			"the posted balance 100031 where the oracle stores 86302",
		holdNetEvaluator{
			goEvaluator: NewGoEvaluator().(goEvaluator),
			decode:      holdNetBalanceNeutral(savingspkg.TxnAmountHold.StoredValue(), savingspkg.TxnAmountRelease.StoredValue()),
		})
	RegisterWrong("savings-wrong-hold-net-ignores-releases",
		"folds the hold DOWN but never ADDS the release back, so the release row stays at "+
			"86302 where the oracle restores 100031",
		holdNetEvaluator{
			goEvaluator: NewGoEvaluator().(goEvaluator),
			decode:      holdNetBalanceNeutral(savingspkg.TxnAmountRelease.StoredValue()),
		})
	RegisterWrong("savings-wrong-hold-net-hold-is-credit",
		"decodes AMOUNT_HOLD to a CREDIT type, so the chain ADDS the held amount (113760) "+
			"where the oracle subtracts it (86302)",
		holdNetEvaluator{
			goEvaluator: NewGoEvaluator().(goEvaluator),
			decode:      holdNetHoldIsCredit(),
		})
	RegisterWrong("savings-wrong-hold-net-id-order",
		"folds the chain in id order instead of the capture's transaction-date order, so the "+
			"0.16 posting (id 2) precedes the 0.15 posting (id 3): the row after id 2 reads "+
			"100016 where the chain has 100015",
		holdNetEvaluator{
			goEvaluator: NewGoEvaluator().(goEvaluator),
			decode:      savingsDecode,
			sortByID:    true,
		})
}
