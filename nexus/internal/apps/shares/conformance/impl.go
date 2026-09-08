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
// the pure vocabulary the slice actually ports — the status, purchase-status and
// dividend-status stored-value mappings and the normalisation of exact decimal
// money text into integer minor units — which is all a captured share vector can
// observe.
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
	case KindProduct:
		return evaluateProduct(req)
	default:
		return Expect{}, fmt.Errorf("shares: request.kind %q is not a known seam", req.Kind)
	}
}

func evaluateAccount(req Request) (Expect, error) {
	acct := shares.ShareAccountStatusFromInt(req.AccountStatusID)
	out := Expect{
		Kind:                KindAccount,
		AccountStatusStored: acct.StoredValue(),
		TotalApprovedShares: req.TotalApprovedShares,
		TotalPendingShares:  req.TotalPendingShares,
	}
	if req.PurchasedShares == 0 {
		// A share-account list row carries no purchase group: nothing to derive.
		return out, nil
	}
	purch := shares.PurchaseStatusFromInt(req.PurchasedStatusID)
	price, err := shares.MinorUnitsFromDecimalText(req.PurchasedPrice, shares.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("shares: request.purchased_price %q: %w", req.PurchasedPrice, err)
	}
	amount, err := shares.MinorUnitsFromDecimalText(req.PurchasedAmount, shares.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("shares: request.purchased_amount %q: %w", req.PurchasedAmount, err)
	}
	out.PurchasedShares = req.PurchasedShares
	out.PurchasedPriceMinor = strconv.FormatInt(int64(price), 10)
	out.PurchasedAmountMinor = strconv.FormatInt(int64(amount), 10)
	out.PurchasedStatusStored = purch.StoredValue()
	return out, nil
}

func evaluateDividend(req Request) (Expect, error) {
	div, err := shares.MinorUnitsFromDecimalText(req.DividendAmount, shares.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("shares: request.dividend_amount %q: %w", req.DividendAmount, err)
	}
	out := Expect{
		Kind:                KindDividend,
		DividendAmountMinor: strconv.FormatInt(int64(div), 10),
	}
	if req.DividendStatusID != 0 {
		out.DividendStatusStored = shares.ShareAccountDividendStatusFromInt(req.DividendStatusID).StoredValue()
	}
	return out, nil
}

func evaluateProduct(req Request) (Expect, error) {
	unit, err := shares.MinorUnitsFromDecimalText(req.UnitPrice, shares.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("shares: request.unit_price %q: %w", req.UnitPrice, err)
	}
	capital, err := shares.MinorUnitsFromDecimalText(req.ShareCapital, shares.MNTMinorDigits)
	if err != nil {
		return Expect{}, fmt.Errorf("shares: request.share_capital %q: %w", req.ShareCapital, err)
	}
	return Expect{
		Kind:              KindProduct,
		UnitPriceMinor:    strconv.FormatInt(int64(unit), 10),
		ShareCapitalMinor: strconv.FormatInt(int64(capital), 10),
		TotalShares:       req.TotalShares,
	}, nil
}

// bumpMinor returns value raised by one minor unit, or value untouched when it is
// empty (a cell the seam does not grade this vector).
func bumpMinor(value string) (string, error) {
	if value == "" {
		return "", nil
	}
	n, err := strconv.ParseInt(value, 10, 64)
	if err != nil {
		return "", err
	}
	return strconv.FormatInt(n+1, 10), nil
}

// offByOneEvaluator is a DELIBERATELY WRONG implementation: it returns every
// money cell it grades one minor unit high. It exists so a graded_against row can
// name an executable defect, exactly as the branch harness's wrong implementation
// does.
type offByOneEvaluator struct{ goEvaluator }

func (offByOneEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	switch e.Kind {
	case KindAccount:
		if e.PurchasedPriceMinor, err = bumpMinor(e.PurchasedPriceMinor); err != nil {
			return e, err
		}
		if e.PurchasedAmountMinor, err = bumpMinor(e.PurchasedAmountMinor); err != nil {
			return e, err
		}
	case KindDividend:
		if e.DividendAmountMinor, err = bumpMinor(e.DividendAmountMinor); err != nil {
			return e, err
		}
	case KindProduct:
		if e.UnitPriceMinor, err = bumpMinor(e.UnitPriceMinor); err != nil {
			return e, err
		}
		if e.ShareCapitalMinor, err = bumpMinor(e.ShareCapitalMinor); err != nil {
			return e, err
		}
	}
	return e, nil
}

