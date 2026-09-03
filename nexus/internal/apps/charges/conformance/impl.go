package conformance

import (
	"fmt"
	"math/big"
	"sort"
	"sync"

	"github.com/gerege/nexus/internal/apps/charges"
)

// ChargeEvaluator is what a charges implementation must be able to do for this
// harness to grade it. It is NOT "persist a charge to a database"; it is the two
// pure computations the slice actually ports — construction validation and fee
// arithmetic — which is all a captured charge vector can observe.
//
// The input carries the oracle's STORED FORM (enum stored values, monetary
// integer strings, micro-per-cent percentage) and the output carries integers,
// for the same non-circularity reason as the ledger harness: the vector supplies
// characters, the implementation supplies integers, and a port that routes a
// percentage through a float64, or truncates instead of HALF_UP, produces a
// different integer and the comparator reports a money kill.
type ChargeEvaluator interface {
	Evaluate(req ChargeRequest) (ChargeResult, error)
}

// ChargeResult is an implementation's answer: the ordered construction-validation
// codes and, when the charge is well-formed and fee-computable, the fee amount
// in integer minor units.
type ChargeResult struct {
	// ValidationCodes is the ordered list of Charge.Validate() codes, empty on
	// success [Charge.java:240-300].
	ValidationCodes []string

	// FeeMinor is the computed fee, meaningful only when FeePresent is true.
	FeeMinor charges.MinorUnits

	// FeePresent reports whether a fee could be computed for this request. It is
	// false for a charge whose validation failed, and false for an
	// interest-based calculation type whose fee needs the loan's interest.
	FeePresent bool
}

// ---------------------------------------------------------------------------
// The registry
// ---------------------------------------------------------------------------

// Every name a vector's graded_against cites must be REGISTERED here, admit.go
// refuses one that is not, and the binary's -impl flag runs it. A JSON row
// naming an implementation nobody can execute is an admissibility failure rather
// than an unfalsifiable claim.

