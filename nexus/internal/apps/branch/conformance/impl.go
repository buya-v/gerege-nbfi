package conformance

import (
	"fmt"
	"sort"
	"strconv"
	"sync"

	"github.com/gerege/nexus/internal/apps/branch"
)

// BranchEvaluator is what a branch implementation must be able to do for this
// harness to grade it: given a cashier-transaction cash movement, a cashier
// summary row set, or a teller status label, return the seam's cells normalised
// through the port's enum and exact-money vocabulary. This is the pure, testable
// money path the branch slice ports.
type BranchEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]BranchEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a BranchEvaluator available under name.
func Register(name string, e BranchEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("branch conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e BranchEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (BranchEvaluator, bool) {
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

// goEvaluator is the port-backed branch vocabulary. For a cash movement it maps
// the txn-type stored id through branch.CashierTxnTypeFromID and normalises the
// amount through branch.MinorUnitsFromDecimalText; for a summary it folds the row
// set with branch.FoldCashierSummary and derives net till cash; for a teller it
// maps the observed status label to the enum's stored value. A port whose enum
// table, fold or exact-money parser diverges from the oracle's stored rows
// produces a different cell.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() BranchEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	switch requestSeam(&req) {
	case SeamCashierSummary:
		return evaluateSummary(req.Summary)
	case SeamTellerStatus:
		return evaluateTellerStatus(req.TellerStatus)
	case SeamCashierTxnAmount:
		return evaluateMovement(req)
	default:
		return Expect{}, fmt.Errorf("branch: request sets no known seam")
	}
}

// evaluateMovement reproduces one cashier-transaction row: the stored txn type
// and the amount normalised to integer minor units.
func evaluateMovement(req Request) (Expect, error) {
	typ, ok := branch.CashierTxnTypeFromID(req.TxnType)
	if !ok {
		return Expect{}, fmt.Errorf("branch: request.txn_type %d is not a known cashier txn type", req.TxnType)
	}
	amt, err := branch.MinorUnitsFromDecimalText(req.TxnAmount, branch.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("branch: request.txn_amount %q: %w", req.TxnAmount, err)
	}
	return Expect{
		TxnTypeID:      typ.ID,
		TxnTypeValue:   typ.Value,
		TxnAmountMinor: strconv.FormatInt(int64(amt), 10),
	}, nil
}

// evaluateSummary folds a cashier summary row set through the port's summary
// fold and derives the net till cash, the cells the read-back's buckets stand
// for. Rows are kept in the order the read-back listed them, so a fold that
// loses or reorders a row produces different bucket sums.
func evaluateSummary(req *SummaryRequest) (Expect, error) {
	rows := make([]branch.CashierTransaction, 0, len(req.Rows))
	for i, row := range req.Rows {
		typ, ok := branch.CashierTxnTypeFromID(row.TxnType)
		if !ok {
			return Expect{}, fmt.Errorf("branch: request.cashier_summary.rows[%d].txn_type %d is not a known cashier txn type", i, row.TxnType)
		}
		amt, err := branch.MinorUnitsFromDecimalText(row.TxnAmount, branch.MNTMinorDigits)
		if err != nil {
			return Expect{}, fmt.Errorf("branch: request.cashier_summary.rows[%d].txn_amount %q: %w", i, row.TxnAmount, err)
		}
		rows = append(rows, branch.CashierTransaction{ID: int64(row.ID), TxnType: typ, TxnAmount: amt})
	}
	totals, err := branch.FoldCashierSummary(rows)
	if err != nil {
		return Expect{}, err
	}
	return Expect{
		SumCashAllocation: strconv.FormatInt(int64(totals.Allocation), 10),
		SumCashSettlement: strconv.FormatInt(int64(totals.Settlement), 10),
		NetCash:           strconv.FormatInt(int64(totals.NetCash()), 10),
	}, nil
}

// evaluateTellerStatus maps the observed status label to the stored m_tellers
// state integer. Only labels the captures serialised are mapped; anything else
// is refused rather than guessed.
func evaluateTellerStatus(req *TellerStatusRequest) (Expect, error) {
	var st branch.TellerStatus
	switch req.StatusLabel {
	case "ACTIVE":
		st = branch.TellerStatusActive
	default:
		return Expect{}, fmt.Errorf("branch: request.teller_status.status_label %q was not observed in any capture", req.StatusLabel)
	}
	return Expect{TellerStatusStored: st.StoredValue()}, nil
}

// offByOneEvaluator is a DELIBERATELY WRONG implementation: it returns the money
// cell of whichever seam the request names one minor unit high. It exists so a
// graded_against row can name an executable defect.
type offByOneEvaluator struct{ goEvaluator }

func (offByOneEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	bump := func(field string, v string) (string, error) {
		n, perr := strconv.ParseInt(v, 10, 64)
		if perr != nil {
			return "", perr
		}
		return strconv.FormatInt(n+1, 10), nil
	}
	switch requestSeam(&req) {
	case SeamCashierSummary:
		e.SumCashAllocation, err = bump("sum_cash_allocation", e.SumCashAllocation)
		if err != nil {
			return e, err
		}
	case SeamTellerStatus:
		e.TellerStatusStored++
	case SeamCashierTxnAmount:
		e.TxnAmountMinor, err = bump("txn_amount_minor", e.TxnAmountMinor)
		if err != nil {
			return e, err
		}
	}
	return e, nil
}