// storedAsIotaOrdinal re-encodes a stored enum id as the contiguous ordinal a Go
// iota enum would assign it (stored ids in these enums are spaced by 100, so the
// iota view of 300 is 3 and of 100 is 1).
func storedAsIotaOrdinal(stored int32) int32 { return stored / 100 }

// statusOrdinalEvaluator is a DELIBERATELY WRONG implementation of the defect
// class loan-wrong-status-iota-ordinal catches for loans: it writes the account,
// purchase and dividend STATUS LABELS back through a contiguous Go iota ordinal
// rather than the stored enum integer. Any vector whose read-back pins the stored
// status goes red.
type statusOrdinalEvaluator struct{ goEvaluator }

func (statusOrdinalEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	switch e.Kind {
	case KindAccount:
		e.AccountStatusStored = storedAsIotaOrdinal(e.AccountStatusStored)
		if req.PurchasedShares != 0 {
			e.PurchasedStatusStored = storedAsIotaOrdinal(e.PurchasedStatusStored)
		}
	case KindDividend:
		if req.DividendStatusID != 0 {
			e.DividendStatusStored = storedAsIotaOrdinal(e.DividendStatusStored)
		}
	}
	return e, nil
}

// transposedProductPriceEvaluator is a DELIBERATELY WRONG implementation: it
// serialises a share product's unit price into the share-capital field and the
// share capital into the unit-price field (a transposed-money-column defect). A
// product read-back whose unit price and capital differ goes red.
type transposedProductPriceEvaluator struct{ goEvaluator }

func (transposedProductPriceEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	if e.Kind == KindProduct {
		e.UnitPriceMinor, e.ShareCapitalMinor = e.ShareCapitalMinor, e.UnitPriceMinor
	}
	return e, nil
}

// transposedSummaryEvaluator is a DELIBERATELY WRONG implementation: it fills
// the summary's totalPendingForApprovalShares fold from totalApprovedShares — a
// serialiser that reads the approved figure into the pending column of the
// account summary fold. The captures' pending figure is 0, so OMITTING the fold
// is indistinguishable (absent folds to 0), but a transpose writes the approved
// 100 into it; any share-account read-back whose approved and pending counts
// differ goes red. The vector notes state this.
type transposedSummaryEvaluator struct{ goEvaluator }

func (transposedSummaryEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	if e.Kind == KindAccount {
		e.TotalPendingShares = e.TotalApprovedShares
	}
	return e, nil
}

// dropZeroMoneyEvaluator is a DELIBERATELY WRONG implementation: it omits a money
// cell whose minor-unit value is zero — the serialiser "helpfully" dropping a
// present-but-zero figure. The product read-back whose share capital is 0.00 goes
// red, and the zero-money cell trips the non-negative invariant because a dropped
// cell is an empty string, not a number.
type dropZeroMoneyEvaluator struct{ goEvaluator }

func (dropZeroMoneyEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := (goEvaluator{}).Evaluate(req)
	if err != nil {
		return e, err
	}
	dropZero := func(s string) string {
		if s == "0" {
			return ""
		}
		return s
	}
	switch e.Kind {
	case KindAccount:
		e.PurchasedPriceMinor = dropZero(e.PurchasedPriceMinor)
		e.PurchasedAmountMinor = dropZero(e.PurchasedAmountMinor)
	case KindDividend:
		e.DividendAmountMinor = dropZero(e.DividendAmountMinor)
	case KindProduct:
		e.UnitPriceMinor = dropZero(e.UnitPriceMinor)
		e.ShareCapitalMinor = dropZero(e.ShareCapitalMinor)
	}
	return e, nil
}

func init() {
	Register("shares-go", NewGoEvaluator())
	RegisterWrong("shares-wrong-off-by-one",
		"returns every graded money cell one minor unit high, so any money-bearing vector goes red",
		offByOneEvaluator{})
	RegisterWrong("shares-wrong-status-iota-ordinal",
		"re-encodes the stored account/purchase/dividend status integer as a contiguous Go iota ordinal (stored id / 100), "+
			"so any vector that pins a stored status goes red",
		statusOrdinalEvaluator{})
	RegisterWrong("shares-wrong-summary-approved-as-pending",
		"fills the summary's totalPendingForApprovalShares fold from totalApprovedShares, so a share-account read-back "+
			"whose approved and pending counts differ goes red",
		transposedSummaryEvaluator{})
	RegisterWrong("shares-wrong-product-price-transposed",
		"serialises a share product's unit price into the share-capital field and the share capital into the unit-price field",
		transposedProductPriceEvaluator{})
	RegisterWrong("shares-wrong-zero-money-dropped",
		"omits a money cell whose minor-unit value is zero (the share-capital 0.00 read-back disappears)",
		dropZeroMoneyEvaluator{})
}