var (
	implMu sync.RWMutex
	impls  = map[string]ChargeEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a ChargeEvaluator available under name. Registering a name
// twice panics: two implementations answering to one name would make the
// report's "implementation" line a lie.
func Register(name string, e ChargeEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("charges conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name, with
// the defect it embodies stated. It is separate from Register so the report can
// say which implementations are known-wrong, and so the default selection can
// never pick one.
func RegisterWrong(name, defect string, e ChargeEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (ChargeEvaluator, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	e, ok := impls[name]
	return e, ok
}

// IsRegisteredWrong reports whether name is a known-wrong implementation, and
// the defect it embodies.
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
// declared wrong. The default selection uses this list, so -impl must be given
// explicitly to grade against a wrong one.
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

// goEvaluator is the Go port, wrapped so the harness can grade it like any
// other implementation.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() ChargeEvaluator { return goEvaluator{} }

// percentScale mirrors charges.percentScale (unexported): the fraction
// Percent / percentScale is "percentage / 100" [charges/money.go].
const percentScale = 100_000_000

func (goEvaluator) Evaluate(req ChargeRequest) (ChargeResult, error) {
	var res ChargeResult
	c, err := chargeFromRequest(req)
	if err != nil {
		return res, err
	}
	for _, ve := range c.Validate() {
		res.ValidationCodes = append(res.ValidationCodes, ve.Code)
	}
	if len(res.ValidationCodes) != 0 {
		return res, nil
	}
	fee, ok, err := feeFor(c, req)
	if err != nil {
		return res, err
	}
	if ok {
		res.FeeMinor = fee
		res.FeePresent = true
	}
	return res, nil
}

// chargeFromRequest decodes a vector request into a charges.Charge. An enum
// stored value the port does not know is an error, not a guess.
func chargeFromRequest(req ChargeRequest) (charges.Charge, error) {
	appliesTo, ok := charges.ChargeAppliesToFromStoredValue(req.AppliesTo)
	if !ok {
		return charges.Charge{}, fmt.Errorf("request.applies_to %d is not a known stored value", req.AppliesTo)
	}
	timeType, ok := charges.ChargeTimeTypeFromStoredValue(req.TimeType)
	if !ok {
		return charges.Charge{}, fmt.Errorf("request.time_type %d is not a known stored value", req.TimeType)
	}
	calcType, ok := charges.ChargeCalculationTypeFromStoredValue(req.CalculationType)
	if !ok {
		return charges.Charge{}, fmt.Errorf("request.calculation_type %d is not a known stored value", req.CalculationType)
	}
	pmode, ok := charges.ChargePaymentModeFromStoredValue(req.PaymentMode)
	if !ok {
		return charges.Charge{}, fmt.Errorf("request.payment_mode %d is not a known stored value", req.PaymentMode)
	}
	amount, err := parseMinorText(req.AmountMinor)
	if err != nil {
		return charges.Charge{}, fmt.Errorf("request.amount_minor: %w", err)
	}
	c := charges.Charge{
		Name:            req.Name,
		CurrencyCode:    req.CurrencyCode,
		Amount:          amount,
		Percentage:      charges.Percent(req.Percentage),
		AppliesTo:       appliesTo,
		TimeType:        timeType,
		CalculationType: calcType,
		PaymentMode:     pmode,
		Penalty:         req.Penalty,
		Active:          req.Active,
		Deleted:         req.Deleted,
	}
	if req.MinCapMinor != nil {
		m, err := parseMinorText(*req.MinCapMinor)
		if err != nil {
			return charges.Charge{}, fmt.Errorf("request.min_cap_minor: %w", err)
		}
		c.MinCap = &m
	}
	if req.MaxCapMinor != nil {
		m, err := parseMinorText(*req.MaxCapMinor)
		if err != nil {
			return charges.Charge{}, fmt.Errorf("request.max_cap_minor: %w", err)
		}
		c.MaxCap = &m
	}
	return c, nil
}

// feeFor computes the fee the oracle would for a VALID charge. ok is false for
// an interest-based calculation type, whose fee needs the loan's interest
// component and is not computable from a base amount alone.
func feeFor(c charges.Charge, req ChargeRequest) (charges.MinorUnits, bool, error) {
	switch {
	case c.CalculationType.IsFlat():
		// Flat amount is authoritative; no arithmetic is performed. The flat fee
		// is the charge's stored amount [Charge.java:76-77], returned unmodified
		// by getAmount [LoanCharge.java:405-406].
		return c.Amount, true, nil
	case c.CalculationType.IsPercentageOfAmount(), c.CalculationType.IsPercentageOfDisbursementAmount():
		base, err := parseMinorText(req.BaseAmountMinor)
		if err != nil {
			return 0, false, fmt.Errorf("request.base_amount_minor: %w", err)
		}
		p, err := charges.PercentageOf(base, c.Percentage)
		if err != nil {
			return 0, false, err
		}
		return charges.MinimumAndMaximumCap(p, c.MinCap, c.MaxCap), true, nil
	default:
		return 0, false, nil
	}
}

// truncatingEvaluator is a DELIBERATELY WRONG implementation: it computes the
// percentage fee by truncating toward zero instead of rounding HALF_UP, so a
// percentage whose exact fee carries a fraction that rounds up will differ by
// one minor unit. It validates identically to the port, so the only cell that
// can go red is the money cell — which is the point.
type truncatingEvaluator struct{ goEvaluator }

func (truncatingEvaluator) Evaluate(req ChargeRequest) (ChargeResult, error) {
	res, err := (goEvaluator{}).Evaluate(req)
	if err != nil || !res.FeePresent {
		return res, err
	}
	c, err := chargeFromRequest(req)
	if err != nil {
		return res, err
	}
	if c.CalculationType.IsPercentageOfAmount() || c.CalculationType.IsPercentageOfDisbursementAmount() {
		base, err := parseMinorText(req.BaseAmountMinor)
		if err != nil {
			return res, err
		}
		n := new(big.Int).Mul(big.NewInt(int64(base)), big.NewInt(int64(c.Percentage)))
		d := big.NewInt(percentScale)
		q, r := new(big.Int), new(big.Int)
		q.QuoRem(n, d, r)
		res.FeeMinor = charges.MinimumAndMaximumCap(charges.MinorUnits(q.Int64()), c.MinCap, c.MaxCap)
	}
	return res, nil
}

func init() {
	Register("charges-go", NewGoEvaluator())
	RegisterWrong("charges-wrong-percent-truncating",
		"computes the percentage fee by truncating toward zero instead of rounding HALF_UP, so any "+
			"percentage whose exact fee carries a fraction that rounds up is one minor unit low",
		truncatingEvaluator{})
}
