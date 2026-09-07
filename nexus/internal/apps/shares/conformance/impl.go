package conformance

import (
	"fmt"
	"sort"
	"strconv"
	"sync"

	"github.com/gerege/nexus/internal/apps/shares"
)

// SharesEvaluator is what a shares implementation must be able to do for this
// harness to grade it. It is NOT "persist a share account to a database"; it is
// the pure vocabulary the slice actually ports — the status/purchase-status
// stored-value mapping and the normalisation of exact decimal money text into
// integer minor units — which is all a captured share vector can observe.
type SharesEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

// ---------------------------------------------------------------------------
// The registry
// ---------------------------------------------------------------------------

var (
	implMu sync.RWMutex
	impls  = map[string]SharesEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a SharesEvaluator available under name.
func Register(name string, e SharesEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("shares conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e SharesEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (SharesEvaluator, bool) {
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

// ---------------------------------------------------------------------------
// The port-backed implementation
// ---------------------------------------------------------------------------

// goEvaluator is the port-backed share vocabulary: it maps the account and
// purchase status stored ids through the port's FromInt tables and normalises the
// money text through shares.MinorUnitsFromDecimalText, so a port whose enum table
// or exact-money parser diverges from the oracle's stored row produces a
// different cell.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() SharesEvaluator { return goEvaluator{} }

func (goEvaluator) Evaluate(req Request) (Expect, error) {
	switch req.Kind {
	case KindAccount:
		return evaluateAccount(req)
	case KindDividend:
		return evaluateDividend(req)
	default:
		return Expect{}, fmt.Errorf("shares: request.kind %q is not a known seam", req.Kind)
	}
}

func evaluateAccount(req Request) (Expect, error) {
	acct := shares.ShareAccountStatusFromInt(req.AccountStatusID)
	purch := shares.PurchaseStatusFromInt(req.PurchasedStatusID)
	price, err := shares.MinorUnitsFromDecimalText(req.PurchasedPrice, shares.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("shares: request.purchased_price %q: %w", req.PurchasedPrice, err)
	}
	amount, err := shares.MinorUnitsFromDecimalText(req.PurchasedAmount, shares.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("shares: request.purchased_amount %q: %w", req.PurchasedAmount, err)
	}
	return Expect{
		Kind:                  KindAccount,
		AccountStatusStored:   acct.StoredValue(),
		TotalApprovedShares:   req.TotalApprovedShares,
		PurchasedShares:       req.PurchasedShares,
		PurchasedPriceMinor:   strconv.FormatInt(int64(price), 10),
		PurchasedAmountMinor:  strconv.FormatInt(int64(amount), 10),
		PurchasedStatusStored: purch.StoredValue(),
	}, nil
}

func evaluateDividend(req Request) (Expect, error) {
	div, err := shares.MinorUnitsFromDecimalText(req.DividendAmount, shares.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("shares: request.dividend_amount %q: %w", req.DividendAmount, err)
	}
	return Expect{
		Kind:                KindDividend,
		DividendAmountMinor: strconv.FormatInt(int64(div), 10),
	}, nil
}

// offByOneEvaluator is a DELIBERATELY WRONG implementation: it returns the
// account seam's purchased amount, or the dividend seam's dividend amount, one
// minor unit high. It exists so a graded_against row can name an executable
// defect, exactly as the branch harness's wrong implementation does.
type offByOneEvaluator struct{ goEvaluator }

func (offByOneEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	switch e.Kind {
	case KindAccount:
		n, perr := strconv.ParseInt(e.PurchasedAmountMinor, 10, 64)
		if perr != nil {
			return e, perr
		}
		e.PurchasedAmountMinor = strconv.FormatInt(n+1, 10)
	case KindDividend:
		n, perr := strconv.ParseInt(e.DividendAmountMinor, 10, 64)
		if perr != nil {
			return e, perr
		}
		e.DividendAmountMinor = strconv.FormatInt(n+1, 10)
	}
	return e, nil
}

func init() {
	Register("shares-go", NewGoEvaluator())
	RegisterWrong("shares-wrong-off-by-one",
		"returns the purchased amount (account seam) or the dividend amount (dividend seam) one minor unit high, "+
			"so any money cell goes red",
		offByOneEvaluator{})
}