// summaryDropLastRowEvaluator is a DELIBERATELY WRONG implementation of the
// cashier-summary seam: it folds the row set with the LAST row dropped, the
// defect class that made the pre/post reads disagree on paper but fold together
// in code. Any summary read-back whose row set has more than one row goes red.
type summaryDropLastRowEvaluator struct{ goEvaluator }

func (summaryDropLastRowEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Summary == nil {
		return (goEvaluator{}).Evaluate(req)
	}
	clipped := *req.Summary
	if len(clipped.Rows) > 0 {
		clipped.Rows = clipped.Rows[:len(clipped.Rows)-1]
	}
	return (goEvaluator{}).Evaluate(Request{Summary: &clipped})
}

// summarySettleAsAllocateEvaluator is a DELIBERATELY WRONG implementation of the
// cashier-summary seam: it feeds settlement rows into the allocation bucket
// (cash that left the till still counted as cash the till holds), so a read-back
// with any settlement row overstates both the allocation bucket and the net till
// cash.
type summarySettleAsAllocateEvaluator struct{ goEvaluator }

func (summarySettleAsAllocateEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Summary == nil {
		return (goEvaluator{}).Evaluate(req)
	}
	misbucketed := *req.Summary
	for i := range misbucketed.Rows {
		if misbucketed.Rows[i].TxnType == branch.TxnSettle.ID {
			misbucketed.Rows[i].TxnType = branch.TxnAllocate.ID
		}
	}
	return (goEvaluator{}).Evaluate(Request{Summary: &misbucketed})
}

// summaryNetCashAddsSettlementEvaluator is a DELIBERATELY WRONG implementation of
// the cashier-summary seam: it derives net till cash as allocation plus
// settlement, i.e. it forgets that settlement removes cash from the till. A
// read-back with any settlement row therefore under-derives nothing and
// overstates net till cash by twice the settlement bucket.
type summaryNetCashAddsSettlementEvaluator struct{ goEvaluator }

func (summaryNetCashAddsSettlementEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Summary == nil {
		return (goEvaluator{}).Evaluate(req)
	}
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	alloc, aerr := strconv.ParseInt(e.SumCashAllocation, 10, 64)
	if aerr != nil {
		return e, aerr
	}
	settle, serr := strconv.ParseInt(e.SumCashSettlement, 10, 64)
	if serr != nil {
		return e, serr
	}
	e.NetCash = strconv.FormatInt(alloc+settle, 10)
	return e, nil
}

// txnLabelTransposedEvaluator is a DELIBERATELY WRONG implementation of the
// cashier-txn-amount seam: it maps each txn type to the OTHER type's display
// label, so the id/value pair an implementation returns stops agreeing with the
// oracle's stored row.
type txnLabelTransposedEvaluator struct{ goEvaluator }

func (txnLabelTransposedEvaluator) Evaluate(req Request) (Expect, error) {
	if req.Summary != nil || req.TellerStatus != nil {
		return (goEvaluator{}).Evaluate(req)
	}
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	switch e.TxnTypeID {
	case branch.TxnAllocate.ID:
		e.TxnTypeValue = branch.TxnSettle.Value
	case branch.TxnSettle.ID:
		e.TxnTypeValue = branch.TxnAllocate.Value
	}
	return e, nil
}

// tellerStatusOrdinalEvaluator is a DELIBERATELY WRONG implementation of the
// teller-status seam: it re-encodes the lifecycle state as a contiguous Go enum
// ordinal (PENDING 1, ACTIVE 2, ...) instead of the stored m_tellers.state
// integer (ACTIVE 300). The stored-value seam catches it; a label-only harness
// would not.
type tellerStatusOrdinalEvaluator struct{ goEvaluator }

func (tellerStatusOrdinalEvaluator) Evaluate(req Request) (Expect, error) {
	if req.TellerStatus == nil {
		return (goEvaluator{}).Evaluate(req)
	}
	switch req.TellerStatus.StatusLabel {
	case "ACTIVE":
		return Expect{TellerStatusStored: 2}, nil
	default:
		return Expect{}, fmt.Errorf("branch: request.teller_status.status_label %q was not observed in any capture", req.TellerStatus.StatusLabel)
	}
}

func init() {
	Register("branch-go", NewGoEvaluator())
	RegisterWrong("branch-wrong-off-by-one",
		"returns the money cell of whichever seam the request names one minor unit high, so any money cell goes red",
		offByOneEvaluator{})
	RegisterWrong("branch-wrong-summary-drops-last-row",
		"drops the last m_cashier_transactions row before folding the cashier summary, so any multi-row read-back's bucket sums go red",
		summaryDropLastRowEvaluator{})
	RegisterWrong("branch-wrong-summary-settle-as-allocate",
		"feeds settlement rows into the allocation bucket, so a read-back with any settlement overstates allocation and net till cash",
		summarySettleAsAllocateEvaluator{})
	RegisterWrong("branch-wrong-summary-net-adds-settlement",
		"derives net till cash as allocation plus settlement instead of allocation minus settlement, so a read-back with any settlement overstates net till cash",
		summaryNetCashAddsSettlementEvaluator{})
	RegisterWrong("branch-wrong-txn-label-transposed",
		"transposes the allocate/settle display labels, so the stored txn-type id and its display value stop agreeing",
		txnLabelTransposedEvaluator{})
	RegisterWrong("branch-wrong-teller-status-ordinal",
		"re-encodes the teller lifecycle state as a contiguous Go enum ordinal (ACTIVE 2) instead of the stored m_tellers.state integer (ACTIVE 300)",
		tellerStatusOrdinalEvaluator{})
}
